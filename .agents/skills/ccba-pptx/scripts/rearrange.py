#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-pptx rearrange slides.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.pptx.rearrange_slides.
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml.pptx import rearrange_slides


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rearrange PowerPoint slides based on a sequence of indices."
    )
    parser.add_argument("template", help="Path to template PPTX file")
    parser.add_argument("output", help="Path for output PPTX file")
    parser.add_argument("sequence", help="Comma-separated sequence of slide indices (0-based)")
    args = parser.parse_args()

    try:
        out = rearrange_slides(args.template, args.sequence, args.output)
        print(f"[OK] Rearranged presentation: {out}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
