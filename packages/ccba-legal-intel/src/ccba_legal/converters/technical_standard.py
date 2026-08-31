# Copyright (c) 2026 CCBA. All rights reserved.
"""Native Technical Standard (TCVN / QCVN) Strategy Converter Facade (ADR 0030, ADR 0034)."""

from __future__ import annotations

from ccba_legal.converters.standard.handlers.heading_handler import slugify_vietnamese
from ccba_legal.converters.standard.strategy import (
    StandardConversionContext,
    process_technical_standard_strategy,
    render_paragraph_with_runs,
    sanitize_prose_greeks_and_variables,
)

__all__ = [
    "StandardConversionContext",
    "process_technical_standard_strategy",
    "render_paragraph_with_runs",
    "sanitize_prose_greeks_and_variables",
    "slugify_vietnamese",
]
