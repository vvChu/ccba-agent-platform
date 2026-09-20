import pytest

from ccba_ai import ai, async_ai


@pytest.mark.fast
@pytest.mark.unit
def test_timeout_scaling_chat():
    ai.mock_mode = True

    # Test explicitly passing timeout
    res = ai.chat("Hello", timeout=10.5)
    assert res

    # Acceptance criteria: ai.chat(..., max_tokens=32768, timeout=180.0) without TypeError
    res_large = ai.chat("Hello large", max_tokens=32768, timeout=180.0)
    assert res_large

    # Large max_tokens -> scaled timeout
    res = ai.chat_multi([{"role": "user", "content": "Hello"}], max_tokens=18000)
    assert res

    # Test chat_with_metadata timeout scaling
    res_meta = ai.chat_with_metadata("Hello", max_tokens=30000)
    assert res_meta.content


@pytest.mark.fast
@pytest.mark.unit
def test_timeout_scaling_kwargs():
    from unittest.mock import MagicMock, patch

    from ccba_ai import AIClient

    client = AIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "OK"
    mock_resp.choices = [mock_choice]

    with patch.object(
        client._client.chat.completions, "create", return_value=mock_resp
    ) as mock_create:
        # Caller did not supply timeout, but max_tokens=25000 -> 25000 / 50.0 = 500.0s
        client.chat("test", max_tokens=25000)
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["timeout"] == 500.0


@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.asyncio
async def test_timeout_scaling_chat_async():
    async_ai.mock_mode = True

    res = await async_ai.chat("Hello", timeout=10.5)
    assert res

    res = await async_ai.chat_multi([{"role": "user", "content": "Hello"}], max_tokens=18000)
    assert res

    res_meta = await async_ai.chat_with_metadata("Hello", max_tokens=30000)
    assert res_meta.content


@pytest.mark.fast
@pytest.mark.unit
def test_adaptive_reasoning_timeout_clamp():
    from unittest.mock import MagicMock, patch

    from ccba_ai import AIClient

    client = AIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False, timeout=60.0)
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "OK"
    mock_resp.choices = [mock_choice]

    with patch.object(
        client._client.chat.completions, "create", return_value=mock_resp
    ) as mock_create:
        # Case 1: Reasoning model, timeout=None, default tokens (auto 16384 -> 16384/50 = 327.68)
        client.chat("test reasoning", model="claude-opus-4-6")
        assert mock_create.call_args.kwargs["timeout"] == max(60.0, 90.0, 16384 / 50.0)
        assert mock_create.call_args.kwargs["timeout"] >= 90.0

        # Case 2: Reasoning model with small custom tokens, timeout=None -> clamped to max(60.0, 90.0, 100/50.0) = 90.0
        client.chat("test reasoning small", model="claude-opus-4-6", max_tokens=100)
        assert mock_create.call_args.kwargs["timeout"] == 90.0

        # Case 3: Reasoning model with explicit caller timeout=10.0 -> preserved strictly
        client.chat("test explicit", model="claude-opus-4-6", timeout=10.0)
        assert mock_create.call_args.kwargs["timeout"] == 10.0

        # Case 4: Non-reasoning model with default tokens -> client.timeout (60.0)
        client.chat("test non-reasoning", model="gemini-3.7-flash")
        assert mock_create.call_args.kwargs["timeout"] == 60.0

        # Case 5: Non-reasoning model with large tokens (>16384) -> scaled
        client.chat("test non-reasoning large", model="gemini-3.7-flash", max_tokens=20000)
        assert mock_create.call_args.kwargs["timeout"] == 20000 / 50.0

        # Case 6: Stream method with explicit timeout
        stream_choice = MagicMock()
        stream_choice.delta.content = "stream chunk"
        stream_choice.message.content = "OK"
        mock_resp.choices = [stream_choice]
        list(client.stream("test stream", model="claude-opus-4-6", timeout=12.5))
        assert mock_create.call_args.kwargs["timeout"] == 12.5

        # Case 7: Complete method alias
        client.complete("test complete", model="claude-opus-4-6", timeout=8.0)
        assert mock_create.call_args.kwargs["timeout"] == 8.0

        # Case 8: chat_with_metadata with explicit timeout
        client.chat_with_metadata("test meta", model="claude-opus-4-6", timeout=25.0)
        assert mock_create.call_args.kwargs["timeout"] == 25.0

        # Case 9: chat_multi with implicit reasoning timeout
        client.chat_multi([{"role": "user", "content": "hi"}], model="claude-opus-4.6")
        assert mock_create.call_args.kwargs["timeout"] >= 90.0

        # Case 10: Stream with empty choices chunk (usage chunk) does not crash
        empty_chunk = MagicMock()
        empty_chunk.choices = []
        normal_chunk = MagicMock()
        normal_chunk.choices = [MagicMock()]
        normal_chunk.choices[0].delta.content = "content chunk"
        with patch.object(
            client._client.chat.completions, "create", return_value=[empty_chunk, normal_chunk]
        ):
            chunks = list(client.stream("test empty chunk", model="claude-opus-4-6"))
            assert chunks == ["content chunk"]


@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.asyncio
async def test_adaptive_reasoning_timeout_clamp_async():
    from unittest.mock import AsyncMock, MagicMock, patch

    from ccba_ai import AsyncAIClient

    client = AsyncAIClient(
        base_url="http://fake:1/v1", api_key="fake", mock_mode=False, timeout=60.0
    )
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "OK"
    mock_resp.choices = [mock_choice]

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_resp
    ) as mock_create:
        # Case 1: Reasoning model, timeout=None -> >= 90.0
        await client.chat("test async reasoning", model="claude-opus-4-6", max_tokens=100)
        assert mock_create.call_args.kwargs["timeout"] == 90.0

        # Case 2: Explicit caller timeout -> preserved
        await client.chat("test async explicit", model="claude-opus-4-6", timeout=10.0)
        assert mock_create.call_args.kwargs["timeout"] == 10.0

        # Case 3: Complete alias async
        await client.complete("test async complete", model="claude-opus-4-6", timeout=14.0)
        assert mock_create.call_args.kwargs["timeout"] == 14.0

        # Case 4: chat_with_metadata async with explicit timeout
        await client.chat_with_metadata("test async meta", model="claude-opus-4.6", timeout=22.0)
        assert mock_create.call_args.kwargs["timeout"] == 22.0

        # Case 5: chat_multi async with implicit reasoning timeout
        await client.chat_multi([{"role": "user", "content": "hi"}], model="claude-opus-4-6")
        assert mock_create.call_args.kwargs["timeout"] >= 90.0

    # Case 6: Async stream with explicit timeout and empty chunk guard
    empty_chunk = MagicMock()
    empty_chunk.choices = []
    normal_chunk = MagicMock()
    normal_chunk.choices = [MagicMock()]
    normal_chunk.choices[0].delta.content = "async stream chunk"

    async def mock_generator():
        yield empty_chunk
        yield normal_chunk

    async def mock_stream_create(**kwargs):
        return mock_generator()

    with patch.object(
        client._client.chat.completions, "create", side_effect=mock_stream_create
    ) as mock_stream:
        chunks = [
            c
            async for c in client.stream("test async stream", model="claude-opus-4.6", timeout=18.0)
        ]
        assert chunks == ["async stream chunk"]
        assert mock_stream.call_args.kwargs["timeout"] == 18.0
