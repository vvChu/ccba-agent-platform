"""
CCBA AI Gateway Client
~~~~~~~~~~~~~~~~~~~~~~

Kết nối AI Gateway trên Server Spark — Đa mô hình (local GPU + cloud), 1 endpoint (tự động khám phá qua ai.models()).
Tích hợp Multi-Tier Failover (Spark -> Cloud Direct -> Antigravity CLI -> Local Ollama -> Mock Provider).

Quick Start:
    from ccba_ai import ai

    reply = ai.chat("Xin chào!")
    reply = ai.chat("Review code", model="claude-sonnet-4-6")

    for chunk in ai.stream("Write quicksort"):
        print(chunk, end="")

    models = ai.models()
"""

from __future__ import annotations

from typing import Any

from ccba_ai.antigravity_provider import (
    AntigravityCLIProvider,
    canonicalize_model_name,
    extract_available_models_from_stderr,
    is_unrecognized_model_error,
    resolve_latest_compatible_model,
)
from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from ccba_ai.client import AIClient, AsyncAIClient
from ccba_ai.copilot_provider import CopilotCLIProvider
from ccba_ai.daemon_bridge import PersistentStdioDaemon
from ccba_ai.exceptions import CCBABaseException, CCBAErrorCode, format_error_json
from ccba_ai.fallback import (
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

# Module-level singletons — Pythonic pattern (NOT builtins injection)
ai = AIClient()
async_ai = AsyncAIClient()

# Convenience function exports
chat = ai.chat
chat_with_metadata = ai.chat_with_metadata
stream = ai.stream
chat_multi = ai.chat_multi
models = ai.models
transcribe = ai.transcribe
encode_image = ai.encode_image
embed = ai.embed


__all__ = [
    # Singletons
    "ai",
    "async_ai",
    # Client classes
    "AIClient",
    "AsyncAIClient",
    # Convenience shorthands (sync)
    "chat",
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
__version__ = "1.2.0"


def __getattr__(name: str) -> Any:
    """Lazy import module-level attributes per PEP 562."""
    if name == "services":
        import ccba_ai.services as services_mod

        return services_mod
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose dynamic attributes to introspection and language servers per PEP 562."""
    return sorted(list(globals().keys()) + ["services"])
