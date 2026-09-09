#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-academic-writing export_paper_to_docx.

Delegates execution to Layer 1 Deep Seam: mdconverter.export_paper_to_docx.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mdconverter import export_paper_to_docx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert academic Markdown draft to standard double-spaced DOCX."
    )
    parser.add_argument("input_path", type=Path, help="Path to input Markdown draft file.")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output Word file path.")
    args = parser.parse_args()

    try:
        out = export_paper_to_docx(args.input_path, args.output)
        print(f"[OK] Generated academic DOCX: {out}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Export failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
