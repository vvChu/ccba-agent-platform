"""CCBA OOXML Docx Subpackage — DOM manipulation, comments, and tracked changes."""

from __future__ import annotations

from ._report_theme import CCBADocxTheme
from ._tech_report import TechnicalReportBuilder, build_tech_report_from_yaml
from .change_engine import revert_deletion, revert_insertion, suggest_deletion, suggest_paragraph
from .cleanup import (
    clone_xml_text,
    get_authors_from_docx,
    get_tracked_change_authors,
    infer_author,
    merge_runs,
    simplify_redlines,
)
from .comment_engine import CommentEngine
from .document import Document, DocxDocument, DocxXMLEditor
from .utilities import XMLEditor

__all__ = [
    "CCBADocxTheme",
    "TechnicalReportBuilder",
    "build_tech_report_from_yaml",
    "DocxDocument",
    "Document",
    "DocxXMLEditor",
    "CommentEngine",
    "XMLEditor",
    "revert_insertion",
    "revert_deletion",
    "suggest_paragraph",
    "suggest_deletion",
    "merge_runs",
    "simplify_redlines",
    "clone_xml_text",
    "get_tracked_change_authors",
    "get_authors_from_docx",
    "infer_author",
]
