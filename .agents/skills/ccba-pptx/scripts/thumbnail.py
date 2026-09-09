#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-pptx thumbnail generator.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.pptx.generate_thumbnails.
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml.pptx import generate_thumbnails


def main() -> int:
    parser = argparse.ArgumentParser(description="Create thumbnail grids from PowerPoint slides.")
    parser.add_argument("input", help="Input PowerPoint file (.pptx)")
    parser.add_argument("output_prefix", nargs="?", default="thumbnails", help="Output prefix")
    parser.add_argument(
        "--cols", type=int, default=5, help="Number of columns (default: 5, max: 6)"
    )
    parser.add_argument(
        "--outline-placeholders", action="store_true", help="Outline text placeholders"
    )
    args = parser.parse_args()

    try:
        grid_files = generate_thumbnails(
            args.input,
            output_prefix=args.output_prefix,
            cols=args.cols,
            outline_placeholders=args.outline_placeholders,
        )
        print(f"[OK] Created {len(grid_files)} grid(s):")
        for gf in grid_files:
            print(f"  - {gf}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
