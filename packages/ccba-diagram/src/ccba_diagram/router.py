"""Intelligent topology analyzer and layout router."""

from __future__ import annotations

from typing import Any

import networkx as nx

from ccba_diagram.layouts.concentric import apply_concentric_layout
from ccba_diagram.layouts.cycle import apply_cycle_layout
from ccba_diagram.layouts.matrix import apply_matrix_layout
from ccba_diagram.layouts.radial import apply_radial_layout
from ccba_diagram.layouts.sugiyama import apply_sugiyama_layout
from ccba_diagram.layouts.tree import apply_tree_layout
from ccba_diagram.layouts.value_chain import apply_value_chain_layout
from ccba_diagram.layouts.wheel import apply_wheel_layout
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme


def _has_enclosing_containers(elements: list[dict[str, Any]]) -> bool:
    """Detect if diagram contains enclosing container boxes to preserve custom grouping."""
    shapes = [el for el in elements if el.get("type") in ("rectangle", "ellipse", "diamond")]
    for shape in shapes:
        sx, sy = float(shape.get("x", 0)), float(shape.get("y", 0))
        sw, sh = float(shape.get("width", 100)), float(shape.get("height", 100))
        for o in shapes:
            if o is not shape:
                ox, oy = float(o.get("x", 0)), float(o.get("y", 0))
                ow, oh = float(o.get("width", 50)), float(o.get("height", 50))
                if (
                    sx <= ox
                    and sy <= oy
                    and (sx + sw) >= (ox + ow)
                    and (sy + sh) >= (oy + oh)
                    and (sw * sh > ow * oh * 1.5)
                ):
                    return True
    return False


def apply_smart_layout(
    elements: list[dict[str, Any]],
    force_engine: str | None = None,
    theme: DiagramTheme = DEFAULT_THEME,
) -> str:
    """Analyze diagram topology and metadata to apply the optimal layout engine in-place.

    Args:
        elements: List of Excalidraw element dicts.
        force_engine: Optional engine override ('sugiyama', 'wheel', 'matrix', 'tree',
            'radial', 'concentric', 'value_chain', 'cycle').
        theme: Theme configuration.

    Returns:
        Name of the engine applied.
    """
    layout_hint = force_engine
    matrix_style = "cross"
    tree_dir = "td"
    metadata_node_id = None

    # 1. Extract metadata tags provided by LLM if not forced
    if not layout_hint:
        for el in elements:
            if el.get("type") == "text":
                txt = str(el.get("text", "")).lower()
                if "#layout:matrix" in txt:
                    layout_hint = "matrix"
                    if "#style:axis" in txt:
                        matrix_style = "axis"
                    metadata_node_id = el.get("id")
                    break
                elif "#layout:cycle" in txt:
                    layout_hint = "cycle"
                    metadata_node_id = el.get("id")
                    break
                elif (
                    "#layout:wheel" in txt
                    or "#layout:star-cycle" in txt
                    or "#layout:star_cycle" in txt
                ):
                    layout_hint = "wheel"
                    metadata_node_id = el.get("id")
                    break
                elif "#layout:radial" in txt:
                    layout_hint = "radial"
                    metadata_node_id = el.get("id")
                    break
                elif "#layout:concentric" in txt:
                    layout_hint = "concentric"
                    metadata_node_id = el.get("id")
                    break
                elif "#layout:value_chain" in txt or "#layout:value-chain" in txt:
                    layout_hint = "value_chain"
                    metadata_node_id = el.get("id")
                    break
                elif "#layout:tree" in txt:
                    layout_hint = "tree"
                    if "#dir:lr" in txt:
                        tree_dir = "lr"
                    metadata_node_id = el.get("id")
                    break
                elif "#layout:sugiyama" in txt:
                    layout_hint = "sugiyama"
                    metadata_node_id = el.get("id")
                    break

    # Strip metadata node from final diagram elements
    if metadata_node_id:
        elements[:] = [el for el in elements if el.get("id") != metadata_node_id]
        for el in elements:
            if el.get("boundElements") is not None:
                el["boundElements"] = [
                    b
                    for b in el["boundElements"]
                    if isinstance(b, dict) and b.get("id") != metadata_node_id
                ]

    # 2. Graph Topology Analysis (NetworkX fallback)
    is_wheel = False
    is_radial = False
    is_cycle = False
    is_tree = False
    is_chain = False

    if not layout_hint:
        g = nx.Graph()
        for el in elements:
            if el.get("type") in ("rectangle", "ellipse", "diamond"):
                g.add_node(el["id"])
            elif el.get("type") == "arrow":
                sb = el.get("startBinding", {})
                eb = el.get("endBinding", {})
                sid = (
                    sb.get("elementId")
                    if isinstance(sb, dict)
                    else (sb if isinstance(sb, str) else None)
                )
                eid = (
                    eb.get("elementId")
                    if isinstance(eb, dict)
                    else (eb if isinstance(eb, str) else None)
                )
                if sid in g and eid in g:
                    g.add_edge(sid, eid)

        if g.nodes:
            active_nodes = [n for n in g.nodes if g.degree(n) > 0]
            g_eval = g.subgraph(active_nodes) if len(active_nodes) >= 3 else g
            degrees = dict(g_eval.degree())
            max_deg = max(degrees.values()) if degrees else 0

            # A. Wheel graph detection (Hub + Outer Cycle)
            if len(g_eval.nodes) >= 4 and max_deg >= 3:
                hub_cand = max(
                    degrees,
                    key=lambda n: (
                        degrees[n],
                        1 if any(k in n.lower() for k in ("hub", "core", "center")) else 0,
                    ),
                )
                outer = [n for n in g_eval.nodes if n != hub_cand]
                if len(outer) >= 3:
                    try:
                        g_outer = g_eval.subgraph(outer)
                        outer_cycles = nx.cycle_basis(g_outer)
                        if outer_cycles:
                            longest_cycle = max(outer_cycles, key=len)
                            if len(longest_cycle) >= max(3, int(len(outer) * 0.7)):
                                hub_neighbors = set(g_eval.neighbors(hub_cand))
                                if len(hub_neighbors.intersection(longest_cycle)) >= int(
                                    len(longest_cycle) * 0.7
                                ):
                                    is_wheel = True
                    except Exception:
                        pass

            # B. Radial Star detection (One hub with leaves of degree 1)
            if not is_wheel and len(g_eval.nodes) > 3:
                high_deg_nodes = [n for n, d in degrees.items() if d > 1]
                if len(high_deg_nodes) <= 1 and max_deg >= len(g_eval.nodes) - 1:
                    is_radial = True

            # C. Cycle detection
            if not is_wheel and not is_radial:
                try:
                    basis = nx.cycle_basis(g_eval)
                    if basis and len(max(basis, key=len)) == len(g_eval.nodes):
                        is_cycle = True
                except Exception:
                    pass

            # D. Tree structure detection
            if not is_wheel and not is_radial and not is_cycle and len(g_eval.nodes) > 3:
                try:
                    if nx.is_tree(g_eval):
                        is_tree = True
                except Exception:
                    pass

            # E. Value Chain / Linear Chain detection
            if (
                not is_wheel
                and not is_radial
                and not is_cycle
                and not is_tree
                and len(g_eval.nodes) > 2
            ):
                deg_vals = list(degrees.values())
                deg_2 = sum(1 for d in deg_vals if d == 2)
                deg_1 = sum(1 for d in deg_vals if d == 1)
                if deg_2 >= len(g_eval.nodes) - 2 and deg_1 <= 2:
                    is_chain = True

    # 3. Route to engine
    engine_name = layout_hint
    if not engine_name:
        if is_wheel:
            engine_name = "wheel"
        elif is_radial:
            engine_name = "radial"
        elif is_cycle:
            engine_name = "cycle"
        elif is_tree:
            engine_name = "tree"
        elif is_chain:
            engine_name = "value_chain"
        elif _has_enclosing_containers(elements):
            return "manual_cluster_preserved"
        else:
            engine_name = "sugiyama"

    if engine_name == "matrix":
        apply_matrix_layout(elements, style=matrix_style, theme=theme)
    elif engine_name == "wheel":
        apply_wheel_layout(elements, theme=theme)
    elif engine_name == "radial":
        apply_radial_layout(elements, theme=theme)
    elif engine_name == "concentric":
        apply_concentric_layout(elements, theme=theme)
    elif engine_name == "tree":
        apply_tree_layout(elements, direction=tree_dir, theme=theme)
    elif engine_name == "value_chain":
        apply_value_chain_layout(elements, theme=theme)
    elif engine_name == "cycle":
        apply_cycle_layout(elements, theme=theme)
    else:
        engine_name = "sugiyama"
        apply_sugiyama_layout(elements, theme=theme)

    return engine_name
