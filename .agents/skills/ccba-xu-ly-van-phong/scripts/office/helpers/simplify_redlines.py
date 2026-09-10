#!/usr/bin/env python3
"""Thin CLI Adapter: Simplify tracked changes by merging adjacent w:ins or w:del elements.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.docx.simplify_redlines (ADR-0035, ADR-0057).
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml.docx.cleanup import (
    _can_merge_tracked,
    _find_elements,
    _get_author,
    _get_authors_from_docx,
    _is_element,
    _merge_tracked_changes_in,
    _merge_tracked_content,
    get_authors_from_docx,
    get_tracked_change_authors,
    infer_author,
    simplify_redlines,
)

__all__ = [
    "simplify_redlines",
    "get_tracked_change_authors",
    "get_authors_from_docx",
    "infer_author",
    "_merge_tracked_changes_in",
    "_is_element",
    "_get_author",
    "_can_merge_tracked",
    "_merge_tracked_content",
    "_find_elements",
    "_get_authors_from_docx",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Simplify tracked changes in docx")
    parser.add_argument("input_directory", help="Unpacked docx directory")
    args = parser.parse_args()

    count, msg = simplify_redlines(args.input_directory)
    print(msg)
    return 0 if "Error" not in msg else 1


if __name__ == "__main__":
    sys.exit(main())
