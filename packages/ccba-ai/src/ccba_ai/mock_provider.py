"""Deterministic In-Memory Mock Provider for CCBA AI Gateway.

Provides a zero-network, ultra-fast mock LLM engine compatible with OpenAI API
interfaces for unit testing, offline development, and air-gapped CI environments.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockUsage:
    """Mock token usage statistics."""

    prompt_tokens: int = 15
    completion_tokens: int = 35
    total_tokens: int = 50


@dataclass
class MockMessage:
    """Mock message object inside completion choice."""

    content: str | None = None
    role: str = "assistant"


@dataclass
class MockChoice:
    """Mock choice object inside ChatCompletion."""

    message: MockMessage = field(default_factory=MockMessage)
    finish_reason: str = "stop"
    index: int = 0


@dataclass
class MockChatCompletion:
    """Mock OpenAI ChatCompletion response."""

    choices: list[MockChoice] = field(default_factory=lambda: [MockChoice()])
    id: str = "mock-chatcmpl-001"
    model: str = "mock-model"
    usage: MockUsage = field(default_factory=MockUsage)


@dataclass
class MockStreamDelta:
    """Mock delta inside stream chunk."""

    content: str | None = None


@dataclass
class MockStreamChoice:
    """Mock choice inside stream chunk."""

    delta: MockStreamDelta = field(default_factory=MockStreamDelta)
    index: int = 0
    finish_reason: str | None = None


@dataclass
class MockStreamChunk:
    """Mock stream chunk object."""

    choices: list[MockStreamChoice] = field(default_factory=lambda: [MockStreamChoice()])
    id: str = "mock-stream-chunk-001"
    model: str = "mock-model"


@dataclass
class MockModelItem:
    """Mock model entry inside models list."""

    id: str


@dataclass
class MockModelList:
    """Mock OpenAI models list response."""

    data: list[MockModelItem] = field(default_factory=list)


class MockCompletions:
    """Mock chat completions resource."""

    def __init__(self, provider: MockProvider) -> None:
        self._provider = provider

    def create(self, **kwargs: Any) -> MockChatCompletion | Generator[MockStreamChunk, None, None]:
        """Create a mock chat completion (sync)."""
        model = str(kwargs.get("model", "mock-model"))
        messages = kwargs.get("messages", [])
        stream = bool(kwargs.get("stream", False))

        # Extract last user message content
        last_content = ""
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "user":
                last_content = str(m.get("content", ""))
                break

        response_text = self._provider.generate_response(last_content, model=model)

        if stream:
            return self._stream_generator(response_text, model)

        return MockChatCompletion(
            choices=[MockChoice(message=MockMessage(content=response_text))],
            model=model,
            usage=MockUsage(
                prompt_tokens=max(1, len(last_content.split())),
                completion_tokens=max(1, len(response_text.split())),
                total_tokens=max(1, len(last_content.split()))
                + max(1, len(response_text.split())),
            ),
        )

    def _stream_generator(
        self, text: str, model: str
    ) -> Generator[MockStreamChunk, None, None]:
        words = text.split(" ")
        for i, word in enumerate(words):
            chunk_text = word if i == len(words) - 1 else word + " "
            yield MockStreamChunk(
                choices=[MockStreamChoice(delta=MockStreamDelta(content=chunk_text))],
                model=model,
            )


class AsyncMockCompletions:
    """Async mock chat completions resource."""

    def __init__(self, provider: MockProvider) -> None:
        self._provider = provider

    async def create(
        self, **kwargs: Any
    ) -> MockChatCompletion | AsyncGenerator[MockStreamChunk, None]:
        """Create a mock chat completion (async)."""
        model = str(kwargs.get("model", "mock-model"))
        messages = kwargs.get("messages", [])
        stream = bool(kwargs.get("stream", False))

        last_content = ""
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "user":
                last_content = str(m.get("content", ""))
                break

        response_text = self._provider.generate_response(last_content, model=model)

        if stream:
            return self._async_stream_generator(response_text, model)

        return MockChatCompletion(
            choices=[MockChoice(message=MockMessage(content=response_text))],
            model=model,
            usage=MockUsage(
                prompt_tokens=max(1, len(last_content.split())),
                completion_tokens=max(1, len(response_text.split())),
                total_tokens=max(1, len(last_content.split()))
                + max(1, len(response_text.split())),
            ),
        )

    async def _async_stream_generator(
        self, text: str, model: str
    ) -> AsyncGenerator[MockStreamChunk, None]:
        words = text.split(" ")
        for i, word in enumerate(words):
            chunk_text = word if i == len(words) - 1 else word + " "
            yield MockStreamChunk(
                choices=[MockStreamChoice(delta=MockStreamDelta(content=chunk_text))],
                model=model,
            )


class MockChatResource:
    """Mock client.chat namespace."""

    def __init__(self, provider: MockProvider) -> None:
        self.completions = MockCompletions(provider)


class AsyncMockChatResource:
    """Async mock client.chat namespace."""

    def __init__(self, provider: MockProvider) -> None:
        self.completions = AsyncMockCompletions(provider)


class MockModelsResource:
    """Mock client.models namespace."""

    def __init__(self, provider: MockProvider) -> None:
        self._provider = provider

    def list(self) -> MockModelList:
        """Return list of available mock models."""
        return MockModelList(data=[MockModelItem(id=m) for m in self._provider.available_models])


class AsyncMockModelsResource:
    """Async mock client.models namespace."""

    def __init__(self, provider: MockProvider) -> None:
        self._provider = provider

    async def list(self) -> MockModelList:
        """Return list of available mock models."""
        return MockModelList(data=[MockModelItem(id=m) for m in self._provider.available_models])


class MockAudioTranscriptions:
    """Mock audio transcription resource."""

    def create(self, **kwargs: Any) -> str:
        """Return mock audio transcription text."""
        return "[MOCK] Audio transcribed successfully."


class MockAudioResource:
    """Mock client.audio namespace."""

    def __init__(self) -> None:
        self.transcriptions = MockAudioTranscriptions()


class MockOpenAIClient:
    """Mock OpenAI sync client duck-typed for AIClient."""

    def __init__(self, provider: MockProvider) -> None:
        self.base_url = "http://mock-in-memory:8090/v1"
        self.timeout = 60.0
        self.chat = MockChatResource(provider)
        self.models = MockModelsResource(provider)
        self.audio = MockAudioResource()

    def close(self) -> None:
        """No-op close for mock client."""
        pass


class AsyncMockOpenAIClient:
    """Mock AsyncOpenAI client duck-typed for AsyncAIClient."""

    def __init__(self, provider: MockProvider) -> None:
        self.base_url = "http://mock-in-memory:8090/v1"
        self.timeout = 60.0
        self.chat = AsyncMockChatResource(provider)
        self.models = AsyncMockModelsResource(provider)
        self.audio = MockAudioResource()

    async def close(self) -> None:
        """No-op close for async mock client."""
        pass


class MockProvider:
    """Deterministic, In-Memory Mock Provider for AI Clients.

    Allows registering custom pattern matches, automatic JSON formatting,
    and emulating OpenAI sync and async interfaces without network requests.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, str] = {}
        self._default_response: str | None = None
        self.available_models: list[str] = [
            "gemini-3.7-flash",
            "gemini-3.7-flash-high",
            "qwen-local-primary",
            "ocr-primary",
            "rag-core",
            "mock-model",
        ]
        self.sync_client = MockOpenAIClient(self)
        self.async_client = AsyncMockOpenAIClient(self)

    def register_pattern(self, pattern: str, response: str) -> None:
        """Register a specific text pattern and its deterministic mock response.

        Args:
            pattern: Substring or keyword to match in prompt.
            response: Response string to return when pattern is matched.
        """
        self._patterns[pattern.lower().strip()] = response

    def clear_patterns(self) -> None:
        """Clear all registered pattern matches."""
        self._patterns.clear()
        self._default_response = None

    def set_default_response(self, response: str | None) -> None:
        """Set a fallback default response when no pattern matches.

        Args:
            response: Default response string, or None to use dynamic generator.
        """
        self._default_response = response

    def generate_response(self, prompt: str, model: str = "mock-model") -> str:
        """Generate a deterministic response based on prompt contents.

        Args:
            prompt: Prompt or last user message text.
            model: Model name requested.

        Returns:
            Deterministic string response.
        """
        prompt_lower = prompt.lower().strip()

        # 1. Check registered exact/substring patterns
        for pat, resp in self._patterns.items():
            if pat in prompt_lower:
                return resp

        # 2. Check explicit default response
        if self._default_response is not None:
            return self._default_response

        # 3. Check JSON request in prompt -> Return valid JSON
        if any(kw in prompt_lower for kw in ("json", "output_format=json", "return a json", "{")):
            return json.dumps(
                {
                    "status": "success",
                    "mock": True,
                    "model": model,
                    "message": "Deterministic mock JSON response.",
                    "data": {"query": prompt[:50]},
                },
                ensure_ascii=False,
            )

        # 4. Standard deterministic mock response
        snippet = prompt[:40].replace("\n", " ").strip()
        return f"[MOCK:{model}] Response to: {snippet}"
