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

    async def upload_file(self, file_content: bytes, mime_type: str) -> str:
        """Upload file to Gemini File API and return URI."""
        # Use direct Google API for upload if key is available
        # Proxies often only map the inference endpoints.
        if not self.api_key:
             raise ValueError("API Key required for file upload (Direct Google API)")

        base_url = "https://generativelanguage.googleapis.com"
        upload_url = f"{base_url}/upload/v1beta/files?key={self.api_key}"

        # 1. Initial Resumable Upload Request
        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(len(file_content)),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json",
        }
        
        # Metadata
        metadata = {"file": {"display_name": "uploaded_file"}}
        
        resp = await self.client.post(upload_url, headers=headers, json=metadata)
        resp.raise_for_status()
        
        upload_url = resp.headers["X-Goog-Upload-URL"]

        # 2. Upload Actual Bytes
        headers = {
            "Content-Length": str(len(file_content)),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        }
        
        resp = await self.client.post(upload_url, headers=headers, content=file_content, timeout=120)
        resp.raise_for_status()
        
        file_info = resp.json()
        file_uri = file_info.get("file", {}).get("uri")
        if not file_uri:
             raise ValueError("Failed to get file URI from upload response")
             
        return str(file_uri)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(
        self,
        prompt: str,
        file_content: bytes,
        mime_type: str,
        model: str,
        config: GenerationConfig,
    ) -> str:
        """Generate content using Gemini API via OpenAI-compatible proxy."""
        file_b64 = base64.b64encode(file_content).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{file_b64}"
        
        # Use OpenAI-compatible format for proxy
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri}
                        }
                    ]
                }
            ],
            "max_tokens": config.max_output_tokens,
            "temperature": config.temperature,
        }

        # Build URL - use OpenAI-compatible endpoint
        base = self.proxy_url.rstrip("/")
        url = f"{base}/v1/chat/completions"

        # Headers
        headers = {"Content-Type": "application/json"}
        if self.proxy_token:
            headers["Authorization"] = f"Bearer {self.proxy_token}"
        elif self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self.client.post(
            url, json=payload, headers=headers, timeout=config.timeout_seconds
        )
        response.raise_for_status()

        data = response.json()
        return self._extract_openai_content(data)

    def _extract_openai_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from OpenAI-compatible response."""
        try:
            choices = response_data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return str(message.get("content", ""))
        except (KeyError, IndexError):
            pass
        return ""


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
