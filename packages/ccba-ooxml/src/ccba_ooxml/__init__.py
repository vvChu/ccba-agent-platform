"""CCBA OOXML Utilities.

Shared library for packaging, unpackaging, validating, and DOM manipulating docx/pptx/xlsx documents.
"""

from __future__ import annotations

from .calc import recalc_xlsx, setup_libreoffice_macro
from .docx import (
    CommentEngine,
    Document,
    DocxDocument,
    DocxXMLEditor,
    XMLEditor,
    revert_deletion,
    revert_insertion,
    suggest_deletion,
    suggest_paragraph,
)
from .pack import pack_document, validate_document
from .tables import (
    StructuredTable,
    TableReconstructor,
    make_descriptive_table_slug,
    vietnamese_to_ascii,
)
from .unpack import unpack_document
from .workspace import OOXMLWorkspace

__all__ = [
    # Document operations
    "pack_document",
    "unpack_document",
    "validate_document",
    "OOXMLWorkspace",
    # Spreadsheet calculation
    "recalc_xlsx",
    "setup_libreoffice_macro",
    # Docx DOM manipulation
    "DocxDocument",
    "Document",
    "DocxXMLEditor",
    "CommentEngine",
    "XMLEditor",
    "revert_insertion",
    "revert_deletion",
    "suggest_paragraph",
    "suggest_deletion",
    # Table extraction & reconstruction
    "StructuredTable",
    "TableReconstructor",
    "make_descriptive_table_slug",
    "vietnamese_to_ascii",
]
