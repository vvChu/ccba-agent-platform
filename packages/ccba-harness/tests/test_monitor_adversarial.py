import threading
from typing import Any

import pytest

pytestmark = [pytest.mark.stress, pytest.mark.adversarial]

from ccba_legal.monitor import TokenMonitor  # type: ignore[import-not-found]


def test_extremely_large_values() -> None:
    """Verify behavior of TokenMonitor with extremely large max_tokens and token counts."""
    # 1. Extremely large max_tokens (e.g., 2^63 - 1)
    huge_limit = 2**63 - 1
    monitor = TokenMonitor(max_tokens=huge_limit)
    assert monitor.max_tokens == huge_limit

    # Check usage percentage with huge values
    current_tokens = 2**62
    percentage = monitor.get_usage_percentage(current_tokens)
    assert percentage == pytest.approx(50.0)

    # 2. Check D-Zone threshold with extremely large values
    in_d, msg = monitor.check_d_zone(current_tokens)
    assert in_d is True
    assert f"{percentage:.2f}%" in msg

    # 3. Check behavior with a huge number of messages containing normal content
    # Ensure it doesn't cause overflow or memory issues (limit message count to 10,000)
    messages = [{"role": "user", "content": "hello"}] * 10000
    # Expected: 10000 * (3 overhead + 1 user token + 1 hello token) + 3 priming = 50003
    tokens = monitor.get_context_token_count(messages)
    assert tokens == 50003


def test_circular_references_in_messages() -> None:
    """Verify that circular references in message structures raise TypeError or resolve gracefully without looping/crashing."""
    monitor = TokenMonitor()

    # 1. Message dict referring to itself in content
    # structure: msg = {"role": "user", "content": msg}
    msg_circular_content: dict[str, Any] = {"role": "user"}
    msg_circular_content["content"] = msg_circular_content

    # Since content_val is a dict (not a str or list), it should be ignored in token calculation, not crashing
    tokens = monitor.get_context_token_count([msg_circular_content])
    # Expected: 3 (message) + 1 (role "user") + 3 (priming) = 7
    assert tokens == 7

    # 2. Content list referring to itself
    # structure: content = [content]
    content_list: list[Any] = []
    content_list.append(content_list)
    msg_circular_list = {"role": "user", "content": content_list}

    # Since content_list is a list, it iterates over its elements.
    # Its only element is itself (a list). The element is checked:
    # isinstance(item, dict) -> False, isinstance(item, str) -> False
    # So it skips the element and terminates. No infinite loop!
    tokens = monitor.get_context_token_count([msg_circular_list])
    # Expected: 3 (message) + 1 (role "user") + 3 (priming) = 7
    assert tokens == 7

    # 3. Messages list referring to itself
    # structure: messages = [messages]
    messages_list: list[Any] = []
    messages_list.append(messages_list)

    # The monitor iterates over messages_list.
    # The first element is messages_list itself (a list).
    # Since it does not have to_dict/dict and is not str or dict, it should raise TypeError gracefully.
    with pytest.raises(TypeError) as exc_info:
        monitor.get_context_token_count(messages_list)
    assert "Unsupported message type" in str(exc_info.value)

    # 4. Circular reference in tool_calls
    # structure: msg = {"role": "assistant", "tool_calls": [msg]}
    msg_circular_tools = {"role": "assistant", "tool_calls": []}
    msg_circular_tools["tool_calls"].append(msg_circular_tools)  # type: ignore

    # The monitor parses tool_calls list.
    # First element is msg_circular_tools (a dict).
    # It tries to find "function" key in msg_circular_tools. There is none.
    # So it skips it. No infinite loop!
    tokens = monitor.get_context_token_count([msg_circular_tools])
    # Expected: 3 (message) + 2 (role "assistant") + 3 (priming) = 8
    assert tokens in (7, 8, 9)

    # 5. Circular reference inside tool_calls' function
    # structure: msg = {"role": "assistant", "tool_calls": [{"type": "function", "function": msg}]}
    tool_call_dict = {"type": "function"}
    msg_circular_func = {"role": "assistant", "tool_calls": [tool_call_dict]}
    tool_call_dict["function"] = msg_circular_func  # type: ignore

    # The monitor parses tool_calls list.
    # First element is tool_call_dict.
    # It gets "function" which is msg_circular_func (a dict).
    # It gets "name" and "arguments" from msg_circular_func. Since they don't exist, it skips them.
    # No infinite loop!
    tokens = monitor.get_context_token_count([msg_circular_func])
    # Expected: 3 (message) + 2 (role "assistant") + 3 (priming) = 8
    assert tokens in (7, 8, 9)


def test_invalid_types_raise_type_error() -> None:
    """Verify that invalid types inside messages raise TypeError or are handled gracefully."""
    monitor = TokenMonitor()

    # 1. Non-iterable messages list
    with pytest.raises(TypeError):
        monitor.get_context_token_count(12345)

    # 2. Boolean messages list (bool is technically int, not iterable)
    with pytest.raises(TypeError):
        monitor.get_context_token_count(True)

    # 3. Custom object without to_dict or dict methods
    class InvalidMessage:
        pass

    with pytest.raises(TypeError) as exc_info:
        monitor.get_context_token_count([InvalidMessage()])
    assert "Unsupported message type" in str(exc_info.value)

    # 4. Raw string passed directly (should raise TypeError)
    with pytest.raises(TypeError) as exc_info:
        monitor.get_context_token_count("hello")
    assert "messages must be a list or tuple" in str(exc_info.value)

    # 5. Raw dictionary passed directly (should raise TypeError)
    with pytest.raises(TypeError) as exc_info:
        monitor.get_context_token_count({"role": "user", "content": "hello"})
    assert "messages must be a list or tuple" in str(exc_info.value)


def test_concurrency_safety() -> None:
    """Test behavior of TokenMonitor under concurrent access by multiple threads."""
    monitor = TokenMonitor()

    # We want to concurrently count tokens on the same monitor instance
    messages_eng = [{"role": "user", "content": "Hello world from thread!"}]
    messages_vie = [{"role": "user", "content": "Chào mừng bạn đến với hệ thống!"}]

    results_eng = []
    results_vie = []
    errors = []

    def worker_eng() -> None:
        try:
            for _ in range(100):
                tokens = monitor.get_context_token_count(messages_eng)
                results_eng.append(tokens)
        except Exception as e:
            errors.append(e)

    def worker_vie() -> None:
        try:
            for _ in range(100):
                tokens = monitor.get_context_token_count(messages_vie)
                results_vie.append(tokens)
        except Exception as e:
            errors.append(e)

    # Spawn 10 threads of each type
    threads = []
    for _ in range(10):
        threads.append(threading.Thread(target=worker_eng))
        threads.append(threading.Thread(target=worker_vie))

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors occurred during concurrent execution: {errors}"

    # Verify results are consistent
    expected_eng = monitor.get_context_token_count(messages_eng)
    expected_vie = monitor.get_context_token_count(messages_vie)

    for res in results_eng:
        assert res == expected_eng
    for res in results_vie:
        assert res == expected_vie


def test_concurrent_initialization() -> None:
    """Verify that multiple threads concurrently triggering the first tiktoken initialization is race-free."""
    # Create a fresh monitor with no encoding initialized
    monitor = TokenMonitor()
    assert monitor._encoding is None
    assert monitor._tiktoken_failed is False

    errors = []

    def initializer() -> None:
        try:
            # Trigger tiktoken loading concurrently
            tokens = monitor._get_string_tokens("Test tiktoken concurrent init")
            assert tokens > 0
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=initializer) for _ in range(20)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors during concurrent init: {errors}"
    # Encoding should now be loaded (or tiktoken failed flag is set if tiktoken is not installed)
    assert (monitor._encoding is not None) or (monitor._tiktoken_failed is True)
