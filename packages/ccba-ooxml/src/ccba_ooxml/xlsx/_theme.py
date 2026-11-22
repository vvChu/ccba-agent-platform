"""CCBA Brand Identity v3.4 Excel styling theme and RichText/geometry helpers."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Border, Color, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ._safety import sanitize_xlsx_value

__all__ = [
    "CCBAExcelTheme",
    "apply_outer_border",
    "argb",
    "bilingual_rich_text",
    "clean_text",
    "configure_a4_portrait",
    "estimate_row_height",
    "grid_border",
    "labeled_rich_text",
    "make_side",
    "set_column_widths",
    "solid_fill",
    "style_merged_range",
    "styled_cell",
    "theme_font",
    "write_row_cells",
]


@dataclass(frozen=True)
class CCBAExcelTheme:
    """Color palette, typography, and A4 Portrait column geometry for CCBA calc sheets."""

    font_name: str = "Segoe UI"
    dark_blue: str = "363883"
    ibst_red: str = "DA251C"
    bim_blue: str = "0093DD"
    input_blue: str = "005A9C"
    white: str = "FFFFFF"
    text_dark: str = "1A202C"
    text_muted: str = "595959"
    subtitle_light: str = "E2E8F0"
    meta_fill: str = "F8FAFC"
    input_fill: str = "F0F6FC"
    section_fill: str = "E8EAF6"
    sub_banner_fill: str = "F1F5F9"
    subtotal_fill: str = "EBF5FB"
    key_result_fill: str = "E6F4FA"
    grand_total_fill: str = "FEF9E7"
    zebra_alt: str = "F9FAFB"
    border_light: str = "CBD5E1"
    col_widths_calc: tuple[int, ...] = (6, 44, 21, 11, 9, 25)
    col_widths_ref: tuple[int, ...] = (15, 36, 13, 52)


def argb(hex_rgb: str) -> str:
    """Normalize a 6-character hex RGB color string into 8-character ARGB."""
    clean = hex_rgb.lstrip("#").upper()
    return f"FF{clean}" if len(clean) == 6 else clean


def solid_fill(hex_rgb: str) -> PatternFill:
    """Create a solid ``PatternFill`` from a hex color string."""
    clean = hex_rgb.lstrip("#").upper()
    return PatternFill(start_color=clean, end_color=clean, fill_type="solid")


def make_side(style: str | None = "thin", color: str = "CBD5E1") -> Side:
    """Create a worksheet cell border ``Side`` helper."""
    return Side(style=style, color=color) if style else Side(style=None)


def grid_border(color: str = "CBD5E1") -> Border:
    """Create a uniform thin border around all four cell edges."""
    edge = make_side("thin", color)
    return Border(left=edge, right=edge, top=edge, bottom=edge)


def theme_font(
    theme: CCBAExcelTheme,
    size: float = 9.0,
    *,
    bold: bool = False,
    italic: bool = False,
    color: str | None = None,
) -> Font:
    """Create an openpyxl ``Font`` configured with the theme font family."""
    return Font(
        name=theme.font_name,
        size=size,
        bold=bold,
        italic=italic,
        color=color or theme.text_dark,
    )


def clean_text(val: Any) -> Any:
    """Sanitize scalar cell values with RULE-5.13 formula-injection protection."""
    return sanitize_xlsx_value(val, allow_formulas=False)


def _clean_rich(val: object) -> str:
    """Strip illegal XML control characters while preserving math symbols in RichText."""
    return str(sanitize_xlsx_value(val, allow_formulas=True))


def bilingual_rich_text(
    vi: str,
    en: str,
    *,
    font_name: str = "Segoe UI",
    vi_bold: bool = False,
    vi_size: float = 9.5,
    en_size: float = 8.5,
    vi_color: str = "1A202C",
    en_color: str = "595959",
) -> CellRichText:
    """Build stacked bilingual ``CellRichText`` (Vietnamese line over italic English)."""
    vi_f = InlineFont(rFont=font_name, sz=vi_size, b=vi_bold, color=Color(rgb=argb(vi_color)))
    en_f = InlineFont(rFont=font_name, sz=en_size, i=True, color=Color(rgb=argb(en_color)))
    return CellRichText(
        TextBlock(vi_f, f"{_clean_rich(vi)}\n"),
        TextBlock(en_f, _clean_rich(en)),
    )


def labeled_rich_text(
    label: str,
    value: str,
    *,
    font_name: str = "Segoe UI",
    label_color: str = "363883",
    value_color: str = "1A202C",
) -> CellRichText:
    """Build inline bold-label + regular-value ``CellRichText`` for metadata blocks."""
    lbl_f = InlineFont(rFont=font_name, sz=8.5, b=True, color=Color(rgb=argb(label_color)))
    val_f = InlineFont(rFont=font_name, sz=8.5, color=Color(rgb=argb(value_color)))
    return CellRichText(
        TextBlock(lbl_f, f"{_clean_rich(label)} "),
        TextBlock(val_f, _clean_rich(value)),
    )


def estimate_row_height(
    segments: Sequence[tuple[str, float, float]],
    min_height: float = 24.0,
) -> float:
    """Estimate safe row height in points to prevent wrapped-text clipping."""
    max_pts = min_height
    for text, col_width, font_pt in segments:
        if not text:
            continue
        usable_chars = max(8.0, (col_width - 2.0) * (10.0 / font_pt) * 0.96)
        lines = sum(max(1, math.ceil(len(p) / usable_chars)) for p in (text.splitlines() or [""]))
        needed = lines * (font_pt * 1.28) + 6.0
        max_pts = max(max_pts, needed)
    return round(max_pts, 1)


def apply_outer_border(
    ws: Worksheet,
    min_col: int,
    min_row: int,
    max_col: int,
    max_row: int,
    color: str = "363883",
    style: str = "medium",
) -> None:
    """Apply an outer perimeter border around a rectangular worksheet range."""
    edge = make_side(style, color)
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            cur = ws.cell(r, c).border
            ws.cell(r, c).border = Border(
                left=edge if c == min_col else cur.left,
                right=edge if c == max_col else cur.right,
                top=edge if r == min_row else cur.top,
                bottom=edge if r == max_row else cur.bottom,
            )


def style_merged_range(
    ws: Worksheet,
    min_col: int,
    min_row: int,
    max_col: int,
    max_row: int,
    fill: PatternFill | None = None,
    border: Border | None = None,
    alignment: Alignment | None = None,
) -> None:
    """Merge a cell rectangle and apply consistent fill, border, and alignment."""
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            cell = ws.cell(r, c)
            if fill is not None:
                cell.fill = fill
            if border is not None:
                cell.border = border
            if alignment is not None:
                cell.alignment = alignment
    if min_col != max_col or min_row != max_row:
        ws.merge_cells(start_row=min_row, start_column=min_col, end_row=max_row, end_column=max_col)


def styled_cell(
    ws: Worksheet,
    row: int,
    col: int,
    value: Any,
    *,
    font: Font | None = None,
    fill_hex: str | None = None,
    border: Border | None = None,
    horiz: str = "left",
    num_fmt: str | None = None,
) -> None:
    """Write a cell value and apply font, fill, border, alignment, and format."""
    cell = ws.cell(row, col, value)
    if font is not None:
        cell.font = font
    if fill_hex is not None:
        cell.fill = solid_fill(fill_hex)
    if border is not None:
        cell.border = border
    cell.alignment = Alignment(horizontal=horiz, vertical="center", wrap_text=True)
    if num_fmt is not None:
        cell.number_format = num_fmt


def write_row_cells(
    ws: Worksheet,
    row: int,
    specs: Sequence[tuple[Any, Font | None, str | None, str, str | None]],
    border: Border,
) -> None:
    """Populate a row of cells from ``(value, font, fill_hex, horiz, num_fmt)`` tuples."""
    for col, (val, font, fill_hex, horiz, num_fmt) in enumerate(specs, start=1):
        styled_cell(
            ws,
            row,
            col,
            val,
            font=font,
            fill_hex=fill_hex,
            border=border,
            horiz=horiz,
            num_fmt=num_fmt,
        )


def set_column_widths(ws: Worksheet, widths: Sequence[int]) -> None:
    """Apply worksheet column widths starting from column A."""
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width


def configure_a4_portrait(
    ws: Worksheet,
    theme: CCBAExcelTheme,
    doc: Mapping[str, Any],
    *,
    repeat_rows: str | None = None,
    fit_to_height: int = 0,
) -> None:
    """Apply standardized A4 Portrait print contract and footer metadata."""
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = fit_to_height
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins.left, ws.page_margins.right = 0.45, 0.45
    ws.page_margins.top, ws.page_margins.bottom = 0.36, 0.42
    ws.page_margins.header, ws.page_margins.footer = 0.18, 0.22
    ws.print_options.horizontalCentered = True
    ws.print_options.gridLines = False
    ws.views.sheetView[0].showGridLines = True
    if repeat_rows:
        ws.print_title_rows = repeat_rows
    fn = theme.font_name
    ws.oddFooter.left.text = f'&"{fn},Regular"&8{doc["doc_no"]} ({doc["revision"]})'
    ws.oddFooter.center.text = (
        f'&"{fn},Italic"&8{doc["consultant"]} — Standard Engineering Calculation'
    )
    ws.oddFooter.right.text = f'&"{fn},Regular"&8Page &P / &N'
