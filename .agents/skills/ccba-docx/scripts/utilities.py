#!/usr/bin/env python3
"""Thin backward-compatibility adapter for Docx XMLEditor.

Delegates core implementation to the `ccba_ooxml.docx.utilities` deep module.
"""

from __future__ import annotations

try:
    from ccba_ooxml.docx.utilities import (
        XMLEditor,
        _create_line_tracking_parser,
        _generate_hex_id,
        _generate_rsid,
    )
except ImportError as e:
    raise ImportError(
        "Package 'ccba-ooxml' chưa được cài đặt trong môi trường ảo. "
        "Vui lòng chạy: python scripts/spoke/spoke_bootstrap.py (hoặc pip install -e packages/ccba-ooxml)"
    ) from e

__all__ = ["XMLEditor", "_create_line_tracking_parser", "_generate_hex_id", "_generate_rsid"]
