"""Unit tests for MockChromeCDP offline testing adapter."""

import pytest
from ccba_legal.crawler import ChromeCDPError, MockChromeCDP


def test_mock_cdp_navigation_and_js_eval() -> None:
    """Verify MockChromeCDP supports simulated navigation and JS evaluation offline."""
    mock_cdp = MockChromeCDP(port=9222)

    # Initial state
    assert mock_cdp.connected is False

    # Simulate get pages
    pages = mock_cdp.get_pages()
    assert len(pages) >= 1
    assert pages[0]["type"] == "page"

    # Connect tab
    mock_cdp.connect_tab(pages[0]["webSocketDebuggerUrl"])
    assert mock_cdp.connected is True

    # Navigate
    mock_cdp.navigate("https://thuvienphapluat.vn/van-ban/PCCC/test.aspx")
    assert mock_cdp.current_url == "https://thuvienphapluat.vn/van-ban/PCCC/test.aspx"

    # Set mock JS return value
    mock_cdp.set_mock_js_response("document.title", "Luật PCCC Mock Title")
    title = mock_cdp.evaluate_js("document.title")
    assert title == "Luật PCCC Mock Title"


def test_mock_cdp_unconnected_raises_error() -> None:
    """Verify MockChromeCDP raises ChromeCDPError when sending commands without connecting."""
    mock_cdp = MockChromeCDP()
    with pytest.raises(ChromeCDPError, match="No active WebSocket connection"):
        mock_cdp.evaluate_js("document.title")


def test_mock_cdp_get_tvpl_metadata() -> None:
    """Verify MockChromeCDP supports offline metadata & relations extraction."""
    from ccba_legal.crawler import get_tvpl_metadata

    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")

    custom_meta = {
        "document_number": "55/2024/QH15",
        "type": "Luật",
        "issued_by": "Quốc hội",
        "signer": "Trần Thanh Mẫn",
        "issued_date": "2024-11-27",
        "effective_date": "2025-07-01",
        "published_date": "2024-12-10",
        "status": "Còn hiệu lực",
        "relations": {
            "guiding_docs": [
                {
                    "title": "Nghị định 105/2025/NĐ-CP",
                    "url": "https://thuvienphapluat.vn/van-ban/PCCC/Nghi-dinh-105-2025-ND-CP.aspx",
                }
            ]
        },
    }
    mock_cdp.set_mock_metadata(custom_meta)

    url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-55-2024-QH15.aspx"
    meta = get_tvpl_metadata(mock_cdp, url)

    assert meta["document_number"] == "55/2024/QH15"
    assert meta["type"] == "Luật"
    assert "guiding_docs" in meta["relations"]
    assert len(meta["relations"]["guiding_docs"]) == 1


def test_mock_cdp_get_crawled_doc_data() -> None:
    """Verify MockChromeCDP supports offline get_crawled_doc_data execution."""
    from ccba_legal.crawler import get_crawled_doc_data

    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")
    mock_cdp.set_mock_js_response("document.title", "Luật PCCC số 55/2024/QH15")
    mock_cdp.set_mock_body_text("Nội dung chi tiết Luật PCCC số 55/2024/QH15")
    mock_cdp.set_mock_links(
        [
            {
                "text": "Nghị định 105/2025/NĐ-CP",
                "href": "https://thuvienphapluat.vn/van-ban/PCCC/Nghi-dinh-105-2025-ND-CP.aspx",
                "relationship": "Guides",
            }
        ]
    )

    url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-55-2024-QH15.aspx"
    title, body, links = get_crawled_doc_data(mock_cdp, url)

    assert title == "Luật PCCC số 55/2024/QH15"
    assert "55/2024/QH15" in body
    assert len(links) == 1
    assert links[0]["text"] == "Nghị định 105/2025/NĐ-CP"


def test_mock_cdp_handling_login_and_popups() -> None:
    """Verify MockChromeCDP login and popup simulation flags."""
    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")

    assert mock_cdp.handle_login() is False
    assert mock_cdp.close_popup() is False

    mock_cdp.mock_login_attempted = True
    mock_cdp.mock_popup_closed = True

    assert mock_cdp.handle_login() is True
    assert mock_cdp.close_popup() is True

