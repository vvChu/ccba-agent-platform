# Copyright (c) 2026 CCBA. All rights reserved.
"""Sanitizers and AST run renderers for standard converters."""

from __future__ import annotations

from ccba_legal.converters.standard.sanitizers.run_renderer import render_paragraph_with_runs
from ccba_legal.converters.standard.sanitizers.text_normalizer import (
    heal_orphaned_strains,
    normalize_degrees_and_angles,
    normalize_formula_equations,
    sanitize_prose_greeks_and_variables,
)
from ccba_legal.converters.technical_formulas import GREEK_MAP, INLINE_SYMBOLS_MAP

__all__ = [
    "GREEK_MAP",
    "INLINE_SYMBOLS_MAP",
    "heal_orphaned_strains",
    "normalize_degrees_and_angles",
    "normalize_formula_equations",
    "render_paragraph_with_runs",
    "sanitize_prose_greeks_and_variables",
]
