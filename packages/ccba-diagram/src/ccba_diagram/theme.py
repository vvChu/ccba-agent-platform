"""Visual ergonomics theme and configuration for diagramming."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiagramTheme:
    """Design theme specifications adhering to CCBA Visual Ergonomics Standard v8.15.10."""

    # Background & Stroke colors
    background_color: str = "#ffffff"
    stroke_color: str = "#1e1e1e"
    stroke_width: int = 1
    font_family: int = 1  # 1: Virgil/Segoe UI, 2: Helvetica, 3: Cascadia

    # Accent colors for multi-tier visual hierarchy
    hub_background: str = "#e3f2fd"
    hub_stroke_color: str = "#0d47a1"
    hub_stroke_width: int = 3

    banner_background: str = "#f5f5f5"
    banner_stroke_color: str = "#757575"

    # Canvas dimensions & ergonomics constraints
    canvas_max_width: float = 1150.0
    canvas_min_width: float = 1000.0
    canvas_padding_x: float = 80.0
    canvas_padding_y: float = 60.0

    # Typography & spacing thresholds
    font_size_min: float = 12.0
    arrow_label_gap: float = 15.0
    arrow_horizontal_clearance: float = 80.0


# Default global singleton theme instance
DEFAULT_THEME = DiagramTheme()
