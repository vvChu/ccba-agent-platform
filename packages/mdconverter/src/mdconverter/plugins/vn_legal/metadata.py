"""
Vietnamese Legal Document Metadata Extractor.

Extracts structured metadata (title, decision number, dates, issuer, etc.)
from Vietnamese legal document content.  Extracted from BaseConverter (H1 fix)
so that the core layer remains domain-agnostic.
"""

import re
from pathlib import Path


def extract_vn_legal_metadata(content: str, source_path: Path) -> dict[str, str]:
    """Extract metadata from Vietnamese legal document content.

    Args:
        content: Markdown content of the document.
        source_path: Original source file path (used as fallback for title).

    Returns:
        Dict with keys: title, short_title, type, decision_number,
        issue_date, effective_date, issuer, signer, status.
    """
    metadata: dict[str, str] = {
        "title": source_path.stem,
        "short_title": "",
        "type": "Document",
        "decision_number": "",
        "issue_date": "",
        "effective_date": "",
        "issuer": "",
        "signer": "",
        "status": "converted",
    }

    # Look at first 3000 chars for metadata
    header = content[:3000]

    # Extract decision number (Quyết định số XXX/QĐ-XXX)
    qd_match = re.search(
        r"(?:Quyết định\s+)?[Ss]ố[:\s]*(\d+/Q[ĐD][-–]?\w+)", header, re.IGNORECASE
    )
    if qd_match:
        metadata["decision_number"] = qd_match.group(1)

    # Extract issue date (ngày DD tháng MM năm YYYY)
    date_match = re.search(
        r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", header, re.IGNORECASE
    )
    if date_match:
        day, month, year = date_match.groups()
        metadata["issue_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Extract effective date (có hiệu lực từ ngày DD/MM/YYYY)
    eff_match = re.search(
        r"hiệu lực\s+(?:từ\s+)?(?:ngày\s+)?(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        header,
        re.IGNORECASE,
    )
    if eff_match:
        date_str = eff_match.group(1).replace("/", "-")
        parts = date_str.split("-")
        if len(parts) == 3:
            metadata["effective_date"] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

    # Extract issuer (Viện KHCN Xây dựng, Bộ Xây dựng, etc.)
    issuer_patterns = [
        r"(Viện\s+KH(?:CN)?\s+[^,\n]+)",
        r"(Bộ\s+[^,\n]+)",
        r"(VIỆN\s+[A-ZĐÀÁẢÃẠ\s]+)",
    ]
    for pattern in issuer_patterns:
        issuer_match = re.search(pattern, header)
        if issuer_match:
            metadata["issuer"] = issuer_match.group(1).strip()[:50]
            break

    # Extract signer
    signer_match = re.search(
        r"(?:VIỆN TRƯỞNG|Viện trưởng)[^\n]*\n[^\n]*\n\*\*([^*]+)\*\*", header
    )
    if signer_match:
        metadata["signer"] = signer_match.group(1).strip()

    # Determine document type
    type_keywords = {
        "Quy chế": "Quy chế nội bộ",
        "Quy định": "Quy định nội bộ",
        "Quyết định": "Quyết định",
        "Thông tư": "Thông tư",
        "Nghị định": "Nghị định",
        "QCVN": "Quy chuẩn Việt Nam",
        "TCVN": "Tiêu chuẩn Việt Nam",
    }
    for keyword, doc_type in type_keywords.items():
        if keyword.lower() in header.lower():
            metadata["type"] = doc_type
            break

    # Extract title from first H1 or bold line
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()[:100]

    # Generate short_title
    if metadata["decision_number"]:
        metadata["short_title"] = f"QĐ {metadata['decision_number'].split('/')[0]}"

    # Set status
    metadata["status"] = "final"

    return metadata
