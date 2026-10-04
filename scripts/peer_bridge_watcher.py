#!/usr/bin/env python3
"""scripts/peer_bridge_watcher.py - Thin CLI wrapper for Peer Agent Bridge Watcher (ADR-0007 / Issue #458).

Coordinates bidirectional state, delta detection via SHA-256 caching, and automated gate triggering.
Core business logic is encapsulated in packages/ccba-harness/src/ccba_harness/peer.py.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure ccba_harness is discoverable
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
PACKAGES_HARNESS = WORKSPACE_DIR / "packages" / "ccba-harness" / "src"
if str(PACKAGES_HARNESS) not in sys.path:
    sys.path.insert(0, str(PACKAGES_HARNESS))

from ccba_harness.peer import run_sync_cycle  # noqa: E402

DEFAULT_PEER_DIR = WORKSPACE_DIR / ".md" / "peer_exchange"


def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(description="Peer Agent Bridge Watcher (Delta SHA-256).")
    parser.add_argument(
        "--once", action="store_true", help="Run a single delta sync cycle and exit."
    )
    parser.add_argument(
        "--watch", action="store_true", help="Run continuously watching for changes."
    )
    parser.add_argument(
        "--interval", type=int, default=5, help="Polling interval in seconds (default: 5)."
    )
    parser.add_argument(
        "--auto-gate", action="store_true", help="Trigger peer implementation gate on code."
    )
    parser.add_argument(
        "--auto-grok", action="store_true", help="Automatically invoke Grok CLI on new prompts."
    )
    parser.add_argument(
        "--dir", type=str, default=str(DEFAULT_PEER_DIR), help="Target peer exchange directory."
    )
    return parser


def watch_loop(peer_dir: Path, interval: int, auto_gate: bool, auto_grok: bool) -> int:
    """Runs continuous polling watch loop until interrupted.

    Args:
        peer_dir: Target peer exchange directory.
        interval: Sleep duration between scan cycles.
        auto_gate: Whether to auto-run implementation gate.
        auto_grok: Whether to auto-invoke Grok CLI on prompts.

    Returns:
        Exit code integer.
    """
    print(f"🚀 Starting Peer Bridge Watcher (interval={interval}s)... Press Ctrl+C to stop.")
    try:
        while True:
            changes = run_sync_cycle(peer_dir, auto_gate=auto_gate, auto_grok=auto_grok)
            for c in changes:
                print(f"[{c.role}] Detected change in: {c.path.name}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatcher stopped.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint.

    Args:
        argv: Optional command-line arguments list.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    peer_dir = Path(args.dir).resolve()

    if args.once or not args.watch:
        changes = run_sync_cycle(peer_dir, auto_gate=args.auto_gate, auto_grok=args.auto_grok)
        for c in changes:
            print(f"[{c.role}] Detected change in: {c.path.name}")
        print(f"[OK] Bridge sync completed. Detected {len(changes)} change(s).")
        return 0

    return watch_loop(peer_dir, args.interval, args.auto_gate, args.auto_grok)


if __name__ == "__main__":
    sys.exit(main())
