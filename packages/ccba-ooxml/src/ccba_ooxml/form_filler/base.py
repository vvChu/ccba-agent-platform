# packages/ccba-ooxml/src/ccba_ooxml/form_filler/base.py
"""Abstract base class and protocol for Form Filler engines."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .exceptions import TemplateProtectionError
from .models import FormFillConfig, TableRule


class BaseFormFillerEngine(ABC):
    """Abstract interface implemented by both Word COM and Soffice Fallback engines."""

    def __init__(self, template_path: Path, config: FormFillConfig | None = None) -> None:
        self.template_path = Path(template_path).resolve()
        self.config = config or FormFillConfig()

    def validate_output_path(self, output_path: Path | str | None) -> None:
        """Ensures output path does not overwrite immutable template file.

        Raises:
            TemplateProtectionError: If output_path resolves to the same file as template_path.
        """
        if output_path is None or not getattr(self.config, "read_only_template", True):
            return
        out = Path(output_path).resolve()
        tpl = self.template_path.resolve()
        if str(out).lower() == str(tpl).lower():
            raise TemplateProtectionError(
                f"Immutable Template Guard: output_path '{out}' cannot overwrite template_path '{self.template_path}'."
            )
        if out.exists() and tpl.exists():
            try:
                if os.path.samefile(out, tpl):
                    raise TemplateProtectionError(
                        f"Immutable Template Guard: output_path '{out}' cannot overwrite template_path '{self.template_path}'."
                    )
            except (ValueError, OSError):
                pass

    @abstractmethod
    def auto_map_fields(self, data: dict[str, Any]) -> None:
        """Automatically maps and fills form fields, checkboxes, and tables from data."""
        ...

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
