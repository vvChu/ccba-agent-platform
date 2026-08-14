"""Naming Convention Hook for CCBA Lifecycle.

Enforces snake_case for Python, camelCase for JavaScript/TypeScript, and warns against generic file names.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseHook, HookContext, HookResult


class NamingHook(BaseHook):
    """Enforces consistent file naming patterns across languages."""

    name = "naming_convention"
    supported_events = ("pre-tool",)

    GENERIC_NAMES = ["test", "temp", "tmp", "report", "dummy", "file", "output", "untitled"]

    def execute(self, context: HookContext) -> HookResult:
        path_arg = context.clean_path
        if not path_arg:
            return HookResult(name=self.name, exit_code=0, message="No path to inspect.")

        path_obj = Path(path_arg)
        filename = path_obj.name
        ext = path_obj.suffix.lower()
        warnings = []

        # 1. Warn against generic file names
        if path_obj.stem.lower() in self.GENERIC_NAMES:
            w = f"[naming-convention] Warning: '{filename}' is a generic name. Use more descriptive file names."
            print(f"\x1b[33m{w}\x1b[0m")
            warnings.append(w)

        # 2. Enforce naming conventions based on file extension
        if ext == ".py":
            if not re.match(r"^[a-z_][a-z0-9_]*$", path_obj.stem):
                w = f"[naming-convention] Warning: Python file '{filename}' does not follow snake_case naming conventions."
                print(f"\x1b[33m{w}\x1b[0m")
                warnings.append(w)
        elif ext in [".js", ".ts", ".jsx", ".tsx"]:
            if not re.match(r"^[a-z][a-zA-Z0-9]*$", path_obj.stem):
                w = f"[naming-convention] Warning: JavaScript/TypeScript file '{filename}' does not follow camelCase naming conventions."
                print(f"\x1b[33m{w}\x1b[0m")
                warnings.append(w)

        return HookResult(
            name=self.name,
            exit_code=0,  # Warning only
            message=f"Naming check finished with {len(warnings)} warning(s).",
            details={"warnings": warnings},
        )
