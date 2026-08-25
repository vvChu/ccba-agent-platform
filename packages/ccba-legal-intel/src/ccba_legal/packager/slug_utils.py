"""Slug generation and path sanitization utilities."""

from __future__ import annotations

import re


def sanitize_slug(text: str) -> str:
    """Create a clean directory slug from URL or title."""
    text = text.lower()
    text = text.replace("/", " ").replace("\\", " ").replace(".", " ")
    accents = {
        "a": "áàảãạăắằẳẵặâấầẩẫậ",
        "d": "đ",
        "e": "éèẻẽẹêếềểễệ",
        "i": "íìỉĩị",
        "o": "óòỏõọôốồổỗộơớờởỡợ",
        "u": "úùủũụưứừửữự",
        "y": "ýỳỷỹỵ",
    }
    for char, group in accents.items():
        for g in group:
            text = text.replace(g, char)
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text).strip("_")
    if len(text) > 60:
        text = text[:60].rstrip("_")
    return text
