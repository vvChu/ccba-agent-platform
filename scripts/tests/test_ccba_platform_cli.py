"""Unit tests for Unified CCBA Platform CLI (scripts/ccba_platform_cli.py)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.ccba_platform_cli import build_parser, execute_ingest_legal, main


def test_cli_parser_help_and_subcommands() -> None:
    """Verify that the parser includes adopt-spoke, sync-spoke, and ingest-legal."""
    parser = build_parser()
    subparsers_actions = [action for action in parser._actions if action.dest == "command"]
    assert len(subparsers_actions) == 1
    choices = subparsers_actions[0].choices
    assert "adopt-spoke" in choices
    assert "sync-spoke" in choices
    assert "ingest-legal" in choices
    assert "doc-audit" in choices


def test_execute_ingest_legal_mock_flow() -> None:
    """Test 4-step autonomous ingestion protocol in mock mode (ADR 0039)."""
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")

        mock_spoke_cli = scripts_dir / "spoke_cli.py"
        mock_spoke_cli.write_text(
            "import sys\nprint('MOCK SPOKE INGEST')\nsys.exit(0)\n",
            encoding="utf-8",
        )

        with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Mocked Ingest Success", stderr=""
            )

            res = execute_ingest_legal(
                url="https://thuvienphapluat.vn/van-ban/mock-law-123.aspx",
                spoke_path=spoke_dir,
                doc_type="vbpl",
                mock=True,
            )

            assert res is True
            # Verify subprocess.run called for spoke_cli.py ingest & validate
            assert mock_run.call_count >= 1


def test_main_cli_dispatch_ingest_legal() -> None:
    """Test main CLI entrypoint dispatching ingest-legal command."""
    with patch("scripts.ccba_platform_cli.execute_ingest_legal", return_value=True) as mock_ingest:
        with patch("sys.argv", ["ccba-platform", "ingest-legal", "https://tvpl.vn/test", "--mock"]):
            exit_code = main()
            assert exit_code == 0
            mock_ingest.assert_called_once()
