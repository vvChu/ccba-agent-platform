"""Thin Backward-Compatible CLI Facade for Markdown-to-DOCX Conversion.

Delegates document generation to the deep seam in ``ccba_legal.cleaners``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from ccba_legal.cleaners import Cleaners, convert_markdown_to_docx
except (ImportError, ValueError):
    _PKG_SRC = Path(__file__).resolve().parents[2] / "packages" / "ccba-legal-intel" / "src"
    if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
        sys.path.insert(0, str(_PKG_SRC))
    from ccba_legal.cleaners import Cleaners, convert_markdown_to_docx

convert_md_to_docx = convert_markdown_to_docx

__all__ = [
    "Cleaners",
    "convert_markdown_to_docx",
    "convert_md_to_docx",
    "main",
]


def main() -> None:
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Convert Markdown to Docx with standard styling.")
    parser.add_argument("input_path", type=Path, help="Path to the input Markdown file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional path to output Docx file. Derived from input by default.",
    )

    args = parser.parse_args()
    input_path: Path = args.input_path

    if not input_path.exists() or not input_path.is_file():
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    output_path: Path = args.output if args.output else input_path.with_suffix(".docx")

    try:
        convert_markdown_to_docx(input_path, output_path)
        print(f"Successfully created {output_path}")
    except Exception as e:
        print(f"Error converting document: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
