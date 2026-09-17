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

    with patch.object(client._client.chat.completions, "create", return_value=mock_resp) as mock_create:
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
