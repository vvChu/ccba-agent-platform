"""Backward-compatible forwarding shim for Excel formula recalculation.

.. deprecated:: 1.2.0
    ``xlsx_recalc`` in ``ccba-pdf-prep`` has been relocated to ``ccba_ooxml``
    to align with domain boundaries (OOXML vs PDF Vision).
    Import from ``ccba_ooxml.calc`` or use ``ccba_ooxml.recalc_xlsx`` instead.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from ccba_ooxml.calc import recalc_xlsx as _ooxml_recalc_xlsx
from ccba_ooxml.calc import setup_libreoffice_macro as _ooxml_setup_macro


def setup_libreoffice_macro() -> bool:
    """Setup LibreOffice macro (forwarded to ccba_ooxml.calc)."""
    warnings.warn(
        "setup_libreoffice_macro in ccba_pdf_prep is deprecated; import from ccba_ooxml instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _ooxml_setup_macro()


def recalc_xlsx(filename: str | Path, timeout: int = 30) -> dict[str, Any]:
    """Recalculate formulas in Excel file (forwarded to ccba_ooxml.calc)."""
    warnings.warn(
        "recalc_xlsx in ccba_pdf_prep is deprecated; import from ccba_ooxml instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _ooxml_recalc_xlsx(filename, timeout=timeout)
