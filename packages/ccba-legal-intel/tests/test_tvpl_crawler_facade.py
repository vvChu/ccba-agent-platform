"""test_tvpl_crawler_facade.py - TDD unit tests for TVPLCrawler Deep Seam Facade."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ccba_legal import TVPLCrawler
from ccba_legal.crawler import MockLegalDocProvider

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_tvpl_crawler_facade_initialization() -> None:
    """Verify TVPLCrawler facade initializes with default or custom components."""
    crawler = TVPLCrawler()
    assert crawler.cookie_vault is not None
    assert crawler.mutex is not None
    assert crawler.engine is not None


def test_tvpl_crawler_facade_fetch_document() -> None:
    """Verify TVPLCrawler.fetch_document retrieves document under session mutex."""
    mock_provider = MockLegalDocProvider(
        fixtures={
            "123/2024/ND-CP": {
                "document_number": "123/2024/ND-CP",
                "title": "Nghị định quy định về quản lý",
                "status": "Còn hiệu lực",
                "content": "Toàn văn nghị định 123...",
            }
        }
    )
    mock_mutex = MagicMock()
    mock_mutex.__enter__.return_value = None
    mock_mutex.__exit__.return_value = None

    crawler = TVPLCrawler(provider=mock_provider, session_mutex=mock_mutex)
    doc = crawler.fetch_document("123/2024/ND-CP")

    assert doc["document_number"] == "123/2024/ND-CP"
    assert doc["title"] == "Nghị định quy định về quản lý"
    assert mock_mutex.__enter__.called


def test_tvpl_crawler_facade_search() -> None:
    """Verify TVPLCrawler.search returns structured document results."""
    crawler = TVPLCrawler()
    results = crawler.search("Luật Xây dựng", max_results=5)

    assert isinstance(results, list)
    assert len(results) >= 1
    assert "Luật Xây dựng" in results[0]["title"]
