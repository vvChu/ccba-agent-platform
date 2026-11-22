"""CCBA Brand Identity v3.4 DOCX theme, A4 geometry constants, and OpenXML helpers."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Pt, RGBColor

__all__ = [
    "CCBADocxTheme",
    "CONTENT_WIDTH_DXA",
    "HEADER_COL_WIDTHS_DXA",
    "MARGIN_BOTTOM_DXA",
    "MARGIN_LEFT_DXA",
    "MARGIN_RIGHT_DXA",
    "MARGIN_TOP_DXA",
    "PAGE_HEIGHT_DXA",
    "PAGE_WIDTH_DXA",
    "SIGNOFF_2COL_WIDTHS_DXA",
    "SIGNOFF_3COL_WIDTHS_DXA",
    "add_styled_run",
    "add_xml_field",
    "apply_rfonts",
    "configure_normal_style",
    "hex_to_rgb",
    "normalize_col_widths",
    "normalize_hex",
    "resolve_ccba_logo",
    "sanitize_xml_text",
    "set_cell_borders",
    "set_cell_margins",
    "set_cell_shading",
    "set_cell_valign",
    "set_row_cant_split",
    "set_row_tbl_header",
    "set_table_borders",
    "set_table_fixed_grid",
    "wcag_safe_text_hex",
]

PAGE_WIDTH_DXA = 11906
PAGE_HEIGHT_DXA = 16838
MARGIN_LEFT_DXA = 1701
MARGIN_RIGHT_DXA = 1134
MARGIN_TOP_DXA = 1134
MARGIN_BOTTOM_DXA = 1134
CONTENT_WIDTH_DXA = 9071
HEADER_COL_WIDTHS_DXA: tuple[int, int] = (3571, 5500)
SIGNOFF_2COL_WIDTHS_DXA: tuple[int, int] = (4535, 4536)
SIGNOFF_3COL_WIDTHS_DXA: tuple[int, int, int] = (3024, 3023, 3024)

_CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_HEX_RE = re.compile(r"^[0-9A-F]{6}$")
_THEME_FONT_ATTRS = ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme")
_TBL_PR_ORDER = (
    "tblStyle",
    "tblpPr",
    "tblOverlap",
    "bidiVisual",
    "tblStyleRowBandSize",
    "tblStyleColBandSize",
    "tblW",
    "jc",
    "tblCellSpacing",
    "tblInd",
    "tblBorders",
    "shd",
    "tblLayout",
    "tblCellMar",
    "tblLook",
)
_TC_PR_ORDER = (
    "cnfStyle",
    "tcW",
    "gridSpan",
    "hMerge",
    "vMerge",
    "tcBorders",
    "shd",
    "noWrap",
    "tcMar",
    "textDirection",
    "tcFitText",
    "vAlign",
    "hideMark",
)
_TR_PR_ORDER = (
    "cnfStyle",
    "divId",
    "gridBefore",
    "gridAfter",
    "wBefore",
    "wAfter",
    "cantSplit",
    "trHeight",
    "tblHeader",
    "tblCellSpacing",
    "jc",
    "hidden",
)
_R_PR_ORDER = (
    "rStyle",
    "rFonts",
    "b",
    "bCs",
    "i",
    "iCs",
    "caps",
    "smallCaps",
    "strike",
    "dstrike",
    "outline",
    "shadow",
    "emboss",
    "imprint",
    "noProof",
    "snapToGrid",
    "vanish",
    "webHidden",
    "color",
    "spacing",
    "w",
    "kern",
    "position",
    "sz",
    "szCs",
    "highlight",
    "u",
    "effect",
    "bdr",
    "shd",
)


@dataclass(frozen=True)
class CCBADocxTheme:
    """Color palette, typography, and A4 geometry for CCBA technical reports."""

    font_name: str = "Segoe UI"
    dark_blue: str = "363883"
    ibst_red: str = "DA251C"
    bim_blue: str = "0093DD"
    primary_ui_blue: str = "005A9C"
    white: str = "FFFFFF"
    text_dark: str = "1A202C"
    text_muted: str = "595959"
    surface_light: str = "F8FAFC"
    surface_tint: str = "F0F6FC"
    section_fill: str = "E8EAF6"
    zebra_alt: str = "F9FAFB"
    border_light: str = "CBD5E1"
    callout_info_fill: str = "F0F6FC"
    callout_warn_fill: str = "FEF9E7"
    callout_danger_fill: str = "FEF2F2"
    callout_ok_fill: str = "ECFDF5"
    content_width_dxa: int = CONTENT_WIDTH_DXA


def resolve_ccba_logo() -> Path | None:
    """Resolve official bundled CCBA logo path without hardcoded machine paths."""
    candidate = (
        Path(__file__).resolve().parent.parent / "templates" / "assets" / "logo_ccba_full.png"
    )
    return candidate if candidate.is_file() else None


def sanitize_xml_text(value: object) -> str:
    """Strip XML 1.0 illegal control characters from arbitrary scalar input."""
    return _CTRL_RE.sub("", "" if value is None else str(value))


def normalize_hex(color: str, fallback: str = "363883") -> str:
    """Normalize and validate a 6-digit uppercase hex RGB string."""
    cleaned = sanitize_xml_text(color).strip().lstrip("#").upper()
    if not cleaned:
        fb = sanitize_xml_text(fallback).strip().lstrip("#").upper()
        if not _HEX_RE.match(fb):
            raise ValueError(f"Invalid fallback hex color: {fallback!r}")
        return fb
    if not _HEX_RE.match(cleaned):
        raise ValueError(f"Invalid 6-digit hex RGB color: {color!r}")
    return cleaned


def wcag_safe_text_hex(accent_hex: str, theme: CCBADocxTheme) -> str:
    """Map light cyan accents to WCAG AA/AAA UI blue for readable body/metric text."""
    norm = normalize_hex(accent_hex, fallback=theme.dark_blue)
    if norm == normalize_hex(theme.bim_blue):
        return normalize_hex(theme.primary_ui_blue)
    return norm


def hex_to_rgb(hex_rgb: str) -> RGBColor:
    """Convert a validated 6-digit hex color string into ``python-docx`` ``RGBColor``."""
    clean = normalize_hex(hex_rgb)
    return RGBColor(int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def normalize_col_widths(
    ncols: int,
    raw_widths: Sequence[int | float] | None = None,
    total_dxa: int = CONTENT_WIDTH_DXA,
) -> list[int]:
    """Return positive integer DXA column widths whose sum strictly equals ``total_dxa``."""
    if ncols < 1:
        raise ValueError(f"Column count must be >= 1, got {ncols}")
    if total_dxa < ncols:
        raise ValueError(f"total_dxa ({total_dxa}) must be >= ncols ({ncols})")
    if raw_widths is None:
        if total_dxa == CONTENT_WIDTH_DXA and ncols == 2:
            return list(SIGNOFF_2COL_WIDTHS_DXA)
        if total_dxa == CONTENT_WIDTH_DXA and ncols == 3:
            return list(SIGNOFF_3COL_WIDTHS_DXA)
        base, rem = divmod(total_dxa, ncols)
        return [base + (1 if idx >= ncols - rem else 0) for idx in range(ncols)]
    if len(raw_widths) != ncols:
        raise ValueError(f"Expected {ncols} column widths, got {len(raw_widths)}")
    if any(isinstance(w, bool) or float(w) <= 0 for w in raw_widths):
        raise ValueError("All column widths must be positive numbers")
    if all(isinstance(w, int) for w in raw_widths) and sum(int(w) for w in raw_widths) == total_dxa:
        return [int(w) for w in raw_widths]
    total_raw = sum(float(w) for w in raw_widths)
    scaled = [max(1, int(round(float(w) * total_dxa / total_raw))) for w in raw_widths]
    diff = total_dxa - sum(scaled)
    if diff != 0:
        widest = max(range(ncols), key=lambda idx: scaled[idx])
        scaled[widest] = max(1, scaled[widest] + diff)
    return scaled


def _set_ordered_child(parent: Any, new_el: Any, order: tuple[str, ...]) -> None:
    """Replace same-tag child and insert in strict OOXML XSD element order."""
    tag_local = str(new_el.tag).split("}")[-1]
    for old in list(parent.findall(new_el.tag)):
        parent.remove(old)
    order_idx = order.index(tag_local) if tag_local in order else len(order)
    for pos, child in enumerate(list(parent)):
        child_local = str(child.tag).split("}")[-1]
        if child_local in order and order.index(child_local) > order_idx:
            parent.insert(pos, new_el)
            return
    parent.append(new_el)


def apply_rfonts(rpr_owner: Any, font_name: str) -> None:
    """Set ``w:ascii``, ``w:hAnsi``, ``w:eastAsia``, and ``w:cs`` on ``w:rPr``."""
    clean_font = sanitize_xml_text(font_name) or "Segoe UI"
    rpr = rpr_owner.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = parse_xml(f"<w:rFonts {nsdecls('w')}/>")
        _set_ordered_child(rpr, rfonts, _R_PR_ORDER)
    for theme_attr in _THEME_FONT_ATTRS:
        rfonts.attrib.pop(qn(theme_attr), None)
    for slot in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(slot), clean_font)


def configure_normal_style(doc: Any, theme: CCBADocxTheme) -> None:
    """Configure the base ``Normal`` style with consistent font and spacing."""
    if "Normal" not in doc.styles:
        return
    normal = doc.styles["Normal"]
    normal.font.name = theme.font_name
    normal.font.size = Pt(10.0)
    normal.font.color.rgb = hex_to_rgb(theme.text_dark)
    apply_rfonts(normal.element, theme.font_name)
    pf = normal.paragraph_format
    pf.line_spacing = 1.15
    pf.space_before = Pt(0)
    pf.space_after = Pt(4)


def add_styled_run(
    para: Any,
    text: object,
    theme: CCBADocxTheme,
    *,
    size_pt: float = 10.0,
    bold: bool = False,
    italic: bool = False,
    color: str | None = None,
) -> Any:
    """Append a sanitized run styled with explicit ``w:rFonts`` across all 4 slots."""
    run = para.add_run(sanitize_xml_text(text))
    run.font.name = theme.font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = hex_to_rgb(color or theme.text_dark)
    apply_rfonts(run._r, theme.font_name)
    return run


def set_table_fixed_grid(table: Any, col_widths_dxa: Sequence[int]) -> None:
    """Enforce ``tblLayout=fixed``, ``tblW=total``, ``tblGrid``, and per-cell ``tcW``."""
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    total_w = sum(col_widths_dxa)
    _set_ordered_child(
        tbl_pr, parse_xml(f'<w:tblW {nsdecls("w")} w:w="{total_w}" w:type="dxa"/>'), _TBL_PR_ORDER
    )
    _set_ordered_child(
        tbl_pr, parse_xml(f'<w:tblLayout {nsdecls("w")} w:val="fixed"/>'), _TBL_PR_ORDER
    )
    for old_grid in list(tbl.findall(qn("w:tblGrid"))):
        tbl.remove(old_grid)
    cols_xml = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_widths_dxa)
    grid_el = parse_xml(f"<w:tblGrid {nsdecls('w')}>{cols_xml}</w:tblGrid>")
    tbl.insert(list(tbl).index(tbl_pr) + 1, grid_el)
    for row in table.rows:
        for c_idx, cell in enumerate(row.cells):
            if c_idx < len(col_widths_dxa):
                tc_pr = cell._tc.get_or_add_tcPr()
                tc_w = parse_xml(
                    f'<w:tcW {nsdecls("w")} w:w="{col_widths_dxa[c_idx]}" w:type="dxa"/>'
                )
                _set_ordered_child(tc_pr, tc_w, _TC_PR_ORDER)


def set_row_cant_split(row: Any) -> None:
    """Enforce ``<w:cantSplit/>`` on a table row to prevent mid-row page splits."""
    tr_pr = row._tr.get_or_add_trPr()
    _set_ordered_child(tr_pr, parse_xml(f"<w:cantSplit {nsdecls('w')}/>"), _TR_PR_ORDER)


def set_row_tbl_header(row: Any) -> None:
    """Mark a table header row with ``<w:tblHeader/>`` for multi-page repetition."""
    tr_pr = row._tr.get_or_add_trPr()
    _set_ordered_child(tr_pr, parse_xml(f"<w:tblHeader {nsdecls('w')}/>"), _TR_PR_ORDER)


def set_cell_shading(cell: Any, fill_hex: str) -> None:
    """Apply solid background shading to a table cell."""
    clean = normalize_hex(fill_hex, fallback="FFFFFF")
    tc_pr = cell._tc.get_or_add_tcPr()
    _set_ordered_child(
        tc_pr,
        parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{clean}"/>'),
        _TC_PR_ORDER,
    )


def set_cell_margins(
    cell: Any, *, top: int = 80, bottom: int = 80, left: int = 110, right: int = 110
) -> None:
    """Set explicit cell padding margins in DXA."""
    tc_pr = cell._tc.get_or_add_tcPr()
    xml = (
        f"<w:tcMar {nsdecls('w')}>"
        f'<w:top w:w="{top}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/>'
        f"</w:tcMar>"
    )
    _set_ordered_child(tc_pr, parse_xml(xml), _TC_PR_ORDER)


def set_cell_valign(cell: Any, valign: str = "center") -> None:
    """Set vertical alignment (``top``, ``center``, ``bottom``) on a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    _set_ordered_child(
        tc_pr, parse_xml(f'<w:vAlign {nsdecls("w")} w:val="{valign}"/>'), _TC_PR_ORDER
    )


def _edge_xml(tag: str, spec: tuple[str, int, str] | None) -> str:
    if spec is None:
        return f'<w:{tag} w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
    val, sz, color = spec
    return f'<w:{tag} w:val="{val}" w:sz="{sz}" w:space="0" w:color="{normalize_hex(color)}"/>'


def set_cell_borders(
    cell: Any,
    *,
    top: tuple[str, int, str] | None = None,
    left: tuple[str, int, str] | None = None,
    bottom: tuple[str, int, str] | None = None,
    right: tuple[str, int, str] | None = None,
) -> None:
    """Apply explicit edge borders to a single table cell in XSD order."""
    tc_pr = cell._tc.get_or_add_tcPr()
    inner = "".join(
        _edge_xml(name, spec)
        for name, spec in (("top", top), ("left", left), ("bottom", bottom), ("right", right))
    )
    _set_ordered_child(
        tc_pr, parse_xml(f"<w:tcBorders {nsdecls('w')}>{inner}</w:tcBorders>"), _TC_PR_ORDER
    )


def set_table_borders(
    table: Any, *, color: str = "CBD5E1", sz: int = 4, none: bool = False
) -> None:
    """Apply uniform single borders or clear all borders on a table."""
    tbl_pr = table._tbl.tblPr
    spec: tuple[str, int, str] | None = None if none else ("single", sz, normalize_hex(color))
    edges = ("top", "left", "bottom", "right", "insideH", "insideV")
    inner = "".join(_edge_xml(name, spec) for name in edges)
    _set_ordered_child(
        tbl_pr, parse_xml(f"<w:tblBorders {nsdecls('w')}>{inner}</w:tblBorders>"), _TBL_PR_ORDER
    )


def add_xml_field(
    para: Any,
    field_name: str,
    theme: CCBADocxTheme,
    *,
    size_pt: float = 8.0,
    color: str | None = None,
    bold: bool = False,
) -> None:
    """Insert a native WordprocessingML field (e.g., ``PAGE`` or ``NUMPAGES``)."""
    clean_field = sanitize_xml_text(field_name).strip().upper()
    parts = [
        f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>',
        f'<w:instrText {nsdecls("w")} xml:space="preserve"> {clean_field} </w:instrText>',
        f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>',
        None,
        f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>',
    ]
    for part in parts:
        run = add_styled_run(
            para, "1" if part is None else "", theme, size_pt=size_pt, bold=bold, color=color
        )
        if part is not None:
            run._r.append(parse_xml(part))
