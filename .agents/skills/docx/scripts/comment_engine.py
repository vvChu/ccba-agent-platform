#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx CommentEngine.

Delegates core implementation to the `ccba_ooxml.docx.comment_engine` deep module.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PKG_SRC = Path(__file__).resolve().parents[4] / "packages" / "ccba-ooxml" / "src"
if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from ccba_ooxml.docx.comment_engine import TEMPLATE_DIR, CommentEngine

__all__ = ["CommentEngine", "TEMPLATE_DIR"]
