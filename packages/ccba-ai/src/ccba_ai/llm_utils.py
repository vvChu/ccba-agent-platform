import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class LLMParseError(ValueError):
    """Raised when LLM output cannot be parsed or fails schema validation in strict mode."""

    def __init__(self, reason: str, raw_output: str) -> None:
        self.reason = reason
        self.raw_output = raw_output
        super().__init__(f"LLM parse failed: {reason}")


class LLMOutputParser:
    """Internal engine to clean up text, strip reasoning tags, and parse/validate JSON from LLM outputs."""

    _THINK_PATTERN = re.compile(r"<think>.*?</think>\n*", re.DOTALL | re.IGNORECASE)
    _THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
    _ORPHAN_END = re.compile(r"^.*?</think>\n*", re.DOTALL | re.IGNORECASE)

    @classmethod
    def strip_think_tags(cls, text: str) -> str:
        """Strip <think>...</think> tags and their contents from reasoning models.

        Handles nested tags, unclosed tags, and orphaned closing tags.
        """
        if not text:
            return ""

        # Loop until no more full <think>...</think> matches exist (handles nested tags)
        prev_text = None
        current_text = text
        while prev_text != current_text:
            prev_text = current_text
            current_text = cls._THINK_PATTERN.sub("", current_text)

        current_text = cls._THINK_UNCLOSED.sub("", current_text)
        current_text = cls._ORPHAN_END.sub("", current_text)
        return current_text.strip()

    @classmethod
    def extract_json(
        cls,
        raw: str,
        schema: type[T] | None = None,
        strict: bool = False,
    ) -> Any:
        """Extract JSON object/array from raw text, with optional Pydantic schema validation.

        Args:
            raw: Raw LLM output string.
            schema: Optional Pydantic BaseModel or type to validate parsed data against.
            strict: If True, raises LLMParseError on parse or schema validation failures instead of returning None.

        Returns:
            Parsed data structure (dict, list, primitive, or validated schema instance), or None if parsing fails (when strict=False).

        Raises:
            LLMParseError: If strict=True and parsing or schema validation fails.
        """
        if not raw:
            if strict:
                raise LLMParseError("Input text is empty", raw_output=raw or "")
            return None

        clean = cls.strip_think_tags(raw)
        data = None

        # 1. Try markdown code blocks first
        match = re.search(
            r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean, flags=re.DOTALL | re.IGNORECASE
        )
        if match:
            cleaned_text = match.group(1).strip()
            data = cls._safe_json_load(cleaned_text)

        # 2. Try matching outer braces or brackets
        if data is None:
            match = re.search(r"([\{\[].*[\}\]])", clean, flags=re.DOTALL)
            if match:
                cleaned_text = match.group(1).strip()
                data = cls._safe_json_load(cleaned_text)

        # 3. Attempt to load clean text directly
        if data is None:
            data = cls._safe_json_load(clean.strip())

        if data is None:
            if strict:
                raise LLMParseError("No valid JSON structure found in text", raw_output=raw)
            return None

        # 4. Schema validation if requested
        if schema is not None:
            try:
                if isinstance(schema, type) and issubclass(schema, BaseModel):
                    return schema.model_validate(data)
                elif callable(schema):
                    return schema(data) if not isinstance(data, dict) else schema(**data)
            except Exception as err:
                if strict:
                    raise LLMParseError(f"Schema validation failed: {err}", raw_output=raw) from err
                return None

        return data

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


# Backward compatibility class alias
Cleaners = LLMOutputParser


def strip_think_tags(text: str) -> str:
    """Helper function to strip <think>...</think> tags from text."""
    return LLMOutputParser.strip_think_tags(text)


def parse_llm_json(
    raw: str,
    schema: type[T] | None = None,
    strict: bool = False,
) -> Any:
    """Helper function to extract and parse JSON from raw LLM output text."""
    return LLMOutputParser.extract_json(raw, schema=schema, strict=strict)
