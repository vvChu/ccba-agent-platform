"""Module implementing Grounding Gate verifier for legal advice responses."""

import re
from typing import Any

LEGAL_DISCLAIMER = """
---
⚠️ **Disclaimer:** Nội dung tư vấn trên được tự động trích xuất và kiểm định bằng AI Agent dựa trên Sổ bộ Pháp lý CCBA (`legal_registry.yaml`). Đây là thông tin tham khảo kỹ thuật, KHÔNG phải văn bản tư vấn pháp lý chính thức. Luôn cần chuyên gia pháp lý hoặc Luật sư xác nhận trước khi áp dụng vào dự án thực tế.
"""


def verify_legal_grounding(
    response_text: str, retrieved_docs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Verify that response_text contains valid citations matching retrieved_docs."""
    # Pattern matching brackets like [Short Name - Doc Num] or [Short Name]
    citations = re.findall(r"\[(.*?)\]", response_text)

    valid_citations = []
    retrieved_identifiers = set()

    for doc in retrieved_docs:
        if doc.get("short_name"):
            retrieved_identifiers.add(doc["short_name"].lower())
        if doc.get("document_number"):
            retrieved_identifiers.add(doc["document_number"].lower())
        if doc.get("id"):
            retrieved_identifiers.add(str(doc["id"]).lower())

    for citation in citations:
        citation_lower = citation.lower()
        if any(ident in citation_lower for ident in retrieved_identifiers):
            valid_citations.append(citation)

    if valid_citations:
        return {
            "is_grounded": True,
            "valid_citations": valid_citations,
            "warning_reason": None,
        }

    return {
        "is_grounded": False,
        "valid_citations": [],
        "warning_reason": "Cảnh báo: Câu trả lời thiếu trích dẫn nguồn văn bản pháp lý hợp lệ từ cơ sở dữ liệu.",
    }


def format_grounded_response(response_text: str, retrieved_docs: list[dict[str, Any]]) -> str:
    """Format final response with grounding check & disclaimer."""
    verification = verify_legal_grounding(response_text, retrieved_docs)

    output = response_text
    if not verification["is_grounded"]:
        output = f"⚠️ **[{verification['warning_reason']}]**\n\n" + output

    if "⚠️ **Disclaimer:**" not in output:
        output = output.strip() + "\n" + LEGAL_DISCLAIMER

    return output
