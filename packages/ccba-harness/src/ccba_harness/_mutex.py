"""Process-aware and expiration-safe file-based mutual exclusion lock.

Prevents write conflicts on shared file resources across concurrent processes.
Combines OS-level kernel locking (msvcrt on Windows, fcntl on POSIX) with JSON metadata
to achieve instant stale lock recovery upon process crash without blocking metadata inspection.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

_thread_locks: dict[Path, threading.Lock] = {}
_thread_locks_mutex = threading.Lock()

# 2GB - 1 virtual byte offset for Windows mandatory byte-range locking.
# Allows reading JSON metadata at offset 0 while guaranteeing strict mutual exclusion.
_LOCK_BYTE_OFFSET = 0x7FFFFFFF


def _is_process_alive(pid: int | None) -> bool:
    """Check whether a process with given PID is still active across Windows and POSIX without terminating it."""
    if pid is None or pid <= 0:
        return False
    if sys.platform.startswith("win"):
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                is_active = exit_code.value == 259  # STILL_ACTIVE
            else:
                is_active = False
            kernel32.CloseHandle(handle)
            return is_active
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _get_thread_lock(path: Path) -> threading.Lock:
    resolved_path = path.resolve()
    with _thread_locks_mutex:
        if resolved_path not in _thread_locks:
            _thread_locks[resolved_path] = threading.Lock()
        return _thread_locks[resolved_path]


class FileMutexLock:
    """A process-aware and expiration-safe hybrid file-based mutual exclusion lock."""

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
        self._fd: int | None = None
        self._thread_lock = _get_thread_lock(self.lock_path)
        self._thread_lock_acquired = False

    def acquire(self) -> FileMutexLock:
        """Acquire the lock, resolving PIDs and expiration dynamically.

        Returns:
            Self instance with active lock.

        Raises:
            TimeoutError: If lock acquisition exceeds configured timeout.
        """
        start_time = time.time()

        # 1. Acquire thread-level lock first
        acquired = self._thread_lock.acquire(timeout=self.timeout)
        if not acquired:
            raise TimeoutError(
                f"Timeout waiting to acquire thread lock on {self.lock_path} after {self.timeout} seconds."
            )
        self._thread_lock_acquired = True

        try:
            # 2. Acquire process-level file lock
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY

            while True:
                fd: int | None = None
                try:
                    fd = os.open(str(self.lock_path), flags, 0o666)

                    # Try acquiring OS-level kernel lock
                    locked_os = False
                    if sys.platform.startswith("win"):
                        import msvcrt

                        try:
                            os.lseek(fd, _LOCK_BYTE_OFFSET, os.SEEK_SET)
                            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                            locked_os = True
                        except (OSError, PermissionError):
                            locked_os = False
                    else:
                        import fcntl

                        try:
                            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            locked_os = True
                            # On POSIX, verify file wasn't unlinked before lock acquisition
                            try:
                                stat_fd = os.fstat(fd)
                                stat_path = os.stat(str(self.lock_path))
                                if stat_fd.st_ino != stat_path.st_ino:
                                    locked_os = False
                            except (FileNotFoundError, OSError):
                                locked_os = False

                            if not locked_os:
                                try:
                                    fcntl.flock(fd, fcntl.LOCK_UN)
                                except OSError:
                                    pass
                        except OSError:
                            locked_os = False

                    if not locked_os:
                        os.close(fd)
                        fd = None
                        elapsed = time.time() - start_time
                        if elapsed >= self.timeout:
                            raise TimeoutError(
                                f"Timeout waiting to acquire file lock on {self.lock_path} after {self.timeout} seconds."
                            )
                        time.sleep(self.retry_interval)
                        continue

                    # OS lock acquired. Verify existing JSON metadata (e.g. for synthetic lock tests or crash recovery)
                    try:
                        os.lseek(fd, 0, os.SEEK_SET)
                        raw_bytes = os.read(fd, 4096)
                        content = raw_bytes.decode("utf-8", errors="ignore").strip()
                        if content:
                            data = json.loads(content)
                            existing_pid = (
                                int(data.get("pid")) if data.get("pid") is not None else None
                            )
                            existing_time = float(data.get("timestamp", 0))

                            if existing_pid is not None and _is_process_alive(existing_pid):
                                age = time.time() - existing_time
                                if age < self.expire_seconds:
                                    # Lock is held by an active process or simulated alive test
                                    if sys.platform.startswith("win"):
                                        import msvcrt

                                        try:
                                            os.lseek(fd, _LOCK_BYTE_OFFSET, os.SEEK_SET)
                                            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                                        except OSError:
                                            pass
                                    else:
                                        import fcntl

                                        try:
                                            fcntl.flock(fd, fcntl.LOCK_UN)
                                        except OSError:
                                            pass

                                    os.close(fd)
                                    fd = None

                                    elapsed = time.time() - start_time
                                    if elapsed >= self.timeout:
                                        raise TimeoutError(
                                            f"Timeout waiting to acquire file lock on {self.lock_path} after {self.timeout} seconds."
                                        )
                                    time.sleep(self.retry_interval)
                                    continue
                    except Exception:
                        # Malformed or unreadable metadata, proceed to overwrite
                        pass

                    # Write our process metadata safely using truncation to eliminate trailing corrupt data
                    lock_data = json.dumps({"pid": self.pid, "timestamp": time.time()}).encode(
                        "utf-8"
                    )
                    os.lseek(fd, 0, os.SEEK_SET)
                    os.ftruncate(fd, 0)
                    os.write(fd, lock_data)
                    os.fsync(fd)

                    self._fd = fd
                    self.is_locked = True
                    break

                except TimeoutError:
                    if fd is not None:
                        try:
                            os.close(fd)
                        except OSError:
                            pass
                    raise
                except Exception as e:
                    if fd is not None:
                        try:
                            os.close(fd)
                        except OSError:
                            pass
                    elapsed = time.time() - start_time
                    if elapsed >= self.timeout:
                        raise TimeoutError(
                            f"Failed to acquire file lock on {self.lock_path}: {e}"
                        ) from e
                    time.sleep(self.retry_interval)

            return self

        except BaseException:
            if self._thread_lock_acquired:
                self._thread_lock.release()
                self._thread_lock_acquired = False
            raise

    def release(self) -> None:
        """Release the lock if it belongs to this process and reset instance state."""
        try:
            if self.is_locked and self._fd is not None:
                fd = self._fd
                if sys.platform.startswith("win"):
                    import msvcrt

                    # Windows order: Unlock -> Close -> Unlink
                    try:
                        os.lseek(fd, _LOCK_BYTE_OFFSET, os.SEEK_SET)
                        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                    except OSError:
                        pass
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    try:
                        self.lock_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                else:
                    import fcntl

                    # POSIX order: Unlink -> Unlock -> Close
                    try:
                        self.lock_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                    try:
                        fcntl.flock(fd, fcntl.LOCK_UN)
                    except OSError:
                        pass
                    try:
                        os.close(fd)
                    except OSError:
                        pass
        finally:
            # Guarantee instance reusability invariant
            self._fd = None
            self.is_locked = False
            if self._thread_lock_acquired:
                self._thread_lock.release()
                self._thread_lock_acquired = False

    def __enter__(self) -> FileMutexLock:
        """Acquire the lock using context manager."""
        return self.acquire()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Release the lock using context manager."""
        self.release()
