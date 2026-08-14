"""Thin Backward-Compatible Facade for Privacy Hook.

Delegates execution to the deep ``PrivacyHook`` class in ``scripts.hooks.privacy``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from .base import HookContext
    from .privacy import PrivacyHook
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.hooks.base import HookContext
    from scripts.hooks.privacy import PrivacyHook

__all__ = ["PrivacyHook", "main"]


def main(event: str = "pre-tool", payload: dict[str, Any] | None = None) -> int:
    """Entrypoint forwarding to PrivacyHook.execute()."""
    hook = PrivacyHook()
    context = HookContext.from_payload(event, payload)
    result = hook.execute(context)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
