#!/usr/bin/env python3
"""check_hardcoded_parameters.py - AST Hardcoded Parameter & KISS Linter.

Thin governance CLI wrapper over ``ccba_harness.scan_parameter_cleanliness``:
1. Raw LLM model names ('gemini-*', 'gpt-*', 'claude-*', 'llama-*', etc.)
   - Must use ``ccba_ai.routing.ModelArchetype`` or ``choose_model()``.
   - Exemption: ``# ccba:allow-raw-model``.
2. Hardcoded network IP addresses (e.g., '100.64.1.1')
   - Exemption: ``# ccba:allow-raw-ip`` or statutory clauses (``3.2.1.1``).
3. Hardcoded machine drive paths ('C:\\...', 'D:\\...', including spaces)
   - Exemption: ``# ccba:allow-machine-path``.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

_RULES = ("raw_model", "raw_ip", "machine_path")


def _load_cleanliness_module() -> Any:
    """Resolve the stdlib cleanliness module via public seam or repo fallback."""
    try:
        from ccba_harness import scan_parameter_cleanliness as _seam_scan

        _ = _seam_scan
        return sys.modules["ccba_harness._parameter_cleanliness"]
    except ImportError:
        pass
    seam_file = (
        Path(__file__).resolve().parents[2]
        / "packages"
        / "ccba-harness"
        / "src"
        / "ccba_harness"
        / "_parameter_cleanliness.py"
    )
    spec = importlib.util.spec_from_file_location("_ccba_parameter_cleanliness", seam_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load cleanliness seam from {seam_file}")
    mod = sys.modules.get(spec.name)
    if mod is None:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    return mod


if TYPE_CHECKING:
    from ccba_harness import ParameterViolation, scan_parameter_cleanliness

    _CLEANLINESS: Any = None
else:
    _CLEANLINESS = _load_cleanliness_module()
    ParameterViolation = _CLEANLINESS.ParameterViolation
    scan_parameter_cleanliness = _CLEANLINESS.scan_parameter_cleanliness

EXEMPT_FILES: frozenset[str] = (
    frozenset() if TYPE_CHECKING else frozenset(_CLEANLINESS._DEFAULT_EXEMPT_MODEL_FILES)
)


def is_whitelisted_file(path: Path) -> bool:
    """Check if file is exempt from parameter inspection using Path segment rules."""
    if _CLEANLINESS is None:
        return False
    return bool(_CLEANLINESS._is_whitelisted_path(path))


def check_file_content(file_path: Path, content: str) -> list[ParameterViolation]:
    """Scan Python source content for hardcoded model, IP, and path violations."""
    if is_whitelisted_file(file_path):
        return []
    return list(
        scan_parameter_cleanliness(
            file_path,
            content=content,
            rules=_RULES,
            check_posix_home=False,
            respect_whitelist=False,
        )
    )


def check_file(file_path: Path) -> list[ParameterViolation]:
    """Read and inspect a single Python file."""
    if is_whitelisted_file(file_path):
        return []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as err:
        return [
            ParameterViolation(
                file_path=file_path,
                line_number=1,
                rule_name="FileReadError",
                message=f"Failed to read file: {err}",
            )
        ]
    return check_file_content(file_path, content)


def scan_directory(root_dir: Path) -> list[ParameterViolation]:
    """Recursively scan directory with segment pruning for parameter violations."""
    return list(
        scan_parameter_cleanliness(
            root_dir,
            rules=_RULES,
            check_posix_home=False,
            respect_whitelist=True,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for AST hardcoded parameter linter."""
    parser = argparse.ArgumentParser(
        description="AST Linter for Hardcoded Parameters & Dynamic Scalability."
    )
    parser.add_argument("--file", type=Path, help="Check a single Python file.")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("."),
        help="Root directory to scan (default: repo root).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=True,
        help="Exit with non-zero code if any violations are found.",
    )
    args = parser.parse_args(argv)
    violations = check_file(args.file) if args.file else scan_directory(args.dir)
    if not violations:
        print("✅ [check_hardcoded_parameters] 0 violations found. All parameters compliant.")
        return 0
    print(f"❌ [check_hardcoded_parameters] Found {len(violations)} violation(s):")
    for v in violations:
        print(f"  {v.file_path.as_posix()}:{v.line_number} [{v.rule_name}]: {v.message}")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
