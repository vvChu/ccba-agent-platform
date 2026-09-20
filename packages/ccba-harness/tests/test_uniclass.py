"""Unit tests for Uniclass 200 & ISO 12006-2 Flat Index and BimClassificationScorer (TICKET-005)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.evals import (
    BimClassificationScorer,
    EvalItem,
    UniclassFlatIndex,
    get_bim_classification_scorers,
    load_eval_dataset,
    load_uniclass_flat_index,
)


def test_uniclass_flat_index_loads_and_lookups() -> None:
    """Test Uniclass flat index loads correctly and supports fast lookups."""
    index = load_uniclass_flat_index()
    assert isinstance(index, UniclassFlatIndex)
    assert len(index.entries_by_code) >= 50

    # Test exact lookups across core tables
    entry_ef = index.lookup_code("EF_20_10_15")
    assert entry_ef is not None
    assert "Cột" in entry_ef.title_vi
    assert entry_ef.table == "EF"
    assert "Result" in entry_ef.iso_12006_layer

    entry_sl = index.lookup_code("SL_25_10_72")
    assert entry_sl is not None
    assert "Phòng" in entry_sl.title_vi or "đọc" in entry_sl.title_vi
    assert entry_sl.table == "SL"

    entry_ss = index.lookup_code("Ss_60_40_36")
    assert entry_ss is not None
    assert entry_ss.table == "Ss"

    entry_pr = index.lookup_code("Pr_60_65_62")
    assert entry_pr is not None
    assert entry_pr.table == "Pr"
    assert "Resource" in entry_pr.iso_12006_layer

    # Test case-insensitivity and hyphen normalization
    entry_lower = index.lookup_code("ef_20_10_15")
    assert entry_lower is not None
    assert entry_lower.code == "EF_20_10_15"

    entry_hyphen = index.lookup_code("EF-20-10-15")
    assert entry_hyphen is not None
    assert entry_hyphen.code == "EF_20_10_15"

    # Test invalid code
    assert index.lookup_code("XX_99_99_99") is None
    assert not index.is_valid_code("INVALID_CODE")
    assert index.is_valid_code("EF_20_10_15")


def test_extract_uniclass_codes() -> None:
    """Test extracting Uniclass 200 code tokens from unstructured text."""
    index = load_uniclass_flat_index()
    text = (
        "Cấu kiện cột bê tông EF_20_10_15 kết nối với hệ dầm EF_20_20. "
        "Vật tư sử dụng bơm Pr_60_65_62 đặt tại phòng SL_25_10_72. "
        "Hệ thống điều hòa Ss_60_40_36 đã được phê duyệt."
    )
    extracted = index.extract_uniclass_codes(text)
    assert "EF_20_10_15" in extracted
    assert "EF_20_20" in extracted
    assert "PR_60_65_62" in extracted
    assert "SL_25_10_72" in extracted
    assert "SS_60_40_36" in extracted


def test_naming_conventions_validation() -> None:
    """Test ISO 19650 container and IFC Alignment linear naming validators."""
    index = load_uniclass_flat_index()

    # Valid ISO 19650 room container names
    assert index.validate_iso_19650_naming("HUB-LIB-B1-L03-SL_25_10_72-002")
    assert index.validate_iso_19650_naming("SKY-PARK-TWR-A-L05-SL_25_30_80-001")
    assert not index.validate_iso_19650_naming("Room-101-Library")
    assert not index.validate_iso_19650_naming("HUB-SL_25_10_72")

    # Valid IFC Alignment linear infrastructure names
    assert index.validate_ifc_alignment_naming("CT01-KM015_350-P04-EF_20_10")
    assert index.validate_ifc_alignment_naming("CT05-KM002_150_KM002_450-EF_10_10")
    assert not index.validate_ifc_alignment_naming("highway_pier_p04")


def test_anti_traps_detection() -> None:
    """Test detection of redteam anti-traps defined in Uniclass flat index."""
    index = load_uniclass_flat_index()

    # Trap 1: Hybrid shaft misclassification
    trap1_text = "Hộp kỹ thuật trục đứng phân loại là Ss_50 chứa các đường ống MEP."
    has_trap, reason = index.check_anti_traps(trap1_text)
    assert has_trap
    assert "Anti-Trap" in str(reason)

    # Trap 3: Element vs Product confusion
    trap3_text = "Thực hiện bóc tách khối lượng EF_25_30 thành Pr_30_59_24 cho mô hình."
    has_trap, reason = index.check_anti_traps(trap3_text)
    assert has_trap

    # Clean text without anti-traps
    clean_text = (
        "Cấu kiện cột chịu lực EF_20_10_15 thuộc lớp Result theo ISO 12006-2. "
        "Đặt tên phòng theo ISO 19650 là HUB-LIB-B1-L03-SL_25_10_72-002."
    )
    has_trap, reason = index.check_anti_traps(clean_text)
    assert not has_trap
    assert reason is None


@pytest.mark.asyncio
async def test_bim_classification_scorer_valid() -> None:
    """Test BimClassificationScorer scoring clean valid output."""
    scorer = BimClassificationScorer()
    item = EvalItem(
        id="test_01",
        input_prompt="Phân loại cấu kiện cột và đặt tên container",
        golden_answer={
            "uniclass_code": "EF_20_10_15",
            "iso_12006_layer": "Result (Elements)",
            "iso_19650_naming": "HUB-LIB-B1-L03-SL_25_10_72-002",
        },
    )
    output = (
        "Theo chuẩn phân loại Uniclass 200, cấu kiện cột chịu lực bê tông cốt thép có mã là EF_20_10_15. "
        "Theo tiêu chuẩn ISO 12006-2, cấu kiện này thuộc lớp Result (Elements). "
        "Mã container đặt theo tiêu chuẩn ISO 19650: HUB-LIB-B1-L03-SL_25_10_72-002."
    )
    result = await scorer.score(output, item)
    assert result.score >= 0.8
    assert not result.is_critical_fail
    assert result.raw_output["expected_code"] == "EF_20_10_15"


@pytest.mark.asyncio
async def test_bim_classification_scorer_anti_trap_critical_fail() -> None:
    """Test BimClassificationScorer triggers critical 0.0 on anti-trap violations."""
    scorer = BimClassificationScorer()
    item = EvalItem(
        id="test_trap",
        input_prompt="Phân loại hộp kỹ thuật trục đứng",
        golden_answer={"uniclass_code": "EF_25_10"},
    )
    output = "Hộp kỹ thuật trục đứng phân loại là Ss_55 chứa hệ thống chữa cháy."
    result = await scorer.score(output, item)
    assert result.score == 0.0
    assert result.is_critical_fail
    assert "Anti-Trap" in result.reasoning


@pytest.mark.asyncio
async def test_bim_classification_scorer_missing_code_partial_score() -> None:
    """Test BimClassificationScorer awards partial score without critical fail when expected code is absent."""
    scorer = BimClassificationScorer()
    item = EvalItem(
        id="test_missing",
        input_prompt="Phân loại cấu kiện cột",
        golden_answer={"uniclass_code": "EF_20_10_15"},
    )
    output = "Đây là một cấu kiện chung không có mã Uniclass cụ thể."
    result = await scorer.score(output, item)
    assert not result.is_critical_fail
    assert result.score == 0.27


def test_get_bim_classification_scorers_suite() -> None:
    """Test standard BIM classification scorer suite configuration."""
    suite = get_bim_classification_scorers()
    names = [s.name for s in suite]
    assert "bim_classification" in names
    assert "progressive_disclosure_links" in names
    assert "anti_debris" in names
    assert "depth" in names
    total_weight = sum(s.weight for s in suite)
    assert pytest.approx(total_weight, rel=1e-2) == 1.0


@pytest.mark.asyncio
async def test_eval_bigbim_classification_dataset_evaluates_cleanly() -> None:
    """Test evaluating items against eval_bigbim_classification.json dataset."""
    from ccba_harness.evals import EvalRunner

    dataset_path = Path(".agents/skills/ccba-eval-gate/test_cases/eval_bigbim_classification.json")
    if not dataset_path.exists():
        pytest.skip("eval_bigbim_classification.json not found")

    items = load_eval_dataset(dataset_path)
    assert len(items) >= 5

    item0 = items[0]
    output0 = (
        f"Theo phân loại Uniclass 200, mã phòng đọc sách là {item0.golden_answer['uniclass_code']}. "
        f"Lớp phân loại theo ISO 12006-2 là Result. "
        f"Mã Information Container theo ISO 19650 là {item0.golden_answer['iso_19650_naming']}.\n"
        f"Tham khảo quy chuẩn chi tiết: [ISO 19650 Documentation](file:///docs/iso19650.md)"
    )

    runner = EvalRunner()
    res = await runner.run(
        [item0], lambda it: output0, scorers=get_bim_classification_scorers(), pass_threshold=75.0
    )
    assert res.overall_score >= 75.0
    assert res.passed_items == 1
