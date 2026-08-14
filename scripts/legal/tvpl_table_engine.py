"""Thin Backward-Compatible Facade for DOCX Table Parsing Engine.

Delegates table extraction to the deep seam in ``ccba_legal.cleaners``.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from ccba_legal.cleaners import (
        Cleaners,
        convert_docx_table_to_markdown,
        extract_docx_with_tables,
    )
except (ImportError, ValueError):
    _PKG_SRC = Path(__file__).resolve().parents[2] / "packages" / "ccba-legal-intel" / "src"
    if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
        sys.path.insert(0, str(_PKG_SRC))
    from ccba_legal.cleaners import (
        Cleaners,
        convert_docx_table_to_markdown,
        extract_docx_with_tables,
    )

__all__ = [
    "Cleaners",
    "convert_docx_table_to_markdown",
    "extract_docx_with_tables",
]
