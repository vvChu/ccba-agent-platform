"""Concentric Rings Layout Engine."""

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


def apply_concentric_layout(
    elements: list[dict[str, Any]],
    theme: DiagramTheme = DEFAULT_THEME,
) -> bool:
    """Apply Concentric Ring Layout to Excalidraw elements in-place.

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

    g = nx.Graph()
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

    degrees = dict(g.degree())
    if not degrees:
        return False
    hub_id = max(degrees, key=degrees.get)

    lengths = nx.single_source_shortest_path_length(g, hub_id)
    layers: dict[int, list[str]] = {}
    for nid in g.nodes:
        dist = lengths.get(nid, 999)
        if dist not in layers:
            layers[dist] = []
        layers[dist].append(nid)

    pos: dict[str, tuple[float, float]] = {}
    center_x, center_y = 600.0, 400.0
    pos[hub_id] = (center_x, center_y)

    sorted_dists = sorted([d for d in layers.keys() if d != 999 and d > 0])
    disconnected_nodes = layers.get(999, [])

    for ring_idx, dist in enumerate(sorted_dists, 1):
        ring_nodes = layers[dist]
        if dist == sorted_dists[-1] and disconnected_nodes:
            ring_nodes.extend(disconnected_nodes)
            disconnected_nodes = []

        n = len(ring_nodes)
        if n > 0:
            radius = 200.0 + (ring_idx - 1) * 180.0
            angle_step = 2.0 * math.pi / n
            for i, nid in enumerate(ring_nodes):
                angle = i * angle_step - math.pi / 2.0
                pos[nid] = (
                    center_x + radius * math.cos(angle),
                    center_y + radius * math.sin(angle),
                )

    if disconnected_nodes:
        outer_radius = 200.0 + len(sorted_dists) * 180.0
        n = len(disconnected_nodes)
        angle_step = 2.0 * math.pi / n
        for i, nid in enumerate(disconnected_nodes):
            angle = i * angle_step - math.pi / 2.0
            pos[nid] = (
                center_x + outer_radius * math.cos(angle),
                center_y + outer_radius * math.sin(angle),
            )

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
        shape["backgroundColor"] = theme.hub_background if sid == hub_id else theme.background_color
        shape["strokeColor"] = theme.hub_stroke_color if sid == hub_id else theme.stroke_color
        shape["strokeWidth"] = theme.hub_stroke_width if sid == hub_id else theme.stroke_width
        shape["fillStyle"] = "solid"

        if sid == hub_id and shape.get("type") == "rectangle" and "roundness" not in shape:
            shape["roundness"] = {"type": 3}

        sync_bound_text_translation(shape, elements, dx, dy, theme=theme)

    for arr, sid, eid in edges:
        s_shape = shapes[sid]
        e_shape = shapes[eid]
        start_x, start_y, end_x, end_y = compute_safe_arrow_endpoints(s_shape, e_shape)

        arr["x"] = float(start_x)
        arr["y"] = float(start_y)
        arr["points"] = [[0.0, 0.0], [float(end_x - start_x), float(end_y - start_y)]]
        arr["roughness"] = 0
        arr["strokeColor"] = theme.stroke_color
        arr["strokeWidth"] = theme.stroke_width
        if not arr.get("endArrowhead") and not arr.get("startArrowhead"):
            arr["endArrowhead"] = "arrow"

    normalize_canvas_bounding_box(elements, min_padding_x=80.0, min_padding_y=60.0)
    return True
