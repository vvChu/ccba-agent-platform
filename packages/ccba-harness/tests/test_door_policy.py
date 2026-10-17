"""Unit tests for ccba_harness.door_policy (Issue #519 — Slice 1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.door_policy import (
    ONE_WAY_DOOR_MANIFEST,
    OneWayDoorCategory,
    RecentMergeRecord,
    classify_pr_door,
    compute_cumulative_streak,
    extract_canonical_module,
    is_sampled_for_audit,
    load_recent_merges_from_git,
    match_one_way_categories,
)


def test_manifest_has_all_seven_categories() -> None:
    """Verifies that all 7 required One-Way Door categories are declaratively configured."""
    assert len(OneWayDoorCategory) == 7
    for cat in OneWayDoorCategory:
        assert cat in ONE_WAY_DOOR_MANIFEST
        assert len(ONE_WAY_DOOR_MANIFEST[cat]) > 0


@pytest.mark.parametrize(
    ("file_path", "expected_category"),
    [
        ("docs/schemas/okf_schema.json", OneWayDoorCategory.SCHEMA_MIGRATION),
        ("packages/ccba-maskara/src/ccba_maskara/scrubber.py", OneWayDoorCategory.AUTHZ_SECURITY),
        ("scripts/sync_spoke.py", OneWayDoorCategory.CROSS_SPOKE_CONTRACT),
        ("packages/ccba-harness/src/ccba_harness/__init__.py", OneWayDoorCategory.PUBLIC_API_SEAM),
        ("packages/ccba-ai/src/ccba_ai/pricing_table.py", OneWayDoorCategory.PII_FINANCE_QUOTA),
        ("pyproject.toml", OneWayDoorCategory.DEPENDENCY_LICENSE),
        ("AGENTS.md", OneWayDoorCategory.HUB_CONSTITUTION),
        ("docs/adr/0067-door-policy.md", OneWayDoorCategory.HUB_CONSTITUTION),
    ],
)
def test_match_each_one_way_category(file_path: str, expected_category: OneWayDoorCategory) -> None:
    """Verifies that each of the 7 One-Way Door categories matches its target file patterns."""
    matched = match_one_way_categories([file_path])
    assert expected_category in matched


def test_two_way_door_pure_documentation() -> None:
    """Verifies that pure documentation changes outside constitutional paths classify as TWO_WAY_DOOR."""
    res = classify_pr_door(["README.md", ".md/knowledge/reports/walkthrough.md"], logic_loc=0)
    assert res.door_type == "TWO_WAY_DOOR"
    assert res.matched_categories == []
    assert res.sampled_for_audit is False


def test_paved_road_isolated_code_change() -> None:
    """Verifies that isolated code changes <= 200 LOC outside the 7 categories classify as PAVED_ROAD."""
    res = classify_pr_door(
        ["packages/ccba-harness/src/ccba_harness/blast_radius.py"],
        logic_loc=85,
        pr_number=101,
    )
    assert res.door_type == "PAVED_ROAD"
    assert res.matched_categories == []
    assert res.cumulative_streak == 1
    assert res.escalated_by_streak is False
    assert res.exceeded_loc_budget is False
    assert res.touched_modules == ["packages/ccba-harness"]


def test_loc_budget_exceeded_escalates_to_one_way_door() -> None:
    """Verifies that exceeding max_paved_loc (200 LOC) escalates a Paved Road PR to ONE_WAY_DOOR."""
    res = classify_pr_door(
        ["packages/ccba-harness/src/ccba_harness/blast_radius.py"],
        logic_loc=205,
    )
    assert res.door_type == "ONE_WAY_DOOR"
    assert res.exceeded_loc_budget is True


def test_cumulative_escalation_k_ge_3_triggers_one_way_door() -> None:
    """Verifies that 2 prior unapproved Paved Road merges + current PR (K=3) escalates to ONE_WAY_DOOR."""
    history = [
        RecentMergeRecord(
            pr_number=510,
            merged_hours_ago=12.0,
            touched_modules=["packages/ccba-harness"],
            door_type="PAVED_ROAD",
            taste_holder_approved=False,
        ),
        RecentMergeRecord(
            pr_number=509,
            merged_hours_ago=36.0,
            touched_modules=["packages/ccba-harness"],
            door_type="PAVED_ROAD",
            taste_holder_approved=False,
        ),
    ]
    res = classify_pr_door(
        ["packages/ccba-harness/src/ccba_harness/verifier.py"],
        logic_loc=40,
        recent_merges=history,
    )
    assert res.cumulative_streak == 3
    assert res.escalated_by_streak is True
    assert res.door_type == "ONE_WAY_DOOR"


def test_cumulative_streak_resets_after_taste_holder_approval() -> None:
    """Verifies that a Taste-Holder approved merge resets the cumulative streak for that module."""
    history = [
        RecentMergeRecord(
            pr_number=511,
            merged_hours_ago=5.0,
            touched_modules=["packages/ccba-harness"],
            door_type="PAVED_ROAD",
            taste_holder_approved=False,
        ),
        RecentMergeRecord(
            pr_number=510,
            merged_hours_ago=10.0,
            touched_modules=["packages/ccba-harness"],
            door_type="ONE_WAY_DOOR",
            taste_holder_approved=True,
        ),
        RecentMergeRecord(
            pr_number=509,
            merged_hours_ago=20.0,
            touched_modules=["packages/ccba-harness"],
            door_type="PAVED_ROAD",
            taste_holder_approved=False,
        ),
    ]
    streak = compute_cumulative_streak(["packages/ccba-harness"], history, window_hours=72.0)
    assert streak == 2


def test_deterministic_10_percent_sample_audit_idempotency() -> None:
    """Verifies that deterministic SHA-256 sampling is idempotent and averages ~10% over 1000 PRs."""
    repo = "vvChu/ccba-agent-platform"
    first_run = [is_sampled_for_audit(repo, pr) for pr in range(1, 1001)]
    second_run = [is_sampled_for_audit(repo, pr) for pr in range(1, 1001)]
    assert first_run == second_run
    sampled_count = sum(1 for x in first_run if x)
    assert 70 <= sampled_count <= 130
    assert is_sampled_for_audit(repo, 0) is False


def test_extract_canonical_module_and_git_fallback(tmp_path: Path) -> None:
    """Verifies canonical module extraction and graceful fallback on non-git directories."""
    assert (
        extract_canonical_module("packages/ccba-harness/src/ccba_harness/peer.py")
        == "packages/ccba-harness"
    )
    assert extract_canonical_module("scripts/governance/compile_catalog.py") == "scripts/governance"
    assert (
        extract_canonical_module(".agents/skills/ccba-new-feature/SKILL.md")
        == ".agents/skills/ccba-new-feature"
    )
    assert extract_canonical_module("README.md") == "root"
    assert load_recent_merges_from_git(tmp_path) == []
