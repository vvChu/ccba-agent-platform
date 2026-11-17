"""test_mdconverter_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for mdconverter.

Covers all features declared in `verify-ccba-mdconverter/features/INDEX.md`:
- FEAT-MDC-001: PEP 562 Lazy Public Seams & MDConvertError Exception Hierarchy
- FEAT-MDC-002: ConverterRegistry Priority Selection & ValueError on Unknown Extension
- FEAT-MDC-003: ConversionCache Hit/Miss & Missing-File Stale-Index Replay
- FEAT-MDC-004: ConversionPipeline Drawing SKIPPED Branch & PostProcessor Chain
- FEAT-MDC-005: Statechart Anti-Lie, bug_path Parity & Live Asyncio/Segmented Bug Replays
- FEAT-MDC-006: Surface Diff Parity, LF SHA-256 Provenance Lock & Drift Classifier
"""

from __future__ import annotations

import asyncio
import importlib.util
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

import mdconverter
from mdconverter import (
    BaseConverter,
    ConversionCache,
    ConversionPipeline,
    ConversionResult,
    ConverterRegistry,
)
from mdconverter.core.analyzer import PageDetail, PDFReport, Segment
from mdconverter.core.base import ConversionStatus
from mdconverter.core.exceptions import (
    ConversionTimeoutError,
    ConverterNotAvailableError,
    InvalidInputError,
    MDConvertError,
    ProviderError,
)
from mdconverter.core.pipeline import LinkPatcherPostProcessor

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_mdconverter.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_mdconverter.py"
    spec = importlib.util.spec_from_file_location("run_verify_mdconverter", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_mdconverter"] = mod
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


def test_feat_mdc_001_lazy_seams_and_exception_hierarchy() -> None:
    """Verify FEAT-MDC-001: PEP 562 lazy public seams and MDConvertError hierarchy."""
    for symbol in (
        "ConversionPipeline",
        "ConverterRegistry",
        "ConversionCache",
        "BaseConverter",
        "ConversionResult",
        "MDConvertError",
        "get_settings",
    ):
        assert symbol in mdconverter.__all__
        assert getattr(mdconverter, symbol) is not None
    for exc_cls in (
        ConverterNotAvailableError,
        ConversionTimeoutError,
        InvalidInputError,
        ProviderError,
    ):
        assert issubclass(exc_cls, MDConvertError)


def test_feat_mdc_002_converter_registry_priority_and_unknown_extension() -> None:
    """Verify FEAT-MDC-002: Priority selection and bug_path_2 ValueError on unknown ext."""
    saved_convs = dict(ConverterRegistry._converters)
    saved_prio = dict(ConverterRegistry._priority)

    class _DummyConv(BaseConverter):
        SUPPORTED_EXTENSIONS = {".zdemo"}

        async def convert(self, source_path: Path) -> ConversionResult:
            return ConversionResult(source_path=source_path, content="ok")

        def supports(self, file_extension: str) -> bool:
            return file_extension.lower() == ".zdemo"

    class _HighPrioConv(_DummyConv):
        pass

    try:
        ConverterRegistry.register("_low", priority=50)(_DummyConv)
        ConverterRegistry.register("_high", priority=10)(_HighPrioConv)
        selected = ConverterRegistry.auto_select(".zdemo")
        assert isinstance(selected, _HighPrioConv)
        with pytest.raises(ValueError, match="No converter supports extension"):
            ConverterRegistry.auto_select(".xyz_unregistered")
    finally:
        ConverterRegistry._converters = saved_convs
        ConverterRegistry._priority = saved_prio


def test_feat_mdc_003_conversion_cache_hit_miss_and_stale_index_replay(tmp_path: Path) -> None:
    """Verify FEAT-MDC-003: ConversionCache hit/miss and bug_path_4 stale index behavior."""
    src = tmp_path / "sample.txt"
    src.write_text("content-v1", encoding="utf-8")
    cache = ConversionCache(cache_dir=tmp_path / "cache")
    assert cache.get(src) is None

    cache.set(src, "# Converted", tool_used="dummy")
    assert cache.get(src) == "# Converted"

    resolved_key = str(src.resolve())
    cache_key = cache._get_cache_key(src)
    (cache.cache_dir / f"{cache_key}.md").unlink()

    assert cache.get(src) is None
    assert resolved_key in cache._index


def test_feat_mdc_004_pipeline_skip_drawing_and_postprocessors(tmp_path: Path) -> None:
    """Verify FEAT-MDC-004: PDF drawing SKIPPED branch and LinkPatcherPostProcessor."""
    pp = LinkPatcherPostProcessor()
    sample = "Xem [Phụ lục](appendices/phu_luc.md) tại đây."
    assert pp.should_process(sample)
    patched = pp.process(sample)
    assert "(./appendices/phu_luc.md)" in patched

    drawing_pdf = tmp_path / "drawing.pdf"
    drawing_pdf.write_bytes(b"%PDF-1.4")
    fake_report = SimpleNamespace(
        category="drawing",
        pages=1,
        should_skip=True,
        skip_reason="Engineering drawing excluded",
        to_dict=lambda: {"category": "drawing", "pages": 1},
    )
    pipeline = ConversionPipeline(output_dir=tmp_path, extract_drawing=False)

    async def _run_skip() -> ConversionResult:
        with patch.object(pipeline, "_analyze_pdf", AsyncMock(return_value=fake_report)):
            return await pipeline.process_file(drawing_pdf)

    res = asyncio.run(_run_skip())
    assert res.status == ConversionStatus.SKIPPED
    assert res.error_message == "Engineering drawing excluded"


def _replay_segmented_partial_chunk(tmp_path: Path, pipeline: ConversionPipeline) -> None:
    """Replay bug_path_3: failed segment writes [!ERROR] marker while returning SUCCESS."""
    report = MagicMock(spec=PDFReport)
    report.category = "hybrid"
    report.pages = 10
    report.should_skip = False
    report.recommended_model = "ocr-primary"
    report.page_details = [PageDetail(0, 10, 1, 210, 297, False, "scan")]
    report.get_segments.return_value = [
        Segment(0, 4, "text", "tier-fast"),
        Segment(5, 9, "scan", "tier-ocr"),
    ]
    report.to_dict.return_value = {"category": "hybrid", "pages": 10}
    c1, c2 = tmp_path / "p1.pdf", tmp_path / "p2.pdf"
    c1.touch()
    c2.touch()
    m1, m2 = AsyncMock(), AsyncMock()
    m1.convert.return_value = ConversionResult(
        c1, status=ConversionStatus.SUCCESS, content="ok chunk"
    )
    m2.convert.return_value = ConversionResult(
        c2, status=ConversionStatus.FAILED, error_message="boom"
    )

    async def _run_partial() -> ConversionResult:
        with (
            patch("mdconverter.core.pipeline.split_pdf", return_value=[c1, c2]),
            patch.object(pipeline, "_create_converter_for_segment", side_effect=[m1, m2]),
            patch("shutil.rmtree"),
        ):
            return await pipeline._process_segmented(tmp_path / "hybrid.pdf", report)

    seg_out = asyncio.run(_run_partial())
    assert seg_out.status == ConversionStatus.SUCCESS
    assert "> [!ERROR] Failed to convert pages 6-10" in seg_out.content


def test_feat_mdc_005_statechart_anti_lie_and_live_bug_paths(tmp_path: Path) -> None:
    """Verify FEAT-MDC-005: Statechart Anti-Lie, bug_path parity, and live replays 1 & 3."""
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

    pipeline = ConversionPipeline(output_dir=tmp_path)

    async def _call_sync_in_loop() -> None:
        pipeline.convert(tmp_path / "doc.pdf")

    with pytest.raises(RuntimeError, match="cannot be called from within a running event loop"):
        asyncio.run(_call_sync_in_loop())

    _replay_segmented_partial_chunk(tmp_path, pipeline)


def test_feat_mdc_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-MDC-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
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
