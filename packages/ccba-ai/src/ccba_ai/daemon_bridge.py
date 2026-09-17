"""Persistent Stdio Daemon Bridge for CCBA CLI Providers.

Provides long-lived process management, stream synchronization (Mutex/Asyncio Lock),
idle timeout termination, and one-shot spillover for Antigravity & Copilot CLIs.
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from typing import Any, cast

logger = logging.getLogger("ccba_ai.daemon")

# Default idle timeout: 15 minutes
DEFAULT_IDLE_TIMEOUT = 900.0


def kill_process_tree(pid: int | None) -> None:
    """Kill process tree on Windows or Unix cleanly."""
    if pid is None:
        return
    if sys.platform == "win32":
        os.system(f"taskkill /F /T /PID {pid} >nul 2>&1")  # noqa: S605
    else:
        try:
            import signal

            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass


class PersistentStdioDaemon:
    """Manages a long-lived CLI subprocess communicating via stdin/stdout streams.

    Features:
    - Lazy on-demand boot (spawned on first request).
    - Serialized thread/async locking for stdin/stdout isolation.
    - Idle timeout watchdog: terminates process after inactivity.
    - Graceful atexit cleanup to prevent zombie processes.
    - Spillover detection when lock contention exceeds threshold.

    Args:
        build_command: Callable returning the command list to start the daemon.
        idle_timeout: Seconds of inactivity before daemon self-terminates.
        max_waiting_requests: Max queued requests before triggering one-shot spillover.
    """

    def __init__(
        self,
        build_command: Callable[[], list[str]],
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
        max_waiting_requests: int = 2,
    ) -> None:
        self.build_command = build_command
        self.idle_timeout = idle_timeout
        self.max_waiting_requests = max_waiting_requests

        self._proc: subprocess.Popen[str] | None = None
        self._async_proc: asyncio.subprocess.Process | None = None
        self._sync_lock = threading.Lock()
        self._async_lock = asyncio.Lock()
        self._state_lock = threading.Lock()
        self._waiting_count = 0
        self._last_active_time = time.time()
        self._watchdog_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Register cleanup on interpreter shutdown
        atexit.register(self.stop)

    @property
    def is_running(self) -> bool:
        """Check if background process is currently alive."""
        if self._proc is not None:
            return self._proc.poll() is None
        if self._async_proc is not None:
            return self._async_proc.returncode is None
        return False

    def _start_sync_if_needed(self) -> subprocess.Popen[str]:
        """Spawn the synchronous subprocess if not currently running."""
        if self._proc is None or self._proc.poll() is not None:
            cmd = self.build_command()
            logger.info(f"[ccba-ai-daemon] Spawning persistent CLI daemon: {' '.join(cmd)}")
            kwargs: dict[str, Any] = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "encoding": "utf-8",
                "bufsize": 1,
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True

            self._proc = subprocess.Popen(cmd, **kwargs)
            self._start_watchdog()

        self._last_active_time = time.time()
        return self._proc

    async def _start_async_if_needed(self) -> asyncio.subprocess.Process:
        """Spawn the asynchronous subprocess if not currently running."""
        if self._async_proc is None or self._async_proc.returncode is not None:
            cmd = self.build_command()
            logger.info(f"[ccba-ai-daemon] Spawning async persistent CLI daemon: {' '.join(cmd)}")
            kwargs: dict[str, Any] = {
                "stdin": asyncio.subprocess.PIPE,
                "stdout": asyncio.subprocess.PIPE,
                "stderr": asyncio.subprocess.PIPE,
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True

            self._async_proc = await asyncio.create_subprocess_exec(*cmd, **kwargs)
            self._start_watchdog()

        self._last_active_time = time.time()
        return self._async_proc

    def _start_watchdog(self) -> None:
        """Start background thread monitoring idle timeout."""
        if self._watchdog_thread is None or not self._watchdog_thread.is_alive():
            self._stop_event.clear()
            self._watchdog_thread = threading.Thread(
                target=self._watchdog_loop, daemon=True, name="CCBA-Daemon-Watchdog"
            )
            self._watchdog_thread.start()

    def _watchdog_loop(self) -> None:
        """Terminate process if idle timeout expires."""
        while not self._stop_event.wait(15.0):
            if not self.is_running:
                break
            idle_duration = time.time() - self._last_active_time
            if idle_duration >= self.idle_timeout:
                logger.info(
                    f"[ccba-ai-daemon] Daemon idle for {idle_duration:.0f}s >= {self.idle_timeout}s. Terminating..."
                )
                self.stop()
                break

    def send_turn_sync(
        self,
        prompt: str,
        parse_response_fn: Callable[[str], tuple[str, Any]],
        fallback_oneshot_fn: Callable[[str], tuple[str, Any]],
        timeout: float = 120.0,
    ) -> tuple[str, Any]:
        """Send a single prompt turn over synchronized Stdio pipe (sync).

        If lock contention exceeds threshold, seamlessly spills over to One-Shot.
        """
        # 1. Check contention for spillover
        with self._state_lock:
            if self._waiting_count >= self.max_waiting_requests:
                logger.info(
                    f"[ccba-ai-daemon] High contention ({self._waiting_count} waiting). Spilling over to One-Shot..."
                )
                return fallback_oneshot_fn(prompt)
            self._waiting_count += 1

        try:
            # 2. Acquire lock for pipe access
            acquired = self._sync_lock.acquire(timeout=timeout)
            if not acquired:
                logger.warning(
                    "[ccba-ai-daemon] Lock acquire timed out. Spilling over to One-Shot."
                )
                return fallback_oneshot_fn(prompt)

            try:
                proc = self._start_sync_if_needed()
                self._last_active_time = time.time()

                if proc.stdin is None or proc.stdout is None:
                    return fallback_oneshot_fn(prompt)

                # Send prompt line
                proc.stdin.write(prompt + "\n")
                proc.stdin.flush()

                # Read output lines until valid response or EOF
                collected_lines: list[str] = []
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    collected_lines.append(line)
                    try:
                        # Attempt early parse on NDJSON events
                        raw_block = "".join(collected_lines)
                        return parse_response_fn(raw_block)
                    except Exception:
                        continue

                # Final parse attempt
                raw_text = "".join(collected_lines)
                if raw_text.strip():
                    return parse_response_fn(raw_text)

                logger.warning(
                    "[ccba-ai-daemon] No output from persistent daemon. Falling back to One-Shot."
                )
                return fallback_oneshot_fn(prompt)

            except Exception as exc:
                logger.warning(f"[ccba-ai-daemon] Daemon turn failed: {exc}. Restarting process...")
                self.stop()
                return fallback_oneshot_fn(prompt)

            finally:
                self._sync_lock.release()

        finally:
            with self._state_lock:
                self._waiting_count = max(0, self._waiting_count - 1)

    async def send_turn_async(
        self,
        prompt: str,
        parse_response_fn: Callable[[str], tuple[str, Any]],
        fallback_oneshot_fn: Callable[[str], Any],
        timeout: float = 120.0,
    ) -> tuple[str, Any]:
        async def _call_fallback() -> tuple[str, Any]:
            res = fallback_oneshot_fn(prompt)
            if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                res = await res
            return cast("tuple[str, Any]", res)

        if self._waiting_count >= self.max_waiting_requests:
            logger.info(
                f"[ccba-ai-daemon] High contention ({self._waiting_count} waiting). Async spilling over to One-Shot..."
            )
            return await _call_fallback()

        self._waiting_count += 1
        try:
            async with self._async_lock:
                try:
                    proc = await self._start_async_if_needed()
                    self._last_active_time = time.time()

                    if proc.stdin is None or proc.stdout is None:
                        return await _call_fallback()

                    proc.stdin.write((prompt + "\n").encode("utf-8"))
                    await proc.stdin.drain()

                    collected_lines: list[str] = []
                    while True:
                        try:
                            line_bytes = await asyncio.wait_for(
                                proc.stdout.readline(), timeout=timeout
                            )
                        except asyncio.TimeoutError:
                            break

                        if not line_bytes:
                            break
                        line_str = line_bytes.decode("utf-8", errors="replace")
                        collected_lines.append(line_str)
                        try:
                            raw_block = "".join(collected_lines)
                            return parse_response_fn(raw_block)
                        except Exception:
                            continue

                    raw_text = "".join(collected_lines)
                    if raw_text.strip():
                        return parse_response_fn(raw_text)

                    return await _call_fallback()

                except Exception as exc:
                    logger.warning(f"[ccba-ai-daemon] Async daemon turn failed: {exc}")
                    self.stop()
                    return await _call_fallback()

        finally:
            self._waiting_count = max(0, self._waiting_count - 1)

    def stop(self) -> None:
        """Safely terminate all background daemon processes and threads."""
        self._stop_event.set()
        if self._proc is not None:
            pid = self._proc.pid
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
            except Exception:
                pass
            kill_process_tree(pid)
            self._proc = None

        if self._async_proc is not None:
            pid = self._async_proc.pid
            try:
                self._async_proc.terminate()
            except Exception:
                pass
            kill_process_tree(pid)
            self._async_proc = None
