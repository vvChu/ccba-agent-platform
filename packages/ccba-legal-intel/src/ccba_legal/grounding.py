"""Grounding Gate and Legal Citation Verifier for CCBA Legal Intel.

Provides deep verification of legal citations in responses against retrieved
documents from the legal registry, eliminating hallucinated or unsupported claims.
"""

from __future__ import annotations

import re
from typing import Any

LEGAL_DISCLAIMER = """
---
⚠️ **Disclaimer:** Nội dung tư vấn trên được tự động trích xuất và kiểm định bằng AI Agent dựa trên Sổ bộ Pháp lý CCBA (`legal_registry.yaml`). Đây là thông tin tham khảo kỹ thuật, KHÔNG phải văn bản tư vấn pháp lý chính thức. Luôn cần chuyên gia pháp lý hoặc Luật sư xác nhận trước khi áp dụng vào dự án thực tế.
"""


def verify_legal_grounding(
    response_text: str, retrieved_docs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Verify that response_text contains valid citations matching retrieved_docs.

    Excludes standard Markdown links (e.g. [text](url)) to prevent false positives.

    Args:
        response_text: The generated legal advice text.
        retrieved_docs: List of documents retrieved from the legal registry.

    Returns:
        Dictionary with grounding status, valid citations found, and any warning reason.
    """
    # Negative lookahead (?!\() ensures we only match standalone bracket citations [Citation],
    # NOT Markdown links like [Link Text](https://url)
    citations = re.findall(r"\[([^\]\n]+)\](?!\()", response_text)

    valid_citations: list[str] = []
    retrieved_identifiers: set[str] = set()

    for doc in retrieved_docs:
        if not isinstance(doc, dict):
            continue
        if doc.get("short_name"):
            retrieved_identifiers.add(str(doc["short_name"]).strip().lower())
        if doc.get("document_number"):
            retrieved_identifiers.add(str(doc["document_number"]).strip().lower())
        if doc.get("id"):
            retrieved_identifiers.add(str(doc["id"]).strip().lower())

    for citation in citations:
        citation_clean = citation.strip()
        citation_lower = citation_clean.lower()
        if any(ident in citation_lower for ident in retrieved_identifiers if ident):
            valid_citations.append(citation_clean)

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


def format_grounded_response(
    response_text: str, retrieved_docs: list[dict[str, Any]]
) -> str:
    """Format final response with grounding verification banner and standard disclaimer.

    Args:
        response_text: The generated response text.
        retrieved_docs: List of reference documents.

    Returns:
        Formatted response with warning banner (if ungrounded) and disclaimer.
    """
    verification = verify_legal_grounding(response_text, retrieved_docs)

    output = response_text.strip()
    if not verification["is_grounded"]:
        warning = verification.get("warning_reason") or "Thiếu căn cứ trích dẫn hợp lệ"
        output = f"⚠️ **[{warning}]**\n\n" + output

    if "⚠️ **Disclaimer:**" not in output:
        output = output + "\n" + LEGAL_DISCLAIMER

    return output


class LegalGroundingGate:
    """Deep Seam class for Legal Grounding verification and response formatting."""

    def __init__(self, disclaimer: str = LEGAL_DISCLAIMER) -> None:
        self.disclaimer = disclaimer

    def verify(
        self, response_text: str, retrieved_docs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Verify citations in response."""
        return verify_legal_grounding(response_text, retrieved_docs)

    def format(
        self, response_text: str, retrieved_docs: list[dict[str, Any]]
    ) -> str:
        """Format response with verification banner and disclaimer."""
        return format_grounded_response(response_text, retrieved_docs)
