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


def test_resolve_default_legal_spoke_discovery() -> None:
    """Test resolving legal spoke from registry, custom path, or fallback."""
    from scripts.ccba_platform_cli import resolve_default_legal_spoke

    # 1. Explicit existing path
    with tempfile.TemporaryDirectory() as tmp_dir:
        resolved = resolve_default_legal_spoke(tmp_dir)
        assert resolved == Path(tmp_dir)

    # 2. Registered spoke match
    mock_spokes = [
        {"name": "ccba-legal-knowledge", "path": "/mock/legal/path", "project_type": "Pháp điển"},
        {"name": "ccba-delivery", "path": "/mock/delivery/path", "project_type": "Quản lý"},
    ]
    with patch("scripts.spoke.decrypt_spoke_registry.get_registered_spokes", return_value=mock_spokes):
        # Match by specific name
        spoke_by_name = resolve_default_legal_spoke("ccba-legal-knowledge")
        assert spoke_by_name == Path("/mock/legal/path")

        # Automatic discovery by profile type
        auto_discovered = resolve_default_legal_spoke()
        assert auto_discovered == Path("/mock/legal/path")


def test_execute_ingest_legal_with_real_crawler_and_mutex() -> None:
    """Test ingest-legal invoking LegalIntelPipeline protected by TVPLSessionMutex."""
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        mock_pipeline_res = MagicMock(status="success", error=None)
        mock_pipeline = MagicMock()
        mock_pipeline.process_document.return_value = mock_pipeline_res

        with patch("ccba_legal.coordinator.LegalIntelPipeline", return_value=mock_pipeline):
            with patch("ccba_legal.crawler.TVPLSessionMutex.__enter__") as mock_mutex_enter:
                with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

                    res = execute_ingest_legal(
                        url="https://thuvienphapluat.vn/van-ban/nghi-dinh-217-2026.aspx",
                        spoke_path=spoke_dir,
                        mock=False,
                    )

                    assert res is True
                    mock_mutex_enter.assert_called_once()
                    mock_pipeline.process_document.assert_called_once()


def test_execute_ingest_legal_cloud_sync() -> None:
    """Test triggering LegalSyncEngine on cloud sync flag."""
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
            with patch("ccba_legal.sync.LegalSyncEngine") as mock_sync:
                res = execute_ingest_legal(
                    url="https://thuvienphapluat.vn/van-ban/test.aspx",
                    spoke_path=spoke_dir,
                    sync_cloud=True,
                    mock=True,
                )
                assert res is True
                mock_sync.assert_called_once()


def test_execute_ingest_legal_error_handling() -> None:
    """Test error handling when target spoke does not exist or spoke command fails."""
    # 1. Nonexistent spoke
    res = execute_ingest_legal(
        url="https://tvpl.vn/test",
        spoke_path=Path("/nonexistent/spoke/path"),
        mock=True,
    )
    assert res is False

    # 2. Spoke execution failure
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Validation Error")
            fail_res = execute_ingest_legal(
                url="https://tvpl.vn/test",
                spoke_path=spoke_dir,
                mock=True,
            )
            assert fail_res is False
