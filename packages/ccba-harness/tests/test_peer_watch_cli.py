"""packages/ccba-harness/tests/test_peer_watch_cli.py - Unit tests for ccba-harness peer-watch CLI.

Validates:
1. CLI help flag and subparser dispatching.
2. Default single-scan execution mode (--once).
3. Upward root discovery and custom directory resolution.
4. Continuous watch loop with graceful exit on KeyboardInterrupt / SystemExit.
5. Delegation parity in scripts/peer_bridge_watcher.py.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ccba_harness.cli import (
    find_workspace_root,
    main,
    resolve_peer_exchange_dir,
    run_peer_watch_cli,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_main_peer_watch_help_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that `ccba-harness peer-watch --help` displays usage and exits with 0."""
    with pytest.raises(SystemExit) as exc_info:
        main(["peer-watch", "--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage: ccba-harness peer-watch" in captured.out
    assert "--once" in captured.out
    assert "--watch" in captured.out
    assert "--interval" in captured.out
    assert "--auto-gate" in captured.out
    assert "--auto-grok" in captured.out
    assert "--dir" in captured.out
    assert "--root" in captured.out


def test_peer_watch_default_once_execution(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that default execution runs a single sync cycle and exits with 0."""
    peer_dir = tmp_path / ".md" / "peer_exchange"
    code = run_peer_watch_cli(["--dir", str(peer_dir)])
    assert code == 0
    captured = capsys.readouterr()
    assert "[OK] Bridge sync completed. Detected 0 change(s)." in captured.out
    assert peer_dir.exists()


def test_peer_watch_custom_dir_and_flags_passed_to_sync(tmp_path: Path) -> None:
    """Verify that custom dir and auto flags are passed to run_sync_cycle."""
    peer_dir = tmp_path / "custom_exchange"
    with patch("ccba_harness.peer.run_sync_cycle", return_value=[]) as mock_sync:
        code = run_peer_watch_cli(
            [
                "--dir",
                str(peer_dir),
                "--once",
                "--auto-gate",
                "--auto-grok",
            ]
        )
        assert code == 0
        mock_sync.assert_called_once_with(
            peer_dir.resolve(),
            auto_gate=True,
            auto_grok=True,
        )


def test_find_workspace_root_and_resolve_dir(tmp_path: Path) -> None:
    """Verify upward root discovery finds directory with .git or workspace_context.yaml."""
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    (project_root / ".git").mkdir()

    sub_dir = project_root / "packages" / "subpackage" / "src"
    sub_dir.mkdir(parents=True)

    found = find_workspace_root(sub_dir)
    assert found == project_root

    resolved_peer_dir = resolve_peer_exchange_dir(None, str(project_root))
    assert resolved_peer_dir == project_root / ".md" / "peer_exchange"
    assert resolved_peer_dir.exists()


def test_peer_watch_loop_graceful_exit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify continuous watch loop catches KeyboardInterrupt and flushes pending triggers."""
    peer_dir = tmp_path / ".md" / "peer_exchange"

    with (
        patch("ccba_harness.peer.run_sync_cycle", return_value=[]),
        patch("time.sleep", side_effect=KeyboardInterrupt),
        patch("ccba_harness.peer.flush_pending_peer_triggers") as mock_flush,
    ):
        code = run_peer_watch_cli(["--dir", str(peer_dir), "--watch", "--interval", "2"])
        assert code == 0
        mock_flush.assert_called_once_with(timeout=2.0)
        captured = capsys.readouterr()
        assert "Starting Peer Bridge Watcher" in captured.out
        assert "[OK] Peer watcher stopped cleanly." in captured.out


def test_main_fast_dispatch_and_script_delegation(tmp_path: Path) -> None:
    """Verify main() fast dispatch and scripts/peer_bridge_watcher delegation."""
    peer_dir = tmp_path / ".md" / "peer_exchange"

    with patch("ccba_harness.cli.run_peer_watch_cli", return_value=0) as mock_cli:
        code = main(["peer-watch", "--dir", str(peer_dir), "--once"])
        assert code == 0
        mock_cli.assert_called_once_with(["--dir", str(peer_dir), "--once"])

    # Test scripts/peer_bridge_watcher.py delegation
    from scripts import peer_bridge_watcher

    with patch("scripts.peer_bridge_watcher.run_peer_watch_cli", return_value=0) as mock_script_cli:
        code = peer_bridge_watcher.main(["--once"])
        assert code == 0
        mock_script_cli.assert_called_once_with(["--once"])
