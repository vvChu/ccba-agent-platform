"""Tree Layout Engine (Top-Down or Left-to-Right Hierarchical Tree)."""

from __future__ import annotations

from typing import Any

import networkx as nx

from ccba_diagram.geometry import (
    compute_safe_arrow_endpoints,
    sync_bound_text_translation,
)
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


def apply_tree_layout(
    elements: list[dict[str, Any]],
    direction: str = "td",
    theme: DiagramTheme = DEFAULT_THEME,
) -> bool:
    """Apply a clean Hierarchical Tree Layout to Excalidraw elements in-place.

    Args:
        elements: List of Excalidraw element dicts.
        direction: 'td' (Top-Down) or 'lr' (Left-to-Right).
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

    # Build NetworkX DiGraph to analyze hierarchy
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

    # 1. Auto-detect Root Node
    roots = [n for n, d in g.in_degree() if d == 0]
    if len(roots) == 1:
        root_id = roots[0]
    elif len(roots) > 1:
        root_id = max(roots, key=g.out_degree)
    else:
        degrees = dict(g.degree())
        root_id = max(degrees, key=degrees.get) if degrees else list(g.nodes)[0]

    # 2. Build Spanning Tree using BFS from Root
    tree_edges = list(nx.bfs_edges(g, root_id))
    t_tree = nx.DiGraph()
    t_tree.add_node(root_id)
    t_tree.add_edges_from(tree_edges)

    for n in g.nodes:
        if n not in t_tree:
            t_tree.add_node(n)
            t_tree.add_edge(root_id, n)

    # 3. Calculate tree structure properties
    depths = nx.single_source_shortest_path_length(t_tree, root_id)

    leaf_counts: dict[str, int] = {}

    def compute_leaves(node: str) -> int:
        children = list(t_tree.successors(node))
        if not children:
            leaf_counts[node] = 1
            return 1
        count = sum(compute_leaves(c) for c in children)
        leaf_counts[node] = count
        return count

    compute_leaves(root_id)

    # 4. Position calculation using leaf-based distribution
    pos: dict[str, tuple[float, float]] = {}
    current_leaf_index = 0
    leaf_spacing = 180.0
    level_spacing = 180.0
    start_x, start_y = 600.0, 100.0

    def layout_node(node: str) -> None:
        nonlocal current_leaf_index
        children = list(t_tree.successors(node))
        depth = depths[node]

        if not children:
            coord = current_leaf_index * leaf_spacing
            current_leaf_index += 1
            if direction == "td":
                pos[node] = (coord, start_y + depth * level_spacing)
            else:
                pos[node] = (start_x + depth * level_spacing, coord)
        else:
            for c in children:
                layout_node(c)

            child_coords = [pos[c][0] if direction == "td" else pos[c][1] for c in children]
            avg_coord = sum(child_coords) / len(child_coords)

            if direction == "td":
                pos[node] = (avg_coord, start_y + depth * level_spacing)
            else:
                pos[node] = (start_x + depth * level_spacing, avg_coord)

    layout_node(root_id)

    # Shift coordinate system
    all_x = [p[0] for p in pos.values()]
    all_y = [p[1] for p in pos.values()]
    min_x = min(all_x) if all_x else 0.0
    min_y = min(all_y) if all_y else 0.0

    target_start_x = 100.0 if direction == "td" else 150.0
    target_start_y = 100.0
    shift_x = target_start_x - min_x
    shift_y = target_start_y - min_y

    for nid in pos:
        pos[nid] = (pos[nid][0] + shift_x, pos[nid][1] + shift_y)

    # 5. Apply shape coordinate mutations
    for sid, (cx, cy) in pos.items():
        shape = shapes[sid]
        old_x = float(shape.get("x", 0.0))
        old_y = float(shape.get("y", 0.0))
        shape_w = float(shape.get("width", 150.0))
        shape_h = float(shape.get("height", 100.0))

        new_x = cx - shape_w / 2.0
        new_y = cy - shape_h / 2.0
        dx = new_x - old_x
        dy = new_y - old_y

        shape["x"] = float(new_x)
        shape["y"] = float(new_y)
        shape["roughness"] = 0
        shape["backgroundColor"] = (
            theme.hub_background if sid == root_id else theme.background_color
        )
        shape["strokeColor"] = theme.hub_stroke_color if sid == root_id else theme.stroke_color
        shape["strokeWidth"] = theme.hub_stroke_width if sid == root_id else theme.stroke_width
        shape["fillStyle"] = "solid"

        if shape.get("type") == "rectangle" and "roundness" not in shape:
            shape["roundness"] = {"type": 3}

        sync_bound_text_translation(shape, elements, dx, dy, theme=theme)

    # 6. Apply Orthogonal Connectors to Spanning Tree arrows
    for arr, sid, eid in edges:
        is_tree_edge = t_tree.has_edge(sid, eid)
        s_shape = shapes[sid]
        e_shape = shapes[eid]
        s_w = float(s_shape.get("width", 150.0))
        s_h = float(s_shape.get("height", 100.0))
        e_w = float(e_shape.get("width", 150.0))
        e_h = float(e_shape.get("height", 100.0))

        if is_tree_edge:
            if direction == "td":
                start_x = float(s_shape["x"] + s_w / 2.0)
                start_y = float(s_shape["y"] + s_h + 5.0)
                end_x = float(e_shape["x"] + e_w / 2.0)
                end_y = float(e_shape["y"] - 5.0)

                arr["x"] = start_x
                arr["y"] = start_y
                dx = end_x - start_x
                dy = end_y - start_y
                mid_y = dy / 2.0
                arr["points"] = [
                    [0.0, 0.0],
                    [0.0, float(mid_y)],
                    [float(dx), float(mid_y)],
                    [float(dx), float(dy)],
                ]
            else:
                start_x = float(s_shape["x"] + s_w + 5.0)
                start_y = float(s_shape["y"] + s_h / 2.0)
                end_x = float(e_shape["x"] - 5.0)
                end_y = float(e_shape["y"] + e_h / 2.0)

                arr["x"] = start_x
                arr["y"] = start_y
                dx = end_x - start_x
                dy = end_y - start_y
                mid_x = dx / 2.0
                arr["points"] = [
                    [0.0, 0.0],
                    [float(mid_x), 0.0],
                    [float(mid_x), float(dy)],
                    [float(dx), float(dy)],
                ]
            arr["roundness"] = {"type": 3}
        else:
            start_x, start_y, end_x, end_y = compute_safe_arrow_endpoints(s_shape, e_shape)
            arr["x"] = start_x
            arr["y"] = start_y
            arr["points"] = [[0.0, 0.0], [float(end_x - start_x), float(end_y - start_y)]]
            arr["strokeStyle"] = "dashed"

        arr["roughness"] = 0
        arr["strokeColor"] = theme.stroke_color
        arr["strokeWidth"] = theme.stroke_width

    return True
