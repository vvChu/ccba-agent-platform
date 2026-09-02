#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx Document.

Delegates core implementation to the `ccba_ooxml.docx` deep module.
Maintains 100% compatibility with existing skills and workflows.
"""

from __future__ import annotations

try:
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
except ImportError as e:
    raise ImportError(
        "Package 'ccba-ooxml' chưa được cài đặt trong môi trường ảo. "
        "Vui lòng chạy: python scripts/spoke/spoke_bootstrap.py (hoặc pip install -e packages/ccba-ooxml)"
    ) from e

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
