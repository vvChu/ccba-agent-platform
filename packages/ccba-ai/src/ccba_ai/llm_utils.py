import json
import re
from typing import Any, TypeVar, cast

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
    def extract_thinking_and_content(cls, text: str) -> tuple[str, str]:
        """Extract thinking and content from text, handling closed, nested, and unclosed <think> tags."""
        if not text:
            return "", ""

        lower_text = text.lower()
        idx = 0
        depth = 0
        last_content_end = 0
        last_think_start = 0
        content_parts = []
        thinking_parts = []

        while idx < len(text):
            next_think = lower_text.find("<think>", idx)
            next_endthink = lower_text.find("</think>", idx)

            if next_think != -1 and (next_endthink == -1 or next_think < next_endthink):
                if depth == 0:
                    content_parts.append(text[last_content_end:next_think])
                    last_think_start = next_think + 7
                depth += 1
                idx = next_think + 7
            elif next_endthink != -1:
                if depth > 0:
                    depth -= 1
                    if depth == 0:
                        thinking_parts.append(text[last_think_start:next_endthink].strip())
                        last_content_end = next_endthink + 8
                else:
                    content_parts.append(text[last_content_end:next_endthink])
                    last_content_end = next_endthink + 8
                idx = next_endthink + 8
            else:
                break

        if depth > 0:
            thinking_parts.append(text[last_think_start:].strip())
        else:
            content_parts.append(text[last_content_end:])

        thinking = "\n\n".join(part for part in thinking_parts if part).strip()
        content = "".join(content_parts)

        # Clean up any orphaned </think> in the content.
        content = re.sub(r"</think>\n*", "", content, flags=re.IGNORECASE).strip()

        return thinking, content

    @classmethod
    def extract_thinking(cls, text: str) -> str:
        """Extract only the thinking part from text."""
        return cls.extract_thinking_and_content(text)[0]

    @classmethod
    def _validate_schema(cls, data: Any, schema: type[T], raw: str, *, strict: bool = False) -> Any:
        """Validate parsed JSON data against a Pydantic BaseModel or callable schema."""
        try:
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                return schema.model_validate(data)
            if callable(schema):
                return (
                    cast(Any, schema)(data)
                    if not isinstance(data, dict)
                    else cast(Any, schema)(**data)
                )
        except Exception as err:
            if strict:
                raise LLMParseError(f"Schema validation failed: {err}", raw_output=raw) from err
            return None
        return data

    @classmethod
    def extract_json(
        cls,
        raw: str,
        schema: type[T] | None = None,
        strict: bool = False,
    ) -> Any:
        """Extract JSON object/array from raw text, with optional Pydantic schema validation."""
        if not raw:
            if strict:
                raise LLMParseError("Input text is empty", raw_output=raw or "")
            return None

        clean = cls.strip_think_tags(raw)
        data = None
        match = re.search(
            r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean, flags=re.DOTALL | re.IGNORECASE
        )
        if match:
            data = cls._safe_json_load(match.group(1).strip())
        if data is None:
            match = re.search(r"([\{\[].*[\}\]])", clean, flags=re.DOTALL)
            if match:
                data = cls._safe_json_load(match.group(1).strip())
        if data is None:
            data = cls._safe_json_load(clean.strip())
        if data is None:
            if strict:
                raise LLMParseError("No valid JSON structure found in text", raw_output=raw)
            return None
        if schema is not None:
            return cls._validate_schema(data, schema, raw, strict=strict)
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


def extract_thinking_and_content(text: str) -> tuple[str, str]:
    """Helper function to extract thinking and content from text."""
    return LLMOutputParser.extract_thinking_and_content(text)


def extract_thinking(text: str) -> str:
    """Helper function to extract only thinking from text."""
    return LLMOutputParser.extract_thinking(text)


def parse_llm_json(
    raw: str,
    schema: type[T] | None = None,
    strict: bool = False,
) -> Any:
    """Helper function to extract and parse JSON from raw LLM output text."""
    return LLMOutputParser.extract_json(raw, schema=schema, strict=strict)


__all__ = [
    "LLMParseError",
    "LLMOutputParser",
    "Cleaners",
    "strip_think_tags",
    "extract_thinking_and_content",
    "extract_thinking",
    "parse_llm_json",
]
