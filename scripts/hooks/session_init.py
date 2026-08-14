"""Thin Backward-Compatible Facade for Session Init Hook.

Delegates execution to the deep ``SessionInitHook`` class in ``scripts.hooks.session``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from .base import HookContext
    from .session import SessionInitHook
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.hooks.base import HookContext
    from scripts.hooks.session import SessionInitHook

__all__ = ["SessionInitHook", "main"]


def main(event: str = "session-init", payload: dict[str, Any] | None = None) -> int:
    """Entrypoint forwarding to SessionInitHook.execute()."""
    hook = SessionInitHook()
    context = HookContext.from_payload(event, payload)
    result = hook.execute(context)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
