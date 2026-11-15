"""
CCBA AI Gateway Client
~~~~~~~~~~~~~~~~~~~~~~

Kết nối AI Gateway trên Server Spark — Đa mô hình (local GPU + cloud), 1 endpoint (tự động khám phá qua ai.models()).
Tích hợp Multi-Tier Failover (Spark -> Cloud Direct -> Antigravity CLI -> Local Ollama -> Mock Provider).

Quick Start:
    from ccba_ai import ai

    reply = ai.chat("Xin chào!")
    reply = ai.chat("Review code", model="claude-sonnet-5-5-high")

    for chunk in ai.stream("Write quicksort"):
        print(chunk, end="")

    models = ai.models()
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ccba_ai.services as services
    from ccba_ai.antigravity_provider import (
        AntigravityCLIProvider,
        canonicalize_model_name,
        extract_available_models_from_stderr,
        is_unrecognized_model_error,
        normalize_gemini_cli_model,
        resolve_latest_compatible_model,
    )
    from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
    from ccba_ai.client import AIClient, AsyncAIClient
    from ccba_ai.copilot_provider import CopilotCLIProvider
    from ccba_ai.daemon_bridge import PersistentStdioDaemon
    from ccba_ai.exceptions import CCBABaseException, CCBAErrorCode, format_error_json
    from ccba_ai.fallback import (
        TIER_FALLBACK_MATRIX,
        TieredFallbackRouter,
        TierType,
        is_mock_mode_enabled,
        map_model_for_tier,
    )
    from ccba_ai.hooks.privacy_guard import PrivacyGuardHook
    from ccba_ai.llm_utils import (
        LLMParseError,
        extract_thinking,
        extract_thinking_and_content,
        parse_llm_json,
        strip_think_tags,
    )
    from ccba_ai.mock_provider import MockProvider
    from ccba_ai.models import (
        AuditFinding,
        AuditReport,
        ChatResult,
        ChatUsage,
        PhaseUpdateResult,
        PlanCreationResult,
        PlanPhaseData,
        PlanStatusResult,
        SEOAuditResult,
        TeamTask,
    )
    from ccba_ai.pipeline import AuditReportSummary, QCAuditPipeline
    from ccba_ai.prompting import (
        OptimizationResult,
        OptimizationStep,
        evaluator_optimizer_loop,
        evaluator_optimizer_loop_async,
        parse_xml_tags,
        xml_envelope,
    )
    from ccba_ai.protocols import QCAuditEngine, QCDiscoveryEngine, QCReporterEngine
    from ccba_ai.routing import ModelArchetype, choose_model, is_reasoning_model, resolve_max_tokens

    ai = AIClient()
    async_ai = AsyncAIClient()
    chat = ai.chat
    complete = ai.complete
    chat_with_metadata = ai.chat_with_metadata
    stream = ai.stream
    chat_multi = ai.chat_multi
    models = ai.models
    transcribe = ai.transcribe
    encode_image = ai.encode_image
    embed = ai.embed

__version__ = "1.2.0"

__all__ = [
    # Singletons
    "ai",
    "async_ai",
    # Client classes
    "AIClient",
    "AsyncAIClient",
    # Convenience shorthands (sync)
    "chat",
    "complete",
    "chat_with_metadata",
    "stream",
    "chat_multi",
    "models",
    "transcribe",
    "encode_image",
    "embed",
    # Routing & Archetypes & Fallback
    "ModelArchetype",
    "choose_model",
    "is_reasoning_model",
    "resolve_max_tokens",
    "TIER_FALLBACK_MATRIX",
    "TierType",
    "TieredFallbackRouter",
    "map_model_for_tier",
    "is_mock_mode_enabled",
    "MockProvider",
    "AntigravityCLIProvider",
    "CopilotCLIProvider",
    "PersistentStdioDaemon",
    "canonicalize_model_name",
    "extract_available_models_from_stderr",
    "is_unrecognized_model_error",
    "normalize_gemini_cli_model",
    "resolve_latest_compatible_model",
    # Utilities & Prompting
    "strip_think_tags",
    "extract_thinking",
    "extract_thinking_and_content",
    "parse_llm_json",
    "LLMParseError",
    "xml_envelope",
    "parse_xml_tags",
    "evaluator_optimizer_loop",
    "evaluator_optimizer_loop_async",
    "OptimizationResult",
    "OptimizationStep",
    # QC audit & Telemetry models
    "ChatResult",
    "ChatUsage",
    "AuditFinding",
    "AuditReport",
    "AuditReportSummary",
    "QCAuditPipeline",
    "SEOAuditResult",
    "TeamTask",
    "PlanCreationResult",
    "PhaseUpdateResult",
    "PlanPhaseData",
    "PlanStatusResult",
    "QCDiscoveryEngine",
    "QCAuditEngine",
    "QCReporterEngine",
    # Services
    "services",
    # Resilience & Circuit Breaker & Hooks
    "PrivacyGuardHook",
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    # Exceptions
    "CCBAErrorCode",
    "CCBABaseException",
    "format_error_json",
]

_AI_SHORTHANDS = (
    "chat",
    "complete",
    "chat_with_metadata",
    "stream",
    "chat_multi",
    "models",
    "transcribe",
    "encode_image",
    "embed",
)

# Unannotated ast.Assign so check_init_lazy_exports_parity inspects all keys.
_LAZY_EXPORTS = {
    "AntigravityCLIProvider": "ccba_ai.antigravity_provider",
    "canonicalize_model_name": "ccba_ai.antigravity_provider",
    "extract_available_models_from_stderr": "ccba_ai.antigravity_provider",
    "is_unrecognized_model_error": "ccba_ai.antigravity_provider",
    "normalize_gemini_cli_model": "ccba_ai.antigravity_provider",
    "resolve_latest_compatible_model": "ccba_ai.antigravity_provider",
    "CircuitBreaker": "ccba_ai.circuit_breaker",
    "CircuitBreakerOpenError": "ccba_ai.circuit_breaker",
    "CircuitState": "ccba_ai.circuit_breaker",
    "AIClient": "ccba_ai.client",
    "AsyncAIClient": "ccba_ai.client",
    "CopilotCLIProvider": "ccba_ai.copilot_provider",
    "PersistentStdioDaemon": "ccba_ai.daemon_bridge",
    "CCBABaseException": "ccba_ai.exceptions",
    "CCBAErrorCode": "ccba_ai.exceptions",
    "format_error_json": "ccba_ai.exceptions",
    "TIER_FALLBACK_MATRIX": "ccba_ai.fallback",
    "TieredFallbackRouter": "ccba_ai.fallback",
    "TierType": "ccba_ai.fallback",
    "is_mock_mode_enabled": "ccba_ai.fallback",
    "map_model_for_tier": "ccba_ai.fallback",
    "PrivacyGuardHook": "ccba_ai.hooks.privacy_guard",
    "LLMParseError": "ccba_ai.llm_utils",
    "extract_thinking": "ccba_ai.llm_utils",
    "extract_thinking_and_content": "ccba_ai.llm_utils",
    "parse_llm_json": "ccba_ai.llm_utils",
    "strip_think_tags": "ccba_ai.llm_utils",
    "MockProvider": "ccba_ai.mock_provider",
    "AuditFinding": "ccba_ai.models",
    "AuditReport": "ccba_ai.models",
    "ChatResult": "ccba_ai.models",
    "ChatUsage": "ccba_ai.models",
    "PhaseUpdateResult": "ccba_ai.models",
    "PlanCreationResult": "ccba_ai.models",
    "PlanPhaseData": "ccba_ai.models",
    "PlanStatusResult": "ccba_ai.models",
    "SEOAuditResult": "ccba_ai.models",
    "TeamTask": "ccba_ai.models",
    "AuditReportSummary": "ccba_ai.pipeline",
    "QCAuditPipeline": "ccba_ai.pipeline",
    "OptimizationResult": "ccba_ai.prompting",
    "OptimizationStep": "ccba_ai.prompting",
    "evaluator_optimizer_loop": "ccba_ai.prompting",
    "evaluator_optimizer_loop_async": "ccba_ai.prompting",
    "parse_xml_tags": "ccba_ai.prompting",
    "xml_envelope": "ccba_ai.prompting",
    "QCDiscoveryEngine": "ccba_ai.protocols",
    "QCAuditEngine": "ccba_ai.protocols",
    "QCReporterEngine": "ccba_ai.protocols",
    "ModelArchetype": "ccba_ai.routing",
    "choose_model": "ccba_ai.routing",
    "is_reasoning_model": "ccba_ai.routing",
    "resolve_max_tokens": "ccba_ai.routing",
}


def _get_or_init_client(attr_name: str) -> Any:
    """Lazily instantiate singleton AI clients and cache module shorthands."""
    if attr_name not in globals():
        from ccba_ai.client import AIClient, AsyncAIClient

        client = globals().setdefault("ai", AIClient())
        globals().setdefault("async_ai", AsyncAIClient())
        for shorthand in _AI_SHORTHANDS:
            globals().setdefault(shorthand, getattr(client, shorthand))
    return globals()[attr_name]


def __getattr__(name: str) -> Any:
    """Lazy import module-level attributes per PEP 562."""
    if name == "services":
        import ccba_ai.services as services_mod

        globals()["services"] = services_mod
        return services_mod
    if name in {"ai", "async_ai", *_AI_SHORTHANDS}:
        return _get_or_init_client(name)
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        mod = importlib.import_module(module_name)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose dynamic attributes to introspection and language servers per PEP 562."""
    return sorted(set(globals().keys()) | set(__all__))
