# packages/ccba-ooxml/src/ccba_ooxml/form_filler/winword_engine.py
"""Windows Native Word COM In-Place Form Filler Engine."""

from __future__ import annotations

import logging
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .aliases import (
    flatten_data,
    normalize_label,
    resolve_field_value,
)
from .base import BaseFormFillerEngine
from .exceptions import EngineUnavailableError, FormFillerError, TemplateNotFoundError
from .layout_guard import FormLayoutGuard
from .models import FormFillConfig, TableRule

logger = logging.getLogger("ccba.ooxml.form_filler.winword")

# Word Save Formats Enum
WD_FORMAT_DOC = 0
WD_FORMAT_DOCX = 16
WD_EXPORT_FORMAT_PDF = 17


def _com_find_replace(rng: Any, find_text: str, replace_text: str) -> bool:
    """Executes find-and-replace on a Word COM Range."""
    try:
        find = getattr(rng, "Find", None)
        if find is None:
            return False
        if hasattr(find, "ClearFormatting"):
            find.ClearFormatting()
        if hasattr(find, "Replacement") and hasattr(find.Replacement, "ClearFormatting"):
            find.Replacement.ClearFormatting()
        if hasattr(find, "Execute"):
            find.Execute(
                FindText=find_text,
                ReplaceWith=replace_text,
                Replace=1,  # wdReplaceOne
            )
            return True
    except Exception as e:
        logger.debug(f"COM find-replace error: {e}")
    return False


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

    def auto_map_fields(self, data: dict[str, Any]) -> None:
        """Automatically maps and fills form fields, checkboxes, and tables from data."""
        if not data or self._doc is None:
            return

        flat = flatten_data(data)

        # 1. Dynamic Data Tables (list[dict])
        self._auto_map_dynamic_tables(flat)

        # 2. Property Sheet Tables (2-col or 4-col key-value cells)
        self._auto_map_property_sheet_tables(flat)

        # 3. Checkboxes across document paragraphs and table cells
        self._auto_map_checkboxes(flat)

        # 4. Inline Paragraphs & Free-text Fields
        self._auto_map_inline_paragraphs(flat)

    def _auto_map_dynamic_tables(self, flat: dict[str, Any]) -> None:
        """Identifies dynamic tables in Word COM document and populates list rows."""
        list_fields = {
            k: v
            for k, v in flat.items()
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)
        }
        self._dynamic_table_indices: set[int] = set()
        if not list_fields or not getattr(self._doc, "Tables", None):
            return

        try:
            table_count = getattr(self._doc.Tables, "Count", 0)
            matched_tables: dict[int, tuple[str, dict[str, str]]] = {}

            for field_key, items in list_fields.items():
                best_table_idx = None
                best_mapping: dict[str, str] = {}
                best_score = 0

                for t_idx in range(1, table_count + 1):
                    table = self._doc.Tables.Item(t_idx)
                    row_count = getattr(table.Rows, "Count", 0)
                    if row_count < 2:
                        continue

                    col_count = getattr(table.Columns, "Count", 0)
                    headers = []
                    for c in range(1, col_count + 1):
                        try:
                            raw_c = table.Cell(1, c).Range.Text
                            headers.append(raw_c.replace("\r", "").replace("\x07", "").strip())
                        except Exception:
                            headers.append(str(c))

                    col_mapping: dict[str, str] = {}
                    for col_name in headers:
                        norm_col = normalize_label(col_name)
                        if norm_col in ["stt", "no", "tt"]:
                            col_mapping[col_name] = col_name
                            continue
                        found, _, resolved_key = resolve_field_value(col_name, items[0])
                        if found and resolved_key:
                            col_mapping[col_name] = resolved_key

                    score = sum(
                        1 for c in col_mapping if normalize_label(c) not in ["stt", "no", "tt"]
                    )
                    min_required = min(2, len(items[0]))
                    if score >= min_required and score > best_score:
                        best_score = score
                        best_mapping = col_mapping
                        best_table_idx = t_idx

                if best_table_idx is not None and best_table_idx not in matched_tables:
                    matched_tables[best_table_idx] = (field_key, best_mapping)

            for t_idx, (field_key, mapping) in matched_tables.items():
                self._dynamic_table_indices.add(t_idx)
                table = self._doc.Tables.Item(t_idx)
                items = list_fields[field_key]
                col_count = getattr(table.Columns, "Count", 0)
                headers = []
                for c in range(1, col_count + 1):
                    try:
                        raw_c = table.Cell(1, c).Range.Text
                        headers.append(raw_c.replace("\r", "").replace("\x07", "").strip())
                    except Exception:
                        headers.append(str(c))

                augmented_rows: list[dict[str, str]] = []
                for idx, row in enumerate(items):
                    row_dict = {str(k): str(v) for k, v in row.items()}
                    for h in headers:
                        if normalize_label(h) in ["stt", "no", "tt"]:
                            stt_val = str(row.get("stt", row.get("STT", idx + 1)))
                            row_dict[h] = stt_val
                            mapping[h] = h
                    augmented_rows.append(row_dict)

                rule = TableRule(
                    table_index=t_idx - 1,
                    data_rows=augmented_rows,
                    delete_unused_template_rows=self.config.prune_empty_rows,
                    allow_break_across_pages=not self.config.prevent_row_split,
                    column_mapping=mapping,
                )
                self.apply_tables([rule])
        except Exception as e:
            logger.debug(f"Dynamic table error in COM: {e}")

    def _auto_map_property_sheet_tables(self, flat: dict[str, Any]) -> None:
        """Fills key-value cell pairs in Word COM tables."""
        if not getattr(self._doc, "Tables", None):
            return

        try:
            table_count = getattr(self._doc.Tables, "Count", 0)
            for i in range(1, table_count + 1):
                if hasattr(self, "_dynamic_table_indices") and i in self._dynamic_table_indices:
                    continue
                t = self._doc.Tables.Item(i)
                try:
                    row_count = getattr(t.Rows, "Count", 0)
                    for r in range(1, row_count + 1):
                        row = t.Rows.Item(r)
                        cell_count = getattr(row.Cells, "Count", 0)
                        if cell_count >= 2:
                            for c_idx in range(1, cell_count, 2):
                                cell_lbl = row.Cells.Item(c_idx)
                                cell_val = row.Cells.Item(c_idx + 1)
                                raw_lbl = (
                                    cell_lbl.Range.Text.replace("\r", "")
                                    .replace("\x07", "")
                                    .strip()
                                )
                                if not raw_lbl:
                                    continue
                                found, val, _ = resolve_field_value(raw_lbl, flat)
                                if found and not isinstance(val, (list, dict)):
                                    raw_val = (
                                        cell_val.Range.Text.replace("\r", "")
                                        .replace("\x07", "")
                                        .strip()
                                    )
                                    if (
                                        not raw_val
                                        or re.match(r"^[\.\…_\–\—\-]+$", raw_val)
                                        or (raw_val.startswith("{{") and raw_val.endswith("}}"))
                                    ):
                                        cell_val.Range.Text = str(val)
                except Exception as row_err:
                    logger.debug(f"Table {i} rows traversal exception: {row_err}")
        except Exception as e:
            logger.debug(f"Property sheet tables error in COM: {e}")

    def _is_option_selected(
        self, norm_opt: str, flat: dict[str, Any], context_label: str | None = None
    ) -> bool:
        """Determines if a checkbox option matches the given dataset with context awareness."""
        if context_label:
            found, field_val, _ = resolve_field_value(context_label, flat)
            if found:
                if isinstance(field_val, str) and normalize_label(field_val) == norm_opt:
                    return True
                if (
                    isinstance(field_val, bool)
                    and field_val is True
                    and norm_opt in ["co", "yes", "true", "dong_y"]
                ):
                    return True
                return False

        if flat.get(norm_opt) is True:
            return True

        for k, v in flat.items():
            if isinstance(v, bool) and v is True and normalize_label(k) == norm_opt:
                return True

        # Category-based fallback when context_label is absent
        GENDER_OPTS = {"nam", "nu", "male", "female"}
        MARITAL_OPTS = {
            "da_ket_hon",
            "doc_than",
            "ly_hon",
            "ket_hon",
            "married",
            "single",
            "divorced",
        }
        if norm_opt in GENDER_OPTS:
            found, g_val, _ = resolve_field_value("gioi_tinh", flat)
            if found and isinstance(g_val, str):
                return normalize_label(g_val) == norm_opt
        elif norm_opt in MARITAL_OPTS:
            found, m_val, _ = resolve_field_value("tinh_trang_hon_nhan", flat)
            if found and isinstance(m_val, str):
                return normalize_label(m_val) == norm_opt

        return False

    def _auto_map_checkboxes(self, flat: dict[str, Any]) -> None:
        """Identifies and checks checkboxes [ ] -> [X] in COM document."""
        postfix_re = re.compile(r"([0-9A-Za-zÀ-ỹ\s]+?)\s*(\[\s*\]|\(\s*\)|☐|□)")
        prefix_re = re.compile(
            r"(\[\s*\]|\(\s*\)|☐|□)\s*([0-9A-Za-zÀ-ỹ\s]+?)(?=\s{2,}|\s*(?:\[|\(|\u2610|\u25a1)|$)"
        )

        try:
            paragraphs = getattr(self._doc, "Paragraphs", [])
            for p in paragraphs:
                self._check_checkboxes_in_range(p.Range, flat, postfix_re, prefix_re)

            tables = getattr(self._doc, "Tables", None)
            if tables:
                table_count = getattr(tables, "Count", 0)
                if table_count > 0:
                    for t_idx in range(1, table_count + 1):
                        t = tables.Item(t_idx)
                        try:
                            row_count = getattr(t.Rows, "Count", 0)
                            for r in range(1, row_count + 1):
                                row = t.Rows.Item(r)
                                cell_count = getattr(row.Cells, "Count", 0)
                                for c in range(1, cell_count + 1):
                                    self._check_checkboxes_in_range(
                                        row.Cells.Item(c).Range, flat, postfix_re, prefix_re
                                    )
                        except Exception:
                            pass
                elif hasattr(tables, "__iter__"):
                    for t in tables:
                        for row in getattr(t, "Rows", []):
                            for cell in getattr(row, "Cells", []):
                                self._check_checkboxes_in_range(
                                    cell.Range, flat, postfix_re, prefix_re
                                )
        except Exception as e:
            logger.debug(f"Checkbox processing error in COM: {e}")

    def _check_checkboxes_in_range(
        self, rng: Any, flat: dict[str, Any], postfix_re: re.Pattern, prefix_re: re.Pattern
    ) -> None:
        text = getattr(rng, "Text", "")
        if not text or not any(cb in text for cb in ["[ ]", "[]", "( )", "()", "☐", "□"]):
            return

        first_box = re.search(r"(\[\s*\]|\[\]|\(\s*\)|\(\)|☐|□)", text)
        if not first_box:
            return
        pre = text[: first_box.start()].strip()
        style = "prefix" if not pre or pre.endswith(":") or pre.endswith("：") else "postfix"

        prefix_label_match = re.match(r"^([0-9A-Za-zÀ-ỹ\s\/\(\)\-\.]+?):\s*", text)
        context_label = prefix_label_match.group(1).strip() if prefix_label_match else None

        if style == "postfix":
            for m in postfix_re.finditer(text):
                opt_raw = m.group(1).strip()
                box = m.group(2)
                norm_opt = normalize_label(opt_raw)
                if not norm_opt:
                    continue
                if self._is_option_selected(norm_opt, flat, context_label):
                    checked_box = "[X]" if "[" in box else ("(X)" if "(" in box else "☒")
                    target = m.group(0)
                    replacement = m.group(0).replace(box, checked_box, 1)
                    if not _com_find_replace(rng, target, replacement):
                        rng.Text = rng.Text.replace(target, replacement, 1)
        else:
            for m in prefix_re.finditer(text):
                box = m.group(1)
                opt_raw = m.group(2).strip()
                norm_opt = normalize_label(opt_raw)
                if not norm_opt:
                    continue
                if self._is_option_selected(norm_opt, flat, context_label):
                    checked_box = "[X]" if "[" in box else ("(X)" if "(" in box else "☒")
                    target = m.group(0)
                    replacement = m.group(0).replace(box, checked_box, 1)
                    if not _com_find_replace(rng, target, replacement):
                        rng.Text = rng.Text.replace(target, replacement, 1)

    def _auto_map_inline_paragraphs(self, flat: dict[str, Any]) -> None:
        """Substitutes label-dot patterns and {{placeholders}} across COM ranges."""
        label_dot_re = re.compile(r"([0-9A-Za-zÀ-ỹ\s\/\(\)\-\.]+?)\s*[:：]?\s*([\.…_–—\-]{2,})")
        placeholder_re = re.compile(r"\{\{?\s*([0-9A-Za-zÀ-ỹ_\-]+)\s*\}\}?")

        try:
            paragraphs = getattr(self._doc, "Paragraphs", [])
            for p in paragraphs:
                self._substitute_inline_in_range(p.Range, flat, label_dot_re, placeholder_re)

            tables = getattr(self._doc, "Tables", None)
            if tables:
                table_count = getattr(tables, "Count", 0)
                if table_count > 0:
                    for t_idx in range(1, table_count + 1):
                        t = tables.Item(t_idx)
                        try:
                            row_count = getattr(t.Rows, "Count", 0)
                            for r in range(1, row_count + 1):
                                row = t.Rows.Item(r)
                                cell_count = getattr(row.Cells, "Count", 0)
                                for c in range(1, cell_count + 1):
                                    self._substitute_inline_in_range(
                                        row.Cells.Item(c).Range, flat, label_dot_re, placeholder_re
                                    )
                        except Exception:
                            pass
                elif hasattr(tables, "__iter__"):
                    for t in tables:
                        for row in getattr(t, "Rows", []):
                            for cell in getattr(row, "Cells", []):
                                self._substitute_inline_in_range(
                                    cell.Range, flat, label_dot_re, placeholder_re
                                )
        except Exception as e:
            logger.debug(f"Inline substitution error in COM: {e}")

    def _substitute_inline_in_range(
        self, rng: Any, flat: dict[str, Any], label_dot_re: re.Pattern, placeholder_re: re.Pattern
    ) -> None:
        text = getattr(rng, "Text", "")
        if not text:
            return

        for m in label_dot_re.finditer(text):
            raw_label = m.group(1).strip()
            dots = m.group(2)
            found, val, _ = resolve_field_value(raw_label, flat)
            if found and not isinstance(val, (list, dict)):
                target = m.group(0)
                prefix = target[: len(target) - len(dots)]
                rep_val = str(val) if prefix.endswith(" ") else f" {val}"
                replacement = f"{prefix}{rep_val}"
                if not _com_find_replace(rng, target, replacement):
                    rng.Text = rng.Text.replace(target, replacement, 1)

        for m in placeholder_re.finditer(text):
            full_ph = m.group(0)
            var_name = m.group(1)
            found, val, _ = resolve_field_value(var_name, flat)
            if found and not isinstance(val, (list, dict)):
                target = full_ph
                replacement = str(val)
                if not _com_find_replace(rng, target, replacement):
                    rng.Text = rng.Text.replace(target, replacement, 1)

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

        if doc_out:
            self.validate_output_path(doc_out)
        if pdf_out:
            self.validate_output_path(pdf_out)

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
