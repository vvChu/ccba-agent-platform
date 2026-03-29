import os
from pathlib import Path

from openai import OpenAI

# Only load .env if it exists in CWD (avoid slow recursive search)
_env_file = Path.cwd() / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass


class AIClient:
    """Lightweight AI Gateway client — wraps OpenAI SDK for unified access."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
    ):
        self._client = OpenAI(
            base_url=base_url or os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1"),
            api_key=api_key or os.environ.get("AI_GATEWAY_KEY", os.environ.get("OPENAI_API_KEY", "")),
        )
        self.default_model = default_model or os.environ.get("AI_MODEL", "qwen3.5-35b")

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
        return response.choices[0].message.content

    def stream(
        self,
        message: str,
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        """Stream a chat response. Yields text chunks."""
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
                yield content

    def chat_multi(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Send a full conversation (multiple messages) and get a response."""
        response = self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    def models(self) -> list[str]:
        """List all available models on the gateway."""
        result = self._client.models.list()
        return sorted({m.id for m in result.data})

    def __repr__(self) -> str:
        return f"AIClient(url={self._client.base_url}, model={self.default_model})"
