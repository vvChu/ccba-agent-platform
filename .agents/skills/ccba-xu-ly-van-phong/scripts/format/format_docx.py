#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-xu-ly-van-phong format_docx.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.format_docx.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ccba_ooxml import format_docx


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python format_docx.py <input.docx> [output.docx]")
        return 1
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path
    try:
        res = format_docx(input_path, output_path)
        print(f"[OK] Formatted document: {res}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Formatting failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
