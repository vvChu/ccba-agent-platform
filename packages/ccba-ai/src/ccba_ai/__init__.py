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

from ccba_ai.client import AIClient

# Module-level singleton — Pythonic pattern (NOT builtins injection)
ai = AIClient()

# Convenience function exports
chat = ai.chat
stream = ai.stream
chat_multi = ai.chat_multi
models = ai.models

__all__ = ["ai", "AIClient", "chat", "stream", "chat_multi", "models"]
__version__ = "1.0.0"
