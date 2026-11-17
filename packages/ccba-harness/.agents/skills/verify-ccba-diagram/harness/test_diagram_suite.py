"""test_diagram_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-diagram.

Covers all features declared in `verify-ccba-diagram/features/INDEX.md`:
- FEAT-DIA-001: Public Deep Seams (__all__ 16 symbols) & DiagramTheme Ergonomics Defaults
- FEAT-DIA-002: apply_smart_layout Tag Stripping, Topology Detection, Container Preservation & Unknown Fallback
- FEAT-DIA-003: get_shape_boundary_point & compute_safe_arrow_endpoints Overlap Clamp
- FEAT-DIA-004: normalize_canvas_bounding_box Positive Padding Shift & sync_bound_text_translation
- FEAT-DIA-005: Statechart Anti-Lie, bug_path Parity & generate_markdown_spec_table Replay
- FEAT-DIA-006: Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier
"""

from __future__ import annotations

import importlib.util
import math
import re
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

import ccba_diagram
from ccba_diagram import (
    DEFAULT_THEME,
    DiagramTheme,
    apply_smart_layout,
    compute_safe_arrow_endpoints,
    generate_markdown_spec_table,
    get_shape_boundary_point,
    normalize_canvas_bounding_box,
    sync_bound_text_translation,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_diagram.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_diagram.py"
    spec = importlib.util.spec_from_file_location("run_verify_diagram", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_diagram"] = mod
    spec.loader.exec_module(mod)
    return mod


def _extract_statechart_lines(skill_md: Path) -> list[str]:
    """Extract the first stateDiagram-v2 mermaid block from SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    for block in re.findall(r"```mermaid\s*\n(.*?)```", text, flags=re.DOTALL):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip() and not ln.startswith("%%")]
        if lines and lines[0].startswith("stateDiagram"):
            return lines
    raise AssertionError(f"No stateDiagram block found in {skill_md}")


def _shape(
    eid: str,
    *,
    x: float = 0.0,
    y: float = 0.0,
    width: float = 150.0,
    height: float = 80.0,
    stype: str = "rectangle",
    text: str | None = None,
    bound_elements: list[dict[str, Any]] | None = None,
    background: str = "#ffffff",
    stroke_width: int = 1,
    stroke_style: str = "solid",
) -> dict[str, Any]:
    """Build a minimal Excalidraw shape dict in memory."""
    el: dict[str, Any] = {
        "id": eid,
        "type": stype,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "backgroundColor": background,
        "strokeWidth": stroke_width,
        "strokeStyle": stroke_style,
    }
    if text is not None:
        el["text"] = text
    if bound_elements is not None:
        el["boundElements"] = list(bound_elements)
    return el


def _arrow(
    aid: str,
    start_id: str,
    end_id: str,
    bound_elements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal bound Excalidraw arrow dict in memory."""
    el: dict[str, Any] = {
        "id": aid,
        "type": "arrow",
        "x": 0.0,
        "y": 0.0,
        "points": [[0.0, 0.0], [100.0, 0.0]],
        "startBinding": {"elementId": start_id},
        "endBinding": {"elementId": end_id},
    }
    if bound_elements is not None:
        el["boundElements"] = list(bound_elements)
    return el


def test_feat_dia_001_public_seams_and_theme_defaults() -> None:
    """Verify FEAT-DIA-001: 16 public __all__ exports and DiagramTheme ergonomic defaults."""
    expected = {
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
    }
    assert set(ccba_diagram.__all__) == expected
    for symbol in expected:
        assert getattr(ccba_diagram, symbol) is not None

    assert isinstance(DEFAULT_THEME, DiagramTheme)
    assert DEFAULT_THEME.canvas_padding_x == 80.0
    assert DEFAULT_THEME.canvas_padding_y == 60.0
    assert DEFAULT_THEME.hub_stroke_width == 3


def test_feat_dia_002_router_hints_topology_and_bug_paths() -> None:
    """Verify FEAT-DIA-002: tag stripping, topology auto-detection, bug_path_1 & bug_path_2."""
    # Metadata tag stripping (including boundElements cleanup)
    meta_txt = {
        "id": "meta_hint",
        "type": "text",
        "text": "#layout:tree #dir:lr",
        "x": 0.0,
        "y": 0.0,
    }
    root = _shape(
        "root",
        bound_elements=[{"id": "meta_hint", "type": "text"}, {"id": "a1", "type": "arrow"}],
    )
    child = _shape("child")
    elements_tagged = [meta_txt, root, child, _arrow("a1", "root", "child")]
    assert apply_smart_layout(elements_tagged) == "tree"
    assert all(el.get("id") != "meta_hint" for el in elements_tagged)
    assert [b["id"] for b in root["boundElements"]] == ["a1"]

    # Automatic cycle and radial detection
    cycle_els = [
        _shape("A"),
        _shape("B"),
        _shape("C"),
        _arrow("e1", "A", "B"),
        _arrow("e2", "B", "C"),
        _arrow("e3", "C", "A"),
    ]
    assert apply_smart_layout(cycle_els) == "cycle"

    radial_els = [
        _shape("HUB"),
        _shape("S1"),
        _shape("S2"),
        _shape("S3"),
        _shape("S4"),
        _arrow("r1", "HUB", "S1"),
        _arrow("r2", "HUB", "S2"),
        _arrow("r3", "HUB", "S3"),
        _arrow("r4", "HUB", "S4"),
    ]
    assert apply_smart_layout(radial_els) == "radial"

    # bug_path_1: Enclosing container preserves manual coordinates without relayout
    outer = _shape("cluster_box", x=10.0, y=20.0, width=600.0, height=400.0)
    inner = _shape("inner_node", x=50.0, y=60.0, width=120.0, height=60.0)
    assert apply_smart_layout([outer, inner]) == "manual_cluster_preserved"
    assert (outer["x"], outer["y"], inner["x"], inner["y"]) == (10.0, 20.0, 50.0, 60.0)

    # bug_path_2: Unknown force_engine silently falls back to sugiyama
    fallback_els = [_shape("N1"), _shape("N2"), _arrow("f1", "N1", "N2")]
    assert apply_smart_layout(fallback_els, force_engine="nonexistent_engine") == "sugiyama"


def test_feat_dia_003_geometry_boundary_and_overlap_clamp() -> None:
    """Verify FEAT-DIA-003: boundary intersection math, degenerate center & bug_path_3 overlap."""
    rect = _shape("R", x=0.0, y=0.0, width=200.0, height=100.0)
    assert get_shape_boundary_point(rect, 0.0, 0.0) == pytest.approx((100.0, 50.0))
    assert get_shape_boundary_point(rect, 50.0, 0.0) == pytest.approx((200.0, 50.0))

    ell = _shape("E", x=0.0, y=0.0, width=200.0, height=100.0, stype="ellipse")
    bx, by = get_shape_boundary_point(ell, 100.0, 50.0)
    assert math.isclose(((bx - 100.0) / 100.0) ** 2 + ((by - 50.0) / 50.0) ** 2, 1.0, rel_tol=1e-6)

    # Separated shapes keep gap padding = 4.0 outside boundaries
    left = _shape("L", x=0.0, y=0.0, width=100.0, height=60.0)
    right = _shape("R2", x=300.0, y=0.0, width=100.0, height=60.0)
    sx, sy, ex, ey = compute_safe_arrow_endpoints(left, right)
    assert (sx, sy, ex, ey) == pytest.approx((104.0, 30.0, 296.0, 30.0))

    # bug_path_3: Coincident centers return exact centers; close/overlapping shapes clamp at quarter size
    same = _shape("S_SAME", x=0.0, y=0.0, width=100.0, height=60.0)
    assert compute_safe_arrow_endpoints(left, same) == pytest.approx((50.0, 30.0, 50.0, 30.0))

    close_right = _shape("R_CLOSE", x=102.0, y=0.0, width=100.0, height=60.0)
    osx, osy, oex, oey = compute_safe_arrow_endpoints(left, close_right)
    # min(100, 60) / 4 = 15.0 from scx=50 -> 65.0, from ecx=152 -> 137.0
    assert (osx, osy, oex, oey) == pytest.approx((65.0, 30.0, 137.0, 30.0))


def test_feat_dia_004_canvas_normalization_and_bound_text_sync() -> None:
    """Verify FEAT-DIA-004: bound text synchronization and negative bbox positive-shift."""
    parent = _shape("P", x=100.0, y=80.0, bound_elements=[{"id": "t_bound", "type": "text"}])
    t_bound = {"id": "t_bound", "type": "text", "x": 110.0, "y": 90.0}
    t_container = {"id": "t_cont", "type": "text", "containerId": "P", "x": 115.0, "y": 95.0}
    t_header = {"id": "t_hdr", "type": "text", "containerHeaderOf": "P", "x": 120.0, "y": 70.0}
    t_unrelated = {"id": "t_other", "type": "text", "x": 300.0, "y": 300.0}
    els = [parent, t_bound, t_container, t_header, t_unrelated]

    sync_bound_text_translation(parent, els, dx=25.0, dy=-15.0)
    assert (t_bound["x"], t_bound["y"]) == pytest.approx((135.0, 75.0))
    assert t_bound["strokeColor"] == DEFAULT_THEME.stroke_color
    assert t_bound["fontFamily"] == DEFAULT_THEME.font_family
    assert (t_container["x"], t_container["y"]) == pytest.approx((140.0, 80.0))
    assert (t_header["x"], t_header["y"]) == pytest.approx((145.0, 55.0))
    assert (t_unrelated["x"], t_unrelated["y"]) == pytest.approx((300.0, 300.0))

    # Multi-point arrow extending to x=-20, y=10 shifts entire canvas so min x>=80, min y>=60
    bbox_els = [
        _shape("B1", x=50.0, y=40.0),
        {
            "id": "arr_neg",
            "type": "arrow",
            "x": 10.0,
            "y": 20.0,
            "points": [[0.0, 0.0], [-30.0, -10.0]],
        },
    ]
    normalize_canvas_bounding_box(bbox_els, min_padding_x=80.0, min_padding_y=60.0)
    # min_x was -20 -> shift_x = 100; min_y was 10 -> shift_y = 50
    assert (bbox_els[0]["x"], bbox_els[0]["y"]) == pytest.approx((150.0, 90.0))
    assert (bbox_els[1]["x"], bbox_els[1]["y"]) == pytest.approx((110.0, 70.0))


def test_feat_dia_005_statechart_anti_lie_and_matrix_table() -> None:
    """Verify FEAT-DIA-005: Statechart Anti-Lie, bug_path parity & spec table (bug_path_4)."""
    runner = _load_runner_module()
    if str(runner.REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(runner.REPO_ROOT))
    from tests.governance.test_statechart_anti_lie import (
        verify_bug_path_matches_statechart,
        verify_statechart_anti_lie,
    )

    skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
    assert verify_statechart_anti_lie(_extract_statechart_lines(skill_md)) == []
    assert verify_bug_path_matches_statechart(skill_md.read_text(encoding="utf-8")) == []

    # bug_path_4: Empty geometric shapes returns fallback notice
    notice = generate_markdown_spec_table([{"id": "t_only", "type": "text", "text": "Title"}])
    assert "Không có nút hình học" in notice

    # Role classification, entity cleanup & wikilink pipe escaping
    hub = _shape(
        "HUB",
        background="#e3f2fd",
        stroke_width=3,
        text="API [[api_doc|Gateway]] #40;v2#41;",
    )
    decision = _shape("DEC", stype="diamond", text="Branch A | B")
    arrow = _arrow("link1", "HUB", "DEC", bound_elements=[{"id": "edge_lbl", "type": "text"}])
    edge_lbl = {"id": "edge_lbl", "type": "text", "text": "route"}

    md = generate_markdown_spec_table([hub, decision, arrow, edge_lbl], table_title="Spec Test")
    assert "### 📋 Spec Test" in md
    assert r"[[api_doc\|Gateway]] (v2)" in md
    assert "Branch A / B" in md
    assert "**Lõi Điều Phối (Hub/Core)** *(Hình Rectangle)*" in md
    assert "**Điểm Quyết Định / Biên** *(Hình Diamond)*" in md
    assert "↳&nbsp;Branch A / B *(route)*" in md


def test_feat_dia_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-DIA-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
    runner = _load_runner_module()
    skill_dir = Path(__file__).resolve().parent.parent
    features_idx = skill_dir / "features" / "INDEX.md"
    assert runner.verify_surface_diff(features_idx, Path(__file__).resolve()) == []

    fm = yaml.safe_load((skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
    sync_sha = str(fm["sync_commit"])
    cov_paths = list(fm["covered_paths"])
    cov_hashes = dict(fm["covered_sha256"])
    assert set(cov_hashes.keys()) == set(cov_paths)
    assert runner.check_git_provenance(sync_sha, cov_paths, expected_sha256=cov_hashes) == []

    classify = runner.classify_drift_status
    assert (
        classify(
            env_blocked=False, suite_passed=True, contract_changed=False, intentional_change=False
        )
        == "in_sync"
    )
    assert (
        classify(
            env_blocked=False, suite_passed=True, contract_changed=True, intentional_change=True
        )
        == "updated"
    )
    assert (
        classify(
            env_blocked=False, suite_passed=False, contract_changed=True, intentional_change=False
        )
        == "bug"
    )
    assert (
        classify(
            env_blocked=True, suite_passed=False, contract_changed=False, intentional_change=False
        )
        == "blocked"
    )
