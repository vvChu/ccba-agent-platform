"""Unit tests for MockProvider in ccba_ai.mock_provider."""

import pytest

from ccba_ai import AIClient, AsyncAIClient
from ccba_ai.mock_provider import MockProvider
from ccba_ai.models import ChatResult


def test_mock_provider_generate_response_default():
    """Test MockProvider generates deterministic responses."""
    provider = MockProvider()
    resp = provider.generate_response("Xin chào hệ thống", model="qwen-local-primary")
    assert "[MOCK:qwen-local-primary]" in resp
    assert "Xin chào" in resp


def test_mock_provider_pattern_matching():
    """Test registering and matching custom patterns."""
    provider = MockProvider()
    provider.register_pattern("kiểm tra pccc", "Kết quả thẩm tra PCCC hợp lệ.")

    resp = provider.generate_response("Yêu cầu kiểm tra PCCC công trình A")
    assert resp == "Kết quả thẩm tra PCCC hợp lệ."

    provider.clear_patterns()
    resp2 = provider.generate_response("Yêu cầu kiểm tra PCCC công trình A")
    assert resp2 != "Kết quả thẩm tra PCCC hợp lệ."


def test_mock_provider_json_auto_detection():
    """Test MockProvider generates valid JSON when requested in prompt."""
    import json

    provider = MockProvider()

    resp = provider.generate_response("Trích xuất thông tin dưới dạng JSON:")
    data = json.loads(resp)
    assert data["status"] == "success"
    assert data["mock"] is True


def test_ai_client_with_mock_mode_sync():
    """Test AIClient operating in explicit mock_mode."""
    client = AIClient(mock_mode=True)

    # Test chat
    reply = client.chat("Test mock chat prompt")
    assert "[MOCK:" in reply

    # Test chat_with_metadata
    result = client.chat_with_metadata("Test metadata", model="gemini-3.7-flash")
    assert isinstance(result, ChatResult)
    assert result.model == "gemini-3.7-flash"
    assert result.usage.prompt_tokens > 0
    assert result.usage.completion_tokens > 0

    # Test stream
    stream_chunks = list(client.stream("Stream test"))
    assert len(stream_chunks) > 0
    assert "".join(stream_chunks) == client.chat("Stream test")

    # Test chat_multi
    multi_reply = client.chat_multi([{"role": "user", "content": "Multi-turn prompt"}])
    assert "[MOCK:" in multi_reply

    # Test models
    models = client.models()
    assert "gemini-3.7-flash" in models
    assert "qwen-local-primary" in models


@pytest.mark.asyncio
async def test_async_ai_client_with_mock_mode():
    """Test AsyncAIClient operating in explicit mock_mode."""
    client = AsyncAIClient(mock_mode=True)

    # Test async chat
    reply = await client.chat("Async prompt")
    assert "[MOCK:" in reply

    # Test async chat_with_metadata
    res = await client.chat_with_metadata("Async metadata", model="gemini-3.7-flash-high")
    assert isinstance(res, ChatResult)
    assert res.model == "gemini-3.7-flash-high"

    # Test async stream
    chunks = []
    async for chunk in client.stream("Async stream"):
        chunks.append(chunk)
    assert len(chunks) > 0

    # Test async chat_multi
    multi_res = await client.chat_multi([{"role": "user", "content": "Async multi"}])
    assert "[MOCK:" in multi_res

    # Test async models
    models = await client.models()
    assert "gemini-3.7-flash" in models
