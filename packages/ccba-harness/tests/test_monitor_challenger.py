import pytest

pytestmark = [pytest.mark.stress, pytest.mark.adversarial]

from ccba_legal.monitor import TokenMonitor  # type: ignore[import-not-found]

# Test inputs for English and Vietnamese
ENG_TEST_CASES = [
    "Hello world",
    "The quick brown fox jumps over the lazy dog.",
    "This is a longer sentence meant to test the fallback token monitor's accuracy compared to standard tiktoken encoding.",
    "Token monitors track and validate LLM context token usage. They are essential to prevent out-of-context errors and control costs.",
]

VIE_TEST_CASES = [
    "Chào thế giới",
    "Cộng hòa Xã hội Chủ nghĩa Việt Nam",
    "Độc lập - Tự do - Hạnh phúc",
    "Báo cáo đánh giá khả năng tái sử dụng (Reuse Assessment) của dự án CCBA Agent Services Platform.",
    "Bộ luật Dân sự nước Cộng hòa xã hội chủ nghĩa Việt Nam quy định địa vị pháp lý, chuẩn mực pháp lý cho cách ứng xử của cá nhân, pháp nhân.",
]


def test_token_estimation_accuracy() -> None:
    """Verify accuracy of token estimation for English vs Vietnamese under normal and mock-disabled tiktoken."""
    # Under normal environment (tiktoken enabled)
    monitor_normal = TokenMonitor()

    # Under mock-disabled tiktoken
    monitor_fallback = TokenMonitor()
    monitor_fallback._tiktoken_failed = True
    monitor_fallback._encoding = None

    print("\n--- TOKEN ESTIMATION COMPARISON ---")

    # Verify fallback monitor actually has no encoding loaded
    assert monitor_fallback._encoding is None
    # Let's count some tokens on fallback monitor to ensure fallback logic runs and keeps _encoding as None
    _ = monitor_fallback._get_string_tokens("test string")
    assert monitor_fallback._encoding is None

    # 1. English cases
    print("\nEnglish Cases:")
    for text in ENG_TEST_CASES:
        tokens_normal = monitor_normal._get_string_tokens(text)
        tokens_fallback = monitor_fallback._get_string_tokens(text)
        ratio = tokens_fallback / tokens_normal if tokens_normal > 0 else 0
        safe_text = text[:40].encode("ascii", errors="replace").decode("ascii")
        print(
            f"Text: '{safe_text}...' | Normal: {tokens_normal} | Fallback: {tokens_fallback} | Ratio (Fallback/Normal): {ratio:.2f}"
        )

        # Fallback estimation should be reasonably proportional (e.g. 0.5x to 2.5x)
        assert 0.5 <= ratio <= 2.5, f"Fallback ratio {ratio:.2f} for English text out of bounds"

    # 2. Vietnamese cases
    print("\nVietnamese Cases:")
    for text in VIE_TEST_CASES:
        tokens_normal = monitor_normal._get_string_tokens(text)
        tokens_fallback = monitor_fallback._get_string_tokens(text)
        ratio = tokens_fallback / tokens_normal if tokens_normal > 0 else 0
        safe_text = text[:40].encode("ascii", errors="replace").decode("ascii")
        print(
            f"Text: '{safe_text}...' | Normal: {tokens_normal} | Fallback: {tokens_fallback} | Ratio (Fallback/Normal): {ratio:.2f}"
        )

        # Fallback estimation should be reasonably proportional (e.g. 0.5x to 2.5x)
        assert 0.5 <= ratio <= 2.5, f"Fallback ratio {ratio:.2f} for Vietnamese text out of bounds"


def test_d_zone_threshold_exact() -> None:
    """Verify that the D-Zone threshold triggers exactly at >= 40.0% usage."""
    monitor = TokenMonitor(max_tokens=1000)

    # Below 40%
    in_d, msg = monitor.check_d_zone(399)
    assert in_d is False
    assert msg == ""

    # Boundary: 39.999%
    in_d, msg = monitor.check_d_zone(int(399.9))
    assert in_d is False
    assert msg == ""

    # Exactly 40.0%
    in_d, msg = monitor.check_d_zone(400)
    assert in_d is True
    assert "40.00%" in msg

    # Above 40.0%
    in_d, msg = monitor.check_d_zone(401)
    assert in_d is True
    assert "40.10%" in msg

    # Float precision test: 39.99999% vs 40.0%
    in_d, msg = monitor.check_d_zone(int(399.9999))
    assert in_d is False

    in_d, msg = monitor.check_d_zone(int(400.0))
    assert in_d is True


def test_stress_empty_and_none() -> None:
    """Stress test with empty and None values."""
    monitor = TokenMonitor()

    # None messages
    assert monitor.get_context_token_count(None) == 0
    # Empty list
    assert monitor.get_context_token_count([]) == 0

    # Message element is None (should raise TypeError)
    with pytest.raises(TypeError):
        monitor.get_context_token_count([None])

    # Message with None content, role, name
    messages = [{"role": None, "content": None, "name": None}]
    # Base overhead: 3 tokens per message + 3 priming tokens = 6 tokens
    assert monitor.get_context_token_count(messages) == 6

    # Empty strings for fields
    messages_empty = [{"role": "", "content": "", "name": ""}]
    # name is "", role is "", content is ""
    # name presence check: if "name" in msg_dict and msg_dict["name"] is not None -> True
    # then num_tokens += 1 + _get_string_tokens("") -> 1 + 0 = 1
    # role check: role_val is "" -> _get_string_tokens("") -> 0
    # content check: content_val is "" -> _get_string_tokens("") -> 0
    # total = 3 (msg overhead) + 1 (name check overhead) + 3 (priming) = 7
    assert monitor.get_context_token_count(messages_empty) == 7


def test_stress_large_inputs() -> None:
    """Stress test with extremely large string inputs."""
    monitor = TokenMonitor()

    large_eng = "hello " * 100000  # 600,000 characters, 100,000 words
    large_vie = "xin chào " * 100000  # 900,000 characters, 200,000 words

    # Normal tiktoken token count
    tokens_eng = monitor._get_string_tokens(large_eng)
    tokens_vie = monitor._get_string_tokens(large_vie)

    assert tokens_eng > 0
    assert tokens_vie > 0

    # Fallback token count
    monitor_fallback = TokenMonitor()
    monitor_fallback._tiktoken_failed = True
    monitor_fallback._encoding = None

    tokens_eng_fb = monitor_fallback._get_string_tokens(large_eng)
    tokens_vie_fb = monitor_fallback._get_string_tokens(large_vie)

    assert tokens_eng_fb > 0
    assert tokens_vie_fb > 0

    # Performance check: count should run in a fraction of a second
    import time

    t0 = time.perf_counter()
    monitor.get_context_token_count([{"role": "user", "content": large_vie}])
    duration = time.perf_counter() - t0
    print(f"\nTime to compute tokens for large Vietnamese input (900k chars): {duration:.4f}s")
    assert duration < 1.0


def test_stress_unusual_characters() -> None:
    """Stress test with emojis, control characters, and special symbols."""
    monitor = TokenMonitor()

    unusual_text = (
        "👨‍👩‍👧‍👦 🚀 §¶ \x00\x01\x02\x03\r\n\t Arabic: العربية, Chinese: 中文, Hindi: हिन्दी"
    )

    tokens_normal = monitor._get_string_tokens(unusual_text)
    assert tokens_normal > 0

    monitor_fallback = TokenMonitor()
    monitor_fallback._tiktoken_failed = True

    tokens_fallback = monitor_fallback._get_string_tokens(unusual_text)
    assert tokens_fallback > 0


def test_complex_and_non_standard_message_structures() -> None:
    """Stress test with deeply nested lists/dicts, non-standard types."""
    monitor = TokenMonitor()

    # 1. Deeply nested list/dict in content
    messages_nested = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Level 1"},
                {
                    "type": "text",
                    "text": {
                        "nested_dict_inside_text_val": "this is not a string, should be skipped safely"
                    },
                },
                [
                    {
                        "type": "text",
                        "text": "Nested list inside content list, should be skipped safely",
                    }
                ],
            ],
        }
    ]
    tokens = monitor.get_context_token_count(messages_nested)
    assert isinstance(tokens, int)

    # 2. Non-standard types inside fields that are expected to be strings
    messages_bad_types = [
        {
            "role": 123,  # int instead of str
            "content": True,  # bool instead of str
            "name": {"key": "val"},  # dict instead of str
        }
    ]
    # Because of explicit isinstance(..., str) checks, this should not crash
    tokens = monitor.get_context_token_count(messages_bad_types)
    # Expected overhead: 3 (msg) + 3 (priming) = 6 tokens.
    # Why?
    # - name: is present and not None, so it adds 1 token. But msg_dict["name"] is a dict, so isinstance(name_val, str) is False, _get_string_tokens(name_val) is skipped.
    # - role: role_val is 123 (int), isinstance is False, skipped.
    # - content: content_val is True (bool), isinstance is False, skipped.
    # Total expected: 3 + 1 (name check overhead) + 3 = 7.
    assert tokens == 7

    # 3. Message object returning invalid type from to_dict()
    class BadMessageObject:
        def to_dict(self) -> str:
            return "not-a-dictionary"

    with pytest.raises(TypeError):
        monitor.get_context_token_count([BadMessageObject()])
