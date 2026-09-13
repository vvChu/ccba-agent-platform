"""test_mcp_legal_search.py - Tests for search_vietnamese_laws tool in MCP Server.

Validates:
1. Dynamic delegation to LegalKnowledgeEngine (ADR 0035, ADR 0050).
2. RULE-3.1 compliance (marking superseded documents and active replacements).
3. Graceful fallback on missing dependency or search errors.
4. Privacy guard enforcement against leaked keys in queries.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ccba_ai.mcp_server import search_vietnamese_laws

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_search_vietnamese_laws_success() -> None:
    """Verify search returns formatted document listings with active status."""
    mock_results = [
        {
            "id": "Luat-Xay-dung-2025-135-2025-QH15",
            "document_number": "135/2025/QH15",
            "title": "Luật Xây dựng năm 2025",
            "status": "ACTIVE",
            "is_superseded": False,
            "notes": "Luật Xây dựng sửa đổi toàn diện",
        }
    ]

    with patch("ccba_legal.LegalKnowledgeEngine") as mock_engine_cls:
        mock_instance = MagicMock()
        mock_instance.search.return_value = mock_results
        mock_engine_cls.return_value = mock_instance

        res = search_vietnamese_laws("Luật Xây dựng")
        assert "Kết quả tra cứu pháp luật cho từ khóa 'Luật Xây dựng':" in res
        assert "[ACTIVE] Luat-Xay-dung-2025-135-2025-QH15: Luật Xây dựng năm 2025" in res
        assert "Ghi chú: Luật Xây dựng sửa đổi toàn diện" in res


def test_search_vietnamese_laws_superseded_warning() -> None:
    """Verify RULE-3.1 warning is emitted for superseded documents."""
    mock_results = [
        {
            "id": "nghi_dinh_175_2024_nd_cp",
            "document_number": "175/2024/NĐ-CP",
            "title": "Nghị định 175/2024/NĐ-CP về nhà chung cư",
            "status": "SUPERSEDED",
            "is_superseded": True,
            "suggested_replacement": "Nghị định 217/2026/NĐ-CP",
            "lifecycle_warning": "Đã bị bãi bỏ toàn bộ",
        }
    ]

    with patch("ccba_legal.LegalKnowledgeEngine") as mock_engine_cls:
        mock_instance = MagicMock()
        mock_instance.search.return_value = mock_results
        mock_engine_cls.return_value = mock_instance

        res = search_vietnamese_laws("175/2024")
        assert "[SUPERSEDED] nghi_dinh_175_2024_nd_cp" in res
        assert "⚠️ CẢNH BÁO RULE-3.1: Văn bản đã hết hiệu lực. Thay thế bởi: Nghị định 217/2026/NĐ-CP" in res
        assert "⚠️ Lưu ý: Đã bị bãi bỏ toàn bộ" in res


def test_search_vietnamese_laws_empty() -> None:
    """Verify empty result returns friendly not found notice."""
    with patch("ccba_legal.LegalKnowledgeEngine") as mock_engine_cls:
        mock_instance = MagicMock()
        mock_instance.search.return_value = []
        mock_engine_cls.return_value = mock_instance

        res = search_vietnamese_laws("van_ban_khong_ton_tai_xyz")
        assert "Không tìm thấy văn bản pháp luật phù hợp" in res


def test_search_vietnamese_laws_import_error() -> None:
    """Verify graceful handling when ccba-legal-intel is missing."""
    with patch.dict("sys.modules", {"ccba_legal": None}):
        res = search_vietnamese_laws("Luật Xây dựng")
        assert "Lỗi: Thư viện ccba-legal-intel chưa được cài đặt" in res


def test_search_vietnamese_laws_privacy_guard() -> None:
    """Verify PrivacyGuardHook blocks API keys in search query."""
    leaked_key = "AIzaSyDummyKey_1234567890abcdef12345"
    with pytest.raises(ValueError, match="Security Violation: Detected sensitive API Key leak"):
        search_vietnamese_laws(f"query with key {leaked_key}")


def test_search_vietnamese_laws_blank_query() -> None:
    """Verify empty or whitespace query returns friendly prompt to input keyword."""
    assert "Vui lòng nhập từ khóa" in search_vietnamese_laws("")
    assert "Vui lòng nhập từ khóa" in search_vietnamese_laws("   ")
