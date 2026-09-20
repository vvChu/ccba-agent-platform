"""Sugiyama Layered Hierarchical Layout Engine (DAG Directed Acyclic Graph)."""

from __future__ import annotations

import math
from typing import Any

from grandalf.graphs import Edge, Graph, Vertex
from grandalf.layouts import SugiyamaLayout

from ccba_diagram.geometry import sync_bound_text_translation
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


class _VertexView:
    def __init__(self, w: float = 150.0, h: float = 100.0) -> None:
        self.w = w
        self.h = h
        self.xy: tuple[float, float] = (0.0, 0.0)


def _heuristic_bind_arrows(shapes: dict[str, dict[str, Any]], arrows: list[dict[str, Any]]) -> None:
    def dist(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def center(shape: dict[str, Any]) -> tuple[float, float]:
        return (
            float(shape.get("x", 0)) + float(shape.get("width", 100)) / 2,
            float(shape.get("y", 0)) + float(shape.get("height", 100)) / 2,
        )

    shape_centers = {sid: center(s) for sid, s in shapes.items()}
    if not shape_centers:
        return

    for arr in arrows:
        pts = arr.get("points", [[0, 0], [100, 100]])
        if not pts:
            continue

        ax, ay = float(arr.get("x", 0)), float(arr.get("y", 0))
        start_pt = (ax + float(pts[0][0]), ay + float(pts[0][1]))
        end_pt = (ax + float(pts[-1][0]), ay + float(pts[-1][1]))

        sb = arr.get("startBinding")
        eb = arr.get("endBinding")

        start_id = (
            sb.get("elementId") if isinstance(sb, dict) else (sb if isinstance(sb, str) else None)
        )
        end_id = (
            eb.get("elementId") if isinstance(eb, dict) else (eb if isinstance(eb, str) else None)
        )

        if not start_id or start_id not in shapes:
            closest = min(shape_centers.keys(), key=lambda sid: dist(start_pt, shape_centers[sid]))
            arr["startBinding"] = {"elementId": closest, "focus": 0, "gap": 15}

        if not end_id or end_id not in shapes:
            closest = min(shape_centers.keys(), key=lambda sid: dist(end_pt, shape_centers[sid]))
            arr["endBinding"] = {"elementId": closest, "focus": 0, "gap": 15}


def apply_sugiyama_layout(
    elements: list[dict[str, Any]], theme: DiagramTheme = DEFAULT_THEME
) -> bool:
    """Apply Sugiyama Hierarchical Layout to the given Excalidraw elements in-place.

    Args:
        elements: List of Excalidraw element dicts.
        theme: Styling and ergonomics theme.

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

    _heuristic_bind_arrows(shapes, arrows)
    vertices = []
    vertex_map = {}

    for sid, shape in shapes.items():
        v = Vertex(sid)
        v.view = _VertexView(w=float(shape.get("width", 150)), h=float(shape.get("height", 100)))
        vertices.append(v)
        vertex_map[sid] = v

    edges = []
    for arr in arrows:
        sb = arr.get("startBinding")
        eb = arr.get("endBinding")

        start_id = (
            sb.get("elementId") if isinstance(sb, dict) else (sb if isinstance(sb, str) else None)
        )
        end_id = (
            eb.get("elementId") if isinstance(eb, dict) else (eb if isinstance(eb, str) else None)
        )

        if start_id in shapes and end_id in shapes:
            e = Edge(vertex_map[start_id], vertex_map[end_id])
            edges.append(e)

            if not isinstance(sb, dict):
                arr["startBinding"] = {"elementId": start_id, "focus": 0, "gap": 15}
            if not isinstance(eb, dict):
                arr["endBinding"] = {"elementId": end_id, "focus": 0, "gap": 15}

    g = Graph(vertices, edges)

    # Run Sugiyama for each connected component
    current_y_offset = 100.0
    for c in g.C:
        sug = SugiyamaLayout(c)
        sug.init_all()
        sug.xspace = 120.0
        sug.yspace = 100.0
        sug.draw()

        for v in c.sV:
            if not hasattr(v.view, "xy"):
                v.view.xy = (0.0, 0.0)

        min_x = min(v.view.xy[0] - v.view.w / 2 for v in c.sV)
        min_y = min(v.view.xy[1] - v.view.h / 2 for v in c.sV)
        max_y = max(v.view.xy[1] + v.view.h / 2 for v in c.sV)

        for v in c.sV:
            shifted_cx = v.view.xy[0] - min_x + 100.0
            shifted_cy = v.view.xy[1] - min_y + current_y_offset

            shape = shapes[v.data]
            old_x = float(shape.get("x", 0.0))
            old_y = float(shape.get("y", 0.0))

            new_x = shifted_cx - v.view.w / 2
            new_y = shifted_cy - v.view.h / 2

            dx = new_x - old_x
            dy = new_y - old_y

            shape["x"] = float(new_x)
            shape["y"] = float(new_y)
            shape["roughness"] = 0
            if shape.get("type") == "rectangle" and "roundness" not in shape:
                shape["roundness"] = {"type": 3}

            cur_stroke = shape.get("strokeColor", "")
            if cur_stroke in ("", "#000000", "#0f172a"):
                shape["strokeColor"] = theme.stroke_color
            cur_bg = shape.get("backgroundColor", "")
            if cur_bg in ("", "transparent"):
                shape["backgroundColor"] = theme.background_color

            sync_bound_text_translation(shape, elements, dx, dy, theme=theme)

        current_y_offset += (max_y - min_y) + 100.0

    # Orthogonal elbow routing for arrows
    for arr in arrows:
        sb = arr.get("startBinding")
        eb = arr.get("endBinding")
        start_id = (
            sb.get("elementId") if isinstance(sb, dict) else (sb if isinstance(sb, str) else None)
        )
        end_id = (
            eb.get("elementId") if isinstance(eb, dict) else (eb if isinstance(eb, str) else None)
        )

        if start_id in shapes and end_id in shapes:
            s_shape = shapes[start_id]
            e_shape = shapes[end_id]

            sx = float(s_shape["x"] + float(s_shape.get("width", 100)) / 2)
            sy = float(s_shape["y"] + float(s_shape.get("height", 100)) + 5)

            ex = float(e_shape["x"] + float(e_shape.get("width", 100)) / 2)
            ey = float(e_shape["y"] - 5)

            arr["x"] = sx
            arr["y"] = sy

            dx = ex - sx
            dy = ey - sy

            mid_y = dy / 2
            arr["points"] = [
                [0.0, 0.0],
                [0.0, float(mid_y)],
                [float(dx), float(mid_y)],
                [float(dx), float(dy)],
            ]
            arr["roughness"] = 0
            arr["strokeColor"] = theme.stroke_color
            arr["roundness"] = {"type": 3}

    return True
