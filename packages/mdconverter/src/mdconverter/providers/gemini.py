"""
AI Gateway Provider Implementation.

All requests go through the unified AI Gateway (LiteLLM on Server Spark) via ccba-ai SDK.
"""

from __future__ import annotations

import base64
import logging
import warnings
from typing import Any

from ccba_ai import AsyncAIClient, CircuitBreaker
from mdconverter.config import get_settings
from mdconverter.core.llm import GenerationConfig, LLMProvider

logger = logging.getLogger(__name__)


class GatewayProvider(LLMProvider):
    """Provider for AI Gateway (LiteLLM) — wraps ccba-ai AsyncAIClient."""

    def __init__(
        self,
        gateway_url: str | None = None,
        api_key: str | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        """Initialize provider."""
        settings = get_settings()
        raw_url = (gateway_url or settings.ai_gateway_url).rstrip("/")
        # Ensure OpenAI-compatible endpoint URL ends with /v1
        base_url = raw_url if raw_url.endswith("/v1") else f"{raw_url}/v1"
        self.gateway_url = raw_url
        self.api_key = api_key or settings.ai_gateway_key
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.client = AsyncAIClient(
            base_url=base_url,
            api_key=self.api_key or "mock-key-for-ci",
            timeout=float(settings.timeout_seconds),
            circuit_breaker=self.circuit_breaker,
        )

    async def __aenter__(self) -> GatewayProvider:
        """Enter async context."""
        return self

    async def __aexit__(self, *exc: object) -> None:
        """Exit async context."""
        pass

    async def generate(
        self,
        prompt: str,
        file_content: bytes,
        mime_type: str,
        model: str,
        config: GenerationConfig,
    ) -> str:
        """Generate content using AI Gateway (OpenAI-compatible multimodal endpoint)."""
        file_b64 = base64.b64encode(file_content).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{file_b64}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ]

        return await self.client.chat_multi(
            messages=messages,
            model=model,
            max_tokens=config.max_output_tokens,
            temperature=config.temperature,
            timeout=float(config.timeout_seconds),
            strip_thinking=True,
        )


# Backward compatibility alias with deprecation warning
class GeminiProvider(GatewayProvider):
    """Deprecated: Use ``GatewayProvider`` instead."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "GeminiProvider is deprecated, use GatewayProvider instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
