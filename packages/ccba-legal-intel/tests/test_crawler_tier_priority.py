"""Unit and integration tests for TVPL VIP crawler resilience and tier priority."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from ccba_legal.cli import handle_login
from ccba_legal.crawler.tier_downloader import _wait_for_download, trigger_download
from ccba_legal.session import get_browser_executable_path


def _eval_js_with_links(links_json: str) -> dict:
    """Helper to evaluate the actual crawler PDF search JS logic in node."""
    from ccba_legal.crawler.tier_downloader import PDF_FINDER_JS

    js_script = f"""
    const links = {links_json}.map(l => ({{
        ...l,
        getAttribute: (attr) => l[attr] || null,
        click: () => {{ l._clicked = true; }}
    }}));
    const document = {{
        querySelectorAll: (sel) => sel === 'a' ? links : []
    }};

    const result = {PDF_FINDER_JS.strip()};

    console.log(JSON.stringify(result));
    """
    proc = subprocess.run(["node", "-e", js_script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout.strip())


@patch("ccba_legal.crawler.tier_downloader.sleep_with_jitter")
def test_pdf_click_prefers_part_minus_100_over_part_zero(mock_sleep, tmp_path: Path):
    """Test 1: Verify Pass 1 prioritizes Born-Digital Vector PDF (part=-100) even when part=0 comes first."""
    # 1. Verify JS evaluation logic directly in Node
    links = [
        {
            "id": "vietnameseHyperLink_Pdf",
            "href": "https://tvpl.vn/download.aspx?part=0",
            "innerText": "Tải bản PDF",
        },
        {
            "id": "filePDFHyperLink",
            "href": "https://tvpl.vn/download.aspx?part=-100",
            "innerText": "Tải văn bản gốc PDF",
        },
    ]
    res_js = _eval_js_with_links(json.dumps(links))
    assert res_js["clicked"] is True
    assert res_js["tier"] == 1
    assert "part=-100" in res_js["href"]

    # 2. Verify trigger_download records pdf_tier=1
    mock_cdp = MagicMock()

    def mock_eval(js: str):
        if "has_docx" in js or "has_pdf" in js:
            return {"has_docx": False, "has_pdf": True, "pdf_tier": 1}
        if "all_links.find" in js:
            # Simulate download appearing on click
            (tmp_path / "born_digital_temp.pdf").write_bytes(b"%PDF-1.4 mock born-digital pdf")
            return {"clicked": True, "tier": 1, "href": "https://tvpl.vn/download.aspx?part=-100"}
        return "https://thuvienphapluat.vn/doc.aspx?tab=7"

    mock_cdp.evaluate_js.side_effect = mock_eval

    res = trigger_download(
        cdp=mock_cdp,
        download_dir=tmp_path,
        slug_name="test_doc",
        format_type="pdf",
        download_attachments=False,
    )
    assert res["success"] is True
    assert res["pdf_tier"] == 1


@patch("ccba_legal.crawler.tier_downloader.sleep_with_jitter")
def test_pdf_click_falls_back_to_part_zero(mock_sleep, tmp_path: Path):
    """Test 2: Verify Pass 2 successfully falls back to Gazette Scan (part=0) when part=-100 is absent."""
    # 1. Verify JS evaluation logic directly in Node
    links = [
        {
            "id": "vietnameseHyperLink_Docx",
            "href": "https://tvpl.vn/download.aspx?part=1",
            "innerText": "Tải bản Word",
        },
        {
            "id": "vietnameseHyperLink_Pdf",
            "href": "https://tvpl.vn/download.aspx?part=0",
            "innerText": "Tải bản PDF",
        },
    ]
    res_js = _eval_js_with_links(json.dumps(links))
    assert res_js["clicked"] is True
    assert res_js["tier"] == 3
    assert "part=0" in res_js["href"]

    # 2. Verify trigger_download records pdf_tier=3
    mock_cdp = MagicMock()

    def mock_eval(js: str):
        if "has_docx" in js or "has_pdf" in js:
            return {"has_docx": False, "has_pdf": True, "pdf_tier": 3}
        if "all_links.find" in js:
            (tmp_path / "scan_temp.pdf").write_bytes(b"%PDF-1.4 mock gazette scan pdf")
            return {"clicked": True, "tier": 3, "href": "https://tvpl.vn/download.aspx?part=0"}
        return "https://thuvienphapluat.vn/doc.aspx?tab=7"

    mock_cdp.evaluate_js.side_effect = mock_eval

    res = trigger_download(
        cdp=mock_cdp,
        download_dir=tmp_path,
        slug_name="test_scan",
        format_type="pdf",
        download_attachments=False,
    )
    assert res["success"] is True
    assert res["pdf_tier"] == 3


@patch("ccba_legal.crawler.tier_downloader.sleep_with_jitter")
def test_tcvn_url_does_not_force_tab_7(mock_sleep, tmp_path: Path):
    """Test 3: Verify TCVN URLs do not navigate to ?tab=7 and do not cause UnboundLocalError."""
    mock_cdp = MagicMock()
    navigated_urls: list[str] = []
    evaluated_js: list[str] = []

    def mock_navigate(url: str):
        navigated_urls.append(url)

    def mock_eval(js: str):
        evaluated_js.append(js)
        if "window.location.href" in js:
            return "https://thuvienphapluat.vn/TCVN/Xay-dung/TCVN-1234-2023.aspx"
        if "has_docx" in js:
            return {"has_docx": False, "has_pdf": False, "pdf_tier": None}
        return ""

    mock_cdp.navigate.side_effect = mock_navigate
    mock_cdp.evaluate_js.side_effect = mock_eval
    mock_cdp.handle_login.return_value = False

    tcvn_url = "https://thuvienphapluat.vn/TCVN/Xay-dung/TCVN-1234-2023.aspx"
    res = trigger_download(
        cdp=mock_cdp,
        download_dir=tmp_path,
        slug_name="tcvn_1234_2023",
        format_type="both",
        download_attachments=False,
        doc_url=tcvn_url,
    )

    # Must NOT have navigated to ?tab=7
    for u in navigated_urls:
        assert "?tab=7" not in u
        assert "tab=7" not in u

    # Must have evaluated the client-side tab switcher #aTabTaiVe
    assert any("#aTabTaiVe" in js for js in evaluated_js)
    assert res["success"] is False
    assert res.get("pdf_tier") is None


def test_wait_for_download_detects_mtime_update_with_oserror_handling(tmp_path: Path):
    """Test 4: Verify _wait_for_download detects mtime update and handles transient OSError safely."""
    test_file = tmp_path / "document.docx"
    test_file.write_bytes(b"initial content")

    # Put file into existing_downloads
    existing = {str(test_file.resolve())}

    start_time = time.time()
    time.sleep(0.05)

    # Update file content and mtime
    test_file.write_bytes(b"updated PK\x03\x04 content")
    os.utime(test_file, (start_time + 1.0, start_time + 1.0))

    found = _wait_for_download(
        watch_dirs=[tmp_path],
        existing_downloads=existing,
        expected_exts=[".docx"],
        timeout=2.0,
        start_time=start_time,
    )
    assert found is not None
    assert found.resolve() == test_file.resolve()

    # Test transient OSError handling (e.g. file unlinked between glob and stat)
    orig_stat = Path.stat

    def mock_stat(self, *args, **kwargs):
        if self.name.endswith(".docx"):
            raise FileNotFoundError("Simulated disappearing file")
        return orig_stat(self, *args, **kwargs)

    with patch.object(Path, "stat", side_effect=mock_stat, autospec=True):
        found_err = _wait_for_download(
            watch_dirs=[tmp_path],
            existing_downloads=set(),
            expected_exts=[".docx"],
            timeout=0.6,
            start_time=time.time(),
        )
        assert found_err is None


def test_login_finds_cross_platform_browser():
    """Test 5: Verify handle_login cross-platform resolution and headless warning."""
    # Test get_browser_executable_path returns a string on this machine
    detected = get_browser_executable_path()
    assert detected is not None
    assert Path(detected).exists()

    # Test handle_login uses detected browser without crashing
    with patch("subprocess.Popen") as mock_popen:
        args = argparse.Namespace(port=9222, url="https://thuvienphapluat.vn")
        rc = handle_login(args)
        assert rc == 0
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert cmd[0] == detected
        assert "--remote-debugging-port=9222" in cmd[1]

    # Test headless warning when DISPLAY is absent on Linux
    with patch("subprocess.Popen"):
        with patch.dict(os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}):
            with patch(
                "ccba_legal.session.get_browser_executable_path",
                return_value="/usr/bin/google-chrome",
            ):
                args = argparse.Namespace(port=9222, url="https://thuvienphapluat.vn")
                with patch("builtins.print") as mock_print:
                    rc = handle_login(args)
                    assert rc == 0
                    printed_text = " ".join(
                        str(call.args[0]) for call in mock_print.call_args_list if call.args
                    )
                    assert "headless" in printed_text.lower() or "display" in printed_text.lower()

    # Test failure when no browser is found
    with patch("ccba_legal.session.get_browser_executable_path", return_value=None):
        args = argparse.Namespace(port=9222, url="https://thuvienphapluat.vn")
        rc_fail = handle_login(args)
        assert rc_fail == 1


def test_handle_ingest_tier3_dual_pdf_workflow(tmp_path: Path):
    """Test 6: Verify handle_ingest ADR 0043 Dual-PDF workflow on Tier 3 Gazette Scan."""
    import hashlib

    import yaml

    from ccba_legal.cli import handle_ingest

    doc_dir = tmp_path / "downloads"
    doc_dir.mkdir(parents=True, exist_ok=True)
    mock_docx = doc_dir / "test_doc.docx"
    mock_docx.write_bytes(b"PK\x03\x04mock docx binary content")
    mock_scan_pdf = doc_dir / "test_doc_scan.pdf"
    mock_scan_pdf.write_bytes(b"%PDF-1.4 mock scan pdf content")

    out_bundle_dir = tmp_path / "legal_docs"

    mock_crawler = MagicMock()
    mock_crawler.fetch_document.return_value = {
        "docx_path": str(mock_docx),
        "pdf_path": str(mock_scan_pdf),
        "pdf_tier": 3,
        "title": "Nghị định Test",
        "document_number": "999/2026/NĐ-CP",
    }

    def fake_convert_docx(docx_path, target_bundle_dir, doc_type=None):
        target_bundle_dir.mkdir(parents=True, exist_ok=True)
        meta_content = {
            "id": target_bundle_dir.name,
            "document_number": "999/2026/NĐ-CP",
            "type": "Nghị định",
            "okf_spec": "v2.4 Universal",
        }
        with open(target_bundle_dir / "metadata.yaml", "w", encoding="utf-8") as f:
            yaml.dump(meta_content, f)
        return {"status": "success"}

    def fake_convert_to_pdf(docx_path, pdf_path):
        Path(pdf_path).write_bytes(b"%PDF-1.4 born-digital vector rendered pdf")

    with (
        patch("ccba_legal.cli.TVPLCrawler", return_value=mock_crawler),
        patch("ccba_legal.cli.convert_docx_to_okf_bundle", side_effect=fake_convert_docx),
        patch("ccba_ooxml.converter.convert_to_pdf", side_effect=fake_convert_to_pdf),
        patch("ccba_legal.cli.GoldStandardProcessor"),
        patch("ccba_legal.linter.lint_target_path", return_value={"total_errors": 0}),
    ):
        args = argparse.Namespace(
            target="https://thuvienphapluat.vn/van-ban/test-doc",
            category="01_vbpl",
            slug="test_dual_pdf_slug",
            output_dir=out_bundle_dir,
            upload_drive=False,
        )
        rc = handle_ingest(args)
        assert rc == 0

    target_bundle = out_bundle_dir / "01_vbpl" / "test_dual_pdf_slug"
    sources_dir = target_bundle / "sources"
    raw_scan = sources_dir / "test_dual_pdf_slug_raw_scan.pdf"
    vector_pdf = sources_dir / "test_dual_pdf_slug.pdf"

    assert raw_scan.exists()
    assert raw_scan.read_bytes() == b"%PDF-1.4 mock scan pdf content"
    assert vector_pdf.exists()
    assert vector_pdf.read_bytes() == b"%PDF-1.4 born-digital vector rendered pdf"

    with open(target_bundle / "metadata.yaml", encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    assert meta["pdf_origin"] == "docx_vector_rendered"
    assert meta["raw_scan_pdf"] == "sources/test_dual_pdf_slug_raw_scan.pdf"
    assert (
        meta["pdf_sha256"]
        == hashlib.sha256(b"%PDF-1.4 born-digital vector rendered pdf").hexdigest()
    )
    assert "source_assets" in meta
    assert meta["source_assets"]["pdf"]["origin"] == "docx_vector_rendered"
    assert (
        meta["source_assets"]["raw_scan"]["sha256"]
        == hashlib.sha256(b"%PDF-1.4 mock scan pdf content").hexdigest()
    )


def test_handle_ingest_tier3_conversion_failure_fallback(tmp_path: Path):
    """Test 7: Verify handle_ingest safely falls back to scan PDF when convert_to_pdf fails."""
    import yaml

    from ccba_legal.cli import handle_ingest

    doc_dir = tmp_path / "downloads"
    doc_dir.mkdir(parents=True, exist_ok=True)
    mock_docx = doc_dir / "test_fail.docx"
    mock_docx.write_bytes(b"PK\x03\x04mock docx")
    mock_scan_pdf = doc_dir / "test_fail_scan.pdf"
    mock_scan_pdf.write_bytes(b"%PDF-1.4 scan fallback pdf")

    out_bundle_dir = tmp_path / "legal_docs"

    mock_crawler = MagicMock()
    mock_crawler.fetch_document.return_value = {
        "docx_path": str(mock_docx),
        "pdf_path": str(mock_scan_pdf),
        "pdf_tier": 3,
        "title": "Nghị định Fallback",
        "document_number": "1000/2026/NĐ-CP",
    }

    def fake_convert_docx(docx_path, target_bundle_dir, doc_type=None):
        target_bundle_dir.mkdir(parents=True, exist_ok=True)
        meta_content = {
            "id": target_bundle_dir.name,
            "document_number": "1000/2026/NĐ-CP",
            "type": "Nghị định",
        }
        with open(target_bundle_dir / "metadata.yaml", "w", encoding="utf-8") as f:
            yaml.dump(meta_content, f)
        return {"status": "success"}

    def fake_convert_error(docx_path, pdf_path):
        raise RuntimeError("LibreOffice process crashed")

    with (
        patch("ccba_legal.cli.TVPLCrawler", return_value=mock_crawler),
        patch("ccba_legal.cli.convert_docx_to_okf_bundle", side_effect=fake_convert_docx),
        patch("ccba_ooxml.converter.convert_to_pdf", side_effect=fake_convert_error),
        patch("ccba_legal.cli.GoldStandardProcessor"),
        patch("ccba_legal.linter.lint_target_path", return_value={"total_errors": 0}),
    ):
        args = argparse.Namespace(
            target="https://thuvienphapluat.vn/van-ban/test-fail",
            category="01_vbpl",
            slug="test_fallback_slug",
            output_dir=out_bundle_dir,
            upload_drive=False,
        )
        rc = handle_ingest(args)
        assert rc == 0

    target_bundle = out_bundle_dir / "01_vbpl" / "test_fallback_slug"
    sources_dir = target_bundle / "sources"
    raw_scan = sources_dir / "test_fallback_slug_raw_scan.pdf"
    target_pdf = sources_dir / "test_fallback_slug.pdf"

    # Should fall back to scan PDF and not leave orphaned raw_scan
    assert not raw_scan.exists()
    assert target_pdf.exists()
    assert target_pdf.read_bytes() == b"%PDF-1.4 scan fallback pdf"

    with open(target_bundle / "metadata.yaml", encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    assert meta.get("pdf_origin") != "docx_vector_rendered"
