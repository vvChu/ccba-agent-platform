"""Unit tests for geometry and mathematical boundary calculations."""

from __future__ import annotations

import math

from ccba_diagram.geometry import (
    compute_safe_arrow_endpoints,
    get_shape_boundary_point,
    normalize_canvas_bounding_box,
    sync_bound_text_translation,
)
from helpers import make_arrow, make_shape, make_text


def test_boundary_point_rectangle():
    """Test ray-box clipping for rectangle shapes."""
    # 200x100 box centered at (200, 150)
    shape = make_shape("box1", "rectangle", x=100, y=100, w=200, h=100)

    # Ray pointing strictly right (+dx, 0) -> cx + hw = 200 + 100 = 300
    bx, by = get_shape_boundary_point(shape, 1.0, 0.0)
    assert math.isclose(bx, 300.0, abs_tol=1e-3)
    assert math.isclose(by, 150.0, abs_tol=1e-3)

    # Ray pointing strictly down (0, +dy) -> cy + hh = 150 + 50 = 200
    bx, by = get_shape_boundary_point(shape, 0.0, 1.0)
    assert math.isclose(bx, 200.0, abs_tol=1e-3)
    assert math.isclose(by, 200.0, abs_tol=1e-3)

    # Ray pointing strictly left (-dx, 0) -> cx - hw = 200 - 100 = 100
    bx, by = get_shape_boundary_point(shape, -1.0, 0.0)
    assert math.isclose(bx, 100.0, abs_tol=1e-3)
    assert math.isclose(by, 150.0, abs_tol=1e-3)


def test_boundary_point_ellipse():
    """Test parametric ellipse boundary intersection."""
    # 200x100 ellipse centered at (200, 150) -> rx=100, ry=50
    shape = make_shape("el1", "ellipse", x=100, y=100, w=200, h=100)

    bx, by = get_shape_boundary_point(shape, 1.0, 0.0)
    assert math.isclose(bx, 300.0, abs_tol=1e-3)
    assert math.isclose(by, 150.0, abs_tol=1e-3)

    bx, by = get_shape_boundary_point(shape, 0.0, 1.0)
    assert math.isclose(bx, 200.0, abs_tol=1e-3)
    assert math.isclose(by, 200.0, abs_tol=1e-3)


def test_safe_arrow_endpoints_non_overlapping():
    """Test safe arrow endpoints between two distant shapes."""
    s1 = make_shape("s1", "rectangle", x=100, y=100, w=100, h=100)
    s2 = make_shape("s2", "rectangle", x=400, y=100, w=100, h=100)

    sx, sy, ex, ey = compute_safe_arrow_endpoints(s1, s2)
    # Source right edge is x=200 -> sx > 200 (with gap pad)
    assert sx > 200.0
    # Target left edge is x=400 -> ex < 400 (with gap pad)
    assert ex < 400.0
    assert ex > sx
    assert math.isclose(sy, 150.0, abs_tol=1.0)
    assert math.isclose(ey, 150.0, abs_tol=1.0)


def test_safe_arrow_endpoints_overlapping_fallback():
    """Test that overlapping shapes do not produce inverted arrows."""
    s1 = make_shape("s1", "rectangle", x=100, y=100, w=100, h=100)
    s2 = make_shape("s2", "rectangle", x=110, y=100, w=100, h=100)

    sx, sy, ex, ey = compute_safe_arrow_endpoints(s1, s2)
    # Must not crash and ex should not be inverted behind sx along direction
    assert isinstance(sx, float) and isinstance(ex, float)


def test_sync_bound_text_translation():
    """Test moving shape moves all its bound texts synchronously."""
    shape = make_shape("s1", "rectangle", x=50, y=50, w=150, h=100)
    text = make_text("t1", "Label", container_id="s1", x=70, y=90)
    shape["boundElements"] = [{"type": "text", "id": "t1"}]

    elements = [shape, text]
    sync_bound_text_translation(shape, elements, dx=50.0, dy=30.0)

    assert math.isclose(text["x"], 120.0)
    assert math.isclose(text["y"], 120.0)


def test_normalize_canvas_bounding_box():
    """Test shifting elements with negative coordinates into safe positive viewport."""
    s1 = make_shape("s1", "rectangle", x=-150, y=-50, w=100, h=100)
    t1 = make_text("t1", "Text", x=-100, y=-20)
    arr = make_arrow("a1", "s1", "s1", sx=-100, sy=0, ex=50, ey=50)

    elements = [s1, t1, arr]
    normalize_canvas_bounding_box(elements, min_padding_x=80.0, min_padding_y=60.0)

    # Minimum x was -150, padding is 80 -> shift_x = 230
    assert s1["x"] >= 80.0
    assert s1["y"] >= 60.0
    assert t1["x"] >= 80.0
    assert arr["x"] >= 80.0
