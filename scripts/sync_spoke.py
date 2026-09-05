#!/usr/bin/env python3
"""sync_spoke.py - Thin Forwarding Facade for CCBA Spoke Selective Skills Synchronizer.

Delegates execution to the deep `run_spoke_sync_cli()` engine in `scripts.spoke.sync.cli`.
Re-exports core procedural helpers for 100% backward compatibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure sys.path contains platform root
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.sync import (
    list_project_backups,
    rollback_project,
    sync_all_spokes,
    sync_project,
)
from scripts.spoke.sync.cli import run_spoke_sync_cli

__all__ = [
    "main",
    "sync_project",
    "sync_all_spokes",
    "list_project_backups",
    "rollback_project",
    "run_spoke_sync_cli",
]


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint forwarding to scripts.spoke.sync.cli."""
    if argv is None:
        argv = sys.argv[1:]
    exit_code = run_spoke_sync_cli(argv)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
