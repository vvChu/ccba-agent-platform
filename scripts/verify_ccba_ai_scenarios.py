#!/usr/bin/env python3
"""E2E Scenario Verification for ccba-ai SDK Architecture.

Verifies that the entire ccba-ai SDK architecture satisfies all 6 core scenarios
in real-world execution against the AI Gateway.
"""

from __future__ import annotations

import asyncio
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ccba_ai import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    ModelArchetype,
    ai,
    async_ai,
    choose_model,
    is_reasoning_model,
    resolve_max_tokens,
)


def log_step(name: str, passed: bool, detail: str = "") -> None:
    badge = "[PASS]" if passed else "[FAIL]"
    print(f"{badge} {name}: {detail}")
    if not passed:
        raise AssertionError(f"Step failed: {name} - {detail}")


def verify_scenario_1_routing() -> None:
    """Scenario 1: Model Archetypes & Dynamic Task Routing."""
    print("\n--- Scenario 1: Model Archetypes & Task Routing ---")
    log_step("Archetype Constants", ModelArchetype.OCR == "ocr-primary", "OCR constant matches contract")
    log_step("Archetype Reasoning", ModelArchetype.REASONING == "gemini-3.7-flash-high", "Reasoning matches contract")
    log_step("Choose Model OCR", choose_model("ocr") == "ocr-primary", "choose_model('ocr') -> ocr-primary")
    log_step("Choose Model Reasoning", choose_model("reasoning") == "gemini-3.7-flash-high", "choose_model('reasoning') -> gemini-3.7-flash-high")
    log_step("Choose Model Coding", choose_model("coding") == "gemini-3.7-flash", "choose_model('coding') -> gemini-3.7-flash")
    log_step("Choose Model Private", choose_model("private") == "qwen-local-primary", "choose_model('private') -> qwen-local-primary")

    # Reasoning Model Detection
    log_step("Is Reasoning High", is_reasoning_model("gemini-3.7-flash-high") is True, "gemini-3.7-flash-high is reasoning")
    log_step("Is Reasoning Thinking", is_reasoning_model("claude-sonnet-4-6-thinking") is True, "claude-sonnet-4-6-thinking is reasoning")
    log_step("Is Standard Non-Reasoning", is_reasoning_model("gemini-3.7-flash") is False, "gemini-3.7-flash is not reasoning")

    # Token Resolution
    log_step(
        "Auto Token Standard",
        resolve_max_tokens("gemini-3.7-flash", 1024, baseline_default=1024) == 1024,
        "Standard preserves 1024",
    )
    log_step(
        "Auto Token Reasoning Elevation",
        resolve_max_tokens("gemini-3.7-flash-high", 1024, baseline_default=1024) == 16384,
        "Reasoning auto-elevates to 16384",
    )
    log_step(
        "Auto Token Custom Preservation",
        resolve_max_tokens("gemini-3.7-flash-high", 500, baseline_default=1024) == 500,
        "Explicit custom max_tokens (500) strictly preserved",
    )


def verify_scenario_2_sync_chat() -> None:
    """Scenario 2: Synchronous Chat Execution with AI Gateway."""
    print("\n--- Scenario 2: Synchronous Chat Execution ---")
    t0 = time.perf_counter()
    reply = ai.chat(
        "Xác nhận hệ thống CCBA AI Gateway: Trả lời ngắn gọn chữ 'OK'.",
        max_tokens=64,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_step("Sync Chat Response", len(reply) > 0, f"Got reply in {elapsed_ms:.1f}ms: '{reply.strip()}'")

    # Chat multi
    multi_reply = ai.chat_multi(
        [
            {"role": "system", "content": "You are a helpful CCBA assistant."},
            {"role": "user", "content": "Say 'CCBA READY'"},
        ],
        max_tokens=64,
    )
    log_step("Sync Chat Multi Response", len(multi_reply) > 0, f"Got multi reply: '{multi_reply.strip()}'")


def verify_scenario_3_telemetry_metadata() -> None:
    """Scenario 3: Chat Telemetry & Usage Extraction (ChatResult)."""
    print("\n--- Scenario 3: Chat Telemetry & Metadata Extraction ---")
    result = ai.chat_with_metadata(
        "Hôm nay thời tiết đẹp không? Trả lời 1 câu ngắn.",
        max_tokens=64,
    )
    log_step("ChatResult Structure", hasattr(result, "content") and hasattr(result, "usage") and hasattr(result, "latency_ms"), "ChatResult contains content, usage, latency_ms")
    log_step("ChatResult Content", len(result.content) > 0, f"Content: '{result.content.strip()}'")
    log_step("ChatResult Latency", result.latency_ms > 0, f"Latency: {result.latency_ms:.1f}ms")
    log_step(
        "ChatResult Usage Tokens",
        result.usage.prompt_tokens > 0 and result.usage.completion_tokens > 0 and result.usage.total_tokens > 0,
        f"Usage: prompt={result.usage.prompt_tokens}, completion={result.usage.completion_tokens}, total={result.usage.total_tokens}",
    )


def verify_scenario_4_circuit_breaker() -> None:
    """Scenario 4: In-Memory Fast-Fail Circuit Breaker."""
    print("\n--- Scenario 4: Fast-Fail Circuit Breaker ---")
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    log_step("Initial State CLOSED", cb.state == CircuitState.CLOSED, "CB starts in CLOSED state")

    # Record 2 failures
    from openai import APIConnectionError
    dummy_err = APIConnectionError(request=None)
    cb.record_failure(dummy_err)
    log_step("1 Failure Stays CLOSED", cb.state == CircuitState.CLOSED, "1 failure < threshold 2")

    cb.record_failure(dummy_err)
    log_step("2 Failures Trips to OPEN", cb.state == CircuitState.OPEN, "Reached threshold -> tripped to OPEN")

    # Check fast-fail
    fast_fail_caught = False
    try:
        cb.check_allowed()
    except CircuitBreakerOpenError as e:
        fast_fail_caught = True
        log_step("Fast-Fail Raised", True, f"Caught fast-fail error without network call: {e.to_json()}")

    log_step("Fast-Fail Confirmed", fast_fail_caught, "CircuitBreakerOpenError raised correctly")

    # Recovery test
    time.sleep(0.15)
    allowed = cb.allow_request()
    log_step("Half-Open Transition", allowed is True and cb.state == CircuitState.HALF_OPEN, "After recovery timeout -> allow_request transitions to HALF_OPEN")

    cb.record_success()
    log_step("Success Closes Breaker", cb.state == CircuitState.CLOSED, "Probe success resets CB to CLOSED")


async def verify_scenario_5_async_chat() -> None:
    """Scenario 5: Asynchronous Chat & Telemetry Execution."""
    print("\n--- Scenario 5: Asynchronous Chat & Telemetry ---")
    reply = await async_ai.chat("Async verification ping: reply 'ASYNC OK'", max_tokens=64)
    log_step("Async Chat", len(reply) > 0, f"Async reply: '{reply.strip()}'")

    res = await async_ai.chat_with_metadata("Async metadata ping", max_tokens=64)
    log_step(
        "Async ChatResult Telemetry",
        res.usage.total_tokens > 0 and res.latency_ms > 0,
        f"Async usage: total_tokens={res.usage.total_tokens}, latency={res.latency_ms:.1f}ms",
    )


def verify_scenario_6_privacy_guard() -> None:
    """Scenario 6: Privacy Guard Interceptor & Secret Protection."""
    print("\n--- Scenario 6: Privacy Guard Outbound Protection ---")
    from ccba_ai.hooks.privacy_guard import PrivacyGuardHook

    hook = PrivacyGuardHook()
    test_leak_prompt = "Đây là API key của tôi: AIzaSyTestKey1234567890abcdefghijklmn"

    # Test direct hook intercept
    blocked = False
    try:
        hook.check_content(test_leak_prompt)
    except ValueError as e:
        blocked = True
        log_step("Privacy Interceptor Blocks Key", True, f"Blocked with error: {str(e)[:60]}...")

    log_step("Privacy Violation Intercepted", blocked, "PrivacyGuardHook raised ValueError on sensitive key")

    # Test AIClient privacy guard integration
    client_blocked = False
    try:
        ai.chat(test_leak_prompt)
    except ValueError:
        client_blocked = True

    log_step("AIClient Blocks Leak", client_blocked, "ai.chat() proactively rejected request containing API key")


def main() -> None:
    print("=" * 70)
    print("  CCBA AI SDK ARCHITECTURAL SCENARIO VERIFICATION")
    print(f"  Target Gateway: {ai._client.base_url}")
    print("=" * 70)

    verify_scenario_1_routing()
    verify_scenario_2_sync_chat()
    verify_scenario_3_telemetry_metadata()
    verify_scenario_4_circuit_breaker()
    asyncio.run(verify_scenario_5_async_chat())
    verify_scenario_6_privacy_guard()

    print("\n" + "=" * 70)
    print("  [SUCCESS] 100% CCBA-AI ARCHITECTURAL SCENARIOS OPERATIONAL & VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
