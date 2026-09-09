#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-pptx replace text.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.pptx.pptx_replace_text.
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml.pptx import pptx_replace_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace text in PowerPoint presentation.")
    parser.add_argument("input_pptx", help="Path to input presentation")
    parser.add_argument("replacements", help="Path to replacements JSON file or search string")
    parser.add_argument("output_pptx", help="Path for output presentation")
    args = parser.parse_args()

    try:
        out = pptx_replace_text(args.input_pptx, args.replacements, args.output_pptx)
        print(f"[OK] Updated presentation: {out}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
