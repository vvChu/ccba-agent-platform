import sys
from typing import Any, cast
from unittest.mock import patch

import pytest

from ccba_legal.monitor import TokenMonitor  # type: ignore[import-not-found]


# Custom message objects for testing
class CustomToDictMessage:
    def __init__(self, role: str, content: str, name: str | None = None) -> None:
        self.role = role
        self.content = content
        self.name = name

    def to_dict(self) -> dict[str, str]:
        d = {"role": self.role, "content": self.content}
        if self.name:
            d["name"] = self.name
        return d


class CustomDictMessage:
    def __init__(self, role: str, content: str, tool_calls: Any = None) -> None:
        self.role = role
        self.content = content
        self.tool_calls = tool_calls

    def dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        return d


def test_initialization() -> None:
    # Valid initialization
    monitor = TokenMonitor()
    assert monitor.max_tokens == 128000

    monitor_custom = TokenMonitor(max_tokens=64000)
    assert monitor_custom.max_tokens == 64000

    # Invalid max_tokens - float
    with pytest.raises(TypeError):
        TokenMonitor(max_tokens=100.5)

    # Invalid max_tokens - string
    with pytest.raises(TypeError):
        TokenMonitor(max_tokens="100")

    # Invalid max_tokens - boolean (bool is subclass of int, but we explicitly forbid it)
    with pytest.raises(TypeError):
        TokenMonitor(max_tokens=True)

    # Invalid max_tokens - negative/zero
    with pytest.raises(ValueError):
        TokenMonitor(max_tokens=0)

    with pytest.raises(ValueError):
        TokenMonitor(max_tokens=-100)


def test_get_usage_percentage() -> None:
    monitor = TokenMonitor(max_tokens=1000)

    # Normal calculations
    assert monitor.get_usage_percentage(0) == 0.0
    assert monitor.get_usage_percentage(400) == 40.0
    assert monitor.get_usage_percentage(1000) == 100.0
    assert monitor.get_usage_percentage(2000) == 200.0

    # Float usage
    assert monitor.get_usage_percentage(450.5) == pytest.approx(45.05)

    # Validation type checks
    with pytest.raises(TypeError):
        monitor.get_usage_percentage("400")

    with pytest.raises(TypeError):
        monitor.get_usage_percentage(True)

    with pytest.raises(TypeError):
        monitor.get_usage_percentage(cast(Any, None))

    # Validation value checks
    with pytest.raises(ValueError):
        monitor.get_usage_percentage(-1)


def test_check_d_zone() -> None:
    monitor = TokenMonitor(max_tokens=1000)

    # Below D-Zone (less than 40%)
    in_d_zone, msg = monitor.check_d_zone(399)
    assert not in_d_zone
    assert msg == ""

    # Exactly D-Zone (40%)
    in_d_zone, msg = monitor.check_d_zone(400)
    assert in_d_zone
    assert "Warning" in msg
    assert "40.00%" in msg
    assert "400/1000" in msg

    # Above D-Zone (more than 40%)
    in_d_zone, msg = monitor.check_d_zone(850)
    assert in_d_zone
    assert "85.00%" in msg


def test_context_token_count_empty() -> None:
    monitor = TokenMonitor()
    assert monitor.get_context_token_count(None) == 0
    assert monitor.get_context_token_count([]) == 0


def test_context_token_count_normal_and_objects() -> None:
    monitor = TokenMonitor()

    # Mix of dict, string, custom to_dict(), custom dict()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        "Hello!",
        CustomToDictMessage(role="user", content="How are you?"),
        CustomDictMessage(role="assistant", content="I am good."),
    ]

    total_tokens = monitor.get_context_token_count(messages)
    # Check that it returns a positive integer
    assert isinstance(total_tokens, int)
    assert total_tokens > 0

    # Unsupported element type raises TypeError
    with pytest.raises(TypeError):
        monitor.get_context_token_count([12345])


def test_context_token_count_name() -> None:
    monitor = TokenMonitor()

    messages_no_name = [{"role": "user", "content": "hello"}]
    messages_with_name = [{"role": "user", "content": "hello", "name": "alice"}]

    tokens_no_name = monitor.get_context_token_count(messages_no_name)
    tokens_with_name = monitor.get_context_token_count(messages_with_name)

    # The difference should be 1 token overhead + tokens for the name "alice"
    name_tokens = monitor._get_string_tokens("alice")
    assert tokens_with_name == tokens_no_name + 1 + name_tokens


def test_context_token_count_multimodal() -> None:
    monitor = TokenMonitor()

    # Content with text and image_url dicts
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}},
            ],
        }
    ]

    tokens_multimodal = monitor.get_context_token_count(messages)

    # Base message overhead: 3 tokens per message + 3 priming tokens
    # Role "user" tokens
    # Content block 1: text "What is in this image?"
    # Content block 2: image_url -> 85 tokens
    expected_base = (
        3
        + 3
        + monitor._get_string_tokens("user")
        + monitor._get_string_tokens("What is in this image?")
        + 85
    )
    assert tokens_multimodal == expected_base


def test_context_token_count_tool_and_function_calls() -> None:
    monitor = TokenMonitor()

    # Message with function_call
    msg_func = [
        {
            "role": "assistant",
            "content": None,
            "function_call": {"name": "get_weather", "arguments": '{"location": "Hanoi"}'},
        }
    ]
    tokens_func = monitor.get_context_token_count(msg_func)

    # Message with tool_calls
    msg_tool = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"location": "Hanoi"}'},
                }
            ],
        }
    ]
    tokens_tool = monitor.get_context_token_count(msg_tool)

    assert isinstance(tokens_func, int)
    assert isinstance(tokens_tool, int)
    assert tokens_func > 0
    assert tokens_tool > 0


def test_fallback_mode_tiktoken_absent() -> None:
    monitor = TokenMonitor(max_tokens=1000)

    # Simulate tiktoken absent by patching sys.modules
    with patch.dict(sys.modules, {"tiktoken": None}):
        # Reset the cached encoding and fail flag
        monitor._encoding = None
        monitor._tiktoken_failed = False

        # ASCII / English text fallback checks
        # Formula: max(len(text) // 4, int(len(text.split()) * 1.3))
        text_ascii = "Hello world"  # len = 11, split_len = 2
        # max(11 // 4, int(2 * 1.3)) = max(2, 2) = 2
        assert monitor._get_string_tokens(text_ascii) == 2

        text_ascii_long = "This is a longer test sentence for ASCII."  # len = 42, split_len = 8
        # max(42 // 4, int(8 * 1.3)) = max(10, 10) = 10
        assert monitor._get_string_tokens(text_ascii_long) == 10

        # Vietnamese / non-ASCII text fallback checks
        # Formula: max(int(len(text) * 0.7), int(len(text.split()) * 2.5))
        text_vn = "Chào thế giới"  # len = 13, split_len = 3
        # max(int(13 * 0.7), int(3 * 2.5)) = max(9, 7) = 9
        assert monitor._get_string_tokens(text_vn) == 9

        text_vn_long = "Chào bạn, đây là một ngày tuyệt vời."  # len = 36, split_len = 8
        # max(int(36 * 0.7), int(8 * 2.5)) = max(25, 20) = 25
        assert monitor._get_string_tokens(text_vn_long) == 25
