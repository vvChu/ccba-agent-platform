"""Unit tests for the 8 deterministic layout engines."""

from __future__ import annotations

from ccba_diagram.layouts.concentric import apply_concentric_layout
from ccba_diagram.layouts.cycle import apply_cycle_layout
from ccba_diagram.layouts.matrix import apply_matrix_layout
from ccba_diagram.layouts.radial import apply_radial_layout
from ccba_diagram.layouts.sugiyama import apply_sugiyama_layout
from ccba_diagram.layouts.tree import apply_tree_layout
from ccba_diagram.layouts.value_chain import apply_value_chain_layout
from ccba_diagram.layouts.wheel import apply_wheel_layout
from helpers import make_arrow, make_shape


def test_sugiyama_layout():
    """Test layered DAG hierarchy via Sugiyama."""
    n1 = make_shape("A", text="Root Node")
    n2 = make_shape("B", text="Child 1")
    n3 = make_shape("C", text="Child 2")
    n4 = make_shape("D", text="Grandchild")
    a1 = make_arrow("a1", "A", "B")
    a2 = make_arrow("a2", "A", "C")
    a3 = make_arrow("a3", "B", "D")
    elements = [n1, n2, n3, n4, a1, a2, a3]

    assert apply_sugiyama_layout(elements)
    # Root A should be higher on Y axis than B and C
    assert n1["y"] < n2["y"]
    assert n1["y"] < n3["y"]
    # B should be higher on Y axis than D
    assert n2["y"] < n4["y"]


def test_wheel_layout():
    """Test wheel star-cycle layout with center hub and outer cycle."""
    hub = make_shape("HUB", text="Center Coordinator", w=160, h=100)
    o1 = make_shape("O1", text="Step 1")
    o2 = make_shape("O2", text="Step 2")
    o3 = make_shape("O3", text="Step 3")
    # Outer cycle edges
    a_c1 = make_arrow("ac1", "O1", "O2")
    a_c2 = make_arrow("ac2", "O2", "O3")
    a_c3 = make_arrow("ac3", "O3", "O1")
    # Spoke edges
    a_s1 = make_arrow("as1", "HUB", "O1")
    a_s2 = make_arrow("as2", "HUB", "O2")
    a_s3 = make_arrow("as3", "HUB", "O3")

    elements = [hub, o1, o2, o3, a_c1, a_c2, a_c3, a_s1, a_s2, a_s3]
    assert apply_wheel_layout(elements)
    # Outer shapes must not overlap with center hub
    for o in (o1, o2, o3):
        dx = o["x"] - hub["x"]
        dy = o["y"] - hub["y"]
        dist = (dx**2 + dy**2) ** 0.5
        assert dist > 150.0


def test_matrix_layout_cross():
    """Test 2x2 matrix layout with crosshair dividers."""
    tl = make_shape("TL", text="High Value / Low Effort (Quick Win)")
    tr = make_shape("TR", text="High Value / High Effort (Strategic)")
    bl = make_shape("BL", text="Low Value / Low Effort")
    br = make_shape("BR", text="Low Value / High Effort (Avoid)")

    elements = [tl, tr, bl, br]
    assert apply_matrix_layout(elements, style="cross")

    # TL must be above and left of BR
    assert tl["x"] < tr["x"]
    assert tl["y"] < bl["y"]
    # Dividers should have been injected into elements
    has_dividers = any(
        isinstance(el.get("id"), str) and el["id"].startswith("matrix_") for el in elements
    )
    assert has_dividers


def test_matrix_layout_axis():
    """Test 2x2 matrix layout with coordinate axis arrows."""
    n1 = make_shape("Q1", text="Quad 1")
    n2 = make_shape("Q2", text="Quad 2")
    n3 = make_shape("Q3", text="Quad 3")
    n4 = make_shape("Q4", text="Quad 4")

    elements = [n1, n2, n3, n4]
    assert apply_matrix_layout(elements, style="axis")

    has_axis = any(
        isinstance(el.get("id"), str) and el["id"].startswith("axis_") for el in elements
    )
    assert has_axis


def test_tree_layout_td_and_lr():
    """Test tree layout in both top-down and left-to-right directions."""
    root = make_shape("ROOT", text="Director")
    c1 = make_shape("C1", text="Manager A")
    c2 = make_shape("C2", text="Manager B")
    a1 = make_arrow("a1", "ROOT", "C1")
    a2 = make_arrow("a2", "ROOT", "C2")

    # Top-Down
    elements_td = [root, c1, c2, a1, a2]
    assert apply_tree_layout(elements_td, direction="td")
    assert root["y"] < c1["y"]
    assert root["y"] < c2["y"]

    # Left-to-Right
    elements_lr = [root, c1, c2, a1, a2]
    assert apply_tree_layout(elements_lr, direction="lr")
    assert root["x"] < c1["x"]
    assert root["x"] < c2["x"]


def test_radial_layout():
    """Test radial star graph layout."""
    hub = make_shape("HUB", text="Database Core")
    s1 = make_shape("S1", text="Client 1")
    s2 = make_shape("S2", text="Client 2")
    s3 = make_shape("S3", text="Client 3")
    a1 = make_arrow("a1", "HUB", "S1")
    a2 = make_arrow("a2", "HUB", "S2")
    a3 = make_arrow("a3", "HUB", "S3")

    elements = [hub, s1, s2, s3, a1, a2, a3]
    assert apply_radial_layout(elements)
    for s in (s1, s2, s3):
        assert s["x"] >= 80.0
        assert s["y"] >= 60.0


def test_concentric_layout():
    """Test concentric ring layout with multi-hop distances."""
    hub = make_shape("CORE", text="Core")
    r1_a = make_shape("R1_A", text="Ring 1 Node A")
    r1_b = make_shape("R1_B", text="Ring 1 Node B")
    r2_a = make_shape("R2_A", text="Ring 2 Node A")

    a1 = make_arrow("a1", "CORE", "R1_A")
    a2 = make_arrow("a2", "CORE", "R1_B")
    a3 = make_arrow("a3", "R1_A", "R2_A")

    elements = [hub, r1_a, r1_b, r2_a, a1, a2, a3]
    assert apply_concentric_layout(elements)
    assert hub["x"] >= 80.0


def test_value_chain_layout():
    """Test value chain layout with primary sequential flow and support activities."""
    p1 = make_shape("INBOUND", text="Inbound Logistics")
    p2 = make_shape("OPS", text="Operations")
    p3 = make_shape("OUTBOUND", text="Outbound Logistics")
    supp = make_shape("INFRA", text="Firm Infrastructure")
    margin = make_shape("MARGIN", text="Margin", shape_type="rectangle")

    a1 = make_arrow("a1", "INBOUND", "OPS")
    a2 = make_arrow("a2", "OPS", "OUTBOUND")
    a3 = make_arrow("a3", "OUTBOUND", "MARGIN")
    a_supp = make_arrow("as", "INFRA", "OPS")

    elements = [p1, p2, p3, supp, margin, a1, a2, a3, a_supp]
    assert apply_value_chain_layout(elements)

    # Primary chain should be ordered horizontally: p1.x < p2.x < p3.x
    assert p1["x"] < p2["x"]
    assert p2["x"] < p3["x"]
    # Support activity should be positioned above primary chain
    assert supp["y"] < p2["y"]


def test_cycle_layout():
    """Test closed feedback loop cycle layout."""
    c1 = make_shape("PLAN", text="Plan")
    c2 = make_shape("DO", text="Do")
    c3 = make_shape("CHECK", text="Check")
    c4 = make_shape("ACT", text="Act")

    a1 = make_arrow("a1", "PLAN", "DO")
    a2 = make_arrow("a2", "DO", "CHECK")
    a3 = make_arrow("a3", "CHECK", "ACT")
    a4 = make_arrow("a4", "ACT", "PLAN")

    elements = [c1, c2, c3, c4, a1, a2, a3, a4]
    assert apply_cycle_layout(elements)
    # Verify all curved arrows have roundness type 2
    for arr in (a1, a2, a3, a4):
        assert arr.get("roundness", {}).get("type") == 2


def test_empty_layout():
    """Verify layout returns False gracefully on empty or single-node elements."""
    assert not apply_sugiyama_layout([])
    assert not apply_wheel_layout([])
    assert not apply_matrix_layout([])
    assert not apply_tree_layout([])
    assert not apply_radial_layout([])
    assert not apply_concentric_layout([])
    assert not apply_value_chain_layout([])
    assert not apply_cycle_layout([])
