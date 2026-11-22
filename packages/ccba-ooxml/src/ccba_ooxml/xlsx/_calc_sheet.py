"""Bilingual CCBA engineering calculation sheet builder complying with RULE-6.1 & Brand v3.4."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import openpyxl
import yaml
from openpyxl.workbook import Workbook
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.worksheet import Worksheet

from ._calc_chrome import (
    add_ccba_header,
    add_project_matrix,
    add_section_banner,
    add_signoff_and_footer,
    add_summary_kpis,
    add_table_headers,
)
from ._ref_sheet import render_references_sheet
from ._safety import verify_xlsx_zip_safety
from ._theme import (
    CCBAExcelTheme,
    apply_outer_border,
    bilingual_rich_text,
    clean_text,
    configure_a4_portrait,
    estimate_row_height,
    grid_border,
    make_side,
    set_column_widths,
    solid_fill,
    style_merged_range,
    theme_font,
    write_row_cells,
)

__all__ = [
    "CalculationSheetBuilder",
    "build_calc_sheet_from_yaml",
    "extract_item_no",
    "load_calc_spec",
    "resolve_ccba_logo",
    "resolve_formula",
]

_REQUIRED_SPEC_KEYS = (
    "document",
    "organization",
    "inputs",
    "sections",
    "summary_kpis",
    "signoff",
    "references",
)
_FORMULA_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_]+)\}")


def resolve_ccba_logo() -> Path | None:
    """Resolve official bundled CCBA logo path without hardcoded machine paths."""
    candidate = (
        Path(__file__).resolve().parent.parent / "templates" / "assets" / "logo_ccba_full.png"
    )
    return candidate if candidate.is_file() else None


def load_calc_spec(config_path: str | Path) -> dict[str, Any]:
    """Load and validate a bilingual calculation sheet YAML specification."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"YAML spec not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML root structure in {path}")
    missing = [k for k in _REQUIRED_SPEC_KEYS if k not in data]
    if missing:
        raise ValueError(f"Missing required calculation spec keys in {path}: {missing}")
    return data


def extract_item_no(item: Mapping[Any, Any]) -> str:
    """Safely extract row item number even if YAML 1.1 parsed ``no:`` as ``False``."""
    raw = item.get("item_no")
    if raw is None:
        raw = item.get("no")
    if raw is None:
        raw = item.get(False)
    return str(clean_text("" if raw is None else raw))


def resolve_formula(template: str, cell_map: Mapping[str, str]) -> str:
    """Resolve symbolic ``{key}`` placeholders into concrete Excel cell coordinates."""

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in cell_map:
            raise ValueError(f"Unknown formula reference key: '{key}'")
        return cell_map[key]

    return _FORMULA_PLACEHOLDER_RE.sub(_sub, template)


class CalculationSheetBuilder:
    """Deterministic builder for CCBA bilingual A4 Portrait Excel calculation sheets."""

    def __init__(self, theme: CCBAExcelTheme | None = None, logo_path: Path | None = None) -> None:
        """Initialize builder with CCBA Brand v3.4 styling theme and optional logo override."""
        self.theme = theme or CCBAExcelTheme()
        self.logo_path = logo_path if logo_path is not None else resolve_ccba_logo()

    def _unit_or_ref(self, vi: Any, en: Any) -> Any:
        vi_s, en_s = str(vi or ""), str(en or "")
        if not en_s or vi_s == en_s:
            return clean_text(vi_s)
        t = self.theme
        return bilingual_rich_text(
            vi_s,
            en_s,
            font_name=t.font_name,
            vi_size=8.5,
            en_size=8.0,
            vi_color=t.text_dark,
            en_color=t.text_muted,
        )

    def _input_row_specs(
        self, item: Mapping[str, Any]
    ) -> list[tuple[Any, Any, str | None, str, str | None]]:
        t = self.theme
        desc = bilingual_rich_text(
            str(item["desc_vi"]),
            str(item["desc_en"]),
            font_name=t.font_name,
            vi_color=t.text_dark,
            en_color=t.text_muted,
        )
        u_cell = self._unit_or_ref(item["unit_vi"], item["unit_en"])
        r_cell = self._unit_or_ref(item["ref_vi"], item["ref_en"])
        return [
            (
                extract_item_no(item),
                theme_font(t, 8.5, bold=True, color=t.text_muted),
                t.white,
                "center",
                None,
            ),
            (desc, None, t.white, "left", None),
            (
                clean_text(item["symbol"]),
                theme_font(t, 9.5, bold=True, italic=True, color=t.dark_blue),
                t.white,
                "center",
                None,
            ),
            (
                clean_text(item["value"]),
                theme_font(t, 10.0, bold=True, color=t.input_blue),
                t.input_fill,
                "right",
                str(item.get("num_fmt", "#,##0.00")),
            ),
            (u_cell, theme_font(t, 9.0), t.white, "center", None),
            (r_cell, theme_font(t, 8.5), t.white, "left", None),
        ]

    def _write_input_row(self, ws: Worksheet, r: int, item: Mapping[str, Any]) -> None:
        t = self.theme
        write_row_cells(ws, r, self._input_row_specs(item), grid_border(t.border_light))
        segs = [
            (f"{item['desc_vi']}\n{item['desc_en']}", float(t.col_widths_calc[1]), 9.2),
            (f"{item['ref_vi']}\n{item['ref_en']}", float(t.col_widths_calc[5]), 8.5),
        ]
        ws.row_dimensions[r].height = estimate_row_height(segs, min_height=29.0)

    def _add_inputs_section(
        self, ws: Worksheet, inputs: list[dict[str, Any]], start_row: int, cell_map: dict[str, str]
    ) -> int:
        t = self.theme
        r = add_section_banner(
            ws, t, start_row, "A. THÔNG SỐ THIẾT KẾ ĐẦU VÀO", "A. DESIGN INPUT PARAMETERS"
        )
        r = add_table_headers(
            ws,
            t,
            r,
            [
                ("TT", "No."),
                ("Thông số & Diễn giải", "Parameter & Description"),
                ("Ký hiệu", "Symbol"),
                ("Giá trị", "Value"),
                ("Đơn vị", "Unit"),
                ("Căn cứ", "Reference"),
            ],
        )
        for item in inputs:
            cell_map[str(item["id"])] = f"D{r}"
            self._write_input_row(ws, r, item)
            r += 1
        apply_outer_border(ws, 1, start_row + 1, 6, r - 1, t.dark_blue, "thin")
        ws.row_dimensions[r].height = 8.0
        return r + 1

    def _row_style_palette(self, style: str) -> tuple[str, str, bool]:
        t = self.theme
        return {
            "grand_total": (t.grand_total_fill, t.ibst_red, True),
            "key_result": (t.key_result_fill, t.dark_blue, True),
            "subtotal": (t.subtotal_fill, t.dark_blue, True),
            "note": (t.zebra_alt, t.text_muted, False),
        }.get(style, (t.white, t.text_dark, False))

    def _resolve_calc_val(
        self, r: int, row_spec: Mapping[str, Any], cell_map: dict[str, str], style: str
    ) -> tuple[Any, Any, str, str | None]:
        t = self.theme
        bg, fg, bold = self._row_style_palette(style)
        f_tpl = row_spec.get("formula")
        val_obj: Any = resolve_formula(str(f_tpl), cell_map) if f_tpl else "—"
        if row_spec.get("id"):
            cell_map[str(row_spec["id"])] = f"D{r}"
        v_sz = 10.5 if style == "grand_total" else 9.5
        v_fnt = theme_font(t, v_sz, bold=bold, color=fg if f_tpl else t.text_muted)
        n_fmt = str(row_spec.get("num_fmt", "#,##0.00")) if f_tpl else None
        return val_obj, v_fnt, ("right" if f_tpl else "center"), n_fmt

    def _calc_row_specs(
        self, r: int, row_spec: Mapping[str, Any], cell_map: dict[str, str], style: str
    ) -> list[tuple[Any, Any, str | None, str, str | None]]:
        t = self.theme
        bg, _fg, bold = self._row_style_palette(style)
        val_obj, v_fnt, v_align, n_fmt = self._resolve_calc_val(r, row_spec, cell_map, style)
        desc = bilingual_rich_text(
            str(row_spec["desc_vi"]),
            str(row_spec["desc_en"]),
            font_name=t.font_name,
            vi_bold=bold,
            vi_color=t.text_dark,
            en_color=t.text_muted,
        )
        u_cell = self._unit_or_ref(row_spec["unit_vi"], row_spec["unit_en"])
        r_cell = self._unit_or_ref(row_spec["ref_vi"], row_spec["ref_en"])
        f_disp = clean_text(row_spec.get("formula_display", ""))
        return [
            (
                extract_item_no(row_spec),
                theme_font(t, 9.0, bold=True, color=t.dark_blue),
                bg,
                "center",
                None,
            ),
            (desc, None, bg, "left", None),
            (f_disp, theme_font(t, 9.0, bold=bold, italic=True), bg, "center", None),
            (val_obj, v_fnt, bg, v_align, n_fmt),
            (u_cell, theme_font(t, 9.0, bold=bold), bg, "center", None),
            (r_cell, theme_font(t, 8.5), bg, "left", None),
        ]

    def _write_calc_row(
        self, ws: Worksheet, r: int, row_spec: Mapping[str, Any], cell_map: dict[str, str]
    ) -> None:
        t = self.theme
        style = str(row_spec.get("style", "calc"))
        s_l = make_side("thin", t.border_light)
        border = (
            solid_border(s_l, make_side("double", t.dark_blue), make_side("medium", t.dark_blue))
            if style == "grand_total"
            else grid_border(t.border_light)
        )
        write_row_cells(ws, r, self._calc_row_specs(r, row_spec, cell_map, style), border)
        segs = [
            (f"{row_spec['desc_vi']}\n{row_spec['desc_en']}", float(t.col_widths_calc[1]), 9.2),
            (str(row_spec.get("formula_display", "")), float(t.col_widths_calc[2]), 9.0),
            (f"{row_spec['ref_vi']}\n{row_spec['ref_en']}", float(t.col_widths_calc[5]), 8.5),
        ]
        ws.row_dimensions[r].height = estimate_row_height(segs, min_height=24.0)

    def _add_calculations_section(
        self,
        ws: Worksheet,
        sections: list[dict[str, Any]],
        start_row: int,
        cell_map: dict[str, str],
    ) -> tuple[int, int]:
        from openpyxl.styles import Alignment

        t = self.theme
        r = add_section_banner(
            ws, t, start_row, "B. BẢNG TÍNH TOÁN CHI TIẾT", "B. DETAILED CALCULATION"
        )
        r = add_table_headers(
            ws,
            t,
            r,
            [
                ("TT", "No."),
                ("Hạng mục & Diễn giải", "Item & Description"),
                ("Ký hiệu & Công thức", "Symbol & Formula"),
                ("Giá trị", "Value"),
                ("Đơn vị", "Unit"),
                ("Căn cứ", "Reference"),
            ],
        )
        table_start = r - 1
        align_l = Alignment(horizontal="left", vertical="center")
        for sec in sections:
            style_merged_range(
                ws, 1, r, 6, r, solid_fill(t.sub_banner_fill), grid_border(t.border_light), align_l
            )
            ws.cell(
                r, 1, clean_text(f"{sec['code']}. {sec['title_vi']} / {sec['title_en']}")
            ).font = theme_font(t, 9.5, bold=True, color=t.dark_blue)
            ws.row_dimensions[r].height = 24.0
            r += 1
            for row_spec in sec["rows"]:
                self._write_calc_row(ws, r, row_spec, cell_map)
                r += 1
        apply_outer_border(ws, 1, table_start, 6, r - 1, t.dark_blue, "thin")
        ws.row_dimensions[r].height = 5.0
        return r + 1, start_row

    def _build_calculation_sheet(self, wb: Workbook, spec: Mapping[str, Any]) -> dict[str, str]:
        t = self.theme
        ws = wb.active
        ws.title = "01-Calculation"
        set_column_widths(ws, t.col_widths_calc)
        doc, org = spec["document"], spec["organization"]
        cell_map: dict[str, str] = {}
        r = add_ccba_header(ws, t, org, doc, t.col_widths_calc, 4, self.logo_path)
        r = add_project_matrix(ws, t, doc, t.col_widths_calc, r)
        r = self._add_inputs_section(ws, spec["inputs"], r, cell_map)
        r, calc_start = self._add_calculations_section(ws, spec["sections"], r, cell_map)
        ws.row_breaks.append(Break(id=calc_start - 1))
        r = add_summary_kpis(ws, t, spec["summary_kpis"], cell_map, r)
        add_signoff_and_footer(ws, t, spec["signoff"], doc, r)
        configure_a4_portrait(ws, t, doc, repeat_rows="1:5", fit_to_height=0)
        return cell_map

    def build_workbook(self, spec: Mapping[str, Any]) -> tuple[Workbook, dict[str, str]]:
        """Construct an in-memory ``openpyxl.Workbook`` and return ``(workbook, cell_map)``."""
        wb = openpyxl.Workbook()
        cell_map = self._build_calculation_sheet(wb, spec)
        render_references_sheet(wb, spec, self.theme, self.logo_path)
        return wb, cell_map

    def build(self, spec: Mapping[str, Any], output_xlsx: str | Path) -> Path:
        """Build workbook from ``spec`` dict, save to ``output_xlsx``, and verify ZIP safety."""
        out_path = Path(output_xlsx).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        wb, _ = self.build_workbook(spec)
        try:
            wb.save(out_path)
        finally:
            wb.close()
        verify_xlsx_zip_safety(out_path)
        return out_path

    def build_from_yaml(
        self,
        config_path: str | Path,
        output_xlsx: str | Path,
        *,
        recalculate: bool = False,
        export_pdf: str | Path | None = None,
        check_errors: bool = False,
    ) -> dict[str, Any]:
        """Build calculation sheet from YAML IR and optionally recalculate, export PDF, or audit."""
        spec = load_calc_spec(config_path)
        out_path = self.build(spec, output_xlsx)
        summary: dict[str, Any] = {"xlsx_path": str(out_path), "success": True}
        if recalculate or export_pdf is not None:
            from ccba_ooxml.calc import recalc_xlsx

            summary.update(recalc_xlsx(out_path, export_pdf=export_pdf, check_errors=check_errors))
        elif check_errors:
            from ccba_ooxml.calc import audit_xlsx_formula_errors

            errs = audit_xlsx_formula_errors(out_path)
            summary["formula_errors"] = errs
            summary["formulas_evaluated"] = False
            if errs:
                summary["success"], summary["error"] = (
                    False,
                    f"Found {len(errs)} Excel formula error(s)",
                )
        return summary


def solid_border(side_lr: Any, top: Any, bottom: Any) -> Any:
    """Construct grand-total row border with double-top and medium-bottom emphasis."""
    from openpyxl.styles import Border

    return Border(left=side_lr, right=side_lr, top=top, bottom=bottom)


def build_calc_sheet_from_yaml(
    config_path: str | Path,
    output_xlsx: str | Path,
    *,
    recalculate: bool = False,
    export_pdf: str | Path | None = None,
    check_errors: bool = False,
    theme: CCBAExcelTheme | None = None,
    logo_path: Path | None = None,
) -> dict[str, Any]:
    """Convenience entrypoint to generate a CCBA bilingual calculation workbook from YAML."""
    builder = CalculationSheetBuilder(theme=theme, logo_path=logo_path)
    return builder.build_from_yaml(
        config_path,
        output_xlsx,
        recalculate=recalculate,
        export_pdf=export_pdf,
        check_errors=check_errors,
    )
