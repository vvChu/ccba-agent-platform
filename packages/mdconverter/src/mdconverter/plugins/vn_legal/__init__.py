"""
Vietnamese Legal Document Plugin.

Provides detection, processing, linting, and metadata extraction
for Vietnamese legal documents (VBPL).
"""

from .detector import is_legal_document
from .metadata import extract_vn_legal_metadata
from .processor import VNLegalProcessor

__all__ = ["is_legal_document", "VNLegalProcessor", "extract_vn_legal_metadata"]
