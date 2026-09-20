"""Geometry and mathematical utilities for Excalidraw element manipulation."""

from __future__ import annotations

import math
from typing import Any

from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


def get_shape_boundary_point(shape: dict[str, Any], dx: float, dy: float) -> tuple[float, float]:
    """Compute the exact boundary point of a shape along direction (dx, dy) from its center.

    Replaces naive radius clipping with precise ray-box and parametric ellipse intersection.

    Args:
        shape: Excalidraw element dict with x, y, width, height, type.
        dx: Direction vector component X.
        dy: Direction vector component Y.

    Returns:
        (bx, by) boundary coordinate.
    """
    cx = float(shape.get("x", 0)) + float(shape.get("width", 150)) / 2
    cy = float(shape.get("y", 0)) + float(shape.get("height", 100)) / 2
    hw = float(shape.get("width", 150)) / 2
    hh = float(shape.get("height", 100)) / 2

    dist = math.hypot(dx, dy)
    if dist == 0 or hw == 0 or hh == 0:
        return cx, cy

    ndx = dx / dist
    ndy = dy / dist

    if shape.get("type") == "ellipse":
        denom = math.sqrt((ndx / hw) ** 2 + (ndy / hh) ** 2)
        t = 1.0 / denom if denom > 0 else min(hw, hh)
    else:
        tx = hw / abs(ndx) if abs(ndx) > 1e-9 else float("inf")
        ty = hh / abs(ndy) if abs(ndy) > 1e-9 else float("inf")
        t = min(tx, ty)

    return cx + ndx * t, cy + ndy * t


def compute_safe_arrow_endpoints(
    s_shape: dict[str, Any],
    e_shape: dict[str, Any],
) -> tuple[float, float, float, float]:
    """Compute safe arrow start and end points between two shapes.

    Enforces boundary clipping and prevents inverted arrows or crushed arrowheads.

    Args:
        s_shape: Source shape dict.
        e_shape: Target shape dict.

    Returns:
        (start_x, start_y, end_x, end_y) coordinates.
    """
    scx = float(s_shape.get("x", 0)) + float(s_shape.get("width", 150)) / 2
    scy = float(s_shape.get("y", 0)) + float(s_shape.get("height", 100)) / 2
    ecx = float(e_shape.get("x", 0)) + float(e_shape.get("width", 150)) / 2
    ecy = float(e_shape.get("y", 0)) + float(e_shape.get("height", 100)) / 2

    dx = ecx - scx
    dy = ecy - scy
    dist = math.hypot(dx, dy)

    if dist < 1e-5:
        return scx, scy, ecx, ecy

    # Boundary points on source and target
    sbx, sby = get_shape_boundary_point(s_shape, dx, dy)
    ebx, eby = get_shape_boundary_point(e_shape, -dx, -dy)

    # Unit direction vector
    ux = dx / dist
    uy = dy / dist

    # Gap padding
    pad = 4.0
    sx = sbx + ux * pad
    sy = sby + uy * pad
    ex = ebx - ux * pad
    ey = eby - uy * pad

    # Verify arrow is not inverted
    dot = (ex - sx) * ux + (ey - sy) * uy
    if dot <= 0:
        # Shapes overlap or are too close: fallback to center-to-center clamped
        sx = scx + ux * (min(s_shape.get("width", 150), s_shape.get("height", 100)) / 4)
        sy = scy + uy * (min(s_shape.get("width", 150), s_shape.get("height", 100)) / 4)
        ex = ecx - ux * (min(e_shape.get("width", 150), e_shape.get("height", 100)) / 4)
        ey = ecy - uy * (min(e_shape.get("width", 150), e_shape.get("height", 100)) / 4)

    return sx, sy, ex, ey


def sync_bound_text_translation(
    shape: dict[str, Any],
    elements: list[dict[str, Any]],
    dx: float,
    dy: float,
    theme: DiagramTheme = DEFAULT_THEME,
) -> None:
    """Synchronously translate bound text elements when their parent shape is moved.

    Args:
        shape: Shape element dict being translated.
        elements: Full list of diagram elements.
        dx: Horizontal displacement.
        dy: Vertical displacement.
        theme: Theme configuration for fallback stroke & font styles.
    """
    sid = shape.get("id")
    if not sid:
        return

    bound_text_ids = set()
    for bound in shape.get("boundElements", []):
        if isinstance(bound, dict) and bound.get("type") == "text" and bound.get("id"):
            bound_text_ids.add(bound["id"])

    for el in elements:
        if el.get("type") != "text":
            continue
        el_id = el.get("id")
        is_bound = (
            (el_id and el_id in bound_text_ids)
            or (el.get("containerId") == sid)
            or (el.get("containerHeaderOf") == sid)
        )
        if is_bound:
            el["x"] = float(el.get("x", 0.0) + dx)
            el["y"] = float(el.get("y", 0.0) + dy)
            if not el.get("strokeColor"):
                el["strokeColor"] = theme.stroke_color
            if not el.get("fontFamily"):
                el["fontFamily"] = theme.font_family


def normalize_canvas_bounding_box(
    elements: list[dict[str, Any]],
    min_padding_x: float = 80.0,
    min_padding_y: float = 60.0,
) -> None:
    """Shift all canvas elements into positive coordinate space if clipped.

    Accounts for shapes, text labels, and multi-point arrows.

    Args:
        elements: List of Excalidraw element dicts.
        min_padding_x: Minimum padding on X axis.
        min_padding_y: Minimum padding on Y axis.
    """
    if not elements:
        return

    min_x = float("inf")
    min_y = float("inf")

    for el in elements:
        if "x" not in el or "y" not in el:
            continue
        el_x = float(el.get("x", 0.0))
        el_y = float(el.get("y", 0.0))

        if el.get("type") == "arrow" and "points" in el:
            pts = el["points"]
            if isinstance(pts, list) and pts:
                p_xs = [
                    el_x + float(p[0]) for p in pts if isinstance(p, (list, tuple)) and len(p) >= 2
                ]
                p_ys = [
                    el_y + float(p[1]) for p in pts if isinstance(p, (list, tuple)) and len(p) >= 2
                ]
                if p_xs:
                    min_x = min(min_x, min(p_xs))
                if p_ys:
                    min_y = min(min_y, min(p_ys))
        else:
            min_x = min(min_x, el_x)
            min_y = min(min_y, el_y)

    if min_x == float("inf") or min_y == float("inf"):
        return

    shift_x = min_padding_x - min_x if min_x < min_padding_x else 0.0
    shift_y = min_padding_y - min_y if min_y < min_padding_y else 0.0

    if shift_x > 0.0 or shift_y > 0.0:
        for el in elements:
            if "x" in el:
                el["x"] = float(el.get("x", 0.0) + shift_x)
            if "y" in el:
                el["y"] = float(el.get("y", 0.0) + shift_y)
