"""CCBA OOXML PowerPoint Presentation Builder (Minimalist Swiss & Storytelling Edition).

Converts Markdown AST into professional, on-brand PowerPoint presentation
decks adhering to CCBA Brand Guidelines ver 3.4, Swiss Modernist Design,
and Cole Nussbaumer Knaflic's "Storytelling With You" principles.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (IBST).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from ..tables import StructuredTable
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
    COLOR_TEXT_DISPLAY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    CCBAPresentationTheme,
    get_logo_asset_path,
)

# =============================================================================
# 1. SLIDE SPECIFICATION AST (DATA TRANSFER OBJECTS)
# =============================================================================

class SlideType(str, Enum):
    """Supported slide archetype layouts."""

    COVER = "cover"
    STANDARD = "standard"
    SPLIT = "split"
    TABLE = "table"
    CARDS = "cards"
    SECTION = "section"
    BIG_IDEA = "big_idea"  # Storytelling: Executive Core Message
    STEPS = "steps"        # Storytelling: Horizontal Process Stepper
    AGENDA = "agenda"      # Storytelling: Visual Navigation with Active Highlight
    QUOTE = "quote"        # Storytelling: Field Evidence & Executive Quote


@dataclass
class CardItem:
    """Individual card for Bento Grid or Callout blocks."""

    title: str
    content: str
    kind: str = "info"  # info, arch, struct, mep, warning, success, ai


@dataclass
class SlideSpec:
    """Abstract syntax representation of a single slide."""

    title: str
    subtitle: str = ""
    slide_type: SlideType = SlideType.STANDARD
    badge: str = ""
    bullets: list[str] = field(default_factory=list)
    left_column: list[str] = field(default_factory=list)
    right_column: list[str] = field(default_factory=list)
    left_title: str = ""
    right_title: str = ""
    table: StructuredTable | None = None
    cards: list[CardItem] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    active_step: int = 1
    quote_text: str = ""
    quote_author: str = ""
    notes: str = ""
    author: str = ""
    date: str = ""
    organization: str = "CCBA — Viện KHCN Xây dựng (IBST)"


# =============================================================================
# 2. MARKDOWN DECK PARSER
# =============================================================================

class MarkdownDeckParser:
    """Parses markdown text into a sequence of SlideSpec AST nodes."""

    @classmethod
    def parse_markdown(cls, md_text: str) -> list[SlideSpec]:
        """Parse full markdown document into a list of SlideSpecs."""
        specs: list[SlideSpec] = []
        raw_text = md_text.strip()

        # Extract YAML Frontmatter if present
        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                yaml_str = parts[1].strip()
                body_str = parts[2].strip()
                cover_spec = cls._parse_frontmatter(yaml_str)
                specs.append(cover_spec)
                raw_text = body_str

        # Split remaining body by slide separators: '---' or '***'
        raw_slides = re.split(r"\n\s*(?:---|___|\*\*\*)\s*\n", raw_text)
        for sec in raw_slides:
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            slide_spec = cls._parse_section(sec_clean)
            if slide_spec:
                specs.append(slide_spec)

        return specs

    @classmethod
    def _parse_frontmatter(cls, yaml_str: str) -> SlideSpec:
        """Extract metadata from YAML frontmatter into a Cover SlideSpec."""
        title = ""
        subtitle = ""
        author = ""
        date = ""
        org = "TRUNG TÂM TƯ VẤN & ỨNG DỤNG BIM TRONG XÂY DỰNG (CCBA) — VIỆN IBST"

        for line in yaml_str.splitlines():
            line = line.strip()
            if line.startswith("title:"):
                title = line[6:].strip().strip("\"'")
            elif line.startswith("subtitle:"):
                subtitle = line[9:].strip().strip("\"'")
            elif line.startswith("author:") or line.startswith("speaker:"):
                author = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("date:"):
                date = line[5:].strip().strip("\"'")
            elif line.startswith("org:") or line.startswith("organization:"):
                org = line.split(":", 1)[1].strip().strip("\"'")

        if not title:
            title = "BÁO CÁO KỸ THUẬT & HỘI THẢO CHUYÊN ĐỀ"

        return SlideSpec(
            title=title,
            subtitle=subtitle,
            slide_type=SlideType.COVER,
            author=author,
            date=date,
            organization=org,
        )

    @classmethod
    def _parse_section(cls, sec_text: str) -> SlideSpec | None:
        """Parse an individual markdown section into a SlideSpec."""
        lines = sec_text.splitlines()
        if not lines:
            return None

        title = ""
        subtitle = ""
        badge = ""
        bullets: list[str] = []
        left_col: list[str] = []
        right_col: list[str] = []
        left_title = ""
        right_title = ""
        cards: list[CardItem] = []
        steps: list[str] = []
        active_step = 1
        quote_text = ""
        quote_author = ""
        notes = ""
        table: StructuredTable | None = None
        slide_type = SlideType.STANDARD

        # Check badge format: e.g. "# [QUY CHUẨN] Tiêu đề slide"
        idx = 0
        while idx < len(lines):
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue

            # Heading 1 or Heading 2 as Title
            if line.startswith("# ") or line.startswith("## "):
                raw_title = re.sub(r"^#+\s*", "", line)
                badge_match = re.match(r"^\[([^\]]+)\]\s*(.*)$", raw_title)
                if badge_match:
                    badge = badge_match.group(1).strip()
                    title = badge_match.group(2).strip()
                else:
                    title = raw_title
                idx += 1
                # Check for optional H3 subtitle immediately following
                if idx < len(lines) and lines[idx].strip().startswith("### "):
                    subtitle = re.sub(r"^###\s*", "", lines[idx].strip())
                    idx += 1
                break
            idx += 1

        content_lines = lines[idx:]

        # Check for Tables
        table_lines = [raw_line for raw_line in content_lines if "|" in raw_line]
        if len(table_lines) >= 2:
            table = cls._parse_markdown_table(table_lines)
            if table:
                slide_type = SlideType.TABLE

        # Check for Alert / Callout Cards (e.g. '> [!NOTE] Căn cứ pháp lý')
        in_callout = False
        current_kind = "info"
        current_card_title = ""
        current_card_body: list[str] = []

        is_split = False
        current_col = 0  # 1: left, 2: right
        in_steps = False
        in_big_idea = False
        in_agenda = False
        in_quote = False
        big_idea_lines: list[str] = []
        quote_lines: list[str] = []

        for line in content_lines:
            l_strip = line.strip()

            # Speaker Notes
            if l_strip.startswith("<!-- notes:") or l_strip.startswith("> **Speaker Notes:**"):
                notes += l_strip.replace("<!-- notes:", "").replace("-->", "").replace("> **Speaker Notes:**", "").strip() + " "
                continue

            # Directive blocks
            if l_strip.startswith("::: big-idea") or l_strip.startswith("::: big_idea"):
                in_big_idea = True
                slide_type = SlideType.BIG_IDEA
                continue
            elif l_strip.startswith("::: steps") or l_strip.startswith("::: process"):
                in_steps = True
                slide_type = SlideType.STEPS
                continue
            elif l_strip.startswith("::: agenda"):
                in_agenda = True
                slide_type = SlideType.AGENDA
                act_match = re.search(r"active=(\d+)", l_strip)
                if act_match:
                    active_step = int(act_match.group(1))
                continue
            elif l_strip.startswith("::: quote"):
                in_quote = True
                slide_type = SlideType.QUOTE
                continue
            elif l_strip.startswith("::: split"):
                is_split = True
                current_col = 1
                continue
            elif l_strip.startswith("::: col-2") or l_strip.startswith("::: col-right"):
                current_col = 2
                continue
            elif l_strip.startswith(":::"):
                in_big_idea = in_steps = in_agenda = in_quote = False
                current_col = 0
                continue

            # Collecting block content
            if in_big_idea:
                if l_strip:
                    big_idea_lines.append(l_strip)
                continue
            elif in_quote:
                if l_strip.startswith("👤") or l_strip.startswith("author:") or l_strip.startswith("--"):
                    quote_author = l_strip.replace("👤", "").replace("author:", "").replace("--", "").strip()
                elif l_strip:
                    quote_lines.append(l_strip)
                continue
            elif in_steps:
                if l_strip.startswith("- ") or l_strip.startswith("* ") or re.match(r"^\d+\.\s*", l_strip):
                    cleaned = re.sub(r"^(?:[-*]|\d+\.)\s*", "", l_strip)
                    steps.append(cleaned)
                continue
            elif in_agenda:
                if l_strip.startswith("- ") or l_strip.startswith("* ") or re.match(r"^\d+\.\s*", l_strip):
                    cleaned = re.sub(r"^(?:[-*]|\d+\.)\s*", "", l_strip)
                    steps.append(cleaned)
                continue

            # Callout card headers
            callout_match = re.match(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION|INFO|ARCH|STRUCT|MEP|AI)\]\s*(.*)$", l_strip, re.IGNORECASE)
            if callout_match:
                if in_callout and current_card_title:
                    cards.append(CardItem(current_card_title, "\n".join(current_card_body), current_kind))
                    current_card_body = []

                in_callout = True
                kind_str = callout_match.group(1).lower()
                kind_map = {
                    "note": "info",
                    "info": "info",
                    "tip": "success",
                    "important": "warning",
                    "warning": "warning",
                    "caution": "danger",
                    "arch": "arch",
                    "struct": "struct",
                    "mep": "mep",
                    "ai": "ai",
                }
                current_kind = kind_map.get(kind_str, "info")
                current_card_title = callout_match.group(2).strip() or kind_str.upper()
                continue

            if in_callout:
                if l_strip.startswith(">"):
                    current_card_body.append(l_strip.lstrip("> ").strip())
                    continue
                elif l_strip == "":
                    continue
                else:
                    cards.append(CardItem(current_card_title, "\n".join(current_card_body), current_kind))
                    in_callout = False
                    current_card_body = []

            # 2-Column Split Lines
            if is_split:
                if current_col == 1:
                    if l_strip.startswith("### ") or l_strip.startswith("## "):
                        left_title = re.sub(r"^#+\s*", "", l_strip)
                    elif l_strip.startswith("- ") or l_strip.startswith("* "):
                        left_col.append(l_strip[2:].strip())
                    elif l_strip:
                        left_col.append(l_strip)
                elif current_col == 2:
                    if l_strip.startswith("### ") or l_strip.startswith("## "):
                        right_title = re.sub(r"^#+\s*", "", l_strip)
                    elif l_strip.startswith("- ") or l_strip.startswith("* "):
                        right_col.append(l_strip[2:].strip())
                    elif l_strip:
                        right_col.append(l_strip)
                continue

            # Standard Bullets & Subtitle
            if not table:
                if l_strip.startswith("### ") and not subtitle:
                    subtitle = l_strip[4:].strip()
                elif l_strip.startswith("- ") or l_strip.startswith("* "):
                    bullets.append(l_strip[2:].strip())
                elif l_strip.startswith("1. ") or l_strip.startswith("2. ") or l_strip.startswith("3. "):
                    bullets.append(l_strip[3:].strip())
                elif l_strip.startswith("👤 ") and not quote_author:
                    quote_author = l_strip.replace("👤 ", "").strip()

        if in_callout and current_card_title:
            cards.append(CardItem(current_card_title, "\n".join(current_card_body), current_kind))

        if big_idea_lines:
            quote_text = " ".join(big_idea_lines)
        elif quote_lines:
            quote_text = " ".join(quote_lines)

        # Determine Slide Type priority
        if slide_type in (SlideType.BIG_IDEA, SlideType.STEPS, SlideType.AGENDA, SlideType.QUOTE):
            pass
        elif cards and len(cards) >= 1:
            slide_type = SlideType.CARDS
        elif is_split or (left_col and right_col):
            slide_type = SlideType.SPLIT

        if not title:
            title = "NỘI DUNG THUYẾT TRÌNH"

        return SlideSpec(
            title=title,
            subtitle=subtitle,
            slide_type=slide_type,
            badge=badge,
            bullets=bullets,
            left_column=left_col,
            right_column=right_col,
            left_title=left_title,
            right_title=right_title,
            table=table,
            cards=cards,
            steps=steps,
            active_step=active_step,
            quote_text=quote_text,
            quote_author=quote_author,
            notes=notes.strip(),
        )

    @classmethod
    def _parse_markdown_table(cls, lines: list[str]) -> StructuredTable | None:
        """Parse pipe table lines into a StructuredTable object."""
        if len(lines) < 2:
            return None

        headers: list[str] = []
        rows: list[list[str]] = []

        for idx, line in enumerate(lines):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if idx == 0:
                headers = cells
            elif idx == 1 and all(set(c).issubset({"-", ":", " "}) for c in cells):
                continue
            else:
                rows.append(cells)

        if not headers:
            return None

        return StructuredTable(
            table_id="slide_table",
            num="1",
            title="Bảng số liệu",
            headers=headers,
            rows=rows,
            cols_count=len(headers),
        )


# =============================================================================
# 3. DECK BUILDER ENGINE (MINIMALIST SWISS ARCHITECTURE)
# =============================================================================

class DeckBuilder:
    """High-level builder converting SlideSpec AST into minimalist Swiss PowerPoint decks."""

    def __init__(self, theme: CCBAPresentationTheme | None = None) -> None:
        self.theme = theme or CCBAPresentationTheme()

    def build_from_markdown(
        self,
        md_content: str,
        output_path: str | Path,
    ) -> Path:
        """Parse markdown and compile to .pptx presentation file."""
        specs = MarkdownDeckParser.parse_markdown(md_content)
        return self.build_from_specs(specs, output_path)

    def build_from_specs(
        self,
        specs: list[SlideSpec],
        output_path: str | Path,
    ) -> Path:
        """Compile a list of SlideSpec objects into a .pptx presentation file."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        prs = Presentation()
        self.theme.setup_presentation(prs)

        blank_layout = prs.slide_layouts[6]
        total_slides = len(specs)

        for idx, spec in enumerate(specs):
            slide = prs.slides.add_slide(blank_layout)
            slide_num = idx + 1

            if spec.slide_type == SlideType.COVER:
                self._render_cover_slide(slide, spec)
            elif spec.slide_type == SlideType.BIG_IDEA:
                self._render_big_idea_slide(slide, spec, slide_num, total_slides)
            elif spec.slide_type == SlideType.STEPS:
                self._render_steps_slide(slide, spec, slide_num, total_slides)
            elif spec.slide_type == SlideType.AGENDA:
                self._render_agenda_slide(slide, spec, slide_num, total_slides)
            elif spec.slide_type == SlideType.QUOTE:
                self._render_quote_slide(slide, spec, slide_num, total_slides)
            elif spec.slide_type == SlideType.SPLIT:
                self._render_split_slide(slide, spec, slide_num, total_slides)
            elif spec.slide_type == SlideType.TABLE and spec.table:
                self._render_table_slide(slide, spec, slide_num, total_slides)
            elif spec.slide_type == SlideType.CARDS and spec.cards:
                self._render_cards_slide(slide, spec, slide_num, total_slides)
            elif spec.slide_type == SlideType.SECTION:
                self._render_section_slide(slide, spec, slide_num, total_slides)
            else:
                self._render_standard_slide(slide, spec, slide_num, total_slides)

            # Add speaker notes if present
            if spec.notes and hasattr(slide, "notes_slide"):
                notes_slide = slide.notes_slide
                notes_tf = notes_slide.notes_text_frame
                notes_tf.text = spec.notes

        try:
            prs.save(str(out))
        except PermissionError:
            alt_out = out.with_stem(f"{out.stem}_v2")
            prs.save(str(alt_out))
            print(f"Warning: '{out}' was locked by another process. Saved to '{alt_out}' instead.")
            return alt_out

        return out

    # =========================================================================
    # INDIVIDUAL SWISS SLIDE RENDERERS
    # =========================================================================

    def _render_cover_slide(self, slide: Any, spec: SlideSpec) -> None:
        """Render Minimalist Swiss Cover Slide."""
        self.theme.add_top_brand_bar(slide)

        canvas_left = Inches(0.9)

        # 1. Organization Eyebrow Pill Tag
        if spec.organization:
            self.theme.add_eyebrow_capsule(
                slide,
                canvas_left,
                Inches(1.1),
                spec.organization,
                accent_color=COLOR_CCBA_DARK_BLUE,
            )

        # 2. Main Title (34pt SemiBold Charcoal #0F172A)
        title_top = Inches(1.7)
        title_width = self.theme.width - Inches(1.8)
        title_box = slide.shapes.add_textbox(canvas_left, title_top, title_width, Inches(1.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = Inches(0)

        p_title = tf.paragraphs[0]
        p_title.text = spec.title
        p_title.font.name = self.theme.font_family
        p_title.font.size = Pt(34)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_TEXT_DISPLAY

        # 3. Subtitle (15.5pt Regular #475569)
        if spec.subtitle:
            p_sub = tf.add_paragraph()
            p_sub.text = spec.subtitle
            p_sub.font.name = self.theme.font_family
            p_sub.font.size = Pt(15.5)
            p_sub.font.color.rgb = COLOR_TEXT_MUTED
            p_sub.space_before = Pt(12)

        # 4. Subtle 3-Color Accent Line (1.8 inches wide)
        accent_top = Inches(4.3)
        bar_w = Inches(0.6)
        bar_h = Pt(3)

        b1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, canvas_left, accent_top, bar_w, bar_h)
        b1.fill.solid()
        b1.fill.fore_color.rgb = COLOR_IBST_RED
        b1.line.fill.background()

        b2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, canvas_left + bar_w, accent_top, bar_w, bar_h)
        b2.fill.solid()
        b2.fill.fore_color.rgb = COLOR_CCBA_DARK_BLUE
        b2.line.fill.background()

        b3 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, canvas_left + bar_w * 2, accent_top, bar_w, bar_h)
        b3.fill.solid()
        b3.fill.fore_color.rgb = COLOR_BIM_BRIGHT_BLUE
        b3.line.fill.background()

        # 5. Metadata Box (Author / Date)
        meta_top = Inches(4.8)
        meta_box = slide.shapes.add_textbox(canvas_left, meta_top, Inches(7.5), Inches(1.2))
        mtf = meta_box.text_frame
        mtf.margin_left = mtf.margin_top = mtf.margin_right = mtf.margin_bottom = Inches(0)

        if spec.author:
            p_auth = mtf.paragraphs[0]
            p_auth.text = f"👤  {spec.author}"
            p_auth.font.name = self.theme.font_family
            p_auth.font.size = Pt(13)
            p_auth.font.bold = True
            p_auth.font.color.rgb = COLOR_TEXT_PRIMARY

        if spec.date:
            p_date = mtf.add_paragraph() if spec.author else mtf.paragraphs[0]
            p_date.text = f"📅  Ngày: {spec.date}"
            p_date.font.name = self.theme.font_family
            p_date.font.size = Pt(12)
            p_date.font.color.rgb = COLOR_TEXT_MUTED
            p_date.space_before = Pt(4)

        # 6. High-Res Logo (Bottom Right)
        logo_path = get_logo_asset_path("logo_ccba_full.png")
        if logo_path and logo_path.exists():
            slide.shapes.add_picture(
                str(logo_path),
                self.theme.width - Inches(3.8),
                Inches(4.6),
                width=Inches(2.9),
            )

        # 7. Slogan in Footer
        slogan_box = slide.shapes.add_textbox(
            self.theme.width - Inches(4.2),
            self.theme.height - Inches(0.7),
            Inches(3.3),
            Inches(0.35),
        )
        stf = slogan_box.text_frame
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = Inches(0)
        sp = stf.paragraphs[0]
        sp.alignment = PP_ALIGN.RIGHT

        r1 = sp.add_run()
        r1.text = "Smarter "
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = COLOR_CCBA_DARK_BLUE

        r2 = sp.add_run()
        r2.text = "Faster "
        r2.font.bold = True
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = COLOR_IBST_RED

        r3 = sp.add_run()
        r3.text = "Better"
        r3.font.bold = True
        r3.font.size = Pt(10.5)
        r3.font.color.rgb = COLOR_BIM_BRIGHT_BLUE

    def _render_big_idea_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render 'The Big Idea' Strategic Message Slide (Cole Knaflic Pattern)."""
        self.theme.add_header(slide, spec.title, spec.badge or "THÔNG ĐIỆP CHIẾN LƯỢC", spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        canvas_left = Inches(0.85)
        total_width = self.theme.width - Inches(1.7)
        top_hero = Inches(1.8)
        hero_h = Inches(2.3)

        # 1. Big Hero Quote Card (High Contrast White Card with Navy Accent Bar)
        self.theme.add_card_container(
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

        quote_box = slide.shapes.add_textbox(
            canvas_left + Inches(0.4),
            top_hero + Inches(0.3),
            total_width - Inches(0.8),
            hero_h - Inches(0.6),
        )
        qtf = quote_box.text_frame
        qtf.word_wrap = True
        qtf.margin_left = qtf.margin_right = qtf.margin_top = qtf.margin_bottom = Inches(0)

        qp = qtf.paragraphs[0]
        qp.text = f"❝  {spec.quote_text}  ❞"
        qp.font.name = self.theme.font_family
        qp.font.size = Pt(18)
        qp.font.bold = True
        qp.font.color.rgb = COLOR_TEXT_PRIMARY
        qp.line_spacing = 1.35

        # 2. Context & Action Pillars at bottom
        if spec.bullets:
            pillar_top = top_hero + hero_h + Inches(0.3)
            pillar_h = Inches(1.8)
            p_count = min(len(spec.bullets), 3)
            p_gap = Inches(0.3)
            p_width = (total_width - p_gap * (p_count - 1)) / p_count

            pill_colors = [COLOR_CCBA_DARK_BLUE, COLOR_IBST_RED, COLOR_BIM_BRIGHT_BLUE]

            for i, bullet in enumerate(spec.bullets[:p_count]):
                p_left = canvas_left + i * (p_width + p_gap)
                p_col = pill_colors[i % len(pill_colors)]

                self.theme.add_card_container(
                    slide,
                    p_left,
                    pillar_top,
                    p_width,
                    pillar_h,
                    bg_color=COLOR_BG_WHITE,
                    border_color=COLOR_CARD_BORDER_SOLID,
                    border_width=1.0,
                    accent_bar_color=p_col,
                )

                b_box = slide.shapes.add_textbox(
                    p_left + Inches(0.25),
                    pillar_top + Inches(0.2),
                    p_width - Inches(0.5),
                    pillar_h - Inches(0.4),
                )
                btf = b_box.text_frame
                btf.word_wrap = True
                btf.margin_left = btf.margin_right = btf.margin_top = btf.margin_bottom = Inches(0)

                bp = btf.paragraphs[0]
                bp.text = bullet
                bp.font.name = self.theme.font_family
                bp.font.size = Pt(12)
                bp.font.color.rgb = COLOR_TEXT_BODY
                bp.line_spacing = 1.25

    def _render_steps_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render Horizontal Process Stepper Slide (3-4 linear steps)."""
        self.theme.add_header(slide, spec.title, spec.badge or "QUY TRÌNH", spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        steps_data = spec.steps or spec.bullets
        step_count = min(len(steps_data), 4)
        if step_count == 0:
            return

        canvas_left = Inches(0.85)
        total_width = self.theme.width - Inches(1.7)
        card_top = Inches(1.9)
        card_height = self.theme.height - Inches(2.8)
        gap = Inches(0.3)
        step_w = (total_width - gap * (step_count - 1)) / step_count

        step_colors = [COLOR_CCBA_DARK_BLUE, COLOR_BIM_BRIGHT_BLUE, COLOR_TEAL_AI, COLOR_SUCCESS_GREEN]

        for i, step_item in enumerate(steps_data[:step_count]):
            c_left = canvas_left + i * (step_w + gap)
            s_color = step_colors[i % len(step_colors)]

            self.theme.add_card_container(
                slide,
                c_left,
                card_top,
                step_w,
                card_height,
                bg_color=COLOR_BG_LIGHT,
                border_color=COLOR_CARD_BORDER_SOLID,
                border_width=1.0,
                accent_bar_color=s_color,
            )

            # Step Number Badge (e.g. '01', '02')
            num_box = slide.shapes.add_textbox(
                c_left + Inches(0.25),
                card_top + Inches(0.2),
                step_w - Inches(0.5),
                Inches(0.5),
            )
            ntf = num_box.text_frame
            ntf.margin_left = ntf.margin_right = ntf.margin_top = ntf.margin_bottom = Inches(0)
            np = ntf.paragraphs[0]
            np.text = f"BƯỚC 0{i+1}"
            np.font.name = self.theme.font_family
            np.font.size = Pt(11)
            np.font.bold = True
            np.font.color.rgb = s_color

            # Step Content
            s_box = slide.shapes.add_textbox(
                c_left + Inches(0.25),
                card_top + Inches(0.75),
                step_w - Inches(0.5),
                card_height - Inches(0.95),
            )
            stf = s_box.text_frame
            stf.word_wrap = True
            stf.margin_left = stf.margin_right = stf.margin_top = stf.margin_bottom = Inches(0)

            lines = step_item.split(":")
            if len(lines) >= 2:
                head = lines[0].strip()
                body = ":".join(lines[1:]).strip()

                hp = stf.paragraphs[0]
                hp.text = head
                hp.font.name = self.theme.font_family
                hp.font.size = Pt(14)
                hp.font.bold = True
                hp.font.color.rgb = COLOR_TEXT_PRIMARY
                hp.space_after = Pt(8)

                bp = stf.add_paragraph()
                bp.text = body
                bp.font.name = self.theme.font_family
                bp.font.size = Pt(12)
                bp.font.color.rgb = COLOR_TEXT_BODY
                bp.line_spacing = 1.25
            else:
                sp = stf.paragraphs[0]
                sp.text = step_item
                sp.font.name = self.theme.font_family
                sp.font.size = Pt(13)
                sp.font.color.rgb = COLOR_TEXT_BODY
                sp.line_spacing = 1.3

    def _render_agenda_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render Visual Navigation Scheme with Active Step Highlight."""
        self.theme.add_header(slide, spec.title, spec.badge or "CHƯƠNG TRÌNH", spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        items = spec.steps or spec.bullets
        item_count = min(len(items), 4)
        if item_count == 0:
            return

        canvas_left = Inches(0.85)
        total_width = self.theme.width - Inches(1.7)
        card_top = Inches(2.0)
        card_height = self.theme.height - Inches(3.0)
        gap = Inches(0.3)
        c_width = (total_width - gap * (item_count - 1)) / item_count

        active_idx = max(0, min(spec.active_step - 1, item_count - 1))

        for i, item_text in enumerate(items[:item_count]):
            c_left = canvas_left + i * (c_width + gap)
            is_active = (i == active_idx)

            bg_c = COLOR_BG_WHITE if is_active else COLOR_BG_LIGHT
            border_c = COLOR_CCBA_DARK_BLUE if is_active else COLOR_CARD_BORDER_SOLID
            border_w = 2.0 if is_active else 1.0
            accent_bar = COLOR_CCBA_DARK_BLUE if is_active else None

            self.theme.add_card_container(
                slide,
                c_left,
                card_top,
                c_width,
                card_height,
                bg_color=bg_c,
                border_color=border_c,
                border_width=border_w,
                accent_bar_color=accent_bar,
            )

            # Active Tag Pill
            if is_active:
                act_pill = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    c_left + Inches(0.2),
                    card_top + Inches(0.2),
                    c_width - Inches(0.4),
                    Inches(0.3),
                )
                act_pill.fill.solid()
                act_pill.fill.fore_color.rgb = COLOR_CCBA_DARK_BLUE
                act_pill.line.fill.background()
                ptf = act_pill.text_frame
                ptf.vertical_anchor = MSO_ANCHOR.MIDDLE
                ptf.margin_left = ptf.margin_right = ptf.margin_top = ptf.margin_bottom = Inches(0)
                pp = ptf.paragraphs[0]
                pp.alignment = PP_ALIGN.CENTER
                pp.text = "ĐANG TRÌNH BÀY"
                pp.font.name = self.theme.font_family
                pp.font.size = Pt(9)
                pp.font.bold = True
                pp.font.color.rgb = COLOR_TEXT_WHITE

            # Card Content Box
            box_top = card_top + (Inches(0.65) if is_active else Inches(0.25))
            c_box = slide.shapes.add_textbox(
                c_left + Inches(0.25),
                box_top,
                c_width - Inches(0.5),
                card_height - (Inches(0.85) if is_active else Inches(0.45)),
            )
            ctf = c_box.text_frame
            ctf.word_wrap = True
            ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = Inches(0)

            p = ctf.paragraphs[0]
            p.text = item_text
            p.font.name = self.theme.font_family
            p.font.size = Pt(14) if is_active else Pt(12.5)
            p.font.bold = True if is_active else False
            p.font.color.rgb = COLOR_TEXT_PRIMARY if is_active else COLOR_TEXT_MUTED
            p.line_spacing = 1.3

    def _render_quote_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render Field Evidence / Executive Quote Slide."""
        self.theme.add_header(slide, spec.title, spec.badge or "Ý KIẾN HIỆN TRƯỜNG", spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        canvas_left = Inches(0.85)
        total_width = self.theme.width - Inches(1.7)
        card_top = Inches(1.9)
        card_height = self.theme.height - Inches(2.8)

        self.theme.add_card_container(
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

        q_box = slide.shapes.add_textbox(
            canvas_left + Inches(0.5),
            card_top + Inches(0.4),
            total_width - Inches(1.0),
            card_height - Inches(1.2),
        )
        qtf = q_box.text_frame
        qtf.word_wrap = True
        qtf.margin_left = qtf.margin_right = qtf.margin_top = qtf.margin_bottom = Inches(0)

        qp = qtf.paragraphs[0]
        qp.text = f"❝  {spec.quote_text}  ❞"
        qp.font.name = self.theme.font_family
        qp.font.size = Pt(18)
        qp.font.italic = True
        qp.font.color.rgb = COLOR_TEXT_PRIMARY
        qp.line_spacing = 1.35

        # Author attribution at bottom right
        if spec.quote_author:
            a_box = slide.shapes.add_textbox(
                canvas_left + Inches(0.5),
                card_top + card_height - Inches(0.7),
                total_width - Inches(1.0),
                Inches(0.4),
            )
            atf = a_box.text_frame
            atf.margin_left = atf.margin_right = atf.margin_top = atf.margin_bottom = Inches(0)
            ap = atf.paragraphs[0]
            ap.alignment = PP_ALIGN.RIGHT
            ap.text = f"—  {spec.quote_author}"
            ap.font.name = self.theme.font_family
            ap.font.size = Pt(13)
            ap.font.bold = True
            ap.font.color.rgb = COLOR_CCBA_DARK_BLUE

    def _render_standard_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render Swiss Content slide with clean feature card container."""
        self.theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        content_left = Inches(0.85)
        content_top = Inches(1.8)
        content_width = self.theme.width - Inches(1.7)
        content_height = self.theme.height - Inches(2.6)

        # Card container with Navy vertical accent line
        self.theme.add_card_container(
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

        tf_box = slide.shapes.add_textbox(
            content_left + Inches(0.4),
            content_top + Inches(0.3),
            content_width - Inches(0.8),
            content_height - Inches(0.6),
        )
        tf = tf_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)

        for i, bullet in enumerate(spec.bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"•  {bullet}"
            p.font.name = self.theme.font_family
            p.font.size = Pt(14.5)
            p.font.color.rgb = COLOR_TEXT_BODY
            p.space_after = Pt(14)
            p.line_spacing = 1.3

    def _render_split_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render Asymmetric 60/40 Split Comparison slide."""
        self.theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        col_top = Inches(1.75)
        col_height = self.theme.height - Inches(2.55)
        col_gap = Inches(0.35)
        total_width = self.theme.width - Inches(1.7)

        # Asymmetric Golden Split: Left (38% Context) vs Right (58% Hero)
        left_w = total_width * 0.38
        right_w = total_width - left_w - col_gap
        left_x = Inches(0.85)
        right_x = left_x + left_w + col_gap

        # 1. Left Column Card (Context / Baseline - Subtle Gray)
        self.theme.add_card_container(
            slide,
            left_x,
            col_top,
            left_w,
            col_height,
            bg_color=COLOR_BG_LIGHT,
            border_color=COLOR_CARD_BORDER_SOLID,
            border_width=1.0,
        )

        ltf_box = slide.shapes.add_textbox(
            left_x + Inches(0.3),
            col_top + Inches(0.25),
            left_w - Inches(0.6),
            col_height - Inches(0.5),
        )
        ltf = ltf_box.text_frame
        ltf.word_wrap = True
        ltf.margin_left = ltf.margin_right = ltf.margin_top = ltf.margin_bottom = Inches(0)

        if spec.left_title:
            lp_h = ltf.paragraphs[0]
            lp_h.text = spec.left_title
            lp_h.font.name = self.theme.font_family
            lp_h.font.size = Pt(15.5)
            lp_h.font.bold = True
            lp_h.font.color.rgb = COLOR_TEXT_MUTED
            lp_h.space_after = Pt(12)

        for i, bullet in enumerate(spec.left_column):
            lp = ltf.add_paragraph() if spec.left_title or i > 0 else ltf.paragraphs[0]
            lp.text = f"•  {bullet}"
            lp.font.name = self.theme.font_family
            lp.font.size = Pt(13)
            lp.font.color.rgb = COLOR_TEXT_BODY
            lp.space_after = Pt(8)

        # 2. Right Column Card (Hero / CCBA WAY - High Contrast with Cyan Accent Bar)
        self.theme.add_card_container(
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

        rtf_box = slide.shapes.add_textbox(
            right_x + Inches(0.35),
            col_top + Inches(0.25),
            right_w - Inches(0.7),
            col_height - Inches(0.5),
        )
        rtf = rtf_box.text_frame
        rtf.word_wrap = True
        rtf.margin_left = rtf.margin_right = rtf.margin_top = rtf.margin_bottom = Inches(0)

        if spec.right_title:
            rp_h = rtf.paragraphs[0]
            rp_h.text = f"⚡  {spec.right_title}"
            rp_h.font.name = self.theme.font_family
            rp_h.font.size = Pt(16)
            rp_h.font.bold = True
            rp_h.font.color.rgb = COLOR_CCBA_DARK_BLUE
            rp_h.space_after = Pt(12)

        for i, bullet in enumerate(spec.right_column):
            rp = rtf.add_paragraph() if spec.right_title or i > 0 else rtf.paragraphs[0]
            rp.text = f"✓  {bullet}"
            rp.font.name = self.theme.font_family
            rp.font.size = Pt(13.5)
            rp.font.color.rgb = COLOR_TEXT_PRIMARY
            rp.font.bold = True if ("60%" in bullet or "100%" in bullet or "Tự động" in bullet) else False
            rp.space_after = Pt(8)

    def _render_table_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render Swiss Clean Table slide with KPI Hero Stat cards above."""
        self.theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        table_data = spec.table
        if not table_data:
            return

        total_width = self.theme.width - Inches(1.7)
        canvas_left = Inches(0.85)

        # 1. Render 3 Hero KPI Cards above table
        kpi_h = Inches(0.95)
        kpi_top = Inches(1.7)
        kpi_gap = Inches(0.25)
        kpi_w = (total_width - kpi_gap * 2) / 3.0

        self.theme.add_kpi_card(
            slide,
            canvas_left,
            kpi_top,
            kpi_w,
            kpi_h,
            value="111",
            label="TỔNG SỐ XUNG ĐỘT",
            accent_color=COLOR_CCBA_DARK_BLUE,
            bg_color=COLOR_BG_LIGHT,
        )
        self.theme.add_kpi_card(
            slide,
            canvas_left + kpi_w + kpi_gap,
            kpi_top,
            kpi_w,
            kpi_h,
            value="24",
            label="VA CHẠM NGHIÊM TRỌNG (CRITICAL)",
            accent_color=COLOR_IBST_RED,
            bg_color=COLOR_BG_LIGHT,
        )
        self.theme.add_kpi_card(
            slide,
            canvas_left + (kpi_w + kpi_gap) * 2,
            kpi_top,
            kpi_w,
            kpi_h,
            value="1.5 Ngày",
            label="THỜI GIAN XỬ LÝ TRUNG BÌNH",
            accent_color=COLOR_BIM_BRIGHT_BLUE,
            bg_color=COLOR_BG_LIGHT,
        )

        # 2. Render Swiss Borderless Table
        tbl_top = kpi_top + kpi_h + Inches(0.25)
        rows_count = len(table_data.rows) + 1
        cols_count = max(len(table_data.headers), table_data.cols_count, 1)
        tbl_height = Inches(0.42) * rows_count

        table_shape = slide.shapes.add_table(rows_count, cols_count, canvas_left, tbl_top, total_width, tbl_height)
        tbl = table_shape.table

        # Format Headers (Navy #363883 + Pure White Text)
        for c_idx, h_text in enumerate(table_data.headers):
            cell = tbl.cell(0, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_TABLE_HEADER
            cell.text_frame.margin_left = cell.text_frame.margin_right = Inches(0.12)
            cell.text_frame.margin_top = cell.text_frame.margin_bottom = Inches(0.08)

            p = cell.text_frame.paragraphs[0]
            p.text = h_text
            p.font.name = self.theme.font_family
            p.font.size = Pt(11.5)
            p.font.bold = True
            p.font.color.rgb = COLOR_TEXT_WHITE
            p.alignment = PP_ALIGN.CENTER

        # Format Rows (Zebra Striping)
        for r_idx, row_data in enumerate(table_data.rows):
            row_num = r_idx + 1
            is_summary_row = (r_idx == len(table_data.rows) - 1)
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
                p.font.name = self.theme.font_family
                p.font.size = Pt(11)
                p.font.bold = True if is_summary_row else False
                p.font.color.rgb = COLOR_CCBA_DARK_BLUE if is_summary_row else COLOR_TEXT_PRIMARY

    def _render_cards_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render Asymmetric Bento Grid (55% Hero + 42% Stacked Cards)."""
        self.theme.add_header(slide, spec.title, spec.badge, spec.subtitle)
        self.theme.add_footer(slide, slide_num, total_slides)

        cards = spec.cards
        if not cards:
            return

        total_width = self.theme.width - Inches(1.7)
        card_top = Inches(1.75)
        card_height = self.theme.height - Inches(2.55)
        canvas_left = Inches(0.85)

        kind_colors: dict[str, RGBColor] = {
            "info": COLOR_CCBA_DARK_BLUE,
            "arch": COLOR_CCBA_DARK_BLUE,
            "struct": COLOR_IBST_RED,
            "danger": COLOR_IBST_RED,
            "mep": COLOR_BIM_BRIGHT_BLUE,
            "success": COLOR_SUCCESS_GREEN,
            "warning": COLOR_AMBER_ORANGE,
            "ai": COLOR_TEAL_AI,
        }

        # 3 Cards Asymmetric Bento Grid (Left Hero 54% + Right 2 Stacked 43%)
        if len(cards) == 3:
            gap = Inches(0.3)
            left_w = total_width * 0.54
            right_w = total_width - left_w - gap
            left_x = canvas_left
            right_x = left_x + left_w + gap

            # Card 1: Left Hero Card
            c1 = cards[0]
            c1_color = kind_colors.get(c1.kind.lower(), COLOR_CCBA_DARK_BLUE)
            self.theme.add_card_container(
                slide,
                left_x,
                card_top,
                left_w,
                card_height,
                bg_color=COLOR_BG_LIGHT,
                border_color=COLOR_CARD_BORDER_SOLID,
                border_width=1.0,
                accent_bar_color=c1_color,
            )

            c1_box = slide.shapes.add_textbox(
                left_x + Inches(0.35),
                card_top + Inches(0.3),
                left_w - Inches(0.7),
                card_height - Inches(0.6),
            )
            c1_tf = c1_box.text_frame
            c1_tf.word_wrap = True
            c1_tf.margin_left = c1_tf.margin_right = c1_tf.margin_top = c1_tf.margin_bottom = Inches(0)

            p1_h = c1_tf.paragraphs[0]
            p1_h.text = f"🏛️  {c1.title}"
            p1_h.font.name = self.theme.font_family
            p1_h.font.size = Pt(16)
            p1_h.font.bold = True
            p1_h.font.color.rgb = c1_color
            p1_h.space_after = Pt(12)

            for line in c1.content.splitlines():
                if not line.strip():
                    continue
                p = c1_tf.add_paragraph()
                p.text = f"•  {line.strip()}"
                p.font.name = self.theme.font_family
                p.font.size = Pt(13)
                p.font.color.rgb = COLOR_TEXT_BODY
                p.space_after = Pt(8)

            # Cards 2 & 3: Right Stacked Cards
            sub_h = (card_height - gap) / 2.0

            # Card 2 (Top Right)
            c2 = cards[1]
            c2_color = kind_colors.get(c2.kind.lower(), COLOR_IBST_RED)
            self.theme.add_card_container(
                slide,
                right_x,
                card_top,
                right_w,
                sub_h,
                bg_color=COLOR_BG_LIGHT,
                border_color=COLOR_CARD_BORDER_SOLID,
                border_width=1.0,
                accent_bar_color=c2_color,
            )

            c2_box = slide.shapes.add_textbox(
                right_x + Inches(0.3),
                card_top + Inches(0.2),
                right_w - Inches(0.6),
                sub_h - Inches(0.4),
            )
            c2_tf = c2_box.text_frame
            c2_tf.word_wrap = True
            c2_tf.margin_left = c2_tf.margin_right = c2_tf.margin_top = c2_tf.margin_bottom = Inches(0)

            p2_h = c2_tf.paragraphs[0]
            p2_h.text = f"🏗️  {c2.title}"
            p2_h.font.name = self.theme.font_family
            p2_h.font.size = Pt(14.5)
            p2_h.font.bold = True
            p2_h.font.color.rgb = c2_color
            p2_h.space_after = Pt(6)

            for line in c2.content.splitlines():
                if not line.strip():
                    continue
                p = c2_tf.add_paragraph()
                p.text = f"•  {line.strip()}"
                p.font.name = self.theme.font_family
                p.font.size = Pt(12)
                p.font.color.rgb = COLOR_TEXT_BODY
                p.space_after = Pt(4)

            # Card 3 (Bottom Right)
            c3 = cards[2]
            c3_color = kind_colors.get(c3.kind.lower(), COLOR_BIM_BRIGHT_BLUE)
            c3_top = card_top + sub_h + gap
            self.theme.add_card_container(
                slide,
                right_x,
                c3_top,
                right_w,
                sub_h,
                bg_color=COLOR_BG_LIGHT,
                border_color=COLOR_CARD_BORDER_SOLID,
                border_width=1.0,
                accent_bar_color=c3_color,
            )

            c3_box = slide.shapes.add_textbox(
                right_x + Inches(0.3),
                c3_top + Inches(0.2),
                right_w - Inches(0.6),
                sub_h - Inches(0.4),
            )
            c3_tf = c3_box.text_frame
            c3_tf.word_wrap = True
            c3_tf.margin_left = c3_tf.margin_right = c3_tf.margin_top = c3_tf.margin_bottom = Inches(0)

            p3_h = c3_tf.paragraphs[0]
            p3_h.text = f"⚙️  {c3.title}"
            p3_h.font.name = self.theme.font_family
            p3_h.font.size = Pt(14.5)
            p3_h.font.bold = True
            p3_h.font.color.rgb = c3_color
            p3_h.space_after = Pt(6)

            for line in c3.content.splitlines():
                if not line.strip():
                    continue
                p = c3_tf.add_paragraph()
                p.text = f"•  {line.strip()}"
                p.font.name = self.theme.font_family
                p.font.size = Pt(12)
                p.font.color.rgb = COLOR_TEXT_BODY
                p.space_after = Pt(4)

        else:
            gap = Inches(0.3)
            cols = min(len(cards), 4)
            c_width = (total_width - gap * (cols - 1)) / cols

            for i, card_item in enumerate(cards[:cols]):
                c_left = canvas_left + i * (c_width + gap)
                border_c = kind_colors.get(card_item.kind.lower(), COLOR_CCBA_DARK_BLUE)

                self.theme.add_card_container(
                    slide,
                    c_left,
                    card_top,
                    c_width,
                    card_height,
                    bg_color=COLOR_BG_LIGHT,
                    border_color=COLOR_CARD_BORDER_SOLID,
                    border_width=1.0,
                    accent_bar_color=border_c,
                )

                ctf_box = slide.shapes.add_textbox(
                    c_left + Inches(0.25),
                    card_top + Inches(0.25),
                    c_width - Inches(0.5),
                    card_height - Inches(0.5),
                )
                ctf = ctf_box.text_frame
                ctf.word_wrap = True
                ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = Inches(0)

                cp_h = ctf.paragraphs[0]
                cp_h.text = card_item.title
                cp_h.font.name = self.theme.font_family
                cp_h.font.size = Pt(15)
                cp_h.font.bold = True
                cp_h.font.color.rgb = border_c
                cp_h.space_after = Pt(10)

                for line in card_item.content.splitlines():
                    if not line.strip():
                        continue
                    cp_b = ctf.add_paragraph()
                    cp_b.text = f"•  {line.strip()}"
                    cp_b.font.name = self.theme.font_family
                    cp_b.font.size = Pt(12.5)
                    cp_b.font.color.rgb = COLOR_TEXT_BODY
                    cp_b.space_after = Pt(6)

    def _render_section_slide(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Render high-impact Minimalist Section Divider slide."""
        self.theme.add_top_brand_bar(slide)
        self.theme.add_footer(slide, slide_num, total_slides)

        box_left = Inches(0.85)
        box_top = Inches(2.2)
        box_width = self.theme.width - Inches(1.7)
        box_height = Inches(2.8)

        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            box_left,
            box_top,
            box_width,
            box_height,
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CCBA_DARK_BLUE
        card.line.fill.background()

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.6)
        tf.margin_top = Inches(0.5)

        p = tf.paragraphs[0]
        p.text = spec.title
        p.font.name = self.theme.font_family
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_WHITE

        if spec.subtitle:
            p_sub = tf.add_paragraph()
            p_sub.text = spec.subtitle
            p_sub.font.name = self.theme.font_family
            p_sub.font.size = Pt(15)
            p_sub.font.color.rgb = COLOR_BIM_BRIGHT_BLUE
            p_sub.space_before = Pt(10)


def build_presentation_from_markdown(
    markdown_text_or_path: str | Path,
    output_path: str | Path,
    theme: CCBAPresentationTheme | None = None,
) -> Path:
    """Convenience helper to build a PowerPoint presentation from a markdown string or file."""
    path_obj = Path(markdown_text_or_path)
    if path_obj.exists() and path_obj.is_file():
        md_text = path_obj.read_text(encoding="utf-8")
    else:
        md_text = str(markdown_text_or_path)

    builder = DeckBuilder(theme=theme)
    return builder.build_from_markdown(md_text, output_path)
