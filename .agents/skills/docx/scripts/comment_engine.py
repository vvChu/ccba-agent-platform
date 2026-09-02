#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx CommentEngine.

Delegates core implementation to the `ccba_ooxml.docx.comment_engine` deep module.
"""

from __future__ import annotations

try:
    from ccba_ooxml.docx.comment_engine import TEMPLATE_DIR, CommentEngine
except ImportError as e:
    raise ImportError(
        "Package 'ccba-ooxml' chưa được cài đặt trong môi trường ảo. "
        "Vui lòng chạy: python scripts/spoke/spoke_bootstrap.py (hoặc pip install -e packages/ccba-ooxml)"
    ) from e

__all__ = ["CommentEngine", "TEMPLATE_DIR"]
