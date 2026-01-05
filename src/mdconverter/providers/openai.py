"""
OpenAI-compatible Provider (DeepSeek, Groq, OpenAI).
"""

import base64
from typing import Any

import httpx

from mdconverter.core.llm import GenerationConfig, LLMProvider


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs (DeepSeek, Groq)."""

    def __init__(self, base_url: str, api_key: str) -> None:
        """Initialize provider."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60)

    async def generate(
        self,
        prompt: str,
        file_content: bytes,
        mime_type: str,
        model: str,
        config: GenerationConfig,
    ) -> str:
        """Generate content using OpenAI-compatible Chat Completion API."""
        # Note: Most OpenAI-compat APIs don't natively support file upload in the same way Gemini does (inline data).
        # However, for text-based files, we can include content in the prompt.
        # For images, we need vision support (like GPT-4o).
        
        is_text = mime_type.startswith("text") or mime_type in [
            "application/json", "application/xml", "application/javascript"
        ]
        
        messages: list[dict[str, Any]] = []

        if is_text:
            try:
                text_content = file_content.decode("utf-8")
                user_content = f"{prompt}\n\nDOCUMENT CONTENT:\n{text_content}"
                messages = [{"role": "user", "content": user_content}]
            except UnicodeDecodeError:
                 return "Error: Cannot decode text file content."
        else:
            # Assume vision capable or fail
            base64_image = base64.b64encode(file_content).decode("utf-8")
            messages = [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_output_tokens,
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=config.timeout_seconds
        )
        response.raise_for_status()
        
        data = response.json()
        return str(data["choices"][0]["message"]["content"])
