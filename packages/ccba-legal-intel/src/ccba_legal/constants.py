# Copyright (c) 2026 CCBA. All rights reserved.
"""Global architectural constants and specifications for CCBA Legal Intelligence Platform (ADR 0021, ADR 0034, ADR 0036)."""

from __future__ import annotations

# Current canonical OKF specification version
CURRENT_OKF_VERSION: str = "2.4"
CURRENT_OKF_SPEC: str = "v2.4 Universal"
CURRENT_OKF_SCHEMA_URI: str = "https://schemas.ccba.vn/okf/v2.4/schema.json"
CURRENT_CONVERTER_VERSION: str = "0.4.0"

# Universal 5 Compartments Invariant (ADR 0036)
DIR_SOURCES: str = "sources"
DIR_TABLES: str = "tables"
DIR_FIGURES: str = "figures"
DIR_ANNEXES: str = "annexes"
DIR_TEMPLATES: str = "templates"
STANDARD_COMPARTMENTS: tuple[str, ...] = (
    DIR_SOURCES,
    DIR_TABLES,
    DIR_FIGURES,
    DIR_ANNEXES,
    DIR_TEMPLATES,
)

# Master CI Verbatim & Parity Thresholds (ADR 0016, ADR 0037)
GATE_0_MIN_DOCX_PDF_PARITY: float = 70.0
GATE_11_MIN_VERBATIM_PARITY: float = 98.0

# VBHN Legislative Consolidation Specifications
PATCH_MANIFEST_VERSION: str = "2.0"

# Auxiliary Data Component Schema Specifications (ADR 0036, ADR 0041)
TABLES_CATALOG_SCHEMA_VERSION: str = "2.4"
FIGURES_CATALOG_SCHEMA_VERSION: str = "2.4"
AST_CLAUSES_SCHEMA_VERSION: str = "2.4"
QA_BENCHMARK_SCHEMA_VERSION: str = "2.4"
