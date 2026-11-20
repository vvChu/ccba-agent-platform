"""Basic Swiss slide archetype renderers for CCBA PPTX DeckBuilder."""

from __future__ import annotations

from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from ._deck_models import SlideSpec
from .templates import (
    COLOR_BG_LIGHT,
    COLOR_BG_WHITE,
    COLOR_BIM_BRIGHT_BLUE,
    COLOR_CARD_BORDER_SOLID,
    COLOR_CCBA_DARK_BLUE,
    COLOR_IBST_RED,
    COLOR_SUCCESS_GREEN,
    COLOR_TEAL_AI,
    COLOR_TEXT_BODY,
    COLOR_TEXT_DISPLAY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    CCBAPresentationTheme,
    get_logo_asset_path,
)


def create_zero_margin_textbox(
    slide: Any,
    left: Any,
    top: Any,
    width: Any,
    height: Any,
    *,
    word_wrap: bool = True,
) -> Any:
    """Create a textbox with zero internal margins and return its text_frame."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = word_wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
    return tf


def _set_paragraph_style(
    paragraph: Any,
    text: str,
    font_family: str,
    size_pt: float,
    color: RGBColor,
    *,
    bold: bool = False,
    italic: bool = False,
    line_spacing: float | None = None,
    space_after_pt: float | None = None,
    space_before_pt: float | None = None,
    alignment: Any = None,
) -> None:
    """Apply consistent typography attributes to a pptx paragraph."""
    paragraph.text = text
    paragraph.font.name = font_family
    paragraph.font.size = Pt(size_pt)
    if bold:
        paragraph.font.bold = True
    if italic:
        paragraph.font.italic = True
    paragraph.font.color.rgb = color
    if line_spacing is not None:
        paragraph.line_spacing = line_spacing
    if space_after_pt is not None:
        paragraph.space_after = Pt(space_after_pt)
    if space_before_pt is not None:
        paragraph.space_before = Pt(space_before_pt)
    if alignment is not None:
        paragraph.alignment = alignment


def _render_cover_accent_bars(slide: Any, canvas_left: Any) -> None:
    """Draw the 3-color minimalist Swiss accent bar below cover titles."""
    accent_top = Inches(4.3)
    bar_w = Inches(0.6)
    bar_h = Pt(3)
    for idx, color in enumerate((COLOR_IBST_RED, COLOR_CCBA_DARK_BLUE, COLOR_BIM_BRIGHT_BLUE)):
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, canvas_left + bar_w * idx, accent_top, bar_w, bar_h
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()


def _render_cover_slogan(theme: CCBAPresentationTheme, slide: Any) -> None:
    """Render the tri-color 'Smarter Faster Better' slogan in the cover footer."""
    stf = create_zero_margin_textbox(
        slide,
        theme.width - Inches(4.2),
        theme.height - Inches(0.7),
        Inches(3.3),
        Inches(0.35),
        word_wrap=False,
    )
    sp = stf.paragraphs[0]
    sp.alignment = PP_ALIGN.RIGHT
    for word, color in (
        ("Smarter ", COLOR_CCBA_DARK_BLUE),
        ("Faster ", COLOR_IBST_RED),
        ("Better", COLOR_BIM_BRIGHT_BLUE),
    ):
        run = sp.add_run()
        run.text = word
        run.font.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = color


def _render_cover_footer_and_logo(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    canvas_left: Any,
) -> None:
    """Render author/date metadata, high-res CCBA logo, and slogan footer."""
    mtf = create_zero_margin_textbox(
        slide, canvas_left, Inches(4.8), Inches(7.5), Inches(1.2), word_wrap=False
    )
    if spec.author:
        _set_paragraph_style(
            mtf.paragraphs[0],
            f"👤  {spec.author}",
            theme.font_family,
            13,
            COLOR_TEXT_PRIMARY,
            bold=True,
        )
    if spec.date:
        p_date = mtf.add_paragraph() if spec.author else mtf.paragraphs[0]
        _set_paragraph_style(
            p_date,
            f"📅  Ngày: {spec.date}",
            theme.font_family,
            12,
            COLOR_TEXT_MUTED,
            space_before_pt=4,
        )

    logo_path = get_logo_asset_path("logo_ccba_full.png")
    if logo_path and logo_path.exists():
        slide.shapes.add_picture(
            str(logo_path), theme.width - Inches(3.8), Inches(4.6), width=Inches(2.9)
        )
    _render_cover_slogan(theme, slide)


def render_cover_slide(theme: CCBAPresentationTheme, slide: Any, spec: SlideSpec) -> None:
    """Render Minimalist Swiss Cover Slide."""
    theme.add_top_brand_bar(slide)
    canvas_left = Inches(0.9)
    if spec.organization:
        theme.add_eyebrow_capsule(
            slide, canvas_left, Inches(1.1), spec.organization, accent_color=COLOR_CCBA_DARK_BLUE
        )

    tf = create_zero_margin_textbox(
        slide, canvas_left, Inches(1.7), theme.width - Inches(1.8), Inches(1.8)
    )
    _set_paragraph_style(
        tf.paragraphs[0], spec.title, theme.font_family, 34, COLOR_TEXT_DISPLAY, bold=True
    )
    if spec.subtitle:
        _set_paragraph_style(
            tf.add_paragraph(),
            spec.subtitle,
            theme.font_family,
            15.5,
            COLOR_TEXT_MUTED,
            space_before_pt=12,
        )

    _render_cover_accent_bars(slide, canvas_left)
    _render_cover_footer_and_logo(theme, slide, spec, canvas_left)


def _render_big_idea_pillar_card(
    theme: CCBAPresentationTheme,
    slide: Any,
    bullet: str,
    left: Any,
    top: Any,
    width: Any,
    height: Any,
    accent: RGBColor,
) -> None:
    """Render a single bottom context/action pillar card on a Big Idea slide."""
    theme.add_card_container(
        slide,
        left,
        top,
        width,
        height,
        bg_color=COLOR_BG_WHITE,
        border_color=COLOR_CARD_BORDER_SOLID,
        border_width=1.0,
        accent_bar_color=accent,
    )
    btf = create_zero_margin_textbox(
        slide, left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), height - Inches(0.4)
    )
    _set_paragraph_style(
        btf.paragraphs[0], bullet, theme.font_family, 12, COLOR_TEXT_BODY, line_spacing=1.25
    )


def _render_big_idea_hero(
    theme: CCBAPresentationTheme,
    slide: Any,
    quote_text: str,
    canvas_left: Any,
    top_hero: Any,
    total_width: Any,
    hero_h: Any,
) -> None:
    """Render the hero quote card for a Big Idea slide."""
    theme.add_card_container(
        slide,
        canvas_left,
        top_hero,
        total_width,
        hero_h,
        bg_color=COLOR_BG_LIGHT,
        border_color=COLOR_CCBA_DARK_BLUE,
        border_width=1.5,
        accent_bar_color=COLOR_CCBA_DARK_BLUE,
    )
    qtf = create_zero_margin_textbox(
        slide,
        canvas_left + Inches(0.4),
        top_hero + Inches(0.3),
        total_width - Inches(0.8),
        hero_h - Inches(0.6),
    )
    _set_paragraph_style(
        qtf.paragraphs[0],
        f"❝  {quote_text}  ❞",
        theme.font_family,
        18,
        COLOR_TEXT_PRIMARY,
        bold=True,
        line_spacing=1.35,
    )


def render_big_idea_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render 'The Big Idea' Strategic Message Slide (Cole Knaflic Pattern)."""
    theme.add_header(slide, spec.title, spec.badge or "THÔNG ĐIỆP CHIẾN LƯỢC", spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)

    canvas_left = Inches(0.85)
    total_width = theme.width - Inches(1.7)
    top_hero, hero_h = Inches(1.8), Inches(2.3)
    _render_big_idea_hero(theme, slide, spec.quote_text, canvas_left, top_hero, total_width, hero_h)
    if not spec.bullets:
        return
    pillar_top, pillar_h = top_hero + hero_h + Inches(0.3), Inches(1.8)
    p_count = min(len(spec.bullets), 3)
    p_gap = Inches(0.3)
    p_width = (total_width - p_gap * (p_count - 1)) / p_count
    pill_colors = [COLOR_CCBA_DARK_BLUE, COLOR_IBST_RED, COLOR_BIM_BRIGHT_BLUE]
    for i, bullet in enumerate(spec.bullets[:p_count]):
        _render_big_idea_pillar_card(
            theme,
            slide,
            bullet,
            canvas_left + i * (p_width + p_gap),
            pillar_top,
            p_width,
            pillar_h,
            pill_colors[i % len(pill_colors)],
        )


def _populate_step_body(theme: CCBAPresentationTheme, stf: Any, step_item: str) -> None:
    """Populate step card heading and body paragraphs from optional `head: body` split."""
    parts = step_item.split(":")
    if len(parts) < 2:
        _set_paragraph_style(
            stf.paragraphs[0], step_item, theme.font_family, 13, COLOR_TEXT_BODY, line_spacing=1.3
        )
        return
    _set_paragraph_style(
        stf.paragraphs[0],
        parts[0].strip(),
        theme.font_family,
        14,
        COLOR_TEXT_PRIMARY,
        bold=True,
        space_after_pt=8,
    )
    _set_paragraph_style(
        stf.add_paragraph(),
        ":".join(parts[1:]).strip(),
        theme.font_family,
        12,
        COLOR_TEXT_BODY,
        line_spacing=1.25,
    )


def _render_single_step_card(
    theme: CCBAPresentationTheme,
    slide: Any,
    index: int,
    step_item: str,
    left: Any,
    top: Any,
    width: Any,
    height: Any,
    color: RGBColor,
) -> None:
    """Render one card column within a horizontal process stepper slide."""
    theme.add_card_container(
        slide,
        left,
        top,
        width,
        height,
        bg_color=COLOR_BG_LIGHT,
        border_color=COLOR_CARD_BORDER_SOLID,
        border_width=1.0,
        accent_bar_color=color,
    )
    ntf = create_zero_margin_textbox(
        slide, left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), Inches(0.5)
    )
    _set_paragraph_style(
        ntf.paragraphs[0], f"BƯỚC 0{index + 1}", theme.font_family, 11, color, bold=True
    )
    stf = create_zero_margin_textbox(
        slide, left + Inches(0.25), top + Inches(0.75), width - Inches(0.5), height - Inches(0.95)
    )
    _populate_step_body(theme, stf, step_item)


def render_steps_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render Horizontal Process Stepper Slide (3-4 linear steps)."""
    theme.add_header(slide, spec.title, spec.badge or "QUY TRÌNH", spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)

    steps_data = spec.steps or spec.bullets
    step_count = min(len(steps_data), 4)
    if step_count == 0:
        return

    canvas_left = Inches(0.85)
    total_width = theme.width - Inches(1.7)
    card_top = Inches(1.9)
    card_height = theme.height - Inches(2.8)
    gap = Inches(0.3)
    step_w = (total_width - gap * (step_count - 1)) / step_count
    step_colors = [COLOR_CCBA_DARK_BLUE, COLOR_BIM_BRIGHT_BLUE, COLOR_TEAL_AI, COLOR_SUCCESS_GREEN]

    for i, step_item in enumerate(steps_data[:step_count]):
        _render_single_step_card(
            theme,
            slide,
            i,
            step_item,
            canvas_left + i * (step_w + gap),
            card_top,
            step_w,
            card_height,
            step_colors[i % len(step_colors)],
        )


def _render_active_agenda_pill(
    theme: CCBAPresentationTheme, slide: Any, left: Any, top: Any, width: Any
) -> None:
    """Render the 'ĐANG TRÌNH BÀY' status capsule inside an active agenda card."""
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        left + Inches(0.2),
        top + Inches(0.2),
        width - Inches(0.4),
        Inches(0.3),
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = COLOR_CCBA_DARK_BLUE
    pill.line.fill.background()
    ptf = pill.text_frame
    ptf.vertical_anchor = MSO_ANCHOR.MIDDLE
    ptf.margin_left = ptf.margin_right = ptf.margin_top = ptf.margin_bottom = Inches(0)
    _set_paragraph_style(
        ptf.paragraphs[0],
        "ĐANG TRÌNH BÀY",
        theme.font_family,
        9,
        COLOR_TEXT_WHITE,
        bold=True,
        alignment=PP_ALIGN.CENTER,
    )


def _render_agenda_card(
    theme: CCBAPresentationTheme,
    slide: Any,
    item_text: str,
    is_active: bool,
    left: Any,
    top: Any,
    width: Any,
    height: Any,
) -> None:
    """Render one agenda column card, highlighted when active."""
    theme.add_card_container(
        slide,
        left,
        top,
        width,
        height,
        bg_color=COLOR_BG_WHITE if is_active else COLOR_BG_LIGHT,
        border_color=COLOR_CCBA_DARK_BLUE if is_active else COLOR_CARD_BORDER_SOLID,
        border_width=2.0 if is_active else 1.0,
        accent_bar_color=COLOR_CCBA_DARK_BLUE if is_active else None,
    )
    if is_active:
        _render_active_agenda_pill(theme, slide, left, top, width)

    box_top = top + (Inches(0.65) if is_active else Inches(0.25))
    box_h = height - (Inches(0.85) if is_active else Inches(0.45))
    ctf = create_zero_margin_textbox(
        slide, left + Inches(0.25), box_top, width - Inches(0.5), box_h
    )
    _set_paragraph_style(
        ctf.paragraphs[0],
        item_text,
        theme.font_family,
        14 if is_active else 12.5,
        COLOR_TEXT_PRIMARY if is_active else COLOR_TEXT_MUTED,
        bold=is_active,
        line_spacing=1.3,
    )


def render_agenda_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render Visual Navigation Scheme with Active Step Highlight."""
    theme.add_header(slide, spec.title, spec.badge or "CHƯƠNG TRÌNH", spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)

    items = spec.steps or spec.bullets
    item_count = min(len(items), 4)
    if item_count == 0:
        return

    canvas_left = Inches(0.85)
    total_width = theme.width - Inches(1.7)
    card_top = Inches(2.0)
    card_height = theme.height - Inches(3.0)
    gap = Inches(0.3)
    c_width = (total_width - gap * (item_count - 1)) / item_count
    active_idx = max(0, min(spec.active_step - 1, item_count - 1))

    for i, item_text in enumerate(items[:item_count]):
        _render_agenda_card(
            theme,
            slide,
            item_text,
            i == active_idx,
            canvas_left + i * (c_width + gap),
            card_top,
            c_width,
            card_height,
        )


def _render_quote_author(
    theme: CCBAPresentationTheme,
    slide: Any,
    author: str,
    canvas_left: Any,
    card_top: Any,
    total_width: Any,
    card_height: Any,
) -> None:
    """Render quote author attribution at the bottom right of the quote card."""
    atf = create_zero_margin_textbox(
        slide,
        canvas_left + Inches(0.5),
        card_top + card_height - Inches(0.7),
        total_width - Inches(1.0),
        Inches(0.4),
        word_wrap=False,
    )
    _set_paragraph_style(
        atf.paragraphs[0],
        f"—  {author}",
        theme.font_family,
        13,
        COLOR_CCBA_DARK_BLUE,
        bold=True,
        alignment=PP_ALIGN.RIGHT,
    )


def render_quote_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render Field Evidence / Executive Quote Slide."""
    theme.add_header(slide, spec.title, spec.badge or "Ý KIẾN HIỆN TRƯỜNG", spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)

    canvas_left = Inches(0.85)
    total_width = theme.width - Inches(1.7)
    card_top, card_height = Inches(1.9), theme.height - Inches(2.8)

    theme.add_card_container(
        slide,
        canvas_left,
        card_top,
        total_width,
        card_height,
        bg_color=COLOR_BG_LIGHT,
        border_color=COLOR_BIM_BRIGHT_BLUE,
        border_width=1.5,
        accent_bar_color=COLOR_BIM_BRIGHT_BLUE,
    )
    qtf = create_zero_margin_textbox(
        slide,
        canvas_left + Inches(0.5),
        card_top + Inches(0.4),
        total_width - Inches(1.0),
        card_height - Inches(1.2),
    )
    _set_paragraph_style(
        qtf.paragraphs[0],
        f"❝  {spec.quote_text}  ❞",
        theme.font_family,
        18,
        COLOR_TEXT_PRIMARY,
        italic=True,
        line_spacing=1.35,
    )
    if spec.quote_author:
        _render_quote_author(
            theme, slide, spec.quote_author, canvas_left, card_top, total_width, card_height
        )


def render_standard_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render Swiss Content slide with clean feature card container."""
    theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
    theme.add_footer(slide, slide_num, total_slides)

    content_left, content_top = Inches(0.85), Inches(1.8)
    content_width, content_height = theme.width - Inches(1.7), theme.height - Inches(2.6)

    theme.add_card_container(
        slide,
        content_left,
        content_top,
        content_width,
        content_height,
        bg_color=COLOR_BG_LIGHT,
        border_color=COLOR_CARD_BORDER_SOLID,
        border_width=1.0,
        accent_bar_color=COLOR_CCBA_DARK_BLUE,
    )
    tf = create_zero_margin_textbox(
        slide,
        content_left + Inches(0.4),
        content_top + Inches(0.3),
        content_width - Inches(0.8),
        content_height - Inches(0.6),
    )
    for i, bullet in enumerate(spec.bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        _set_paragraph_style(
            p,
            f"•  {bullet}",
            theme.font_family,
            14.5,
            COLOR_TEXT_BODY,
            space_after_pt=14,
            line_spacing=1.3,
        )


def render_section_slide(
    theme: CCBAPresentationTheme,
    slide: Any,
    spec: SlideSpec,
    slide_num: int,
    total_slides: int,
) -> None:
    """Render high-impact Minimalist Section Divider slide."""
    theme.add_top_brand_bar(slide)
    theme.add_footer(slide, slide_num, total_slides)

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.85),
        Inches(2.2),
        theme.width - Inches(1.7),
        Inches(2.8),
    )
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CCBA_DARK_BLUE
    card.line.fill.background()

    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.6)
    tf.margin_top = Inches(0.5)

    _set_paragraph_style(
        tf.paragraphs[0], spec.title, theme.font_family, 28, COLOR_TEXT_WHITE, bold=True
    )
    if spec.subtitle:
        _set_paragraph_style(
            tf.add_paragraph(),
            spec.subtitle,
            theme.font_family,
            15,
            COLOR_BIM_BRIGHT_BLUE,
            space_before_pt=10,
        )
