"""
Vietnamese Legal Document Detector.

Identifies documents that contain Vietnamese legal terminology and structure.
"""

import re
from re import Pattern

# Compiled patterns for performance
LEGAL_PATTERNS: list[Pattern[str]] = [
    re.compile(r"Điều\s+\d+", re.IGNORECASE),
    re.compile(r"Chương\s+[IVXLC]+", re.IGNORECASE),
    re.compile(r"Mục\s+\d+", re.IGNORECASE),
    re.compile(r"Khoản\s+\d+", re.IGNORECASE),
    re.compile(r"Điểm\s+[a-zđ]", re.IGNORECASE),
    re.compile(r"Quy\s+chế", re.IGNORECASE),
    re.compile(r"Nghị\s+định", re.IGNORECASE),
    re.compile(r"Thông\s+tư", re.IGNORECASE),
    re.compile(r"Quyết\s+định", re.IGNORECASE),
    re.compile(r"Phụ\s+lục", re.IGNORECASE),
]


def is_legal_document(content: str, threshold: int = 2) -> bool:
    """
    Check if content is a Vietnamese legal document.

    Args:
        content: The document content to check.
        threshold: Minimum number of legal patterns to match.

    Returns:
        True if document appears to be a Vietnamese legal document.
    """
    if not content:
        return False

    matches = 0
    for pattern in LEGAL_PATTERNS:
        if pattern.search(content):
            matches += 1
            if matches >= threshold:
                return True

    return False


def get_document_type(content: str) -> str:
    """
    Determine the type of Vietnamese legal document.

    Returns one of: 'quy_che', 'nghi_dinh', 'thong_tu', 'quyet_dinh', 'unknown'
    """
    content_lower = content.lower()

    if "quy chế" in content_lower:
        return "quy_che"
    elif "nghị định" in content_lower:
        return "nghi_dinh"
    elif "thông tư" in content_lower:
        return "thong_tu"
    elif "quyết định" in content_lower:
        return "quyet_dinh"

    return "unknown"
