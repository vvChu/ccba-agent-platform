"""Unit tests for Hybrid FileMutexLock (OS Kernel Lock + JSON Metadata)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from ccba_harness import FileMutexLock


def test_hybrid_mutex_basic(tmp_path: Path) -> None:
    """Test basic lock acquire, metadata creation, and clean release."""
    lock_file = tmp_path / "test_basic.lock"
    mutex = FileMutexLock(lock_file, timeout=1.0, retry_interval=0.05)

    with mutex:
        assert mutex.is_locked
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()
        assert "timestamp" in data

    assert not mutex.is_locked
    assert not lock_file.exists()


def test_hybrid_mutex_instance_reusability(tmp_path: Path) -> None:
    """Test that a single FileMutexLock instance can be acquired and released repeatedly."""
    lock_file = tmp_path / "test_reusable.lock"
    mutex = FileMutexLock(lock_file, timeout=1.0, retry_interval=0.05)

    for cycle in range(3):
        with mutex:
            assert mutex.is_locked, f"Cycle {cycle}: should be locked"
            assert lock_file.exists(), f"Cycle {cycle}: lock file should exist"
            assert mutex._fd is not None, f"Cycle {cycle}: file descriptor should be open"
        assert not mutex.is_locked, f"Cycle {cycle}: should be released"
        assert mutex._fd is None, f"Cycle {cycle}: file descriptor should be reset to None"
        assert not mutex._thread_lock_acquired, f"Cycle {cycle}: thread lock flag should be reset"
        assert not lock_file.exists(), f"Cycle {cycle}: lock file should be unlinked"


def test_hybrid_mutex_read_while_locked(tmp_path: Path) -> None:
    """Test reading JSON metadata while lock is held (verifying High-Offset Locking on Windows)."""
    lock_file = tmp_path / "test_read_under_lock.lock"

    with FileMutexLock(lock_file, timeout=1.0):
        # On Windows, mandatory locking on byte 0 would cause PermissionError here.
        # High-Offset locking (0x7FFFFFFF) must allow seamless metadata reading.
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()
        assert time.time() - float(data["timestamp"]) < 5.0

    assert not lock_file.exists()


def test_hybrid_mutex_concurrency_timeout(tmp_path: Path) -> None:
    """Test that concurrent acquisition attempts time out properly."""
    lock_file = tmp_path / "test_concurrent.lock"
    acquired_order = []
    errors = []

    def worker(worker_id: int, hold_time: float, wait_timeout: float) -> None:
        try:
            with FileMutexLock(lock_file, timeout=wait_timeout, retry_interval=0.02):
                acquired_order.append(worker_id)
                time.sleep(hold_time)
        except Exception as e:
            errors.append((worker_id, e))

    # Thread 1 acquires and holds for 0.4s
    t1 = threading.Thread(target=worker, args=(1, 0.4, 1.0))
    # Thread 2 tries with 0.1s timeout -> should timeout
    t2 = threading.Thread(target=worker, args=(2, 0.1, 0.1))

    t1.start()
    time.sleep(0.05)  # Ensure thread 1 locks first
    t2.start()

    t1.join()
    t2.join()

    assert acquired_order == [1]
    assert len(errors) == 1
    assert errors[0][0] == 2
    assert isinstance(errors[0][1], TimeoutError)


def test_hybrid_mutex_subprocess_termination(tmp_path: Path) -> None:
    """Test immediate lock recovery when holding process is forcefully terminated (Zero-Stale-Lock)."""
    lock_file = tmp_path / "test_crash_recovery.lock"

    # Spawn subprocess that acquires lock and sleeps indefinitely
    sub_code = f"""
import time
from pathlib import Path
from ccba_harness import FileMutexLock

lock = FileMutexLock(Path(r"{lock_file}"), timeout=2.0)
with lock:
    print("LOCKED", flush=True)
    time.sleep(60)
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", sub_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait until child prints LOCKED
        assert proc.stdout is not None
        line = proc.stdout.readline().strip()
        assert line == "LOCKED", (
            f"Subprocess failed to lock: {proc.stderr.read() if proc.stderr else ''}"
        )
        assert lock_file.exists()

        # Verify parent cannot immediately acquire lock without waiting
        with pytest.raises(TimeoutError):
            with FileMutexLock(lock_file, timeout=0.1, retry_interval=0.02):
                pass

        # Forcefully terminate child process (simulating unhandled crash / kill -9)
        proc.terminate()
        proc.wait(timeout=5.0)

        # OS kernel must have reclaimed the lock descriptor immediately!
        # Parent should acquire lock well within 0.5s without waiting for 300s expiration.
        t_start = time.time()
        with FileMutexLock(lock_file, timeout=1.0, retry_interval=0.02) as recovered:
            assert recovered.is_locked
            assert lock_file.exists()
            content = lock_file.read_text(encoding="utf-8")
            data = json.loads(content)
            assert data["pid"] == os.getpid()

        t_elapsed = time.time() - t_start
        assert t_elapsed < 0.5, f"Lock recovery took too long: {t_elapsed:.3f}s (expected < 0.5s)"

    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_hybrid_mutex_synthetic_stale_override(tmp_path: Path) -> None:
    """Test overriding stale lock file left by dead PID."""
    lock_file = tmp_path / "test_dead_pid.lock"
    # PID 9999999 is nonexistent
    stale_data = {"pid": 9999999, "timestamp": time.time() - 10}
    lock_file.write_text(json.dumps(stale_data), encoding="utf-8")

    with FileMutexLock(lock_file, timeout=0.5, retry_interval=0.05) as mutex:
        assert mutex.is_locked
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()


def test_hybrid_mutex_synthetic_alive_timeout(tmp_path: Path) -> None:
    """Test backward compatibility: simulated alive lock without OS descriptor blocks until timeout."""
    lock_file = tmp_path / "test_simulated_alive.lock"
    alive_data = {"pid": os.getpid(), "timestamp": time.time()}
    lock_file.write_text(json.dumps(alive_data), encoding="utf-8")

    with pytest.raises(TimeoutError):
        with FileMutexLock(lock_file, timeout=0.2, retry_interval=0.03):
            pass


def test_hybrid_mutex_reentrancy_same_thread(tmp_path: Path) -> None:
    """Test that nested acquisitions on the same thread succeed without deadlocking."""
    lock_file = tmp_path / "test_reentrant.lock"

    with FileMutexLock(lock_file, timeout=1.0) as outer_mutex:
        assert outer_mutex.is_locked
        assert lock_file.exists()

        with FileMutexLock(lock_file, timeout=1.0) as inner_mutex:
            assert inner_mutex.is_locked
            assert inner_mutex._reentrant

        # Inner released, outer still locked
        assert outer_mutex.is_locked
        assert lock_file.exists()

    # Outer released
    assert not outer_mutex.is_locked
    assert not lock_file.exists()
