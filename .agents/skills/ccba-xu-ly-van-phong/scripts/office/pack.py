#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-xu-ly-van-phong pack document.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.pack_document.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from ccba_ooxml import pack_document


def pack(
    input_directory: str,
    output_file: str,
    original_file: str | None = None,
    validate: bool = True,
    infer_author_func: Any = None,
) -> tuple[None, str]:
    """Backward compatible wrapper for packing."""
    try:
        ok = pack_document(input_directory, output_file, validate=validate)
        return None, "" if ok else "Validation failed"
    except Exception as exc:
        return None, f"Error: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack a directory into an Office file")
    parser.add_argument("input_directory", help="Unpacked Office directory")
    parser.add_argument("output_file", help="Output Office file (.docx/.pptx/.xlsx)")
    parser.add_argument("--force", action="store_true", help="Skip validation")
    args = parser.parse_args()

    try:
        ok = pack_document(args.input_directory, args.output_file, validate=not args.force)
        return 0 if ok else 1
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
