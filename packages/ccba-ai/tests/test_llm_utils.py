import pytest
from pydantic import BaseModel

from ccba_ai import LLMParseError, parse_llm_json, strip_think_tags
from ccba_ai.llm_utils import Cleaners, LLMOutputParser


class SampleModel(BaseModel):
    name: str
    score: int


def test_strip_think_tags():
    # 1. Closed tags
    text = "<think>some internal thought</think>\nActual response text."
    assert strip_think_tags(text) == "Actual response text."

    # 2. Unclosed tags
    text = "Some intro.\n<think>unclosed thought from reasoning model"
    assert strip_think_tags(text) == "Some intro."

    # 3. Orphaned end tags
    text = "part of think block</think>\nActual text."
    assert strip_think_tags(text) == "Actual text."

    # 4. Case insensitivity and whitespace
    text = "<THINK>\n  nested details\n  </THINK>\n\n  hello  "
    assert strip_think_tags(text) == "hello"

    # 5. Nested think tags
    text = "<think>outer <think>inner</think> thought</think>\nNested result"
    assert strip_think_tags(text) == "Nested result"

    # 6. Empty or None input
    assert strip_think_tags("") == ""
    assert strip_think_tags(None) == ""


def test_parse_llm_json():
    # 1. Standard markdown code block
    raw = """
Here is the JSON you requested:
```json
{
  "key": "value",
  "num": 42
}
```
Have a nice day!
"""
    parsed = parse_llm_json(raw)
    assert parsed == {"key": "value", "num": 42}

    # 2. Outer brace parsing fallback
    raw = 'Random text prefix {"hello": "world"} random text suffix'
    parsed = parse_llm_json(raw)
    assert parsed == {"hello": "world"}

    # 3. Handling Extra data
    raw = """
```json
{"severity": "high", "issue": "Clash detected"}
```
Note: This is an extra line of explanation that might cause JSONDecodeError on full text.
"""
    parsed = parse_llm_json(raw)
    assert parsed == {"severity": "high", "issue": "Clash detected"}

    # 4. Parsing a list
    raw = "```json\n[1, 2, 3]\n```"
    parsed = parse_llm_json(raw)
    assert parsed == [1, 2, 3]

    # 5. Invalid JSON returns None when strict=False
    assert parse_llm_json("not a json string") is None
    assert parse_llm_json("") is None


def test_parse_llm_json_with_schema():
    raw = '{"name": "Audit Test", "score": 95}'
    model = parse_llm_json(raw, schema=SampleModel)
    assert isinstance(model, SampleModel)
    assert model.name == "Audit Test"
    assert model.score == 95

    # Validation failure returns None in non-strict mode
    bad_raw = '{"name": "Audit Test", "score": "invalid_number"}'
    assert parse_llm_json(bad_raw, schema=SampleModel) is None


def test_parse_llm_json_strict_mode():
    raw = "Not JSON at all"
    with pytest.raises(LLMParseError) as exc_info:
        parse_llm_json(raw, strict=True)
    assert "No valid JSON structure" in exc_info.value.reason
    assert exc_info.value.raw_output == raw

    # Schema validation failure in strict mode
    bad_raw = '{"name": "Audit Test", "score": "invalid_number"}'
    with pytest.raises(LLMParseError) as exc_info:
        parse_llm_json(bad_raw, schema=SampleModel, strict=True)
    assert "Schema validation failed" in exc_info.value.reason


def test_backward_compatibility_cleaners():
    assert Cleaners is LLMOutputParser
    assert Cleaners.strip_think_tags("<think>abc</think>def") == "def"
    assert Cleaners.extract_json('{"a": 1}') == {"a": 1}
