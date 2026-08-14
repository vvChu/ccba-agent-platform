"""Thin Backward-Compatible Facade for Simplify Gate Hook.

Delegates execution to the deep ``SimplifyGateHook`` class in ``scripts.hooks.simplify``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from .base import HookContext
    from .simplify import SimplifyGateHook
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.hooks.base import HookContext
    from scripts.hooks.simplify import SimplifyGateHook

matched_severity = SimplifyGateHook.matched_severity
get_git_diff_signals = SimplifyGateHook.get_git_diff_signals
count_lines = SimplifyGateHook.count_lines
build_verb_pattern = SimplifyGateHook.build_verb_pattern

__all__ = [
    "SimplifyGateHook",
    "matched_severity",
    "get_git_diff_signals",
    "count_lines",
    "build_verb_pattern",
    "main",
]


def main(event: str = "user-prompt-submit", payload: dict[str, Any] | None = None) -> int:
    """Entrypoint forwarding to SimplifyGateHook.execute()."""
    hook = SimplifyGateHook()
    context = HookContext.from_payload(event, payload)
    result = hook.execute(context)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
