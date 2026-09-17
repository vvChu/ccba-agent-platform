import asyncio
import os
import time
from collections.abc import AsyncGenerator, Callable, Generator
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, OpenAI

from ccba_ai.circuit_breaker import CircuitBreaker
from ccba_ai.fallback import TieredFallbackRouter, is_mock_mode_enabled
from ccba_ai.hooks import PrivacyGuardHook
from ccba_ai.llm_utils import strip_think_tags
from ccba_ai.mock_provider import MockProvider
from ccba_ai.models import ChatResult, ChatUsage
from ccba_ai.routing import resolve_max_tokens

RETRYABLE_EXCEPTIONS = (APIConnectionError, APITimeoutError)


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(exc, APIStatusError) and getattr(exc, "status_code", 0) >= 500:
        return True
    return False


def _retry_sync(
    fn: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    circuit_breaker: CircuitBreaker | None = None,
) -> Any:
    if circuit_breaker is not None:
        circuit_breaker.check_allowed()

    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            result = fn()
            if circuit_breaker is not None:
                circuit_breaker.record_success()
            return result
        except Exception as e:
            if _is_retryable_exception(e):
                if circuit_breaker is not None:
                    circuit_breaker.record_failure(e)
            if attempt < max_retries and _is_retryable_exception(e):
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise


async def _retry_async(
    coro_fn: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    circuit_breaker: CircuitBreaker | None = None,
) -> Any:
    if circuit_breaker is not None:
        circuit_breaker.check_allowed()

    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            result = await coro_fn()
            if circuit_breaker is not None:
                circuit_breaker.record_success()
            return result
        except Exception as e:
            if _is_retryable_exception(e):
                if circuit_breaker is not None:
                    circuit_breaker.record_failure(e)
            if attempt < max_retries and _is_retryable_exception(e):
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                raise


def _find_and_load_env() -> None:
    """Recursively search upward from CWD to find and load .env or .env.ai-gateway."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    current = Path.cwd()
    # Search up to 5 levels upward
    for _ in range(6):
        for name in (".env.ai-gateway", ".env"):
            env_path = current / name
            if env_path.exists():
                load_dotenv(env_path)
                return
        if current.parent == current:
            break
        current = current.parent


class AIClient:
    """Lightweight AI Gateway client — wraps OpenAI SDK with multi-tier failover and mock support."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        circuit_breaker: CircuitBreaker | None = None,
        fallback_router: TieredFallbackRouter | None = None,
        enable_failover: bool = True,
        mock_mode: bool | None = None,
        mock_provider: MockProvider | None = None,
    ):
        try:
            _find_and_load_env()
        except Exception:
            pass

        if timeout is not None:
            self.timeout = float(timeout)
        else:
            try:
                self.timeout = float(os.environ.get("AI_GATEWAY_TIMEOUT", "60.0"))
            except ValueError:
                self.timeout = 60.0

        self.mock_mode = mock_mode if mock_mode is not None else is_mock_mode_enabled()
        if mock_provider is not None:
            self.mock_provider = mock_provider
        elif (
            fallback_router is not None
            and getattr(fallback_router, "mock_provider", None) is not None
        ):
            self.mock_provider = fallback_router.mock_provider
        else:
            self.mock_provider = MockProvider()

        self.fallback_router = fallback_router or TieredFallbackRouter(
            mock_provider=self.mock_provider,
            enable_fallback=enable_failover,
            mock_mode=self.mock_mode,
        )

        self._client = OpenAI(
            base_url=base_url or os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1"),
            api_key=api_key
            or os.environ.get(
                "AI_GATEWAY_KEY", os.environ.get("OPENAI_API_KEY", "mock-key-for-ci")
            ),
            timeout=self.timeout,
        )
        self.default_model = default_model or os.environ.get("AI_MODEL", "qwen-local-primary")
        self.privacy_guard = PrivacyGuardHook()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.circuit_breaker = circuit_breaker if circuit_breaker is not None else CircuitBreaker()

    def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        strip_thinking: bool = True,
        timeout: float | None = None,
    ) -> str:
        """Send a chat message and get a text response.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response (auto-allocated to 16384 for reasoning models if at default 1024).
            temperature: Sampling temperature (0.0–2.0).
            strip_thinking: If True, automatically strips <think>...</think> tags from output.

        Returns:
            The assistant's response text, or empty string if model refused.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384
        )

        if timeout is not None:
            effective_timeout = float(timeout)
        elif effective_max_tokens > 16384:
            effective_timeout = max(self.timeout, effective_max_tokens / 50.0)
        else:
            effective_timeout = self.timeout

        def _call(client_inst: Any, m: str) -> Any:
            kwargs: dict[str, Any] = {
                "model": m,
                "messages": messages,
                "max_tokens": effective_max_tokens,
                "temperature": temperature,
                "timeout": effective_timeout,
            }
            return client_inst.chat.completions.create(**kwargs)

        def _primary_call() -> Any:
            return _retry_sync(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = self.fallback_router.execute_sync(
            _primary_call,
            model=target_model,
            timeout=effective_timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=_call,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        if strip_thinking:
            response_text = strip_think_tags(response_text)
        return response_text

    def chat_with_metadata(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        strip_thinking: bool = True,
        timeout: float | None = None,
    ) -> ChatResult:
        """Send a chat message and receive structured result with latency and token usage.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response (auto-allocated to 16384 for reasoning models if at default 1024).
            temperature: Sampling temperature (0.0–2.0).
            strip_thinking: If True, automatically strips <think>...</think> tags from output.

        Returns:
            ChatResult object containing content, model, usage, latency_ms, and raw_response.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384
        )

        if timeout is not None:
            effective_timeout = float(timeout)
        elif effective_max_tokens > 16384:
            effective_timeout = max(self.timeout, effective_max_tokens / 50.0)
        else:
            effective_timeout = self.timeout

        def _call(client_inst: Any, m: str) -> Any:
            kwargs: dict[str, Any] = {
                "model": m,
                "messages": messages,
                "max_tokens": effective_max_tokens,
                "temperature": temperature,
                "timeout": effective_timeout,
            }
            return client_inst.chat.completions.create(**kwargs)

        def _primary_call() -> Any:
            return _retry_sync(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        start_time = time.perf_counter()
        response = self.fallback_router.execute_sync(
            _primary_call,
            model=target_model,
            timeout=effective_timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=_call,
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        msg = response.choices[0].message
        response_text = msg.content or ""
        self.privacy_guard.check_content(response_text)

        from ccba_ai.llm_utils import LLMOutputParser

        thinking = getattr(msg, "reasoning_content", None)
        if not isinstance(thinking, str):
            thinking = None
        extracted_thinking, content = LLMOutputParser.extract_thinking_and_content(response_text)
        if not thinking:
            thinking = extracted_thinking

        if strip_thinking:
            response_text = content

        usage = ChatUsage()
        if hasattr(response, "usage") and response.usage:
            usage = ChatUsage(
                prompt_tokens=getattr(response.usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(response.usage, "completion_tokens", 0) or 0,
                total_tokens=getattr(response.usage, "total_tokens", 0) or 0,
            )

        resolved_model = getattr(response, "model", target_model) or target_model

        return ChatResult(
            content=response_text,
            thinking=thinking or "",
            model=resolved_model,
            usage=usage,
            latency_ms=latency_ms,
            raw_response=response,
        )

    def stream(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Stream a chat response, yielding text chunks as they arrive.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0–2.0).

        Yields:
            Text chunks of the assistant response as they stream in.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384
        )

        def _call(client_inst: Any, m: str) -> Any:
            return client_inst.chat.completions.create(
                model=m,
                messages=messages,
                max_tokens=effective_max_tokens,
                temperature=temperature,
                stream=True,
            )

        def _primary_call() -> Any:
            return _retry_sync(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = self.fallback_router.execute_sync(
            _primary_call,
            model=target_model,
            timeout=self.timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=_call,
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                self.privacy_guard.check_content(content)
                yield content

    def chat_multi(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        strip_thinking: bool = True,
        timeout: float | None = None,
    ) -> str:
        """Send a multi-turn conversation and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model name override. Uses default_model if None.
            max_tokens: Maximum tokens in the response (auto-allocated to 16384 for reasoning models if at default 2048).
            temperature: Sampling temperature (0.0–2.0).
            strip_thinking: If True, automatically strips <think>...</think> tags from output.
            timeout: Optional per-request timeout in seconds.

        Returns:
            The assistant's response text, or empty string if model refused.
        """
        for msg in messages:
            self.privacy_guard.check_content(msg.get("content", ""))

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=2048, reasoning_allocation=16384
        )

        create_kwargs: dict[str, Any] = {
            "messages": messages,
            "max_tokens": effective_max_tokens,
            "temperature": temperature,
        }

        if timeout is not None:
            effective_timeout = float(timeout)
        elif effective_max_tokens > 16384:
            effective_timeout = max(self.timeout, effective_max_tokens / 50.0)
        else:
            effective_timeout = self.timeout

        create_kwargs["timeout"] = effective_timeout

        def _call(client_inst: Any, m: str) -> Any:
            kwargs = dict(create_kwargs)
            kwargs["model"] = m
            return client_inst.chat.completions.create(**kwargs)

        def _primary_call() -> Any:
            return _retry_sync(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = self.fallback_router.execute_sync(
            _primary_call,
            model=target_model,
            timeout=effective_timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=_call,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        if strip_thinking:
            response_text = strip_think_tags(response_text)
        return response_text

    def models(self) -> list[str]:
        """List all available models on the gateway.

        Returns:
            Sorted list of unique model ID strings.
        """

        def _call(client_inst: Any, m: str) -> Any:
            return client_inst.models.list()

        def _primary_call() -> Any:
            return _retry_sync(
                lambda: self._client.models.list(),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        result = self.fallback_router.execute_sync(
            _primary_call,
            model=self.default_model,
            timeout=self.timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=_call,
        )
        return sorted({m.id for m in result.data})

    def transcribe(
        self,
        audio_path: str | Path,
        *,
        model: str = "audio-primary",
        language: str = "vi",
    ) -> str:
        """Transcribe an audio file via the AI Gateway.

        Args:
            audio_path: Path to the audio file (mp3, wav, m4a, etc.).
            model: Transcription model to use on the gateway.
            language: BCP-47 language code (e.g. 'vi', 'en').

        Returns:
            The transcribed text, stripped of leading/trailing whitespace.

        Raises:
            FileNotFoundError: If the audio file does not exist.
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file '{audio_path}' not found.")

        def _call(client_inst: Any, m: str) -> Any:
            with open(path, "rb") as f:
                return client_inst.audio.transcriptions.create(
                    model=m,
                    file=f,
                    language=language,
                    response_format="text",
                )

        def _primary_call() -> Any:
            return _retry_sync(
                lambda: _call(self._client, model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = self.fallback_router.execute_sync(
            _primary_call,
            model=model,
            timeout=self.timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=_call,
        )
        return str(response).strip()

    def embed(
        self, texts: str | list[str], *, model: str = "gemini-embedding-2"
    ) -> list[list[float]]:
        """Embed a text or list of texts via the AI Gateway.

        Args:
            texts: A string or list of strings to embed.
            model: Embedding model to use on the gateway.

        Returns:
            A list of embedding vectors (one for each input string).
        """
        text_list = [texts] if isinstance(texts, str) else texts

        if self.mock_mode:
            return [[0.1] * 3072 for _ in text_list]

        def _call(client_inst: Any, m: str) -> Any:
            return client_inst.embeddings.create(
                model=m, input=text_list, extra_body={"drop_params": True}
            )

        def _primary_call() -> Any:
            return _retry_sync(
                lambda: _call(self._client, model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = self.fallback_router.execute_sync(
            _primary_call,
            model=model,
            timeout=self.timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=_call,
        )
        return [item.embedding for item in response.data]

    def encode_image(
        self,
        image_path: str | Path,
        *,
        max_pixels: int = 1024,
        quality: int = 85,
    ) -> str:
        """Resize and base64-encode an image for vision APIs.

        Args:
            image_path: Path to the image file.
            max_pixels: The maximum side length (width or height) in pixels to resize the image to.
            quality: Compression quality (1-95) for JPEG.

        Returns:
            The base64 encoded string of the compressed JPEG image.
        """
        import base64

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file '{image_path}' not found.")

        try:
            from io import BytesIO

            from PIL import Image, ImageOps

            raw_img = Image.open(path)
            img: Any = ImageOps.exif_transpose(raw_img)  # Auto-orient
            img.thumbnail((max_pixels, max_pixels), Image.Resampling.LANCZOS)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            buf = BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            # Fallback: raw base64 without resize
            return base64.b64encode(path.read_bytes()).decode("utf-8")

    def close(self) -> None:
        """Close the underlying OpenAI client session."""
        try:
            self._client.close()
        except Exception:
            pass

    def __repr__(self) -> str:
        return (
            f"AIClient(url={getattr(self._client, 'base_url', 'mock')}, model={self.default_model})"
        )


class AsyncAIClient:
    """Async Lightweight AI Gateway client — wraps AsyncOpenAI SDK with multi-tier failover and mock support."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        circuit_breaker: CircuitBreaker | None = None,
        fallback_router: TieredFallbackRouter | None = None,
        enable_failover: bool = True,
        mock_mode: bool | None = None,
        mock_provider: MockProvider | None = None,
    ):
        try:
            _find_and_load_env()
        except Exception:
            pass

        if timeout is not None:
            self.timeout = float(timeout)
        else:
            try:
                self.timeout = float(os.environ.get("AI_GATEWAY_TIMEOUT", "60.0"))
            except ValueError:
                self.timeout = 60.0

        self.mock_mode = mock_mode if mock_mode is not None else is_mock_mode_enabled()
        if mock_provider is not None:
            self.mock_provider = mock_provider
        elif (
            fallback_router is not None
            and getattr(fallback_router, "mock_provider", None) is not None
        ):
            self.mock_provider = fallback_router.mock_provider
        else:
            self.mock_provider = MockProvider()

        self.fallback_router = fallback_router or TieredFallbackRouter(
            mock_provider=self.mock_provider,
            enable_fallback=enable_failover,
            mock_mode=self.mock_mode,
        )

        self._client = AsyncOpenAI(
            base_url=base_url or os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1"),
            api_key=api_key
            or os.environ.get(
                "AI_GATEWAY_KEY", os.environ.get("OPENAI_API_KEY", "mock-key-for-ci")
            ),
            timeout=self.timeout,
        )
        self.default_model = default_model or os.environ.get("AI_MODEL", "qwen-local-primary")
        self.privacy_guard = PrivacyGuardHook()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.circuit_breaker = circuit_breaker if circuit_breaker is not None else CircuitBreaker()

    async def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        strip_thinking: bool = True,
        timeout: float | None = None,
    ) -> str:
        """Send an async chat message and get a text response.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response (auto-allocated to 16384 for reasoning models if at default 1024).
            temperature: Sampling temperature (0.0–2.0).
            strip_thinking: If True, automatically strips <think>...</think> tags from output.

        Returns:
            The assistant's response text, or empty string if model refused.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384
        )

        if timeout is not None:
            effective_timeout = float(timeout)
        elif effective_max_tokens > 16384:
            effective_timeout = max(self.timeout, effective_max_tokens / 50.0)
        else:
            effective_timeout = self.timeout

        async def _call(client_inst: Any, m: str) -> Any:
            kwargs: dict[str, Any] = {
                "model": m,
                "messages": messages,
                "max_tokens": effective_max_tokens,
                "temperature": temperature,
                "timeout": effective_timeout,
            }
            return await client_inst.chat.completions.create(**kwargs)

        async def _primary_call() -> Any:
            return await _retry_async(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = await self.fallback_router.execute_async(
            _primary_call,
            model=target_model,
            timeout=effective_timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_coro_builder=_call,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        if strip_thinking:
            response_text = strip_think_tags(response_text)
        return response_text

    async def chat_with_metadata(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        strip_thinking: bool = True,
        timeout: float | None = None,
    ) -> ChatResult:
        """Send an async chat message and receive structured result with latency and token usage.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response (auto-allocated to 16384 for reasoning models if at default 1024).
            temperature: Sampling temperature (0.0–2.0).
            strip_thinking: If True, automatically strips <think>...</think> tags from output.

        Returns:
            ChatResult object containing content, model, usage, latency_ms, and raw_response.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384
        )

        if timeout is not None:
            effective_timeout = float(timeout)
        elif effective_max_tokens > 16384:
            effective_timeout = max(self.timeout, effective_max_tokens / 50.0)
        else:
            effective_timeout = self.timeout

        async def _call(client_inst: Any, m: str) -> Any:
            kwargs: dict[str, Any] = {
                "model": m,
                "messages": messages,
                "max_tokens": effective_max_tokens,
                "temperature": temperature,
                "timeout": effective_timeout,
            }
            return await client_inst.chat.completions.create(**kwargs)

        async def _primary_call() -> Any:
            return await _retry_async(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        start_time = time.perf_counter()
        response = await self.fallback_router.execute_async(
            _primary_call,
            model=target_model,
            timeout=effective_timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_coro_builder=_call,
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        msg = response.choices[0].message
        response_text = msg.content or ""
        self.privacy_guard.check_content(response_text)

        from ccba_ai.llm_utils import LLMOutputParser

        thinking = getattr(msg, "reasoning_content", None)
        if not isinstance(thinking, str):
            thinking = None
        extracted_thinking, content = LLMOutputParser.extract_thinking_and_content(response_text)
        if not thinking:
            thinking = extracted_thinking

        if strip_thinking:
            response_text = content

        usage = ChatUsage()
        if hasattr(response, "usage") and response.usage:
            usage = ChatUsage(
                prompt_tokens=getattr(response.usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(response.usage, "completion_tokens", 0) or 0,
                total_tokens=getattr(response.usage, "total_tokens", 0) or 0,
            )

        resolved_model = getattr(response, "model", target_model) or target_model

        return ChatResult(
            content=response_text,
            thinking=thinking or "",
            model=resolved_model,
            usage=usage,
            latency_ms=latency_ms,
            raw_response=response,
        )

    async def stream(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream an async chat response, yielding text chunks as they arrive.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0–2.0).

        Yields:
            Text chunks of the assistant response as they stream in.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384
        )

        async def _call(client_inst: Any, m: str) -> Any:
            return await client_inst.chat.completions.create(
                model=m,
                messages=messages,
                max_tokens=effective_max_tokens,
                temperature=temperature,
                stream=True,
            )

        async def _primary_call() -> Any:
            return await _retry_async(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = await self.fallback_router.execute_async(
            _primary_call,
            model=target_model,
            timeout=self.timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_coro_builder=_call,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                self.privacy_guard.check_content(content)
                yield content

    async def chat_multi(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        strip_thinking: bool = True,
        timeout: float | None = None,
    ) -> str:
        """Send an async multi-turn conversation and get a response."""
        for msg in messages:
            self.privacy_guard.check_content(msg.get("content", ""))

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model, max_tokens, baseline_default=2048, reasoning_allocation=16384
        )

        create_kwargs: dict[str, Any] = {
            "messages": messages,
            "max_tokens": effective_max_tokens,
            "temperature": temperature,
        }

        if timeout is not None:
            effective_timeout = float(timeout)
        elif effective_max_tokens > 16384:
            effective_timeout = max(self.timeout, effective_max_tokens / 50.0)
        else:
            effective_timeout = self.timeout

        create_kwargs["timeout"] = effective_timeout

        async def _call(client_inst: Any, m: str) -> Any:
            kwargs = dict(create_kwargs)
            kwargs["model"] = m
            return await client_inst.chat.completions.create(**kwargs)

        async def _primary_call() -> Any:
            return await _retry_async(
                lambda: _call(self._client, target_model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = await self.fallback_router.execute_async(
            _primary_call,
            model=target_model,
            timeout=effective_timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_coro_builder=_call,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        if strip_thinking:
            response_text = strip_think_tags(response_text)
        return response_text

    async def models(self) -> list[str]:
        """List all available models on the gateway.

        Returns:
            Sorted list of unique model ID strings.
        """

        async def _call(client_inst: Any, m: str) -> Any:
            return await client_inst.models.list()

        async def _primary_call() -> Any:
            return await _retry_async(
                lambda: self._client.models.list(),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        result = await self.fallback_router.execute_async(
            _primary_call,
            model=self.default_model,
            timeout=self.timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_coro_builder=_call,
        )
        return sorted({m.id for m in result.data})

    async def embed(
        self, texts: str | list[str], *, model: str = "gemini-embedding-2"
    ) -> list[list[float]]:
        """Embed a text or list of texts via the AI Gateway (async).

        Args:
            texts: A string or list of strings to embed.
            model: Embedding model to use on the gateway.

        Returns:
            A list of embedding vectors (one for each input string).
        """
        text_list = [texts] if isinstance(texts, str) else texts

        if self.mock_mode:
            return [[0.1] * 3072 for _ in text_list]

        async def _call(client_inst: Any, m: str) -> Any:
            return await client_inst.embeddings.create(
                model=m, input=text_list, extra_body={"drop_params": True}
            )

        async def _primary_call() -> Any:
            return await _retry_async(
                lambda: _call(self._client, model),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
                circuit_breaker=self.circuit_breaker,
            )

        response = await self.fallback_router.execute_async(
            _primary_call,
            model=model,
            timeout=self.timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_coro_builder=_call,
        )
        return [item.embedding for item in response.data]

    async def aclose(self) -> None:
        """Close the underlying AsyncOpenAI client session."""
        try:
            await self._client.close()
        except Exception:
            pass

    async def close(self) -> None:
        """Alias for aclose()."""
        await self.aclose()

    def __repr__(self) -> str:
        return f"AsyncAIClient(url={getattr(self._client, 'base_url', 'mock')}, model={self.default_model})"
