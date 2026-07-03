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
        if not text:
            return ""
        text = cls._THINK_PATTERN.sub("", text)
        text = cls._THINK_UNCLOSED.sub("", text)
        text = cls._ORPHAN_END.sub("", text)
        return text.strip()

    @classmethod
    def extract_json(cls, raw: str) -> Any:
        """Extract JSON dictionary or list from raw text containing Markdown fences."""
        if not raw:
            return None

        clean = cls.strip_think_tags(raw)

        # Try markdown code blocks first
        match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean, flags=re.DOTALL)
        if match:
            cleaned_text = match.group(1).strip()
            res = cls._safe_json_load(cleaned_text)
            if res is not None:
                return res

        # Try matching outer braces or brackets
        match = re.search(r"([\{\[].*[\}\]])", clean, flags=re.DOTALL)
        if match:
            cleaned_text = match.group(1).strip()
            res = cls._safe_json_load(cleaned_text)
            if res is not None:
                return res

        # Attempt to load clean text directly
        return cls._safe_json_load(clean.strip())

    @classmethod
    def _safe_json_load(cls, text: str) -> Any:
        """Safely load JSON, handling Extra data anomalies by truncating at error position."""
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            if "Extra data" in str(e) and e.pos is not None:
                try:
                    return json.loads(text[: e.pos].strip())
                except json.JSONDecodeError:
                    pass
            return None


def strip_think_tags(text: str) -> str:
    """Helper function to strip <think>...</think> tags from text."""
    return Cleaners.strip_think_tags(text)


def parse_llm_json(raw: str) -> Any:
    """Helper function to extract and parse JSON from raw LLM output text."""
    return Cleaners.extract_json(raw)
