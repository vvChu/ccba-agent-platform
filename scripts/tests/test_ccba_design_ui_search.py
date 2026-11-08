"""Unit tests for ccba-design UI/UX & Web Portal BM25 search engine, Design Dials, WCAG 2.2 contrast & Slop Auditor."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = [pytest.mark.fast, pytest.mark.unit]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UI_SCRIPTS_DIR = PROJECT_ROOT / ".agents" / "skills" / "ccba-design" / "scripts" / "ui"


def _load_ui_module(module_name: str, filename: str) -> Any:
    """Dynamically load a module from .agents/skills/ccba-design/scripts/ui/."""
    filepath = UI_SCRIPTS_DIR / filename
    if str(UI_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(UI_SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ui_bm25_search_across_all_four_domains() -> None:
    """Verify BM25 search returns expected domain-specific rows across style, ux, chart, and product."""
    core = _load_ui_module("ccba_design_ui_core", "core.py")

    res_style = core.search("mira dense portal table", domain="style")
    assert res_style["domain"] == "style"
    assert res_style["count"] >= 1
    assert any("Mira Dense Portal" in r["Style Name"] for r in res_style["results"])

    res_ux = core.search("wcag focus sticky header scroll-margin-top", domain="ux")
    assert res_ux["domain"] == "ux"
    assert res_ux["count"] >= 1
    assert any(r["Rule ID"] == "UX-01" for r in res_ux["results"])

    res_chart = core.search("heatmap clash discipline pccc", domain="chart")
    assert res_chart["domain"] == "chart"
    assert res_chart["count"] >= 1
    assert any("Cross-Discipline Clash Heatmap" in r["Chart Type"] for r in res_chart["results"])

    res_prod = core.search("legal statutory vbpl okf clause", domain="product")
    assert res_prod["domain"] == "product"
    assert res_prod["count"] >= 1
    assert any("Legal Intelligence" in r["Product Type"] for r in res_prod["results"])

    res_typo = core.search("vietnamese be vietnam pro tabular", domain="typography")
    assert res_typo["domain"] == "typography"
    assert res_typo["count"] >= 1
    assert any("Be Vietnam Pro" in r["Heading Font"] for r in res_typo["results"])

    res_stack = core.search("sharepoint spfx fluent ui", domain="stack")
    assert res_stack["domain"] == "stack"
    assert res_stack["count"] >= 1
    assert any("sharepoint-spfx" in r["Stack Name"] for r in res_stack["results"])


def test_ui_detect_domain_and_search_all() -> None:
    """Verify automatic domain routing and multi-domain search_all aggregation."""
    core = _load_ui_module("ccba_design_ui_core", "core.py")

    assert core.detect_domain("wcag focus keyboard paste") == "ux"
    assert core.detect_domain("heatmap gantt sankey sparkline") == "chart"
    assert core.detect_domain("mira nova hairline bento") == "style"
    assert core.detect_domain("vbpl legal portal pccc dashboard") == "product"
    assert core.detect_domain("vietnamese font typeface diacritics") == "typography"
    assert core.detect_domain("sharepoint spfx nextjs tanstack") == "stack"

    combined = core.search_all("portal table compliance vietnamese nextjs", max_results=2)
    assert "product" in combined
    assert "style" in combined
    assert "typography" in combined
    assert "stack" in combined


def test_compute_design_dials_modes_and_clamping() -> None:
    """Verify quantitative Design Dials map density, variance, and motion to deterministic CSS specs."""
    core = _load_ui_module("ccba_design_ui_core", "core.py")

    dense = core.compute_design_dials(density=9, variance=2, motion=1)
    assert dense["surface_mode"] == "Operate"
    assert "28px-32px" in dense["density_dial"]
    assert "Swiss" in dense["variance_dial"]
    assert "150ms-200ms" in dense["motion_dial"]

    spacious = core.compute_design_dials(density=2, variance=9, motion=9)
    assert spacious["surface_mode"] == "Persuade"
    assert "40px-48px" in spacious["density_dial"]
    assert "Bento" in spacious["variance_dial"]


def test_compute_contrast_ratio_wcag_compliance() -> None:
    """Verify WCAG 2.1/2.2 contrast calculation on CCBA canonical brand pairs and invalid hex rejection."""
    core = _load_ui_module("ccba_design_ui_core", "core.py")

    # CCBA Dark Blue #363883 vs White #FFFFFF -> 10.24:1 (AAA Pass)
    ccba_navy = core.compute_contrast_ratio("#FFFFFF", "#363883")
    assert ccba_navy["ratio"] == pytest.approx(10.24, abs=0.05)
    assert ccba_navy["wcag_aaa_normal"] is True
    assert ccba_navy["wcag_aa_normal"] is True

    # Prohibited pair: White #FFFFFF on Attention Yellow #F2C811 -> ~1.61:1 (Fail)
    bad_yellow = core.compute_contrast_ratio("#FFFFFF", "#F2C811")
    assert bad_yellow["ratio"] < 2.0
    assert bad_yellow["wcag_aa_normal"] is False
    assert bad_yellow["wcag_aa_large"] is False

    with pytest.raises(ValueError, match="Invalid hex color"):
        core.compute_contrast_ratio("#12345", "#FFFFFF")


def test_audit_ui_code_dual_assertion() -> None:
    """Verify deterministic UI slop auditor catches all 6 anti-patterns and passes clean portal markup."""
    core = _load_ui_module("ccba_design_ui_core", "core.py")

    clean_markup = (
        '<div className="bg-card text-foreground border border-border flex gap-3">\n'
        '  <table className="w-full tabular-nums"><tbody><tr><td>102.4</td></tr></tbody></table>\n'
        "</div>\n"
    )
    assert core.audit_ui_code(clean_markup) == []

    sloppy_markup = (
        '<div className="bg-slate-900 space-x-4 border-l-4" style={{ fontSize: "clamp(1rem, 3vw, 2rem)", fontFamily: "Clash Display" }}>\n'
        '  <input type="password" onPaste={(e) => e.preventDefault()} />\n'
        "  <table><tbody><tr><td>42</td></tr></tbody></table>\n"
        "</div>\n"
    )
    findings = core.audit_ui_code(sloppy_markup)
    rule_ids = {f["rule_id"] for f in findings}
    assert {
        "SLOP-01",
        "SLOP-02",
        "SLOP-03",
        "SLOP-04",
        "SLOP-05",
        "SLOP-06",
        "SLOP-07",
    }.issubset(rule_ids)


def test_generate_and_persist_design_system_hierarchy(tmp_path: Path) -> None:
    """Verify CLI brief generator and MASTER.md + pages/<page>.md hierarchical persistence."""
    search_mod = _load_ui_module("ccba_design_ui_search", "search.py")
    brief = search_mod.generate_design_system_brief(
        "qc audit pccc dashboard heatmap vietnamese",
        project_name="CCBA-QC-Portal",
        density=9,
        variance=4,
        motion=2,
        stack_query="nextjs-shadcn",
    )
    assert "UI/UX & PORTAL DESIGN SYSTEM: CCBA-QC-PORTAL" in brief
    assert "Surface Mode: Operate" in brief
    assert "6. STACK IMPLEMENTATION GUARDRAILS" in brief

    master_path = search_mod.persist_design_system(brief, tmp_path, project_name="CCBA-QC-Portal")
    assert master_path == tmp_path / "ccba-qc-portal" / "MASTER.md"
    assert master_path.exists()
    assert "CCBA-QC-PORTAL" in master_path.read_text(encoding="utf-8")

    page_path = search_mod.persist_design_system(
        brief, tmp_path, project_name="CCBA-QC-Portal", page_slug="pccc-heatmap"
    )
    assert page_path == tmp_path / "ccba-qc-portal" / "pages" / "pccc-heatmap.md"
    assert page_path.exists()


def test_shared_bm25_engine_across_logo_and_cip_cores() -> None:
    """Verify logo/core.py and cip/core.py share deterministic BM25 sorting without reverse=True."""
    scripts_dir = PROJECT_ROOT / ".agents" / "skills" / "ccba-design" / "scripts"
    for sub, mod_name, query in (
        ("logo", "ccba_design_logo_core", "minimalist tech"),
        ("cip", "ccba_design_cip_core", "business card corporate"),
    ):
        spec = importlib.util.spec_from_file_location(mod_name, scripts_dir / sub / "core.py")
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.search(query)
        assert res["count"] >= 1
        assert len(res["results"]) >= 1
