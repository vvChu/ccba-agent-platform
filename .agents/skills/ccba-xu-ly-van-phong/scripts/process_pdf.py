#!/usr/bin/env python3
"""Thin CLI Adapter: Local PDF manipulation tool supporting merge, split, and text extraction.

Delegates execution to Layer 1 Deep Seam: ccba_pdf_prep.manipulation (ADR-0035, ADR-0057).
"""

from __future__ import annotations

import argparse
import sys

from ccba_pdf_prep.manipulation import (
    extract_text_from_pdf,
    merge_pdfs,
    parse_pages,
    split_pdf_pages,
)

__all__ = [
    "parse_pages",
    "merge_pdfs",
    "split_pdf",
    "extract_text",
]


def split_pdf(input_pdf: str, pages_str: str, output: str) -> None:
    """Backward compatible wrapper for splitting pages from a PDF file."""
    split_pdf_pages(input_pdf, pages_str, output)
    print(f"Successfully split pages {pages_str} from {input_pdf} into {output}")


def extract_text(input_pdf: str, output: str) -> None:
    """Backward compatible wrapper for extracting text from a PDF file."""
    extract_text_from_pdf(input_pdf, output)
    print(f"Successfully extracted text from {input_pdf} into {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF manipulation tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    merge_parser = subparsers.add_parser("merge", help="Merge multiple PDFs")
    merge_parser.add_argument("--input", nargs="+", required=True, help="Input PDF files")
    merge_parser.add_argument("--output", required=True, help="Output PDF file")

    split_parser = subparsers.add_parser("split", help="Split pages from a PDF")
    split_parser.add_argument("--input", required=True, help="Input PDF file")
    split_parser.add_argument("--pages", required=True, help="Pages to extract (e.g. 1-3,5)")
    split_parser.add_argument("--output", required=True, help="Output PDF file")

    extract_parser = subparsers.add_parser("extract", help="Extract text from a PDF")
    extract_parser.add_argument("--input", required=True, help="Input PDF file")
    extract_parser.add_argument("--output", required=True, help="Output text file")

    args = parser.parse_args()

    try:
        if args.command == "merge":
            merge_pdfs(args.input, args.output)
            print(f"Successfully merged {len(args.input)} PDFs into {args.output}")
        elif args.command == "split":
            split_pdf(args.input, args.pages, args.output)
        elif args.command == "extract":
            extract_text(args.input, args.output)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
