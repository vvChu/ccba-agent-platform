"""
LLM Provider Abstraction.

Defines the interface for all LLM backends (Gemini, OpenAI, DeepSeek, Groq).
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class GenerationConfig(BaseModel):
    """Configuration for text generation."""

    temperature: float = 0.1
    max_output_tokens: int = 65536
    timeout_seconds: int = 600


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        file_content: bytes,
        mime_type: str,
        model: str,
        config: GenerationConfig,
    ) -> str:
        """
        Generate content from a prompt and file.

        Args:
            prompt: Text instruction.
            file_content: Binary content of the file.
            mime_type: MIME type of the file.
            model: Model name to use.
            config: Generation configuration.

        Returns:
            Generated text content.
        """
        pass
