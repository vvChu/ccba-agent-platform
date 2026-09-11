"""test_harness_fallback.py - Tests for graceful fallback and lazy loading when ccba-harness is absent.

Verifies Issue #252 resolution:
1. Isolated `ccba_ai` import without ccba_harness in environment.
2. PEP 562 lazy-loading of `ccba_ai.services`.
3. Concurrency mutual exclusion of SimpleFileLock.
4. Stale lock expiration and recovery.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from ccba_ai.services._lock_fallback import SimpleFileLock


def test_isolated_ai_import_without_harness() -> None:
    """Verify that importing ccba_ai without ccba_harness succeeds and does not eager-load services."""
    code = (
        "import sys\n"
        "sys.modules['ccba_harness'] = None\n"
        "import ccba_ai\n"
        "from ccba_ai import ai\n"
        "assert ai is not None\n"
        "# Ensure services was NOT eagerly imported\n"
        "assert 'ccba_ai.services' not in sys.modules\n"
        "print('ISOLATED_IMPORT_SUCCESS')\n"
    )
    res = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0, f"Import failed with stderr: {res.stderr}"
    assert "ISOLATED_IMPORT_SUCCESS" in res.stdout


def test_pep562_lazy_services_access() -> None:
    """Verify PEP 562 lazy loading of ccba_ai.services, __dir__ autocomplete and AttributeError."""
    import ccba_ai

    # 1. Autocomplete / introspection support via __dir__
    assert "services" in dir(ccba_ai)

    # 2. Lazy attribute access
    services = ccba_ai.services
    assert services is not None
    assert hasattr(services, "create_plan")
    assert hasattr(services, "add_task")

    # 3. Non-existent attribute raises AttributeError
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent_symbol'"):
        _ = ccba_ai.nonexistent_symbol


def test_lock_fallback_mutual_exclusion() -> None:
    """Verify SimpleFileLock mutual exclusion and timeout when lock is held."""
    with TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / "test.lock"

        lock1 = SimpleFileLock(lock_file, timeout=0.5, retry_interval=0.02)
        lock2 = SimpleFileLock(lock_file, timeout=0.1, retry_interval=0.02)

        with lock1:
            assert lock1.is_locked
            assert lock_file.exists()

            # lock2 must fail while lock1 is held
            with pytest.raises(TimeoutError):
                with lock2:
                    pass

        # After lock1 releases, lock2 must acquire successfully
        assert not lock1.is_locked
        assert not lock_file.exists()

        with lock2:
            assert lock2.is_locked
            assert lock_file.exists()


def test_stale_lock_recovery() -> None:
    """Verify SimpleFileLock detects and recovers from stale lock files older than expire_seconds."""
    with TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / "stale.lock"

        # Manually create a stale lock file with an old timestamp
        lock_file.write_text("99999:0.0", encoding="utf-8")
        past_time = time.time() - 300.0  # 5 minutes ago
        os.utime(lock_file, (past_time, past_time))

        # Acquire lock with 60s expiration
        lock = SimpleFileLock(lock_file, timeout=1.0, expire_seconds=60.0)
        with lock:
            assert lock.is_locked
            assert lock_file.exists()

        # Clean release
        assert not lock.is_locked
        assert not lock_file.exists()


def test_services_execution_without_harness() -> None:
    """Verify plan creation works cleanly using SimpleFileLock in harness-free subshell."""
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from tempfile import TemporaryDirectory\n"
        "sys.modules['ccba_harness'] = None\n"
        "import ccba_ai.services as services\n"
        "with TemporaryDirectory() as tmp:\n"
        "    res = services.create_plan(\n"
        "        title='Test Plan',\n"
        "        phases_list=['Phase 1', 'Phase 2'],\n"
        "        workspace_root=Path(tmp)\n"
        "    )\n"
        "    assert res.status == 'success'\n"
        "    assert len(res.created_files) > 0\n"
        "    # Test team task addition under fallback lock\n"
        "    task = services.add_task(name='Test Task', workspace_root=Path(tmp))\n"
        "    assert task.name == 'Test Task'\n"
        "    print('SERVICES_EXECUTION_SUCCESS')\n"
    )
    res = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0, f"Plan creation failed with stderr: {res.stderr}"
    assert "SERVICES_EXECUTION_SUCCESS" in res.stdout
