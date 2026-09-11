"""_lock_fallback.py - Safe fallback file lock using standard library only.

Provides atomic mutual exclusion when ccba-harness is not available in the environment.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from types import TracebackType

logger = logging.getLogger(__name__)


class SimpleFileLock:
    """Atomic, expiration-safe file lock relying purely on Python standard library.

    Protects against concurrent file writes when ccba-harness is not installed.
    """

    def __init__(
        self,
        lock_path: Path | str,
        timeout: float = 10.0,
        retry_interval: float = 0.05,
        expire_seconds: float = 60.0,
    ) -> None:
        """Initialize the fallback file lock.

        Args:
            lock_path: Path to the lock file.
            timeout: Maximum seconds to wait for acquiring lock.
            retry_interval: Seconds to sleep between lock acquisition attempts.
            expire_seconds: Seconds after which a lock is considered stale.
        """
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.expire_seconds = expire_seconds
        self.is_locked = False
        self.pid = os.getpid()

    def __enter__(self) -> SimpleFileLock:
        """Acquire the lock atomically, recovering from stale locks if needed.

        Returns:
            SimpleFileLock instance.

        Raises:
            TimeoutError: If lock could not be acquired within timeout.
        """
        start_time = time.time()
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                # Atomic file creation using exclusive creation mode ('x')
                with open(self.lock_path, "x", encoding="utf-8") as f:
                    f.write(f"{self.pid}:{time.time()}")
                self.is_locked = True
                return self
            except (FileExistsError, PermissionError):
                # Check for stale lock
                try:
                    mtime = self.lock_path.stat().st_mtime
                    if (time.time() - mtime) >= self.expire_seconds:
                        logger.warning(
                            "Stale lock detected on %s (> %.1fs). Invalidating...",
                            self.lock_path,
                            self.expire_seconds,
                        )
                        self.lock_path.unlink(missing_ok=True)
                        continue
                except (OSError, PermissionError):
                    pass

                if (time.time() - start_time) >= self.timeout:
                    raise TimeoutError(
                        f"Timeout acquiring lock on {self.lock_path} after {self.timeout}s."
                    ) from None
                time.sleep(self.retry_interval)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Release the lock file."""
        if self.is_locked:
            try:
                self.lock_path.unlink(missing_ok=True)
            except Exception:
                pass
            self.is_locked = False
