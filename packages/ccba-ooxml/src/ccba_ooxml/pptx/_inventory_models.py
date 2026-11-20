"""Data models and type aliases for PPTX text inventory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pptx.enum.text import PP_ALIGN
from pptx.shapes.base import BaseShape
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ._inventory_metrics import ShapeData

# Type aliases for cleaner signatures
JsonValue = str | int | float | bool | None
ParagraphDict = dict[str, JsonValue]
ShapeDict = dict[str, str | float | bool | list[ParagraphDict] | list[str] | dict[str, Any] | None]
InventoryData = dict[str, dict[str, "ShapeData"]]  # Dict of slide_id -> {shape_id -> ShapeData}
InventoryDict = dict[str, dict[str, ShapeDict]]  # JSON-serializable inventory


@dataclass
class ShapeWithPosition:
    """A shape with its absolute position on the slide."""

    shape: BaseShape
    absolute_left: int  # in EMUs
    absolute_top: int  # in EMUs


def _extract_bullet_and_level(paragraph: Any) -> tuple[bool, int | None]:
    """Extract bullet flag and indentation level from a paragraph XML node."""
    if not (hasattr(paragraph, "_p") and paragraph._p is not None and paragraph._p.pPr is not None):
        return False, None
    p_pr = paragraph._p.pPr
    ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    if p_pr.find(f"{ns}buChar") is not None or p_pr.find(f"{ns}buAutoNum") is not None:
        level = paragraph.level if hasattr(paragraph, "level") else None
        return True, level
    return False, None


def _extract_alignment(paragraph: Any) -> str | None:
    """Extract paragraph alignment string if non-default (not LEFT)."""
    if not (hasattr(paragraph, "alignment") and paragraph.alignment is not None):
        return None
    alignment_map = {
        PP_ALIGN.CENTER: "CENTER",
        PP_ALIGN.RIGHT: "RIGHT",
        PP_ALIGN.JUSTIFY: "JUSTIFY",
    }
    return alignment_map.get(paragraph.alignment)


def _extract_font_color(font: Any) -> tuple[str | None, str | None]:
    """Extract RGB hex color or fallback theme color name from a run font."""
    try:
        if font.color.rgb:
            return str(font.color.rgb), None
    except (AttributeError, TypeError):
        try:
            if font.color.theme_color:
                return None, font.color.theme_color.name
        except (AttributeError, TypeError):
            pass
    return None, None


def _extract_font_props(paragraph: Any) -> dict[str, Any]:
    """Extract font properties from the first run of a paragraph."""
    props: dict[str, Any] = {
        "font_name": None,
        "font_size": None,
        "bold": None,
        "italic": None,
        "underline": None,
        "color": None,
        "theme_color": None,
    }
    if not paragraph.runs or not hasattr(paragraph.runs[0], "font"):
        return props
    font = paragraph.runs[0].font
    if font.name:
        props["font_name"] = font.name
    if font.size:
        props["font_size"] = font.size.pt
    if font.bold is not None:
        props["bold"] = font.bold
    if font.italic is not None:
        props["italic"] = font.italic
    if font.underline is not None:
        props["underline"] = font.underline
    props["color"], props["theme_color"] = _extract_font_color(font)
    return props


def _extract_line_spacing(paragraph: Any, font_size: float | None) -> float | None:
    """Extract line spacing in points from explicit pt or multiplier."""
    if not (hasattr(paragraph, "line_spacing") and paragraph.line_spacing is not None):
        return None
    if hasattr(paragraph.line_spacing, "pt"):
        return round(paragraph.line_spacing.pt, 2)
    effective_size = font_size if font_size else 12.0
    return round(paragraph.line_spacing * effective_size, 2)


class ParagraphData:
    """Data structure for paragraph properties extracted from a PowerPoint paragraph."""

    def __init__(self, paragraph: Any):
        """Initialize from a PowerPoint paragraph object.

        Args:
            paragraph: The PowerPoint paragraph object
        """
        self.text: str = paragraph.text.strip()
        self.bullet, self.level = _extract_bullet_and_level(paragraph)
        self.alignment: str | None = _extract_alignment(paragraph)
        self.space_before: float | None = (
            paragraph.space_before.pt
            if hasattr(paragraph, "space_before") and paragraph.space_before
            else None
        )
        self.space_after: float | None = (
            paragraph.space_after.pt
            if hasattr(paragraph, "space_after") and paragraph.space_after
            else None
        )
        font_props = _extract_font_props(paragraph)
        self.font_name: str | None = font_props["font_name"]
        self.font_size: float | None = font_props["font_size"]
        self.bold: bool | None = font_props["bold"]
        self.italic: bool | None = font_props["italic"]
        self.underline: bool | None = font_props["underline"]
        self.color: str | None = font_props["color"]
        self.theme_color: str | None = font_props["theme_color"]
        self.line_spacing: float | None = _extract_line_spacing(paragraph, self.font_size)

    def to_dict(self) -> ParagraphDict:
        """Convert to dictionary for JSON serialization, excluding None values."""
        result: ParagraphDict = {"text": self.text}
        if self.bullet:
            result["bullet"] = self.bullet
        if self.level is not None:
            result["level"] = self.level
        if self.alignment:
            result["alignment"] = self.alignment
        if self.space_before is not None:
            result["space_before"] = self.space_before
        if self.space_after is not None:
            result["space_after"] = self.space_after
        if self.font_name:
            result["font_name"] = self.font_name
        if self.font_size is not None:
            result["font_size"] = self.font_size
        if self.bold is not None:
            result["bold"] = self.bold
        if self.italic is not None:
            result["italic"] = self.italic
        if self.underline is not None:
            result["underline"] = self.underline
        if self.color:
            result["color"] = self.color
        if self.theme_color:
            result["theme_color"] = self.theme_color
        if self.line_spacing is not None:
            result["line_spacing"] = self.line_spacing
        return result


class PresentationInventory(BaseModel):
    """Structured presentation inventory containing geometry and shapes."""

    total_slides: int
    slide_width_pt: float
    slide_height_pt: float
    slides: list[dict[str, Any]] = Field(default_factory=list)
