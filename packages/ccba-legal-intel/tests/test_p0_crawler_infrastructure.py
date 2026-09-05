"""Comprehensive unit tests for P0 crawler infrastructure enhancements."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import websocket

from ccba_legal.cdp import ChromeCDP
from ccba_legal.crawler.batch_crawler import TVPLBatchCrawler
from ccba_legal.crawler.engine import TVPLCrawlerEngine
from ccba_legal.crawler.tier_downloader import _wait_for_download, trigger_download


def test_tvpl_batch_crawler_init_with_output_dir(tmp_path: Path):
    """Test TVPLBatchCrawler accepts output_dir without TypeError."""
    custom_out = tmp_path / "custom_docs"
    crawler = TVPLBatchCrawler(output_dir=custom_out)
    assert crawler.output_dir == custom_out
    assert isinstance(crawler.engine, TVPLCrawlerEngine)


def test_tvpl_batch_crawler_init_default():
    """Test TVPLBatchCrawler default output_dir."""
    crawler = TVPLBatchCrawler()
    assert crawler.output_dir == Path(".md/extracted_docs")
    assert isinstance(crawler.engine, TVPLCrawlerEngine)


def test_tvpl_batch_crawler_with_custom_engine():
    """Test TVPLBatchCrawler preserves custom engine if provided."""
    mock_engine = MagicMock()
    mock_engine.fetch_doc.return_value = {"slug": "test", "relations": {}}
    crawler = TVPLBatchCrawler(crawler_engine=mock_engine)
    res = crawler.crawl_hierarchy("test_url", max_depth=0)
    assert "test" in res
    mock_engine.fetch_doc.assert_called_once_with("test_url")


def test_cdp_send_command_filters_async_events():
    """Test send_command filters out async events and matches exact req_id."""
    cdp = ChromeCDP(port=9222)
    mock_ws = MagicMock()
    cdp.ws = mock_ws

    sent_payloads = []

    def mock_send(msg):
        sent_payloads.append(json.loads(msg))

    mock_ws.send.side_effect = mock_send

    def mock_recv():
        req_id = sent_payloads[-1]["id"]
        if not hasattr(mock_recv, "call_count"):
            mock_recv.call_count = 0
        mock_recv.call_count += 1
        if mock_recv.call_count == 1:
            return json.dumps({"method": "Page.loadEventFired", "params": {"timestamp": 123}})
        if mock_recv.call_count == 2:
            return json.dumps({"id": 999999, "result": {"stale": True}})
        return json.dumps({"id": req_id, "result": {"success": True, "value": "matched"}})

    mock_ws.recv.side_effect = mock_recv

    resp = cdp.send_command("Custom.method", {"param1": "val1"}, timeout=5.0)
    assert resp.get("result", {}).get("value") == "matched"
    assert mock_recv.call_count == 3


def test_cdp_send_command_timeout():
    """Test send_command returns default payload on websocket timeout."""
    cdp = ChromeCDP(port=9222)
    mock_ws = MagicMock()
    cdp.ws = mock_ws
    mock_ws.recv.side_effect = websocket.WebSocketTimeoutException("Timeout")

    resp = cdp.send_command("Custom.method", {}, timeout=1.0)
    assert resp == {"result": {"value": None}}


def test_cdp_single_set_download_behavior_definition():
    """Test that ChromeCDP has only one set_download_behavior definition."""
    methods = [
        name
        for name, _ in inspect.getmembers(ChromeCDP, predicate=inspect.isfunction)
        if name == "set_download_behavior"
    ]
    assert len(methods) == 1


def test_wait_for_download_success(tmp_path: Path):
    """Test _wait_for_download detects complete file with size > 0."""
    target_file = tmp_path / "document.docx"
    target_file.write_bytes(b"PK\x03\x04valid_docx_content")

    found = _wait_for_download([tmp_path], set(), [".docx"], timeout=2.0)
    assert found is not None
    assert found.name == "document.docx"


def test_wait_for_download_ignores_crdownload_until_ready(tmp_path: Path):
    """Test _wait_for_download ignores crdownload while in progress."""
    cr_file = tmp_path / "document.docx.crdownload"
    cr_file.write_bytes(b"partial")

    found = _wait_for_download([tmp_path], set(), [".docx"], timeout=0.8)
    assert found is None

    # Simulate download completing
    cr_file.unlink()
    final_file = tmp_path / "document.docx"
    final_file.write_bytes(b"complete")

    found = _wait_for_download([tmp_path], set(), [".docx"], timeout=2.0)
    assert found is not None
    assert found.name == "document.docx"


def test_wait_for_download_ignores_zero_byte(tmp_path: Path):
    """Test _wait_for_download ignores 0-byte files."""
    empty_file = tmp_path / "document.docx"
    empty_file.write_bytes(b"")

    found = _wait_for_download([tmp_path], set(), [".docx"], timeout=0.8)
    assert found is None


def test_trigger_download_fast_fail_missing_docx(tmp_path: Path):
    """Test trigger_download fast-fails if requested format docx is not in DOM."""
    mock_cdp = MagicMock()
    mock_cdp.evaluate_js.return_value = {"has_docx": False, "has_pdf": True}

    res = trigger_download(
        cdp=mock_cdp,
        download_dir=tmp_path,
        slug_name="test_fast_fail",
        format_type="docx",
        download_attachments=False,
    )
    assert res["success"] is False
    assert res["error"] == "DOCX not available in tab=7"


def test_trigger_download_fast_fail_missing_pdf(tmp_path: Path):
    """Test trigger_download fast-fails if requested format pdf is not in DOM."""
    mock_cdp = MagicMock()
    mock_cdp.evaluate_js.return_value = {"has_docx": True, "has_pdf": False}

    res = trigger_download(
        cdp=mock_cdp,
        download_dir=tmp_path,
        slug_name="test_fast_fail_pdf",
        format_type="pdf",
        download_attachments=False,
    )
    assert res["success"] is False
    assert res["error"] == "PDF not available in tab=7"


def test_trigger_download_fast_fail_both_missing(tmp_path: Path):
    """Test trigger_download fast-fails if format_type=both and neither is available."""
    mock_cdp = MagicMock()
    mock_cdp.evaluate_js.return_value = {"has_docx": False, "has_pdf": False}

    res = trigger_download(
        cdp=mock_cdp,
        download_dir=tmp_path,
        slug_name="test_fast_fail_both",
        format_type="both",
        download_attachments=False,
    )
    assert res["success"] is False
    assert res["error"] == "Neither DOCX nor PDF available in tab=7"


def test_trigger_download_sequential_barrier_cooldown(tmp_path: Path):
    """Test Sequential Barrier triggers cooldown between Phase 1 and Phase 3."""
    mock_cdp = MagicMock()

    def mock_eval(js):
        if "has_docx" in js and "has_pdf" in js:
            return {"has_docx": True, "has_pdf": True}
        if (
            "Clicked PDF" in js
            or "vietnamesehyperlink_pdf" in js
            or "bản pdf" in js
            or "a_pdf" in js
        ):
            (tmp_path / "temp.pdf").write_bytes(b"%PDF-1.4")
            return "Clicked PDF"
        if "Clicked DOCX" in js or "docx" in js or "a_docx" in js:
            (tmp_path / "temp.docx").write_bytes(b"PK\x03\x04docx")
            return "Clicked DOCX"
        return ""

    mock_cdp.evaluate_js.side_effect = mock_eval

    with patch("time.sleep") as mock_sleep:
        res = trigger_download(
            cdp=mock_cdp,
            download_dir=tmp_path,
            slug_name="sequential_doc",
            format_type="both",
            download_attachments=False,
        )

        assert res["success"] is True
        assert res["docx_path"] is not None
        assert res["pdf_path"] is not None
        mock_sleep.assert_any_call(2.0)


def test_tvpl_batch_crawler_init_positional_path(tmp_path: Path):
    """Test TVPLBatchCrawler handles positional Path argument as output_dir."""
    custom_out = tmp_path / "positional_dir"
    crawler = TVPLBatchCrawler(custom_out)
    assert crawler.output_dir == custom_out
    assert isinstance(crawler.engine, TVPLCrawlerEngine)


def test_tvpl_batch_crawler_inherits_engine_output_dir(tmp_path: Path):
    """Test TVPLBatchCrawler inherits output_dir from custom TVPLCrawler facade."""
    from ccba_legal.crawler.engine import TVPLCrawler

    custom_out = tmp_path / "inherited_dir"
    facade = TVPLCrawler(output_dir=custom_out)
    crawler = TVPLBatchCrawler(crawler_engine=facade)
    assert crawler.output_dir == custom_out
    assert crawler.engine == facade.engine


def test_set_download_behavior_falls_back_to_page_when_browser_errors():
    """Test set_download_behavior falls back to Page target when Browser target returns CDP error."""
    cdp = ChromeCDP(port=9222)
    cdp.ws = MagicMock()

    sent_methods: list[str] = []

    def mock_send_command(method: str, params: dict, timeout: float = 15.0):
        sent_methods.append(method)
        if method == "Browser.setDownloadBehavior":
            return {"id": 1, "error": {"code": -32601, "message": "Browser method not found"}}
        if method == "Page.setDownloadBehavior":
            return {"id": 2, "result": {}}
        return {"result": {}}

    cdp.send_command = mock_send_command  # type: ignore[method-assign]

    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = False
        res = cdp.set_download_behavior("/tmp/download")

    assert res is True
    assert "Browser.setDownloadBehavior" in sent_methods
    assert "Page.setDownloadBehavior" in sent_methods


def test_cdp_navigate_resilient_to_closed_websocket():
    """Test navigate gracefully absorbs WebSocketConnectionClosed during navigation."""
    from ccba_legal.cdp import ChromeCDPError

    cdp = ChromeCDP(port=9222)
    cdp.ws = MagicMock()

    def mock_send_command(method: str, params: dict, timeout: float = 15.0):
        raise ChromeCDPError("WebSocket connection closed while sending CDP command Page.navigate")

    cdp.send_command = mock_send_command  # type: ignore[method-assign]

    # Should not raise exception
    cdp.navigate("https://thuvienphapluat.vn")


def test_trigger_download_skips_wait_when_click_returns_no_link(tmp_path: Path):
    """Test trigger_download does not hang for 30s when click functions return 'No DOCX/DOC link'."""
    mock_cdp = MagicMock()

    def mock_eval(js):
        if "has_docx" in js:
            return {"has_docx": True, "has_pdf": False}
        if "Clicked DOCX" in js or "all_links.find" in js:
            return "No DOCX/DOC link in tab=7"
        return ""

    mock_cdp.evaluate_js.side_effect = mock_eval

    with patch("ccba_legal.crawler.tier_downloader._wait_for_download") as mock_wait:
        res = trigger_download(
            cdp=mock_cdp,
            download_dir=tmp_path,
            slug_name="no_click_test",
            format_type="docx",
            download_attachments=False,
        )
        assert res["success"] is False
        mock_wait.assert_not_called()
