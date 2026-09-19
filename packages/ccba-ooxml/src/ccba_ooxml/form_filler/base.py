# packages/ccba-ooxml/src/ccba_ooxml/form_filler/base.py
"""Abstract base class and protocol for Form Filler engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .models import FormFillConfig, TableRule


class BaseFormFillerEngine(ABC):
    """Abstract interface implemented by both Word COM and Soffice Fallback engines."""

    def __init__(self, template_path: Path, config: FormFillConfig | None = None) -> None:
        self.template_path = Path(template_path).resolve()
        self.config = config or FormFillConfig()

    @abstractmethod
    def apply_paragraphs(self, mapping: dict[str, str]) -> None:
        """Substitutes placeholder keys in paragraphs with target text."""
        ...

    @abstractmethod
    def apply_tables(self, table_rules: list[TableRule]) -> None:
        """Fills table data and applies table-specific layout guards."""
        ...

    @abstractmethod
    def apply_layout_guard(self) -> None:
        """Applies global layout guard rules (anti-row-split, page-break keywords)."""
        ...

    @abstractmethod
    def export(
        self,
        doc_out: Path | str | None = None,
        pdf_out: Path | str | None = None,
    ) -> dict[str, Path]:
        """Saves filled document to output DOC/DOCX and/or PDF formats."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Releases underlying resources and cleans up background processes."""
        ...

    def __enter__(self) -> BaseFormFillerEngine:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
