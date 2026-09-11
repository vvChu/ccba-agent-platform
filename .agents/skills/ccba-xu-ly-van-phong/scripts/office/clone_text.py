#!/usr/bin/env python3
"""Thin CLI Adapter: Tiêm nội dung mới vào lõi XML bảo toàn định dạng.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.docx.clone_xml_text (ADR-0035, ADR-0057).
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml.docx.cleanup import clone_xml_text

__all__ = ["clone_xml_text"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject new content into XML core preserving styles"
    )
    parser.add_argument("xml_file", help="Path to document.xml file")
    parser.add_argument("--map", required=True, help="Path to translation map JSON file")
    args = parser.parse_args()

    try:
        changes_made = clone_xml_text(args.xml_file, args.map)
        print(f"[SUCCESS] XML text replacement completed: {changes_made} token(s) replaced.")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
