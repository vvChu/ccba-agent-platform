"""CCBA Diagramming Utilities — 8 Deterministic Layout Engines & Visual Ergonomics."""

from __future__ import annotations

from ccba_diagram.geometry import (
    compute_safe_arrow_endpoints,
    get_shape_boundary_point,
    normalize_canvas_bounding_box,
    sync_bound_text_translation,
)
from ccba_diagram.layouts.concentric import apply_concentric_layout
from ccba_diagram.layouts.cycle import apply_cycle_layout
from ccba_diagram.layouts.matrix import apply_matrix_layout
from ccba_diagram.layouts.radial import apply_radial_layout
from ccba_diagram.layouts.sugiyama import apply_sugiyama_layout
from ccba_diagram.layouts.tree import apply_tree_layout
from ccba_diagram.layouts.value_chain import apply_value_chain_layout
from ccba_diagram.layouts.wheel import apply_wheel_layout
from ccba_diagram.matrix_table import generate_markdown_spec_table
from ccba_diagram.router import apply_smart_layout
from ccba_diagram.theme import DEFAULT_THEME, DiagramTheme

__all__ = [
    "DEFAULT_THEME",
    "DiagramTheme",
    "apply_concentric_layout",
    "apply_cycle_layout",
    "apply_matrix_layout",
    "apply_radial_layout",
    "apply_smart_layout",
    "apply_sugiyama_layout",
    "apply_tree_layout",
    "apply_value_chain_layout",
    "apply_wheel_layout",
    "compute_safe_arrow_endpoints",
    "generate_markdown_spec_table",
    "get_shape_boundary_point",
    "normalize_canvas_bounding_box",
    "sync_bound_text_translation",
]
