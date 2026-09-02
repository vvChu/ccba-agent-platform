"""Multi-Tier Failover Matrix & Fallback Router for CCBA AI Gateway.

Provides automatic cascade routing across 5 tiers:
- Tier 1 (Default): LiteLLM Server Spark (:8090)
- Tier 2 (Cloud Direct): Direct API calls via Cloud Provider Environment Variables
- Tier 3 (Antigravity CLI): Zero-config fallback via ``agy -p`` subprocess (~30-40s latency)
- Tier 4 (Local Offline): Local Ollama daemon (127.0.0.1:11434/v1)
- Tier 5 (Deterministic Mock): In-memory mock engine for unit tests and offline CI
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from enum import Enum
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, OpenAI

from ccba_ai.antigravity_provider import AntigravityCLIProvider
from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ccba_ai.mock_provider import MockProvider

logger = logging.getLogger("ccba_ai.fallback")

RETRYABLE_EXCEPTIONS = (APIConnectionError, APITimeoutError, CircuitBreakerOpenError)


class TierType(str, Enum):
    """Tier classification for LLM Failover Router."""

    TIER1_GATEWAY = "tier1_gateway"
    TIER2_CLOUD = "tier2_cloud"
    TIER3_ANTIGRAVITY = "tier3_antigravity"
    TIER4_OLLAMA = "tier4_ollama"
    TIER5_MOCK = "tier5_mock"


def is_mock_mode_enabled() -> bool:
    """Check if mock mode is globally enabled via environment variables."""
    val = os.environ.get("CCBA_AI_MOCK", "").lower().strip()
    return val in ("1", "true", "yes", "on")


def map_model_for_tier(requested_model: str, tier: TierType, provider_type: str = "gemini") -> str:
    """Map standard model archetype alias to appropriate model name for target tier.

    Args:
        requested_model: The original requested model alias (e.g. 'gemini-3.7-flash').
        tier: Target failover tier.
        provider_type: Provider backend type for Tier 2 ('gemini', 'groq', 'openai').

    Returns:
        Mapped model name suitable for the target provider.
    """
    if tier == TierType.TIER5_MOCK:
        return requested_model or "mock-model"

    if tier == TierType.TIER4_OLLAMA:
        return os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")

    if tier == TierType.TIER3_ANTIGRAVITY:
        # Map to agy model names; pass through if already an agy model name
        req = (requested_model or "").lower().strip()
        if any(k in req for k in ("high", "reasoning", "pro", "o1", "o3")):
            return "gemini-3.7-flash-high"
        return "gemini-3.7-flash-medium"

    if tier == TierType.TIER2_CLOUD:
        req = (requested_model or "").lower().strip()
        if provider_type == "gemini":
            if any(k in req for k in ("high", "reasoning", "pro", "o1", "o3")):
                return "gemini-2.5-pro"
            return "gemini-2.5-flash"
        elif provider_type == "groq":
            if any(k in req for k in ("high", "reasoning", "deepseek")):
                return "deepseek-r1-distill-llama-70b"
            return "llama-3.3-70b-versatile"
        elif provider_type == "openai":
            if any(k in req for k in ("high", "reasoning", "o1", "o3")):
                return "o3-mini"
            return "gpt-4o-mini"

    return requested_model


class TieredFallbackRouter:
    """Orchestrates multi-tier failover and graceful degradation across LLM providers."""

    def __init__(
        self,
        mock_provider: MockProvider | None = None,
        agy_provider: AntigravityCLIProvider | None = None,
        enable_fallback: bool = True,
        enable_mock_fallback: bool = False,
        mock_mode: bool | None = None,
    ) -> None:
        self.mock_provider = mock_provider or MockProvider()
        self.agy_provider = agy_provider
        self.enable_fallback = enable_fallback
        self.mock_mode = mock_mode
        self.enable_mock_fallback = enable_mock_fallback or (
            mock_mode if mock_mode is not None else is_mock_mode_enabled()
        )
        self._sync_clients: dict[str, Any] = {}
        self._async_clients: dict[str, Any] = {}

    def get_tier2_config(self) -> dict[str, str] | None:
        """Discover available Cloud Direct provider configuration from environment."""
        # 1. Check Google Gemini
        g_val = os.environ.get("GEMINI_API_KEY", "").strip()
        if g_val:
            cfg: dict[str, str] = {}
            cfg["provider"] = "gemini"
            cfg["endpoint"] = os.environ.get(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            cfg["secret"] = g_val
            cfg["default_model"] = "gemini-2.5-flash"
            return cfg

        # 2. Check Groq
        groq_val = os.environ.get("GROQ_API_KEY", "").strip()
        if groq_val:
            cfg = {}
            cfg["provider"] = "groq"
            cfg["endpoint"] = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
            cfg["secret"] = groq_val
            cfg["default_model"] = "llama-3.3-70b-versatile"
            return cfg

        # 3. Check OpenAI Direct (distinct from mock/placeholder)
        o_val = os.environ.get("OPENAI_API_KEY", "").strip()
        if o_val and not o_val.startswith("mock") and o_val != "fake":
            cfg = {}
            cfg["provider"] = "openai"
            cfg["endpoint"] = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            cfg["secret"] = o_val
            cfg["default_model"] = "gpt-4o-mini"
            return cfg

        return None

    def _get_agy_provider(self) -> AntigravityCLIProvider | None:
        """Get or lazily create AntigravityCLIProvider.

        Returns None if explicitly disabled (agy_provider=False passed to __init__
        is not supported; simply don't set it).
        """
        if self.agy_provider is None:
            self.agy_provider = AntigravityCLIProvider()
        return self.agy_provider

    def get_tier4_ollama_config(self) -> dict[str, str] | None:
        """Discover Local Ollama daemon configuration."""
        ollama_url = os.environ.get("OLLAMA_URL") or os.environ.get("OLLAMA_HOST")
        if not ollama_url:
            ollama_url = "http://127.0.0.1:11434/v1"
        elif not ollama_url.endswith("/v1"):
            ollama_url = f"{ollama_url.rstrip('/')}/v1"

        cfg: dict[str, str] = {}
        cfg["provider"] = "ollama"
        cfg["endpoint"] = ollama_url
        cfg["secret"] = "ollama"
        cfg["default_model"] = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
        return cfg

    def get_sync_client(
        self, tier: TierType, timeout: float = 30.0, provider_cfg: dict[str, str] | None = None
    ) -> Any:
        """Get or create cached OpenAI client for specified tier."""
        if tier == TierType.TIER5_MOCK:
            return self.mock_provider.sync_client

        endpoint = provider_cfg.get("endpoint", "") if provider_cfg else ""
        cache_key = f"{tier.value}_{endpoint}_{timeout}"
        if cache_key not in self._sync_clients:
            if provider_cfg:
                self._sync_clients[cache_key] = OpenAI(
                    base_url=provider_cfg["endpoint"],
                    api_key=provider_cfg["secret"],
                    timeout=timeout,
                )
        return self._sync_clients.get(cache_key)

    def get_async_client(
        self, tier: TierType, timeout: float = 30.0, provider_cfg: dict[str, str] | None = None
    ) -> Any:
        """Get or create cached AsyncOpenAI client for specified tier."""
        if tier == TierType.TIER5_MOCK:
            return self.mock_provider.async_client

        endpoint = provider_cfg.get("endpoint", "") if provider_cfg else ""
        cache_key = f"{tier.value}_{endpoint}_{timeout}"
        if cache_key not in self._async_clients:
            if provider_cfg:
                self._async_clients[cache_key] = AsyncOpenAI(
                    base_url=provider_cfg["endpoint"],
                    api_key=provider_cfg["secret"],
                    timeout=timeout,
                )
        return self._async_clients.get(cache_key)

    def is_tier_failover_exception(self, exc: Exception) -> bool:
        """Check whether caught exception triggers fallback to subsequent tier."""
        if isinstance(exc, RETRYABLE_EXCEPTIONS):
            return True
        if isinstance(exc, APIStatusError) and getattr(exc, "status_code", 0) >= 500:
            return True
        return False

    def execute_sync(
        self,
        primary_fn: Callable[[], Any],
        model: str,
        timeout: float = 60.0,
        circuit_breaker: CircuitBreaker | None = None,
        fallback_fn_builder: Callable[[Any, str], Any] | None = None,
    ) -> Any:
        """Execute request with automatic multi-tier fallback cascade (sync)."""
        is_mock = self.mock_mode if self.mock_mode is not None else is_mock_mode_enabled()
        if is_mock:
            if fallback_fn_builder:
                return fallback_fn_builder(self.mock_provider.sync_client, model)
            return primary_fn()

        try:
            return primary_fn()
        except Exception as primary_exc:
            if not self.enable_fallback or not self.is_tier_failover_exception(primary_exc):
                raise

            logger.warning(
                f"[ccba-ai] Primary Gateway (Tier 1) connection failed: {primary_exc}. Attempting multi-tier failover..."
            )

            # --- Try Tier 2 (Cloud Direct) ---
            tier2_cfg = self.get_tier2_config()
            if tier2_cfg and fallback_fn_builder:
                try:
                    mapped_model = map_model_for_tier(
                        model, TierType.TIER2_CLOUD, tier2_cfg["provider"]
                    )
                    client = self.get_sync_client(
                        TierType.TIER2_CLOUD, timeout=timeout, provider_cfg=tier2_cfg
                    )
                    logger.info(
                        f"[ccba-ai] Failing over to Tier 2 ({tier2_cfg['provider']}: {mapped_model})..."
                    )
                    res = fallback_fn_builder(client, mapped_model)
                    return res
                except Exception as t2_exc:
                    logger.warning(f"[ccba-ai] Tier 2 ({tier2_cfg['provider']}) failed: {t2_exc}")

            # --- Try Tier 3 (Antigravity CLI Bridge) ---
            agy = self._get_agy_provider()
            if agy and agy.is_available() and fallback_fn_builder:
                try:
                    mapped_model = map_model_for_tier(model, TierType.TIER3_ANTIGRAVITY)
                    logger.info(
                        f"[ccba-ai] Failing over to Tier 3 (Antigravity CLI: {mapped_model})... "
                        "WARNING: ~30-40s latency expected."
                    )
                    res = fallback_fn_builder(agy.sync_client, mapped_model)
                    return res
                except Exception as t3_exc:
                    logger.warning(f"[ccba-ai] Tier 3 (Antigravity CLI) failed: {t3_exc}")

            # --- Try Tier 4 (Local Ollama) ---
            tier4_cfg = self.get_tier4_ollama_config()
            if tier4_cfg and fallback_fn_builder:
                try:
                    mapped_model = map_model_for_tier(model, TierType.TIER4_OLLAMA)
                    client = self.get_sync_client(
                        TierType.TIER4_OLLAMA, timeout=min(timeout, 30.0), provider_cfg=tier4_cfg
                    )
                    logger.info(
                        f"[ccba-ai] Failing over to Tier 4 (Local Ollama: {mapped_model})..."
                    )
                    res = fallback_fn_builder(client, mapped_model)
                    return res
                except Exception as t4_exc:
                    logger.warning(f"[ccba-ai] Tier 4 (Local Ollama) failed: {t4_exc}")

            # --- Try Tier 5 (Mock Provider Fallback if enabled) ---
            if self.enable_mock_fallback and fallback_fn_builder:
                logger.info(
                    "[ccba-ai] All live tiers exhausted. Failing over to Tier 5 (Mock Provider)..."
                )
                return fallback_fn_builder(self.mock_provider.sync_client, model)

            # Re-raise original primary error if all failovers failed
            raise primary_exc

    async def execute_async(
        self,
        primary_coro_fn: Callable[[], Any],
        model: str,
        timeout: float = 60.0,
        circuit_breaker: CircuitBreaker | None = None,
        fallback_coro_builder: Callable[[Any, str], Any] | None = None,
    ) -> Any:
        """Execute request with automatic multi-tier fallback cascade (async)."""
        is_mock = self.mock_mode if self.mock_mode is not None else is_mock_mode_enabled()
        if is_mock:
            if fallback_coro_builder:
                return await fallback_coro_builder(self.mock_provider.async_client, model)
            return await primary_coro_fn()

        try:
            return await primary_coro_fn()
        except Exception as primary_exc:
            if not self.enable_fallback or not self.is_tier_failover_exception(primary_exc):
                raise

            logger.warning(
                f"[ccba-ai] Primary Gateway (Tier 1) async connection failed: {primary_exc}. Attempting multi-tier failover..."
            )

            # --- Try Tier 2 (Cloud Direct) ---
            tier2_cfg = self.get_tier2_config()
            if tier2_cfg and fallback_coro_builder:
                try:
                    mapped_model = map_model_for_tier(
                        model, TierType.TIER2_CLOUD, tier2_cfg["provider"]
                    )
                    client = self.get_async_client(
                        TierType.TIER2_CLOUD, timeout=timeout, provider_cfg=tier2_cfg
                    )
                    logger.info(
                        f"[ccba-ai] Failing over to Tier 2 ({tier2_cfg['provider']}: {mapped_model})..."
                    )
                    res = await fallback_coro_builder(client, mapped_model)
                    return res
                except Exception as t2_exc:
                    logger.warning(
                        f"[ccba-ai] Tier 2 ({tier2_cfg['provider']}) async failed: {t2_exc}"
                    )

            # --- Try Tier 3 (Antigravity CLI Bridge) ---
            agy = self._get_agy_provider()
            if agy and agy.is_available() and fallback_coro_builder:
                try:
                    mapped_model = map_model_for_tier(model, TierType.TIER3_ANTIGRAVITY)
                    logger.info(
                        f"[ccba-ai] Failing over to Tier 3 (Antigravity CLI: {mapped_model})... "
                        "WARNING: ~30-40s latency expected."
                    )
                    res = await fallback_coro_builder(agy.async_client, mapped_model)
                    return res
                except Exception as t3_exc:
                    logger.warning(f"[ccba-ai] Tier 3 (Antigravity CLI) async failed: {t3_exc}")

            # --- Try Tier 4 (Local Ollama) ---
            tier4_cfg = self.get_tier4_ollama_config()
            if tier4_cfg and fallback_coro_builder:
                try:
                    mapped_model = map_model_for_tier(model, TierType.TIER4_OLLAMA)
                    client = self.get_async_client(
                        TierType.TIER4_OLLAMA, timeout=min(timeout, 30.0), provider_cfg=tier4_cfg
                    )
                    logger.info(
                        f"[ccba-ai] Failing over to Tier 4 (Local Ollama: {mapped_model})..."
                    )
                    res = await fallback_coro_builder(client, mapped_model)
                    return res
                except Exception as t4_exc:
                    logger.warning(f"[ccba-ai] Tier 4 (Local Ollama) async failed: {t4_exc}")

            # --- Try Tier 5 (Mock Provider Fallback if enabled) ---
            if self.enable_mock_fallback and fallback_coro_builder:
                logger.info(
                    "[ccba-ai] All live tiers exhausted. Failing over to Tier 5 (Mock Provider)..."
                )
                return await fallback_coro_builder(self.mock_provider.async_client, model)

            # Re-raise original primary error if all failovers failed
            raise primary_exc
