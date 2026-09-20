"""Value Chain Layout Engine (Michael Porter's Value Chain & Pipeline)."""

from __future__ import annotations

from typing import Any

import networkx as nx

from ccba_diagram.geometry import (
    compute_safe_arrow_endpoints,
    normalize_canvas_bounding_box,
    sync_bound_text_translation,
)
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


def _node_has_margin_keyword(shape: dict[str, Any], elements: list[dict[str, Any]]) -> bool:
    """Check if a shape or its bound text contains margin-related keywords."""
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
    combined = " ".join(texts).lower()
    keywords = ["margin", "profit", "biên lợi nhuận"]
    return any(kw in combined for kw in keywords)


def apply_value_chain_layout(
    elements: list[dict[str, Any]],
    theme: DiagramTheme = DEFAULT_THEME,
) -> bool:
    """Apply Michael Porter's Value Chain Layout to Excalidraw elements in-place.

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

    # 1. Identify Primary Chain (Longest Path in DAG)
    primary_chain = []
    try:
        if nx.is_directed_acyclic_graph(g):
            primary_chain = nx.dag_longest_path(g)
        else:
            primary_chain = list(nx.topological_sort(g))
    except Exception:
        degrees = dict(g.out_degree())
        primary_chain = sorted(degrees, key=degrees.get, reverse=True)

    # 2. Support Activities
    support_activities = [n for n in g.nodes if n not in primary_chain]

    margin_id = None
    if primary_chain and g.out_degree(primary_chain[-1]) == 0 and len(primary_chain) > 1:
        candidate = primary_chain[-1]
        if len(primary_chain) >= 3 and _node_has_margin_keyword(shapes[candidate], elements):
            margin_id = candidate
            primary_chain = primary_chain[:-1]

    pos: dict[str, tuple[float, float]] = {}
    start_x = 150.0
    primary_y = 520.0
    support_y = 300.0
    step_x = 220.0

    for idx, nid in enumerate(primary_chain):
        pos[nid] = (start_x + idx * step_x, primary_y)

    n_support = len(support_activities)
    if n_support > 0:
        max_primary_x = start_x + max(0, len(primary_chain) - 1) * step_x
        span_width = max_primary_x - start_x

        if n_support == 1:
            pos[support_activities[0]] = (start_x + span_width / 2.0, support_y)
        else:
            support_step = span_width / (n_support - 1) if n_support > 1 else step_x
            for idx, nid in enumerate(support_activities):
                pos[nid] = (start_x + idx * support_step, support_y)

    if margin_id:
        last_primary_x = start_x + len(primary_chain) * step_x
        pos[margin_id] = (last_primary_x + 50.0, primary_y)

    # 3. Update shape coordinates and aesthetics
    for sid, (cx, cy) in pos.items():
        shape = shapes[sid]
        old_x = float(shape.get("x", 0.0))
        old_y = float(shape.get("y", 0.0))
        shape_w = float(shape.get("width", 150.0))
        shape_h = float(shape.get("height", 100.0))

        if sid == margin_id:
            shape["type"] = "diamond"
            shape_w = max(shape_w, 120.0)
            shape_h = max(shape_h, 120.0)
            shape["width"] = shape_w
            shape["height"] = shape_h

        new_x = cx - shape_w / 2.0
        new_y = cy - shape_h / 2.0
        dx = new_x - old_x
        dy = new_y - old_y

        shape["x"] = float(new_x)
        shape["y"] = float(new_y)
        shape["roughness"] = 0
        shape["backgroundColor"] = theme.background_color
        shape["strokeColor"] = theme.stroke_color
        shape["strokeWidth"] = theme.stroke_width
        shape["fillStyle"] = "solid"

        if sid in primary_chain:
            shape["strokeWidth"] = 2
            if shape.get("type") == "rectangle" and "roundness" not in shape:
                shape["roundness"] = {"type": 3}
        elif sid in support_activities:
            shape["strokeWidth"] = 1.5
            shape["strokeStyle"] = "dashed"

        sync_bound_text_translation(shape, elements, dx, dy, theme=theme)

    # 4. Update arrow geometry
    for arr, sid, eid in edges:
        s_shape = shapes[sid]
        e_shape = shapes[eid]
        s_h = float(s_shape.get("height", 100.0))
        s_is_support = sid in support_activities
        e_is_primary = eid in primary_chain

        sx = float(s_shape["x"] + float(s_shape.get("width", 150.0)) / 2.0)

        if s_is_support and e_is_primary:
            gap = float(e_shape["y"] - (s_shape["y"] + s_h))
            pad = min(5.0, (gap - 2.0) / 2.0) if gap > 12.0 else 0.0
            start_x = sx
            start_y = float(s_shape["y"] + s_h + pad)
            end_y = float(e_shape["y"] - pad)

            arr["x"] = start_x
            arr["y"] = start_y
            arr["points"] = [[0.0, 0.0], [0.0, float(end_y - start_y)]]
            arr["strokeStyle"] = "dashed"
        else:
            start_x, start_y, end_x, end_y = compute_safe_arrow_endpoints(s_shape, e_shape)
            arr["x"] = start_x
            arr["y"] = start_y
            arr["points"] = [[0.0, 0.0], [float(end_x - start_x), float(end_y - start_y)]]
            arr["strokeStyle"] = "solid"

        arr["roughness"] = 0
        arr["strokeColor"] = theme.stroke_color
        arr["strokeWidth"] = theme.stroke_width
        if not arr.get("endArrowhead") and not arr.get("startArrowhead"):
            arr["endArrowhead"] = "arrow"

    normalize_canvas_bounding_box(elements, min_padding_x=80.0, min_padding_y=60.0)
    return True
