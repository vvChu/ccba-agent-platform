"""Unit tests for layout router and topology detection."""

from __future__ import annotations

from ccba_diagram.router import apply_smart_layout
from helpers import make_arrow, make_shape, make_text


def test_router_explicit_hint():
    """Test router respects explicit #layout:* hints from text nodes."""
    hint_node = make_text("hint", "#layout:wheel")
    hub = make_shape("HUB", text="Hub")
    s1 = make_shape("S1", text="Spoke 1")
    s2 = make_shape("S2", text="Spoke 2")
    elements = [hint_node, hub, s1, s2]

    engine = apply_smart_layout(elements)
    assert engine == "wheel"
    # Metadata text node must be stripped from elements
    assert all(el.get("id") != "hint" for el in elements)


def test_router_forced_engine():
    """Test router respects force_engine parameter."""
    s1 = make_shape("S1")
    s2 = make_shape("S2")
    elements = [s1, s2]

    engine = apply_smart_layout(elements, force_engine="tree")
    assert engine == "tree"


def test_router_detect_cycle_graph():
    """Test automatic topology detection of closed cycle graph."""
    c1 = make_shape("A")
    c2 = make_shape("B")
    c3 = make_shape("C")
    a1 = make_arrow("a1", "A", "B")
    a2 = make_arrow("a2", "B", "C")
    a3 = make_arrow("a3", "C", "A")
    elements = [c1, c2, c3, a1, a2, a3]

    engine = apply_smart_layout(elements)
    assert engine == "cycle"


def test_router_detect_star_graph():
    """Test automatic topology detection of hub-and-spoke star graph."""
    hub = make_shape("HUB")
    s1 = make_shape("S1")
    s2 = make_shape("S2")
    s3 = make_shape("S3")
    s4 = make_shape("S4")
    a1 = make_arrow("a1", "HUB", "S1")
    a2 = make_arrow("a2", "HUB", "S2")
    a3 = make_arrow("a3", "HUB", "S3")
    a4 = make_arrow("a4", "HUB", "S4")
    elements = [hub, s1, s2, s3, s4, a1, a2, a3, a4]

    engine = apply_smart_layout(elements)
    assert engine == "radial"


def test_router_detect_tree_graph():
    """Test automatic topology detection of spanning tree."""
    r = make_shape("ROOT")
    c1 = make_shape("C1")
    c2 = make_shape("C2")
    c3 = make_shape("C3")
    c4 = make_shape("C4")
    a1 = make_arrow("a1", "ROOT", "C1")
    a2 = make_arrow("a2", "ROOT", "C2")
    a3 = make_arrow("a3", "C1", "C3")
    a4 = make_arrow("a4", "C1", "C4")
    elements = [r, c1, c2, c3, c4, a1, a2, a3, a4]

    engine = apply_smart_layout(elements)
    assert engine == "tree"


def test_router_detect_wheel_graph():
    """Test automatic topology detection of Wheel graph (Hub + Outer cycle)."""
    hub = make_shape("HUB_CORE")
    o1 = make_shape("O1")
    o2 = make_shape("O2")
    o3 = make_shape("O3")
    o4 = make_shape("O4")
    # Outer cycle
    ac1 = make_arrow("ac1", "O1", "O2")
    ac2 = make_arrow("ac2", "O2", "O3")
    ac3 = make_arrow("ac3", "O3", "O4")
    ac4 = make_arrow("ac4", "O4", "O1")
    # Spokes
    as1 = make_arrow("as1", "HUB_CORE", "O1")
    as2 = make_arrow("as2", "HUB_CORE", "O2")
    as3 = make_arrow("as3", "HUB_CORE", "O3")
    as4 = make_arrow("as4", "HUB_CORE", "O4")
    elements = [hub, o1, o2, o3, o4, ac1, ac2, ac3, ac4, as1, as2, as3, as4]

    engine = apply_smart_layout(elements)
    assert engine == "wheel"
