"""Tests for VN Legal detector."""

from mdconverter.plugins.vn_legal.detector import get_document_type, is_legal_document


class TestIsLegalDocument:
    """Test is_legal_document function."""

    def test_empty_content(self) -> None:
        """Test empty content returns False."""
        assert is_legal_document("") is False

    def test_non_legal_content(self) -> None:
        """Test non-legal content returns False."""
        content = "This is a regular document about programming."
        assert is_legal_document(content) is False

    def test_legal_content_with_dieu(self) -> None:
        """Test content with 'Điều' markers."""
        content = """
        Điều 1. Phạm vi điều chỉnh
        Khoản 1. Quy định về phạm vi
        """
        assert is_legal_document(content) is True

    def test_legal_content_with_chuong(self) -> None:
        """Test content with 'Chương' markers."""
        content = """
        Chương I. Quy định chung
        Điều 1. Phạm vi
        """
        assert is_legal_document(content) is True

    def test_legal_content_with_quy_che(self) -> None:
        """Test content with 'Quy chế' marker."""
        content = "Quy chế hoạt động của Viện"
        assert is_legal_document(content, threshold=1) is True


class TestGetDocumentType:
    """Test get_document_type function."""

    def test_quy_che(self) -> None:
        """Test detection of quy_che type."""
        assert get_document_type("Quy chế hoạt động") == "quy_che"

    def test_nghi_dinh(self) -> None:
        """Test detection of nghi_dinh type."""
        assert get_document_type("Nghị định số 123") == "nghi_dinh"

    def test_thong_tu(self) -> None:
        """Test detection of thong_tu type."""
        assert get_document_type("Thông tư hướng dẫn") == "thong_tu"

    def test_quyet_dinh(self) -> None:
        """Test detection of quyet_dinh type."""
        assert get_document_type("Quyết định số 456") == "quyet_dinh"

    def test_unknown(self) -> None:
        """Test unknown document type."""
        assert get_document_type("Regular document") == "unknown"
