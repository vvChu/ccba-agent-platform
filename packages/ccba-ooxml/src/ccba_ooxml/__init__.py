"""CCBA OOXML Utilities

Shared library for packaging, unpackaging, and validating docx/pptx/xlsx documents.
"""

from __future__ import annotations

from .pack import pack_document, validate_document
from .unpack import unpack_document
from .workspace import OOXMLWorkspace

__all__ = [
    # Document operations
    "pack_document",
    "unpack_document",
    "validate_document",
    "OOXMLWorkspace",
]
