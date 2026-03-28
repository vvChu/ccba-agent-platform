"""
Gemini Provider Implementation — via AI Gateway.

All requests go through the unified AI Gateway (LiteLLM on Server Spark).
"""

import base64
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from mdconverter.config import settings
from mdconverter.core.llm import GenerationConfig, LLMProvider


class GeminiProvider(LLMProvider):
    """Provider for AI Gateway (LiteLLM) — supports all models."""

    def __init__(self, gateway_url: str | None = None, api_key: str | None = None) -> None:
        """Initialize provider."""
        self.gateway_url = (gateway_url or settings.ai_gateway_url).rstrip("/")
        self.api_key = api_key or settings.ai_gateway_key
        self.client = httpx.AsyncClient(timeout=60)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(
        self,
        prompt: str,
        file_content: bytes,
        mime_type: str,
        model: str,
        config: GenerationConfig,
    ) -> str:
        """Generate content using AI Gateway (OpenAI-compatible endpoint)."""
        file_b64 = base64.b64encode(file_content).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{file_b64}"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            "max_tokens": config.max_output_tokens,
            "temperature": config.temperature,
        }

        url = f"{self.gateway_url}/chat/completions"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self.client.post(
            url, json=payload, headers=headers, timeout=config.timeout_seconds
        )
        response.raise_for_status()

        data = response.json()
        return self._extract_content(data)

    def _extract_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from OpenAI-compatible response."""
        try:
            choices = response_data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return str(message.get("content", ""))
        except (KeyError, IndexError):
            pass
        return ""
