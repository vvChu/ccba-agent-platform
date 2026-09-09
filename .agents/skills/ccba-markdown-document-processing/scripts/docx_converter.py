#!/usr/bin/env python3
"""CCBA Master Skill: Markdown Document Processing Engine (Docx Converter).

Thin CLI Adapter delegating to mdconverter.tables.convert_docx_to_okf_bundle.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mdconverter.tables import convert_docx_to_okf_bundle, normalize_docx_markdown


def main() -> None:
    """CLI entry point for converting DOCX to OKF Markdown bundle."""
    parser = argparse.ArgumentParser(description="Convert DOCX to OKF Markdown bundle.")
    parser.add_argument("docx_path", type=str, help="Path to input DOCX file")
    parser.add_argument("target_bundle_dir", type=str, help="Target bundle output directory")
    args = parser.parse_args()

    docx_file = Path(args.docx_path)
    bundle_dir = Path(args.target_bundle_dir)

    res = convert_docx_to_okf_bundle(docx_file, bundle_dir)
    print("\n[COMPLETE OKF BUNDLE RESULT]:", res)


if __name__ == "__main__":
    main()

__all__ = ["normalize_docx_markdown", "convert_docx_to_okf_bundle"]
