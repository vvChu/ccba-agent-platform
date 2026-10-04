#!/usr/bin/env python3
"""scripts/peer_bridge_watcher.py - Thin CLI wrapper for Peer Agent Bridge Watcher (ADR-0007 / Issue #467).

Delegates directly to ccba_harness.cli.run_peer_watch_cli to eliminate code duplication
between Hub and Spokes.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure ccba_harness is discoverable
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
PACKAGES_HARNESS = WORKSPACE_DIR / "packages" / "ccba-harness" / "src"
if str(PACKAGES_HARNESS) not in sys.path:
    sys.path.insert(0, str(PACKAGES_HARNESS))

from ccba_harness.cli import run_peer_watch_cli  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint delegating to ccba_harness.cli.run_peer_watch_cli."""
    return run_peer_watch_cli(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
