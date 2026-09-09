#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-pptx inventory.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.pptx.extract_text_inventory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ccba_ooxml.pptx import extract_text_inventory, save_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text inventory from PowerPoint (.pptx).")
    parser.add_argument("input", help="Input PowerPoint file (.pptx)")
    parser.add_argument("output", help="Output JSON file for inventory")
    parser.add_argument(
        "--issues-only", action="store_true", help="Include only shapes with issues"
    )
    args = parser.parse_args()

    try:
        inv = extract_text_inventory(args.input, issues_only=args.issues_only)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        save_inventory(inv, out_path)
        print(f"[OK] Inventory saved to: {out_path}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
