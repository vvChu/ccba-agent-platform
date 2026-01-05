"""
Vietnamese Legal Document Plugin.
"""

from .detector import is_legal_document
from .processor import VNLegalProcessor


def register() -> None:
    """Register this plugin."""
    # In a real system, we might register hooks or processors to a central registry.
    # For now, just ensuring it's importable is enough, or we could print a debug log.
    pass

__all__ = ["is_legal_document", "VNLegalProcessor", "register"]
