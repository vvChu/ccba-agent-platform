"""Unit tests for Legal Template Generator (Seam tests).

Verifies Decree 30/2020/NĐ-CP formatting across both direct package imports
and thin facade re-exports.
"""

from __future__ import annotations

import pytest
from scripts.legal.legal_template_generator import (
    generate_legal_document as facade_generate_legal_document,
)

from ccba_legal.templates import (
    ND30_HEADER,
    SUPPORTED_DOC_TYPES,
    generate_legal_document,
)


def test_generate_compliance_report_format() -> None:
    """Test generating compliance report contains NĐ 30/2020 elements and citations."""
    data = {
        "project_name": "Dự án Tòa nhà Văn phòng CCBA Tower",
        "subject": "Rà soát tuân thủ quy định PCCC và Giấy phép Xây dựng",
        "advisory_content": "Theo quy định tại [NĐ 207/2026 - 207/2026/NĐ-CP], hồ sơ nghiệm thu cần bổ sung biên bản kiểm tra.",
        "retrieved_docs": [{"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP"}],
        "author": "Chuyên gia Pháp lý CCBA",
    }

    result = generate_legal_document("compliance_report", data)
    assert "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in result
    assert "Độc lập - Tự do - Hạnh phúc" in result
    assert "BÁO CÁO TƯ VẤN TUÂN THỦ PHÁP LÝ" in result
    assert "CCBA Tower" in result
    assert "⚠️ **Disclaimer:**" in result

    # Test facade parity
    facade_result = facade_generate_legal_document("compliance_report", data)
    assert facade_result == result


def test_generate_inquiry_letter_format() -> None:
    """Test generating official inquiry letter."""
    data = {
        "recipient": "Cục Quản lý Hoạt động Xây dựng - Bộ Xây dựng",
        "subject": "Về việc xin ý kiến áp dụng Quy chuẩn kỹ thuật QCVN 06:2022/BXD",
        "advisory_content": "Kính gửi Bộ Xây dựng cho ý kiến về việc áp dụng [SĐ 1:2023 QCVN 06].",
        "author": "CCBA Legal Team",
    }

    result = generate_legal_document("inquiry_letter", data)
    assert "CÔNG VĂN HỎI Ý KIẾN" in result or "Kính gửi" in result
    assert "Bộ Xây dựng" in result


def test_generate_contract_risk_advisory_format() -> None:
    """Test generating contract risk advisory letter."""
    data = {
        "subject": "Đánh giá Rủi ro Điều khoản Phạt Vi phạm Hợp đồng EPC",
        "advisory_content": "Căn cứ Điều 146 Luật Xây dựng 2025, mức phạt vi phạm không vượt quá 12%.",
        "retrieved_docs": [{"short_name": "Luật XD 2025", "document_number": "135/2025/QH15"}],
        "author": "Luật sư Trưởng CCBA",
    }

    result = generate_legal_document("contract_risk_advisory", data)
    assert "THƯ PHẢN HỒI RỦI RO HỢP ĐỒNG XÂY DỰNG" in result
    assert "Luật sư Trưởng CCBA" in result


def test_invalid_doc_type_raises_value_error() -> None:
    """Test passing unsupported doc_type raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        generate_legal_document("unknown_doc_type", {})
    assert "unsupported" in str(exc_info.value).lower()


def test_constants_exported() -> None:
    """Test exported constants."""
    assert "compliance_report" in SUPPORTED_DOC_TYPES
    assert "TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM" in ND30_HEADER
