import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator, Callable, Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, OpenAI

from ccba_ai.circuit_breaker import CircuitBreaker
from ccba_ai.fallback import TieredFallbackRouter, is_mock_mode_enabled
from ccba_ai.hooks import PrivacyGuardHook
from ccba_ai.llm_utils import LLMOutputParser, strip_think_tags
from ccba_ai.mock_provider import MockProvider
from ccba_ai.models import ChatResult, ChatUsage
from ccba_ai.routing import ModelArchetype, is_reasoning_model, resolve_max_tokens

logger = logging.getLogger("ccba_ai.client")
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


def _sanitize_gateway_url(url: str | None) -> str:
    """Sanitize gateway URL redirecting legacy port :8045 to centralized port :8090."""
    raw = (
        (url.strip() if url and url.strip() else None)
        or (os.environ.get("AI_GATEWAY_URL") or "").strip()
        or "http://100.83.192.30:8090/v1"  # ccba:allow-raw-ip
    )
    if ":8045" in raw:
        logger.warning(
            "Legacy AI Gateway port :8045 detected in URL (%s). Automatically redirecting to http://100.83.192.30:8090/v1",  # ccba:allow-raw-ip
            raw,
        )
        return "http://100.83.192.30:8090/v1"  # ccba:allow-raw-ip
    return raw


def _compute_effective_timeout(
    model: str,
    base_timeout: float,
    effective_max_tokens: int,
    timeout: float | None = None,
) -> float:
    """Compute effective timeout adhering to Adaptive Reasoning Timeout Clamp.

    - If caller explicitly passed timeout: respect float(timeout).
    - If timeout is None:
      * If reasoning model: max(base_timeout, 90.0, effective_max_tokens / 50.0).
      * If non-reasoning but effective_max_tokens > 16384: max(base_timeout, effective_max_tokens / 50.0).
      * Otherwise: base_timeout.
    """
    if timeout is not None:
        return float(timeout)
    if is_reasoning_model(model):
        return max(base_timeout, 90.0, effective_max_tokens / 50.0)
    if effective_max_tokens > 16384:
        return max(base_timeout, effective_max_tokens / 50.0)
    return base_timeout


@dataclass(frozen=True)
class _ChatCallSpec:
    """Immutable in-process specification for an OpenAI-compatible chat call."""

    target_model: str
    effective_timeout: float
    create_kwargs: dict[str, Any]

    def as_call_fn(self) -> Callable[[Any, str], Any]:
        """Return a(client, model) callable for sync or async chat.completions.create."""
        return lambda c, m: c.chat.completions.create(**{**self.create_kwargs, "model": m})


def _resolve_timeout_value(timeout: float | None) -> float:
    """Resolve explicit timeout or fallback to AI_GATEWAY_TIMEOUT environment variable."""
    if timeout is not None:
        return float(timeout)
    try:
        return float(os.environ.get("AI_GATEWAY_TIMEOUT", "90.0"))
    except ValueError:
        return 90.0


def _resolve_api_key(api_key: str | None) -> str:
    """Resolve API key from explicit value or ordered environment variables."""
    for env_key in ("AI_GATEWAY_KEY", "CCBA_AI_API_KEY", "LITELLM_API_KEY", "OPENAI_API_KEY"):
        if api_key:
            return api_key
        api_key = os.environ.get(env_key)
    return api_key or "mock-key-for-ci"


def _extract_chat_usage(response: Any) -> ChatUsage:
    """Extract normalized integer ChatUsage from an OpenAI-compatible response."""
    u = getattr(response, "usage", None)
    if not u:
        return ChatUsage()
    p, c, t = (
        getattr(u, "prompt_tokens", 0),
        getattr(u, "completion_tokens", 0),
        getattr(u, "total_tokens", 0),
    )
    return ChatUsage(
        prompt_tokens=p if isinstance(p, int) else 0,
        completion_tokens=c if isinstance(c, int) else 0,
        total_tokens=t if isinstance(t, int) else 0,
    )


class _BaseAIClient:
    """Shared in-process core module for AIClient and AsyncAIClient."""

    _client_cls: type[Any] = OpenAI
    _client: Any

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
    ) -> None:
        try:
            _find_and_load_env()
        except Exception:
            pass

        self.timeout = _resolve_timeout_value(timeout)
        self._mock_mode = mock_mode if mock_mode is not None else is_mock_mode_enabled()
        router_mock = getattr(fallback_router, "mock_provider", None) if fallback_router else None
        self.mock_provider = mock_provider or router_mock or MockProvider()
        self.fallback_router = fallback_router or TieredFallbackRouter(
            mock_provider=self.mock_provider,
            enable_fallback=enable_failover,
            mock_mode=self._mock_mode,
        )
        self.base_url = _sanitize_gateway_url(base_url)
        self.default_model = default_model or os.environ.get("AI_MODEL", ModelArchetype.LOCAL)
        self.privacy_guard = PrivacyGuardHook()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.circuit_breaker = circuit_breaker if circuit_breaker is not None else CircuitBreaker()
        key_val = _resolve_api_key(api_key)
        self._client = self._client_cls(
            base_url=self.base_url,
            api_key=key_val,
            timeout=self.timeout,
        )

    @property
    def mock_mode(self) -> bool:
        return self._mock_mode

    @mock_mode.setter
    def mock_mode(self, value: bool) -> None:
        self._mock_mode = bool(value)
        if hasattr(self, "fallback_router") and self.fallback_router is not None:
            self.fallback_router.mock_mode = bool(value)

    def _prepare_chat_call(
        self,
        messages_or_prompt: str | list[dict[str, Any]],
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        baseline_default: int = 1024,
        temperature: float = 0.7,
        timeout: float | None = None,
        stream: bool = False,
    ) -> _ChatCallSpec:
        """Validate input privacy, resolve reasoning token/timeout clamp, and build call spec."""
        if isinstance(messages_or_prompt, str):
            self.privacy_guard.check_content(messages_or_prompt)
            messages: list[dict[str, Any]] = (
                [{"role": "system", "content": system}] if system else []
            )
            messages.append({"role": "user", "content": messages_or_prompt})
        else:
            for msg in messages_or_prompt:
                self.privacy_guard.check_content(msg.get("content", ""))
            messages = messages_or_prompt

        target_model = model or self.default_model
        effective_max_tokens = resolve_max_tokens(
            target_model,
            max_tokens,
            baseline_default=baseline_default,
            reasoning_allocation=16384,
        )
        effective_timeout = _compute_effective_timeout(
            target_model, self.timeout, effective_max_tokens, timeout
        )
        kwargs: dict[str, Any] = {
            "messages": messages,
            "max_tokens": effective_max_tokens,
            "temperature": temperature,
            "timeout": effective_timeout,
        }
        if stream:
            kwargs["stream"] = True
        return _ChatCallSpec(target_model, effective_timeout, kwargs)

    def _finalize_chat_result(
        self,
        response: Any,
        target_model: str,
        *,
        latency_ms: float = 0.0,
        strip_thinking: bool = True,
    ) -> ChatResult:
        """Extract content and thinking, enforce PrivacyGuardHook on both, and return ChatResult."""
        msg = response.choices[0].message
        response_text = msg.content or ""
        self.privacy_guard.check_content(response_text)

        raw_thinking = getattr(msg, "reasoning_content", None)
        thinking = raw_thinking if isinstance(raw_thinking, str) else None
        extracted_thinking, content = LLMOutputParser.extract_thinking_and_content(response_text)
        thinking = thinking or extracted_thinking
        if thinking:
            self.privacy_guard.check_content(thinking)
        if strip_thinking:
            response_text = strip_think_tags(content)

        resp_model = getattr(response, "model", None)
        resolved_model = resp_model if isinstance(resp_model, str) else target_model
        return ChatResult(
            content=response_text,
            thinking=thinking or "",
            model=resolved_model,
            usage=_extract_chat_usage(response),
            latency_ms=latency_ms,
            raw_response=response,
        )


class AIClient(_BaseAIClient):
    """Lightweight AI Gateway client — wraps OpenAI SDK with multi-tier failover and mock support."""

    _client_cls = OpenAI
    _client: OpenAI

    def _dispatch_sync(self, model: str, timeout: float, call_fn: Callable[[Any, str], Any]) -> Any:
        """Execute call_fn against self._client with retry and multi-tier failover."""
        primary = lambda: _retry_sync(  # noqa: E731
            lambda: call_fn(self._client, model),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
            circuit_breaker=self.circuit_breaker,
        )
        return self.fallback_router.execute_sync(
            primary,
            model=model,
            timeout=timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_fn_builder=call_fn,
        )

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
        """Send a chat message and get a text response."""
        return self.chat_with_metadata(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            strip_thinking=strip_thinking,
            timeout=timeout,
        ).content

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
        """Send a chat message and receive structured result with latency and token usage."""
        spec = self._prepare_chat_call(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            baseline_default=1024,
            temperature=temperature,
            timeout=timeout,
        )
        start_time = time.perf_counter()
        response = self._dispatch_sync(spec.target_model, spec.effective_timeout, spec.as_call_fn())
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return self._finalize_chat_result(
            response, spec.target_model, latency_ms=latency_ms, strip_thinking=strip_thinking
        )

    def complete(
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
        """Send a completion/chat request (alias for chat())."""
        return self.chat(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            strip_thinking=strip_thinking,
            timeout=timeout,
        )

    def stream(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float | None = None,
    ) -> Generator[str, None, None]:
        """Stream a chat response, yielding text chunks as they arrive."""
        spec = self._prepare_chat_call(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            baseline_default=1024,
            temperature=temperature,
            timeout=timeout,
            stream=True,
        )
        response = self._dispatch_sync(spec.target_model, spec.effective_timeout, spec.as_call_fn())
        for chunk in response:
            if getattr(chunk, "choices", None):
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
        """Send a multi-turn conversation and get a response."""
        spec = self._prepare_chat_call(
            messages,
            model=model,
            max_tokens=max_tokens,
            baseline_default=2048,
            temperature=temperature,
            timeout=timeout,
        )
        response = self._dispatch_sync(spec.target_model, spec.effective_timeout, spec.as_call_fn())
        return self._finalize_chat_result(
            response, spec.target_model, strip_thinking=strip_thinking
        ).content

    def models(self) -> list[str]:
        """List all available models on the gateway."""
        result = self._dispatch_sync(
            self.default_model, self.timeout, lambda c, _m: c.models.list()
        )
        return sorted({m.id for m in result.data})

    def transcribe(
        self,
        audio_path: str | Path,
        *,
        model: str = "audio-primary",
        language: str = "vi",
    ) -> str:
        """Transcribe an audio file via the AI Gateway."""
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file '{audio_path}' not found.")

        def _call(client_inst: Any, m: str) -> Any:
            with open(path, "rb") as f:
                return client_inst.audio.transcriptions.create(
                    model=m, file=f, language=language, response_format="text"
                )

        return str(self._dispatch_sync(model, self.timeout, _call)).strip()

    def embed(
        self, texts: str | list[str], *, model: str = ModelArchetype.EMBEDDING
    ) -> list[list[float]]:
        """Embed a text or list of texts via the AI Gateway."""
        text_list = [texts] if isinstance(texts, str) else texts
        if self.mock_mode:
            return [[0.1] * 3072 for _ in text_list]
        response = self._dispatch_sync(
            model,
            self.timeout,
            lambda c, m: c.embeddings.create(
                model=m, input=text_list, extra_body={"drop_params": True}
            ),
        )
        return [item.embedding for item in response.data]

    def encode_image(
        self, image_path: str | Path, *, max_pixels: int = 1024, quality: int = 85
    ) -> str:
        """Resize and base64-encode an image for vision APIs."""
        import base64

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file '{image_path}' not found.")
        try:
            from io import BytesIO

            from PIL import Image, ImageOps

            img: Any = ImageOps.exif_transpose(Image.open(path))
            img.thumbnail((max_pixels, max_pixels), Image.Resampling.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
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


class AsyncAIClient(_BaseAIClient):
    """Async Lightweight AI Gateway client — wraps AsyncOpenAI SDK with multi-tier failover and mock support."""

    _client_cls = AsyncOpenAI
    _client: AsyncOpenAI

    async def _dispatch_async(
        self, model: str, timeout: float, coro_fn: Callable[[Any, str], Any]
    ) -> Any:
        """Execute async coro_fn against self._client with retry and multi-tier failover."""
        primary = lambda: _retry_async(  # noqa: E731
            lambda: coro_fn(self._client, model),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
            circuit_breaker=self.circuit_breaker,
        )
        return await self.fallback_router.execute_async(
            primary,
            model=model,
            timeout=timeout,
            circuit_breaker=self.circuit_breaker,
            fallback_coro_builder=coro_fn,
        )

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
        """Send an async chat message and get a text response."""
        res = await self.chat_with_metadata(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            strip_thinking=strip_thinking,
            timeout=timeout,
        )
        return res.content

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
        """Send an async chat message and receive structured result with latency and token usage."""
        spec = self._prepare_chat_call(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            baseline_default=1024,
            temperature=temperature,
            timeout=timeout,
        )
        start_time = time.perf_counter()
        response = await self._dispatch_async(
            spec.target_model, spec.effective_timeout, spec.as_call_fn()
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return self._finalize_chat_result(
            response, spec.target_model, latency_ms=latency_ms, strip_thinking=strip_thinking
        )

    async def complete(
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
        """Send an async completion/chat request (alias for chat())."""
        return await self.chat(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            strip_thinking=strip_thinking,
            timeout=timeout,
        )

    async def stream(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream an async chat response, yielding text chunks as they arrive."""
        spec = self._prepare_chat_call(
            message,
            model=model,
            system=system,
            max_tokens=max_tokens,
            baseline_default=1024,
            temperature=temperature,
            timeout=timeout,
            stream=True,
        )
        response = await self._dispatch_async(
            spec.target_model, spec.effective_timeout, spec.as_call_fn()
        )
        async for chunk in response:
            if getattr(chunk, "choices", None):
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
        spec = self._prepare_chat_call(
            messages,
            model=model,
            max_tokens=max_tokens,
            baseline_default=2048,
            temperature=temperature,
            timeout=timeout,
        )
        response = await self._dispatch_async(
            spec.target_model, spec.effective_timeout, spec.as_call_fn()
        )
        return self._finalize_chat_result(
            response, spec.target_model, strip_thinking=strip_thinking
        ).content

    async def models(self) -> list[str]:
        """List all available models on the gateway."""
        result = await self._dispatch_async(
            self.default_model, self.timeout, lambda c, _m: c.models.list()
        )
        return sorted({m.id for m in result.data})

    async def embed(
        self, texts: str | list[str], *, model: str = ModelArchetype.EMBEDDING
    ) -> list[list[float]]:
        """Embed a text or list of texts via the AI Gateway (async)."""
        text_list = [texts] if isinstance(texts, str) else texts
        if self.mock_mode:
            return [[0.1] * 3072 for _ in text_list]
        response = await self._dispatch_async(
            model,
            self.timeout,
            lambda c, m: c.embeddings.create(
                model=m, input=text_list, extra_body={"drop_params": True}
            ),
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
