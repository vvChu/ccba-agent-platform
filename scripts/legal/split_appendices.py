"""Thin CLI Delegate for Splitting Markdown Legal Appendices.

Delegates extraction and file slicing to the deep seam in ``ccba_legal.appendices``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ccba_legal.appendices import (
    AppendixSplitter,
    roman_to_decimal,
)

__all__ = [
    "roman_to_decimal",
    "AppendixSplitter",
    "main",
]


def main() -> None:
    """CLI entry point for appendix splitting."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Split embedded legal appendices from markdown documents."
    )
    default_base = (
        Path(__file__).resolve().parents[1]
        / ".md"
        / "legal_docs"
        / "luat_xay_dung_2025_so_135_2025_qh15"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=default_base,
        help="Base directory of the target legal bundle.",
    )
    parser.add_argument(
        "--guiding-dir",
        type=Path,
        default=None,
        help="Subdirectory containing guiding documents (default: <base-dir>/guiding_docs).",
    )

    args = parser.parse_args()
    base_dir = args.base_dir
    guiding_dir = args.guiding_dir or (base_dir / "guiding_docs")

    print(f"Processing appendices in: {guiding_dir}")
    splitter = AppendixSplitter()
    summary = splitter.process_directory(guiding_dir=guiding_dir, base_dir=base_dir)

    print(f"Processed {summary.get('files_processed', 0)} files.")
    print(f"Created {summary.get('total_appendices_created', 0)} appendix files.")
    print("Appendix splitting completed successfully!")


if __name__ == "__main__":
    main()
