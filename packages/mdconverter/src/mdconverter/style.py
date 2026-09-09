"""Style analysis, linguistic metrics, and text anonymization engine.

Provides deterministic tools for:
- Redacting sensitive information (API keys, credentials, Vietnamese phone numbers, CCCD/CMND).
- Computing linguistic and stylistic metrics (sentence length, readability, lexical diversity).
- Parsing template placeholders from Markdown documents.
"""

from __future__ import annotations

import re
from typing import Any


def redact_sensitive_info(text: str) -> str:
    """Sanitize and mask sensitive credentials and PII from text.

    Masks:
    - OpenAI / Generic API keys (sk-...)
    - Google API keys (AIzaSy...)
    - Emails
    - Vietnamese phone numbers (10-11 digits, +84)
    - Vietnamese citizen IDs (CMND 9 digits, CCCD 12 digits)

    Args:
        text: Raw text to sanitize.

    Returns:
        Sanitized text with redaction tokens.
    """
    if not text:
        return ""

    # 1. API Keys
    sanitized = re.sub(r"\b(sk-[a-zA-Z0-9]{32,})\b", "[REDACTED_API_KEY]", text)
    sanitized = re.sub(r"\b(AIzaSy[a-zA-Z0-9-_]{33})\b", "[REDACTED_API_KEY]", sanitized)

    # 2. Emails
    sanitized = re.sub(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", sanitized
    )

    # 3. Vietnamese Phone Numbers
    sanitized = re.sub(r"\b(0\d{9,10})\b", "[REDACTED_PHONE]", sanitized)
    sanitized = re.sub(r"\b(\+84\d{9,10})\b", "[REDACTED_PHONE]", sanitized)

    # 4. Vietnamese Citizen Identification (CMND / CCCD)
    sanitized = re.sub(r"\b\d{12}\b", "[REDACTED_CCCD]", sanitized)
    sanitized = re.sub(r"\b\d{9}\b", "[REDACTED_CMND]", sanitized)

    return sanitized


def analyze_style_metrics(text: str) -> dict[str, Any]:
    """Compute deterministic linguistic and stylistic metrics from a document text.

    Args:
        text: Text content to analyze.

    Returns:
        Dictionary of computed metrics (word count, sentence count, avg sentence length, lexical diversity, etc.)
    """
    if not text.strip():
        return {
            "total_words": 0,
            "total_sentences": 0,
            "avg_sentence_length": 0.0,
            "lexical_diversity": 0.0,
            "heading_count": 0,
            "bullet_item_count": 0,
            "tone_indicators": {"formal": 0, "technical": 0, "conversational": 0},
        }

    words = re.findall(r"\b\w+\b", text.lower())
    total_words = len(words)
    unique_words = len(set(words))
    lexical_diversity = round(unique_words / total_words, 3) if total_words > 0 else 0.0

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    total_sentences = len(sentences)
    avg_sentence_length = round(total_words / total_sentences, 1) if total_sentences > 0 else 0.0

    lines = text.splitlines()
    heading_count = sum(1 for line in lines if line.strip().startswith("#"))
    bullet_item_count = sum(1 for line in lines if line.strip().startswith(("-", "*", "+")))

    # Tone indicators based on keywords
    text_lower = text.lower()
    formal_keywords = ["căn cứ", "quyết định", "điều khoản", "trân trọng", "kính gửi", "ban hành"]
    technical_keywords = ["thông số", "quy chuẩn", "tiêu chuẩn", "ifc", "bim", "hệ số", "kết cấu"]
    conversational_keywords = ["bạn", "chúng ta", "hãy", "thực ra", "nhé", "nhỉ", "tuyệt vời"]

    formal_score = sum(text_lower.count(kw) for kw in formal_keywords)
    technical_score = sum(text_lower.count(kw) for kw in technical_keywords)
    conversational_score = sum(text_lower.count(kw) for kw in conversational_keywords)

    return {
        "total_words": total_words,
        "total_sentences": total_sentences,
        "avg_sentence_length": avg_sentence_length,
        "lexical_diversity": lexical_diversity,
        "heading_count": heading_count,
        "bullet_item_count": bullet_item_count,
        "tone_indicators": {
            "formal": formal_score,
            "technical": technical_score,
            "conversational": conversational_score,
        },
    }


def parse_template_placeholders(template_md: str) -> list[str]:
    """Extract all placeholder variable names (e.g. {{project_name}}) from template markdown.

    Args:
        template_md: Markdown template containing placeholders.

    Returns:
        Deduplicated list of placeholder names found in order of appearance.
    """
    matches = re.findall(r"\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}", template_md)
    seen = set()
    result = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


__all__ = [
    "redact_sensitive_info",
    "analyze_style_metrics",
    "parse_template_placeholders",
]
