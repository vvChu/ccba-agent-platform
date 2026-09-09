"""CCBA OOXML PowerPoint Presentation Subpackage.

Provides AST-driven presentation deck building, brand templates,
and DOM manipulation for PowerPoint presentations.
"""

from __future__ import annotations

from .deck_builder import (
    CardItem,
    DeckBuilder,
    MarkdownDeckParser,
    SlideSpec,
    SlideType,
    build_presentation_from_markdown,
)
from .inventory import (
    ParagraphData,
    PresentationInventory,
    ShapeData,
    extract_text_inventory,
    get_inventory_as_dict,
    pptx_inventory,
    save_inventory,
)
from .rearrange import rearrange_presentation, rearrange_slides
from .replace import apply_replacements, pptx_replace_text
from .templates import (
    COLOR_AMBER_ORANGE,
    COLOR_BG_LIGHT,
    COLOR_BG_WHITE,
    COLOR_BIM_BRIGHT_BLUE,
    COLOR_CARD_BORDER,
    COLOR_CCBA_DARK_BLUE,
    COLOR_DISCIPLINE_ARC,
    COLOR_DISCIPLINE_MEP,
    COLOR_DISCIPLINE_STR,
    COLOR_IBST_RED,
    COLOR_PRIMARY_UI_BLUE,
    COLOR_SUCCESS_GREEN,
    COLOR_TEAL_AI,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    COLOR_WARNING_YELLOW,
    FONT_OFFICE_SAFE,
    FONT_PRIMARY,
    SLIDE_HEIGHT_4_3,
    SLIDE_HEIGHT_16_9,
    SLIDE_WIDTH_4_3,
    SLIDE_WIDTH_16_9,
    CCBAPresentationTheme,
    get_logo_asset_path,
)
from .thumbnail import generate_thumbnails

__all__ = [
    # Deck Builder
    "DeckBuilder",
    "MarkdownDeckParser",
    "SlideSpec",
    "SlideType",
    "CardItem",
    "build_presentation_from_markdown",
    # Inventory & Inspection
    "ParagraphData",
    "ShapeData",
    "PresentationInventory",
    "extract_text_inventory",
    "get_inventory_as_dict",
    "pptx_inventory",
    "save_inventory",
    # Manipulation & Rendering
    "apply_replacements",
    "pptx_replace_text",
    "rearrange_presentation",
    "rearrange_slides",
    "generate_thumbnails",
    # Theme & Tokens
    "CCBAPresentationTheme",
    "get_logo_asset_path",
    # Colors
    "COLOR_IBST_RED",
    "COLOR_CCBA_DARK_BLUE",
    "COLOR_BIM_BRIGHT_BLUE",
    "COLOR_PRIMARY_UI_BLUE",
    "COLOR_TEAL_AI",
    "COLOR_AMBER_ORANGE",
    "COLOR_SUCCESS_GREEN",
    "COLOR_WARNING_YELLOW",
    "COLOR_TEXT_PRIMARY",
    "COLOR_TEXT_MUTED",
    "COLOR_TEXT_WHITE",
    "COLOR_BG_WHITE",
    "COLOR_BG_LIGHT",
    "COLOR_CARD_BORDER",
    "COLOR_DISCIPLINE_ARC",
    "COLOR_DISCIPLINE_STR",
    "COLOR_DISCIPLINE_MEP",
    # Typography & Dimensions
    "FONT_PRIMARY",
    "FONT_OFFICE_SAFE",
    "SLIDE_WIDTH_16_9",
    "SLIDE_HEIGHT_16_9",
    "SLIDE_WIDTH_4_3",
    "SLIDE_HEIGHT_4_3",
]
