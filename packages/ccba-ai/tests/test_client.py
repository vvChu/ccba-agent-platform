"""Tests for AIClient."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from ccba_ai.client import AIClient


class TestAIClientInit:
    """Test AIClient initialization."""

    @patch.dict("os.environ", {"AI_GATEWAY_URL": "http://test:1234/v1"}, clear=False)
    def test_init_from_env(self) -> None:
        """Test client picks up URL from environment."""
        client = AIClient()
        assert "test:1234" in str(client._client.base_url)

    def test_init_explicit_url(self) -> None:
        """Test client uses explicitly provided URL."""
        client = AIClient(base_url="http://explicit:5678/v1")
        assert "explicit:5678" in str(client._client.base_url)

    def test_init_default_model(self) -> None:
        """Test default model is set."""
        client = AIClient()
        assert client.default_model is not None
        assert isinstance(client.default_model, str)

    @patch.dict("os.environ", {"AI_MODEL": "test-model"}, clear=False)
    def test_init_model_from_env(self) -> None:
        """Test model can be set from environment."""
        client = AIClient()
        assert client.default_model == "test-model"

    def test_init_explicit_model(self) -> None:
        """Test client uses explicitly provided model."""
        client = AIClient(default_model="custom-model")
        assert client.default_model == "custom-model"


class TestAIClientChat:
    """Test AIClient.chat() method."""

    def test_chat_returns_string(self) -> None:
        """Test chat returns a string even when content is None."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        # Mock the OpenAI client's completions.create method
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None  # Model refused

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            result = client.chat("test")
            assert result == ""
            assert isinstance(result, str)

    def test_chat_returns_content(self) -> None:
        """Test chat returns actual content."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from AI"

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            result = client.chat("test")
            assert result == "Hello from AI"

    def test_chat_passes_system_message(self) -> None:
        """Test chat includes system message when provided."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"

        with patch.object(
            client._client.chat.completions, "create", return_value=mock_response
        ) as mock_create:
            client.chat("hello", system="You are helpful")
            args = mock_create.call_args
            messages = args.kwargs["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"


class TestAIClientStream:
    """Test AIClient.stream() method."""

    def test_stream_returns_generator(self) -> None:
        """Test stream returns a Generator."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        # Create mock chunks
        chunks = []
        for text in ["Hello", " ", "world"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            chunks.append(chunk)

        with patch.object(client._client.chat.completions, "create", return_value=iter(chunks)):
            result = client.stream("test")
            assert isinstance(result, Generator)
            collected = list(result)
            assert collected == ["Hello", " ", "world"]

    def test_stream_skips_none_content(self) -> None:
        """Test stream skips chunks with None content."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        chunks = []
        for text in ["Hello", None, "world"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            chunks.append(chunk)

        with patch.object(client._client.chat.completions, "create", return_value=iter(chunks)):
            collected = list(client.stream("test"))
            assert collected == ["Hello", "world"]


class TestAIClientChatMulti:
    """Test AIClient.chat_multi() method."""

    def test_chat_multi_returns_string(self) -> None:
        """Test chat_multi returns a string."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Multi response"

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            messages = [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello"},
                {"role": "user", "content": "How are you?"},
            ]
            result = client.chat_multi(messages)
            assert result == "Multi response"

    def test_chat_multi_handles_none(self) -> None:
        """Test chat_multi returns empty string when content is None."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            result = client.chat_multi([{"role": "user", "content": "test"}])
            assert result == ""


class TestAIClientModels:
    """Test AIClient.models() method."""

    def test_models_returns_sorted_list(self) -> None:
        """Test models returns a sorted list of model IDs."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        mock_result = MagicMock()
        model_b = MagicMock()
        model_b.id = "model-b"
        model_a = MagicMock()
        model_a.id = "model-a"
        mock_result.data = [model_b, model_a]

        with patch.object(client._client.models, "list", return_value=mock_result):
            result = client.models()
            assert result == ["model-a", "model-b"]

    def test_models_deduplicates(self) -> None:
        """Test models removes duplicates."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")

        mock_result = MagicMock()
        model_a1 = MagicMock()
        model_a1.id = "model-a"
        model_a2 = MagicMock()
        model_a2.id = "model-a"
        mock_result.data = [model_a1, model_a2]

        with patch.object(client._client.models, "list", return_value=mock_result):
            result = client.models()
            assert result == ["model-a"]


class TestAIClientRepr:
    """Test AIClient.__repr__()."""

    def test_repr_includes_url_and_model(self) -> None:
        """Test repr shows url and model."""
        client = AIClient(base_url="http://test:1/v1", default_model="test-model")
        repr_str = repr(client)
        assert "test:1" in repr_str
        assert "test-model" in repr_str


class TestAIClientRetry:
    """Test AIClient retry and error handling."""

    def test_chat_retries_on_connection_error_and_succeeds(self) -> None:
        """Test chat retries when connection error occurs and succeeds on retry."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake", max_retries=2, retry_delay=0.01)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Recovered response"

        from openai import APIConnectionError

        side_effects = [APIConnectionError(request=MagicMock()), mock_response]
        with patch.object(client._client.chat.completions, "create", side_effect=side_effects) as mock_create:
            result = client.chat("test retry")
            assert result == "Recovered response"
            assert mock_create.call_count == 2

    def test_chat_raises_after_max_retries(self) -> None:
        """Test chat raises exception if retries are exhausted."""
        import pytest
        from openai import APIConnectionError

        client = AIClient(base_url="http://fake:1/v1", api_key="fake", max_retries=2, retry_delay=0.01)

        with patch.object(client._client.chat.completions, "create", side_effect=APIConnectionError(request=MagicMock())) as mock_create:
            with pytest.raises(APIConnectionError):
                client.chat("test retry fail")
            assert mock_create.call_count == 3
