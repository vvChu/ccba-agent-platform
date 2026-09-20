"""test_slicing.py - Unit tests for Three-Tier Adaptive Slicing and Dynamic Perturbation Engine (TICKET-006)."""

from __future__ import annotations

from pathlib import Path

from ccba_harness.evals.models import EvalItem
from ccba_harness.evals.slicing import (
    AdaptiveDataSlicer,
    DynamicPerturbationEngine,
    SlicedDataset,
    SlicingTier,
    classify_slicing_tier,
)
from ccba_harness.evals.tuner import (
    GitRatchetOptimizer,
    RatchetConfig,
)


def test_classify_slicing_tier():
    """Verify tier classification boundaries."""
    assert classify_slicing_tier(0) == SlicingTier.TIER_A
    assert classify_slicing_tier(5) == SlicingTier.TIER_A
    assert classify_slicing_tier(11) == SlicingTier.TIER_A

    assert classify_slicing_tier(12) == SlicingTier.TIER_B
    assert classify_slicing_tier(20) == SlicingTier.TIER_B
    assert classify_slicing_tier(29) == SlicingTier.TIER_B

    assert classify_slicing_tier(30) == SlicingTier.TIER_C
    assert classify_slicing_tier(100) == SlicingTier.TIER_C


def test_adaptive_slicer_tier_a_100_percent_evaluation():
    """Verify Tier A (<12 items) retains 100% of items for tuning with 0 holdout starvation."""
    items = [
        EvalItem(id=f"item_{i}", input_prompt=f"Prompt {i}", golden_answer="Answer")
        for i in range(6)
    ]
    slicer = AdaptiveDataSlicer()
    sliced = slicer.slice(items, split_ratio=0.7, seed=42)

    assert isinstance(sliced, SlicedDataset)
    assert sliced.tier == SlicingTier.TIER_A
    assert sliced.tuning_size == 6
    assert sliced.holdout_size == 0
    assert len(sliced.tuning_items) == 6
    assert len(sliced.holdout_items) == 0


def test_adaptive_slicer_tier_b_stratified_split():
    """Verify Tier B (12 <= N < 30) splits 70% tuning / 30% holdout with stratified balance."""
    items = []
    # 8 items with verdict KHONG_DAT, 4 items with verdict DAT (total 12)
    for i in range(8):
        items.append(
            EvalItem(
                id=f"fail_{i}",
                input_prompt=f"Prompt fail {i}",
                metadata={"parametric_rules": {"expected_verdict": "KHONG_DAT"}},
            )
        )
    for i in range(4):
        items.append(
            EvalItem(
                id=f"pass_{i}",
                input_prompt=f"Prompt pass {i}",
                metadata={"parametric_rules": {"expected_verdict": "DAT"}},
            )
        )

    slicer = AdaptiveDataSlicer()
    sliced = slicer.slice(items, split_ratio=0.7, seed=42)

    assert sliced.tier == SlicingTier.TIER_B
    assert sliced.tuning_size == 8
    assert sliced.holdout_size == 4

    # Check stratification: both sets should contain both verdicts
    tuning_verdicts = {
        item.metadata.get("parametric_rules", {}).get("expected_verdict")
        for item in sliced.tuning_items
    }
    holdout_verdicts = {
        item.metadata.get("parametric_rules", {}).get("expected_verdict")
        for item in sliced.holdout_items
    }
    assert "KHONG_DAT" in tuning_verdicts and "DAT" in tuning_verdicts
    assert "KHONG_DAT" in holdout_verdicts and "DAT" in holdout_verdicts


def test_adaptive_slicer_tier_c_blinded_multi_seed():
    """Verify Tier C (N >= 30) splits 70/30 deterministically according to seed."""
    items = [
        EvalItem(id=f"item_{i:02d}", input_prompt=f"Prompt {i}")
        for i in range(40)
    ]
    slicer = AdaptiveDataSlicer()
    sliced1 = slicer.slice(items, split_ratio=0.7, seed=42)
    sliced2 = slicer.slice(items, split_ratio=0.7, seed=42)
    sliced_diff = slicer.slice(items, split_ratio=0.7, seed=999)

    assert sliced1.tier == SlicingTier.TIER_C
    assert sliced1.tuning_size == 28
    assert sliced1.holdout_size == 12

    # Deterministic with same seed
    ids1 = [it.id for it in sliced1.tuning_items]
    ids2 = [it.id for it in sliced2.tuning_items]
    assert ids1 == ids2

    # Different seed produces different split
    ids_diff = [it.id for it in sliced_diff.tuning_items]
    assert ids1 != ids_diff


def test_dynamic_perturbation_engine_deterministic_and_varying():
    """Verify DynamicPerturbationEngine perturbs parametric numbers deterministically."""
    engine = DynamicPerturbationEngine()
    prompt = "Hành lang dài 28m trong nhà F1.3 không có hút khói sự cố."

    res1 = engine.perturb_prompt(prompt, seed=42)
    res2 = engine.perturb_prompt(prompt, seed=42)
    res3 = engine.perturb_prompt(prompt, seed=123)

    assert res1 == res2, "Same seed must produce identical perturbed prompt"
    assert res1 != res3, "Different seed should produce different perturbation"
    assert "hành lang" in res1.lower()
    assert "m" in res1


def test_dynamic_perturbation_engine_preserves_regulatory_invariant():
    """Verify perturbation keeps corridor length within non-compliant regime (>15m)."""
    engine = DynamicPerturbationEngine()
    prompt = "Thẩm tra hành lang dài 28m không hút khói theo QCVN 06:2022"

    for s in [1, 7, 42, 99, 2026]:
        perturbed = engine.perturb_prompt(prompt, seed=s)
        # Verify length extracted is strictly > 15m to preserve regulatory invariant
        import re
        m = re.search(r"(\d+)\s*m", perturbed)
        assert m is not None
        val = int(m.group(1))
        assert val > 15, f"Perturbed length {val}m should maintain non-compliance invariant (>15m)"


def test_dynamic_perturbation_item_and_dataset():
    """Verify perturbing EvalItem and list of EvalItems."""
    engine = DynamicPerturbationEngine()
    item = EvalItem(
        id="item_orig",
        input_prompt="Khoảng hở bảo trì máy bơm 900mm theo tiêu chuẩn.",
        metadata={"category": "MEP"},
    )
    perturbed_item = engine.perturb_item(item, seed=42)
    assert perturbed_item.id.startswith("item_orig_p")
    assert perturbed_item.metadata.get("is_perturbed") is True
    assert perturbed_item.metadata.get("category") == "MEP"


def test_git_ratchet_optimizer_three_tier_adaptive_slicing_integration(tmp_path: Path):
    """Verify GitRatchetOptimizer splits dataset and records slicing metadata and holdout score."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: ccba-ai-qc-pccc-audit\n---\n# PCCC Audit Skill\nĐạt chuẩn QCVN 06:2022/BXD.",
        encoding="utf-8",
    )

    # Use actual 12 items dataset
    dataset_file = (
        Path(__file__).resolve().parent.parent.parent.parent
        / ".agents"
        / "skills"
        / "ccba-eval-gate"
        / "test_cases"
        / "eval_pccc_audit.json"
    )
    assert dataset_file.exists()

    cfg = RatchetConfig(
        target_file=skill_file,
        eval_dataset_file=dataset_file,
        skill_name="ccba-ai-qc-pccc-audit",
        max_iterations=1,
    )

    opt = GitRatchetOptimizer(
        config=cfg,
        dry_run_git=True,
        project_root=tmp_path,
    )

    report = opt.run()
    assert report.slicing_tier == "TIER_B"
    assert report.tuning_size == 8
    assert report.holdout_size == 4
    assert report.holdout_score is not None
    assert isinstance(report.holdout_score, float)
    assert 0.0 <= report.holdout_score <= 100.0
