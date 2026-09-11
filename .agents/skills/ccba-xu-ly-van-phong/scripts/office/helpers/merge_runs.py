#!/usr/bin/env python3
"""Thin CLI Adapter: Merge adjacent runs with identical formatting in DOCX.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.docx.merge_runs (ADR-0035, ADR-0057).
"""

from __future__ import annotations

import argparse
import sys

from ccba_ooxml.docx.cleanup import (
    _can_merge,
    _consolidate_text,
    _find_elements,
    _first_child_run,
    _get_child,
    _get_children,
    _is_adjacent,
    _is_run,
    _merge_run_content,
    _merge_runs_in,
    _next_element_sibling,
    _next_sibling_run,
    _remove_elements,
    _strip_run_rsid_attrs,
    merge_runs,
)

__all__ = [
    "merge_runs",
    "_find_elements",
    "_get_child",
    "_get_children",
    "_is_adjacent",
    "_remove_elements",
    "_strip_run_rsid_attrs",
    "_merge_runs_in",
    "_first_child_run",
    "_next_element_sibling",
    "_next_sibling_run",
    "_is_run",
    "_can_merge",
    "_merge_run_content",
    "_consolidate_text",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge adjacent runs with identical formatting")
    parser.add_argument("input_directory", help="Unpacked docx directory")
    args = parser.parse_args()

    count, msg = merge_runs(args.input_directory)
    print(msg)
    return 0 if "Error" not in msg else 1


if __name__ == "__main__":
    sys.exit(main())
