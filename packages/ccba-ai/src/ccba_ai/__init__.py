"""
CCBA AI Gateway Client
~~~~~~~~~~~~~~~~~~~~~~

Kết nối AI Gateway trên Server Spark — 22 models, 1 endpoint.

Quick Start:
    from ccba_ai import ai

    reply = ai.chat("Xin chào!")
    reply = ai.chat("Review code", model="claude-sonnet-4-6")

    for chunk in ai.stream("Write quicksort"):
        print(chunk, end="")

    models = ai.models()
"""

from ccba_ai import services
from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from ccba_ai.client import AIClient, AsyncAIClient
from ccba_ai.exceptions import CCBABaseException, CCBAErrorCode, format_error_json
from ccba_ai.legal_knowledge import LegalKnowledgeGateway, legal_knowledge
from ccba_ai.llm_utils import LLMParseError, parse_llm_json, strip_think_tags
from ccba_ai.models import AuditFinding, AuditReport, ChatResult, ChatUsage
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


def write_file(path, content: str, encoding: str = "utf-8") -> None:
    """Safe file writer that runs pre-write privacy hooks to block API key leaks."""
    from ccba_ai.hooks import PrivacyGuardHook

    guard = PrivacyGuardHook()
    guard.check_content(content)

    with open(path, "w", encoding=encoding) as f:
        f.write(content)


__all__ = [
    # Singletons
    "ai",
    "async_ai",
    "legal_knowledge",  # NOTE: zero active callers — retained for API stability only
    # Client classes
    "AIClient",
    "AsyncAIClient",
    "LegalKnowledgeGateway",
    # Convenience shorthands (sync)
    "chat",
    "chat_with_metadata",
    "stream",
    "chat_multi",
    "models",
    "transcribe",
    "encode_image",
    # Routing & Archetypes
    "ModelArchetype",
    "choose_model",
    "is_reasoning_model",
    "resolve_max_tokens",
    # Utilities
    "write_file",
    "strip_think_tags",
    "parse_llm_json",
    "LLMParseError",
    # QC audit & Telemetry models
    "ChatResult",
    "ChatUsage",
    "AuditFinding",
    "AuditReport",
    "QCDiscoveryEngine",
    "QCAuditEngine",
    "QCReporterEngine",
    # Services
    "services",
    # Resilience & Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    # Exceptions
    "CCBAErrorCode",
    "CCBABaseException",
    "format_error_json",
]
__version__ = "1.0.0"
