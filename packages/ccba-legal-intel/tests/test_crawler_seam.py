"""Unit tests for TVPL Crawler Provider Seam & Mock Legal Provider."""

import pytest

from ccba_legal.crawler import LegalDocProvider, MockLegalDocProvider, TVPLCrawlFailedException


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
