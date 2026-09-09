#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-xu-ly-van-phong convert_md_to_docx.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.convert_md_to_docx.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ccba_ooxml import convert_md_to_docx


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python convert_md_to_docx.py <input.md> [output.docx]")
        return 1
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".docx")
    try:
        res = convert_md_to_docx(input_path, output_path)
        print(f"[OK] Converted to DOCX: {res}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Conversion failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
