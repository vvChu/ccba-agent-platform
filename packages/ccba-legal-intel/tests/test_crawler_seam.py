import pytest

from ccba_legal.crawler import LegalDocProvider, MockLegalDocProvider, TVPLCrawlFailedException

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_legal_doc_provider_abstract():
    """Verify LegalDocProvider raises NotImplementedError when called directly."""
    provider = LegalDocProvider()
    with pytest.raises(NotImplementedError):
        provider.fetch_doc("VBHN-105-2025")


def test_mock_legal_doc_provider_default():
    """Verify MockLegalDocProvider returns default mock document structure."""
    provider = MockLegalDocProvider()
    doc = provider.fetch_doc("VBHN-105-2025")

    assert doc["document_number"] == "VBHN-105-2025"
    assert doc["type"] == "Nghị định"
    assert doc["issued_by"] == "Chính phủ"
    assert "Mock content" in doc["content"]


def test_mock_legal_doc_provider_custom_fixtures():
    """Verify MockLegalDocProvider correctly returns custom registered fixtures."""
    custom_data = {
        "document_number": "QCVN-06-2022",
        "type": "Quy chuẩn",
        "issued_by": "Bộ Xây Dựng",
        "status": "Còn hiệu lực",
        "content": "Quy chuẩn kỹ thuật quốc gia về an toàn cháy cho nhà và công trình",
    }
    provider = MockLegalDocProvider()
    provider.add_fixture("QCVN-06-2022", custom_data)

    doc = provider.fetch_doc("QCVN-06-2022")
    assert doc["document_number"] == "QCVN-06-2022"
    assert doc["issued_by"] == "Bộ Xây Dựng"
    assert doc["content"] == "Quy chuẩn kỹ thuật quốc gia về an toàn cháy cho nhà và công trình"


def test_tvpl_crawler_engine_with_mock_provider(tmp_path):
    """Verify TVPLCrawlerEngine executes fetch_doc via MockLegalDocProvider under lock."""
    from ccba_legal.crawler import TVPLCrawlerEngine, TVPLSessionMutex

    mock_provider = MockLegalDocProvider()
    custom_lock = tmp_path / "test_session.lock"
    mutex = TVPLSessionMutex(lock_path=custom_lock)

    engine = TVPLCrawlerEngine(provider=mock_provider, mutex=mutex)
    doc = engine.fetch_doc("ND-105-2025")

    assert doc["document_number"] == "ND-105-2025"
    assert doc["type"] == "Nghị định"
    # Lock file should be cleaned up after execution
    assert not custom_lock.exists()


def test_tvpl_crawler_engine_exception_handling(tmp_path):
    """Verify TVPLCrawlerEngine catches provider errors, releases lock, and raises TVPLCrawlFailedException."""
    from ccba_legal.crawler import TVPLCrawlerEngine, TVPLSessionMutex

    class FailingProvider(LegalDocProvider):
        def fetch_doc(self, doc_id_or_url: str):
            raise RuntimeError("Connection dropped mid-crawl")

    custom_lock = tmp_path / "failing_session.lock"
    mutex = TVPLSessionMutex(lock_path=custom_lock)
    engine = TVPLCrawlerEngine(provider=FailingProvider(), mutex=mutex)

    with pytest.raises(TVPLCrawlFailedException) as exc_info:
        engine.fetch_doc("BROKEN-DOC")

    assert "Connection dropped mid-crawl" in str(exc_info.value)
    # Lock file must be cleanly released despite the exception
    assert not custom_lock.exists()


def test_tvpl_selectors_multi_session_confirm_js_checks_visibility():
    """Verify multi-session confirmation JS checks computed visibility and active .ui-dialog."""
    from ccba_legal.crawler.selectors import TVPLSelectors

    js = TVPLSelectors.get_multi_session_confirm_js()
    assert "getComputedStyle" in js
    assert ".ui-dialog" in js
    assert "st.display === 'none'" in js
    assert "ContinueLogin" in js


def test_get_crawled_doc_data_filters_promo_and_tutorial_links():
    """Verify get_crawled_doc_data filters out social share, DMCA, and tutorial query links."""
    from unittest.mock import MagicMock

    from ccba_legal.tvpl_parser import get_crawled_doc_data

    mock_cdp = MagicMock()
    mock_cdp.handle_login.return_value = False
    mock_cdp.close_popup.return_value = False

    def fake_eval(expr: str):
        if expr == "document.title":
            return "Quyết định 1812/QĐ-BXD"
        if "divContentDoc" in expr:
            return "Nội dung quyết định"
        if "querySelectorAll('a')" in expr:
            return [
                {
                    "text": "Share FB",
                    "href": "http://www.facebook.com/sharer.php?u=https://thuvienphapluat.vn/van-ban/test.aspx",
                    "relationship": "Guides",
                },
                {
                    "text": "Hướng dẫn",
                    "href": "https://thuvienphapluat.vn/van-ban/test.aspx?v=tvpl-hdsd-luoc-do",
                    "relationship": "Guides",
                },
                {
                    "text": "Luật Xây dựng 2025",
                    "href": "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Luat-Xay-dung-2025-123456.aspx",
                    "relationship": "Guides",
                },
            ]
        return None

    mock_cdp.evaluate_js.side_effect = fake_eval
    _, _, links = get_crawled_doc_data(
        mock_cdp, "https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Quyet-dinh-1812.aspx"
    )
    assert len(links) == 1
    assert links[0]["href"].endswith("Luat-Xay-dung-2025-123456.aspx")
