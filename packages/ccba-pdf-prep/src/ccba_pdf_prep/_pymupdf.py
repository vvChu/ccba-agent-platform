"""Internal lazy loader for PyMuPDF inside ccba_pdf_prep."""

from __future__ import annotations

import os
from typing import Any


def _get_fitz() -> Any:
    """Configure PYMUPDF_MESSAGE=fd:2 and lazily import pymupdf."""
    os.environ.setdefault("PYMUPDF_MESSAGE", "fd:2")
    import pymupdf

    return pymupdf
