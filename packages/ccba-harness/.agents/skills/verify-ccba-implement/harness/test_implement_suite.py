"""test_implement_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-implement.

Covers all features declared in `verify-ccba-implement/features/INDEX.md`:
- FEAT-IMP-001: Frontmatter, Orchestrator Tier & Slash Command Contract
- FEAT-IMP-002: Context Budget Escalation (Cycle 3 Brief, Cycle 5 /boost) & 5-Step SDLC Flow
- FEAT-IMP-003: Tier 2A implement-spec.md: Task Graph Frontier, First-Unit Canary & Single-Writer (COND-01)
- FEAT-IMP-004: Tier 2A prototype_logic.md & prototyping_patterns.md: Shareable HTML, Guided Walkthroughs & prototype/<slug>
- FEAT-IMP-005: Spoke Sync Legacy Aliases (implement, discard-feature) & Archetype Catalog Registration
- FEAT-IMP-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-IMP-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from scripts.spoke.sync.coordinator import SKILL_DEPRECATION_ALIASES

from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> object:
    """Dynamically loads run_verify_implement.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_implement.py"
    spec = importlib.util.spec_from_file_location("run_verify_implement", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_implement"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_feat_imp_001_frontmatter_and_orchestrator_contract() -> None:
    """Verifies FEAT-IMP-001: SkillValidator compliance, orchestrator tier, and slash command."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-implement" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-implement"
    assert fm["command"] == "/ccba-implement"
    assert fm["tier"] == "orchestrator"
    assert fm["is-orchestrated"] is True
    assert fm["user-invocable"] is True
    assert fm["disable-model-invocation"] is True
    assert fm["bundle"] == "_core"


def test_feat_imp_002_context_budget_and_5step_sdlc_flow() -> None:
    """Verifies FEAT-IMP-002: Context Budget 3/5 cycle rules and 5-step implementation flow."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-implement" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "python scripts/safe_pytest.py -f",
        "Leo thang sớm (Chu kỳ 3)",
        "Deep Problem Brief",
        "Dừng cứng (Chu kỳ 5)",
        "Boost Escalation Gate",
        "nêu rõ tiêu đề ticket trước khi bắt đầu",
        "python -m ccba_harness verify-patch --preset code --target",
        "Double-Pass Adversarial Review",
    ):
        assert token in body, f"Missing /ccba-implement token: {token}"

    eval_budget = runner.evaluate_loop_budget_action  # type: ignore[attr-defined]
    assert eval_budget(1) == "CONTINUE_SCOPED_TDD"
    assert eval_budget(2) == "CONTINUE_SCOPED_TDD"
    assert eval_budget(3) == "DEEP_PROBLEM_BRIEF"
    assert eval_budget(4) == "DEEP_PROBLEM_BRIEF"
    assert eval_budget(5) == "BOOST_ESCALATION_STOP"


def test_feat_imp_003_implement_spec_canary_and_single_writer() -> None:
    """Verifies FEAT-IMP-003: implement-spec.md Task Graph, First-Unit Canary & Single-Writer."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    spec_path = (
        repo_root / ".agents" / "skills" / "ccba-implement" / "references" / "implement-spec.md"
    )
    assert spec_path.is_file()
    spec_text = spec_path.read_text(encoding="utf-8")

    for marker in (
        "Task Graph",
        "Frontier",
        "fresh context window",
        "First-Unit Canary",
        "Single-Writer",
        "integration branch",
        ".worktrees/ticket-",
        "python -m ccba_harness verify-patch --preset code",
    ):
        assert marker in spec_text, f"Missing marker in implement-spec.md: {marker}"


def test_feat_imp_004_prototype_logic_and_patterns_references() -> None:
    """Verifies FEAT-IMP-004: prototype_logic.md & prototyping_patterns.md v1.3.2 contracts."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    logic_text = (
        repo_root / ".agents" / "skills" / "ccba-implement" / "references" / "prototype_logic.md"
    ).read_text(encoding="utf-8")
    patterns_text = (
        repo_root
        / ".agents"
        / "skills"
        / "ccba-implement"
        / "references"
        / "prototyping_patterns.md"
    ).read_text(encoding="utf-8")

    for marker in (
        "Shareable HTML",
        "Guided Walkthroughs",
        "TUI",
        "prototype/<slug>",
    ):
        assert marker in logic_text

    assert "Primary Source" in patterns_text
    assert "prototype/<slug>" in patterns_text


def test_feat_imp_005_spoke_sync_aliases_and_archetype_catalog() -> None:
    """Verifies FEAT-IMP-005: Legacy aliases (implement, discard-feature) & catalog registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert SKILL_DEPRECATION_ALIASES.get("implement") == "ccba-implement"
    assert SKILL_DEPRECATION_ALIASES.get("discard-feature") == "ccba-implement"
    assert SKILL_DEPRECATION_ALIASES.get("ccba-discard-feature") == "ccba-implement"

    catalog_path = (
        repo_root
        / "packages"
        / "ccba-harness"
        / "src"
        / "ccba_harness"
        / "evals"
        / "archetypes_catalog.yaml"
    )
    catalog_data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    ce_entry = next(item for item in catalog_data["archetypes"] if item["name"] == "coding")
    assert "implement" in ce_entry["keywords"]


def test_feat_imp_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-IMP-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
    runner = _load_runner_module()
    port = runner.find_free_port()  # type: ignore[attr-defined]
    proc = runner.start_probe_server(port, tmp_path)  # type: ignore[attr-defined]
    try:
        assert runner.poll_readiness(f"http://127.0.0.1:{port}/healthz", timeout_seconds=5.0)  # type: ignore[attr-defined]
    finally:
        runner.cleanup_process_group(proc)  # type: ignore[attr-defined]
    assert not runner.is_port_in_use(port)  # type: ignore[attr-defined]

    bug_path = [
        {"from": "SpecBreakdown", "to": "FirstUnitCanary", "when": "task_graph_charted"},
        {
            "from": "FirstUnitCanary",
            "to": "SubagentDirectMergeError",
            "when": "subagent_merged_into_integration_branch",
        },
    ]
    assert bug_path[0]["to"] == bug_path[1]["from"]

    validate_merge = runner.validate_spec_merge_transition  # type: ignore[attr-defined]
    ok_sub, err_sub = validate_merge(
        actor="subagent", canary_verified=True, verify_patch_exit_code=0
    )
    assert not ok_sub
    assert "SubagentDirectMergeError" in err_sub

    ok_lock, err_lock = validate_merge(
        actor="orchestrator", canary_verified=True, verify_patch_exit_code=1
    )
    assert not ok_lock
    assert "HardLockBlocked" in err_lock

    ok_pass, state_pass = validate_merge(
        actor="orchestrator", canary_verified=True, verify_patch_exit_code=0
    )
    assert ok_pass
    assert state_pass == "HandoverReady"

    classify = runner.classify_drift_status  # type: ignore[attr-defined]
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


def test_feat_imp_007_surface_diff_and_domain_eval_parity() -> None:
    """Verifies Surface Diff parity against features/INDEX.md and 100% Evals simulator score."""
    from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig

    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    features_idx = (
        repo_root
        / "packages"
        / "ccba-harness"
        / ".agents"
        / "skills"
        / "verify-ccba-implement"
        / "features"
        / "INDEX.md"
    )
    suite_file = Path(__file__).resolve()
    missing_feats = runner.verify_surface_diff(features_idx, suite_file)  # type: ignore[attr-defined]
    assert not missing_feats, f"Uncovered features in INDEX.md: {missing_feats}"

    changed = runner.check_git_provenance(  # type: ignore[attr-defined]
        "0575c8a164c2d4a9502d820307797da393b76329",
        [
            ".agents/skills/ccba-implement/SKILL.md",
            ".agents/skills/ccba-implement/references/implement-spec.md",
        ],
    )
    assert changed == []

    skill_file = repo_root / ".agents" / "skills" / "ccba-implement" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-implement")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score == 100.0
    assert eval_rep.passed_items == eval_rep.total_items == 2
