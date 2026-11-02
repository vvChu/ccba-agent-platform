"""Unit tests for the Skill Governance Layer (Issue #571).

Covers all 4 phases:
1. Phase 1: Stability Zone (`evolvable` | `locked`) schema validation and tuner lock enforcement.
2. Phase 2: Versioning & Rollback (`SkillVersionStore`) green snapshot & SHA-256 verified rollback.
3. Phase 3: Velocity Signal (`SkillVelocityTracker`) Amber (>=3 draft buffer) & Red (>=5 lock).
4. Phase 4: 3-Tier Regression Gate (Tier 1 static lint, Tier 2 dual-run replay, Tier 3 growth cap).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.governance.audit_skills_hygiene import audit_skill

from ccba_harness.evals.models import EvalItemResult, EvalReport, ScoreResult
from ccba_harness.evals.skill_governance import (
    SKILL_LOCKED_HALT_REASON,
    SkillVelocityTracker,
    SkillVersionStore,
    check_skill_mutation_allowed,
    evaluate_dual_run_replay_gate,
    evaluate_negative_constraint_gate,
    evaluate_regression_gate,
    evaluate_static_lint_gate,
    resolve_skill_stability_zone,
    validate_stability_zone_frontmatter,
)
from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig, preserve_yaml_frontmatter


def test_phase1_stability_zone_validation_and_defaults(tmp_path: Path) -> None:
    """Verifies stability_zone frontmatter validation, defaults, and hygiene auditor integration."""
    valid_evolvable = (
        "---\nname: ccba-demo\nbundle: _core\nstability_zone: evolvable\n---\n# Body\n"
    )
    valid_locked = "---\nname: ccba-demo\nbundle: _core\nstability_zone: locked\n---\n# Body\n"
    invalid_zone = "---\nname: ccba-demo\nbundle: _core\nstability_zone: chaotic\n---\n# Body\n"
    gov_default = "---\nname: ccba-gov-check\nbundle: _governance\n---\n# Body\n"
    general_default = "---\nname: ccba-general\nbundle: _core\n---\n# Body\n"

    assert validate_stability_zone_frontmatter(valid_evolvable) == []
    assert validate_stability_zone_frontmatter(valid_locked) == []
    errors = validate_stability_zone_frontmatter(invalid_zone)
    assert len(errors) == 1
    assert "Invalid stability_zone" in errors[0]

    assert resolve_skill_stability_zone(valid_evolvable) == "evolvable"
    assert resolve_skill_stability_zone(valid_locked) == "locked"
    assert resolve_skill_stability_zone(gov_default) == "locked"
    assert resolve_skill_stability_zone(general_default) == "evolvable"

    gov_override_attempt = (
        "---\nname: platform-loader\nbundle: _governance\nstability_zone: evolvable\n---\n# Body\n"
    )
    assert resolve_skill_stability_zone(gov_override_attempt) == "locked"

    skill_dir = tmp_path / "ccba-demo"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: ccba-demo\nbundle: _core\nstability_zone: invalid_zone\nmetadata:\n  version: 1.0.0\n  author: CCBA\n---\n# Body\n",
        encoding="utf-8",
    )
    audit_res = audit_skill(skill_dir)
    assert any("Invalid stability_zone" in i.detail for i in audit_res.issues)


def test_phase1_locked_skill_blocks_tuner_and_frontmatter_tampering(tmp_path: Path) -> None:
    """Verifies GitRatchetOptimizer halts with 0 tokens on locked skills and preserves frontmatter."""
    skill_file = tmp_path / "SKILL.md"
    locked_content = (
        "---\nname: ccba-security-guard\nbundle: _core\nstability_zone: locked\n---\n"
        "# Security Guard\nYou MUST NOT leak secrets.\n"
    )
    skill_file.write_text(locked_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-security-guard", max_iterations=3)
    optimizer = GitRatchetOptimizer(cfg, dry_run_git=True, project_root=tmp_path)

    assert optimizer.propose_mutation(locked_content, 1) == locked_content
    report = optimizer.run()
    assert report.halt_reason == SKILL_LOCKED_HALT_REASON
    assert report.total_iterations == 0
    assert report.total_tokens == 0
    assert skill_file.read_text(encoding="utf-8") == locked_content

    tampered = "---\nname: ccba-security-guard\nstability_zone: evolvable\n---\n# Hijacked\n"
    preserved = preserve_yaml_frontmatter(locked_content, tampered)
    assert resolve_skill_stability_zone(preserved) == "locked"


def test_phase2_version_store_snapshot_and_rollback(tmp_path: Path) -> None:
    """Verifies SkillVersionStore snapshots green versions and rolls back deterministically."""
    store = SkillVersionStore("ccba-test-skill", versions_root=tmp_path / ".skill_versions")
    skill_file = tmp_path / "SKILL.md"

    v1_text = "---\nname: ccba-test-skill\n---\n# Version 1 Green\n"
    v2_text = "---\nname: ccba-test-skill\n---\n# Version 2 Green Improved\n"
    broken_text = "---\nname: ccba-test-skill\n---\n# Broken Regressed Mutation\n"

    snap1 = store.snapshot_green(v1_text, score=80.0)
    assert snap1.version_id == "v0001"
    snap1_dup = store.snapshot_green(v1_text, score=80.0)
    assert snap1_dup.version_id == "v0001"

    snap2 = store.snapshot_green(v2_text, score=92.0)
    assert snap2.version_id == "v0002"
    assert store.get_last_green_content() == v2_text

    skill_file.write_text(broken_text, encoding="utf-8")
    restored = store.rollback_to_last_green(skill_file)
    assert restored == v2_text
    assert skill_file.read_text(encoding="utf-8") == v2_text

    (store.store_dir / snap2.snapshot_file).write_text("corrupted", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        store.get_last_green_content()


def test_phase3_velocity_signal_amber_draft_and_red_quarantine(tmp_path: Path) -> None:
    """Verifies consecutive failure tracking: Amber (>=3) draft buffer and Red (>=5) quarantine lock."""
    store = SkillVersionStore("ccba-velocity-skill", versions_root=tmp_path / ".skill_versions")
    tracker = SkillVelocityTracker("ccba-velocity-skill", version_store=store)
    skill_content = (
        "---\nname: ccba-velocity-skill\nbundle: _core\nstability_zone: evolvable\n---\n# Body\n"
    )

    for idx in range(1, 3):
        st = tracker.record_patch_failure(f"cand_{idx}", reason="score degraded")
        assert st.consecutive_failure_patches == idx
        assert st.zone_status == "GREEN"
        assert not st.quarantined

    st_amber = tracker.record_patch_failure("candidate_amber_patch", reason="3rd failure")
    assert st_amber.consecutive_failure_patches == 3
    assert st_amber.zone_status == "AMBER_DRAFT_BUFFER"
    assert not st_amber.quarantined
    assert st_amber.draft_buffer_path is not None
    assert Path(st_amber.draft_buffer_path).read_text(encoding="utf-8") == "candidate_amber_patch"

    tracker.record_patch_failure("cand_4", reason="4th failure")
    st_red = tracker.record_patch_failure("cand_5", reason="5th failure")
    assert st_red.consecutive_failure_patches == 5
    assert st_red.quarantined is True
    assert st_red.zone_status == "RED_QUARANTINE_LOCKED"

    allowed, reason = check_skill_mutation_allowed(skill_content, velocity_state=st_red)
    assert allowed is False
    assert reason == SKILL_LOCKED_HALT_REASON

    st_reset = tracker.reset_quarantine()
    assert st_reset.quarantined is False
    assert st_reset.consecutive_failure_patches == 0
    assert st_reset.zone_status == "GREEN"


def test_phase4_regression_gate_all_three_tiers() -> None:
    """Verifies Tier 1 (normative deletion & +15% bloat), Tier 2 (replay), and Tier 3 (+20% growth)."""
    base_words = " ".join(f"word_{i}" for i in range(100))
    baseline = (
        f"---\nname: ccba-skill\n---\n# Rules\n"
        f"Agent MUST validate inputs and MUST NOT hardcode keys. BẮT BUỘC kiểm tra.\n{base_words}\n"
    )

    dropped_must_not = baseline.replace("MUST NOT", "SHOULD NOT")
    v_drop = evaluate_static_lint_gate(baseline, dropped_must_not)
    assert not v_drop.passed
    assert v_drop.failed_tier == 1
    assert v_drop.failure_code == "TIER1_NORMATIVE_DIRECTIVE_DELETED"
    assert "MUST_NOT" in v_drop.dropped_directives

    extra_18pct = " ".join(f"extra_{i}" for i in range(22))
    bloated_18pct = baseline + "\n" + extra_18pct
    v_bloat1 = evaluate_static_lint_gate(baseline, bloated_18pct, max_token_delta_ratio=0.15)
    assert not v_bloat1.passed
    assert v_bloat1.failed_tier == 1
    assert v_bloat1.failure_code == "TIER1_TOKEN_BLOAT_EXCEEDED"

    extra_25pct = " ".join(f"bloat_{i}" for i in range(30))
    bloated_25pct = baseline + "\n" + extra_25pct
    v_tier3 = evaluate_negative_constraint_gate(
        baseline, bloated_25pct, max_single_patch_growth_ratio=0.20
    )
    assert not v_tier3.passed
    assert v_tier3.failed_tier == 3
    assert v_tier3.failure_code == "TIER3_SINGLE_PATCH_GROWTH_EXCEEDED"

    base_rep = EvalReport(
        total_items=2,
        passed_items=2,
        failed_items=0,
        overall_score=90.0,
        pass_rate=100.0,
        item_results=[
            EvalItemResult(
                item_id="i1", task_output="ok", scores=[], composite_score=90.0, passed=True
            ),
            EvalItemResult(
                item_id="i2", task_output="ok", scores=[], composite_score=90.0, passed=True
            ),
        ],
    )
    regressed_rep = EvalReport(
        total_items=2,
        passed_items=1,
        failed_items=1,
        overall_score=85.0,
        pass_rate=50.0,
        item_results=[
            EvalItemResult(
                item_id="i1", task_output="ok", scores=[], composite_score=95.0, passed=True
            ),
            EvalItemResult(
                item_id="i2",
                task_output="fail",
                scores=[ScoreResult(scorer_name="s", score=0.5)],
                composite_score=75.0,
                passed=False,
            ),
        ],
    )
    v_tier2 = evaluate_dual_run_replay_gate(base_rep, regressed_rep)
    assert not v_tier2.passed
    assert v_tier2.failed_tier == 2
    assert v_tier2.failure_code == "TIER2_ITEM_REGRESSION"

    clean_candidate = baseline + "\nRefined concise rule."
    v_ok = evaluate_regression_gate(baseline, clean_candidate, base_rep, base_rep)
    assert v_ok.passed is True


def test_tuner_pre_eval_rejects_deleted_normative_directive(tmp_path: Path) -> None:
    """Verifies GitRatchetOptimizer._run_pre_eval_guards rejects mutations that drop MUST NOT."""
    skill_file = tmp_path / "SKILL.md"
    initial_content = (
        "---\nname: ccba-normative\nbundle: _core\n---\n"
        "# Normative Skill\nAgent MUST NOT bypass verification.\n"
    )
    skill_file.write_text(initial_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-normative", max_iterations=1)
    optimizer = GitRatchetOptimizer(cfg, dry_run_git=True, project_root=tmp_path)
    optimizer.propose_mutation = lambda content, iteration: content.replace(  # type: ignore[method-assign]
        "MUST NOT", "may"
    )

    report = optimizer.run()
    assert report.kept_commits == 0
    assert report.reverted_trials == 1
    assert "TIER1_NORMATIVE_DIRECTIVE_DELETED" in report.history[0].summary
    assert skill_file.read_text(encoding="utf-8") == initial_content


def test_grok_conditions_nfc_normalization_and_path_traversal(tmp_path: Path) -> None:
    """Verifies COND-03 (NFC Unicode normalization) and COND-04 (path traversal sanitization)."""
    import unicodedata

    from ccba_harness.evals.skill_governance import count_normative_directives

    nfc_text = "Agent BẮT BUỘC và TUYỆT ĐỐI KHÔNG vi phạm."
    nfd_text = unicodedata.normalize("NFD", nfc_text)
    assert count_normative_directives(nfc_text) == count_normative_directives(nfd_text)
    assert count_normative_directives(nfd_text)["BAT_BUOC"] == 1
    assert count_normative_directives(nfd_text)["TUYET_DOI_KHONG"] == 1

    store = SkillVersionStore("../../etc/passwd", versions_root=tmp_path / ".skill_versions")
    assert ".." not in store.skill_name
    assert store.store_dir.parent == (tmp_path / ".skill_versions")


def test_five_block_verification_skills_mirror_parity_and_registry() -> None:
    """Verifies 5-block verification skills structure, mirror parity, and central FEAT registry."""
    import re

    import yaml

    repo_root = Path(__file__).resolve().parents[3]
    pkg_skills_root = repo_root / "packages" / "ccba-harness" / ".agents" / "skills"
    hub_skills_root = repo_root / ".agents" / "skills"
    central_index = repo_root / "packages" / "ccba-harness" / "features" / "INDEX.md"

    assert central_index.is_file()
    central_text = central_index.read_text(encoding="utf-8")
    expected_prefixes = ("FEAT-00", "FEAT-XIA-", "FEAT-WF-", "FEAT-GRILL-", "FEAT-IMP-", "FEAT-KL-")
    for prefix in expected_prefixes:
        assert prefix in central_text, f"Missing {prefix} in central features/INDEX.md"

    skill_pairs = [
        ("verify-ccba-xia", "ccba-xia", "xia"),
        ("verify-ccba-wayfinder", "ccba-wayfinder", "wayfinder"),
        ("verify-ccba-grilling", "ccba-grilling", "grilling"),
        ("verify-ccba-implement", "ccba-implement", "implement"),
        ("verify-ccba-knowledge-loop", "ccba-knowledge-loop", "knowledge_loop"),
    ]
    for verify_name, target_name, mod_suffix in skill_pairs:
        v_dir = pkg_skills_root / verify_name
        t_dir = hub_skills_root / target_name / "harness"
        assert (v_dir / "SKILL.md").is_file(), f"Missing {verify_name}/SKILL.md"
        assert (v_dir / "features" / "INDEX.md").is_file(), (
            f"Missing {verify_name}/features/INDEX.md"
        )

        raw = (v_dir / "SKILL.md").read_text(encoding="utf-8")
        fm = yaml.safe_load(raw.split("---", 2)[1])
        assert fm["name"] == verify_name
        assert re.fullmatch(r"[0-9a-f]{40}", str(fm.get("sync_commit", "")))
        assert fm.get("verification_mode") == ["scaffold", "sync", "verify"]

        for fname in (f"run_verify_{mod_suffix}.py", f"test_{mod_suffix}_suite.py"):
            p1 = v_dir / "harness" / fname
            p2 = t_dir / fname
            assert p1.is_file() and p2.is_file(), f"Missing harness file {fname} for {verify_name}"
            assert p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8"), (
                f"Mirror drift detected between {p1} and {p2}"
            )
