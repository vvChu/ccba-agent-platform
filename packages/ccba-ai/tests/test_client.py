"""Tests for AIClient."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError

from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ccba_ai.client import AIClient
from ccba_ai.fallback import TieredFallbackRouter


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

    def test_init_default_timeout(self) -> None:
        """Test client defaults to 90.0s timeout."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("ccba_ai.client._find_and_load_env"):
                client = AIClient(base_url="http://fake:1/v1", api_key="fake")
                assert client.timeout == 90.0
                assert client._client.timeout == 90.0

    @patch.dict("os.environ", {"AI_GATEWAY_TIMEOUT": "45.0"}, clear=False)
    def test_init_timeout_from_env(self) -> None:
        """Test client picks up timeout from environment."""
        with patch("ccba_ai.client._find_and_load_env"):
            client = AIClient(base_url="http://fake:1/v1", api_key="fake")
            assert client.timeout == 45.0
            assert client._client.timeout == 45.0

    def test_init_explicit_timeout(self) -> None:
        """Test client uses explicitly provided timeout."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake", timeout=30.0)
        assert client.timeout == 30.0
        assert client._client.timeout == 30.0

    def test_url_sanitizer_redirects_8045_explicit(self) -> None:
        """Test URL sanitizer automatically redirects :8045 to :8090."""
        client = AIClient(base_url="http://100.83.192.30:8045/v1")
        assert "8090" in str(client._client.base_url)
        assert "8045" not in str(client._client.base_url)
        assert client.base_url == "http://100.83.192.30:8090/v1"

    @patch.dict("os.environ", {"AI_GATEWAY_URL": "http://localhost:8045/v1"}, clear=False)
    def test_url_sanitizer_redirects_8045_from_env(self) -> None:
        """Test URL sanitizer automatically redirects env var containing :8045 to :8090."""
        with patch("ccba_ai.client._find_and_load_env"):
            client = AIClient()
            assert "8090" in str(client._client.base_url)
            assert "8045" not in str(client._client.base_url)
            assert client.base_url == "http://100.83.192.30:8090/v1"

    @patch.dict("os.environ", {"AI_GATEWAY_URL": ""}, clear=False)
    def test_url_sanitizer_empty_env_fallback(self) -> None:
        """Test URL sanitizer falls back to 8090 when AI_GATEWAY_URL is empty string."""
        with patch("ccba_ai.client._find_and_load_env"):
            client = AIClient()
            assert client.base_url == "http://100.83.192.30:8090/v1"

    def test_url_sanitizer_whitespace_trim(self) -> None:
        """Test URL sanitizer trims whitespace and sanitizes port."""
        client = AIClient(base_url="   http://100.83.192.30:8045/v1\n  ")
        assert client.base_url == "http://100.83.192.30:8090/v1"

    @patch.dict(
        "os.environ", {"AI_GATEWAY_KEY": "", "OPENAI_API_KEY": "fallback-test-key"}, clear=False
    )
    def test_api_key_empty_gateway_key_fallback(self) -> None:
        """Test api_key falls back to OPENAI_API_KEY when AI_GATEWAY_KEY is empty."""
        with patch("ccba_ai.client._find_and_load_env"):
            client = AIClient(base_url="http://fake:1/v1")
            assert client._client.api_key == "fallback-test-key"

    def test_complete_alias_calls_chat(self) -> None:
        """Test complete() acts as an alias for chat()."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")
        with patch.object(client, "chat", return_value="completion result") as mock_chat:
            res = client.complete("Hello", model="test-model", timeout=15.0)
            assert res == "completion result"
            mock_chat.assert_called_once_with(
                "Hello",
                model="test-model",
                system=None,
                max_tokens=1024,
                temperature=0.7,
                strip_thinking=True,
                timeout=15.0,
            )


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

    def test_chat_strip_thinking_default(self) -> None:
        """Test chat automatically strips <think> tags by default."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "<think>Let me ponder...</think>Final Answer"

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            result = client.chat("test")
            assert result == "Final Answer"

    def test_chat_strip_thinking_disabled(self) -> None:
        """Test chat preserves <think> tags when strip_thinking=False."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "<think>Let me ponder...</think>Final Answer"

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            result = client.chat("test", strip_thinking=False)
            assert "<think>Let me ponder...</think>Final Answer" in result

    def test_chat_auto_max_tokens_for_reasoning(self) -> None:
        """Test chat automatically increases max_tokens to 16384 for reasoning models."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Answer"

        with patch.object(
            client._client.chat.completions, "create", return_value=mock_response
        ) as mock_create:
            # When calling reasoning model with default max_tokens=1024
            client.chat("test", model="gemini-3.7-flash-high")
            assert mock_create.call_args.kwargs["max_tokens"] == 16384

            # When calling reasoning model with explicit max_tokens=500
            client.chat("test", model="gemini-3.7-flash-high", max_tokens=500)
            assert mock_create.call_args.kwargs["max_tokens"] == 500

            # When calling standard model with default max_tokens=1024
            client.chat("test", model="gemini-3.7-flash")
            assert mock_create.call_args.kwargs["max_tokens"] == 1024


class TestAIClientChatWithMetadata:
    """Test AIClient.chat_with_metadata() method."""

    def test_chat_with_metadata_returns_chat_result(self) -> None:
        """Test chat_with_metadata returns a ChatResult with usage and latency."""
        from ccba_ai.models import ChatResult

        client = AIClient(base_url="http://fake:1/v1", api_key="fake")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "<think>Think...</think>Result Text"
        mock_response.model = "gemini-3.7-flash"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            res = client.chat_with_metadata("test prompt")
            assert isinstance(res, ChatResult)
            assert res.content == "Result Text"
            assert res.model == "gemini-3.7-flash"
            assert res.usage.prompt_tokens == 100
            assert res.usage.completion_tokens == 50
            assert res.usage.total_tokens == 150
            assert res.latency_ms >= 0.0

    def test_chat_with_metadata_without_usage_object(self) -> None:
        """Test chat_with_metadata handles responses without usage object gracefully."""
        client = AIClient(base_url="http://fake:1/v1", api_key="fake")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "No usage response"
        mock_response.model = "qwen-local-primary"
        mock_response.usage = None

        with patch.object(client._client.chat.completions, "create", return_value=mock_response):
            res = client.chat_with_metadata("test")
            assert res.content == "No usage response"
            assert res.usage.prompt_tokens == 0
            assert res.usage.completion_tokens == 0
            assert res.usage.total_tokens == 0


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
        client = AIClient(
            base_url="http://fake:1/v1", api_key="fake", max_retries=2, retry_delay=0.01
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Recovered response"

        side_effects = [APIConnectionError(request=MagicMock()), mock_response]
        with patch.object(
            client._client.chat.completions, "create", side_effect=side_effects
        ) as mock_create:
            result = client.chat("test retry")
            assert result == "Recovered response"
            assert mock_create.call_count == 2

    def test_chat_raises_after_max_retries(self) -> None:
        """Test chat raises exception if retries are exhausted."""
        router = TieredFallbackRouter(enable_fallback=False, mock_mode=False)
        client = AIClient(
            base_url="http://fake:1/v1",
            api_key="fake",
            max_retries=2,
            retry_delay=0.01,
            fallback_router=router,
            mock_mode=False,
        )

        with patch.object(
            client._client.chat.completions,
            "create",
            side_effect=APIConnectionError(request=MagicMock()),
        ) as mock_create:
            with pytest.raises(APIConnectionError):
                client.chat("test retry fail")
            assert mock_create.call_count == 3

    def test_chat_fast_fails_when_circuit_breaker_open(self) -> None:
        """Test chat fails immediately with CircuitBreakerOpenError without calling API."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
        cb.record_failure()
        assert cb.allow_request() is False

        router = TieredFallbackRouter(enable_fallback=False, mock_mode=False)
        client = AIClient(
            base_url="http://fake:1/v1",
            api_key="fake",
            circuit_breaker=cb,
            fallback_router=router,
            mock_mode=False,
        )

        with patch.object(client._client.chat.completions, "create") as mock_create:
            with pytest.raises(CircuitBreakerOpenError):
                client.chat("should fast fail")
            mock_create.assert_not_called()
