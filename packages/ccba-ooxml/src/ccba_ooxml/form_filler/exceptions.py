# packages/ccba-ooxml/src/ccba_ooxml/form_filler/exceptions.py
"""Exceptions for Word Form Filler module."""

from __future__ import annotations


class FormFillerError(Exception):
    """Base exception for all form filler errors."""


class EngineUnavailableError(FormFillerError):
    """Raised when the requested or required execution engine is unavailable."""


class TemplateNotFoundError(FormFillerError):
    """Raised when the template document file does not exist."""


class LayoutGuardError(FormFillerError):
    """Raised when applying layout guard rules fails."""
