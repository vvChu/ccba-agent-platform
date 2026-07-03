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
from ccba_ai.client import AIClient, AsyncAIClient
from ccba_ai.exceptions import CCBABaseException, CCBAErrorCode, format_error_json
from ccba_ai.llm_utils import parse_llm_json, strip_think_tags
from ccba_ai.models import AuditFinding, AuditReport

# Module-level singletons — Pythonic pattern (NOT builtins injection)
ai = AIClient()
async_ai = AsyncAIClient()

# Convenience function exports
chat = ai.chat
stream = ai.stream
chat_multi = ai.chat_multi
models = ai.models


def write_file(path, content: str, encoding: str = "utf-8") -> None:
    """Safe file writer that runs pre-write privacy hooks to block API key leaks."""
    from ccba_ai.hooks import PrivacyGuardHook

    guard = PrivacyGuardHook()
    guard.check_content(content)

    with open(path, "w", encoding=encoding) as f:
        f.write(content)


__all__ = [
    "ai",
    "async_ai",
    "AIClient",
    "AsyncAIClient",
    "chat",
    "stream",
    "chat_multi",
    "models",
    "write_file",
    "services",
    "CCBAErrorCode",
    "CCBABaseException",
    "format_error_json",
    "strip_think_tags",
    "parse_llm_json",
    "AuditFinding",
    "AuditReport",
]
__version__ = "1.0.0"
