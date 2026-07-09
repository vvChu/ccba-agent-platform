"""Process-aware and expiration-safe file-based mutual exclusion lock.

Prevents write conflicts on shared file resources across concurrent processes.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

_thread_locks: dict[Path, threading.Lock] = {}
_thread_locks_mutex = threading.Lock()


def _get_thread_lock(path: Path) -> threading.Lock:
    resolved_path = path.resolve()
    with _thread_locks_mutex:
        if resolved_path not in _thread_locks:
            _thread_locks[resolved_path] = threading.Lock()
        return _thread_locks[resolved_path]


class FileMutexLock:
    """A process-aware and expiration-safe file-based mutual exclusion lock."""

    def __init__(
        self,
        lock_path: Path,
        timeout: float = 10.0,
        retry_interval: float = 0.1,
        expire_seconds: float = 300.0,
    ) -> None:
        """Initialize the mutex lock.

        Args:
            lock_path: Path to the lock file.
            timeout: Maximum seconds to wait for acquiring lock.
            retry_interval: Seconds to wait between check loops.
            expire_seconds: Seconds after which lock is considered stale and overridden.
        """
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.expire_seconds = expire_seconds
        self.pid = os.getpid()
        self.is_locked = False
        self._thread_lock = _get_thread_lock(self.lock_path)
        self._thread_lock_acquired = False

    def __enter__(self) -> FileMutexLock:
        """Acquire the lock, resolving PIDs and expiration dynamically."""
        start_time = time.time()

        # 1. Acquire thread-level lock first
        acquired = self._thread_lock.acquire(timeout=self.timeout)
        if not acquired:
            raise TimeoutError(
                f"Timeout waiting to acquire thread lock on {self.lock_path} after {self.timeout} seconds."
            )
        self._thread_lock_acquired = True

        # 2. Acquire process-level file lock
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                # Attempt to create the lock file atomically
                lock_data = {"pid": self.pid, "timestamp": time.time()}
                with open(self.lock_path, "x", encoding="utf-8") as f:
                    json.dump(lock_data, f)
                self.is_locked = True
                break
            except (FileExistsError, PermissionError):
                # Read the existing lock file to check if owner is dead or expired
                try:
                    content = self.lock_path.read_text(encoding="utf-8")
                    data = json.loads(content)
                    lock_pid = int(data.get("pid")) if data.get("pid") is not None else None
                    lock_time = float(data.get("timestamp", 0))
                except Exception:
                    # Corrupted file, override
                    lock_pid = None
                    lock_time = 0.0

                pid_active = True
                if lock_pid is not None:
                    try:
                        # Check if process is still alive (SIG 0 does not kill the process)
                        os.kill(lock_pid, 0)
                    except OSError:
                        pid_active = False
                else:
                    pid_active = False

                if not pid_active:
                    try:
                        self.lock_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    continue

                age = time.time() - lock_time
                if age >= self.expire_seconds:
                    try:
                        self.lock_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    continue

                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    raise TimeoutError(
                        f"Timeout waiting to acquire file lock on {self.lock_path} after {self.timeout} seconds."
                    ) from None

                time.sleep(self.retry_interval)
            except Exception as e:
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    raise TimeoutError(
                        f"Failed to acquire file lock on {self.lock_path}: {e}"
                    ) from e
                time.sleep(self.retry_interval)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Release the lock if it belongs to this process."""
        try:
            if self.is_locked and self.lock_path.exists():
                try:
                    content = self.lock_path.read_text(encoding="utf-8")
                    data = json.loads(content)
                    if data.get("pid") == self.pid:
                        self.lock_path.unlink()
                except Exception:
                    pass
                self.is_locked = False
        finally:
            if self._thread_lock_acquired:
                self._thread_lock.release()
                self._thread_lock_acquired = False
