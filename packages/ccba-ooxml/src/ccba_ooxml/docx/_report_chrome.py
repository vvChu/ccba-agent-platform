"""Cover page, running header/footer, KPI cards, and atomic sign-off chrome."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, Twips
from PIL import Image as PILImage

from ._report_theme import (
    CONTENT_WIDTH_DXA,
    HEADER_COL_WIDTHS_DXA,
    MARGIN_BOTTOM_DXA,
    MARGIN_LEFT_DXA,
    MARGIN_RIGHT_DXA,
    MARGIN_TOP_DXA,
    PAGE_HEIGHT_DXA,
    PAGE_WIDTH_DXA,
    CCBADocxTheme,
    add_styled_run,
    add_xml_field,
    normalize_col_widths,
    normalize_hex,
    sanitize_xml_text,
    set_cell_borders,
    set_cell_margins,
    set_cell_shading,
    set_cell_valign,
    set_row_cant_split,
    set_table_borders,
    set_table_fixed_grid,
    wcag_safe_text_hex,
)

__all__ = [
    "DEFAULT_SIGNOFF_TITLE",
    "configure_a4_section",
    "normalize_consultant_name",
    "render_cover_page",
    "render_kpi_cards",
    "render_running_header_footer",
    "render_signoff_block",
]

DEFAULT_SIGNOFF_TITLE = "XÁC NHẬN & PHÊ DUYỆT / APPROVAL SIGN-OFF"
_DEFAULT_ORG = {
    "parent_vi": "VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG",
    "parent_en": "Institute for Building Science and Technology",
    "unit_vi": "TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG",
    "unit_en": "Center for Consulting Services and BIM Application in Construction (CCBA)",
}
_IBST_CCBA_SLASH_RE = re.compile(r"\bIBST\s*/\s*CCBA\b", re.IGNORECASE)
_MINISTRY_RE = re.compile(r"bộ\s+xây\s+dựng", re.IGNORECASE)
_VI_SUFFIX_RE = re.compile(r"\s*\((?:IBST|CCBA)\)\s*$", re.IGNORECASE)


def normalize_consultant_name(raw: object, default: str = "IBST - CCBA") -> str:
    """Normalize consultant label per RULE-6.1 (disallow IBST/CCBA slash)."""
    cleaned = sanitize_xml_text(raw).strip() or default
    cleaned = _IBST_CCBA_SLASH_RE.sub("IBST - CCBA", cleaned)
    return cleaned.replace(" / ", " - ")


def _clean_vi_org(raw: object, default_val: str) -> str:
    """Enforce RULE-6.1 on Vietnamese org headers (no ministry or trailing acronyms)."""
    text = sanitize_xml_text(raw).strip() or default_val
    if _MINISTRY_RE.search(text):
        return default_val
    cleaned = _VI_SUFFIX_RE.sub("", text).strip()
    return cleaned or default_val


def _join_bilingual(vi: object, en: object, sep: str = " — ") -> str:
    vi_s = sanitize_xml_text(vi).strip()
    en_s = sanitize_xml_text(en).strip()
    if not en_s or en_s == vi_s:
        return vi_s or "—"
    return f"{vi_s}{sep}{en_s}" if vi_s else en_s


def _drop_empty_first_paragraph(container: Any) -> None:
    """Remove initial empty paragraph inside header/footer so table sits flush."""
    if container.paragraphs:
        first = container.paragraphs[0]
        if not first.text.strip() and len(container.tables) > 0:
            parent = first._element.getparent()
            if parent is not None:
                parent.remove(first._element)


def _truncate_line(text: object, limit: int = 58) -> str:
    clean = " ".join(sanitize_xml_text(text).split())
    return clean if len(clean) <= limit else f"{clean[: limit - 1].rstrip()}…"


def configure_a4_section(doc: Any, theme: CCBADocxTheme) -> Any:
    """Configure section 0 to A4 Portrait (L=30mm, R/T/B=20mm) and first-page flag."""
    sec = doc.sections[0]
    sec.page_width = Twips(PAGE_WIDTH_DXA)
    sec.page_height = Twips(PAGE_HEIGHT_DXA)
    sec.left_margin = Twips(MARGIN_LEFT_DXA)
    sec.right_margin = Twips(MARGIN_RIGHT_DXA)
    sec.top_margin = Twips(MARGIN_TOP_DXA)
    sec.bottom_margin = Twips(MARGIN_BOTTOM_DXA)
    sec.header_distance = Twips(567)
    sec.footer_distance = Twips(567)
    sec.different_first_page_header_footer = True
    _ = theme
    return sec


def _render_cover_org_banner(
    doc: Any, theme: CCBADocxTheme, org: Mapping[str, Any], logo_path: Path | None
) -> None:
    """Render top RULE-6.1 2-tier org header and dynamically scaled CCBA logo."""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, none=True)
    set_table_fixed_grid(tbl, [6671, 2400])
    row = tbl.rows[0]
    set_row_cant_split(row)
    left_cell, right_cell = row.cells[0], row.cells[1]
    red_bdr = ("single", 18, theme.ibst_red)
    for cell in (left_cell, right_cell):
        set_cell_valign(cell, "center")
        set_cell_margins(cell, top=40, bottom=120, left=0, right=0)
        set_cell_borders(cell, bottom=red_bdr)

    lines = [
        (
            _clean_vi_org(org.get("parent_vi"), _DEFAULT_ORG["parent_vi"]),
            10.0,
            True,
            False,
            theme.dark_blue,
        ),
        (org.get("parent_en") or _DEFAULT_ORG["parent_en"], 8.5, False, True, theme.text_muted),
        (
            _clean_vi_org(org.get("unit_vi"), _DEFAULT_ORG["unit_vi"]),
            9.5,
            True,
            False,
            theme.text_dark,
        ),
        (org.get("unit_en") or _DEFAULT_ORG["unit_en"], 8.5, False, True, theme.text_muted),
    ]
    for idx, (txt, sz, is_b, is_i, col) in enumerate(lines):
        p = left_cell.paragraphs[0] if idx == 0 else left_cell.add_paragraph()
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(0), Pt(1.5)
        add_styled_run(p, txt, theme, size_pt=sz, bold=is_b, italic=is_i, color=col)

    p_logo = right_cell.paragraphs[0]
    p_logo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_logo.paragraph_format.space_after = Pt(0)
    if logo_path and logo_path.is_file():
        with PILImage.open(logo_path) as im:
            w_px, h_px = im.size
        width_cm = 3.8
        height_cm = width_cm * (h_px / w_px) if w_px > 0 else width_cm * (558 / 1024)
        p_logo.add_run().add_picture(str(logo_path), width=Cm(width_cm), height=Cm(height_cm))


def _cover_matrix_rows(doc_meta: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Build Document Control Matrix key-value rows."""
    consultant = normalize_consultant_name(doc_meta.get("consultant"))
    rows: list[tuple[str, str]] = [
        ("Mã hồ sơ / Document No.", sanitize_xml_text(doc_meta.get("doc_no") or "CCBA-RPT-001")),
        ("Phiên bản / Revision", sanitize_xml_text(doc_meta.get("revision") or "Rev. 01")),
        ("Ngày phát hành / Issue Date", sanitize_xml_text(doc_meta.get("date") or "—")),
        (
            "Dự án / Project",
            _join_bilingual(doc_meta.get("project_vi"), doc_meta.get("project_en")),
        ),
        (
            "Chủ đầu tư / Client",
            _join_bilingual(doc_meta.get("client_vi"), doc_meta.get("client_en"), " / "),
        ),
    ]
    if doc_meta.get("location_vi") or doc_meta.get("location_en"):
        rows.append(
            (
                "Địa điểm / Location",
                _join_bilingual(doc_meta.get("location_vi"), doc_meta.get("location_en"), " / "),
            )
        )
    if doc_meta.get("discipline_vi") or doc_meta.get("discipline_en"):
        rows.append(
            (
                "Bộ môn / Discipline",
                _join_bilingual(
                    doc_meta.get("discipline_vi"), doc_meta.get("discipline_en"), " / "
                ),
            )
        )
    rows.append(("Đơn vị tư vấn / Consultant", consultant))
    if doc_meta.get("status"):
        rows.append(("Trạng thái / Status", sanitize_xml_text(doc_meta["status"])))
    if doc_meta.get("contact_email"):
        rows.append(("Liên hệ / Contact Email", sanitize_xml_text(doc_meta["contact_email"])))
    return rows


def _render_cover_titles(doc: Any, theme: CCBADocxTheme, doc_meta: Mapping[str, Any]) -> None:
    """Render centered category badge, VI/EN titles, and optional subtitle."""
    cat_txt = (
        doc_meta.get("category") or "BÁO CÁO ĐÁNH GIÁ KỸ THUẬT  •  TECHNICAL EVALUATION REPORT"
    )
    for text, sz, is_b, is_i, col, sb, sa in (
        (str(cat_txt).upper(), 10.0, True, False, theme.ibst_red, 38, 10),
        (doc_meta.get("title_vi") or "BÁO CÁO KỸ THUẬT", 19.0, True, False, theme.dark_blue, 4, 6),
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(sb), Pt(sa)
        add_styled_run(p, text, theme, size_pt=sz, bold=is_b, italic=is_i, color=col)
    if doc_meta.get("title_en"):
        p_en = doc.add_paragraph()
        p_en.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_en.paragraph_format.space_after = Pt(6 if doc_meta.get("subtitle") else 24)
        add_styled_run(
            p_en, doc_meta["title_en"], theme, size_pt=12.0, italic=True, color=theme.text_muted
        )
    if doc_meta.get("subtitle"):
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sub.paragraph_format.space_after = Pt(22)
        add_styled_run(p_sub, doc_meta["subtitle"], theme, size_pt=10.5, color=theme.text_dark)


def _render_cover_matrix(doc: Any, theme: CCBADocxTheme, doc_meta: Mapping[str, Any]) -> None:
    """Render Page 1 Document Control Matrix table with fixed grid and cantSplit."""
    matrix_rows = _cover_matrix_rows(doc_meta)
    tbl = doc.add_table(rows=len(matrix_rows), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, color=theme.border_light, sz=4)
    set_table_fixed_grid(tbl, [3071, 6000])
    for idx, (label, val) in enumerate(matrix_rows):
        row = tbl.rows[idx]
        set_row_cant_split(row)
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_shading(c0, theme.surface_light)
        set_cell_shading(c1, theme.white)
        for cell in (c0, c1):
            set_cell_valign(cell, "center")
            set_cell_margins(cell, top=90, bottom=90, left=120, right=120)
        p0, p1 = c0.paragraphs[0], c1.paragraphs[0]
        p0.paragraph_format.space_after, p1.paragraph_format.space_after = Pt(0), Pt(0)
        add_styled_run(p0, label, theme, size_pt=9.0, bold=True, color=theme.dark_blue)
        add_styled_run(p1, val, theme, size_pt=9.0, color=theme.text_dark)


def render_cover_page(
    doc: Any,
    theme: CCBADocxTheme,
    org: Mapping[str, Any],
    doc_meta: Mapping[str, Any],
    logo_path: Path | None,
) -> None:
    """Render standalone Page 1 cover with logo, RULE-6.1 org block, and Control Matrix."""
    _render_cover_org_banner(doc, theme, org, logo_path)
    _render_cover_titles(doc, theme, doc_meta)
    _render_cover_matrix(doc, theme, doc_meta)
    p_tag = doc.add_paragraph()
    p_tag.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tag.paragraph_format.space_before, p_tag.paragraph_format.space_after = Pt(28), Pt(0)
    for word, col in (
        ("Smarter  •  ", theme.dark_blue),
        ("Faster  •  ", theme.ibst_red),
        ("Better", theme.bim_blue),
    ):
        add_styled_run(p_tag, word, theme, size_pt=10.0, bold=True, color=col)
    doc.add_page_break()


def _render_running_header(
    section: Any,
    theme: CCBADocxTheme,
    doc_no: str,
    consultant: str,
    short_title: str,
    *,
    revision: str | None = None,
) -> None:
    """Render Pages 2+ single-line fixed-width running header."""
    hdr = section.header
    h_tbl = hdr.add_table(rows=1, cols=2, width=Twips(CONTENT_WIDTH_DXA))
    set_table_borders(h_tbl, none=True)
    set_table_fixed_grid(h_tbl, list(HEADER_COL_WIDTHS_DXA))
    set_row_cant_split(h_tbl.rows[0])
    _drop_empty_first_paragraph(hdr)
    left_label = (
        f"{doc_no} ({revision}) | {consultant}"
        if revision and revision.lower() not in doc_no.lower()
        else f"{doc_no}  |  {consultant}"
    )
    specs = (
        (
            h_tbl.rows[0].cells[0],
            left_label,
            WD_ALIGN_PARAGRAPH.LEFT,
            True,
            theme.dark_blue,
        ),
        (h_tbl.rows[0].cells[1], short_title, WD_ALIGN_PARAGRAPH.RIGHT, False, theme.text_muted),
    )
    for cell, txt, align, is_b, col in specs:
        set_cell_margins(cell, top=0, bottom=60, left=0, right=0)
        set_cell_borders(cell, bottom=("single", 6, theme.border_light))
        p = cell.paragraphs[0]
        p.alignment = align
        p.paragraph_format.space_after = Pt(0)
        add_styled_run(p, txt, theme, size_pt=8.5, bold=is_b, italic=not is_b, color=col)


def _render_running_footer(
    section: Any, theme: CCBADocxTheme, doc_meta: Mapping[str, Any], consultant: str
) -> None:
    """Render Pages 2+ tri-color footer with native Word PAGE/NUMPAGES XML fields."""
    ftr = section.footer
    f_tbl = ftr.add_table(rows=1, cols=2, width=Twips(CONTENT_WIDTH_DXA))
    set_table_borders(f_tbl, none=True)
    set_table_fixed_grid(f_tbl, [6571, 2500])
    set_row_cant_split(f_tbl.rows[0])
    _drop_empty_first_paragraph(ftr)
    c_left, c_right = f_tbl.rows[0].cells[0], f_tbl.rows[0].cells[1]
    for cell in (c_left, c_right):
        set_cell_margins(cell, top=70, bottom=0, left=0, right=0)
        set_cell_borders(cell, top=("single", 8, theme.dark_blue))

    pl = c_left.paragraphs[0]
    pl.paragraph_format.space_after = Pt(0)
    for word, col in (
        ("Smarter ", theme.dark_blue),
        ("Faster ", theme.ibst_red),
        ("Better", theme.bim_blue),
    ):
        add_styled_run(pl, word, theme, size_pt=8.0, bold=True, color=col)
    email = sanitize_xml_text(doc_meta.get("contact_email") or "").strip()
    meta_tail = f"  |  {consultant}" + (f"  |  {email}" if email else "")
    add_styled_run(pl, meta_tail, theme, size_pt=8.0, color=theme.text_muted)

    pr = c_right.paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pr.paragraph_format.space_after = Pt(0)
    add_styled_run(pr, "Trang ", theme, size_pt=8.0, color=theme.text_muted)
    add_xml_field(pr, "PAGE", theme, size_pt=8.0, color=theme.dark_blue, bold=True)
    add_styled_run(pr, " / ", theme, size_pt=8.0, color=theme.text_muted)
    add_xml_field(pr, "NUMPAGES", theme, size_pt=8.0, color=theme.dark_blue, bold=True)


def render_running_header_footer(
    section: Any, theme: CCBADocxTheme, doc_meta: Mapping[str, Any]
) -> None:
    """Render Pages 2+ single-line header ([3571, 5500] DXA) and tri-color footer."""
    consultant = normalize_consultant_name(doc_meta.get("consultant"))
    doc_no = sanitize_xml_text(doc_meta.get("doc_no") or "CCBA-RPT")
    raw_rev = sanitize_xml_text(doc_meta.get("revision") or "").strip()
    revision = raw_rev or None if doc_meta.get("header_include_revision") else None
    short_title = _truncate_line(
        doc_meta.get("short_title") or doc_meta.get("title_vi") or doc_meta.get("title_en") or ""
    )
    _render_running_header(section, theme, doc_no, consultant, short_title, revision=revision)
    _render_running_footer(section, theme, doc_meta, consultant)


def render_kpi_cards(doc: Any, theme: CCBADocxTheme, kpis: Sequence[Mapping[str, Any]]) -> None:
    """Render horizontal KPI summary strip with WCAG AA/AAA text contrast mapping."""
    if not kpis:
        return
    widths = normalize_col_widths(len(kpis), total_dxa=theme.content_width_dxa)
    tbl = doc.add_table(rows=1, cols=len(kpis))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, none=True)
    set_table_fixed_grid(tbl, widths)
    set_row_cant_split(tbl.rows[0])
    light_bdr = ("single", 4, theme.border_light)

    for idx, kpi in enumerate(kpis):
        cell = tbl.rows[0].cells[idx]
        accent = normalize_hex(str(kpi.get("accent") or theme.dark_blue), fallback=theme.dark_blue)
        val_color = wcag_safe_text_hex(accent, theme)
        set_cell_shading(cell, theme.surface_light)
        set_cell_valign(cell, "center")
        set_cell_margins(cell, top=90, bottom=90, left=100, right=100)
        set_cell_borders(
            cell, top=("single", 18, accent), left=light_bdr, bottom=light_bdr, right=light_bdr
        )

        p_lbl = cell.paragraphs[0]
        p_lbl.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_lbl.paragraph_format.space_after = Pt(2)
        add_styled_run(
            p_lbl,
            kpi.get("label_vi") or kpi.get("label") or "",
            theme,
            size_pt=8.5,
            bold=True,
            color=theme.text_dark,
        )
        if kpi.get("label_en"):
            p_en = cell.add_paragraph()
            p_en.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_en.paragraph_format.space_after = Pt(4)
            add_styled_run(
                p_en, kpi["label_en"], theme, size_pt=7.5, italic=True, color=theme.text_muted
            )
        p_val = cell.add_paragraph()
        p_val.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_val.paragraph_format.space_after = Pt(0)
        add_styled_run(
            p_val, kpi.get("value") or "—", theme, size_pt=13.5, bold=True, color=val_color
        )
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before, spacer.paragraph_format.space_after = Pt(0), Pt(4)


def _populate_signer_cell(cell: Any, theme: CCBADocxTheme, signer: Mapping[str, Any]) -> None:
    """Populate a symmetric signature cell without duplicating org/email metadata."""
    set_cell_shading(cell, theme.white)
    set_cell_valign(cell, "top")
    set_cell_margins(cell, top=110, bottom=110, left=100, right=100)
    role_hdr = _join_bilingual(signer.get("title_vi"), signer.get("title_en"), " / ")
    job_title = _join_bilingual(signer.get("role_vi"), signer.get("role_en"), " / ")
    entries = (
        (role_hdr.upper(), 9.0, True, False, theme.dark_blue, 0, 2),
        ("(Ký, ghi rõ họ tên)", 8.5, False, True, theme.text_muted, 0, 0),
        (signer.get("name") or "", 9.5, True, False, theme.text_dark, 34, 2),
        (job_title, 9.0, False, False, theme.text_dark, 0, 0),
    )
    for idx, (text, sz, is_b, is_i, col, sb, sa) in enumerate(entries):
        p = cell.paragraphs[0] if idx == 0 else cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(sb), Pt(sa)
        add_styled_run(p, text, theme, size_pt=sz, bold=is_b, italic=is_i, color=col)


def render_signoff_block(
    doc: Any,
    theme: CCBADocxTheme,
    signoff: Sequence[Mapping[str, Any]],
    *,
    title: str | None = DEFAULT_SIGNOFF_TITLE,
) -> None:
    """Render atomic 2-col or 3-col sign-off grid without duplicating org/email info."""
    if not signoff:
        return
    cleaned_title = sanitize_xml_text(title).strip() if title is not None else ""
    if cleaned_title:
        p_hdr = doc.add_paragraph()
        p_hdr.paragraph_format.space_before, p_hdr.paragraph_format.space_after = Pt(14), Pt(6)
        p_hdr.paragraph_format.keep_with_next = True
        add_styled_run(
            p_hdr,
            cleaned_title,
            theme,
            size_pt=10.5,
            bold=True,
            color=theme.dark_blue,
        )
    widths = normalize_col_widths(len(signoff), total_dxa=theme.content_width_dxa)
    tbl = doc.add_table(rows=1, cols=len(signoff))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, color=theme.border_light, sz=4)
    set_table_fixed_grid(tbl, widths)
    set_row_cant_split(tbl.rows[0])
    for idx, signer in enumerate(signoff):
        _populate_signer_cell(tbl.rows[0].cells[idx], theme, signer)
