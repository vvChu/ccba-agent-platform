"""OKFStructureProcessor Facade Class."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ccba_legal.formatter.chunker import generate_chunks
from ccba_legal.formatter.metadata import (
    inject_anchors,
)
from ccba_legal.formatter.splitter import (
    split_by_chapters,
    split_concept_appendices,
)
from ccba_legal.formatter.table_flattener import (
    find_top_level_tables,
    flatten_html_table,
    grid_to_csv,
    grid_to_json,
    grid_to_markdown,
    process_tables,
)


class OKFStructureProcessor:
    """Handles parsing, formatting, and structural splitting of OKF documents."""

    def __init__(self, formula_standardizer: Callable[[str], str] | None = None) -> None:
        self.formula_standardizer = formula_standardizer

    def format_content(self, content: str, bundle_dir: Path) -> str:
        """Process tables, run formula standardization (if set), and inject anchors."""
        processed_content = self.process_tables(content, bundle_dir)
        if self.formula_standardizer:
            try:
                processed_content = self.formula_standardizer(processed_content)
            except Exception as e:
                print(f"[OKF Formatter] Formula standardization skipped: {e}")
        processed_content = self.inject_anchors(processed_content)
        return processed_content

    def inject_anchors(self, text: str) -> str:
        return inject_anchors(text)

    def flatten_html_table(self, table_soup: Any) -> tuple[list[list[str]], bool, int]:
        return flatten_html_table(table_soup)

    def grid_to_markdown(self, grid: list[list[str]]) -> str:
        return grid_to_markdown(grid)

    def grid_to_csv(self, grid: list[list[str]]) -> str:
        return grid_to_csv(grid)

    def grid_to_json(self, grid: list[list[str]]) -> str:
        return grid_to_json(grid)

    def find_top_level_tables(self, soup: Any) -> list[Any]:
        return find_top_level_tables(soup)

    def process_tables(self, content: str, bundle_dir: Path) -> str:
        return process_tables(content, bundle_dir)

    def split_concept_appendices(self, file_path: Path) -> list[str]:
        return split_concept_appendices(file_path)

    def split_by_chapters(self, content: str, sections_dir: Path) -> None:
        split_by_chapters(content, sections_dir)

    def generate_chunks(self, content: str, bundle_dir: Path) -> None:
        generate_chunks(content, bundle_dir)
