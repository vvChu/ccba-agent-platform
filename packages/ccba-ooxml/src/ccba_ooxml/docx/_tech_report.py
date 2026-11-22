"""Section-agnostic CCBA Brand v3.4 Technical Evaluation Report DOCX builder."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Twips

from ._report_chrome import (
    configure_a4_section,
    render_cover_page,
    render_kpi_cards,
    render_running_header_footer,
    render_signoff_block,
)
from ._report_theme import (
    CCBADocxTheme,
    add_styled_run,
    configure_normal_style,
    normalize_col_widths,
    resolve_ccba_logo,
    sanitize_xml_text,
    set_cell_borders,
    set_cell_margins,
    set_cell_shading,
    set_cell_valign,
    set_row_cant_split,
    set_row_tbl_header,
    set_table_borders,
    set_table_fixed_grid,
)

__all__ = [
    "TechnicalReportBuilder",
    "build_tech_report_from_yaml",
    "load_report_spec",
]

_REQUIRED_SPEC_KEYS = ("document", "organization", "sections")
_ALIGN_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _validate_spec(spec: Mapping[str, Any], source_label: str = "spec") -> None:
    """Validate mandatory top-level report specification keys and sections list."""
    missing = [k for k in _REQUIRED_SPEC_KEYS if k not in spec]
    if missing:
        raise ValueError(f"Missing required report spec keys in {source_label}: {missing}")
    if not isinstance(spec["document"], Mapping) or not isinstance(spec["organization"], Mapping):
        raise ValueError(f"'document' and 'organization' must be mappings in {source_label}")
    sections = spec["sections"]
    if not isinstance(sections, Sequence) or isinstance(sections, (str, bytes)) or not sections:
        raise ValueError(f"'sections' must be a non-empty list in {source_label}")


def load_report_spec(config_path: str | Path) -> dict[str, Any]:
    """Load and validate a technical evaluation report YAML specification."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"YAML spec not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid YAML root structure in {path}")
    spec: dict[str, Any] = {str(k): v for k, v in raw.items()}
    _validate_spec(spec, str(path))
    return spec


class TechnicalReportBuilder:
    """Deterministic builder for section-agnostic CCBA Brand v3.4 DOCX reports."""

    def __init__(self, theme: CCBADocxTheme | None = None, logo_path: Path | None = None) -> None:
        """Initialize report builder with CCBA Brand v3.4 theme and optional logo override."""
        self.theme = theme or CCBADocxTheme()
        self.logo_path = logo_path if logo_path is not None else resolve_ccba_logo()

    def _callout_palette(self, tone: str) -> tuple[str, str]:
        t = self.theme
        return {
            "warn": ("B45309", t.callout_warn_fill),
            "warning": ("B45309", t.callout_warn_fill),
            "danger": (t.ibst_red, t.callout_danger_fill),
            "critical": (t.ibst_red, t.callout_danger_fill),
            "ok": ("15803D", t.callout_ok_fill),
            "success": ("15803D", t.callout_ok_fill),
            "recommendation": (t.dark_blue, t.callout_info_fill),
        }.get(tone.lower().strip(), (t.primary_ui_blue, t.callout_info_fill))

    def _render_paragraphs(self, doc: Any, paragraphs: Sequence[Any]) -> None:
        t = self.theme
        for item in paragraphs:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(5)
            if isinstance(item, Mapping):
                p.alignment = _ALIGN_MAP.get(
                    str(item.get("align", "left")).lower(), WD_ALIGN_PARAGRAPH.LEFT
                )
                add_styled_run(
                    p,
                    item.get("text", ""),
                    t,
                    size_pt=float(item.get("size_pt", 10.0)),
                    bold=bool(item.get("bold", False)),
                    italic=bool(item.get("italic", False)),
                    color=str(item["color"]) if item.get("color") else None,
                )
            else:
                add_styled_run(p, item, t, size_pt=10.0)

    def _render_bullets(self, doc: Any, bullets: Sequence[Any]) -> None:
        t = self.theme
        for item in bullets:
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent, pf.first_line_indent = Twips(360), Twips(-180)
            pf.space_after = Pt(3)
            add_styled_run(p, "•  ", t, size_pt=10.0, bold=True, color=t.primary_ui_blue)
            if isinstance(item, Mapping):
                if item.get("label"):
                    add_styled_run(
                        p, f"{item['label']}: ", t, size_pt=10.0, bold=True, color=t.text_dark
                    )
                add_styled_run(p, item.get("text", ""), t, size_pt=10.0, color=t.text_dark)
            else:
                add_styled_run(p, item, t, size_pt=10.0, color=t.text_dark)

    def _render_callouts(self, doc: Any, callouts: Sequence[Mapping[str, Any]]) -> None:
        t = self.theme
        for box in callouts:
            accent, fill = self._callout_palette(str(box.get("tone", "info")))
            tbl = doc.add_table(rows=1, cols=1)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_table_borders(tbl, none=True)
            set_table_fixed_grid(tbl, [t.content_width_dxa])
            set_row_cant_split(tbl.rows[0])
            cell = tbl.rows[0].cells[0]
            set_cell_shading(cell, fill)
            set_cell_margins(cell, top=100, bottom=100, left=160, right=140)
            set_cell_borders(
                cell,
                left=("single", 24, accent),
                top=("single", 4, t.border_light),
                bottom=("single", 4, t.border_light),
                right=("single", 4, t.border_light),
            )
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2 if box.get("body") or box.get("text") else 0)
            if box.get("title"):
                add_styled_run(p, box["title"], t, size_pt=9.5, bold=True, color=accent)
                p = cell.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
            add_styled_run(
                p, box.get("body") or box.get("text") or "", t, size_pt=9.5, color=t.text_dark
            )
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_before, spacer.paragraph_format.space_after = Pt(0), Pt(4)

    def _populate_table_row(
        self,
        row: Any,
        values: Sequence[Any],
        alignments: Sequence[str],
        *,
        is_header: bool,
        fill_hex: str,
    ) -> None:
        t = self.theme
        set_row_cant_split(row)
        if is_header:
            set_row_tbl_header(row)
        txt_col = t.white if is_header else t.text_dark
        for c_idx, cell in enumerate(row.cells):
            set_cell_shading(cell, fill_hex)
            set_cell_valign(cell, "center")
            set_cell_margins(cell, top=75, bottom=75, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            align_key = (
                "center"
                if is_header
                else (alignments[c_idx] if c_idx < len(alignments) else "left")
            )
            p.alignment = _ALIGN_MAP.get(align_key.lower(), WD_ALIGN_PARAGRAPH.LEFT)
            val = values[c_idx] if c_idx < len(values) else ""
            add_styled_run(p, val, t, size_pt=9.0, bold=is_header, color=txt_col)

    def _render_table(self, doc: Any, tbl_spec: Mapping[str, Any]) -> None:
        t = self.theme
        if tbl_spec.get("caption"):
            p_cap = doc.add_paragraph()
            p_cap.paragraph_format.space_before, p_cap.paragraph_format.space_after = Pt(6), Pt(3)
            p_cap.paragraph_format.keep_with_next = True
            add_styled_run(p_cap, tbl_spec["caption"], t, size_pt=9.5, bold=True, color=t.dark_blue)
        hdr_rows = list(tbl_spec.get("header_rows") or [])
        if not hdr_rows and tbl_spec.get("headers"):
            hdr_rows = [list(tbl_spec["headers"])]
        body_rows = list(tbl_spec.get("rows") or [])
        if not hdr_rows and not body_rows:
            return
        ncols = max((len(r) for r in [*hdr_rows, *body_rows]), default=1)
        widths = normalize_col_widths(ncols, tbl_spec.get("col_widths"), t.content_width_dxa)
        aligns = [str(a) for a in (tbl_spec.get("alignments") or [])]

        tbl = doc.add_table(rows=len(hdr_rows) + len(body_rows), cols=ncols)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(tbl, color=t.border_light, sz=4)
        set_table_fixed_grid(tbl, widths)
        for r_idx, row_vals in enumerate(hdr_rows):
            self._populate_table_row(
                tbl.rows[r_idx], row_vals, aligns, is_header=True, fill_hex=t.dark_blue
            )
        for b_idx, row_vals in enumerate(body_rows):
            fill = t.zebra_alt if b_idx % 2 == 1 else t.white
            self._populate_table_row(
                tbl.rows[len(hdr_rows) + b_idx], row_vals, aligns, is_header=False, fill_hex=fill
            )
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before, spacer.paragraph_format.space_after = Pt(0), Pt(4)

    def _render_block_group(self, doc: Any, container: Mapping[str, Any]) -> None:
        if container.get("kpis"):
            render_kpi_cards(doc, self.theme, container["kpis"])
        if container.get("paragraphs"):
            self._render_paragraphs(doc, container["paragraphs"])
        if container.get("bullets"):
            self._render_bullets(doc, container["bullets"])
        if container.get("callouts"):
            self._render_callouts(doc, container["callouts"])
        for tbl_spec in container.get("tables") or ():
            self._render_table(doc, tbl_spec)

    def _render_heading(self, doc: Any, title_vi: str, title_en: str | None, *, level: int) -> None:
        t = self.theme
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        color = t.dark_blue if level == 1 else t.primary_ui_blue
        add_styled_run(p, title_vi, t, size_pt=12.5 if level == 1 else 10.5, bold=True, color=color)
        if title_en:
            p_en = doc.add_paragraph()
            p_en.paragraph_format.space_after = Pt(4)
            p_en.paragraph_format.keep_with_next = True
            add_styled_run(
                p_en,
                title_en,
                t,
                size_pt=9.0 if level == 1 else 8.5,
                italic=True,
                color=t.text_muted,
            )

    def _render_section(self, doc: Any, sec: Mapping[str, Any]) -> None:
        code = sanitize_xml_text(sec.get("code") or "").strip()
        raw_vi = sanitize_xml_text(sec.get("title_vi") or sec.get("title") or "SECTION").strip()
        heading_vi = f"{code}. {raw_vi}" if code else raw_vi
        title_en = sanitize_xml_text(sec.get("title_en") or "").strip() or None
        self._render_heading(doc, heading_vi, title_en, level=1)
        self._render_block_group(doc, sec)
        for sub in sec.get("subsections") or ():
            sub_code = sanitize_xml_text(sub.get("code") or "").strip()
            sub_vi = sanitize_xml_text(sub.get("title_vi") or sub.get("title") or "").strip()
            sub_heading = f"{sub_code} {sub_vi}".strip() if sub_code else sub_vi
            sub_en = sanitize_xml_text(sub.get("title_en") or "").strip() or None
            if sub_heading:
                self._render_heading(doc, sub_heading, sub_en, level=2)
            self._render_block_group(doc, sub)

    def build_document(self, spec: Mapping[str, Any]) -> Any:
        """Construct an in-memory ``python-docx`` Document from a report specification."""
        _validate_spec(spec)
        doc = Document()
        configure_normal_style(doc, self.theme)
        section = configure_a4_section(doc, self.theme)
        render_cover_page(doc, self.theme, spec["organization"], spec["document"], self.logo_path)
        render_running_header_footer(section, self.theme, spec["document"])
        if spec.get("kpis"):
            render_kpi_cards(doc, self.theme, spec["kpis"])
        for sec in spec["sections"]:
            self._render_section(doc, sec)
        if spec.get("signoff"):
            render_signoff_block(doc, self.theme, spec["signoff"])
        return doc

    def build(self, spec: Mapping[str, Any], output_docx: str | Path) -> Path:
        """Build a DOCX report from ``spec`` mapping and save it to ``output_docx``."""
        out_path = Path(output_docx).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc = self.build_document(spec)
        doc.save(str(out_path))
        return out_path

    def build_from_yaml(
        self,
        config_path: str | Path,
        output_docx: str | Path,
        *,
        export_pdf: str | Path | None = None,
    ) -> dict[str, Any]:
        """Build a DOCX report from YAML IR and optionally export a Vector PDF preview."""
        spec = load_report_spec(config_path)
        out_path = self.build(spec, output_docx)
        summary: dict[str, Any] = {
            "docx_path": str(out_path),
            "section_count": len(spec["sections"]),
            "success": True,
        }
        if export_pdf is not None:
            from ccba_ooxml.converter import docx_to_pdf
            from ccba_ooxml.form_filler.exceptions import EngineUnavailableError, FormFillerError

            try:
                pdf_out = docx_to_pdf(out_path, export_pdf)
                summary["pdf_path"] = str(pdf_out)
            except (EngineUnavailableError, FormFillerError, OSError) as exc:
                summary["success"] = False
                summary["error"] = str(exc)
        return summary


def build_tech_report_from_yaml(
    config_path: str | Path,
    output_docx: str | Path,
    *,
    export_pdf: str | Path | None = None,
    theme: CCBADocxTheme | None = None,
    logo_path: Path | None = None,
) -> dict[str, Any]:
    """Convenience entrypoint to generate a CCBA Brand v3.4 DOCX technical report from YAML."""
    builder = TechnicalReportBuilder(theme=theme, logo_path=logo_path)
    return builder.build_from_yaml(config_path, output_docx, export_pdf=export_pdf)
