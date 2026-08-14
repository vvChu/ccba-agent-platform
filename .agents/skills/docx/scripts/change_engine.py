#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx change_engine.

Delegates core implementation to the `ccba_ooxml.docx.change_engine` deep module.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PKG_SRC = Path(__file__).resolve().parents[4] / "packages" / "ccba-ooxml" / "src"
if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from ccba_ooxml.docx.change_engine import (
    revert_deletion,
    revert_insertion,
    suggest_deletion,
    suggest_paragraph,
)

__all__ = ["revert_insertion", "revert_deletion", "suggest_paragraph", "suggest_deletion"]
