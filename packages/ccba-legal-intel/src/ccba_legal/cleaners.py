"""Helper utilities to clean up text and extract JSON from LLM responses."""

import json
import re
from typing import Any


class Cleaners:
    """Helper utilities to clean up text and extract JSON from LLM responses."""

    _THINK_PATTERN = re.compile(r"<think>.*?</think>\n*", re.DOTALL | re.IGNORECASE)
    _THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
    _ORPHAN_END = re.compile(r"^.*?</think>\n*", re.DOTALL | re.IGNORECASE)

    @classmethod
    def strip_think_tags(cls, text: str) -> str:
        """Strip <think>...</think> tags and their contents from reasoning models."""
        text = cls._THINK_PATTERN.sub("", text)
        text = cls._THINK_UNCLOSED.sub("", text)
        text = cls._ORPHAN_END.sub("", text)
        return text.strip()

    @classmethod
    def extract_json(cls, raw: str) -> Any:
        """Extract JSON dictionary or list from raw text containing Markdown fences."""
        clean = cls.strip_think_tags(raw)
        match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        match = re.search(r"([\{\[].*[\}\]])", clean, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    @classmethod
    def remove_ocr_artifacts(cls, text: str) -> str:
        """Remove long uppercase lines commonly created by page headers/footers in OCR."""
        return re.sub(r"^[A-ZÀ-Ỹ][A-ZÀ-Ỹ\s_]{14,}\.?\s*$", "", text, flags=re.MULTILINE).strip()
