"""Matrix / 2x2 Quadrant Grid Layout Engine."""

from __future__ import annotations

import uuid
from typing import Any

from ccba_diagram.geometry import (
    compute_safe_arrow_endpoints,
    sync_bound_text_translation,
)
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


def _get_shape_text(shape: dict[str, Any], elements: list[dict[str, Any]]) -> str:
    """Retrieve all text associated with a shape."""
    texts = []
    if shape.get("text"):
        texts.append(str(shape["text"]))
    sid = shape.get("id")
    for bound in shape.get("boundElements", []):
        if isinstance(bound, dict) and bound.get("type") == "text":
            tid = bound.get("id")
            for el in elements:
                if el.get("id") == tid and el.get("text"):
                    texts.append(str(el["text"]))
    for el in elements:
        if el.get("type") == "text" and el.get("containerId") == sid and el.get("text"):
            texts.append(str(el["text"]))
    return " ".join(texts).lower()


def _assign_quadrants(
    shape_ids: list[str],
    shapes: dict[str, dict[str, Any]],
    elements: list[dict[str, Any]],
) -> dict[str, int]:
    """Map each shape ID to a quadrant index (0: TL, 1: TR, 2: BL, 3: BR)."""
    assigned: dict[str, int] = {}
    remaining = list(shape_ids)

    # 1. Keyword-based matching
    kw_quadrants = {
        0: ["top_left", "high_left", "goc 2", "góc 2", "q2", "quadrant 2", "tl"],
        1: ["top_right", "high_right", "goc 4", "góc 4", "q4", "quadrant 4", "tr"],
        2: ["bot_left", "bottom_left", "low_left", "goc 1", "góc 1", "q1", "quadrant 1", "bl"],
        3: ["bot_right", "bottom_right", "low_right", "goc 3", "góc 3", "q3", "quadrant 3", "br"],
    }
    for sid in list(remaining):
        s_text = f"{sid.lower()} {_get_shape_text(shapes[sid], elements)}"
        for q_idx, kws in kw_quadrants.items():
            if any(kw in s_text for kw in kws):
                if q_idx not in assigned.values():
                    assigned[sid] = q_idx
                    remaining.remove(sid)
                    break

    # 2. Position-based matching if coordinates are distinct
    if remaining:
        xs = [shapes[sid].get("x", 0.0) for sid in shape_ids]
        ys = [shapes[sid].get("y", 0.0) for sid in shape_ids]
        if max(xs) - min(xs) > 30 or max(ys) - min(ys) > 30:
            avg_x = sum(xs) / len(xs)
            avg_y = sum(ys) / len(ys)
            for sid in list(remaining):
                col = 0 if shapes[sid].get("x", 0.0) < avg_x else 1
                row = 0 if shapes[sid].get("y", 0.0) < avg_y else 1
                q_idx = row * 2 + col
                if q_idx not in assigned.values():
                    assigned[sid] = q_idx
                    remaining.remove(sid)

    # 3. Sequential fallback for any remaining nodes
    available_slots = [q for q in range(max(4, len(shape_ids))) if q not in assigned.values()]
    for sid in remaining:
        slot = available_slots.pop(0) if available_slots else len(assigned)
        assigned[sid] = slot

    return assigned


def apply_matrix_layout(
    elements: list[dict[str, Any]],
    style: str = "cross",
    theme: DiagramTheme = DEFAULT_THEME,
) -> bool:
    """Apply 2x2 Matrix / Quadrant Grid Layout to Excalidraw elements in-place.

    Args:
        elements: List of Excalidraw element dicts.
        style: Divider style ('cross' for crosshair dividers, 'axis' for coordinate arrows).
        theme: Theme configuration.

    Returns:
        True if layout applied successfully, False otherwise.
    """
    shapes: dict[str, dict[str, Any]] = {}
    arrows: list[dict[str, Any]] = []

    for el in elements:
        t = el.get("type")
        if t in ("rectangle", "ellipse", "diamond"):
            shapes[el["id"]] = el
        elif t == "arrow":
            arrows.append(el)

    if not shapes:
        return False

    cx = 600.0
    cy = 400.0
    col_offset = 180.0
    row_offset = 130.0

    slot_coords = {
        0: (cx - col_offset, cy - row_offset),  # Top-Left
        1: (cx + col_offset, cy - row_offset),  # Top-Right
        2: (cx - col_offset, cy + row_offset),  # Bottom-Left
        3: (cx + col_offset, cy + row_offset),  # Bottom-Right
    }

    quad_assignments = _assign_quadrants(list(shapes.keys()), shapes, elements)

    # 1. Update node positions and aesthetics
    for sid, q_idx in quad_assignments.items():
        shape = shapes[sid]
        target_cx, target_cy = slot_coords.get(
            q_idx,
            (
                cx + (1.0 if q_idx % 2 else -1.0) * col_offset,
                cy + (1.0 if (q_idx // 2) % 2 else -1.0) * row_offset + (q_idx // 4) * 180.0,
            ),
        )

        old_x = shape.get("x", 0.0)
        old_y = shape.get("y", 0.0)
        shape_w = shape.get("width", 150.0)
        shape_h = shape.get("height", 100.0)

        new_x = target_cx - shape_w / 2.0
        new_y = target_cy - shape_h / 2.0
        dx = new_x - old_x
        dy = new_y - old_y

        shape["x"] = float(new_x)
        shape["y"] = float(new_y)
        shape["roughness"] = 0
        shape["backgroundColor"] = theme.background_color
        shape["strokeColor"] = theme.stroke_color
        shape["strokeWidth"] = theme.stroke_width
        shape["fillStyle"] = "solid"

        sync_bound_text_translation(shape, elements, dx, dy, theme=theme)

    # 2. Draw background dividers (crosshair or axis)
    elements[:] = [
        el
        for el in elements
        if not (
            isinstance(el.get("id"), str)
            and (el["id"].startswith("matrix_") or el["id"].startswith("axis_"))
        )
    ]

    min_x = cx - col_offset - 120.0
    max_x = cx + col_offset + 120.0
    min_y = cy - row_offset - 100.0
    max_y = cy + row_offset + 100.0

    background_elements: list[dict[str, Any]] = []

    if style == "cross":
        v_line = {
            "id": f"matrix_v_{uuid.uuid4().hex[:8]}",
            "type": "arrow",
            "x": cx,
            "y": min_y,
            "width": 0,
            "height": max_y - min_y,
            "strokeColor": "#a8a29e",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "points": [[0, 0], [0, float(max_y - min_y)]],
            "startArrowhead": None,
            "endArrowhead": None,
        }
        h_line = {
            "id": f"matrix_h_{uuid.uuid4().hex[:8]}",
            "type": "arrow",
            "x": min_x,
            "y": cy,
            "width": max_x - min_x,
            "height": 0,
            "strokeColor": "#a8a29e",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "points": [[0, 0], [float(max_x - min_x), 0]],
            "startArrowhead": None,
            "endArrowhead": None,
        }
        background_elements.extend([v_line, h_line])

    elif style == "axis":
        axis_origin_x = min_x + 50.0
        axis_origin_y = max_y - 30.0
        y_axis = {
            "id": f"axis_y_{uuid.uuid4().hex[:8]}",
            "type": "arrow",
            "x": axis_origin_x,
            "y": axis_origin_y,
            "width": 0,
            "height": axis_origin_y - min_y,
            "strokeColor": theme.stroke_color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "points": [[0, 0], [0, float(-(axis_origin_y - min_y))]],
            "startArrowhead": None,
            "endArrowhead": "arrow",
        }
        x_axis = {
            "id": f"axis_x_{uuid.uuid4().hex[:8]}",
            "type": "arrow",
            "x": axis_origin_x,
            "y": axis_origin_y,
            "width": max_x - axis_origin_x,
            "height": 0,
            "strokeColor": theme.stroke_color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "points": [[0, 0], [float(max_x - axis_origin_x), 0]],
            "startArrowhead": None,
            "endArrowhead": "arrow",
        }
        background_elements.extend([y_axis, x_axis])

    elements[0:0] = background_elements

    # 3. Update arrows
    for arr in arrows:
        sb = arr.get("startBinding", {})
        eb = arr.get("endBinding", {})
        start_id = (
            sb.get("elementId") if isinstance(sb, dict) else (sb if isinstance(sb, str) else None)
        )
        end_id = (
            eb.get("elementId") if isinstance(eb, dict) else (eb if isinstance(eb, str) else None)
        )

        if start_id in shapes and end_id in shapes:
            s_shape = shapes[start_id]
            e_shape = shapes[end_id]
            start_x, start_y, end_x, end_y = compute_safe_arrow_endpoints(s_shape, e_shape)
            arr["x"] = start_x
            arr["y"] = start_y
            arr["points"] = [[0.0, 0.0], [float(end_x - start_x), float(end_y - start_y)]]

        arr["roughness"] = 0
        arr["strokeColor"] = theme.stroke_color
        if arr.get("strokeStyle") != "dashed":
            arr["strokeStyle"] = "solid"

    return True
