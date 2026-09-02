# Copyright (c) 2026 CCBA. All rights reserved.
"""Data Models & State Definitions for Modular Technical Standard Converter (OKF v2.4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Literal

from docx.table import Table
from docx.text.paragraph import Paragraph

# Strict block typing
DocumentBlockType = Literal["p", "tbl"]
DocumentBlock = tuple[DocumentBlockType, Paragraph | Table]


class HierarchyState(Enum):
    """Hierarchy State Machine states for Standard Documents."""

    BODY_TEXT = auto()
    IN_TRONG_DO = auto()
    IN_LETTERED_LIST = auto()
    IN_BULLET_LIST = auto()
    IN_TABLE = auto()
    IN_FIGURE = auto()


@dataclass
class StandardConversionConfig:
    """Configuration options for standard conversion."""

    bundle_dir: Path
    output_filename: str | None = None
    rid_to_katex: dict[str, str] = field(default_factory=dict)
    enable_modular_annexes: bool = True
    enable_formula_vision: bool = True
    enable_table_extraction: bool = True


@dataclass
class ConversionMetrics:
    """Metrics recorded during document conversion."""

    total_paragraphs: int = 0
    total_tables: int = 0
    clauses_count: int = 0
    tables_count: int = 0
    figures_count: int = 0
    formulas_count: int = 0
    templates_count: int = 0
