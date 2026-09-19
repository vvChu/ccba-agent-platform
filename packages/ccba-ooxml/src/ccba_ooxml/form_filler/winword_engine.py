# packages/ccba-ooxml/src/ccba_ooxml/form_filler/winword_engine.py
"""Windows Native Word COM In-Place Form Filler Engine."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseFormFillerEngine
from .exceptions import EngineUnavailableError, FormFillerError, TemplateNotFoundError
from .layout_guard import FormLayoutGuard
from .models import FormFillConfig, TableRule

logger = logging.getLogger("ccba.ooxml.form_filler.winword")

# Word Save Formats Enum
WD_FORMAT_DOC = 0
WD_FORMAT_DOCX = 16
WD_EXPORT_FORMAT_PDF = 17


class WinwordEngine(BaseFormFillerEngine):
    """Windows-native engine interacting directly with Word DOM via COM (win32com.client).

    Performs in-place single-pass paragraph replacement and table population, supporting
    both binary .doc (Word 97-2003) and modern .docx natively without multi-stage conversions.
    """

    def __init__(
        self,
        template_path: Path,
        config: FormFillConfig | None = None,
        word_app: Any | None = None,
    ) -> None:
        super().__init__(template_path, config)
        if not self.template_path.exists():
            raise TemplateNotFoundError(f"Template document '{self.template_path}' not found.")

        self._word = word_app
        self._doc: Any | None = None
        self._temp_dir: Path | None = None
        self._working_doc_path: Path | None = None
        self._owns_word_app = word_app is None

        self._initialize_word_com()

    def _initialize_word_com(self) -> None:
        """Initializes Word COM application and opens working document copy."""
        if self._word is None:
            try:
                import win32com.client
            except ImportError as e:
                raise EngineUnavailableError(
                    "win32com.client (pywin32) is not available. WinwordEngine requires Windows and pywin32."
                ) from e

            try:
                # Dispatch Word application
                self._word = win32com.client.DispatchEx("Word.Application")
                self._word.Visible = False
                self._word.DisplayAlerts = False
            except Exception as e:
                raise EngineUnavailableError(
                    f"Failed to start Microsoft Word COM instance: {e}"
                ) from e

        # Create working copy in temp directory to prevent modifying template original
        self._temp_dir = Path(tempfile.mkdtemp(prefix="ccba_word_com_"))
        self._working_doc_path = self._temp_dir / f"working_{self.template_path.name}"
        shutil.copy2(self.template_path, self._working_doc_path)

        try:
            self._doc = self._word.Documents.Open(
                FileName=str(self._working_doc_path),
                ConfirmConversions=False,
                ReadOnly=False,
                AddToRecentFiles=False,
                Visible=False,
            )
        except Exception as e:
            self.close()
            raise FormFillerError(
                f"Word COM failed to open '{self.template_path.name}': {e}"
            ) from e

    def apply_paragraphs(self, mapping: dict[str, str]) -> None:
        """Single-pass replacement across all document paragraphs and table cells."""
        if not mapping or self._doc is None:
            return

        # 1. Main Document Paragraphs
        try:
            for p in self._doc.Paragraphs:
                self._substitute_in_range(p.Range, mapping)
        except Exception as e:
            logger.debug(f"Paragraph substitution encountered error: {e}")

        # 2. Table Cells Paragraphs
        try:
            for table in self._doc.Tables:
                for row in table.Rows:
                    for cell in row.Cells:
                        self._substitute_in_range(cell.Range, mapping)
        except Exception as e:
            logger.debug(f"Table cells substitution encountered error: {e}")

    def _substitute_in_range(self, rng: Any, mapping: dict[str, str]) -> None:
        """Substitutes placeholder keys in COM Range while preserving font formatting."""
        try:
            raw_text = rng.Text
            if not raw_text:
                return

            needs_replace = False
            for k in mapping:
                if k in raw_text:
                    needs_replace = True
                    break

            if not needs_replace:
                return

            # Capture font attributes before text replacement
            font_copy = None
            if self.config.keep_font_formatting:
                try:
                    font_copy = rng.Font.Duplicate
                except Exception:
                    font_copy = None

            new_text = raw_text
            for k, v in mapping.items():
                if k in new_text:
                    new_text = new_text.replace(k, str(v))

            rng.Text = new_text

            # Restore original font attributes
            if font_copy is not None:
                try:
                    rng.Font = font_copy
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Range substitution error: {e}")

    def apply_tables(self, table_rules: list[TableRule]) -> None:
        """Fills table data and applies COM-specific layout guards."""
        if not table_rules or self._doc is None:
            return

        for rule in table_rules:
            table = self._resolve_table(rule)
            if table is None:
                logger.warning(
                    f"⚠️ Target table not found: index={rule.table_index}, keyword='{rule.header_keyword}'"
                )
                continue

            # Populate data rows
            if rule.data_rows and table.Rows.Count >= 2:
                self._populate_table_rows(table, rule)

            # Apply row-split guard (AllowBreakAcrossPages = False)
            prevent_split = self.config.prevent_row_split or not rule.allow_break_across_pages
            if prevent_split:
                for row in table.Rows:
                    FormLayoutGuard.apply_com_cant_split(row)

            # Prune empty rows
            if rule.delete_unused_template_rows or self.config.prune_empty_rows:
                for i in range(table.Rows.Count, 1, -1):
                    row = table.Rows.Item(i)
                    if FormLayoutGuard.is_com_row_empty(row):
                        FormLayoutGuard.remove_com_row(row)

    def _resolve_table(self, rule: TableRule) -> Any | None:
        """Finds target COM table by index or keyword search."""
        if not self._doc.Tables or self._doc.Tables.Count == 0:
            return None

        if rule.header_keyword:
            kw = rule.header_keyword.lower()
            for i in range(1, self._doc.Tables.Count + 1):
                t = self._doc.Tables.Item(i)
                if t.Rows.Count > 0:
                    header_text = t.Rows.Item(1).Range.Text.lower()
                    if kw in header_text:
                        return t

        target_idx_1based = rule.table_index + 1
        if target_idx_1based <= self._doc.Tables.Count:
            return self._doc.Tables.Item(target_idx_1based)

        return None

    def _populate_table_rows(self, table: Any, rule: TableRule) -> None:
        """Inserts dynamic data rows in Word COM table."""
        try:
            # 1-based indexing for COM Table
            template_row = table.Rows.Item(2)
            headers = [
                table.Cell(1, c).Range.Text.replace("\r", "").replace("\x07", "").strip()
                for c in range(1, table.Columns.Count + 1)
            ]

            for item_idx, data_row in enumerate(rule.data_rows):
                if item_idx == 0:
                    current_row = template_row
                else:
                    # Append new row to table
                    current_row = table.Rows.Add()

                for col_idx in range(1, table.Columns.Count + 1):
                    col_name = (
                        headers[col_idx - 1] if col_idx - 1 < len(headers) else str(col_idx - 1)
                    )
                    val = None

                    if rule.column_mapping and col_name in rule.column_mapping:
                        dict_key = rule.column_mapping[col_name]
                        val = data_row.get(dict_key)
                    elif col_name in data_row:
                        val = data_row[col_name]
                    elif str(col_idx - 1) in data_row:
                        val = data_row[str(col_idx - 1)]

                    if val is not None:
                        current_row.Cells.Item(col_idx).Range.Text = str(val)
        except Exception as e:
            logger.warning(f"Error populating COM table rows: {e}")

    def apply_layout_guard(self) -> None:
        """Applies global layout guards across Word COM document."""
        if self._doc is None:
            return

        # 1. Enforce PageBreakBefore for keyword-matching paragraphs
        if self.config.page_break_keywords:
            try:
                for p in self._doc.Paragraphs:
                    p_text_lower = p.Range.Text.lower()
                    for kw in self.config.page_break_keywords:
                        if kw.lower() in p_text_lower:
                            FormLayoutGuard.apply_com_page_break_before(p)
                            break
            except Exception as e:
                logger.debug(f"Error applying page break guard: {e}")

        # 2. Prevent row split across all tables
        if self.config.prevent_row_split:
            try:
                for table in self._doc.Tables:
                    for row in table.Rows:
                        FormLayoutGuard.apply_com_cant_split(row)
            except Exception as e:
                logger.debug(f"Error applying cant-split guard: {e}")

    def export(
        self,
        doc_out: Path | str | None = None,
        pdf_out: Path | str | None = None,
    ) -> dict[str, Path]:
        """Saves document via Word COM SaveAs2 and ExportAsFixedFormat."""
        if self._doc is None:
            raise FormFillerError("Document not initialized or already closed.")

        self.apply_layout_guard()

        outputs: dict[str, Path] = {}

        if doc_out:
            doc_path = Path(doc_out).resolve()
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            fmt = WD_FORMAT_DOC if doc_path.suffix.lower() == ".doc" else WD_FORMAT_DOCX

            try:
                self._doc.SaveAs2(FileName=str(doc_path), FileFormat=fmt)
                outputs["doc"] = doc_path
            except Exception as e:
                raise FormFillerError(f"Failed to save document to '{doc_path}': {e}") from e

        if pdf_out:
            pdf_path = Path(pdf_out).resolve()
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                self._doc.ExportAsFixedFormat(
                    OutputFileName=str(pdf_path),
                    ExportFormat=WD_EXPORT_FORMAT_PDF,
                    OpenAfterExport=False,
                    OptimizeFor=0,  # wdExportOptimizeForPrint
                )
                outputs["pdf"] = pdf_path
            except Exception as e:
                raise FormFillerError(f"Failed to export PDF to '{pdf_path}': {e}") from e

        return outputs

    def close(self) -> None:
        """Closes document and quits Word COM application safely, preventing orphaned processes."""
        if self._doc is not None:
            try:
                self._doc.Close(SaveChanges=False)
            except Exception as e:
                logger.debug(f"Error closing Word document: {e}")
            self._doc = None

        if self._owns_word_app and self._word is not None:
            try:
                self._word.Quit()
            except Exception as e:
                logger.debug(f"Error quitting Word application: {e}")
            self._word = None

        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
