import pytest

from ccba_ai import parse_llm_json, strip_think_tags


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
    raw = "Random text prefix {\"hello\": \"world\"} random text suffix"
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

    # 5. Invalid JSON returns None
    assert parse_llm_json("not a json string") is None
