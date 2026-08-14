"""Thin Backward-Compatible Facade for Test Speed Guard Hook.

Delegates execution to the deep ``TestSpeedHook`` class in ``scripts.hooks.speed``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Resilient Import for standalone vs package invocation
try:
    from .base import HookContext
    from .speed import TestSpeedHook
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.hooks.base import HookContext
    from scripts.hooks.speed import TestSpeedHook

has_slow_marker = TestSpeedHook.has_slow_marker
get_modified_test_files = TestSpeedHook.get_modified_test_files


def check_test_file_speed(
    test_file: Path, project_root: Path, max_fast_seconds: float = 2.0
) -> tuple[bool, float, str]:
    hook = TestSpeedHook(max_fast_seconds=max_fast_seconds)
    return hook.check_test_file_speed(test_file, project_root)


__all__ = [
    "TestSpeedHook",
    "has_slow_marker",
    "get_modified_test_files",
    "check_test_file_speed",
    "main",
]


def main(event: str = "post-tool", payload: dict[str, Any] | None = None) -> int:
    """CLI or hook entry point for test speed checks."""
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # If invoked directly via CLI with arguments
    if sys.argv and len(sys.argv) > 1 and not payload:
        parser = argparse.ArgumentParser(description="CCBA Test Execution Speed Guard Linter/Hook.")
        parser.add_argument("files", nargs="*", help="Specific test file(s) to check.")
        parser.add_argument(
            "--threshold",
            type=float,
            default=2.0,
            help="Max allowed execution duration (seconds) for fast tests. Default: 2.0s",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with non-zero code if any test exceeds threshold without @pytest.mark.slow.",
        )
        args = parser.parse_args()

        hook = TestSpeedHook(max_fast_seconds=args.threshold, strict=args.strict)
        project_root = Path(__file__).resolve().parents[2]

        targets: list[Path] = []
        if args.files:
            for f in args.files:
                p = Path(f)
                if not p.is_absolute():
                    p = project_root / p
                if p.exists() and p.name.startswith("test_"):
                    targets.append(p)
        else:
            targets = get_modified_test_files(project_root)

        if not targets:
            print("🛡️ [TestSpeedGuard] No modified test files to check.")
            return 0

        print(f"🛡️ [TestSpeedGuard] Checking {len(targets)} test file(s) for speed compliance...")
        warnings_count = 0
        for tf in targets:
            ok, duration, msg = hook.check_test_file_speed(tf, project_root)
            if not ok:
                warnings_count += 1
                print(f"  {msg}")
            else:
                print(f"  ✅ '{tf.name}' passed speed check ({duration:.2f}s)")

        if warnings_count > 0 and args.strict:
            print(f"\n❌ [TestSpeedGuard Strict] {warnings_count} test file(s) failed speed check.")
            return 1
        return 0

    # Otherwise called programmatically as a hook
    hook = TestSpeedHook()
    context = HookContext.from_payload(event, payload)
    result = hook.execute(context)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
