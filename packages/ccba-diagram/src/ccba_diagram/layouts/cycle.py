"""Cycle Layout Engine (Circular Closed Feedback Loop)."""

from __future__ import annotations

import math
from typing import Any

import networkx as nx

from ccba_diagram.geometry import (
    compute_safe_arrow_endpoints,
    normalize_canvas_bounding_box,
    sync_bound_text_translation,
)
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


def apply_cycle_layout(
    elements: list[dict[str, Any]],
    theme: DiagramTheme = DEFAULT_THEME,
) -> bool:
    """Apply Cycle Layout to Excalidraw elements in-place.

    Args:
        elements: List of Excalidraw element dicts.
        theme: Theme configuration.

    Returns:
        True if successfully applied, False otherwise.
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

    g = nx.DiGraph()
    for sid in shapes:
        g.add_node(sid)

    edges: list[tuple[dict[str, Any], str, str]] = []
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
            g.add_edge(start_id, end_id)
            edges.append((arr, start_id, end_id))

    if not g.nodes:
        return False

    try:
        cycles = list(nx.simple_cycles(g))
        if cycles:
            ordered_nodes = max(cycles, key=len)
            for n in g.nodes:
                if n not in ordered_nodes:
                    ordered_nodes.append(n)
        else:
            ordered_nodes = list(g.nodes)
    except Exception:
        ordered_nodes = list(g.nodes)

    pos: dict[str, tuple[float, float]] = {}
    center_x, center_y = 600.0, 400.0
    n = len(ordered_nodes)

    if n > 0:
        radius = max(250.0, n * 60.0)
        angle_step = 2.0 * math.pi / n
        for i, nid in enumerate(ordered_nodes):
            angle = i * angle_step - math.pi / 2.0
            pos[nid] = (
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            )

    # 1. Update shape positions and aesthetics
    for sid, (x, y) in pos.items():
        shape = shapes[sid]
        old_x = float(shape.get("x", 0.0))
        old_y = float(shape.get("y", 0.0))
        shape_w = float(shape.get("width", 150.0))
        shape_h = float(shape.get("height", 100.0))

        new_x = x - shape_w / 2.0
        new_y = y - shape_h / 2.0
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

    # 2. Update arrows geometrically with outward curved path
    for arr, sid, eid in edges:
        s_shape = shapes[sid]
        e_shape = shapes[eid]
        start_x, start_y, end_x, end_y = compute_safe_arrow_endpoints(s_shape, e_shape)

        mx = (start_x + end_x) / 2.0
        my = (start_y + end_y) / 2.0

        v_cx = mx - center_x
        v_cy = my - center_y
        v_dist = math.hypot(v_cx, v_cy)
        if v_dist > 0:
            push_amount = 50.0
            mx = mx + (v_cx / v_dist) * push_amount
            my = my + (v_cy / v_dist) * push_amount

        arr["x"] = float(start_x)
        arr["y"] = float(start_y)
        arr["points"] = [
            [0.0, 0.0],
            [float(mx - start_x), float(my - start_y)],
            [float(end_x - start_x), float(end_y - start_y)],
        ]
        arr["roughness"] = 0
        arr["strokeColor"] = theme.stroke_color
        arr["strokeWidth"] = theme.stroke_width
        arr["roundness"] = {"type": 2}
        if arr.get("strokeStyle") != "dashed":
            arr["strokeStyle"] = "solid"
        if not arr.get("endArrowhead") and not arr.get("startArrowhead"):
            arr["endArrowhead"] = "arrow"

    normalize_canvas_bounding_box(elements, min_padding_x=80.0, min_padding_y=60.0)
    return True
