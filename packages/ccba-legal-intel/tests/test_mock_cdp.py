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
