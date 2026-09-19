# packages/ccba-ooxml/src/ccba_ooxml/form_filler/fallback_engine.py
"""Headless cross-platform Form Filler Engine using LibreOffice and python-docx."""

from __future__ import annotations

import copy
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ..soffice import find_soffice_bin, run_soffice
from .base import BaseFormFillerEngine
from .exceptions import EngineUnavailableError, FormFillerError, TemplateNotFoundError
from .layout_guard import FormLayoutGuard
from .models import FormFillConfig, TableRule

logger = logging.getLogger("ccba.ooxml.form_filler.fallback")


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
