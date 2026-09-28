"""test_tuner_git_lock.py - Unit tests for GitMutexLock and GitRatchetOptimizer integration.

Tests:
1. Normal acquire & release via context manager and explicit API.
2. Timeout when lock is already held by another thread.
3. Bypass (no-op) when enabled=False.
4. GitRatchetOptimizer bypass when dry_run=True or lock_enabled=False.
5. Correct lock_path auto-resolution based on project_root.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from ccba_harness.evals.tuner import GitMutexLock, GitRatchetOptimizer, RatchetConfig

pytestmark = [pytest.mark.fast, pytest.mark.unit]


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture()
def lock_path(tmp_path: Path) -> Path:
    return tmp_path / "test_evals_tuner.lock"


@pytest.fixture()
def minimal_config(tmp_path: Path) -> RatchetConfig:
    target = tmp_path / "SKILL.md"
    target.write_text("# Skill\n\nContent.", encoding="utf-8")
    return RatchetConfig(
        target_file=target,
        max_iterations=1,
        enable_adaptive_slicing=False,
    )


# ===========================================================================
# 1. Normal acquire & release
# ===========================================================================


def test_git_mutex_lock_acquire_and_release(lock_path: Path) -> None:
    """Lock can be acquired and released via context manager; lock file is cleaned up."""
    lock = GitMutexLock(lock_path=lock_path, timeout=5.0)

    assert not lock_path.exists()
    with lock:
        assert lock._fd is not None
        assert lock_path.exists()

    # After release: fd closed, lock file removed
    assert lock._fd is None
    assert not lock_path.exists()


def test_git_mutex_lock_explicit_acquire_release(lock_path: Path) -> None:
    """explicit acquire()/release() API works without context manager."""
    lock = GitMutexLock(lock_path=lock_path, timeout=5.0)

    lock.acquire()
    assert lock._fd is not None
    lock.release()
    assert lock._fd is None


def test_git_mutex_lock_reentrant_multiple_cycles(lock_path: Path) -> None:
    """Lock can be acquired and released multiple times in sequence."""
    lock = GitMutexLock(lock_path=lock_path, timeout=5.0)

    for _ in range(3):
        with lock:
            assert lock._fd is not None
        assert lock._fd is None


def test_git_mutex_lock_release_on_exception(lock_path: Path) -> None:
    """Lock is released even if body raises an exception."""
    lock = GitMutexLock(lock_path=lock_path, timeout=5.0)

    with pytest.raises(ValueError):
        with lock:
            raise ValueError("test error")

    # Lock must have been released
    assert lock._fd is None
    assert not lock_path.exists()


# ===========================================================================
# 2. Timeout when lock is held
# ===========================================================================


def test_git_mutex_lock_timeout_when_held(lock_path: Path) -> None:
    """TimeoutError is raised when the lock cannot be acquired within the timeout."""
    holder = GitMutexLock(lock_path=lock_path, timeout=10.0)
    contender = GitMutexLock(lock_path=lock_path, timeout=0.1, retry_interval=0.02)

    ready = threading.Event()
    release_signal = threading.Event()

    def hold_lock() -> None:
        with holder:
            ready.set()
            release_signal.wait(timeout=5.0)

    t = threading.Thread(target=hold_lock, daemon=True)
    t.start()
    ready.wait(timeout=3.0)

    try:
        with pytest.raises(TimeoutError, match="GitMutexLock"):
            contender.acquire()
    finally:
        release_signal.set()
        t.join(timeout=3.0)


def test_git_mutex_lock_timeout_message_includes_path(lock_path: Path) -> None:
    """TimeoutError message includes the lock file path for diagnostics."""
    holder = GitMutexLock(lock_path=lock_path, timeout=10.0)
    contender = GitMutexLock(lock_path=lock_path, timeout=0.05, retry_interval=0.01)

    ready = threading.Event()
    release_signal = threading.Event()

    def hold_lock() -> None:
        with holder:
            ready.set()
            release_signal.wait(timeout=5.0)

    t = threading.Thread(target=hold_lock, daemon=True)
    t.start()
    ready.wait(timeout=3.0)

    try:
        with pytest.raises(TimeoutError) as exc_info:
            contender.acquire()
        assert str(lock_path) in str(exc_info.value)
    finally:
        release_signal.set()
        t.join(timeout=3.0)


# ===========================================================================
# 3. Bypass when enabled=False
# ===========================================================================


def test_git_mutex_lock_disabled_is_noop(tmp_path: Path) -> None:
    """When enabled=False the lock never touches the filesystem."""
    lock_path = tmp_path / "should_not_exist.lock"
    lock = GitMutexLock(lock_path=lock_path, timeout=5.0, enabled=False)

    with lock:
        # No file should be created
        assert not lock_path.exists()
        assert lock._fd is None

    assert not lock_path.exists()


def test_git_mutex_lock_disabled_acquire_returns_self(tmp_path: Path) -> None:
    """acquire() on a disabled lock returns self immediately."""
    lock = GitMutexLock(lock_path=tmp_path / "x.lock", enabled=False)
    result = lock.acquire()
    assert result is lock
    lock.release()  # must not raise


# ===========================================================================
# 4. GitRatchetOptimizer bypass integration
# ===========================================================================


def test_optimizer_dry_run_bypasses_lock(minimal_config: RatchetConfig, tmp_path: Path) -> None:
    """When dry_run_git=True the optimizer creates a disabled lock."""
    minimal_config.dry_run_git = True
    opt = GitRatchetOptimizer(
        config=minimal_config,
        dry_run_git=True,
        project_root=tmp_path,
    )
    assert not opt.git_lock.enabled


def test_optimizer_lock_disabled_param_bypasses_lock(
    minimal_config: RatchetConfig, tmp_path: Path
) -> None:
    """When lock_enabled=False the optimizer creates a disabled lock even in non-dry-run mode."""
    # force a git dir to exist so project_root detection works cleanly
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    opt = GitRatchetOptimizer(
        config=minimal_config,
        dry_run_git=False,
        project_root=tmp_path,
        lock_enabled=False,
    )
    assert not opt.git_lock.enabled


def test_optimizer_injected_lock_is_used(minimal_config: RatchetConfig, tmp_path: Path) -> None:
    """A custom GitMutexLock injected via git_lock= is wired into the optimizer."""
    custom_lock = GitMutexLock(enabled=False)
    opt = GitRatchetOptimizer(
        config=minimal_config,
        dry_run_git=True,
        project_root=tmp_path,
        git_lock=custom_lock,
    )
    assert opt.git_lock is custom_lock


def test_optimizer_lock_path_auto_resolved(minimal_config: RatchetConfig, tmp_path: Path) -> None:
    """Lock path defaults to <project_root>/.git/evals_tuner.lock when not injected."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    opt = GitRatchetOptimizer(
        config=minimal_config,
        dry_run_git=False,
        project_root=tmp_path,
        lock_enabled=True,
    )
    assert opt.git_lock.lock_path == tmp_path / ".git" / "evals_tuner.lock"


def test_optimizer_git_commit_uses_lock(minimal_config: RatchetConfig, tmp_path: Path) -> None:
    """git_commit_improvement acquires and releases the lock around the git call."""
    lock_path = tmp_path / "test.lock"
    lock = GitMutexLock(lock_path=lock_path, timeout=5.0)
    opt = GitRatchetOptimizer(
        config=minimal_config,
        dry_run_git=True,
        project_root=tmp_path,
        git_lock=lock,
    )

    result = opt.git_commit_improvement("+5%")
    assert result is True
    # Lock file should be cleaned up after commit
    assert not lock_path.exists()


def test_optimizer_git_rollback_uses_lock(minimal_config: RatchetConfig, tmp_path: Path) -> None:
    """git_rollback_target acquires and releases the lock around the rollback."""
    lock_path = tmp_path / "rollback.lock"
    lock = GitMutexLock(lock_path=lock_path, timeout=5.0)
    opt = GitRatchetOptimizer(
        config=minimal_config,
        dry_run_git=True,
        project_root=tmp_path,
        git_lock=lock,
    )

    original = "# Skill\n\nOriginal content.\n"
    minimal_config.target_file.write_text(original, encoding="utf-8")
    opt.git_rollback_target(original, has_committed=False)

    # Content should be restored
    assert minimal_config.target_file.read_text(encoding="utf-8") == original
    assert not lock_path.exists()
