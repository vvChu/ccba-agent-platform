"""
PDF and Content Utilities for mdconverter.
Refactored to use ccba_pdf_prep.
"""

import logging
from collections.abc import Sequence

from ccba_pdf_prep import get_blind_chunks, split_pdf

logger = logging.getLogger(__name__)

# Re-export
__all__ = ["split_pdf", "get_blind_chunks", "merge_markdown"]


def merge_markdown(parts: Sequence[str], separator: str = "\n\n---\n\n") -> str:
    """Merge multiple markdown strings into one."""
    # Filter out empty parts
    valid_parts = [p.strip() for p in parts if p and p.strip()]
    return separator.join(valid_parts)
