#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx change_engine.

Delegates core implementation to the `ccba_ooxml.docx.change_engine` deep module.
"""

from __future__ import annotations

try:
    from ccba_ooxml.docx.change_engine import (
        revert_deletion,
        revert_insertion,
        suggest_deletion,
        suggest_paragraph,
    )
except ImportError as e:
    raise ImportError(
        "Package 'ccba-ooxml' chưa được cài đặt trong môi trường ảo. "
        "Vui lòng chạy: python scripts/spoke/spoke_bootstrap.py (hoặc pip install -e packages/ccba-ooxml)"
    ) from e

__all__ = ["revert_insertion", "revert_deletion", "suggest_paragraph", "suggest_deletion"]
