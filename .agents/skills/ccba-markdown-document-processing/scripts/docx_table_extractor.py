#!/usr/bin/env python3
"""Docx High-Precision Table Extractor Engine.

Thin CLI Adapter delegating to mdconverter.tables.extract_docx_tables.
"""

from __future__ import annotations

import sys
from pathlib import Path

from mdconverter.tables import extract_docx_tables


def main() -> None:
    """Extract tables from DOCX and report structured grid metrics."""
    docx_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".md/extracted_docs/qcvn_06_2022_bxd/qcvn_06_2022_bxd.docx")
    )
    if not docx_file.exists():
        print(f"File not found: {docx_file}")
        sys.exit(1)

    tables = extract_docx_tables(docx_file)
    print(f"Extracted {len(tables)} structured tables from {docx_file}")
    for t in tables:
        print(f"  - [{t.table_id}] {t.caption} ({t.rows} rows x {t.cols} cols)")


if __name__ == "__main__":
    main()
