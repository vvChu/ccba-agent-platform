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
async def test_async_client_privacy_guard_blocks_api_key():
    """PrivacyGuard must block API keys from being sent via async client."""
    client = AsyncAIClient(base_url="http://test-gateway/v1", api_key="mock-key")

    malicious_prompt = "My key is AIzaSyABC123def456GHI789jkl012MNO345pq"

    with pytest.raises(ValueError, match="PrivacyGuard"):
        await client.chat(malicious_prompt)
