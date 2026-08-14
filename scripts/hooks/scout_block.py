"""Thin Backward-Compatible Facade for Scout Block Hook.

Delegates execution to the deep ``ScoutBlockHook`` class in ``scripts.hooks.scout``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from .base import HookContext
    from .scout import ScoutBlockHook
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.hooks.base import HookContext
    from scripts.hooks.scout import ScoutBlockHook

is_path_blocked = ScoutBlockHook.is_path_blocked
is_allowed_command = ScoutBlockHook.is_allowed_command
check_tool_arguments = ScoutBlockHook.check_tool_arguments
BLOCKED_DIRS = ScoutBlockHook.BLOCKED_DIRS

__all__ = [
    "ScoutBlockHook",
    "is_path_blocked",
    "is_allowed_command",
    "check_tool_arguments",
    "BLOCKED_DIRS",
    "main",
]


def main(event: str = "pre-tool", payload: dict[str, Any] | None = None) -> int:
    """Entrypoint forwarding to ScoutBlockHook.execute()."""
    hook = ScoutBlockHook()
    context = HookContext.from_payload(event, payload)
    result = hook.execute(context)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
