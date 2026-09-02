"""Unit tests for crawler multi-attachment discovery and download."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ccba_legal.crawler.tier_downloader import trigger_download


@pytest.mark.unit
def test_trigger_download_discovers_attachments(tmp_path: Path):
    """Test that trigger_download discovers and registers tab=7 standalone attachments."""
    mock_cdp = MagicMock()

    def mock_eval(js: str):
        if "hasAttachExt" in js or "attachLinks" in js:
            return [
                {
                    "text": "Phụ lục 1 Bảng tính định mức.xlsx",
                    "href": "https://files.tvpl.vn/att1.xlsx",
                },
                {
                    "text": "Mẫu số 02 Tờ trình đề nghị.docx",
                    "href": "https://files.tvpl.vn/att2.docx",
                },
            ]
        if "window.location.href" in js:
            return "https://thuvienphapluat.vn/van-ban/Xay-dung/test-doc-12345.aspx?tab=7"
        if "tải văn bản tiếng việt" in js or "docx=1" in js:
            # Simulate downloaded file appearing
            (tmp_path / "downloaded_temp.docx").write_bytes(b"PK\x03\x04")
            return "Clicked DOCX"
        if "tải bản pdf" in js or "part=-100" in js:
            return "Clicked PDF"
        return ""

    mock_cdp.evaluate_js.side_effect = mock_eval

    res = trigger_download(
        cdp=mock_cdp,
        download_dir=tmp_path,
        slug_name="test_doc",
        format_type="docx",
        download_attachments=True,
    )

    assert res["success"] is True
    assert "attachments" in res
    assert len(res["attachments"]) == 2
    assert any("xlsx" in att for att in res["attachments"])
    assert any("docx" in att for att in res["attachments"])
