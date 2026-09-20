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
        with patch("ccba_ai.client._find_and_load_env"):
            client = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake")
            assert client.timeout == 90.0
            assert client._client.timeout == 90.0

    with patch.dict("os.environ", {"AI_GATEWAY_TIMEOUT": "45.0"}, clear=False):
        with patch("ccba_ai.client._find_and_load_env"):
            client = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake")
            assert client.timeout == 45.0
            assert client._client.timeout == 45.0

    client_custom = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake", timeout=30.0)
    assert client_custom.timeout == 30.0
    assert client_custom._client.timeout == 30.0


def test_async_url_sanitizer_redirects_8045():
    """Test AsyncAIClient URL sanitizer automatically redirects :8045 to :8090."""
    client = AsyncAIClient(base_url="http://100.83.192.30:8045/v1")
    assert "8090" in str(client._client.base_url)
    assert "8045" not in str(client._client.base_url)
    assert client.base_url == "http://100.83.192.30:8090/v1"


def test_async_url_sanitizer_empty_env_and_whitespace():
    """Test AsyncAIClient URL sanitizer handles empty env and trims whitespace."""
    with patch.dict("os.environ", {"AI_GATEWAY_URL": ""}, clear=False):
        with patch("ccba_ai.client._find_and_load_env"):
            client = AsyncAIClient()
            assert client.base_url == "http://100.83.192.30:8090/v1"

    client_ws = AsyncAIClient(base_url="  http://100.83.192.30:8045/v1 \n ")
    assert client_ws.base_url == "http://100.83.192.30:8090/v1"


@pytest.mark.asyncio
async def test_async_complete_alias_calls_chat():
    """Test AsyncAIClient.complete() acts as an alias for chat()."""
    client = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake")
    with patch.object(
        client, "chat", new_callable=AsyncMock, return_value="async complete result"
    ) as mock_chat:
        res = await client.complete("Hello async", model="test-model", timeout=20.0)
        assert res == "async complete result"
        mock_chat.assert_called_once_with(
            "Hello async",
            model="test-model",
            system=None,
            max_tokens=1024,
            temperature=0.7,
            strip_thinking=True,
            timeout=20.0,
        )


# ---------------------------------------------------------------------------
# Test: async chat methods work correctly (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_async_client_privacy_guard_blocks_api_key():
    """PrivacyGuard must block API keys from being sent via async client."""
    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    malicious_prompt = "My key is AIzaSyABC123def456GHI789jkl012MNO345pq"

    with pytest.raises(ValueError, match="PrivacyGuard"):
        await client.chat(malicious_prompt)


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_async_client_chat_fast_fails_when_circuit_breaker_open():
    """AsyncAIClient.chat() should fail immediately with CircuitBreakerOpenError."""
    from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
    from ccba_ai.fallback import TieredFallbackRouter

    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
    cb.record_failure()
    assert cb.allow_request() is False

    router = TieredFallbackRouter(enable_fallback=False, mock_mode=False)
    client = AsyncAIClient(
        base_url="http://test-gateway/v1",
        api_key="mock-key",
        circuit_breaker=cb,
        fallback_router=router,
        mock_mode=False,
    )

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        with pytest.raises(CircuitBreakerOpenError):
            await client.chat("should fast fail async")
        mock_create.assert_not_called()
