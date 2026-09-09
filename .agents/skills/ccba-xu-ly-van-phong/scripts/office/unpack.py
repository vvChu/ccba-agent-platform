#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-xu-ly-van-phong unpack document.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.unpack_document.
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml import unpack_document


def unpack(
    input_file: str,
    output_directory: str,
    merge_runs: bool = True,
    simplify_redlines: bool = True,
) -> tuple[None, str]:
    """Backward compatible wrapper for unpacking."""
    try:
        unpack_document(input_file, output_directory)
        return None, ""
    except Exception as exc:
        return None, f"Error: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Unpack an Office document into XML directory")
    parser.add_argument("office_file", help="Path to input .docx/.pptx/.xlsx file")
    parser.add_argument("output_dir", help="Output directory to write unpacked XML files")
    args = parser.parse_args()

    try:
        unpack_document(args.office_file, args.output_dir)
        print(f"[OK] Unpacked to {args.output_dir}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
