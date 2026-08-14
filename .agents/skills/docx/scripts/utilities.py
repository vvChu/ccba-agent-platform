#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx XMLEditor.

Delegates core implementation to the `ccba_ooxml.docx.utilities` deep module.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PKG_SRC = Path(__file__).resolve().parents[4] / "packages" / "ccba-ooxml" / "src"
if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from ccba_ooxml.docx.utilities import (
    XMLEditor,
    _create_line_tracking_parser,
    _generate_hex_id,
    _generate_rsid,
)

__all__ = ["XMLEditor", "_create_line_tracking_parser", "_generate_hex_id", "_generate_rsid"]
