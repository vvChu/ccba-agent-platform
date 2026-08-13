"""Helper utilities to clean up text and extract JSON from LLM responses."""

import re
from typing import Any, TypeVar

from ccba_ai import parse_llm_json, strip_think_tags

T = TypeVar("T")


class Cleaners:
    """Helper utilities to clean up text and extract JSON from LLM responses.

    Delegates LLM output parsing and tag stripping to `ccba-ai`'s `LLMOutputParser`,
    while retaining domain-specific OCR cleanup helpers.
    """

    @classmethod
    def strip_think_tags(cls, text: str) -> str:
        """Strip <think>...</think> tags and their contents from reasoning models."""
        return strip_think_tags(text)

    @classmethod
    def extract_json(
        cls,
        raw: str,
        schema: type[T] | None = None,
        strict: bool = False,
    ) -> Any:
        """Extract JSON dictionary or list from raw text containing Markdown fences."""
        return parse_llm_json(raw, schema=schema, strict=strict)

    @classmethod
    def remove_ocr_artifacts(cls, text: str) -> str:
        """Remove long uppercase lines commonly created by page headers/footers in OCR."""
        return re.sub(r"^[A-ZÀ-Ỹ][A-ZÀ-Ỹ\s_]{14,}\.?\s*$", "", text, flags=re.MULTILINE).strip()
