"""Unit and integration tests for TVPL VIP crawler resilience and tier priority."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccba_legal.cli import handle_login
from ccba_legal.crawler.tier_downloader import _wait_for_download, trigger_download
from ccba_legal.session import get_browser_executable_path


def _eval_js_with_links(links_json: str) -> dict:
    """Helper to evaluate the actual crawler PDF search JS logic in node."""
    js_script = f"""
    const links = {links_json}.map(l => ({{
        ...l,
        getAttribute: (attr) => l[attr] || null,
        click: () => {{ l._clicked = true; }}
    }}));
    const document = {{
        querySelectorAll: (sel) => sel === 'a' ? links : []
    }};

    const result = (() => {{
        let all_links = Array.from(document.querySelectorAll('a'));
        // Pass 1: Tier 1 - VIP Born-Digital Vector Searchable PDF (part=-100 or #filePDFHyperLink)
        let a_tier1 = all_links.find(lnk => {{
            let id = (lnk.id || '').toLowerCase();
            let h = (lnk.href || '').toLowerCase();
            return id.includes('filepdfhyperlink') || h.includes('part=-100');
        }});
        if (a_tier1) {{
            let href_val = (a_tier1.getAttribute('href') || a_tier1.href || '').trim();
            if (href_val.toLowerCase().startsWith('javascript:')) {{
                try {{ eval(decodeURIComponent(href_val.replace(/^javascript:/i, ''))); }}
                catch(e) {{ a_tier1.click(); }}
            }} else {{
                a_tier1.click();
            }}
            return {{ clicked: true, tier: 1, href: a_tier1.href || a_tier1.innerText }};
        }}
        // Pass 2: Tier 3 - Gazette Scan / Photocopy PDF Fallback (part=0 or #vietnameseHyperLink_Pdf)
        let a_tier3 = all_links.find(lnk => {{
            let t = (lnk.innerText || '').toLowerCase();
            let h = (lnk.href || '').toLowerCase();
            let id = (lnk.id || '').toLowerCase();
            return id.includes('vietnamesehyperlink_pdf') ||
                   (t.includes('tải') && t.includes('bản pdf')) ||
                   (t.includes('tải') && t.includes('văn bản gốc')) ||
                   h.includes('part=0');
        }});
        if (!a_tier3) {{
            a_tier3 = all_links.find(lnk => {{
                let h = (lnk.href || '').toLowerCase();
                return h.endsWith('.pdf') || h.includes('.pdf?');
            }});
        }}
        if (a_tier3) {{
            let href_val = (a_tier3.getAttribute('href') || a_tier3.href || '').trim();
            if (href_val.toLowerCase().startsWith('javascript:')) {{
                try {{ eval(decodeURIComponent(href_val.replace(/^javascript:/i, ''))); }}
                catch(e) {{ a_tier3.click(); }}
            }} else {{
                a_tier3.click();
            }}
            return {{ clicked: true, tier: 3, href: a_tier3.href || a_tier3.innerText }};
        }}
        return {{ clicked: false, tier: null, href: null }};
    }})();

    console.log(JSON.stringify(result));
    """
    proc = subprocess.run(["node", "-e", js_script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout.strip())


@patch("ccba_legal.crawler.tier_downloader.sleep_with_jitter")
def test_pdf_click_prefers_part_minus_100_over_part_zero(mock_sleep, tmp_path: Path):
    """Test 1: Verify Pass 1 prioritizes Born-Digital Vector PDF (part=-100) even when part=0 comes first."""
    # 1. Verify JS evaluation logic directly in Node
    links = [
        {"id": "vietnameseHyperLink_Pdf", "href": "https://tvpl.vn/download.aspx?part=0", "innerText": "Tải bản PDF"},
        {"id": "filePDFHyperLink", "href": "https://tvpl.vn/download.aspx?part=-100", "innerText": "Tải văn bản gốc PDF"}
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
        {"id": "vietnameseHyperLink_Docx", "href": "https://tvpl.vn/download.aspx?part=1", "innerText": "Tải bản Word"},
        {"id": "vietnameseHyperLink_Pdf", "href": "https://tvpl.vn/download.aspx?part=0", "innerText": "Tải bản PDF"}
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

    # Test failure when no browser is found
    with patch("ccba_legal.session.get_browser_executable_path", return_value=None):
        args = argparse.Namespace(port=9222, url="https://thuvienphapluat.vn")
        rc_fail = handle_login(args)
        assert rc_fail == 1
