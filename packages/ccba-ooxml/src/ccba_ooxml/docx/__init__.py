"""CCBA OOXML Docx Subpackage — DOM manipulation, comments, and tracked changes."""

from __future__ import annotations

from .change_engine import revert_deletion, revert_insertion, suggest_deletion, suggest_paragraph
from .comment_engine import CommentEngine
from .document import Document, DocxDocument, DocxXMLEditor
from .utilities import XMLEditor

__all__ = [
    "DocxDocument",
    "Document",
    "DocxXMLEditor",
    "CommentEngine",
    "XMLEditor",
    "revert_insertion",
    "revert_deletion",
    "suggest_paragraph",
    "suggest_deletion",
]
