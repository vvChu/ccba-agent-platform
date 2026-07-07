"""
Local PDF manipulation tool supporting merge, split, and text extraction.
"""

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def parse_pages(pages_str: str) -> list[int]:
    """Parse pages string like '1-3,5' into 0-indexed page numbers."""
    pages = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            pages.extend(range(int(start) - 1, int(end)))
        else:
            pages.append(int(part) - 1)
    return pages


def merge_pdfs(inputs: list[str], output: str) -> None:
    """Merge multiple PDFs into a single file."""
    writer = PdfWriter()
    for path in inputs:
        writer.append(path)
    with open(output, "wb") as f:
        writer.write(f)
    print(f"Successfully merged {len(inputs)} PDFs into {output}")


def split_pdf(input_pdf: str, pages_str: str, output: str) -> None:
    """Split pages from a PDF file."""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    pages = parse_pages(pages_str)
    for p in pages:
        if 0 <= p < len(reader.pages):
            writer.add_page(reader.pages[p])
    with open(output, "wb") as f:
        writer.write(f)
    print(f"Successfully split pages {pages_str} from {input_pdf} into {output}")


def extract_text(input_pdf: str, output: str) -> None:
    """Extract text from a PDF file."""
    reader = PdfReader(input_pdf)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    Path(output).write_text(text, encoding="utf-8")
    print(f"Successfully extracted text from {input_pdf} into {output}")


def main():
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
        elif args.command == "split":
            split_pdf(args.input, args.pages, args.output)
        elif args.command == "extract":
            extract_text(args.input, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
