"""
Gemini Provider Implementation.
"""

import base64
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from mdconverter.config import settings
from mdconverter.core.llm import GenerationConfig, LLMProvider


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini API."""

    def __init__(self, proxy_url: str | None = None, api_key: str | None = None) -> None:
        """Initialize provider."""
        self.proxy_url = proxy_url or settings.antigravity_proxy
        self.api_key = api_key or settings.gemini_api_key
        # Use Antigravity Token if behind proxy and auth enabled
        self.proxy_token = settings.antigravity_access_token
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
        """Generate content using Gemini API."""
        file_b64 = base64.b64encode(file_content).decode("utf-8")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": file_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_output_tokens,
            },
        }

        # Build URL
        # If proxy_url is antigravity local, format: {url}/v1beta/models/{model}:generateContent
        base = self.proxy_url.rstrip("/")
        url = f"{base}/v1beta/models/{model}:generateContent"

        # Headers
        headers = {}
        if self.proxy_token:
             headers["Authorization"] = f"Bearer {self.proxy_token}"
        elif self.api_key:
             # If using direct Google API or Proxy requires key in param?
             # Standard Gemini uses ?key=... query param usually, but let's stick to what worked or header.
             # If not proxy, we might need query param.
             # But for now assuming Proxy or existing logic.
                 url += f"?key={self.api_key}"

        response = await self.client.post(url, json=payload, headers=headers, timeout=config.timeout_seconds)
        response.raise_for_status()

        data = response.json()
        return self._extract_content(data)

    def _extract_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from Gemini response."""
        try:
            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return str(parts[0].get("text", ""))
        except (KeyError, IndexError):
            pass
        return ""
