"""test_pdf_prep_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-pdf-prep.

Covers all features declared in `verify-ccba-pdf-prep/features/INDEX.md`:
- FEAT-PDF-001: Public Deep Seams (__all__) & DTO Hierarchy
- FEAT-PDF-002: PDFReport.get_segments() & should_skip Contract
- FEAT-PDF-003: Missing PDF & Analyzer Failure Error Branch (bug_path_1)
- FEAT-PDF-004: Drawing Strategy Tiling Failure (bug_path_2) & Degraded Result (bug_path_3)
- FEAT-PDF-005: Statechart Anti-Lie, bug_path Parity & Live UNKNOWN/TEXT_RICH Replays (bug_path_4)
- FEAT-PDF-006: Surface Diff Parity, LF SHA-256 Provenance Lock & Drift Classifier
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

import ccba_pdf_prep
from ccba_pdf_prep import (
    PageDetail,
    PDFCategory,
    PDFProcessingError,
    PDFProcessingPipeline,
    PDFReport,
    ProcessingResult,
    Segment,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_pdf_prep.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_pdf_prep.py"
    spec = importlib.util.spec_from_file_location("run_verify_pdf_prep", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_pdf_prep"] = mod
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


def _make_report(
    pdf_path: Path,
    category: PDFCategory,
    details: list[PageDetail] | None = None,
) -> PDFReport:
    """Build an in-memory PDFReport without parsing real PDF files."""
    page_details = details or [
        PageDetail(0, 120, 0, 210.0, 297.0, False, "text"),
        PageDetail(1, 120, 0, 210.0, 297.0, False, "text"),
    ]
    return PDFReport(
        file_path=pdf_path,
        category=category,
        recommended_model="tier-fast",
        confidence=0.95,
        pages=len(page_details),
        text_pages=len(page_details),
        image_pages=0,
        drawing_pages=1 if category == PDFCategory.DRAWING else 0,
        total_text_chars=240,
        avg_text_density=120.0,
        size_mb=0.5,
        is_oversized=(category == PDFCategory.DRAWING),
        page_details=page_details,
    )


def test_feat_pdf_001_public_seams_and_dtos() -> None:
    """Verify FEAT-PDF-001: public __all__ exports and core DTO contracts."""
    for symbol in (
        "PDFProcessingPipeline",
        "ProcessingResult",
        "PDFProcessingError",
        "PDFReport",
        "PDFCategory",
        "Segment",
        "PageDetail",
        "render_page_to_image",
        "get_pdf_page_count",
    ):
        assert symbol in ccba_pdf_prep.__all__
        assert getattr(ccba_pdf_prep, symbol) is not None

    seg = Segment(start_page=2, end_page=5, page_type="scan", model_hint="tier-ocr")
    assert seg.page_count == 4


def test_feat_pdf_002_report_segments_and_skip_contract(tmp_path: Path) -> None:
    """Verify FEAT-PDF-002: contiguous segment grouping and DRAWING should_skip property."""
    details = [
        PageDetail(0, 500, 0, 210.0, 297.0, False, "text"),
        PageDetail(1, 450, 0, 210.0, 297.0, False, "text"),
        PageDetail(2, 5, 1, 210.0, 297.0, False, "scan"),
    ]
    hybrid = _make_report(tmp_path / "hybrid.pdf", PDFCategory.HYBRID, details=details)
    segs = hybrid.get_segments(model_hints={"text": "tier-fast", "scan": "tier-ocr"})
    assert [(s.start_page, s.end_page, s.page_type) for s in segs] == [
        (0, 1, "text"),
        (2, 2, "scan"),
    ]
    assert hybrid.should_skip is False

    drawing = _make_report(tmp_path / "arch.pdf", PDFCategory.DRAWING, details=details[:1])
    assert drawing.should_skip is True
    assert "Engineering drawing detected" in drawing.skip_reason


def test_feat_pdf_003_missing_pdf_and_analyzer_failure(tmp_path: Path) -> None:
    """Verify FEAT-PDF-003: bug_path_1 PDFProcessingError on missing PDF or analyzer crash."""
    out_dir = tmp_path / "out"
    pipeline = PDFProcessingPipeline()
    with pytest.raises(PDFProcessingError, match="PDF not found"):
        pipeline.process(tmp_path / "absent.pdf", out_dir)

    pdf_file = tmp_path / "corrupt.pdf"
    pdf_file.write_bytes(b"%PDF-corrupt")
    bad_analyzer = MagicMock()
    bad_analyzer.analyze.side_effect = RuntimeError("cannot parse xref")
    failing_pipeline = PDFProcessingPipeline(analyzer=bad_analyzer)
    with pytest.raises(PDFProcessingError, match="Analysis failed"):
        failing_pipeline.process(pdf_file, out_dir)


def test_feat_pdf_004_drawing_tiling_and_degraded_branches(tmp_path: Path) -> None:
    """Verify FEAT-PDF-004: bug_path_2 tiling failure and bug_path_3 degraded drawing result."""
    pdf_file = tmp_path / "drawing.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")
    drawing_details = [PageDetail(0, 10, 0, 841.0, 594.0, True, "drawing")]
    report = _make_report(pdf_file, PDFCategory.DRAWING, details=drawing_details)

    analyzer = MagicMock()
    analyzer.analyze.return_value = report

    # bug_path_2: optimizer failure raises PDFProcessingError("Tiling failed...")
    bad_opt = MagicMock()
    bad_opt.tile_page_smart.side_effect = RuntimeError("pixmap overflow")
    p_fail = PDFProcessingPipeline(analyzer=analyzer, optimizer=bad_opt)
    with pytest.raises(PDFProcessingError, match="Tiling failed"):
        p_fail.process(pdf_file, tmp_path / "out_fail")

    # bug_path_3: detector & composer failures degrade gracefully with None paths
    tile_paths = [tmp_path / f"tile_{i}.png" for i in range(4)]
    good_opt = MagicMock()
    good_opt.tile_page_smart.return_value = (tile_paths, [])
    bad_det = MagicMock()
    bad_det.extract.side_effect = ValueError("no title block")
    bad_comp = MagicMock()
    bad_comp.quad_view.side_effect = OSError("composite error")

    p_degraded = PDFProcessingPipeline(
        analyzer=analyzer, optimizer=good_opt, detector=bad_det, composer=bad_comp
    )
    res = p_degraded.process(pdf_file, tmp_path / "out_degraded")
    assert isinstance(res, ProcessingResult)
    assert len(res.tile_paths) == 4
    assert res.titleblock_path is None
    assert res.composite_path is None


def test_feat_pdf_005_statechart_anti_lie_and_live_bug_paths(tmp_path: Path) -> None:
    """Verify FEAT-PDF-005: Statechart Anti-Lie, bug_path parity, and bug_path_4 UNKNOWN replay."""
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

    # bug_path_4: UNKNOWN category returns minimal result with empty chunk/tile lists
    pdf_file = tmp_path / "unknown.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")
    unknown_report = _make_report(pdf_file, PDFCategory.UNKNOWN)
    analyzer = MagicMock()
    analyzer.analyze.return_value = unknown_report

    res = PDFProcessingPipeline(analyzer=analyzer).process(pdf_file, tmp_path / "out_unknown")
    assert res.report.category == PDFCategory.UNKNOWN
    assert res.chunk_paths == []
    assert res.tile_paths == []
    assert len(res.segments) == 1

    # Verify TEXT_RICH chunking path invokes split_pdf cleanly
    text_report = _make_report(pdf_file, PDFCategory.TEXT_RICH)
    analyzer.analyze.return_value = text_report
    fake_chunk = tmp_path / "chunk_0.pdf"
    with patch("ccba_pdf_prep.pipeline.split_pdf", return_value=[fake_chunk]):
        text_res = PDFProcessingPipeline(analyzer=analyzer).process(pdf_file, tmp_path / "out_txt")
    assert text_res.chunk_paths == [fake_chunk]


def test_feat_pdf_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-PDF-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
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
