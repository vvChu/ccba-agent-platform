"""Grounding Gate and Legal Citation Verifier for CCBA Legal Intel.

Provides deep verification of legal citations in responses against retrieved
documents from the legal registry, eliminating hallucinated or unsupported claims.
"""

from __future__ import annotations

import re
from typing import Any

from ccba_legal.jurisdiction import validate_authority_naming, validate_tier_authority

LEGAL_DISCLAIMER = """
---
⚠️ **Disclaimer:** Nội dung tư vấn trên được tự động trích xuất và kiểm định bằng AI Agent dựa trên Sổ bộ Pháp lý CCBA (`legal_registry.yaml`). Đây là thông tin tham khảo kỹ thuật, KHÔNG phải văn bản tư vấn pháp lý chính thức. Luôn cần chuyên gia pháp lý hoặc Luật sư xác nhận trước khi áp dụng vào dự án thực tế.
"""

NATIONAL_FALLBACK_DISCLAIMER = """
---
ℹ️ **Lưu ý Lãnh thổ (National Fallback):** Chưa ghi nhận văn bản phân cấp địa phương đặc thù trong Sổ bộ pháp lý. Nội dung đang áp dụng theo quy định của pháp luật Trung ương (Toàn quốc). Cần kiểm tra văn bản phân cấp của UBND cấp tỉnh tại địa phương trước khi áp dụng.
"""


def verify_legal_grounding(
    response_text: str,
    retrieved_docs: list[dict[str, Any]],
    jurisdiction: str | None = None,
) -> dict[str, Any]:
    """Verify that response_text contains valid citations matching retrieved_docs and adheres to governance guardrails.

    Excludes standard Markdown links (e.g. [text](url)) to prevent false positives.
    Audits for dissolved authority names and 3-tier local government authority compliance.

    Args:
        response_text: The generated legal advice text.
        retrieved_docs: List of documents retrieved from the legal registry.
        jurisdiction: Optional target jurisdiction code (e.g. 'VN-HN', 'VN-HCM').

    Returns:
        Dictionary with grounding status, valid citations found, authority violations, and any warning reason.
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

    # Determine target jurisdiction for authority naming & tier audits
    target_jur = jurisdiction
    if not target_jur:
        for doc in retrieved_docs:
            if isinstance(doc, dict) and doc.get("territory") and doc.get("territory") != "VN":
                target_jur = str(doc["territory"])
                break

    is_national_fallback = False
    if not target_jur:
        target_jur = "VN"
    elif target_jur != "VN":
        has_local_doc = any(
            isinstance(d, dict) and str(d.get("territory", "")).upper() == target_jur.upper()
            for d in retrieved_docs
        )
        if not has_local_doc and retrieved_docs:
            is_national_fallback = True

    # Governance checks: Dissolved authorities & 3-tier government authority limits
    authority_violations = validate_authority_naming(response_text, jurisdiction=target_jur)
    tier_violations = validate_tier_authority(response_text, jurisdiction=target_jur)

    if authority_violations or tier_violations:
        warnings = []
        for v in authority_violations:
            warnings.append(f"Cảnh báo danh xưng cơ quan: {v.get('warning')}")
        for v in tier_violations:
            warnings.append(f"Cảnh báo thẩm quyền: {v.get('warning')}")
        return {
            "is_grounded": False,
            "valid_citations": valid_citations,
            "warning_reason": " | ".join(warnings),
            "authority_violations": authority_violations,
            "tier_violations": tier_violations,
            "is_national_fallback": is_national_fallback,
        }

    if valid_citations:
        return {
            "is_grounded": True,
            "valid_citations": valid_citations,
            "warning_reason": None,
            "authority_violations": [],
            "tier_violations": [],
            "is_national_fallback": is_national_fallback,
        }

    return {
        "is_grounded": False,
        "valid_citations": [],
        "warning_reason": "Cảnh báo: Câu trả lời thiếu trích dẫn nguồn văn bản pháp lý hợp lệ từ cơ sở dữ liệu.",
        "authority_violations": [],
        "tier_violations": [],
        "is_national_fallback": is_national_fallback,
    }


def format_grounded_response(
    response_text: str,
    retrieved_docs: list[dict[str, Any]],
    jurisdiction: str | None = None,
) -> str:
    """Format final response with grounding verification banner and standard disclaimer.

    Args:
        response_text: The generated response text.
        retrieved_docs: List of reference documents.
        jurisdiction: Optional target territory code.

    Returns:
        Formatted response with warning banner (if ungrounded) and disclaimer.
    """
    verification = verify_legal_grounding(response_text, retrieved_docs, jurisdiction=jurisdiction)

    output = response_text.strip()
    if not verification["is_grounded"]:
        warning = verification.get("warning_reason") or "Thiếu căn cứ trích dẫn hợp lệ"
        output = f"⚠️ **[{warning}]**\n\n" + output

    if verification.get("is_national_fallback") and "ℹ️ **Lưu ý Lãnh thổ" not in output:
        output = output + "\n" + NATIONAL_FALLBACK_DISCLAIMER

    if "⚠️ **Disclaimer:**" not in output:
        output = output + "\n" + LEGAL_DISCLAIMER

    return output


class LegalGroundingGate:
    """Deep Seam class for Legal Grounding verification and response formatting."""

    def __init__(
        self,
        disclaimer: str = LEGAL_DISCLAIMER,
        default_jurisdiction: str | None = None,
    ) -> None:
        self.disclaimer = disclaimer
        self.default_jurisdiction = default_jurisdiction

    def verify(
        self,
        response_text: str,
        retrieved_docs: list[dict[str, Any]],
        jurisdiction: str | None = None,
    ) -> dict[str, Any]:
        """Verify citations and governance compliance in response."""
        jur = jurisdiction or self.default_jurisdiction
        return verify_legal_grounding(response_text, retrieved_docs, jurisdiction=jur)

    def format(
        self,
        response_text: str,
        retrieved_docs: list[dict[str, Any]],
        jurisdiction: str | None = None,
    ) -> str:
        """Format response with verification banner and disclaimer."""
        jur = jurisdiction or self.default_jurisdiction
        return format_grounded_response(response_text, retrieved_docs, jurisdiction=jur)


__all__ = [
    "LEGAL_DISCLAIMER",
    "NATIONAL_FALLBACK_DISCLAIMER",
    "verify_legal_grounding",
    "format_grounded_response",
    "LegalGroundingGate",
]
