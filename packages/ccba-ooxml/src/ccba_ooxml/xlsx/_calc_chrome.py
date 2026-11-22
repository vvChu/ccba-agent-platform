"""Shared header, metadata matrix, KPI cards, sign-off, and footer renderers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.styles import Alignment, Border, Color
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.worksheet.worksheet import Worksheet

from ._safety import sanitize_xlsx_value
from ._theme import (
    CCBAExcelTheme,
    apply_outer_border,
    argb,
    bilingual_rich_text,
    clean_text,
    estimate_row_height,
    grid_border,
    labeled_rich_text,
    make_side,
    solid_fill,
    style_merged_range,
    styled_cell,
    theme_font,
)

__all__ = [
    "add_brand_footer",
    "add_ccba_header",
    "add_project_matrix",
    "add_section_banner",
    "add_signoff_and_footer",
    "add_summary_kpis",
    "add_table_headers",
    "embed_ccba_logo",
]


def _rt(
    t: CCBAExcelTheme,
    vi: Any,
    en: Any,
    *,
    bold: bool = False,
    vi_sz: float = 9.0,
    en_sz: float = 8.0,
    vi_col: str | None = None,
    en_col: str | None = None,
) -> CellRichText:
    return bilingual_rich_text(
        str(vi or ""),
        str(en or ""),
        font_name=t.font_name,
        vi_bold=bold,
        vi_size=vi_sz,
        en_size=en_sz,
        vi_color=vi_col or t.text_dark,
        en_color=en_col or t.text_muted,
    )


def _join_pair(vi: Any, en: Any, sep: str) -> str:
    vi_s, en_s = str(vi or "").strip(), str(en or "").strip()
    if not en_s or en_s == vi_s:
        return vi_s or "—"
    return f"{vi_s}{sep}{en_s}" if vi_s else en_s


def embed_ccba_logo(
    ws: Worksheet, logo_path: Path | None, logo_col_idx: int, col_widths: tuple[int, ...]
) -> None:
    """Embed right-aligned CCBA logo inside the upper-right header block."""
    if not logo_path or not logo_path.is_file():
        return
    img = XLImage(str(logo_path))
    w = 132
    ratio = (img.height / img.width) if (img.width and img.height) else (558 / 1024)
    h = round(w * ratio)
    img.width, img.height = w, h
    off_x = max(6, int(sum(col_widths[logo_col_idx:]) * 7.2 - w - 10))
    marker = AnchorMarker(
        col=logo_col_idx, colOff=pixels_to_EMU(off_x), row=0, rowOff=pixels_to_EMU(6)
    )
    size = XDRPositiveSize2D(cx=pixels_to_EMU(w), cy=pixels_to_EMU(h))
    ws.add_image(img, OneCellAnchor(_from=marker, ext=size))


def add_ccba_header(
    ws: Worksheet,
    t: CCBAExcelTheme,
    org: Mapping[str, Any],
    doc: Mapping[str, Any],
    col_widths: tuple[int, ...],
    logo_col_idx: int,
    logo_path: Path | None,
    subtitle: tuple[str, str] | None = None,
) -> int:
    """Render RULE-6.1 2-tier organization header, logo, and dark-navy title banner."""
    max_col = len(col_widths)
    tiers = [
        (org["parent_vi"], theme_font(t, 10.5, bold=True, color=t.dark_blue), 16.5),
        (org["parent_en"], theme_font(t, 8.5, italic=True, color=t.text_muted), 14.0),
        (org["unit_vi"], theme_font(t, 10.0, bold=True), 16.5),
        (org["unit_en"], theme_font(t, 8.5, italic=True, color=t.text_muted), 15.0),
    ]
    align_l = Alignment(horizontal="left", vertical="center")
    for idx, (txt, fnt, ht) in enumerate(tiers, start=1):
        ws.row_dimensions[idx].height = ht
        style_merged_range(ws, 1, idx, logo_col_idx, idx, solid_fill(t.white), alignment=align_l)
        ws.cell(idx, 1, clean_text(txt)).font = fnt

    style_merged_range(ws, logo_col_idx + 1, 1, max_col, 4, solid_fill(t.white))
    red_line = Border(bottom=make_side("medium", t.ibst_red))
    for c in range(1, max_col + 1):
        ws.cell(4, c).border = red_line
    embed_ccba_logo(ws, logo_path, logo_col_idx, col_widths)

    ws.row_dimensions[5].height = 6.0
    t_vi, t_en = subtitle or (doc["title_vi"], doc["title_en"])
    center_wrap = Alignment(horizontal="center", vertical="center", wrap_text=True)
    style_merged_range(ws, 1, 6, max_col, 6, solid_fill(t.dark_blue), alignment=center_wrap)
    ws.cell(
        6,
        1,
        _rt(
            t, t_vi, t_en, bold=True, vi_sz=11.0, en_sz=9.0, vi_col=t.white, en_col=t.subtitle_light
        ),
    )
    ws.row_dimensions[6].height, ws.row_dimensions[7].height = 38.0, 6.0
    return 8


def _matrix_pairs(doc: Mapping[str, Any]) -> list[tuple[tuple[str, str], tuple[str, str]]]:
    """Build left/right metadata label-value pairs for the Project Control Matrix."""
    disc = str(doc.get("discipline_en") or doc.get("discipline_vi") or "").strip()
    consultant = f"{doc['consultant']} — {disc}" if disc else str(doc["consultant"])
    return [
        (
            ("Dự án / Project:", _join_pair(doc.get("project_vi"), doc.get("project_en"), " — ")),
            ("Mã hồ sơ / Doc No.:", str(doc["doc_no"])),
        ),
        (
            ("Chủ đầu tư / Client:", _join_pair(doc.get("client_vi"), doc.get("client_en"), " / ")),
            ("Phiên bản / Revision:", str(doc["revision"])),
        ),
        (
            ("Quản lý dự án / PMC:", str(doc.get("pmc") or doc.get("package_vi") or "—")),
            ("Ngày lập / Date:", str(doc["date"])),
        ),
        (
            (
                "Địa điểm / Location:",
                _join_pair(doc.get("location_vi"), doc.get("location_en"), " / "),
            ),
            ("Tư vấn / Consultant:", consultant),
        ),
    ]


def add_project_matrix(
    ws: Worksheet,
    t: CCBAExcelTheme,
    doc: Mapping[str, Any],
    col_widths: tuple[int, ...],
    start_row: int,
) -> int:
    """Render bilingual 2-block Project Control Matrix across A:C and D:F."""
    border = grid_border(t.border_light)
    align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    lw, rw = float(sum(col_widths[0:3])), float(sum(col_widths[3:6]))
    for idx, ((ll, lv), (rl, rv)) in enumerate(_matrix_pairs(doc)):
        r = start_row + idx
        style_merged_range(ws, 1, r, 3, r, solid_fill(t.meta_fill), border, align)
        ws.cell(r, 1, labeled_rich_text(ll, lv, font_name=t.font_name, label_color=t.dark_blue))
        style_merged_range(ws, 4, r, 6, r, solid_fill(t.white), border, align)
        ws.cell(r, 4, labeled_rich_text(rl, rv, font_name=t.font_name, label_color=t.dark_blue))
        ws.row_dimensions[r].height = estimate_row_height(
            [(f"{ll} {lv}", lw, 8.5), (f"{rl} {rv}", rw, 8.5)], min_height=21.0
        )
    apply_outer_border(ws, 1, start_row, 6, start_row + 3, t.dark_blue, "thin")
    ws.row_dimensions[start_row + 4].height = 8.0
    return start_row + 5


def add_section_banner(
    ws: Worksheet, t: CCBAExcelTheme, row_idx: int, title_vi: str, title_en: str, max_col: int = 6
) -> int:
    """Render full-width section banner with left Brand v3.4 dark-blue accent border."""
    border = Border(
        top=make_side("thin", t.dark_blue),
        bottom=make_side("thin", t.dark_blue),
        left=make_side("medium", t.dark_blue),
        right=make_side("thin", t.dark_blue),
    )
    align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    style_merged_range(ws, 1, row_idx, max_col, row_idx, solid_fill(t.section_fill), border, align)
    ws.cell(
        row_idx, 1, _rt(t, title_vi, title_en, bold=True, vi_sz=9.5, en_sz=8.0, vi_col=t.dark_blue)
    )
    ws.row_dimensions[row_idx].height = 29.0
    return row_idx + 1


def add_table_headers(
    ws: Worksheet, t: CCBAExcelTheme, row_idx: int, headers: list[tuple[str, str]]
) -> int:
    """Render a bilingual dark-navy table header row."""
    border = grid_border(t.white)
    for c_idx, (vi, en) in enumerate(headers, start=1):
        rt = _rt(
            t, vi, en, bold=True, vi_sz=9.0, en_sz=8.0, vi_col=t.white, en_col=t.subtitle_light
        )
        styled_cell(ws, row_idx, c_idx, rt, fill_hex=t.dark_blue, border=border, horiz="center")
    ws.row_dimensions[row_idx].height = 31.0
    return row_idx + 1


def add_summary_kpis(
    ws: Worksheet,
    t: CCBAExcelTheme,
    kpis: list[dict[str, Any]],
    cell_map: Mapping[str, str],
    start_row: int,
) -> int:
    """Render Section C 3-card live KPI summary strip bound via Excel formulas."""
    r = add_section_banner(
        ws, t, start_row, "C. TỔNG HỢP KẾT QUẢ & PHÊ DUYỆT", "C. CALCULATION SUMMARY & SIGN-OFF"
    )
    spans = ((1, 2), (3, 4), (5, 6))
    ws.row_dimensions[r].height, ws.row_dimensions[r + 1].height = 25.0, 25.0
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for idx, kpi in enumerate(kpis[:3]):
        tid = str(kpi["target_id"])
        if tid not in cell_map:
            raise ValueError(f"Unknown KPI target_id: '{tid}'")
        c1, c2 = spans[idx]
        accent = str(kpi.get("accent") or t.dark_blue)
        sl, sa = make_side("thin", t.border_light), make_side("medium", accent)
        style_merged_range(
            ws,
            c1,
            r,
            c2,
            r,
            solid_fill(t.meta_fill),
            Border(left=sl, right=sl, top=sa, bottom=sl),
            center,
        )
        ws.cell(r, c1, _rt(t, kpi["label_vi"], kpi["label_en"], bold=True, vi_sz=8.5))
        style_merged_range(
            ws,
            c1,
            r + 1,
            c2,
            r + 1,
            solid_fill(t.white),
            Border(left=sl, right=sl, top=sl, bottom=sa),
            center,
        )
        vc = ws.cell(r + 1, c1, f"={cell_map[tid]}")
        vc.font, vc.number_format = (
            theme_font(t, 13.0, bold=True, color=accent),
            str(kpi.get("num_fmt", "#,##0.00")),
        )
    ws.row_dimensions[r + 2].height = 5.0
    return r + 3


def add_brand_footer(
    ws: Worksheet, t: CCBAExcelTheme, doc: Mapping[str, Any], row_idx: int, max_col: int = 6
) -> int:
    """Render 3-color CCBA slogan and unit attribution footer."""
    ws.row_dimensions[row_idx - 1].height, ws.row_dimensions[row_idx].height = 4.0, 25.0
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    style_merged_range(ws, 1, row_idx, max_col, row_idx, solid_fill(t.white), alignment=center)
    cons = str(sanitize_xlsx_value(doc["consultant"], allow_formulas=True))
    blocks = [
        TextBlock(
            InlineFont(rFont=t.font_name, sz=9.0, b=True, color=Color(rgb=argb(t.dark_blue))),
            "Smarter ",
        ),
        TextBlock(
            InlineFont(rFont=t.font_name, sz=9.0, b=True, color=Color(rgb=argb(t.ibst_red))),
            "Faster ",
        ),
        TextBlock(
            InlineFont(rFont=t.font_name, sz=9.0, b=True, color=Color(rgb=argb(t.bim_blue))),
            "Better\n",
        ),
        TextBlock(
            InlineFont(rFont=t.font_name, sz=8.0, i=True, color=Color(rgb=argb(t.text_muted))),
            f"Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng ({cons})",
        ),
    ]
    ws.cell(row_idx, 1, CellRichText(*blocks))
    return row_idx + 1


def add_signoff_and_footer(
    ws: Worksheet,
    t: CCBAExcelTheme,
    signoff: list[dict[str, Any]],
    doc: Mapping[str, Any],
    start_row: int,
) -> int:
    """Render 3-level engineering sign-off grid and CCBA brand footer."""
    spans = ((1, 2), (3, 4), (5, 6))
    border, center = (
        grid_border(t.border_light),
        Alignment(horizontal="center", vertical="center", wrap_text=True),
    )
    for offset, ht in enumerate((25.0, 33.0, 24.0)):
        ws.row_dimensions[start_row + offset].height = ht
    for idx, signer in enumerate(signoff[:3]):
        c1, c2 = spans[idx]
        style_merged_range(
            ws, c1, start_row, c2, start_row, solid_fill(t.meta_fill), border, center
        )
        ws.cell(
            start_row,
            c1,
            _rt(
                t, signer["title_vi"], signer["title_en"], bold=True, vi_sz=9.0, vi_col=t.dark_blue
            ),
        )
        style_merged_range(
            ws, c1, start_row + 1, c2, start_row + 1, solid_fill(t.white), border, center
        )
        name = signer.get("name")
        ws.cell(
            start_row + 1,
            c1,
            clean_text(name) if name else "(Ký, ghi rõ họ tên / Signature & Full Name)",
        ).font = theme_font(
            t, 8.0, italic=not bool(name), color=t.text_dark if name else t.text_muted
        )
        style_merged_range(
            ws, c1, start_row + 2, c2, start_row + 2, solid_fill(t.white), border, center
        )
        dt = signer.get("date") or "____/____/____"
        ws.cell(
            start_row + 2,
            c1,
            clean_text(f"{signer['role_vi']} / {signer['role_en']}\nNgày / Date: {dt}"),
        ).font = theme_font(t, 8.0)
    apply_outer_border(ws, 1, start_row, 6, start_row + 2, t.dark_blue, "thin")
    return add_brand_footer(ws, t, doc, start_row + 4)
