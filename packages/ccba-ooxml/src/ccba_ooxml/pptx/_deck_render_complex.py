"""Complex Swiss slide renderers (split, KPI table, bento cards) for CCBA PPTX."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from ..tables import StructuredTable
from ._deck_models import CardItem, SlideSpec
from ._deck_render_basic import create_zero_margin_textbox
from .templates import (
    COLOR_AMBER_ORANGE,
    COLOR_BG_LIGHT,
    COLOR_BG_MUTED,
    COLOR_BG_WHITE,
    COLOR_BIM_BRIGHT_BLUE,
    COLOR_CARD_BORDER_SOLID,
    COLOR_CCBA_DARK_BLUE,
    COLOR_IBST_RED,
    COLOR_SUCCESS_GREEN,
    COLOR_TABLE_HEADER,
    COLOR_TEAL_AI,
    COLOR_TEXT_BODY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    CCBAPresentationTheme,
)

_CARD_KIND_COLORS: dict[str, RGBColor] = {
    "info": COLOR_CCBA_DARK_BLUE,
    "arch": COLOR_CCBA_DARK_BLUE,
    "struct": COLOR_IBST_RED,
    "danger": COLOR_IBST_RED,
    "mep": COLOR_BIM_BRIGHT_BLUE,
    "success": COLOR_SUCCESS_GREEN,
    "warning": COLOR_AMBER_ORANGE,
    "ai": COLOR_TEAL_AI,
}


@dataclass(frozen=True)
class _CardRect:
    """Position and size of one rendered Bento card."""

    left: Any
    top: Any
    width: Any
    height: Any


@dataclass(frozen=True)
class _CardStyle:
    """Visual typography and padding configuration for a Bento card slot."""

    pad_x: float
    pad_y: float
    title_pt: float
    title_space_pt: float
    body_pt: float
    body_space_pt: float
    title_prefix: str
    default_color: RGBColor


def _render_split_left_column(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    left_x: Any,
    col_top: Any,
    left_w: Any,
    col_height: Any,
) -> None:
    """Render the left context/baseline column of a Split Comparison slide."""
    theme.add_card_container(
        slide,
        left_x,
        col_top,
        left_w,
        col_height,
        bg_color=COLOR_BG_LIGHT,
        border_color=COLOR_CARD_BORDER_SOLID,
        border_width=1.0,
    )
    ltf = create_zero_margin_textbox(
        slide,
        left_x + Inches(0.3),
        col_top + Inches(0.25),
        left_w - Inches(0.6),
        col_height - Inches(0.5),
    )
    if spec.left_title:
        lp_h = ltf.paragraphs[0]
        lp_h.text = spec.left_title
        lp_h.font.name = theme.font_family
        lp_h.font.size = Pt(15.5)
        lp_h.font.bold = True
        lp_h.font.color.rgb = COLOR_TEXT_MUTED
        lp_h.space_after = Pt(12)

    for i, bullet in enumerate(spec.left_column):
        lp = ltf.add_paragraph() if spec.left_title or i > 0 else ltf.paragraphs[0]
        lp.text = f"•  {bullet}"
        lp.font.name = theme.font_family
        lp.font.size = Pt(13)
        lp.font.color.rgb = COLOR_TEXT_BODY
        lp.space_after = Pt(8)


def _render_split_right_column(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    right_x: Any,
    col_top: Any,
    right_w: Any,
    col_height: Any,
) -> None:
    """Render the highlighted hero right column of a Split Comparison slide."""
    theme.add_card_container(
        slide,
        right_x,
        col_top,
        right_w,
        col_height,
        bg_color=COLOR_BG_WHITE,
        border_color=COLOR_BIM_BRIGHT_BLUE,
        border_width=1.5,
        accent_bar_color=COLOR_BIM_BRIGHT_BLUE,
    )
    rtf = create_zero_margin_textbox(
        slide,
        right_x + Inches(0.35),
        col_top + Inches(0.25),
        right_w - Inches(0.7),
        col_height - Inches(0.5),
    )
    if spec.right_title:
        rp_h = rtf.paragraphs[0]
        rp_h.text = f"⚡  {spec.right_title}"
        rp_h.font.name = theme.font_family
        rp_h.font.size = Pt(16)
        rp_h.font.bold = True
        rp_h.font.color.rgb = COLOR_CCBA_DARK_BLUE
        rp_h.space_after = Pt(12)

    for i, bullet in enumerate(spec.right_column):
        rp = rtf.add_paragraph() if spec.right_title or i > 0 else rtf.paragraphs[0]
        rp.text = f"✓  {bullet}"
        rp.font.name = theme.font_family
        rp.font.size = Pt(13.5)
        rp.font.color.rgb = COLOR_TEXT_PRIMARY
        rp.font.bold = "60%" in bullet or "100%" in bullet or "Tự động" in bullet
        rp.space_after = Pt(8)


def render_split_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render Asymmetric 60/40 Split Comparison slide."""
    theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)

    col_top = Inches(1.75)
    col_height = theme.height - Inches(2.55)
    col_gap = Inches(0.35)
    total_width = theme.width - Inches(1.7)
    left_w = total_width * 0.38
    right_w = total_width - left_w - col_gap
    left_x = Inches(0.85)
    right_x = left_x + left_w + col_gap

    _render_split_left_column(theme, slide, spec, left_x, col_top, left_w, col_height)
    _render_split_right_column(theme, slide, spec, right_x, col_top, right_w, col_height)


def _render_table_kpis(
    theme: CCBAPresentationTheme,
    slide: Any,
    canvas_left: Any,
    total_width: Any,
    kpi_top: Any,
    kpi_h: Any,
) -> None:
    """Render the 3 Hero KPI stat cards positioned above a table."""
    kpi_gap = Inches(0.25)
    kpi_w = (total_width - kpi_gap * 2) / 3.0
    kpi_specs = (
        ("111", "TỔNG SỐ XUNG ĐỘT", COLOR_CCBA_DARK_BLUE),
        ("24", "VA CHẠM NGHIÊM TRỌNG (CRITICAL)", COLOR_IBST_RED),
        ("1.5 Ngày", "THỜI GIAN XỬ LÝ TRUNG BÌNH", COLOR_BIM_BRIGHT_BLUE),
    )
    for idx, (value, label, accent) in enumerate(kpi_specs):
        theme.add_kpi_card(
            slide,
            canvas_left + (kpi_w + kpi_gap) * idx,
            kpi_top,
            kpi_w,
            kpi_h,
            value=value,
            label=label,
            accent_color=accent,
            bg_color=COLOR_BG_LIGHT,
        )


def _populate_table_headers(
    theme: CCBAPresentationTheme,
    tbl: Any,
    headers: list[str],
) -> None:
    """Apply CCBA navy header styling and text to table row 0."""
    for c_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_TABLE_HEADER
        cell.text_frame.margin_left = cell.text_frame.margin_right = Inches(0.12)
        cell.text_frame.margin_top = cell.text_frame.margin_bottom = Inches(0.08)
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.name = theme.font_family
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_WHITE
        p.alignment = PP_ALIGN.CENTER


def _populate_table_rows(
    theme: CCBAPresentationTheme,
    tbl: Any,
    table_data: StructuredTable,
    cols_count: int,
) -> None:
    """Apply zebra striping and summary highlight to table body rows."""
    for r_idx, row_data in enumerate(table_data.rows):
        row_num = r_idx + 1
        is_summary_row = r_idx == len(table_data.rows) - 1
        bg = COLOR_BG_MUTED if (r_idx % 2 == 1 or is_summary_row) else COLOR_BG_WHITE
        for c_idx, cell_value in enumerate(row_data):
            if c_idx >= cols_count:
                break
            cell = tbl.cell(row_num, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            cell.text_frame.margin_left = cell.text_frame.margin_right = Inches(0.12)
            cell.text_frame.margin_top = cell.text_frame.margin_bottom = Inches(0.06)
            p = cell.text_frame.paragraphs[0]
            p.text = cell_value
            p.font.name = theme.font_family
            p.font.size = Pt(11)
            p.font.bold = is_summary_row
            p.font.color.rgb = COLOR_CCBA_DARK_BLUE if is_summary_row else COLOR_TEXT_PRIMARY


def render_table_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render Swiss Clean Table slide with KPI Hero Stat cards above."""
    theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)

    table_data = spec.table
    if not table_data:
        return

    total_width = theme.width - Inches(1.7)
    canvas_left = Inches(0.85)
    kpi_h = Inches(0.95)
    kpi_top = Inches(1.7)
    _render_table_kpis(theme, slide, canvas_left, total_width, kpi_top, kpi_h)

    tbl_top = kpi_top + kpi_h + Inches(0.25)
    rows_count = len(table_data.rows) + 1
    cols_count = max(len(table_data.headers), table_data.cols_count, 1)
    tbl = slide.shapes.add_table(
        rows_count, cols_count, canvas_left, tbl_top, total_width, Inches(0.42) * rows_count
    ).table
    _populate_table_headers(theme, tbl, table_data.headers)
    _populate_table_rows(theme, tbl, table_data, cols_count)


def _render_styled_card(
    theme: CCBAPresentationTheme,
    slide: Any,
    card: CardItem,
    rect: _CardRect,
    style: _CardStyle,
) -> None:
    """Render one bordered Bento card container with titled bullet content."""
    accent = _CARD_KIND_COLORS.get(card.kind.lower(), style.default_color)
    theme.add_card_container(
        slide,
        rect.left,
        rect.top,
        rect.width,
        rect.height,
        bg_color=COLOR_BG_LIGHT,
        border_color=COLOR_CARD_BORDER_SOLID,
        border_width=1.0,
        accent_bar_color=accent,
    )
    tf = create_zero_margin_textbox(
        slide,
        rect.left + Inches(style.pad_x),
        rect.top + Inches(style.pad_y),
        rect.width - Inches(style.pad_x * 2),
        rect.height - Inches(style.pad_y * 2),
    )
    p_h = tf.paragraphs[0]
    p_h.text = f"{style.title_prefix}{card.title}"
    p_h.font.name = theme.font_family
    p_h.font.size = Pt(style.title_pt)
    p_h.font.bold = True
    p_h.font.color.rgb = accent
    p_h.space_after = Pt(style.title_space_pt)

    for line in card.content.splitlines():
        if not line.strip():
            continue
        p_b = tf.add_paragraph()
        p_b.text = f"•  {line.strip()}"
        p_b.font.name = theme.font_family
        p_b.font.size = Pt(style.body_pt)
        p_b.font.color.rgb = COLOR_TEXT_BODY
        p_b.space_after = Pt(style.body_space_pt)


def _render_three_card_bento(
    theme: CCBAPresentationTheme,
    slide: Any,
    cards: list[CardItem],
    canvas_left: Any,
    card_top: Any,
    total_width: Any,
    card_height: Any,
) -> None:
    """Render the asymmetric 3-card Bento layout (54% hero + 2 stacked right)."""
    gap = Inches(0.3)
    left_w = total_width * 0.54
    right_w = total_width - left_w - gap
    right_x = canvas_left + left_w + gap
    sub_h = (card_height - gap) / 2.0

    slots = (
        (
            cards[0],
            _CardRect(canvas_left, card_top, left_w, card_height),
            _CardStyle(0.35, 0.3, 16, 12, 13, 8, "🏛️  ", COLOR_CCBA_DARK_BLUE),
        ),
        (
            cards[1],
            _CardRect(right_x, card_top, right_w, sub_h),
            _CardStyle(0.3, 0.2, 14.5, 6, 12, 4, "🏗️  ", COLOR_IBST_RED),
        ),
        (
            cards[2],
            _CardRect(right_x, card_top + sub_h + gap, right_w, sub_h),
            _CardStyle(0.3, 0.2, 14.5, 6, 12, 4, "⚙️  ", COLOR_BIM_BRIGHT_BLUE),
        ),
    )
    for card, rect, style in slots:
        _render_styled_card(theme, slide, card, rect, style)


def render_cards_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render Asymmetric Bento Grid (55% Hero + 42% Stacked Cards) or Multi-Card Row."""
    theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)
    if not spec.cards:
        return

    total_width = theme.width - Inches(1.7)
    card_top = Inches(1.75)
    card_height = theme.height - Inches(2.55)
    canvas_left = Inches(0.85)

    if len(spec.cards) == 3:
        _render_three_card_bento(
            theme, slide, spec.cards, canvas_left, card_top, total_width, card_height
        )
        return

    gap = Inches(0.3)
    cols = min(len(spec.cards), 4)
    c_width = (total_width - gap * (cols - 1)) / cols
    grid_style = _CardStyle(0.25, 0.25, 15, 10, 12.5, 6, "", COLOR_CCBA_DARK_BLUE)
    for i, card_item in enumerate(spec.cards[:cols]):
        rect = _CardRect(canvas_left + i * (c_width + gap), card_top, c_width, card_height)
        _render_styled_card(theme, slide, card_item, rect, grid_style)
