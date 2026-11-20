"""Slide specification AST data transfer objects for CCBA PPTX deck builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..tables import StructuredTable


class SlideType(str, Enum):
    """Supported slide archetype layouts."""

    COVER = "cover"
    STANDARD = "standard"
    SPLIT = "split"
    TABLE = "table"
    CARDS = "cards"
    SECTION = "section"
    BIG_IDEA = "big_idea"  # Storytelling: Executive Core Message
    STEPS = "steps"  # Storytelling: Horizontal Process Stepper
    AGENDA = "agenda"  # Storytelling: Visual Navigation with Active Highlight
    QUOTE = "quote"  # Storytelling: Field Evidence & Executive Quote


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
