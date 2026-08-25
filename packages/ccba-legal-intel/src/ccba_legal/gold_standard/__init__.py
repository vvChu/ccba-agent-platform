"""Modular Gold Standard package for CCBA Legal Intelligence Platform."""

from __future__ import annotations

from .anchor_injector import inject_semantic_anchors
from .ast_qa_generator import (
    extract_tables_and_formulas,
    generate_bundle_ast_and_qa,
    generate_clauses_ast,
)
from .processor import GoldStandardProcessor, process_okf_bundle
from .profiles import DocProfile, get_doc_profile
from .sanitizers import (
    clean_html_tables,
    clean_table_footnotes_and_superscripts,
    normalize_notes_and_lists,
    normalize_tvpl_formatting,
    strip_existing_anchors,
)

__all__ = [
    "DocProfile",
    "get_doc_profile",
    "strip_existing_anchors",
    "normalize_tvpl_formatting",
    "clean_html_tables",
    "clean_table_footnotes_and_superscripts",
    "normalize_notes_and_lists",
    "inject_semantic_anchors",
    "generate_bundle_ast_and_qa",
    "generate_clauses_ast",
    "extract_tables_and_formulas",
    "GoldStandardProcessor",
    "process_okf_bundle",
]
