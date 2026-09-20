"""Helper utilities for ccba-diagram tests."""

from __future__ import annotations

from typing import Any


def make_shape(
    sid: str,
    shape_type: str = "rectangle",
    x: float = 0.0,
    y: float = 0.0,
    w: float = 150.0,
    h: float = 100.0,
    text: str | None = None,
) -> dict[str, Any]:
    """Helper to create a standard Excalidraw shape dict."""
    el = {
        "id": sid,
        "type": shape_type,
        "x": float(x),
        "y": float(y),
        "width": float(w),
        "height": float(h),
        "strokeColor": "#1e1e1e",
        "backgroundColor": "#ffffff",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "roughness": 0,
        "boundElements": [],
    }
    if text:
        el["text"] = text
    return el


def make_arrow(
    aid: str,
    from_id: str,
    to_id: str,
    sx: float = 0.0,
    sy: float = 0.0,
    ex: float = 100.0,
    ey: float = 100.0,
) -> dict[str, Any]:
    """Helper to create an Excalidraw arrow dict connecting two shapes."""
    return {
        "id": aid,
        "type": "arrow",
        "x": float(sx),
        "y": float(sy),
        "points": [[0.0, 0.0], [float(ex - sx), float(ey - sy)]],
        "startBinding": {"elementId": from_id, "focus": 0, "gap": 15},
        "endBinding": {"elementId": to_id, "focus": 0, "gap": 15},
        "strokeColor": "#1e1e1e",
        "strokeWidth": 1,
        "roughness": 0,
        "endArrowhead": "arrow",
    }


def make_text(
    tid: str,
    text: str,
    container_id: str | None = None,
    x: float = 0.0,
    y: float = 0.0,
) -> dict[str, Any]:
    """Helper to create an Excalidraw text element."""
    el = {
        "id": tid,
        "type": "text",
        "text": text,
        "x": float(x),
        "y": float(y),
        "fontSize": 14,
        "fontFamily": 1,
        "strokeColor": "#1e1e1e",
    }
    if container_id:
        el["containerId"] = container_id
    return el
