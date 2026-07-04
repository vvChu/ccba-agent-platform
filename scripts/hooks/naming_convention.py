"""
Hook script for pre-tool naming convention checks.
Enforces snake_case for Python, camelCase for JavaScript/TypeScript, and warns against generic names.
"""

import re
from pathlib import Path


def main(event: str, payload: dict) -> int:
    path_arg = payload.get("path")
    if not path_arg:
        return 0

    path_obj = Path(path_arg)
    filename = path_obj.name
    ext = path_obj.suffix.lower()

    # 1. Warn against generic file names
    generic_names = ["test", "temp", "tmp", "report", "dummy", "file", "output", "untitled"]
    if path_obj.stem.lower() in generic_names:
        print(
            f"[naming-convention] Warning: '{filename}' is a generic name. Use more descriptive file names."
        )
        return 0  # Warn only

    # 2. Enforce naming conventions based on file extension
    # snake_case for Python
    if ext == ".py":
        if not re.match(r"^[a-z_][a-z0-9_]*$", path_obj.stem):
            print(
                f"[naming-convention] Warning: Python file '{filename}' does not follow snake_case naming conventions."
            )

    # camelCase for JavaScript/TypeScript
    elif ext in [".js", ".ts", ".jsx", ".tsx"]:
        if not re.match(r"^[a-z][a-zA-Z0-9]*$", path_obj.stem):
            print(
                f"[naming-convention] Warning: JavaScript/TypeScript file '{filename}' does not follow camelCase naming conventions."
            )

    return 0
