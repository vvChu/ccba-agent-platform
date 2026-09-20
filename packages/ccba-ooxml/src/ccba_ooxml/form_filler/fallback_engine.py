# packages/ccba-ooxml/src/ccba_ooxml/form_filler/fallback_engine.py
"""Headless cross-platform Form Filler Engine using LibreOffice and python-docx."""

from __future__ import annotations

import copy
import logging
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ..soffice import find_soffice_bin, run_soffice
from .aliases import (
    flatten_data,
    normalize_label,
    resolve_field_value,
)
from .base import BaseFormFillerEngine
from .exceptions import EngineUnavailableError, FormFillerError, TemplateNotFoundError
from .layout_guard import FormLayoutGuard
from .models import FormFillConfig, TableRule

logger = logging.getLogger("ccba.ooxml.form_filler.fallback")


def _replace_text_in_paragraph_runs(p: Any, target: str, replacement: str) -> bool:
    """Replaces first occurrence of target in paragraph runs, preserving formatting."""
    if not target or target not in p.text:
        return False

    for run in p.runs:
        if target in run.text:
            run.text = run.text.replace(target, replacement, 1)
            return True

    full_text = p.text
    idx = full_text.find(target)
    if idx == -1:
        return False
    target_end = idx + len(target)

    return _replace_slice_in_paragraph_runs(p, idx, target_end, replacement)


def _replace_slice_in_paragraph_runs(
    p: Any, start_idx: int, end_idx: int, replacement: str
) -> bool:
    """Replaces exact character slice [start_idx, end_idx] in paragraph runs.

    Preserves font properties of runs outside the slice, and applies replacement
    into the primary run intersecting the slice without destroying surrounding formatting.
    """
    if start_idx >= end_idx:
        return False

    cur_pos = 0
    runs_to_modify = []
    for r_i, run in enumerate(p.runs):
        r_len = len(run.text)
        r_start = cur_pos
        r_end = cur_pos + r_len
        cur_pos = r_end

        if max(r_start, start_idx) < min(r_end, end_idx):
            runs_to_modify.append((r_i, run, r_start, r_end))

    if not runs_to_modify:
        return False

    first_idx, first_run, f_start, f_end = runs_to_modify[0]
    prefix = first_run.text[: max(0, start_idx - f_start)]

    last_idx, last_run, l_start, l_end = runs_to_modify[-1]
    suffix = last_run.text[min(len(last_run.text), end_idx - l_start) :]

    if first_idx == last_idx:
        first_run.text = prefix + replacement + suffix
    else:
        first_run.text = prefix + replacement
        for _, mid_run, _, _ in runs_to_modify[1:-1]:
            mid_run.text = ""
        last_run.text = suffix

    return True


class SofficeFallbackEngine(BaseFormFillerEngine):
    """Fallback engine using python-docx for manipulation and LibreOffice (soffice) for .doc/.pdf conversion."""

    def __init__(self, template_path: Path, config: FormFillConfig | None = None) -> None:
        super().__init__(template_path, config)
        if not self.template_path.exists():
            raise TemplateNotFoundError(f"Template document '{self.template_path}' not found.")

        self._temp_dir: Path | None = None
        self._working_docx_path: Path | None = None
        self._doc: Any | None = None

        self._initialize_document()

    def _initialize_document(self) -> None:
        """Loads template into python-docx, converting from .doc via soffice if necessary."""
        try:
            import docx
        except ImportError as e:
            raise EngineUnavailableError(
                "python-docx is required for SofficeFallbackEngine. Please install python-docx."
            ) from e

        ext = self.template_path.suffix.lower()

        if ext == ".docx":
            # Work on a copy in temp dir to avoid modifying original template
            self._temp_dir = Path(tempfile.mkdtemp(prefix="ccba_form_filler_"))
            self._working_docx_path = self._temp_dir / f"working_{self.template_path.name}"
            shutil.copy2(self.template_path, self._working_docx_path)
            self._doc = docx.Document(str(self._working_docx_path))
        elif ext == ".doc":
            # Binary Word 97-2003 requires LibreOffice conversion to DOCX first
            soffice_bin = find_soffice_bin()
            if not soffice_bin:
                raise EngineUnavailableError(
                    f"Converting legacy .doc template '{self.template_path.name}' requires LibreOffice (soffice), "
                    "which was not found on this system."
                )

            self._temp_dir = Path(tempfile.mkdtemp(prefix="ccba_form_filler_"))
            logger.info(
                f"🔄 Converting binary .doc '{self.template_path.name}' to .docx via soffice..."
            )
            res = run_soffice(
                [
                    "--headless",
                    "--convert-to",
                    "docx",
                    str(self.template_path),
                    "--outdir",
                    str(self._temp_dir),
                ],
                timeout=self.config.timeout_seconds,
            )
            if res.returncode != 0:
                raise FormFillerError(
                    f"LibreOffice failed to convert .doc to .docx: {res.stderr or 'Unknown error'}"
                )

            converted_name = f"{self.template_path.stem}.docx"
            self._working_docx_path = self._temp_dir / converted_name
            if not self._working_docx_path.exists():
                raise FormFillerError(
                    f"Expected converted file '{self._working_docx_path}' not found."
                )

            self._doc = docx.Document(str(self._working_docx_path))
        else:
            raise FormFillerError(f"Unsupported document format '{ext}'. Expected .doc or .docx.")

    def auto_map_fields(self, data: dict[str, Any]) -> None:
        """Automatically maps and fills form fields, checkboxes, and tables from data."""
        if not data or self._doc is None:
            return

        flat = flatten_data(data)

        # 1. Dynamic Data Tables (list[dict])
        self._auto_map_dynamic_tables(flat)

        # 2. Property Sheet Tables (2-col or 4-col key-value cells)
        self._auto_map_property_sheet_tables(flat)

        # 3. Checkboxes across body paragraphs and table cells
        self._auto_map_checkboxes(flat)

        # 4. Inline Paragraphs & Free-text Fields
        self._auto_map_inline_paragraphs(flat)

    def _auto_map_dynamic_tables(self, flat: dict[str, Any]) -> None:
        """Identifies dynamic tables in document and populates list data rows."""
        list_fields = {
            k: v
            for k, v in flat.items()
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)
        }
        self._dynamic_table_indices: set[int] = set()
        if not list_fields or not self._doc.tables:
            return

        matched_tables: dict[int, tuple[str, dict[str, str]]] = {}

        for field_key, items in list_fields.items():
            best_table_idx = None
            best_mapping: dict[str, str] = {}
            best_score = 0

            for table_idx, table in enumerate(self._doc.tables):
                if len(table.rows) < 2:
                    continue

                header_cells = [c.text.strip() for c in table.rows[0].cells]
                col_mapping: dict[str, str] = {}

                for col_name in header_cells:
                    norm_col = normalize_label(col_name)
                    if norm_col in ["stt", "no", "tt"]:
                        col_mapping[col_name] = col_name
                        continue
                    found, _, resolved_key = resolve_field_value(col_name, items[0])
                    if found and resolved_key:
                        col_mapping[col_name] = resolved_key

                score = sum(1 for c in col_mapping if normalize_label(c) not in ["stt", "no", "tt"])
                min_required = min(2, len(items[0]))
                if score >= min_required and score > best_score:
                    best_score = score
                    best_mapping = col_mapping
                    best_table_idx = table_idx

            if best_table_idx is not None and best_table_idx not in matched_tables:
                matched_tables[best_table_idx] = (field_key, best_mapping)

        for table_idx, (field_key, mapping) in matched_tables.items():
            self._dynamic_table_indices.add(table_idx)
            table = self._doc.tables[table_idx]
            items = list_fields[field_key]
            header_cells = [c.text.strip() for c in table.rows[0].cells]
            augmented_rows: list[dict[str, str]] = []
            for idx, row in enumerate(items):
                row_dict = {str(k): str(v) for k, v in row.items()}
                for h in header_cells:
                    if normalize_label(h) in ["stt", "no", "tt"]:
                        stt_val = str(row.get("stt", row.get("STT", idx + 1)))
                        row_dict[h] = stt_val
                        mapping[h] = h
                augmented_rows.append(row_dict)

            rule = TableRule(
                table_index=table_idx,
                data_rows=augmented_rows,
                delete_unused_template_rows=self.config.prune_empty_rows,
                allow_break_across_pages=not self.config.prevent_row_split,
                column_mapping=mapping,
            )
            self.apply_tables([rule])

    def _auto_map_property_sheet_tables(self, flat: dict[str, Any]) -> None:
        """Fills key-value cell pairs in property sheet tables (2-col or 4-col layout)."""
        if not self._doc.tables:
            return

        for table_idx, table in enumerate(self._doc.tables):
            if hasattr(self, "_dynamic_table_indices") and table_idx in self._dynamic_table_indices:
                continue
            for row in table.rows:
                unique_cells = []
                visited_tc: set[Any] = set()

                for cell in row.cells:
                    if cell._tc not in visited_tc:
                        visited_tc.add(cell._tc)
                        unique_cells.append(cell)

                if len(unique_cells) >= 2:
                    for i in range(0, len(unique_cells) - 1, 2):
                        lbl_cell = unique_cells[i]
                        val_cell = unique_cells[i + 1]
                        lbl_text = lbl_cell.text.strip()
                        if not lbl_text:
                            continue
                        found, val, _ = resolve_field_value(lbl_text, flat)
                        if found and not isinstance(val, (list, dict)):
                            val_text = val_cell.text.strip()
                            if (
                                not val_text
                                or re.match(r"^[\.\…_\–\—\s]+$", val_text)
                                or (val_text.startswith("{{") and val_text.endswith("}}"))
                            ):
                                if val_cell.paragraphs:
                                    p = val_cell.paragraphs[0]
                                    if p.runs and self.config.keep_font_formatting:
                                        primary = p.runs[0]
                                        fn = primary.font.name
                                        fs = primary.font.size
                                        b = primary.bold
                                        it = primary.italic
                                        p.text = str(val)
                                        if p.runs:
                                            r = p.runs[0]
                                            if fn:
                                                r.font.name = fn
                                            if fs:
                                                r.font.size = fs
                                            if b is not None:
                                                r.bold = b
                                            if it is not None:
                                                r.italic = it
                                    else:
                                        p.text = str(val)
                                else:
                                    val_cell.text = str(val)

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
        """Identifies and checks checkboxes [ ] -> [X] based on matching data values."""
        paragraphs = list(self._doc.paragraphs)
        for table in self._doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    paragraphs.extend(cell.paragraphs)

        postfix_re = re.compile(r"([0-9A-Za-zÀ-ỹ\s]+?)\s*(\[\s*\]|\(\s*\)|☐|□)")
        prefix_re = re.compile(
            r"(\[\s*\]|\(\s*\)|☐|□)\s*([0-9A-Za-zÀ-ỹ\s]+?)(?=\s{2,}|\s*(?:\[|\(|\u2610|\u25a1)|$)"
        )

        for p in paragraphs:
            text = p.text
            if not text or not any(cb in text for cb in ["[ ]", "[]", "( )", "()", "☐", "□"]):
                continue

            first_box = re.search(r"(\[\s*\]|\[\]|\(\s*\)|\(\)|☐|□)", text)
            if not first_box:
                continue
            pre = text[: first_box.start()].strip()
            style = "prefix" if not pre or pre.endswith(":") or pre.endswith("：") else "postfix"

            prefix_label_match = re.match(r"^([0-9A-Za-zÀ-ỹ\s\/\(\)\-\.]+?):\s*", text)
            context_label = prefix_label_match.group(1).strip() if prefix_label_match else None

            replacements: list[tuple[int, int, str]] = []

            if style == "postfix":
                for m in postfix_re.finditer(text):
                    opt_raw = m.group(1).strip()
                    box = m.group(2)
                    norm_opt = normalize_label(opt_raw)
                    if not norm_opt:
                        continue
                    if self._is_option_selected(norm_opt, flat, context_label):
                        checked_box = "[X]" if "[" in box else ("(X)" if "(" in box else "☒")
                        replacements.append((m.start(2), m.end(2), checked_box))
            else:
                for m in prefix_re.finditer(text):
                    box = m.group(1)
                    opt_raw = m.group(2).strip()
                    norm_opt = normalize_label(opt_raw)
                    if not norm_opt:
                        continue
                    if self._is_option_selected(norm_opt, flat, context_label):
                        checked_box = "[X]" if "[" in box else ("(X)" if "(" in box else "☒")
                        replacements.append((m.start(1), m.end(1), checked_box))

            if replacements:
                replacements.sort(key=lambda item: item[0], reverse=True)
                for s_idx, e_idx, cb_char in replacements:
                    _replace_slice_in_paragraph_runs(p, s_idx, e_idx, cb_char)

    def _auto_map_inline_paragraphs(self, flat: dict[str, Any]) -> None:
        """Substitutes label-dot patterns and {{placeholders}} across all paragraphs."""
        paragraphs = list(self._doc.paragraphs)
        for table in self._doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    paragraphs.extend(cell.paragraphs)

        label_dot_re = re.compile(r"([0-9A-Za-zÀ-ỹ\s\/\(\)\-\.]+?)\s*[:：]?\s*([\.…_–—\-]{2,})")
        placeholder_re = re.compile(r"\{\{?\s*([0-9A-Za-zÀ-ỹ_\-]+)\s*\}\}?")

        for p in paragraphs:
            text = p.text
            if not text:
                continue

            replacements: list[tuple[int, int, str]] = []

            for m in label_dot_re.finditer(text):
                raw_label = m.group(1).strip()
                found, val, _ = resolve_field_value(raw_label, flat)
                if found and not isinstance(val, (list, dict)):
                    prefix_str = text[: m.start(2)]
                    rep_text = str(val) if prefix_str.endswith(" ") else f" {val}"
                    replacements.append((m.start(2), m.end(2), rep_text))

            for m in placeholder_re.finditer(text):
                var_name = m.group(1)
                found, val, _ = resolve_field_value(var_name, flat)
                if found and not isinstance(val, (list, dict)):
                    replacements.append((m.start(0), m.end(0), str(val)))

            if replacements:
                replacements.sort(key=lambda item: item[0], reverse=True)
                for start_idx, end_idx, rep_text in replacements:
                    _replace_slice_in_paragraph_runs(p, start_idx, end_idx, rep_text)

    def apply_paragraphs(self, mapping: dict[str, str]) -> None:
        """Substitutes placeholders across all body paragraphs and table cell paragraphs."""
        if not mapping or self._doc is None:
            return

        # 1. Process main document paragraphs
        for p in self._doc.paragraphs:
            self._substitute_in_paragraph(p, mapping)

        # 2. Process paragraphs inside all tables
        for table in self._doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        self._substitute_in_paragraph(p, mapping)

    def _substitute_in_paragraph(self, p: Any, mapping: dict[str, str]) -> None:
        """Smart substitution preserving font properties from the first matched run."""
        text = p.text
        needs_replace = False
        for key in mapping:
            if key in text:
                needs_replace = True
                break

        if not needs_replace:
            return

        new_text = text
        for key, val in mapping.items():
            if key in new_text:
                new_text = new_text.replace(key, str(val))

        if self.config.keep_font_formatting and p.runs:
            # Capture formatting of primary run
            primary_run = p.runs[0]
            font_name = primary_run.font.name
            font_size = primary_run.font.size
            is_bold = primary_run.bold
            is_italic = primary_run.italic

            p.text = new_text
            if p.runs:
                r = p.runs[0]
                if font_name:
                    r.font.name = font_name
                if font_size:
                    r.font.size = font_size
                if is_bold is not None:
                    r.bold = is_bold
                if is_italic is not None:
                    r.italic = is_italic
        else:
            p.text = new_text

    def apply_tables(self, table_rules: list[TableRule]) -> None:
        """Populates tabular data according to TableRule specifications."""
        if not table_rules or self._doc is None:
            return

        for rule in table_rules:
            table = self._resolve_table(rule)
            if table is None:
                logger.warning(
                    f"⚠️ Target table not found for rule: index={rule.table_index}, keyword='{rule.header_keyword}'"
                )
                continue

            # Populate data rows if provided
            if rule.data_rows and len(table.rows) >= 2:
                self._populate_table_rows(table, rule)

            # Apply layout guard for table rows
            prevent_split = self.config.prevent_row_split or not rule.allow_break_across_pages
            if prevent_split:
                for row in table.rows:
                    FormLayoutGuard.apply_docx_cant_split(row)

            # Delete remaining empty template rows if requested
            if rule.delete_unused_template_rows or self.config.prune_empty_rows:
                # Iterate in reverse to avoid index invalidation
                for i in range(len(table.rows) - 1, 0, -1):
                    row = table.rows[i]
                    if FormLayoutGuard.is_docx_row_empty(row):
                        FormLayoutGuard.remove_docx_row(table, row)

    def _resolve_table(self, rule: TableRule) -> Any | None:
        """Finds target table by index or keyword search."""
        if not self._doc.tables:
            return None

        if rule.header_keyword:
            kw = rule.header_keyword.lower()
            for table in self._doc.tables:
                if len(table.rows) > 0 and kw in table.rows[0].text.lower():
                    return table

        if rule.table_index < len(self._doc.tables):
            return self._doc.tables[rule.table_index]

        return None

    def _populate_table_rows(self, table: Any, rule: TableRule) -> None:
        """Duplicates template row and fills values for each data item."""
        if len(table.rows) < 2:
            return

        template_row = table.rows[1]
        headers = [c.text.strip() for c in table.rows[0].cells]

        for item_idx, data_row in enumerate(rule.data_rows):
            if item_idx == 0:
                # Use existing template row for the first item
                current_row = template_row
            else:
                # Clone template row XML element
                new_tr = copy.deepcopy(template_row._tr)
                table._tbl.append(new_tr)
                # python-docx wraps rows dynamically
                current_row = table.rows[-1]

            # Fill cell values
            for col_idx, cell in enumerate(current_row.cells):
                col_name = headers[col_idx] if col_idx < len(headers) else str(col_idx)
                val = None

                if rule.column_mapping and col_name in rule.column_mapping:
                    dict_key = rule.column_mapping[col_name]
                    val = data_row.get(dict_key)
                elif col_name in data_row:
                    val = data_row[col_name]
                elif str(col_idx) in data_row:
                    val = data_row[str(col_idx)]

                if val is not None:
                    cell.text = str(val)

    def apply_layout_guard(self) -> None:
        """Applies global layout guards across the document."""
        if self._doc is None:
            return

        # 1. Enforce PageBreakBefore for keyword-matching paragraphs
        if self.config.page_break_keywords:
            for p in self._doc.paragraphs:
                p_text_lower = p.text.lower()
                for kw in self.config.page_break_keywords:
                    if kw.lower() in p_text_lower:
                        FormLayoutGuard.apply_docx_page_break_before(p)
                        break

        # 2. Prevent row split across all tables
        if self.config.prevent_row_split:
            for table in self._doc.tables:
                for row in table.rows:
                    FormLayoutGuard.apply_docx_cant_split(row)

    def export(
        self,
        doc_out: Path | str | None = None,
        pdf_out: Path | str | None = None,
    ) -> dict[str, Path]:
        """Saves output document and converts to requested formats."""
        if self._doc is None or self._working_docx_path is None:
            raise FormFillerError("Document not initialized.")

        if doc_out:
            self.validate_output_path(doc_out)
        if pdf_out:
            self.validate_output_path(pdf_out)

        # Ensure global layout guard is applied
        self.apply_layout_guard()

        # Save current working document
        self._doc.save(str(self._working_docx_path))

        outputs: dict[str, Path] = {}

        if doc_out:
            doc_path = Path(doc_out).resolve()
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            ext = doc_path.suffix.lower()

            if ext == ".docx":
                shutil.copy2(self._working_docx_path, doc_path)
                outputs["doc"] = doc_path
            elif ext == ".doc":
                soffice_bin = find_soffice_bin()
                if not soffice_bin:
                    raise EngineUnavailableError(
                        "Exporting to binary .doc requires LibreOffice (soffice)."
                    )

                run_soffice(
                    [
                        "--headless",
                        "--convert-to",
                        "doc",
                        str(self._working_docx_path),
                        "--outdir",
                        str(doc_path.parent),
                    ],
                    timeout=self.config.timeout_seconds,
                )
                # soffice outputs file with same stem
                converted = doc_path.parent / f"{self._working_docx_path.stem}.doc"
                if converted.exists() and converted != doc_path:
                    shutil.move(str(converted), str(doc_path))
                outputs["doc"] = doc_path
            else:
                shutil.copy2(self._working_docx_path, doc_path)
                outputs["doc"] = doc_path

        if pdf_out:
            pdf_path = Path(pdf_out).resolve()
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            soffice_bin = find_soffice_bin()
            if not soffice_bin:
                raise EngineUnavailableError("Exporting to .pdf requires LibreOffice (soffice).")

            run_soffice(
                [
                    "--headless",
                    "--convert-to",
                    "pdf",
                    str(self._working_docx_path),
                    "--outdir",
                    str(pdf_path.parent),
                ],
                timeout=self.config.timeout_seconds,
            )
            converted_pdf = pdf_path.parent / f"{self._working_docx_path.stem}.pdf"
            if converted_pdf.exists() and converted_pdf != pdf_path:
                shutil.move(str(converted_pdf), str(pdf_path))
            outputs["pdf"] = pdf_path

        return outputs

    def close(self) -> None:
        """Removes temporary working directory."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception as e:
                logger.debug(f"Failed to clean up temp dir {self._temp_dir}: {e}")
        self._doc = None
