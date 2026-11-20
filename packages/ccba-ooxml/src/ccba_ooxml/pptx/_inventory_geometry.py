"""Shape filtering, recursive position collection, sorting, and overlap detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pptx.shapes.base import BaseShape

from ._inventory_models import ShapeWithPosition

if TYPE_CHECKING:
    from ._inventory_metrics import ShapeData


def is_valid_shape(shape: BaseShape) -> bool:
    """Check if a shape contains meaningful text content."""
    if not hasattr(shape, "text_frame") or not shape.text_frame:  # type: ignore
        return False

    text = shape.text_frame.text.strip()  # type: ignore
    if not text:
        return False

    if hasattr(shape, "is_placeholder") and shape.is_placeholder:  # type: ignore
        if shape.placeholder_format and shape.placeholder_format.type:  # type: ignore
            placeholder_type = (
                str(shape.placeholder_format.type).split(".")[-1].split(" ")[0]  # type: ignore
            )
            if placeholder_type == "SLIDE_NUMBER":
                return False
            if placeholder_type == "FOOTER" and text.isdigit():
                return False

    return True


def collect_shapes_with_absolute_positions(
    shape: BaseShape, parent_left: int = 0, parent_top: int = 0
) -> list[ShapeWithPosition]:
    """Recursively collect all shapes with valid text, calculating absolute positions."""
    if hasattr(shape, "shapes"):
        result = []
        group_left = shape.left if hasattr(shape, "left") else 0
        group_top = shape.top if hasattr(shape, "top") else 0
        abs_group_left = parent_left + group_left
        abs_group_top = parent_top + group_top
        for child in shape.shapes:  # type: ignore
            result.extend(
                collect_shapes_with_absolute_positions(child, abs_group_left, abs_group_top)
            )
        return result

    if is_valid_shape(shape):
        shape_left = shape.left if hasattr(shape, "left") else 0
        shape_top = shape.top if hasattr(shape, "top") else 0
        return [
            ShapeWithPosition(
                shape=shape,
                absolute_left=parent_left + shape_left,
                absolute_top=parent_top + shape_top,
            )
        ]

    return []


def sort_shapes_by_position(shapes: list[ShapeData]) -> list[ShapeData]:
    """Sort shapes by visual position (top-to-bottom, left-to-right).

    Shapes within 0.5 inches vertically are considered on the same row.
    """
    if not shapes:
        return shapes

    shapes = sorted(shapes, key=lambda s: (s.top, s.left))
    result = []
    row = [shapes[0]]
    row_top = shapes[0].top

    for shape in shapes[1:]:
        if abs(shape.top - row_top) <= 0.5:
            row.append(shape)
        else:
            result.extend(sorted(row, key=lambda s: s.left))
            row = [shape]
            row_top = shape.top

    result.extend(sorted(row, key=lambda s: s.left))
    return result


def calculate_overlap(
    rect1: tuple[float, float, float, float],
    rect2: tuple[float, float, float, float],
    tolerance: float = 0.05,
) -> tuple[bool, float]:
    """Calculate if and how much two rectangles overlap."""
    left1, top1, w1, h1 = rect1
    left2, top2, w2, h2 = rect2

    overlap_width = min(left1 + w1, left2 + w2) - max(left1, left2)
    overlap_height = min(top1 + h1, top2 + h2) - max(top1, top2)

    if overlap_width > tolerance and overlap_height > tolerance:
        overlap_area = overlap_width * overlap_height
        return True, round(overlap_area, 2)

    return False, 0


def detect_overlaps(shapes: list[ShapeData]) -> None:
    """Detect overlapping shapes and update their overlapping_shapes dictionaries."""
    n = len(shapes)
    for i in range(n):
        for j in range(i + 1, n):
            shape1 = shapes[i]
            shape2 = shapes[j]
            assert shape1.shape_id, f"Shape at index {i} has no shape_id"
            assert shape2.shape_id, f"Shape at index {j} has no shape_id"
            rect1 = (shape1.left, shape1.top, shape1.width, shape1.height)
            rect2 = (shape2.left, shape2.top, shape2.width, shape2.height)
            overlaps, overlap_area = calculate_overlap(rect1, rect2)
            if overlaps:
                shape1.overlapping_shapes[shape2.shape_id] = overlap_area
                shape2.overlapping_shapes[shape1.shape_id] = overlap_area
