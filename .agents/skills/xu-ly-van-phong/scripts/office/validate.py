"""
Command line tool to validate Office document XML files against XSD schemas and tracked changes.

Usage:
    python validate.py <path> [--original <original_file>] [--auto-repair] [--author NAME]

The first argument can be either:
- An unpacked directory containing the Office document XML files
- A packed Office file (.docx/.pptx/.xlsx) which will be unpacked to a temp directory

Auto-repair fixes:
- paraId/durableId values that exceed OOXML limits
- Missing xml:space="preserve" on w:t elements with whitespace
"""

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

from validators import DOCXSchemaValidator, PPTXSchemaValidator, RedliningValidator


def main():
    parser = argparse.ArgumentParser(description="Validate Office document XML files")
    parser.add_argument(
        "path",
        help="Path to unpacked directory or packed Office file (.docx/.pptx/.xlsx)",
    )
    parser.add_argument(
        "--original",
        required=False,
        default=None,
        help="Path to original file (.docx/.pptx/.xlsx). If omitted, all XSD errors are reported and redlining validation is skipped.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--auto-repair",
        action="store_true",
        help="Automatically repair common issues (hex IDs, whitespace preservation)",
    )
    parser.add_argument(
        "--author",
        default="Claude",
        help="Author name for redlining validation (default: Claude)",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        sys.exit(1)

    original_file = None
    if args.original:
        original_file = Path(args.original)
        if not original_file.is_file():
            print(f"Error: {original_file} is not a file", file=sys.stderr)
            sys.exit(1)
        if original_file.suffix.lower() not in [".docx", ".pptx", ".xlsx"]:
            print(f"Error: {original_file} must be a .docx, .pptx, or .xlsx file", file=sys.stderr)
            sys.exit(1)

    file_extension = ""
    if original_file:
        file_extension = original_file.suffix.lower()
    elif path.is_file():
        file_extension = path.suffix.lower()
    elif path.is_dir():
        if (path / "word" / "document.xml").exists():
            file_extension = ".docx"
        elif (path / "ppt" / "presentation.xml").exists():
            file_extension = ".pptx"
        elif (path / "xl" / "workbook.xml").exists():
            file_extension = ".xlsx"

    if file_extension not in [".docx", ".pptx", ".xlsx"]:
        print(f"Error: Cannot determine file type from {path}. Use --original or provide a .docx/.pptx/.xlsx file/directory.", file=sys.stderr)
        sys.exit(1)

    temp_dir_obj = None
    if path.is_file() and path.suffix.lower() in [".docx", ".pptx", ".xlsx"]:
        temp_dir_obj = tempfile.TemporaryDirectory()
        try:
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(temp_dir_obj.name)
            unpacked_dir = Path(temp_dir_obj.name)
        except Exception as e:
            print(f"Error: Extraction failed: {e}", file=sys.stderr)
            if temp_dir_obj:
                temp_dir_obj.cleanup()
            sys.exit(1)
    else:
        if not path.is_dir():
            print(f"Error: {path} is not a directory or Office file", file=sys.stderr)
            sys.exit(1)
        unpacked_dir = path

    match file_extension:
        case ".docx":
            validators = [
                DOCXSchemaValidator(unpacked_dir, original_file, verbose=args.verbose),
            ]
            if original_file:
                validators.append(
                    RedliningValidator(
                        unpacked_dir, original_file, verbose=args.verbose, author=args.author
                    )
                )
        case ".pptx":
            validators = [
                PPTXSchemaValidator(unpacked_dir, original_file, verbose=args.verbose),
            ]
        case _:
            print(f"Error: Validation not supported for file type {file_extension}")
            sys.exit(1)

    try:
        if args.auto_repair:
            total_repairs = sum(v.repair() for v in validators)
            if total_repairs:
                print(f"Auto-repaired {total_repairs} issue(s)")

        success = all(v.validate() for v in validators)

        if success:
            print("All validations PASSED!")

        sys.exit(0 if success else 1)
    finally:
        if temp_dir_obj:
            temp_dir_obj.cleanup()


if __name__ == "__main__":
    main()
