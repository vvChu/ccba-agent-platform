"""CCBA PowerPoint Presentation Theme & Master Templates (ver 3.4 - Minimalist Swiss Edition).

Provides design tokens, brand colors, typography scales, layout dimensions,
and visual element builders adhering to the CCBA Brand Identity Guidelines
and Swiss International Minimalist Architecture.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (IBST).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# =============================================================================
# 1. CORE BRAND & FUNCTIONAL COLORS (CCBA BRAND GUIDELINES VER 3.4)
# =============================================================================

# Core Brand Colors
COLOR_IBST_RED = RGBColor(218, 37, 28)  # #DA251C - Energy, Pioneering, Structure (STR)
COLOR_CCBA_DARK_BLUE = RGBColor(54, 56, 131)  # #363883 - Professional, Trust, Architecture (ARC)
COLOR_BIM_BRIGHT_BLUE = RGBColor(0, 147, 221)  # #0093DD - Innovation, Tech, MEP (MEP)
COLOR_PRIMARY_UI_BLUE = RGBColor(0, 90, 156)  # #005A9C - Secondary UI, Borders

# Functional & Status Colors
COLOR_TEAL_AI = RGBColor(23, 162, 184)  # #17A2B8 - AI Copilot, Automation
COLOR_AMBER_ORANGE = RGBColor(211, 84, 0)  # #D35400 - Review, Sign-off
COLOR_SUCCESS_GREEN = RGBColor(40, 167, 69)  # #28A745 - Pass Gate, Verified
COLOR_WARNING_YELLOW = RGBColor(242, 200, 17)  # #F2C811 - Warning, Attention

# Neutrals & Swiss Slate Palette (WCAG 2.1 AAA Tested >= 10:1 Contrast)
COLOR_TEXT_DISPLAY = RGBColor(15, 23, 42)  # #0F172A - Slate 900 (Display Titles)
COLOR_TEXT_PRIMARY = RGBColor(30, 41, 59)  # #1E293B - Slate 800 (Main Headings & Numbers)
COLOR_TEXT_BODY = RGBColor(51, 65, 85)  # #334155 - Slate 700 (Body text & Bullets)
COLOR_TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B - Slate 500 (Subtitles, Table Headers)
COLOR_TEXT_WHITE = RGBColor(255, 255, 255)  # #FFFFFF - Pure White
COLOR_TEXT_DARK_NAVY = RGBColor(11, 27, 61)  # #0B1B3D - Enforced dark text on cyan
COLOR_TEXT_BLACK = RGBColor(26, 32, 44)  # #1A202C - Enforced text on yellow

# Background & Surface Colors (Scandinavian / Swiss Minimalist)
COLOR_BG_WHITE = RGBColor(255, 255, 255)  # #FFFFFF - Pure Canvas
COLOR_BG_LIGHT = RGBColor(248, 250, 252)  # #F8FAFC - Card Surface Light
COLOR_BG_MUTED = RGBColor(241, 245, 249)  # #F1F5F9 - Alternate Card / Table Row
COLOR_CAPSULE_BG = RGBColor(238, 242, 255)  # #EEF2FF - Soft Indigo Capsule

# Borders
COLOR_CARD_BORDER_HAIRLINE = RGBColor(226, 232, 240)  # #E2E8F0 - 0.75pt Hairline divider
COLOR_CARD_BORDER_SOLID = RGBColor(203, 213, 225)  # #CBD5E1 - 1.0pt Solid Card border
COLOR_CARD_BORDER = COLOR_CARD_BORDER_SOLID

COLOR_TABLE_HEADER = COLOR_CCBA_DARK_BLUE
COLOR_TABLE_ALT_ROW = COLOR_BG_MUTED

# BIM Discipline Color Mapping
COLOR_DISCIPLINE_ARC = COLOR_CCBA_DARK_BLUE
COLOR_DISCIPLINE_STR = COLOR_IBST_RED
COLOR_DISCIPLINE_MEP = COLOR_BIM_BRIGHT_BLUE


# =============================================================================
# 2. TYPOGRAPHY & SLIDE SPECIFICATIONS
# =============================================================================

FONT_PRIMARY = "Inter"
FONT_OFFICE_SAFE = "Segoe UI"
FONT_FALLBACK_ARIAL = "Arial"
FONT_MONOSPACE = "Consolas"

# Slide Dimensions (16:9 Widescreen Default)
SLIDE_WIDTH_16_9 = Inches(13.333)
SLIDE_HEIGHT_16_9 = Inches(7.5)

SLIDE_WIDTH_4_3 = Inches(10.0)
SLIDE_HEIGHT_4_3 = Inches(7.5)


def get_logo_asset_path(filename: str = "logo_ccba_full.png") -> Path | None:
    """Locate bundled CCBA logo asset."""
    package_dir = Path(__file__).resolve().parent.parent
    asset_path = package_dir / "templates" / "assets" / filename
    if asset_path.exists():
        return asset_path
    return None


# =============================================================================
# 3. PRESENTATION THEME CONFIGURATION
# =============================================================================


@dataclass
class CCBAPresentationTheme:
    """Master theme holding design tokens and layout styling rules."""

    primary_color: RGBColor = COLOR_CCBA_DARK_BLUE
    secondary_color: RGBColor = COLOR_BIM_BRIGHT_BLUE
    accent_color: RGBColor = COLOR_IBST_RED
    bg_color: RGBColor = COLOR_BG_WHITE
    text_color: RGBColor = COLOR_TEXT_PRIMARY
    font_family: str = FONT_OFFICE_SAFE  # Default to Segoe UI for cross-machine zero-drift
    aspect_ratio: str = "16:9"
    confidentiality: str = "CCBA — Viện KHCN Xây dựng (IBST)"

    @property
    def width(self) -> Any:
        return SLIDE_WIDTH_16_9 if self.aspect_ratio == "16:9" else SLIDE_WIDTH_4_3

    @property
    def height(self) -> Any:
        return SLIDE_HEIGHT_16_9 if self.aspect_ratio == "16:9" else SLIDE_HEIGHT_4_3

    def setup_presentation(self, prs: Any) -> None:
        """Configure presentation dimensions."""
        prs.slide_width = self.width
        prs.slide_height = self.height

    def add_top_brand_bar(self, slide: Any) -> None:
        """Add subtle 3-color brand accent line at the very top edge."""
        bar_height = Inches(0.05)  # Thin 3.6pt accent bar
        total_w = self.width
        seg_w = total_w / 3.0

        # Segment 1: Red #DA251C
        s1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, seg_w, bar_height)
        s1.fill.solid()
        s1.fill.fore_color.rgb = COLOR_IBST_RED
        s1.line.fill.background()

        # Segment 2: Dark Blue #363883
        s2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, seg_w, 0, seg_w, bar_height)
        s2.fill.solid()
        s2.fill.fore_color.rgb = COLOR_CCBA_DARK_BLUE
        s2.line.fill.background()

        # Segment 3: Bright Blue #0093DD
        s3 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, seg_w * 2, 0, seg_w, bar_height)
        s3.fill.solid()
        s3.fill.fore_color.rgb = COLOR_BIM_BRIGHT_BLUE
        s3.line.fill.background()

    def add_eyebrow_capsule(
        self,
        slide: Any,
        left: Any,
        top: Any,
        text: str,
        accent_color: RGBColor | None = None,
    ) -> Any:
        """Add a delicate pill-shaped category badge (Eyebrow Tag)."""
        color = accent_color or self.primary_color
        # Estimate width based on text length
        capsule_w = max(Inches(1.5), Inches(len(text) * 0.11 + 0.5))
        capsule_h = Inches(0.32)

        pill = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            left,
            top,
            capsule_w,
            capsule_h,
        )
        pill.fill.solid()
        pill.fill.fore_color.rgb = COLOR_CAPSULE_BG
        pill.line.color.rgb = color
        pill.line.width = Pt(1.0)

        tf = pill.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = text.upper()
        p.font.name = self.font_family
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = color

        return pill

    def add_header(
        self,
        slide: Any,
        title: str,
        category_badge: str = "",
        subtitle: str = "",
    ) -> None:
        """Add Swiss-style minimal header with crisp typography and subtle divider."""
        self.add_top_brand_bar(slide)

        header_left: Any = Inches(0.85)
        current_top: Any = Inches(0.35)
        header_width: Any = self.width - Inches(1.7)

        # Eyebrow Tag if category badge provided
        if category_badge:
            self.add_eyebrow_capsule(slide, header_left, current_top, category_badge)
            current_top += Inches(0.40)

        # Main Title Box
        title_box = slide.shapes.add_textbox(header_left, current_top, header_width, Inches(0.65))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = Inches(0)

        p = tf.paragraphs[0]
        p.text = title
        p.font.name = self.font_family
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_DISPLAY

        if subtitle:
            p_sub = tf.add_paragraph()
            p_sub.text = subtitle
            p_sub.font.name = self.font_family
            p_sub.font.size = Pt(12.5)
            p_sub.font.color.rgb = COLOR_TEXT_MUTED
            p_sub.space_before = Pt(3)
            current_top += Inches(0.65)
        else:
            current_top += Inches(0.50)

        # Subtle Hairline Divider (0.75pt)
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            header_left,
            current_top + Inches(0.12),
            header_width,
            Pt(1),
        )
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_CARD_BORDER_HAIRLINE
        line.line.fill.background()

    def add_card_container(
        self,
        slide: Any,
        left: Any,
        top: Any,
        width: Any,
        height: Any,
        bg_color: RGBColor = COLOR_BG_LIGHT,
        border_color: RGBColor = COLOR_CARD_BORDER_SOLID,
        border_width: float = 1.0,
        accent_bar_color: RGBColor | None = None,
    ) -> Any:
        """Render a rounded card container with optional vertical accent bar."""
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            left,
            top,
            width,
            height,
        )
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_width > 0:
            card.line.color.rgb = border_color
            card.line.width = Pt(border_width)
        else:
            card.line.fill.background()

        # Vertical accent indicator on left border if specified
        if accent_bar_color:
            bar_w = Inches(0.06)
            bar = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                left,
                top + Inches(0.15),
                bar_w,
                height - Inches(0.3),
            )
            bar.fill.solid()
            bar.fill.fore_color.rgb = accent_bar_color
            bar.line.fill.background()

        return card

    def add_kpi_card(
        self,
        slide: Any,
        left: Any,
        top: Any,
        width: Any,
        height: Any,
        value: str,
        label: str,
        accent_color: RGBColor = COLOR_CCBA_DARK_BLUE,
        bg_color: RGBColor = COLOR_BG_LIGHT,
    ) -> None:
        """Render a Swiss Hero KPI Number Block (e.g. '60%', '111', '1.5 ngày')."""
        self.add_card_container(
            slide,
            left,
            top,
            width,
            height,
            bg_color=bg_color,
            border_color=COLOR_CARD_BORDER_SOLID,
            border_width=1.0,
        )

        # Value (Hero Number 36-44pt Bold)
        val_box = slide.shapes.add_textbox(
            left + Inches(0.2),
            top + Inches(0.12),
            width - Inches(0.4),
            height * 0.55,
        )
        vtf = val_box.text_frame
        vtf.margin_left = vtf.margin_right = vtf.margin_top = vtf.margin_bottom = Inches(0)
        vp = vtf.paragraphs[0]
        vp.alignment = PP_ALIGN.CENTER
        vp.text = value
        vp.font.name = self.font_family
        vp.font.size = Pt(36)
        vp.font.bold = True
        vp.font.color.rgb = accent_color

        # Label (11pt Regular / Muted)
        lbl_box = slide.shapes.add_textbox(
            left + Inches(0.15),
            top + height * 0.58,
            width - Inches(0.3),
            height * 0.38,
        )
        ltf = lbl_box.text_frame
        ltf.word_wrap = True
        ltf.margin_left = ltf.margin_right = ltf.margin_top = ltf.margin_bottom = Inches(0)
        lp = ltf.paragraphs[0]
        lp.alignment = PP_ALIGN.CENTER
        lp.text = label
        lp.font.name = self.font_family
        lp.font.size = Pt(10.5)
        lp.font.bold = True
        lp.font.color.rgb = COLOR_TEXT_MUTED

    def add_footer(
        self,
        slide: Any,
        slide_num: int = 1,
        total_slides: int = 1,
    ) -> None:
        """Add standardized footer with CCBA Smarter Faster Better 3-color slogan."""
        footer_top = self.height - Inches(0.50)
        footer_left = Inches(0.85)
        footer_width = self.width - Inches(1.7)

        # Subtle divider hairline (0.75pt)
        div = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            footer_left,
            footer_top - Pt(6),
            footer_width,
            Pt(0.75),
        )
        div.fill.solid()
        div.fill.fore_color.rgb = COLOR_CARD_BORDER_HAIRLINE
        div.line.fill.background()

        # Left: Confidentiality / Authority
        left_box = slide.shapes.add_textbox(footer_left, footer_top, Inches(4.5), Inches(0.35))
        ltf = left_box.text_frame
        ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = Inches(0)
        lp = ltf.paragraphs[0]
        lp.text = self.confidentiality
        lp.font.name = self.font_family
        lp.font.size = Pt(9.5)
        lp.font.color.rgb = COLOR_TEXT_MUTED

        # Center: Slogan with 3 Distinct Brand Colors
        center_box = slide.shapes.add_textbox(
            self.width / 2.0 - Inches(2.2),
            footer_top,
            Inches(4.4),
            Inches(0.35),
        )
        ctf = center_box.text_frame
        ctf.margin_left = ctf.margin_top = ctf.margin_right = ctf.margin_bottom = Inches(0)
        cp = ctf.paragraphs[0]
        cp.alignment = PP_ALIGN.CENTER

        r1 = cp.add_run()
        r1.text = "Smarter "
        r1.font.name = self.font_family
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_CCBA_DARK_BLUE

        r2 = cp.add_run()
        r2.text = "Faster "
        r2.font.bold = True
        r2.font.name = self.font_family
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_IBST_RED

        r3 = cp.add_run()
        r3.text = "Better"
        r3.font.bold = True
        r3.font.name = self.font_family
        r3.font.size = Pt(9.5)
        r3.font.color.rgb = COLOR_BIM_BRIGHT_BLUE

        # Right: Slide Number
        right_box = slide.shapes.add_textbox(
            self.width - Inches(0.85) - Inches(2.0),
            footer_top,
            Inches(2.0),
            Inches(0.35),
        )
        rtf = right_box.text_frame
        rtf.margin_left = rtf.margin_top = rtf.margin_right = rtf.margin_bottom = Inches(0)
        rp = rtf.paragraphs[0]
        rp.alignment = PP_ALIGN.RIGHT
        rp.text = f"{slide_num} / {total_slides}" if total_slides > 1 else str(slide_num)
        rp.font.name = self.font_family
        rp.font.size = Pt(9.5)
        rp.font.bold = True
        rp.font.color.rgb = COLOR_TEXT_MUTED
