"""Thin Backward-Compatible Facade for Brand Enforcement Hook.

Delegates execution to the deep ``BrandHook`` class in ``scripts.hooks.brand``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from .base import HookContext
    from .brand import BrandHook
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.hooks.base import HookContext
    from scripts.hooks.brand import BrandHook

load_brand_rules = BrandHook.load_brand_rules
check_file = BrandHook.check_file
DEFAULT_BRAND_PATTERNS = BrandHook.DEFAULT_BRAND_PATTERNS
DEFAULT_PROHIBITED_WORDS = BrandHook.DEFAULT_PROHIBITED_WORDS

__all__ = [
    "BrandHook",
    "load_brand_rules",
    "check_file",
    "DEFAULT_BRAND_PATTERNS",
    "DEFAULT_PROHIBITED_WORDS",
    "main",
]


def main(event: str = "post-tool", payload: dict[str, Any] | None = None) -> int:
    """Entrypoint forwarding to BrandHook.execute()."""
    hook = BrandHook()
    context = HookContext.from_payload(event, payload)
    result = hook.execute(context)
    return result.exit_code


if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
