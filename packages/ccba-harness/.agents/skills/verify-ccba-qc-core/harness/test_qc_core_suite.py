"""test_qc_core_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-qc-core.

Covers all features declared in `verify-ccba-qc-core/features/INDEX.md`:
- FEAT-QCC-001: PEP 562 _LAZY_EXPORTS (14 symbols), __all__ & __dir__ Parity
- FEAT-QCC-002: PcccJurisdictionRouter Dual-Pathway Routing, C07 Escalation & PC13 Fallback
- FEAT-QCC-003: DiscoveryEngine Index Scanning & Missing PDF FileNotFoundError (bug_path_1)
- FEAT-QCC-004: QCBatchOrchestrator Page Lookup, blank.png Fallback (bug_path_2) & Missing CSV Guard
- FEAT-QCC-005: Statechart Anti-Lie, bug_path Parity & ReporterEngine Markdown/JSON Synthesis
- FEAT-QCC-006: Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

import ccba_qc_core
from ccba_qc_core import (
    DiscoveryEngine,
    PcccJurisdictionRouter,
    PcccProjectSpec,
    PcccProjectType,
    ProjectBackbone,
    QCBatchOrchestrator,
    ReporterEngine,
    SheetEntry,
)
from ccba_qc_core import pipeline as qcc_pipeline

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_qc_core.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_qc_core.py"
    spec = importlib.util.spec_from_file_location("run_verify_qc_core", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_qc_core"] = mod
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


def _write_two_page_pdf(pdf_path: Path) -> None:
    """Create a minimal 2-page PDF in tmp_path without external fixtures."""
    os.environ.setdefault("PYMUPDF_MESSAGE", "fd:2")
    import pymupdf

    open_pdf: Any = pymupdf.open
    doc: Any = open_pdf()
    page0 = doc.new_page(width=400, height=400)
    page0.insert_text((40, 72), "DANH MUC BAN VE - INDEX OF DRAWINGS")
    page1 = doc.new_page(width=400, height=400)
    page1.insert_text((40, 72), "MAT BANG TANG 1 - SHEET A-101")
    doc.save(str(pdf_path))
    doc.close()


def test_feat_qcc_001_lazy_exports_and_dir_parity() -> None:
    """Verify FEAT-QCC-001: PEP 562 _LAZY_EXPORTS (14 symbols), __all__ & __dir__ parity."""
    assert len(ccba_qc_core.__all__) == 14
    assert set(ccba_qc_core.__all__) == set(ccba_qc_core._LAZY_EXPORTS.keys())
    assert set(ccba_qc_core.__all__).issubset(set(dir(ccba_qc_core)))

    for sym in (
        "QCAuditPipeline",
        "QCBatchOrchestrator",
        "DiscoveryEngine",
        "PcccJurisdictionRouter",
        "PcccProjectSpec",
        "PcccProjectType",
        "PcccJurisdictionResult",
        "ReporterEngine",
    ):
        assert getattr(ccba_qc_core, sym) is not None

    missing_attr = "non_existent_qc_core_symbol_xyz"
    with pytest.raises(AttributeError, match="no attribute"):
        _ = getattr(ccba_qc_core, missing_attr)


def test_feat_qcc_002_pccc_jurisdiction_routing_and_escalation() -> None:
    """Verify FEAT-QCC-002: C07 high-rise escalation (bug_path_4), PC07, and PC13 fallback (bug_path_3)."""
    # bug_path_4: Group A / >=100m high-rise Annex III escalates to C07 & BO_XAY_DUNG
    res_c07 = PcccJurisdictionRouter.evaluate(
        PcccProjectSpec(
            project_type="Chung cư cao tầng",
            floors=32,
            height_m=105.0,
            floor_area_m2=25000.0,
            investment_tier="NHOM_A",
        )
    )
    assert res_c07.is_annex_iii is True
    assert res_c07.police_required is True
    assert res_c07.police_tier == "C07"
    assert res_c07.cqcmvxd_required is True
    assert res_c07.cqcmvxd_tier == "BO_XAY_DUNG"
    assert "PC12" in res_c07.police_forms

    # Standard Annex III NHOM_B routes to PC07 & SO_XAY_DUNG
    res_pc07 = PcccJurisdictionRouter.evaluate(
        PcccProjectSpec(
            project_type="Khách sạn",
            floors=10,
            height_m=36.0,
            floor_area_m2=4000.0,
            investment_tier="NHOM_B",
        )
    )
    assert res_pc07.police_tier == "PC07"
    assert res_pc07.cqcmvxd_tier == "SO_XAY_DUNG"

    # bug_path_3: Unrecognized type normalizes to OTHER below thresholds -> PC13 self-appraisal
    spec_other = PcccProjectSpec(
        project_type="Công trình phụ trợ lạ",
        floors=2,
        height_m=8.0,
        floor_area_m2=200.0,
        investment_tier="TU_NHAN",
    )
    assert spec_other.get_canonical_type() == PcccProjectType.OTHER
    res_pc13 = PcccJurisdictionRouter.evaluate(spec_other)
    assert res_pc13.police_required is False
    assert res_pc13.cqcmvxd_required is False
    assert res_pc13.investor_self_appraisal is True
    assert res_pc13.investor_forms == ["PC13"]


def test_feat_qcc_003_discovery_engine_and_missing_pdf_bug_path_1(tmp_path: Path) -> None:
    """Verify FEAT-QCC-003: DiscoveryEngine index scan, backbone serialization & bug_path_1."""
    eng = DiscoveryEngine(project_name="Tower A", output_dir=tmp_path / "disc_out")
    assert eng.output_dir.is_dir()

    # bug_path_1: Non-existent PDF raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="PDF not found"):
        eng.find_index_pages(tmp_path / "absent_set.pdf")

    sample_pdf = tmp_path / "arch_set.pdf"
    _write_two_page_pdf(sample_pdf)
    assert eng.find_index_pages(sample_pdf, search_limit=5) == [0]

    bb = ProjectBackbone(
        project="Tower A",
        generated_at="2026-11-17T12:00:00",
        total_files=1,
        total_sheets=1,
        sheets=[SheetEntry(file="arch_set.pdf", page_num=1, sheet_no="A-101", level="Tang 1")],
        index_pages={"arch_set.pdf": [0]},
    )
    payload = bb.to_dict()
    assert payload["total_sheets"] == 1
    assert payload["sheets"][0]["sheet_no"] == "A-101"


def test_feat_qcc_004_batch_orchestrator_blank_fallback_bug_path_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify FEAT-QCC-004: QCBatchOrchestrator blank.png fallback (bug_path_2) & sheet search."""
    proj_dir = tmp_path / "proj"
    pdf_dir = proj_dir / "Kien Truc"
    pdf_dir.mkdir(parents=True)
    sample_pdf = pdf_dir / "kt_tang1.pdf"
    _write_two_page_pdf(sample_pdf)

    orch = QCBatchOrchestrator(
        project_dir=proj_dir,
        matrix_csv=tmp_path / "missing_matrix.csv",
        out_dir=tmp_path / "batch_out",
    )
    assert orch.blank_img.is_file()

    found_pdf, found_page = orch.find_page_in_dir(pdf_dir, "A-101|Mat bang")
    assert found_pdf == sample_pdf
    assert found_page == 1

    # bug_path_2: Negative page index or render failure returns blank_img safely
    out_img = tmp_path / "batch_out" / "renders" / "t1_arch.png"
    assert orch.render_page(sample_pdf, -1, out_img) == orch.blank_img

    def _boom_render(**_kwargs: Any) -> None:
        raise RuntimeError("synthetic render error")

    monkeypatch.setattr(qcc_pipeline, "render_page_to_image", _boom_render)
    assert orch.render_page(sample_pdf, 1, out_img) == orch.blank_img

    with pytest.raises(FileNotFoundError, match="Matrix file not found"):
        asyncio.run(orch.run_batch())


def test_feat_qcc_005_statechart_anti_lie_and_reporter_synthesize(tmp_path: Path) -> None:
    """Verify FEAT-QCC-005: Statechart Anti-Lie, bug_path parity & ReporterEngine synthesis."""
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

    backbone = ProjectBackbone(
        project="Test Tower",
        generated_at="2026-11-17T12:00:00",
        total_files=1,
        total_sheets=1,
        sheets=[
            SheetEntry(
                file="a.pdf", page_num=1, sheet_no="A-101", level="Tang 1", discipline="Arch"
            )
        ],
    )
    reporter = ReporterEngine(project_name="Test Tower")
    out_md = tmp_path / "reports" / "qc_summary.md"
    result_path = reporter.synthesize(
        backbone=backbone,
        audit_results=[
            {"level": "Tang 1", "ai_model": "tier-fast", "findings": [], "summary": "OK"}
        ],
        output_path=out_md,
    )
    assert result_path == out_md and out_md.is_file()
    md_text = out_md.read_text(encoding="utf-8")
    assert "## 1. Tom Tat Ho So" in md_text
    assert "## 2. Ma Tran Phoi Hop" in md_text

    json_summary = out_md.with_suffix(".json")
    assert json_summary.is_file()
    summary_data = json.loads(json_summary.read_text(encoding="utf-8"))
    assert summary_data["project"] == "Test Tower"
    assert len(summary_data["audit_results"]) == 1


def test_feat_qcc_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-QCC-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
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
