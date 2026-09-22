"""Unit tests for Unified CCBA Platform CLI (scripts/ccba_platform_cli.py)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.ccba_platform_cli import build_parser, execute_ingest_legal, main, sanitize_doc_slug


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
    with patch(
        "scripts.spoke.decrypt_spoke_registry.get_registered_spokes", return_value=mock_spokes
    ):
        # Match by specific name
        spoke_by_name = resolve_default_legal_spoke("ccba-legal-knowledge")
        assert spoke_by_name == Path("/mock/legal/path")

        # Automatic discovery by profile type
        auto_discovered = resolve_default_legal_spoke()
        assert auto_discovered == Path("/mock/legal/path")


def test_execute_ingest_legal_with_real_crawler_and_mutex() -> None:
    """Test ingest-legal invoking TVPLCrawler protected by TVPLSessionMutex."""
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        mock_crawler_res = {
            "title": "Nghị định 217/2026/NĐ-CP",
            "document_number": "217/2026/NĐ-CP",
            "docx_path": str(spoke_dir / "temp.docx"),
            "pdf_path": str(spoke_dir / "temp.pdf"),
            "status": "effective",
        }
        Path(mock_crawler_res["docx_path"]).write_text("dummy docx", encoding="utf-8")
        Path(mock_crawler_res["pdf_path"]).write_text("dummy pdf", encoding="utf-8")

        mock_crawler = MagicMock()
        mock_crawler.fetch_document.return_value = mock_crawler_res

        with patch("ccba_legal.crawler.TVPLCrawler", return_value=mock_crawler):
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
                    mock_crawler.fetch_document.assert_called_once()


def test_execute_ingest_legal_spoke_delegation_args() -> None:
    """Verify that execute_ingest_legal delegates docx, pdf, and metadata JSON to Spoke CLI."""
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

            res = execute_ingest_legal(
                url="https://thuvienphapluat.vn/van-ban/nghi-dinh-217-2026.aspx",
                spoke_path=spoke_dir,
                category="01_vbpl",
                mock=True,
            )

            assert res is True
            assert mock_run.call_count >= 2
            # Check ingest call arguments
            ingest_call_args = mock_run.call_args_list[0][0][0]
            assert "ingest" in ingest_call_args
            assert "-c" in ingest_call_args
            assert "01_vbpl" in ingest_call_args
            assert "--pdf-path" in ingest_call_args
            assert "--metadata" in ingest_call_args

            # Check validate call arguments and environment
            val_call_args = mock_run.call_args_list[1][0][0]
            assert "validate" in val_call_args
            assert "--bundle" in val_call_args
            val_call_kwargs = mock_run.call_args_list[1][1]
            assert val_call_kwargs.get("env", {}).get("CI") == "true"


def test_execute_ingest_legal_offline_mode() -> None:
    """Verify offline ingestion with pre-existing local docx and pdf files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        spoke_dir = tmp_path / "spoke"
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        local_docx = tmp_path / "offline.docx"
        local_docx.write_text("offline docx", encoding="utf-8")
        local_pdf = tmp_path / "offline.pdf"
        local_pdf.write_text("offline pdf", encoding="utf-8")

        with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

            res = execute_ingest_legal(
                url="offline_doc_test",
                spoke_path=spoke_dir,
                mock=False,
                docx=local_docx,
                pdf=local_pdf,
            )

            assert res is True
            ingest_call_args = mock_run.call_args_list[0][0][0]
            assert "ingest" in ingest_call_args
            assert "--pdf-path" in ingest_call_args
            assert "--metadata" in ingest_call_args


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


def test_sanitize_doc_slug() -> None:
    """Verify snake_case slug generation from various URL formats."""
    # TVPL decree URL with hyphens
    assert (
        sanitize_doc_slug(
            "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Nghi-dinh-217-2026-ND-CP.aspx"
        )
        == "nghi_dinh_217_2026_nd_cp"
    )
    # TCVN standard
    assert sanitize_doc_slug("TCVN-7336-2021") == "tcvn_7336_2021"
    # Special characters stripped and collapsed
    assert sanitize_doc_slug("Thong-Tu--01//2024..bxd") == "thong_tu_01_2024_bxd"


def test_execute_ingest_legal_offline_mode_missing_pdf() -> None:
    """Verify rejection when specified offline PDF does not exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        spoke_dir = tmp_path / "spoke"
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        local_docx = tmp_path / "doc.docx"
        local_docx.write_text("content", encoding="utf-8")

        res = execute_ingest_legal(
            url="test_doc",
            spoke_path=spoke_dir,
            mock=False,
            docx=local_docx,
            pdf=tmp_path / "nonexistent.pdf",
        )
        assert res is False


def test_execute_ingest_legal_adopts_crawler_slug() -> None:
    """Verify execute_ingest_legal adopts canonical slug returned by TVPLCrawler."""
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("laws: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        mock_crawler_res = {
            "title": "Nghị định 217/2026/NĐ-CP",
            "document_number": "217/2026/NĐ-CP",
            "slug": "nghi_dinh_217_2026_nd_cp_canonical",
            "docx_path": str(spoke_dir / "temp.docx"),
            "pdf_path": str(spoke_dir / "temp.pdf"),
            "status": "effective",
        }
        Path(mock_crawler_res["docx_path"]).write_text("dummy docx", encoding="utf-8")
        Path(mock_crawler_res["pdf_path"]).write_text("dummy pdf", encoding="utf-8")

        mock_crawler = MagicMock()
        mock_crawler.fetch_document.return_value = mock_crawler_res

        with patch("ccba_legal.crawler.TVPLCrawler", return_value=mock_crawler):
            with patch("ccba_legal.crawler.TVPLSessionMutex.__enter__"):
                with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

                    res = execute_ingest_legal(
                        url="https://thuvienphapluat.vn/van-ban/raw-url-title-12345.aspx",
                        spoke_path=spoke_dir,
                        mock=False,
                    )

                    assert res is True
                    # Spoke ingest should be called with canonical slug
                    ingest_args = mock_run.call_args_list[0][0][0]
                    assert "nghi_dinh_217_2026_nd_cp_canonical" in ingest_args


def test_execute_ingest_legal_category_standards() -> None:
    """Verify category 03_tcvn harmonizes doc_type to tcvn."""
    with tempfile.TemporaryDirectory() as tmp_spoke:
        spoke_dir = Path(tmp_spoke)
        scripts_dir = spoke_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "legal_registry.yaml").write_text("standards: []\n", encoding="utf-8")
        (scripts_dir / "spoke_cli.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        with patch("scripts.ccba_platform_cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

            res = execute_ingest_legal(
                url="tcvn_7336_2021",
                spoke_path=spoke_dir,
                category="03_tcvn",
                mock=True,
            )

            assert res is True
            ingest_args = mock_run.call_args_list[0][0][0]
            assert "-c" in ingest_args
            assert "03_tcvn" in ingest_args
            assert "-t" in ingest_args
            assert "tcvn" in ingest_args
