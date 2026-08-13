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

from scripts.spoke.spoke_synchronizer import SpokeSynchronizer, sync_project


def main():
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
    args = parser.parse_args()
    sys.exit(sync_project(args.spoke, args.sync_item))


if __name__ == "__main__":
    main()
