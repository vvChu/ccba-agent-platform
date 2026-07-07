#!/usr/bin/env python3
"""
Command line tool to validate Office document XML files against XSD schemas and tracked changes.

Usage:
    python validate.py <dir> --original <original_file>
"""

import argparse
import sys
from pathlib import Path

from .validation import OOXMLValidator


def main():
    parser = argparse.ArgumentParser(description="Validate Office document XML files")
    parser.add_argument(
        "unpacked_dir",
        help="Path to unpacked Office document directory",
    )
    parser.add_argument(
        "--original",
        required=True,
        help="Path to original file (.docx/.pptx/.xlsx)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    # Validate paths
    unpacked_dir = Path(args.unpacked_dir)
    original_file = Path(args.original)
    file_extension = original_file.suffix.lower()
    if not unpacked_dir.is_dir():
        print(f"Error: {unpacked_dir} is not a directory", file=sys.stderr)
        sys.exit(1)
    if not original_file.is_file():
        print(f"Error: {original_file} is not a file", file=sys.stderr)
        sys.exit(1)
    if file_extension not in [".docx", ".pptx", ".xlsx"]:
        print(f"Error: {original_file} must be a .docx, .pptx, or .xlsx file", file=sys.stderr)
        sys.exit(1)

    # Run validators
    validator = OOXMLValidator(unpacked_dir, original_file, verbose=args.verbose)
    success = validator.validate()

    if success:
        print("All validations PASSED!")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
