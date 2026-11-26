"""test_eval_guards_and_quarantine_v2.py - Regression & contract tests for Wave 0 (Issue #910).

Covers:
1. VelocitySignalState v1->v2 one-time quarantine reset, load_state(None, None) preservation,
   SHA-256 drift auto-reset on run()/run_async(), and FailureKind quarantine accounting.
2. Post-baseline Sanity Gate (ORACLE_MISMATCH_HALT & ALREADY_OPTIMAL_SKIP at 0 mutation tokens).
3. Hard Holdout Gate BEFORE git_commit_improvement (sync & async, Tier-A rejection, error rollback)
   and zero .skill_versions disk writes under dry_run_git=True.
4. Dedicated router_advisor archetype, boundary regex matching (COND-ROUTER-MATCH-INPUT),
   and eval_ccba_ask.json 12-case Tier-B (8/4) calibration.
5. Fail-closed daemon guards (UNCONFIGURED skip, MOCK_SIMULATOR_FORBIDDEN, Draft PR, /boost gate).
6. Single-skill CI Token Ratchet Gate (COND-TOKEN-GATE) and prohibition coverage gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ccba_harness.evals._eval_guards import (
    FailureKind,
    compute_dataset_sha256,
    compute_lf_sha256,
    is_eligible_for_boost_escalation,
    run_ci_ratchet_post_mutation_gate,
)
from ccba_harness.evals.archetypes import (
    get_default_domain_scorers,
    resolve_domain_archetype,
    resolve_domain_dataset,
    resolve_domain_dataset_contract,
)
from ccba_harness.evals.daemon import NightlyTunerDaemon, SkillEvolutionSummary
from ccba_harness.evals.models import EvalItem, EvalItemResult, EvalReport
from ccba_harness.evals.runner import EvalRunner, load_eval_dataset
from ccba_harness.evals.simulation import build_mock_agent_task
from ccba_harness.evals.skill_governance import (
    SKILL_LOCKED_HALT_REASON,
    VELOCITY_SCHEMA_VERSION,
    SkillVelocityTracker,
    SkillVersionStore,
    evaluate_static_lint_gate,
    resolve_skill_stability_zone,
)
from ccba_harness.evals.slicing import AdaptiveDataSlicer, SlicingTier
from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig

pytestmark = [pytest.mark.fast, pytest.mark.unit]

_PAD = " ".join(f"policy_{i}" for i in range(400))


def _make_report(score: float, total_items: int = 1, crit: bool = False) -> EvalReport:
    return EvalReport(
        total_items=total_items,
        passed_items=total_items if score >= 90.0 and not crit else 0,
        failed_items=0 if score >= 90.0 and not crit else total_items,
        overall_score=score,
        pass_rate=100.0 if score >= 90.0 and not crit else 0.0,
        item_results=[
            EvalItemResult(
                item_id=f"i{idx}",
                task_output="ok",
                scores=[],
                composite_score=score,
                passed=(score >= 90.0 and not crit),
                critical_failed=crit,
            )
            for idx in range(total_items)
        ],
    )


def test_velocity_v1_one_time_reset_and_v2_preservation(tmp_path: Path) -> None:
    """Legacy v1 sidecar without schema_version resets once to v2; load_state() preserves v2."""
    store = SkillVersionStore("ccba-ask", versions_root=tmp_path / ".skill_versions")
    tracker = SkillVelocityTracker("ccba-ask", version_store=store)
    tracker.state_path.parent.mkdir(parents=True, exist_ok=True)

    # Legacy v1 quarantined state (missing schema_version key)
    legacy_v1 = {
        "skill_name": "ccba-ask",
        "consecutive_failure_patches": 5,
        "total_keeps": 0,
        "total_failures": 5,
        "quarantined": True,
        "zone_status": "RED_QUARANTINE_LOCKED",
    }
    tracker.state_path.write_text(json.dumps(legacy_v1), encoding="utf-8")

    migrated = tracker.load_state()
    assert migrated.schema_version == VELOCITY_SCHEMA_VERSION
    assert migrated.quarantined is False
    assert migrated.zone_status == "GREEN"
    assert migrated.consecutive_failure_patches == 0

    # Re-trip quarantine under v2 using counting failures
    for idx in range(5):
        tracker.record_patch_failure(
            f"bad_{idx}", reason="regressed", failure_kind=FailureKind.MUTATION_REGRESSION.value
        )
    st_locked = tracker.load_state()
    assert st_locked.schema_version == 2
    assert st_locked.quarantined is True
    assert st_locked.zone_status == "RED_QUARANTINE_LOCKED"

    # Non-counting failures NEVER increment counters on a fresh tracker
    store2 = SkillVersionStore("ccba-fresh", versions_root=tmp_path / ".skill_versions")
    tracker2 = SkillVelocityTracker("ccba-fresh", version_store=store2)
    for kind in (FailureKind.ORACLE_INVALID, FailureKind.INFRA_ERROR, FailureKind.ALREADY_OPTIMAL):
        st2 = tracker2.record_patch_failure("x", reason="infra", failure_kind=kind.value)
        assert st2.consecutive_failure_patches == 0
        assert st2.total_failures == 0
        assert st2.quarantined is False


def test_velocity_sha256_auto_reset_on_run_and_dry_run_no_disk_write(tmp_path: Path) -> None:
    """run() passes (content_sha, dataset_sha) to auto-reset v2 quarantine on drift; dry_run writes 0 files."""
    skill_file = tmp_path / "SKILL.md"
    v1_body = f"---\nname: ccba-demo\nstability_zone: evolvable\n---\n# Demo v1\n{_PAD}\n"
    skill_file.write_text(v1_body, encoding="utf-8")
    ds = [EvalItem(id="d1", input_prompt="Prompt 1", golden_answer="Ans")]

    # Seed a v2 quarantined sidecar tied to v1_body + ds
    store = SkillVersionStore("ccba-demo", versions_root=tmp_path / ".skill_versions")
    tracker = SkillVelocityTracker("ccba-demo", version_store=store)
    st = tracker.load_state(
        content_sha256=compute_lf_sha256(v1_body), dataset_sha256=compute_dataset_sha256(ds)
    )
    st.quarantined = True
    st.consecutive_failure_patches = 5
    st.zone_status = "RED_QUARANTINE_LOCKED"
    tracker.save_state(st)

    # Same hashes -> stays locked
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-demo", max_iterations=1)
    opt_same = GitRatchetOptimizer(cfg, dry_run_git=False, project_root=tmp_path, dataset=ds)
    rep_same = opt_same.run()
    assert rep_same.halt_reason == SKILL_LOCKED_HALT_REASON

    # Modify SKILL.md -> hash changes -> quarantine auto-resets and baseline runs
    v2_body = v1_body + "\nUpdated rule.\n"
    skill_file.write_text(v2_body, encoding="utf-8")
    opt_changed = GitRatchetOptimizer(cfg, dry_run_git=False, project_root=tmp_path, dataset=ds)
    opt_changed.evaluate_content = MagicMock(return_value=_make_report(100.0))  # type: ignore[method-assign]
    rep_changed = opt_changed.run()
    assert rep_changed.halt_reason == "ALREADY_OPTIMAL_SKIP"
    assert tracker.load_state().quarantined is False

    # dry_run_git=True must NOT create .skill_versions beside SKILL.md
    dry_dir = tmp_path / "dry_isolation"
    dry_dir.mkdir()
    dry_skill = dry_dir / "SKILL.md"
    dry_skill.write_text(v2_body, encoding="utf-8")
    cfg_dry = RatchetConfig(target_file=dry_skill, skill_name="ccba-dry", max_iterations=1)
    opt_dry = GitRatchetOptimizer(cfg_dry, dry_run_git=True, project_root=dry_dir, dataset=ds)
    opt_dry.evaluate_content = MagicMock(return_value=_make_report(100.0))  # type: ignore[method-assign]
    opt_dry.run()
    assert not (dry_dir / ".skill_versions").exists()


def test_baseline_sanity_gate_oracle_mismatch_and_already_optimal(tmp_path: Path) -> None:
    """baseline <= 0 -> ORACLE_MISMATCH_HALT; baseline >= target -> ALREADY_OPTIMAL_SKIP (0 muts)."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        f"---\nname: ccba-sanity\nstability_zone: evolvable\n---\n# Sanity\n{_PAD}\n",
        encoding="utf-8",
    )
    ds = [EvalItem(id="s1", input_prompt="Q", golden_answer="A")]
    cfg = RatchetConfig(
        target_file=skill_file, skill_name="ccba-sanity", target_score=90.0, max_iterations=3
    )

    opt_zero = GitRatchetOptimizer(cfg, dry_run_git=True, project_root=tmp_path, dataset=ds)
    opt_zero.evaluate_content = MagicMock(return_value=_make_report(0.0))  # type: ignore[method-assign]
    rep_zero = opt_zero.run()
    assert rep_zero.halt_reason == "ORACLE_MISMATCH_HALT"
    assert rep_zero.total_iterations == 0
    assert opt_zero.evaluate_content.call_count == 1

    opt_opt = GitRatchetOptimizer(cfg, dry_run_git=True, project_root=tmp_path, dataset=ds)
    opt_opt.evaluate_content = MagicMock(return_value=_make_report(95.0))  # type: ignore[method-assign]
    rep_opt = opt_opt.run()
    assert rep_opt.halt_reason == "ALREADY_OPTIMAL_SKIP"
    assert rep_opt.total_iterations == 0
    assert opt_opt.evaluate_content.call_count == 1


@pytest.mark.asyncio
async def test_hard_holdout_gate_blocks_commit_before_git_sync_and_async(tmp_path: Path) -> None:
    """Holdout drop, holdout error, or Tier-A empty holdout blocks git_commit_improvement."""
    skill_file = tmp_path / "SKILL.md"
    base = f"---\nname: ccba-ho\nstability_zone: evolvable\n---\n# Holdout Gate\n{_PAD}\n"
    skill_file.write_text(base, encoding="utf-8")
    tune_ds = [EvalItem(id="t1", input_prompt="Tune")]
    ho_ds = [EvalItem(id="h1", input_prompt="Holdout")]

    # 1. Sync: tuning improves 50->90, holdout drops 80->60 -> NO commit, rollback
    cfg = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-ho",
        target_score=100.0,
        max_iterations=1,
        require_holdout_for_keep=True,
    )
    opt_sync = GitRatchetOptimizer(cfg, dry_run_git=True, project_root=tmp_path, dataset=tune_ds)
    opt_sync.holdout_dataset = ho_ds
    opt_sync.propose_mutation = MagicMock(return_value=base + "\nAdded rule.")  # type: ignore[method-assign]
    opt_sync.git_commit_improvement = MagicMock(return_value=True)  # type: ignore[method-assign]

    ho_calls = 0

    def eval_drop(content: str, dataset: list[EvalItem] | None = None) -> EvalReport:
        nonlocal ho_calls
        if dataset is ho_ds:
            ho_calls += 1
            return _make_report(80.0 if ho_calls == 1 else 60.0)
        return _make_report(90.0 if "Added rule." in content else 50.0)

    opt_sync.evaluate_content = eval_drop  # type: ignore[method-assign]
    rep_sync = opt_sync.run()
    assert rep_sync.kept_commits == 0
    assert rep_sync.reverted_trials == 1
    assert opt_sync.git_commit_improvement.call_count == 0
    assert skill_file.read_text(encoding="utf-8") == base

    # 2. Async: holdout raises on candidate -> NO commit, rollback
    opt_async = GitRatchetOptimizer(cfg, dry_run_git=True, project_root=tmp_path, dataset=tune_ds)
    opt_async.holdout_dataset = ho_ds
    opt_async.propose_mutation = MagicMock(return_value=base + "\nAsync rule.")  # type: ignore[method-assign]
    opt_async.git_commit_improvement = MagicMock(return_value=True)  # type: ignore[method-assign]
    a_ho_calls = 0

    async def eval_err(content: str, dataset: list[EvalItem] | None = None) -> EvalReport:
        nonlocal a_ho_calls
        if dataset is ho_ds:
            a_ho_calls += 1
            if a_ho_calls == 1:
                return _make_report(80.0)
            raise RuntimeError("Holdout crash")
        return _make_report(90.0 if "Async rule." in content else 50.0)

    opt_async.evaluate_content_async = eval_err  # type: ignore[method-assign]
    rep_async = await opt_async.run_async()
    assert rep_async.kept_commits == 0
    assert opt_async.git_commit_improvement.call_count == 0
    assert "lỗi chấm holdout" in rep_async.history[0].summary

    # 3. Tier-A (holdout_size == 0) with require_holdout_for_keep=True -> NO commit
    opt_tier_a = GitRatchetOptimizer(cfg, dry_run_git=True, project_root=tmp_path, dataset=tune_ds)
    opt_tier_a.holdout_dataset = []
    opt_tier_a.propose_mutation = MagicMock(return_value=base + "\nTierA rule.")  # type: ignore[method-assign]
    opt_tier_a.git_commit_improvement = MagicMock(return_value=True)  # type: ignore[method-assign]
    opt_tier_a.evaluate_content = lambda content, dataset=None: _make_report(  # type: ignore[method-assign]
        90.0 if "TierA rule." in content else 50.0
    )
    rep_a = opt_tier_a.run()
    assert rep_a.kept_commits == 0
    assert opt_tier_a.git_commit_improvement.call_count == 0


@pytest.mark.asyncio
async def test_router_advisor_archetype_boundary_and_tier_b_dataset() -> None:
    """Verifies ccba-ask -> router_advisor (boundary regex safe) & 12-case TIER_B (8/4) eval."""
    arch_ask = resolve_domain_archetype("ccba-ask")
    assert arch_ask is not None and arch_ask.name == "router_advisor"
    assert resolve_domain_dataset("ccba-ask") == "eval_ccba_ask.json"

    arch_maskara = resolve_domain_archetype("ccba-maskara")
    assert arch_maskara is not None and arch_maskara.name == "coding"
    assert resolve_domain_archetype("ccba-task-runner") is None
    arch_wayfinder = resolve_domain_archetype("ccba-wayfinder")
    assert arch_wayfinder is not None and arch_wayfinder.name == "platform_tooling"

    items = load_eval_dataset(skill_name="ccba-ask")
    assert len(items) == 12
    sliced = AdaptiveDataSlicer().slice(items, split_ratio=0.7, seed=42)
    assert sliced.tier == SlicingTier.TIER_B
    assert sliced.tuning_size == 8
    assert sliced.holdout_size == 4

    task = build_mock_agent_task("READ-ONLY consultation router", "ccba-ask")
    scorers = get_default_domain_scorers("ccba-ask")
    report = await EvalRunner().run(dataset=items, task=task, scorers=scorers)
    assert report.overall_score == 100.0
    assert report.passed_items == 12


def test_daemon_unconfigured_mock_ban_draft_pr_and_boost_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verifies fail-closed dataset contract, mock ban, --draft PR, and /boost filter."""
    tc_dir = tmp_path / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
    tc_dir.mkdir(parents=True)
    (tc_dir / "eval_general_domain.json").write_text("[]", encoding="utf-8")
    (tc_dir / "eval_ccba_ask.json").write_text("[]", encoding="utf-8")

    # Contract: unknown skill -> UNCONFIGURED (never eval_general_domain.json)
    res_unknown = resolve_domain_dataset_contract("ccba-mystery-xyz", tc_dir)
    assert res_unknown.status == "UNCONFIGURED"
    res_ask = resolve_domain_dataset_contract("ccba-ask", tc_dir)
    assert res_ask.status == "CONFIGURED" and res_ask.tier == "tier1_skill"

    # Daemon batch: unconfigured skill skipped at 0 tokens; configured skill blocked under mock
    unknown_skill = tmp_path / ".agents" / "skills" / "ccba-mystery-xyz"
    unknown_skill.mkdir(parents=True)
    (unknown_skill / "SKILL.md").write_text(
        "---\nname: ccba-mystery-xyz\n---\n# X\n", encoding="utf-8"
    )
    ask_skill = tmp_path / ".agents" / "skills" / "ccba-ask"
    ask_skill.mkdir(parents=True)
    (ask_skill / "SKILL.md").write_text("---\nname: ccba-ask\n---\n# Ask\n", encoding="utf-8")

    daemon = NightlyTunerDaemon(root=tmp_path, use_real_llm=False, no_telegram=True)
    report = daemon.run_nightly_batch(dry_run=True)
    by_name = {s.skill_name: s for s in report.results}
    assert by_name["ccba-mystery-xyz"].halt_reason == "UNCONFIGURED"
    assert by_name["ccba-mystery-xyz"].total_tokens == 0
    assert by_name["ccba-ask"].halt_reason == "MOCK_SIMULATOR_FORBIDDEN"
    assert by_name["ccba-ask"].total_tokens == 0

    # Draft PR check
    captured_cmds: list[list[str]] = []

    def fake_run(cmd: list[str], *args: object, **kwargs: object) -> MagicMock:
        captured_cmds.append(cmd)
        return MagicMock(returncode=0, stdout="https://github.com/vvChu/repo/pull/999\n", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    url = daemon._submit_gh_pr_with_fallback("auto-tune/test", "body")
    assert url == "https://github.com/vvChu/repo/pull/999"
    assert "--draft" in captured_cmds[0]

    # /boost eligibility gate
    assert not is_eligible_for_boost_escalation(
        SkillEvolutionSummary(
            "s1",
            Path("x"),
            0.0,
            0.0,
            0,
            0,
            "HALT_ORACLE_MISMATCH_HALT",
            halt_reason="ORACLE_MISMATCH_HALT",
        )
    )
    assert not is_eligible_for_boost_escalation(
        SkillEvolutionSummary(
            "s2", Path("x"), 50.0, 50.0, 0, 0, "UNCONFIGURED", halt_reason="UNCONFIGURED"
        )
    )
    assert is_eligible_for_boost_escalation(
        SkillEvolutionSummary("s3", Path("x"), 70.0, 70.0, 0, 3, "UNCHANGED", halt_reason=None)
    )


def test_ci_ratchet_post_mutation_gate_and_prohibition_coverage(tmp_path: Path) -> None:
    """Verifies COND-TOKEN-GATE (missing key fallback + leakage) and COND-NORMATIVE-TESTS."""
    # Missing baseline key falls back to ceiling without KeyError
    ok, code, _ = run_ci_ratchet_post_mutation_gate(
        "ccba-unlisted-skill",
        "---\nname: ccba-unlisted-skill\n---\n# Clean\nShort body.\n",
        tmp_path,
    )
    assert ok is True and code is None

    # Spoke leakage rejected
    leak_ok, leak_code, _ = run_ci_ratchet_post_mutation_gate(
        "ccba-unlisted-skill",
        "---\nname: ccba-unlisted-skill\n---\nSee vvc-notes repo.\n",
        tmp_path,
    )
    assert leak_ok is False and leak_code == "CI_SPOKE_LEAKAGE_DETECTED"

    # Prohibition deduplication allowed; total deletion rejected
    base_dup = (
        "---\nname: s\n---\nAgent MUST NOT edit code. Agent MUST NOT edit files. "
        f"BẮT BUỘC kiểm tra. BẮT BUỘC ghi log.\n{_PAD}\n"
    )
    compact_ok = (
        f"---\nname: s\n---\nAgent MUST NOT edit code or files. BẮT BUỘC kiểm tra.\n{_PAD}\n"
    )
    assert evaluate_static_lint_gate(base_dup, compact_ok).passed is True

    wiped = f"---\nname: s\n---\nAgent may edit code freely.\n{_PAD}\n"
    verdict_wiped = evaluate_static_lint_gate(base_dup, wiped)
    assert verdict_wiped.passed is False
    assert verdict_wiped.failure_code == "TIER1_NORMATIVE_DIRECTIVE_DELETED"

    # Default stability_zone is locked
    assert resolve_skill_stability_zone("---\nname: ccba-any\n---\n# Body\n") == "locked"
