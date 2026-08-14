"""Unified Hook Runner CLI for ccba-agent-platform.

Orchestrates lifecycle hooks: session-init, pre-tool, post-tool, user-prompt-submit
via the deep HookCoordinator subsystem in scripts.hooks.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from scripts.hooks import get_default_coordinator


def run_hooks(event: str, payload: dict[str, Any]) -> int:
    """Executes all hooks registered for event via default HookCoordinator."""
    coordinator = get_default_coordinator()
    exit_code, _ = coordinator.run_event(event, payload)
    return exit_code


def main() -> None:
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="CCBA Platform Lifecycle Hook Runner")
    parser.add_argument(
        "event",
        choices=["session-init", "pre-tool", "post-tool", "user-prompt-submit"],
        help="Lifecycle event to trigger",
    )
    parser.add_argument("--tool", help="Name of the tool being called (for pre/post tool use)")
    parser.add_argument("--path", help="Target path of the tool call (if applicable)")
    parser.add_argument("--args", help="JSON encoded arguments of the tool call")
    parser.add_argument("--status", help="Exit status, prompt, or result description")

    args = parser.parse_args()

    payload = {
        "tool": args.tool,
        "path": args.path,
        "args": args.args,
        "status": args.status,
    }

    exit_code = run_hooks(args.event, payload)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
