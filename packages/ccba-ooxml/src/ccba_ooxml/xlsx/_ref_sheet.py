"""Renderer for the ``02-References`` worksheet of CCBA calculation workbooks."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from openpyxl.styles import Alignment
from openpyxl.workbook import Workbook
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.worksheet import Worksheet

from ._calc_chrome import add_brand_footer, add_ccba_header, add_section_banner, add_table_headers
from ._theme import (
    CCBAExcelTheme,
    apply_outer_border,
    bilingual_rich_text,
    clean_text,
    configure_a4_portrait,
    estimate_row_height,
    grid_border,
    set_column_widths,
    solid_fill,
    style_merged_range,
    styled_cell,
    theme_font,
    write_row_cells,
)

__all__ = ["render_references_sheet"]


def _rt(t: CCBAExcelTheme, vi: Any, en: Any) -> Any:
    return bilingual_rich_text(
        str(vi or ""),
        str(en or ""),
        font_name=t.font_name,
        vi_size=8.5,
        en_size=8.0,
        vi_color=t.text_dark,
        en_color=t.text_muted,
    )


def _write_one_standard_row(
    ws: Worksheet,
    r: int,
    t: CCBAExcelTheme,
    item: Mapping[str, Any],
    def_vi: str,
    def_en: str,
    border: Any,
) -> None:
    s_vi, s_en = str(item.get("scope_vi") or def_vi), str(item.get("scope_en") or def_en)
    scope_v: Any = clean_text(s_vi) if s_vi == s_en else _rt(t, s_vi, s_en)
    specs = [
        (
            clean_text(item["code"]),
            theme_font(t, 9.0, bold=True, color=t.dark_blue),
            None,
            "center",
            None,
        ),
        (_rt(t, item["title_vi"], item["title_en"]), None, None, "left", None),
        (scope_v, theme_font(t, 8.5), None, "center", None),
        (_rt(t, item["clauses_vi"], item["clauses_en"]), None, None, "left", None),
    ]
    write_row_cells(ws, r, specs, border)
    segs = [
        (f"{item['title_vi']}\n{item['title_en']}", float(t.col_widths_ref[1]), 8.5),
        (f"{item['clauses_vi']}\n{item['clauses_en']}", float(t.col_widths_ref[3]), 8.5),
    ]
    ws.row_dimensions[r].height = estimate_row_height(segs, min_height=34.0) + 6.0


def _write_standards_table(
    ws: Worksheet,
    t: CCBAExcelTheme,
    standards: list[dict[str, Any]],
    doc: Mapping[str, Any],
    start_row: int,
) -> int:
    """Populate Applicable Codes & Standards table on ``02-References``."""
    r = add_section_banner(
        ws, t, start_row, "1. QUY CHUẨN & TIÊU CHUẨN ÁP DỤNG", "1. APPLICABLE CODES & STANDARDS", 4
    )
    hdrs = [
        ("Mã hiệu", "Code"),
        ("Tên tiêu chuẩn / quy chuẩn", "Standard Title"),
        ("Lĩnh vực", "Scope"),
        ("Điều khoản & Phạm vi áp dụng", "Cited Clauses & Application"),
    ]
    r = add_table_headers(ws, t, r, hdrs)
    border = grid_border(t.border_light)
    def_vi = str(doc.get("discipline_vi") or "Kỹ thuật")
    def_en = str(doc.get("discipline_en") or "Engineering")
    for item in standards:
        _write_one_standard_row(ws, r, t, item, def_vi, def_en, border)
        r += 1
    apply_outer_border(ws, 1, start_row + 1, 4, r - 1, t.dark_blue, "thin")
    ws.row_dimensions[r].height = 6.0
    return r + 1


def _write_one_glossary_row(
    ws: Worksheet, r: int, t: CCBAExcelTheme, item: Mapping[str, Any], bg: str, border: Any
) -> None:
    specs = [
        (
            clean_text(item["symbol"]),
            theme_font(t, 9.0, bold=True, italic=True, color=t.dark_blue),
            bg,
            "center",
            None,
        ),
        (clean_text(item["meaning_vi"]), theme_font(t, 8.5), bg, "left", None),
        (clean_text(item["unit"]), theme_font(t, 8.5, bold=True), bg, "center", None),
        (
            clean_text(item["meaning_en"]),
            theme_font(t, 8.5, italic=True, color=t.text_muted),
            bg,
            "left",
            None,
        ),
    ]
    write_row_cells(ws, r, specs, border)
    segs = [
        (str(item["meaning_vi"]), float(t.col_widths_ref[1]), 8.5),
        (str(item["meaning_en"]), float(t.col_widths_ref[3]), 8.5),
    ]
    ws.row_dimensions[r].height = estimate_row_height(segs, min_height=20.0)


def _write_glossary_table(
    ws: Worksheet, t: CCBAExcelTheme, glossary: list[dict[str, Any]], start_row: int
) -> int:
    """Populate Symbol & Unit Glossary table on ``02-References``."""
    r = add_section_banner(
        ws, t, start_row, "2. CHÚ GIẢI KÝ HIỆU & ĐƠN VỊ", "2. SYMBOL & UNIT GLOSSARY", 4
    )
    hdrs = [
        ("Ký hiệu", "Symbol"),
        ("Ý nghĩa (Tiếng Việt)", "Description (Vietnamese)"),
        ("Đơn vị", "Unit"),
        ("Diễn giải (Tiếng Anh)", "Description (English)"),
    ]
    r = add_table_headers(ws, t, r, hdrs)
    border = grid_border(t.border_light)
    for idx, item in enumerate(glossary):
        _write_one_glossary_row(ws, r, t, item, t.zebra_alt if idx % 2 else t.white, border)
        r += 1
    apply_outer_border(ws, 1, start_row + 1, 4, r - 1, t.dark_blue, "thin")
    ws.row_dimensions[r].height = 6.0
    return r + 1


def _default_legend_rows(t: CCBAExcelTheme) -> list[tuple[str, str, str, str, str]]:
    return [
        (
            "Ô nhập liệu\n(Input)",
            t.input_fill,
            t.input_blue,
            "Số xanh trên nền xanh nhạt — Tham số đầu vào có thể thay đổi; công thức tự động cập nhật.",
            "Blue text on light blue fill — Editable input parameters; formulas update automatically.",
        ),
        (
            "Ô công thức\n(Formula)",
            t.subtotal_fill,
            t.dark_blue,
            "Số tính toán tự động bằng công thức Excel sống (Live Formula); không ghi đè giá trị cứng.",
            "Live Excel formula cells; do not overwrite with hardcoded values.",
        ),
        (
            "Kết quả chính\n(Total)",
            t.grand_total_fill,
            t.ibst_red,
            "Số đỏ đậm trên nền vàng nhạt — Thông số thiết kế tổng hợp cuối cùng.",
            "Bold red text on light gold fill — Final governing engineering design figures.",
        ),
    ]


def _write_legend_table(
    ws: Worksheet, t: CCBAExcelTheme, refs: Mapping[str, Any], start_row: int
) -> int:
    """Populate Workbook Conventions & Visual Color Legend table."""
    r = add_section_banner(
        ws, t, start_row, "3. QUY ƯỚC BẢNG TÍNH", "3. WORKBOOK CONVENTIONS & LEGEND", 4
    )
    border = grid_border(t.border_light)
    align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    for entry in refs.get("legend") or _default_legend_rows(t):
        lbl, bg, fg, vi_t, en_t = (
            (entry["label"], entry["fill"], entry["color"], entry["vi"], entry["en"])
            if isinstance(entry, Mapping)
            else entry
        )
        styled_cell(
            ws,
            r,
            1,
            clean_text(lbl),
            font=theme_font(t, 8.5, bold=True, color=str(fg)),
            fill_hex=str(bg),
            border=border,
            horiz="center",
        )
        style_merged_range(ws, 2, r, 4, r, solid_fill(t.white), border, align)
        ws.cell(r, 2, _rt(t, vi_t, en_t))
        ws.row_dimensions[r].height = 28.0
        r += 1
    apply_outer_border(ws, 1, start_row + 1, 4, r - 1, t.dark_blue, "thin")
    return r


def _write_technical_notes_table(
    ws: Worksheet, t: CCBAExcelTheme, notes: list[dict[str, Any]], start_row: int
) -> int:
    """Populate bilingual Technical Notes & Design Scope section on ``02-References``."""
    r = add_section_banner(
        ws,
        t,
        start_row,
        "4. GHI CHÚ KỸ THUẬT & PHẠM VI ÁP DỤNG",
        "4. TECHNICAL NOTES & DESIGN SCOPE",
        4,
    )
    border, align = (
        grid_border(t.border_light),
        Alignment(horizontal="left", vertical="center", wrap_text=True),
    )
    note_w = float(sum(t.col_widths_ref[1:]))
    for item in notes:
        styled_cell(
            ws,
            r,
            1,
            clean_text(item["code"]),
            font=theme_font(t, 9.0, bold=True, color=t.dark_blue),
            fill_hex=t.grand_total_fill,
            border=border,
            horiz="center",
        )
        style_merged_range(ws, 2, r, 4, r, solid_fill(t.white), border, align)
        ws.cell(r, 2, _rt(t, item["note_vi"], item["note_en"]))
        ws.row_dimensions[r].height = estimate_row_height(
            [(f"{item['note_vi']}\n{item['note_en']}", note_w, 8.5)], min_height=34.0
        )
        r += 1
    apply_outer_border(ws, 1, start_row + 1, 4, r - 1, t.dark_blue, "thin")
    return r


def render_references_sheet(
    wb: Workbook, spec: Mapping[str, Any], theme: CCBAExcelTheme, logo_path: Path | None
) -> None:
    """Create and populate the ``02-References`` worksheet."""
    ws = wb.create_sheet(title="02-References")
    set_column_widths(ws, theme.col_widths_ref)
    doc, org, refs = spec["document"], spec["organization"], spec["references"]
    notes = list(refs.get("technical_notes") or [])
    subtitle = (
        "DANH MỤC TIÊU CHUẨN ÁP DỤNG & CHÚ GIẢI KÝ HIỆU",
        "APPLICABLE CODES, STANDARDS & SYMBOL GLOSSARY",
    )
    r = add_ccba_header(ws, theme, org, doc, theme.col_widths_ref, 3, logo_path, subtitle)
    r = _write_standards_table(ws, theme, refs["standards"], doc, r)
    r = _write_glossary_table(ws, theme, refs["glossary"], r)
    if notes:
        ws.row_breaks.append(Break(id=r - 1))
    r = _write_legend_table(ws, theme, refs, r)
    if notes:
        ws.row_dimensions[r].height = 6.0
        r = _write_technical_notes_table(ws, theme, notes, r + 1)
    add_brand_footer(ws, theme, doc, r + 1, 4)
    configure_a4_portrait(
        ws, theme, doc, repeat_rows="1:5" if notes else None, fit_to_height=0 if notes else 1
    )
