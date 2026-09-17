from unittest.mock import MagicMock, patch

import pytest

from ccba_ai import AIClient, AsyncAIClient
from ccba_ai.routing import resolve_max_tokens


@pytest.mark.fast
@pytest.mark.unit
def test_resolve_max_tokens():
    # Regular model, default tokens
    assert resolve_max_tokens("gemini-3.7-flash", 1024) == 1024

    # Reasoning model, default tokens -> scaled to 16384
    assert resolve_max_tokens("gemini-3.7-flash-high", 1024) == 16384

    # Reasoning model, explicit tokens -> preserved
    assert resolve_max_tokens("gemini-3.7-flash-high", 4096) == 4096

    # Different baseline
    assert resolve_max_tokens("gemini-3.7-flash-high", 2048, baseline_default=2048) == 16384


@pytest.mark.fast
@pytest.mark.unit
def test_stream_reasoning_tokens_allocation():
    client = AIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta.content = "stream chunk"

    with patch.object(client._client.chat.completions, "create", return_value=[mock_chunk]) as mock_create:
        chunks = list(client.stream("hello", model="gemini-3.7-flash-high"))
        assert chunks == ["stream chunk"]
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["max_tokens"] == 16384


@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_stream_reasoning_tokens_allocation():
    client = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta.content = "async chunk"

    async def mock_generator():
        yield mock_chunk

    async def mock_create_fn(**kwargs):
        return mock_generator()

    with patch.object(client._client.chat.completions, "create", side_effect=mock_create_fn) as mock_create:
        chunks = [c async for c in client.stream("hello", model="gemini-3.7-flash-high")]
        assert chunks == ["async chunk"]
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["max_tokens"] == 16384



