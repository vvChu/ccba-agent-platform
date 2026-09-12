"""Unit tests for scripts/hooks/session.py (SessionInitHook).

Verifies:
1. Workspace .md and extracted_docs directory creation.
2. Active mutex lock (< 300s) prevents spawning update checker.
3. Stale mutex lock (> 300s) is cleared and spawns update checker.
4. Update checker is spawned with --check-only and anchored to project root.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.hooks.base import HookContext
from scripts.hooks.session import SessionInitHook

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_session_init_creates_kb_dir(tmp_path: Path) -> None:
    """Verify SessionInitHook creates .md and extracted_docs folders."""
    hook = SessionInitHook()
    ctx = HookContext(event="session-init", cwd=str(tmp_path))

    with patch("subprocess.run", side_effect=subprocess.SubprocessError("Not a git repo")):
        res = hook.execute(ctx)
        assert res.exit_code == 0
        assert (tmp_path / ".md").exists()
        assert (tmp_path / ".md" / "extracted_docs").exists()


def test_session_init_active_mutex_lock_skips_checker(tmp_path: Path) -> None:
    """Verify active upstream sync lock skips triggering update checker."""
    scratch_dir = tmp_path / ".md" / "scratch"
    scratch_dir.mkdir(parents=True)
    lock_file = scratch_dir / "upstream_sync.lock"
    lock_file.write_text("pid: 12345", encoding="utf-8")

    hook = SessionInitHook()
    ctx = HookContext(event="session-init", cwd=str(tmp_path))

    with patch("subprocess.run", side_effect=subprocess.SubprocessError("Not a git repo")):
        with patch("subprocess.Popen") as mock_popen:
            res = hook.execute(ctx)
            assert res.exit_code == 0
            # Popen should NOT be called because lock is active
            mock_popen.assert_not_called()
            # Lock file still exists
            assert lock_file.exists()


def test_session_init_stale_mutex_lock_cleared_and_spawns_checker(tmp_path: Path) -> None:
    """Verify stale upstream sync lock (> 300s) is cleared and checker is triggered."""
    scratch_dir = tmp_path / ".md" / "scratch"
    scratch_dir.mkdir(parents=True)
    lock_file = scratch_dir / "upstream_sync.lock"
    lock_file.write_text("pid: 12345", encoding="utf-8")

    # Set mtime to 400 seconds ago
    stale_time = time.time() - 400
    os.utime(lock_file, (stale_time, stale_time))

    hook = SessionInitHook()
    ctx = HookContext(event="session-init", cwd=str(tmp_path))

    def mock_run_side_effect(cmd, **kwargs):
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = str(tmp_path) + "\n"
        return mock_res

    with patch("subprocess.run", side_effect=mock_run_side_effect):
        with patch("subprocess.Popen") as mock_popen:
            res = hook.execute(ctx)
            assert res.exit_code == 0
            assert not lock_file.exists()
            mock_popen.assert_called_once()
            call_args, call_kwargs = mock_popen.call_args
            assert "--check-only" in call_args[0]
            assert call_kwargs.get("cwd") == str(tmp_path)
