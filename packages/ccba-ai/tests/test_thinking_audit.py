import pytest

from ccba_ai.llm_utils import extract_thinking, extract_thinking_and_content


@pytest.mark.fast
@pytest.mark.unit
def test_extract_thinking():
    # 1. Closed tags
    text = "<think>I am thinking</think>\nHere is the answer."
    thinking, content = extract_thinking_and_content(text)
    assert thinking == "I am thinking"
    assert content == "Here is the answer."

    # 2. Nested/Multiple tags
    text = "<think>Think 1</think>\n<think>Think 2</think>\nAnswer"
    thinking, content = extract_thinking_and_content(text)
    assert thinking == "Think 1\n\nThink 2"
    assert content == "Answer"

    # 3. Unclosed tag
    text = "Intro\n<think>I am thinking but cut off"
    thinking, content = extract_thinking_and_content(text)
    assert thinking == "I am thinking but cut off"
    assert content == "Intro"

    # 4. No tags
    text = "Just the answer"
    thinking, content = extract_thinking_and_content(text)
    assert thinking == ""
    assert content == "Just the answer"

    # 5. Extract thinking helper
    assert extract_thinking("<think>Think</think>Test") == "Think"

    # 6. Real nested tags
    text = "A <think> B <think> C </think> D </think> E"
    thinking, content = extract_thinking_and_content(text)
    assert thinking == "B <think> C </think> D"
    assert content == "A  E"


@pytest.mark.fast
@pytest.mark.unit
def test_chat_result_thinking_from_think_tags():
    from unittest.mock import MagicMock, patch

    from ccba_ai import AIClient

    client = AIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "<think>Audit step 1: verifying code</think>All clear!"
    mock_choice.message.reasoning_content = None
    mock_resp.choices = [mock_choice]
    mock_resp.model = "gemini-3.7-flash-high"
    mock_resp.usage = None

    with patch.object(client._client.chat.completions, "create", return_value=mock_resp):
        res = client.chat_with_metadata("Audit this", strip_thinking=True)
        assert res.thinking == "Audit step 1: verifying code"
        assert res.content == "All clear!"


@pytest.mark.fast
@pytest.mark.unit
def test_chat_result_thinking_from_reasoning_content():
    from unittest.mock import MagicMock, patch

    from ccba_ai import AIClient

    client = AIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "All clear!"
    mock_choice.message.reasoning_content = "Native reasoning audit trail"
    mock_resp.choices = [mock_choice]
    mock_resp.model = "gemini-3.7-flash-high"
    mock_resp.usage = None

    with patch.object(client._client.chat.completions, "create", return_value=mock_resp):
        res = client.chat_with_metadata("Audit this")
        assert res.thinking == "Native reasoning audit trail"
        assert res.content == "All clear!"


@pytest.mark.fast
@pytest.mark.unit
def test_chat_result_thinking_privacy_guard_blocks_reasoning_content_leak():
    from unittest.mock import MagicMock, patch

    from ccba_ai import AIClient

    client = AIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Normal output without keys."
    mock_choice.message.reasoning_content = (
        "Leaking key: AIzaSyDummyGeminiKey_1234567890abcdef in reasoning"
    )
    mock_resp.choices = [mock_choice]
    mock_resp.model = "gemini-3.7-flash-high"
    mock_resp.usage = None

    with patch.object(client._client.chat.completions, "create", return_value=mock_resp):
        with pytest.raises(ValueError, match="Security Violation: Detected sensitive API Key leak"):
            client.chat_with_metadata("Audit this")


@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_chat_result_thinking_privacy_guard_blocks_reasoning_content_leak():
    from unittest.mock import AsyncMock, MagicMock, patch

    from ccba_ai import AsyncAIClient

    client = AsyncAIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Normal output without keys."
    mock_choice.message.reasoning_content = (
        "Leaking key: AIzaSyDummyGeminiKey_1234567890abcdef in async reasoning"
    )
    mock_resp.choices = [mock_choice]
    mock_resp.model = "gemini-3.7-flash-high"
    mock_resp.usage = None

    with patch.object(
        client._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_resp
    ):
        with pytest.raises(ValueError, match="Security Violation: Detected sensitive API Key leak"):
            await client.chat_with_metadata("Audit this")
