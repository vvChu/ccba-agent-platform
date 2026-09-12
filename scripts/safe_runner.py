#!/usr/bin/env python3
"""safe_runner.py - Detached Process Runner for CCBA Agent Platform.

Executes long-running shell commands asynchronously in a detached process via DetachedExecutionEngine.
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to sys.path if needed
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

try:
    from ccba_harness import DetachedExecutionEngine
except ImportError as exc:
    raise ImportError(
        "ccba-harness package is required by safe_runner.py. "
        "Please install it in your environment: pip install -e <hub_path>/packages/ccba-harness "
        "or run 'python scripts/spoke_bootstrap.py'"
    ) from exc

# Backward compatibility module-level function aliases
resolve_scratch_dir = DetachedExecutionEngine.resolve_scratch_dir
_cleanup_old_logs = DetachedExecutionEngine.cleanup_old_logs
check_status = DetachedExecutionEngine.check_status


def run_detached(command: str) -> None:
    """Launches command in a detached subprocess and records status."""
    DetachedExecutionEngine.run_detached(command)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detached Process Runner")
    parser.add_argument("--command", type=str, help="Command to run in detached background process")
    parser.add_argument(
        "--status", action="store_true", help="Check status of background execution"
    )
    parser.add_argument("--status-id", type=str, help="Check status of a specific execution ID")

    args = parser.parse_args()

    if args.status or args.status_id:
        check_status(args.status_id)
    elif args.command:
        run_detached(args.command)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
