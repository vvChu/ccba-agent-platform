"""Modular converters package for CCBA Legal Intelligence Platform."""

from __future__ import annotations

from .archetype_scanner import DocumentArchetype, FullDocStructuralScanner, detect_document_pipeline
from .omml import omml_to_latex
from .table_extractor import classify_and_extract_tables
from .technical_formulas import (
    GREEK_MAP,
    INLINE_SYMBOLS_MAP,
    MATH_OPERATORS_MAP,
    load_bundle_formula_overrides,
)
from .technical_standard import process_technical_standard_strategy, slugify_vietnamese
from .unit_normalizer import (
    normalize_clause_numbers,
    normalize_docx_markdown,
    normalize_units_and_math,
)
from .vbpl_admin import (
    extract_legal_basis_graph,
    process_vbpl_bundle_okf_v22,
    process_vbpl_bundle_okf_v24,
)

__all__ = [
    "DocumentArchetype",
    "FullDocStructuralScanner",
    "detect_document_pipeline",
    "classify_and_extract_tables",
    "process_technical_standard_strategy",
    "process_vbpl_bundle_okf_v22",
    "process_vbpl_bundle_okf_v24",
    "normalize_clause_numbers",
    "normalize_docx_markdown",
    "normalize_units_and_math",
    "extract_legal_basis_graph",
    "omml_to_latex",
    "GREEK_MAP",
    "INLINE_SYMBOLS_MAP",
    "MATH_OPERATORS_MAP",
    "load_bundle_formula_overrides",
    "slugify_vietnamese",
]
