#!/usr/bin/env python3
"""QCVN Markdown Table Standardizer Engine.

Thin CLI Adapter delegating to mdconverter.tables.format_all_qcvn_md_tables.
"""

from __future__ import annotations

import sys
from pathlib import Path

from mdconverter.tables import format_all_qcvn_md_tables


def main() -> None:
    """Format technical compliance tables in a Markdown file."""
    if len(sys.argv) < 2:
        print("Usage: python qcvn_md_table_formatter.py <document.md>")
        sys.exit(1)

    target_md = Path(sys.argv[1])
    if not target_md.exists():
        print(f"File not found: {target_md}")
        sys.exit(1)

    count = format_all_qcvn_md_tables(target_md)
    print(f"Formatted {count} 2D GFM Pipe Tables in {target_md}")


if __name__ == "__main__":
    main()

__all__ = ["format_all_qcvn_md_tables"]
