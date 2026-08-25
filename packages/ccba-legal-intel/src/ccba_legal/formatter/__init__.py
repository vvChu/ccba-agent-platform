"""Modular Formatter package for CCBA Legal Intelligence Platform."""

from __future__ import annotations

from .chunker import generate_chunks
from .metadata import (
    extract_parent_metadata,
    inject_anchors,
    inject_warning_block,
)
from .processor import OKFStructureProcessor
from .splitter import (
    split_by_chapters,
    split_concept_appendices,
)
from .table_flattener import (
    find_top_level_tables,
    flatten_html_table,
    grid_to_csv,
    grid_to_json,
    grid_to_markdown,
    process_tables,
)

__all__ = [
    "extract_parent_metadata",
    "inject_anchors",
    "inject_warning_block",
    "flatten_html_table",
    "grid_to_markdown",
    "grid_to_csv",
    "grid_to_json",
    "find_top_level_tables",
    "process_tables",
    "split_concept_appendices",
    "split_by_chapters",
    "generate_chunks",
    "OKFStructureProcessor",
]
