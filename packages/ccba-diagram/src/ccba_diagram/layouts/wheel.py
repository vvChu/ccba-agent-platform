"""Wheel / Star-Cycle Layout Engine.

Positions a central hub with surrounding outer nodes in a circular cycle,
connecting the cycle nodes clockwise with curved outward arrows, and connecting
spokes to/from the center hub with straight lines.
"""

from __future__ import annotations

import math
from typing import Any

import networkx as nx

from ccba_diagram.geometry import (
    compute_safe_arrow_endpoints,
    get_shape_boundary_point,
    normalize_canvas_bounding_box,
    sync_bound_text_translation,
)
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


def _find_wheel_components(
    shapes: dict[str, dict[str, Any]],
    arrows: list[dict[str, Any]],
    center_y: float = 400.0,
) -> tuple[
    str | None,
    list[str],
    list[tuple[dict[str, Any], str, str]],
    nx.DiGraph,
    nx.Graph,
    list[str],
    list[str],
]:
    """Extract graph edges, hub node, outer cycle nodes, header banners, and auxiliary shapes."""
    g_dir = nx.DiGraph()
    g_undir = nx.Graph()
    for sid in shapes:
        g_dir.add_node(sid)
        g_undir.add_node(sid)

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
            g_dir.add_edge(start_id, end_id)
            g_undir.add_edge(start_id, end_id)
            edges.append((arr, start_id, end_id))

    if not g_undir.nodes:
        return None, [], edges, g_dir, g_undir, [], []

    # Detect Header Banner shapes: degree == 0, width >= 600, upper half of canvas (y <= center_y)
    header_ids = [
        sid
        for sid, s in shapes.items()
        if g_undir.degree(sid) == 0
        and float(s.get("width", 0.0)) >= 600.0
        and float(s.get("y", 0.0)) <= center_y
    ]

    active_shape_ids = [sid for sid in shapes if sid not in header_ids]
    if not active_shape_ids:
        return None, [], edges, g_dir, g_undir, header_ids, []

    # Separate connected shapes from unattached auxiliary shapes (e.g. badges, annotations)
    connected_shape_ids = [sid for sid in active_shape_ids if g_undir.degree(sid) > 0]
    aux_shape_ids = [sid for sid in active_shape_ids if g_undir.degree(sid) == 0]

    # Fallback to all active shapes if graph has no edges at all yet
    eval_shape_ids = connected_shape_ids if connected_shape_ids else active_shape_ids

    degrees = dict(g_undir.degree(eval_shape_ids))
    if not degrees:
        return None, [], edges, g_dir, g_undir, header_ids, aux_shape_ids

    hub_id = max(
        degrees,
        key=lambda n: (
            degrees[n],
            1 if any(k in n.lower() for k in ("hub", "core", "center")) else 0,
        ),
    )
    outer_nodes = [nid for nid in eval_shape_ids if nid != hub_id]
    return hub_id, outer_nodes, edges, g_dir, g_undir, header_ids, aux_shape_ids


def _order_outer_nodes(
    outer_nodes: list[str],
    g_dir: nx.DiGraph,
    g_undir: nx.Graph,
) -> list[str]:
    """Order outer nodes along the cycle path, normalized to begin at outer_nodes[0]."""
    if len(outer_nodes) <= 1:
        return list(outer_nodes)

    sub_dir = g_dir.subgraph(outer_nodes)
    try:
        cycles = list(nx.simple_cycles(sub_dir))
        if cycles:
            longest = max(cycles, key=len)
            if outer_nodes and outer_nodes[0] in longest:
                idx = longest.index(outer_nodes[0])
                longest = longest[idx:] + longest[:idx]
            return longest + [n for n in outer_nodes if n not in longest]
    except Exception:
        pass

    sub_undir = g_undir.subgraph(outer_nodes)
    try:
        basis = nx.cycle_basis(sub_undir)
        if basis:
            longest = max(basis, key=len)
            if outer_nodes and outer_nodes[0] in longest:
                idx = longest.index(outer_nodes[0])
                longest = longest[idx:] + longest[:idx]
            if len(longest) >= 3:
                fwd = sum(
                    1
                    for i in range(len(longest))
                    if g_dir.has_edge(longest[i], longest[(i + 1) % len(longest)])
                )
                bwd = sum(
                    1
                    for i in range(len(longest))
                    if g_dir.has_edge(longest[(i + 1) % len(longest)], longest[i])
                )
                if bwd > fwd:
                    longest = [longest[0]] + longest[:0:-1]
            return longest + [n for n in outer_nodes if n not in longest]
    except Exception:
        pass

    return list(outer_nodes)


def _position_shapes(
    shapes: dict[str, dict[str, Any]],
    pos: dict[str, tuple[float, float]],
    elements: list[dict[str, Any]],
    hub_id: str,
    theme: DiagramTheme = DEFAULT_THEME,
) -> None:
    """Update shape positions and apply executive styling."""
    for sid, (x, y) in pos.items():
        shape = shapes[sid]
        old_x = shape.get("x", 0.0)
        old_y = shape.get("y", 0.0)
        sw = shape.get("width", 150.0)
        sh = shape.get("height", 100.0)

        new_x = float(x - sw / 2.0)
        new_y = float(y - sh / 2.0)
        dx = new_x - old_x
        dy = new_y - old_y

        shape["x"] = new_x
        shape["y"] = new_y
        shape["roughness"] = 0
        shape["backgroundColor"] = theme.hub_background if sid == hub_id else theme.background_color
        shape["strokeColor"] = theme.hub_stroke_color if sid == hub_id else theme.stroke_color
        shape["strokeWidth"] = theme.hub_stroke_width if sid == hub_id else theme.stroke_width
        shape["fillStyle"] = "solid"

        sync_bound_text_translation(shape, elements, dx, dy, theme=theme)


def _route_arrows(
    edges: list[tuple[dict[str, Any], str, str]],
    shapes: dict[str, dict[str, Any]],
    hub_id: str,
    center_x: float,
    center_y: float,
    theme: DiagramTheme = DEFAULT_THEME,
) -> None:
    """Route cycle and spoke arrows with boundary clipping and curvature."""
    for arr, sid, eid in edges:
        s_shape = shapes[sid]
        e_shape = shapes[eid]
        start_x, start_y, end_x, end_y = compute_safe_arrow_endpoints(s_shape, e_shape)

        arr["x"] = float(start_x)
        arr["y"] = float(start_y)
        arr["roughness"] = 0
        if not arr.get("strokeColor"):
            arr["strokeColor"] = theme.stroke_color
        if not arr.get("strokeWidth"):
            arr["strokeWidth"] = theme.stroke_width
        if not arr.get("endArrowhead") and not arr.get("startArrowhead"):
            arr["endArrowhead"] = "arrow"

        is_cycle_edge = sid != hub_id and eid != hub_id
        if is_cycle_edge:
            mx = (start_x + end_x) / 2.0
            my = (start_y + end_y) / 2.0
            v_cx = mx - center_x
            v_cy = my - center_y
            v_dist = math.hypot(v_cx, v_cy)
            if v_dist > 0:
                mx += (v_cx / v_dist) * 40.0
                my += (v_cy / v_dist) * 40.0
            arr["points"] = [
                [0.0, 0.0],
                [float(mx - start_x), float(my - start_y)],
                [float(end_x - start_x), float(end_y - start_y)],
            ]
            arr["roundness"] = {"type": 2}
            if arr.get("strokeStyle") != "dashed":
                arr["strokeStyle"] = "solid"
        else:
            arr["points"] = [
                [0.0, 0.0],
                [float(end_x - start_x), float(end_y - start_y)],
            ]
            arr["roundness"] = None


def apply_wheel_layout(
    elements: list[dict[str, Any]],
    center_x: float = 600.0,
    center_y: float = 400.0,
    radius: float | None = None,
    theme: DiagramTheme = DEFAULT_THEME,
) -> bool:
    """Apply Wheel / Star-Cycle layout to Excalidraw elements in-place.

    Center hub is positioned at (center_x, center_y), and outer nodes form a
    circular cycle around it at radius R.
    """
    shapes: dict[str, dict[str, Any]] = {}
    arrows: list[dict[str, Any]] = []
    for el in elements:
        t = el.get("type")
        if t in ("rectangle", "ellipse", "diamond"):
            shapes[el["id"]] = el
        elif t == "arrow":
            arrows.append(el)

    if len(shapes) < 2:
        return False

    hub_id, outer_nodes, edges, g_dir, g_undir, header_ids, aux_shape_ids = _find_wheel_components(
        shapes, arrows, center_y
    )
    if not hub_id or not outer_nodes:
        return False

    # Anchor header banners at safe top coordinate y = 30
    for hid in header_ids:
        h_shape = shapes[hid]
        old_y = float(h_shape.get("y", 0.0))
        new_y = 30.0
        dy = new_y - old_y
        h_shape["y"] = new_y
        h_shape["roughness"] = 0
        h_shape["backgroundColor"] = theme.banner_background
        h_shape["strokeColor"] = theme.banner_stroke_color
        h_shape["fillStyle"] = "solid"
        sync_bound_text_translation(h_shape, elements, 0.0, dy, theme=theme)

    ordered_nodes = _order_outer_nodes(outer_nodes, g_dir, g_undir)
    n = len(ordered_nodes)
    angle_step = 2.0 * math.pi / n

    if radius is not None:
        r = radius
    else:
        min_clearance = 70.0
        hub_shape = shapes[hub_id]
        r_candidates = [max(260.0, len(ordered_nodes) * 55.0)]
        for i, nid in enumerate(ordered_nodes):
            angle = i * angle_step - math.pi / 2.0
            dx_ray = math.cos(angle)
            dy_ray = math.sin(angle)
            h_bx, h_by = get_shape_boundary_point(hub_shape, dx_ray, dy_ray)
            h_cx = float(hub_shape.get("x", 0.0)) + float(hub_shape.get("width", 150.0)) / 2.0
            h_cy = float(hub_shape.get("y", 0.0)) + float(hub_shape.get("height", 100.0)) / 2.0
            hub_reach = math.hypot(h_bx - h_cx, h_by - h_cy)

            n_shape = shapes[nid]
            n_bx, n_by = get_shape_boundary_point(n_shape, -dx_ray, -dy_ray)
            n_cx = float(n_shape.get("x", 0.0)) + float(n_shape.get("width", 150.0)) / 2.0
            n_cy = float(n_shape.get("y", 0.0)) + float(n_shape.get("height", 100.0)) / 2.0
            node_reach = math.hypot(n_bx - n_cx, n_by - n_cy)

            r_candidates.append(hub_reach + node_reach + min_clearance)
        r = max(r_candidates)

    dy_wheel = 0.0
    if header_ids:
        tentative_min_y = min(
            center_y - float(shapes[hub_id].get("height", 100.0)) / 2.0,
            *(
                (center_y + r * math.sin(i * angle_step - math.pi / 2.0))
                - float(shapes[nid].get("height", 100.0)) / 2.0
                for i, nid in enumerate(ordered_nodes)
            ),
        )
        if tentative_min_y < 120.0:
            dy_wheel = 120.0 - tentative_min_y
            center_y += dy_wheel

    if dy_wheel > 0.0 and aux_shape_ids:
        for aid in aux_shape_ids:
            a_shape = shapes[aid]
            a_shape["y"] = float(a_shape.get("y", 0.0)) + dy_wheel
            sync_bound_text_translation(a_shape, elements, 0.0, dy_wheel, theme=theme)

    pos: dict[str, tuple[float, float]] = {hub_id: (center_x, center_y)}
    for i, nid in enumerate(ordered_nodes):
        angle = i * angle_step - math.pi / 2.0
        pos[nid] = (
            center_x + r * math.cos(angle),
            center_y + r * math.sin(angle),
        )

    _position_shapes(shapes, pos, elements, hub_id, theme=theme)
    _route_arrows(edges, shapes, hub_id, center_x, center_y, theme=theme)

    min_pad_y = 30.0 if header_ids else 60.0
    normalize_canvas_bounding_box(elements, min_padding_x=80.0, min_padding_y=min_pad_y)

    return True
