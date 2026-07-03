import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

from openai import AsyncOpenAI, OpenAI

from ccba_ai.hooks import PrivacyGuardHook


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

    def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat message and get a text response."""
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
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
        """Stream a chat response. Yields text chunks."""
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
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

        response = self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        return response_text

    def models(self) -> list[str]:
        """List all available models on the gateway."""
        result = self._client.models.list()
        return sorted({m.id for m in result.data})

    def __repr__(self) -> str:
        return f"AIClient(url={self._client.base_url}, model={self.default_model})"


class AsyncAIClient:
    """Async Lightweight AI Gateway client — wraps AsyncOpenAI SDK for unified access."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
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

    async def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Send an async chat message and get a text response."""
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = await self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
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
        """Stream an async chat response. Yields text chunks."""
        self.privacy_guard.check_content(message)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = await self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
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

        response = await self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response_text = response.choices[0].message.content or ""
        self.privacy_guard.check_content(response_text)
        return response_text

    async def models(self) -> list[str]:
        """List all available models on the gateway."""
        result = await self._client.models.list()
        return sorted({m.id for m in result.data})

    def __repr__(self) -> str:
        return f"AsyncAIClient(url={self._client.base_url}, model={self.default_model})"
