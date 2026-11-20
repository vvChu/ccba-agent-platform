"""CCBA OOXML PowerPoint Presentation Builder (Minimalist Swiss & Storytelling Edition).

Converts Markdown AST into professional, on-brand PowerPoint presentation
decks adhering to CCBA Brand Guidelines ver 3.4, Swiss Modernist Design,
and Cole Nussbaumer Knaflic's "Storytelling With You" principles.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (IBST).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx import Presentation

from ._deck_models import CardItem, SlideSpec, SlideType
from ._deck_parser import MarkdownDeckParser
from ._deck_render_basic import (
    render_agenda_slide,
    render_big_idea_slide,
    render_cover_slide,
    render_quote_slide,
    render_section_slide,
    render_standard_slide,
    render_steps_slide,
)
from ._deck_render_complex import render_cards_slide, render_split_slide, render_table_slide
from .templates import CCBAPresentationTheme


def _save_presentation_safe(prs: Any, out: Path) -> Path:
    """Save presentation cleanly, falling back to a `_v2` filename if file-locked."""
    try:
        prs.save(str(out))
        return out
    except PermissionError:
        alt_out = out.with_stem(f"{out.stem}_v2")
        prs.save(str(alt_out))
        print(f"Warning: '{out}' was locked by another process. Saved to '{alt_out}' instead.")
        return alt_out


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

    def _render_slide_by_spec(
        self,
        slide: Any,
        spec: SlideSpec,
        slide_num: int,
        total_slides: int,
    ) -> None:
        """Dispatch a single SlideSpec to its matching slide renderer."""
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
            self._render_slide_by_spec(slide, spec, idx + 1, total_slides)
            if spec.notes and hasattr(slide, "notes_slide"):
                slide.notes_slide.notes_text_frame.text = spec.notes

        return _save_presentation_safe(prs, out)

    def _render_cover_slide(self, slide: Any, spec: SlideSpec) -> None:
        """Render Minimalist Swiss Cover Slide."""
        render_cover_slide(self.theme, slide, spec)

    def _render_big_idea_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render 'The Big Idea' Strategic Message Slide."""
        render_big_idea_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_steps_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render Horizontal Process Stepper Slide."""
        render_steps_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_agenda_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render Visual Navigation Scheme with Active Step Highlight."""
        render_agenda_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_quote_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render Field Evidence / Executive Quote Slide."""
        render_quote_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_standard_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render Swiss Content slide with clean feature card container."""
        render_standard_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_split_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render Asymmetric 60/40 Split Comparison slide."""
        render_split_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_table_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render Swiss Clean Table slide with KPI Hero Stat cards above."""
        render_table_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_cards_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render Asymmetric Bento Grid or Multi-Card Row."""
        render_cards_slide(self.theme, slide, spec, slide_num, total_slides)

    def _render_section_slide(
        self, slide: Any, spec: SlideSpec, slide_num: int, total_slides: int
    ) -> None:
        """Render high-impact Minimalist Section Divider slide."""
        render_section_slide(self.theme, slide, spec, slide_num, total_slides)


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


__all__ = [
    "CardItem",
    "DeckBuilder",
    "MarkdownDeckParser",
    "SlideSpec",
    "SlideType",
    "build_presentation_from_markdown",
]
