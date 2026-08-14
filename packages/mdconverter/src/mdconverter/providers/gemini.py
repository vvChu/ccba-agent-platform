"""
AI Gateway Provider Implementation.

All requests go through the unified AI Gateway (LiteLLM on Server Spark).
"""

import base64
import logging
import warnings
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from ccba_ai.circuit_breaker import CircuitBreaker
from mdconverter.config import get_settings
from mdconverter.core.llm import GenerationConfig, LLMProvider

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Return True for errors worth retrying (5xx, timeouts, connection errors)."""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.ConnectError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


class GatewayProvider(LLMProvider):
    """Provider for AI Gateway (LiteLLM) — supports all models."""

    def __init__(
        self,
        gateway_url: str | None = None,
        api_key: str | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        """Initialize provider."""
        settings = get_settings()
        self.gateway_url = (gateway_url or settings.ai_gateway_url).rstrip("/")
        self.api_key = api_key or settings.ai_gateway_key
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        # M1 fix: Use explicit timeout config instead of flat 60s.
        # read timeout must accommodate large document conversion (up to 600s).
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=settings.timeout_seconds, write=30, pool=30)
        )

    async def __aenter__(self) -> "GatewayProvider":
        """Enter async context."""
        return self

    async def __aexit__(self, *exc: object) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception(_is_retryable),
    )
    async def generate(
        self,
        prompt: str,
        file_content: bytes,
        mime_type: str,
        model: str,
        config: GenerationConfig,
    ) -> str:
        """Generate content using AI Gateway (OpenAI-compatible endpoint)."""
        self.circuit_breaker.check_allowed()

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

        try:
            response = await self.client.post(
                url, json=payload, headers=headers, timeout=config.timeout_seconds
            )
            response.raise_for_status()
            self.circuit_breaker.record_success()
            data = response.json()
            return self._extract_content(data)
        except Exception as exc:
            if _is_retryable(exc):
                self.circuit_breaker.record_failure(exc)
            raise

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


# L1 fix: Backward compatibility alias with deprecation warning
class GeminiProvider(GatewayProvider):
    """Deprecated: Use ``GatewayProvider`` instead."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "GeminiProvider is deprecated, use GatewayProvider instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
