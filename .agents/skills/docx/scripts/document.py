#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx Document.

Delegates core implementation to the `ccba_ooxml.docx` deep module.
Maintains 100% compatibility with existing skills and workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Safe Bootstrap: ensure packages/ccba-ooxml/src is in sys.path
_PKG_SRC = Path(__file__).resolve().parents[4] / "packages" / "ccba-ooxml" / "src"
if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from ccba_ooxml.docx import (
    CommentEngine,
    DocxDocument,
    DocxXMLEditor,
    XMLEditor,
    revert_deletion,
    revert_insertion,
    suggest_deletion,
    suggest_paragraph,
)
from ccba_ooxml.docx.comment_engine import TEMPLATE_DIR

Document = DocxDocument

__all__ = [
    "Document",
    "DocxDocument",
    "DocxXMLEditor",
    "CommentEngine",
    "XMLEditor",
    "TEMPLATE_DIR",
    "revert_insertion",
    "revert_deletion",
    "suggest_paragraph",
    "suggest_deletion",
]
