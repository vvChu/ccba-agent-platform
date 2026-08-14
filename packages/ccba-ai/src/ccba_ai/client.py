import asyncio
import os
import time
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, OpenAI

from ccba_ai.hooks import PrivacyGuardHook

RETRYABLE_EXCEPTIONS = (APIConnectionError, APITimeoutError)


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(exc, APIStatusError) and getattr(exc, "status_code", 0) >= 500:
        return True
    return False


def _retry_sync(fn, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            if attempt < max_retries and _is_retryable_exception(e):
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise


async def _retry_async(
    coro_fn, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0
):
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except Exception as e:
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
    """Lightweight AI Gateway client — wraps OpenAI SDK for unified access."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        try:
            _find_and_load_env()
        except Exception:
            pass

        self._client = OpenAI(
            base_url=base_url or os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1"),
            api_key=api_key
            or os.environ.get(
                "AI_GATEWAY_KEY", os.environ.get("OPENAI_API_KEY", "mock-key-for-ci")
            ),
        )
        self.default_model = default_model or os.environ.get("AI_MODEL", "qwen-local-primary")
        self.privacy_guard = PrivacyGuardHook()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat message and get a text response.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0–2.0).

        Returns:
            The assistant's response text, or empty string if model refused.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = _retry_sync(
            lambda: self._client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        return response_text

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

        response = _retry_sync(
            lambda: self._client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            ),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                self.privacy_guard.check_content(content)
                yield content

    def chat_multi(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Send a multi-turn conversation and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model name override. Uses default_model if None.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0–2.0).

        Returns:
            The assistant's response text, or empty string if model refused.
        """
        for msg in messages:
            self.privacy_guard.check_content(msg.get("content", ""))

        response = _retry_sync(
            lambda: self._client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        return response_text

    def models(self) -> list[str]:
        """List all available models on the gateway.

        Returns:
            Sorted list of unique model ID strings.
        """
        result = _retry_sync(
            lambda: self._client.models.list(),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
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

        with open(path, "rb") as f:
            response = _retry_sync(
                lambda: self._client.audio.transcriptions.create(
                    model=model,
                    file=f,
                    language=language,
                    response_format="text",
                ),
                max_retries=self.max_retries,
                initial_delay=self.retry_delay,
            )
            return str(response).strip()

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

            img = Image.open(path)
            img = ImageOps.exif_transpose(img)  # Auto-orient
            img.thumbnail((max_pixels, max_pixels), Image.Resampling.LANCZOS)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            buf = BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            # Fallback: raw base64 without resize
            return base64.b64encode(path.read_bytes()).decode("utf-8")

    def __repr__(self) -> str:
        return f"AIClient(url={self._client.base_url}, model={self.default_model})"


class AsyncAIClient:
    """Async Lightweight AI Gateway client — wraps AsyncOpenAI SDK for unified access."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        try:
            _find_and_load_env()
        except Exception:
            pass

        self._client = AsyncOpenAI(
            base_url=base_url or os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1"),
            api_key=api_key
            or os.environ.get(
                "AI_GATEWAY_KEY", os.environ.get("OPENAI_API_KEY", "mock-key-for-ci")
            ),
        )
        self.default_model = default_model or os.environ.get("AI_MODEL", "qwen-local-primary")
        self.privacy_guard = PrivacyGuardHook()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Send an async chat message and get a text response.

        Args:
            message: The user message to send.
            model: Model name override. Uses default_model if None.
            system: Optional system prompt.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0–2.0).

        Returns:
            The assistant's response text, or empty string if model refused.
        """
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = await _retry_async(
            lambda: self._client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        return response_text

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

        response = await _retry_async(
            lambda: self._client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            ),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                self.privacy_guard.check_content(content)
                yield content

    async def chat_multi(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Send an async multi-turn conversation and get a response."""
        for msg in messages:
            self.privacy_guard.check_content(msg.get("content", ""))

        response = await _retry_async(
            lambda: self._client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        return response_text

    async def models(self) -> list[str]:
        """List all available models on the gateway.

        Returns:
            Sorted list of unique model ID strings.
        """
        result = await _retry_async(
            lambda: self._client.models.list(),
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )
        return sorted({m.id for m in result.data})

    def __repr__(self) -> str:
        return f"AsyncAIClient(url={self._client.base_url}, model={self.default_model})"
