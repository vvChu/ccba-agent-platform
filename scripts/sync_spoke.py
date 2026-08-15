#!/usr/bin/env python3
"""
CLI entrypoint for CCBA Spoke Selective Skills Synchronizer.
Delegates execution to the SpokeSynchronizer deep module.
"""

import argparse
import sys
from pathlib import Path

# Ensure sys.path contains platform root
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke import sync_all_spokes, sync_project


def main():
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CCBA Spoke Selective Skills Synchronizer")
    parser.add_argument(
        "--spoke",
        default=".",
        help="Path to the target spoke project folder (defaults to current directory).",
    )
    parser.add_argument(
        "--sync-item",
        default=None,
        help="Name of a specific skill or workflow to synchronize on-demand.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Batch synchronize all registered Spokes from Hub Registry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files on disk.",
    )
    args = parser.parse_args()

    if args.all:
        sys.exit(sync_all_spokes(sync_item=args.sync_item, dry_run=args.dry_run))
    else:
        sys.exit(sync_project(args.spoke, args.sync_item, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
