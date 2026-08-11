"""Unit tests for Legal Grounding Gate Verifier (Seam tests)."""

from scripts.legal.legal_grounding_gate import format_grounded_response, verify_legal_grounding


def test_verify_legal_grounding_valid_citation():
    """Test response containing valid citation matching retrieved docs is grounded."""
    retrieved_docs = [
        {"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP", "id": "ND-207-2026"}
    ]
    response_text = "Theo quy định tại [NĐ 207/2026 - 207/2026/NĐ-CP], việc nghiệm thu công trình thực hiện theo Điều 12."

    result = verify_legal_grounding(response_text, retrieved_docs)
    assert result["is_grounded"] is True
    assert len(result["valid_citations"]) > 0


def test_verify_legal_grounding_missing_citation():
    """Test response without any legal citations is flagged as ungrounded."""
    retrieved_docs = [
        {"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP", "id": "ND-207-2026"}
    ]
    response_text = "Việc nghiệm thu công trình thực hiện theo quy định chung của chủ đầu tư."

    result = verify_legal_grounding(response_text, retrieved_docs)
    assert result["is_grounded"] is False
    assert (
        "Cảnh báo" in result["warning_reason"]
        or "thiếu trích dẫn" in result["warning_reason"].lower()
    )


def test_format_grounded_response_adds_disclaimer():
    """Test formatted response includes official CCBA legal disclaimer."""
    response_text = (
        "Theo quy định tại [NĐ 207/2026 - 207/2026/NĐ-CP], việc nghiệm thu thực hiện theo quy định."
    )
    retrieved_docs = [
        {"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP", "id": "ND-207-2026"}
    ]

    formatted = format_grounded_response(response_text, retrieved_docs)
    assert "⚠️ Disclaimer" in formatted or "chuyên gia pháp lý" in formatted
