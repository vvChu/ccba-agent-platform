# packages/ccba-ooxml/src/ccba_ooxml/form_filler/__init__.py
"""Word Form Filler Module — Dual-Engine In-Place Document Filling with Form Layout Guard.

Supports native Windows Word COM automation and headless cross-platform LibreOffice fallback.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .base import BaseFormFillerEngine
from .exceptions import (
    EngineUnavailableError,
    FormFillerError,
    LayoutGuardError,
    TemplateNotFoundError,
    TemplateProtectionError,
)
from .fallback_engine import SofficeFallbackEngine
from .layout_guard import FormLayoutGuard
from .models import FormFillConfig, TableRowData, TableRule
from .winword_engine import WinwordEngine


def _is_windows() -> bool:
    return os.name == "nt"


class WordFormFiller:
    """Unified Facade for filling Word form templates with layout guard enforcement."""

    def __init__(
        self,
        template_path: Path | str,
        config: FormFillConfig | None = None,
        engine: str | None = None,
    ) -> None:
        self.template_path = Path(template_path).resolve()
        if not self.template_path.exists():
            raise TemplateNotFoundError(f"Template document '{self.template_path}' not found.")

        self.config = config or FormFillConfig()
        if engine:
            self.config.engine = engine  # type: ignore[assignment]

        self._engine = self._resolve_engine()

    def _resolve_engine(self) -> BaseFormFillerEngine:
        """Resolves optimal engine based on OS platform and configuration."""
        selected_engine = self.config.engine

        if selected_engine == "winword":
            return WinwordEngine(self.template_path, self.config)

        if selected_engine == "soffice":
            return SofficeFallbackEngine(self.template_path, self.config)

        # "auto" detection
        if _is_windows():
            try:
                return WinwordEngine(self.template_path, self.config)
            except Exception:
                # Fallback to soffice if Word COM initialization fails
                return SofficeFallbackEngine(self.template_path, self.config)

        return SofficeFallbackEngine(self.template_path, self.config)

    def auto_map_fields(self, data: dict[str, Any]) -> WordFormFiller:
        """Automatically maps and fills form fields, checkboxes, and tables from data.

        Returns self for fluent method chaining.
        """
        self._engine.auto_map_fields(data)
        return self

    def apply_paragraphs(self, mapping: dict[str, str]) -> WordFormFiller:
        """Substitutes placeholder mappings in body paragraphs and table cells.

        Returns self for fluent method chaining.
        """
        self._engine.apply_paragraphs(mapping)
        return self

    def apply_tables(self, table_rules: list[TableRule]) -> WordFormFiller:
        """Populates dynamic table rows and applies table-specific layout guards.

        Returns self for fluent method chaining.
        """
        self._engine.apply_tables(table_rules)
        return self

    def apply_layout_guard(self) -> WordFormFiller:
        """Applies global layout guards (anti-split rows, forced page breaks).

        Returns self for fluent method chaining.
        """
        self._engine.apply_layout_guard()
        return self

    def export(
        self,
        doc_out: Path | str | None = None,
        pdf_out: Path | str | None = None,
    ) -> dict[str, Path]:
        """Exports the filled document to DOC/DOCX and/or PDF files."""
        return self._engine.export(doc_out=doc_out, pdf_out=pdf_out)

    def close(self) -> None:
        """Closes the underlying engine and cleans up processes and temporary files."""
        if hasattr(self, "_engine") and self._engine is not None:
            self._engine.close()

    def __enter__(self) -> WordFormFiller:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


__all__ = [
    "BaseFormFillerEngine",
    "EngineUnavailableError",
    "FormFillConfig",
    "FormFillerError",
    "FormLayoutGuard",
    "LayoutGuardError",
    "SofficeFallbackEngine",
    "TableRowData",
    "TableRule",
    "TemplateNotFoundError",
    "TemplateProtectionError",
    "WinwordEngine",
    "WordFormFiller",
]
