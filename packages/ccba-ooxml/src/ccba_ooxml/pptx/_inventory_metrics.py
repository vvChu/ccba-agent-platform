"""Shape metrics, font measurement, and overflow estimation for PPTX inventory."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from pptx.shapes.base import BaseShape

from ._inventory_models import ParagraphData, ShapeDict


def _font_dirs_and_extensions() -> tuple[list[str], list[str]]:
    """Return platform-specific font search directories and file extensions."""
    if platform.system() == "Darwin":
        return (
            ["/System/Library/Fonts/", "/Library/Fonts/", "~/Library/Fonts/"],
            [".ttf", ".otf", ".ttc", ".dfont"],
        )
    return (
        ["/usr/share/fonts/truetype/", "/usr/local/share/fonts/", "~/.fonts/"],
        [".ttf", ".otf"],
    )


def _match_font_in_dir(
    font_dir_path: Path,
    font_name: str,
    font_variations: list[str],
    extensions: list[str],
) -> str | None:
    """Search a single font directory for an exact or fuzzy font file match."""
    for variant in font_variations:
        for ext in extensions:
            font_path = font_dir_path / f"{variant}{ext}"
            if font_path.exists():
                return str(font_path)
    try:
        font_name_lower = font_name.lower().replace(" ", "")
        for file_path in font_dir_path.iterdir():
            if file_path.is_file():
                file_name_lower = file_path.name.lower()
                if font_name_lower in file_name_lower and any(
                    file_name_lower.endswith(ext) for ext in extensions
                ):
                    return str(file_path)
    except (OSError, PermissionError):
        return None
    return None


def _extract_placeholder_info(shape: BaseShape, slide: Any) -> tuple[str | None, float | None]:
    """Extract placeholder type label and layout default font size."""
    if not (hasattr(shape, "is_placeholder") and shape.is_placeholder):  # type: ignore
        return None, None
    if not (shape.placeholder_format and shape.placeholder_format.type):  # type: ignore
        return None, None
    placeholder_type = str(shape.placeholder_format.type).split(".")[-1].split(" ")[0]  # type: ignore
    default_font_size = None
    if slide and hasattr(slide, "slide_layout"):
        default_font_size = ShapeData.get_default_font_size(shape, slide.slide_layout)
    return placeholder_type, default_font_size


def _extract_emu_positions(
    shape: BaseShape, absolute_left: int | None, absolute_top: int | None
) -> tuple[int, int, int, int]:
    """Extract (left, top, width, height) in EMUs using absolute offsets if given."""
    left_emu = (
        absolute_left
        if absolute_left is not None
        else (shape.left if hasattr(shape, "left") else 0)
    )
    top_emu = (
        absolute_top if absolute_top is not None else (shape.top if hasattr(shape, "top") else 0)
    )
    width_emu = shape.width if hasattr(shape, "width") else 0
    height_emu = shape.height if hasattr(shape, "height") else 0
    return left_emu, top_emu, width_emu, height_emu


def _load_pil_font(font_name: str, font_size: int) -> Any:
    """Load TrueType font via ShapeData.get_font_path or fall back to PIL default."""
    font_path = ShapeData.get_font_path(font_name)
    if font_path:
        try:
            return ImageFont.truetype(font_path, size=font_size)
        except Exception:
            return ImageFont.load_default()
    return ImageFont.load_default()


def _measure_paragraph_height_px(
    shape_data: ShapeData,
    paragraph: Any,
    usable_width_px: int,
    draw: Any,
    default_font_size: int,
    para_idx: int,
) -> float:
    """Estimate rendered pixel height for a single non-empty paragraph."""
    para_data = ParagraphData(paragraph)
    font_name = para_data.font_name or "Arial"
    font_size = int(para_data.font_size or default_font_size)
    font = _load_pil_font(font_name, font_size)

    all_wrapped_lines: list[str] = []
    for line in paragraph.text.split("\n"):
        all_wrapped_lines.extend(shape_data._wrap_text_line(line, usable_width_px, draw, font))
    if not all_wrapped_lines:
        return 0.0

    line_height_px = (
        para_data.line_spacing * 96 / 72 if para_data.line_spacing else font_size * 96 / 72
    )
    height_px = len(all_wrapped_lines) * line_height_px
    if para_idx > 0 and para_data.space_before:
        height_px += para_data.space_before * 96 / 72
    if para_data.space_after:
        height_px += para_data.space_after * 96 / 72
    return height_px


def _collect_overflow_dict(shape_data: ShapeData) -> dict[str, Any]:
    """Build nested overflow metadata dictionary for ShapeData.to_dict."""
    overflow_data: dict[str, Any] = {}
    if shape_data.frame_overflow_bottom is not None:
        overflow_data["frame"] = {"overflow_bottom": shape_data.frame_overflow_bottom}
    slide_overflow: dict[str, float] = {}
    if shape_data.slide_overflow_right is not None:
        slide_overflow["overflow_right"] = shape_data.slide_overflow_right
    if shape_data.slide_overflow_bottom is not None:
        slide_overflow["overflow_bottom"] = shape_data.slide_overflow_bottom
    if slide_overflow:
        overflow_data["slide"] = slide_overflow
    return overflow_data


class ShapeData:
    """Data structure for shape properties extracted from a PowerPoint shape."""

    @staticmethod
    def emu_to_inches(emu: int) -> float:
        """Convert EMUs (English Metric Units) to inches."""
        return emu / 914400.0

    @staticmethod
    def inches_to_pixels(inches: float, dpi: int = 96) -> int:
        """Convert inches to pixels at given DPI."""
        return int(inches * dpi)

    @staticmethod
    def get_font_path(font_name: str) -> str | None:
        """Get the font file path for a given font name."""
        font_variations = [
            font_name,
            font_name.lower(),
            font_name.replace(" ", ""),
            font_name.replace(" ", "-"),
        ]
        font_dirs, extensions = _font_dirs_and_extensions()
        for font_dir in font_dirs:
            font_dir_path = Path(font_dir).expanduser()
            if not font_dir_path.exists():
                continue
            matched = _match_font_in_dir(font_dir_path, font_name, font_variations, extensions)
            if matched:
                return matched
        return None

    @staticmethod
    def get_slide_dimensions(slide: Any) -> tuple[int | None, int | None]:
        """Get slide dimensions from slide object."""
        try:
            prs = slide.part.package.presentation_part.presentation
            return prs.slide_width, prs.slide_height
        except (AttributeError, TypeError):
            return None, None

    @staticmethod
    def get_default_font_size(shape: BaseShape, slide_layout: Any) -> float | None:
        """Extract default font size from slide layout for a placeholder shape."""
        try:
            if not hasattr(shape, "placeholder_format"):
                return None
            shape_type = shape.placeholder_format.type  # type: ignore
            for layout_placeholder in slide_layout.placeholders:
                if layout_placeholder.placeholder_format.type == shape_type:
                    for elem in layout_placeholder.element.iter():
                        if "defRPr" in elem.tag and (sz := elem.get("sz")):
                            return float(sz) / 100.0
                    break
        except Exception:
            pass
        return None

    def __init__(
        self,
        shape: BaseShape,
        absolute_left: int | None = None,
        absolute_top: int | None = None,
        slide: Any | None = None,
    ):
        """Initialize from a PowerPoint shape object."""
        self.shape = shape
        self.shape_id: str = ""
        self.slide_width_emu, self.slide_height_emu = (
            self.get_slide_dimensions(slide) if slide else (None, None)
        )
        self.placeholder_type, self.default_font_size = _extract_placeholder_info(shape, slide)
        left_emu, top_emu, width_emu, height_emu = _extract_emu_positions(
            shape, absolute_left, absolute_top
        )
        self.left: float = round(self.emu_to_inches(left_emu), 2)
        self.top: float = round(self.emu_to_inches(top_emu), 2)
        self.width: float = round(self.emu_to_inches(width_emu), 2)
        self.height: float = round(self.emu_to_inches(height_emu), 2)
        self.left_emu, self.top_emu, self.width_emu, self.height_emu = (
            left_emu,
            top_emu,
            width_emu,
            height_emu,
        )
        self.frame_overflow_bottom: float | None = None
        self.slide_overflow_right: float | None = None
        self.slide_overflow_bottom: float | None = None
        self.overlapping_shapes: dict[str, float] = {}
        self.warnings: list[str] = []
        self._estimate_frame_overflow()
        self._calculate_slide_overflow()
        self._detect_bullet_issues()

    @property
    def paragraphs(self) -> list[ParagraphData]:
        """Calculate paragraphs from the shape's text frame."""
        if not self.shape or not hasattr(self.shape, "text_frame"):
            return []
        return [
            ParagraphData(paragraph)
            for paragraph in self.shape.text_frame.paragraphs  # type: ignore
            if paragraph.text.strip()
        ]

    def _get_default_font_size(self) -> int:
        """Get default font size from theme text styles or use conservative default."""
        try:
            if not (hasattr(self.shape, "part") and hasattr(self.shape.part, "slide_layout")):
                return 14
            slide_master = self.shape.part.slide_layout.slide_master  # type: ignore
            if not hasattr(slide_master, "element"):
                return 14
            style_name = (
                "titleStyle"
                if self.placeholder_type and "TITLE" in self.placeholder_type
                else "bodyStyle"
            )
            for child in slide_master.element.iter():
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag == style_name:
                    for elem in child.iter():
                        if "sz" in elem.attrib:
                            return int(elem.attrib["sz"]) // 100
        except Exception:
            pass
        return 14

    def _get_usable_dimensions(self, text_frame: Any) -> tuple[int, int]:
        """Get usable width and height in pixels after accounting for margins."""
        margins = {"top": 0.05, "bottom": 0.05, "left": 0.1, "right": 0.1}
        if hasattr(text_frame, "margin_top") and text_frame.margin_top:
            margins["top"] = self.emu_to_inches(text_frame.margin_top)
        if hasattr(text_frame, "margin_bottom") and text_frame.margin_bottom:
            margins["bottom"] = self.emu_to_inches(text_frame.margin_bottom)
        if hasattr(text_frame, "margin_left") and text_frame.margin_left:
            margins["left"] = self.emu_to_inches(text_frame.margin_left)
        if hasattr(text_frame, "margin_right") and text_frame.margin_right:
            margins["right"] = self.emu_to_inches(text_frame.margin_right)
        usable_width = self.width - margins["left"] - margins["right"]
        usable_height = self.height - margins["top"] - margins["bottom"]
        return self.inches_to_pixels(usable_width), self.inches_to_pixels(usable_height)

    def _wrap_text_line(self, line: str, max_width_px: int, draw: Any, font: Any) -> list[str]:
        """Wrap a single line of text to fit within max_width_px."""
        if not line:
            return [""]
        if draw.textlength(line, font=font) <= max_width_px:
            return [line]
        wrapped: list[str] = []
        current_line = ""
        for word in line.split(" "):
            test_line = current_line + (" " if current_line else "") + word
            if draw.textlength(test_line, font=font) <= max_width_px:
                current_line = test_line
            else:
                if current_line:
                    wrapped.append(current_line)
                current_line = word
        if current_line:
            wrapped.append(current_line)
        return wrapped

    def _estimate_frame_overflow(self) -> None:
        """Estimate if text overflows the shape bounds using PIL text measurement."""
        if not self.shape or not hasattr(self.shape, "text_frame"):
            return
        text_frame = self.shape.text_frame  # type: ignore
        if not text_frame or not text_frame.paragraphs:
            return
        usable_width_px, usable_height_px = self._get_usable_dimensions(text_frame)
        if usable_width_px <= 0 or usable_height_px <= 0:
            return
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        default_font_size = self._get_default_font_size()
        total_height_px = 0.0
        for para_idx, paragraph in enumerate(text_frame.paragraphs):
            if paragraph.text.strip():
                total_height_px += _measure_paragraph_height_px(
                    self, paragraph, usable_width_px, draw, default_font_size, para_idx
                )
        if total_height_px > usable_height_px:
            overflow_inches = round((total_height_px - usable_height_px) / 96.0, 2)
            if overflow_inches > 0.05:
                self.frame_overflow_bottom = overflow_inches

    def _calculate_slide_overflow(self) -> None:
        """Calculate if shape overflows the slide boundaries."""
        if self.slide_width_emu is None or self.slide_height_emu is None:
            return
        right_edge_emu = self.left_emu + self.width_emu
        if right_edge_emu > self.slide_width_emu:
            overflow_inches = round(self.emu_to_inches(right_edge_emu - self.slide_width_emu), 2)
            if overflow_inches > 0.01:
                self.slide_overflow_right = overflow_inches
        bottom_edge_emu = self.top_emu + self.height_emu
        if bottom_edge_emu > self.slide_height_emu:
            overflow_inches = round(self.emu_to_inches(bottom_edge_emu - self.slide_height_emu), 2)
            if overflow_inches > 0.01:
                self.slide_overflow_bottom = overflow_inches

    def _detect_bullet_issues(self) -> None:
        """Detect bullet point formatting issues in paragraphs."""
        if not self.shape or not hasattr(self.shape, "text_frame"):
            return
        text_frame = self.shape.text_frame  # type: ignore
        if not text_frame or not text_frame.paragraphs:
            return
        bullet_symbols = ["•", "●", "○"]
        for paragraph in text_frame.paragraphs:
            text = paragraph.text.strip()
            if text and any(text.startswith(symbol + " ") for symbol in bullet_symbols):
                self.warnings.append("manual_bullet_symbol: use proper bullet formatting")
                break

    @property
    def has_any_issues(self) -> bool:
        """Check if shape has any issues (overflow, overlap, or warnings)."""
        return (
            self.frame_overflow_bottom is not None
            or self.slide_overflow_right is not None
            or self.slide_overflow_bottom is not None
            or len(self.overlapping_shapes) > 0
            or len(self.warnings) > 0
        )

    def to_dict(self) -> ShapeDict:
        """Convert to dictionary for JSON serialization."""
        result: ShapeDict = {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }
        if self.placeholder_type:
            result["placeholder_type"] = self.placeholder_type
        if self.default_font_size:
            result["default_font_size"] = self.default_font_size
        overflow_data = _collect_overflow_dict(self)
        if overflow_data:
            result["overflow"] = overflow_data
        if self.overlapping_shapes:
            result["overlap"] = {"overlapping_shapes": self.overlapping_shapes}
        if self.warnings:
            result["warnings"] = self.warnings
        result["paragraphs"] = [para.to_dict() for para in self.paragraphs]
        return result
