"""Tests for AsyncAIClient and the async_ai singleton."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ccba_ai import AsyncAIClient, async_ai
from ccba_ai.hooks import PrivacyGuardHook

# ---------------------------------------------------------------------------
# Test: async_ai is properly exported
# ---------------------------------------------------------------------------


def test_async_ai_singleton_exported():
    """async_ai should be accessible from the top-level ccba_ai namespace."""
    import ccba_ai

    assert hasattr(ccba_ai, "async_ai"), "async_ai must be in ccba_ai namespace"
    assert isinstance(ccba_ai.async_ai, AsyncAIClient)


def test_async_ai_in_all():
    """async_ai must be declared in __all__ for explicit public API."""
    import ccba_ai

    assert "async_ai" in ccba_ai.__all__, "async_ai must be listed in __all__"


def test_async_ai_has_privacy_guard():
    """AsyncAIClient singleton must carry a PrivacyGuardHook instance."""
    assert isinstance(async_ai.privacy_guard, PrivacyGuardHook)


def test_async_ai_repr():
    """AsyncAIClient repr should mention URL and model."""
    r = repr(async_ai)
    assert "AsyncAIClient" in r


def test_async_client_init_timeout():
    """Test AsyncAIClient timeout initialization."""
    with patch.dict("os.environ", {}, clear=True):
        client = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake")
        assert client.timeout == 60.0
        assert client._client.timeout == 60.0

    with patch.dict("os.environ", {"AI_GATEWAY_TIMEOUT": "45.0"}, clear=False):
        client = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake")
        assert client.timeout == 45.0
        assert client._client.timeout == 45.0

    client_custom = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake", timeout=30.0)
    assert client_custom.timeout == 30.0
    assert client_custom._client.timeout == 30.0


# ---------------------------------------------------------------------------
# Test: async chat methods work correctly (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_async_client_chat_calls_api():
    """AsyncAIClient.chat() should call the underlying OpenAI async client."""
    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "test response"

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response
        result = await client.chat("Hello", model="test-model")

    assert result == "test response"
    mock_create.assert_called_once()


@pytest.mark.anyio
async def test_async_client_chat_strip_thinking():
    """AsyncAIClient.chat() should strip <think> tags by default."""
    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "<think>Pondering async...</think>Async Result"

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response
        result = await client.chat("Hello")
    assert result == "Async Result"

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response
        result_raw = await client.chat("Hello", strip_thinking=False)
    assert "<think>Pondering async...</think>Async Result" in result_raw


@pytest.mark.anyio
async def test_async_client_chat_auto_max_tokens():
    """AsyncAIClient.chat() should auto-allocate 16384 max_tokens for reasoning models."""
    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "OK"

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response
        await client.chat("Hello", model="gemini-3.7-flash-high")
        assert mock_create.call_args.kwargs["max_tokens"] == 16384


@pytest.mark.anyio
async def test_async_client_chat_multi():
    """AsyncAIClient.chat_multi() should accept message list and return text."""
    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "multi response"

    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Say hello"},
    ]

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response
        result = await client.chat_multi(messages, model="test-model")

    assert result == "multi response"


@pytest.mark.anyio
async def test_async_client_chat_with_metadata():
    """AsyncAIClient.chat_with_metadata() should return ChatResult with usage & latency."""
    from ccba_ai.models import ChatResult

    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "<think>Pondering...</think>Async Answer"
    mock_response.model = "gemini-3.7-flash-high"
    mock_response.usage.prompt_tokens = 250
    mock_response.usage.completion_tokens = 80
    mock_response.usage.total_tokens = 330

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response
        res = await client.chat_with_metadata("Test async metadata")

    assert isinstance(res, ChatResult)
    assert res.content == "Async Answer"
    assert res.model == "gemini-3.7-flash-high"
    assert res.usage.prompt_tokens == 250
    assert res.usage.completion_tokens == 80
    assert res.usage.total_tokens == 330
    assert res.latency_ms >= 0.0


@pytest.mark.anyio
async def test_async_client_privacy_guard_blocks_api_key():
    """PrivacyGuard must block API keys from being sent via async client."""
    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    malicious_prompt = "My key is AIzaSyABC123def456GHI789jkl012MNO345pq"

    with pytest.raises(ValueError, match="PrivacyGuard"):
        await client.chat(malicious_prompt)


@pytest.mark.anyio
async def test_async_client_chat_retries_on_connection_error():
    """AsyncAIClient.chat() should retry on connection error and succeed."""
    client = AsyncAIClient(
        base_url="http://test-gateway/v1", api_key="mock-key", max_retries=2, retry_delay=0.01
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "recovered response"

    from openai import APIConnectionError

    side_effects = [APIConnectionError(request=MagicMock()), mock_response]
    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock, side_effect=side_effects
    ) as mock_create:
        result = await client.chat("Hello", model="test-model")

    assert result == "recovered response"
    assert mock_create.call_count == 2


@pytest.mark.anyio
async def test_async_client_chat_fast_fails_when_circuit_breaker_open():
    """AsyncAIClient.chat() should fail immediately with CircuitBreakerOpenError."""
    from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
    cb.record_failure()
    assert cb.allow_request() is False

    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key", circuit_breaker=cb)

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        with pytest.raises(CircuitBreakerOpenError):
            await client.chat("should fast fail async")
        mock_create.assert_not_called()
