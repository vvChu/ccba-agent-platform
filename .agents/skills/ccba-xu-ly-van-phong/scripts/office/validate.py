#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-xu-ly-van-phong validate document.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.validate_document.
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml import validate_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Office document XML files")
    parser.add_argument(
        "path", help="Path to Office file (.docx/.pptx/.xlsx) or unpacked directory"
    )
    args = parser.parse_args()

    try:
        ok = validate_document(args.path)
        if ok:
            print(f"[OK] Validation passed: {args.path}")
            return 0
        else:
            print(f"[FAIL] Validation failed: {args.path}", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
