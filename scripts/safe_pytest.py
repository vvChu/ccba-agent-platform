#!/usr/bin/env python3
"""safe_pytest.py - Auto-Wrapper CLI Script for Scoped Pytest Execution.

Discovers target test files and runs pytest via DetachedExecutionEngine.
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to sys.path if needed
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

try:
    from scripts.eval.process_safety import DetachedExecutionEngine
except ImportError:
    from eval.process_safety import (
        DetachedExecutionEngine,  # type: ignore[import-not-found,no-redef]
    )

# Backward compatibility function alias
find_modified_test_files = DetachedExecutionEngine.find_modified_test_files


def main() -> int:
    """Main CLI entry point for safe_pytest."""
    parser = argparse.ArgumentParser(description="Safe Pytest Runner Wrapper for CCBA Platform")
    parser.add_argument("-f", "--file", type=str, help="Specific test file or pattern to run")
    parser.add_argument("-p", "--package", type=str, help="Specific package name to run tests for")
    parser.add_argument(
        "-F",
        "--fast",
        action="store_true",
        help="Run only fast unit tests (<2s SLA, pure logic/mocks)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned runner command without executing",
    )
    parser.add_argument(
        "--allow-unscoped",
        action="store_true",
        help="Allow running pytest across entire workspace",
    )
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional pytest options")

    args = parser.parse_args()

    return int(
        DetachedExecutionEngine.run_safe_pytest(
            target_file=args.file,
            package=args.package,
            fast=args.fast,
            dry_run=args.dry_run,
            allow_unscoped=args.allow_unscoped,
            extra_args=args.extra_args,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
