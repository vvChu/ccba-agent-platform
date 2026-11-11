"""test_code_review_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-code-review.

Covers all features declared in `verify-ccba-code-review/features/INDEX.md`:
- FEAT-REV-001: Frontmatter, Slash Command & GPI Threshold (16.5 >= 12.0)
- FEAT-REV-002: Step 1-3 Simplify Gate (400 LOC/8 files/200 LOC), Copilot Gate & Explicit Standards Handoff
- FEAT-REV-003: Step 4-5 fresh context window (v1.3.2 #1341), Execution-Proven Filter & ## Merge Danger
- FEAT-REV-004: Complete Level 3 Reference Suite (14 Checklists & Workflows in references/)
- FEAT-REV-005: Spoke Sync Legacy Alias (code-review -> ccba-code-review) & Archetype Catalog Registration
- FEAT-REV-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-REV-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from scripts.spoke.sync.coordinator import SKILL_DEPRECATION_ALIASES

from ccba_harness.gpi import calculate_gpi
from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> object:
    """Dynamically loads run_verify_code_review.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_code_review.py"
    spec = importlib.util.spec_from_file_location("run_verify_code_review", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_code_review"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_skill_provenance(skill_md: Path) -> tuple[str, list[str], dict[str, str]]:
    """Parses sync_commit, covered_paths, and covered_sha256 from SKILL.md frontmatter."""
    fm = yaml.safe_load(skill_md.read_text(encoding="utf-8").split("---", 2)[1])
    return str(fm["sync_commit"]), list(fm["covered_paths"]), dict(fm["covered_sha256"])


def test_feat_rev_001_frontmatter_and_gpi_contract() -> None:
    """Verifies FEAT-REV-001: SkillValidator compliance, slash command, and GPI == 16.5."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-code-review" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-code-review"
    assert fm["command"] == "/ccba-code-review"
    assert fm["user-invocable"] is True
    assert fm["disable-model-invocation"] is True
    assert fm["bundle"] == "_software"
    assert fm["tier"] == "kernel"

    gpi = fm["gpi"]
    score = calculate_gpi(
        s=float(gpi["s"]),
        k=float(gpi["k"]),
        a=float(gpi["a"]),
        p=float(gpi["p"]),
    )
    assert score == 16.5 >= 12.0


def test_feat_rev_002_simplify_copilot_gates_and_standards_handoff() -> None:
    """Verifies FEAT-REV-002: Simplify Gate, Copilot Gate, and explicit standards handoff."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-code-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Simplify Gate - RULE-2.10",
        "400 LOC",
        "8 tệp",
        "200 LOC",
        "python scripts/validation/audit_pr_comments.py --pr <pr_id>",
        "docs/rules/code_quality_standards.md",
        "docs/rules/code_quality_verification.md",
        "12 Fowler smells",
    ):
        assert token in body, f"Missing /ccba-code-review token: {token}"


def test_feat_rev_003_fresh_context_window_and_execution_proven_filter() -> None:
    """Verifies FEAT-REV-003: fresh context window, candidate + repro_command, and ## Merge Danger."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-code-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "fresh context window",
        "CRITICAL CONSTRAINT: You are a dedicated review sub-agent.",
        "candidate",
        "repro_command",
        "## Merge Danger",
        "Verified Findings",
        "Dropped / Unverified Notes",
        "python -m ccba_harness verify-patch --preset ci",
    ):
        assert token in body, f"Missing /ccba-code-review token: {token}"

    validate_rev = runner.validate_code_review_execution  # type: ignore[attr-defined]
    ok_cop, err_cop = validate_rev(copilot_unresolved=True)
    assert not ok_cop
    assert "CopilotBlocked" in err_cop

    ok_fork, err_fork = validate_rev(used_fresh_context_window=False)
    assert not ok_fork
    assert "ContextForkedViolation" in err_fork


def test_feat_rev_004_level3_reference_suite_completeness() -> None:
    """Verifies FEAT-REV-004: All 14 Level 3 reference files in .agents/skills/ccba-code-review/references/."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    ref_root = repo_root / ".agents" / "skills" / "ccba-code-review" / "references"
    expected_refs = (
        "input-mode-resolution.md",
        "requesting-code-review.md",
        "checklist-workflow.md",
        "checklists/base.md",
        "checklists/python.md",
        "checklists/api.md",
        "checklists/web-app.md",
        "spec-compliance-review.md",
        "edge-case-scouting.md",
        "parallel-review-workflow.md",
        "codebase-scan-workflow.md",
        "code-review-reception.md",
        "verification-before-completion.md",
        "unslop_checklist.md",
    )
    for rel in expected_refs:
        path = ref_root / rel
        assert path.is_file(), f"Missing ccba-code-review reference: {rel}"


def test_feat_rev_005_spoke_sync_alias_and_archetype_catalog() -> None:
    """Verifies FEAT-REV-005: Legacy alias (code-review -> ccba-code-review) & catalog registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert SKILL_DEPRECATION_ALIASES.get("code-review") == "ccba-code-review"
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
    coding_entry = next(item for item in catalog_data["archetypes"] if item["name"] == "coding")
    assert "code" in coding_entry["keywords"]


def test_feat_rev_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-REV-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
    runner = _load_runner_module()
    port = runner.find_free_port()  # type: ignore[attr-defined]
    proc = runner.start_probe_server(port, tmp_path)  # type: ignore[attr-defined]
    try:
        assert runner.poll_readiness(f"http://127.0.0.1:{port}/healthz", timeout_seconds=5.0)  # type: ignore[attr-defined]
    finally:
        runner.cleanup_process_group(proc)  # type: ignore[attr-defined]
    assert not runner.is_port_in_use(port)  # type: ignore[attr-defined]

    bug_path = [
        {
            "from": "SimplifyAndCopilotGate",
            "to": "ParallelSubagents",
            "when": "simplify_and_copilot_clear",
        },
        {
            "from": "ParallelSubagents",
            "to": "ContextForkedViolation",
            "when": "subagent_forked_caller_context_or_spawned_child",
        },
    ]
    assert bug_path[0]["to"] == bug_path[1]["from"]

    validate_rev = runner.validate_code_review_execution  # type: ignore[attr-defined]
    ok_child, err_child = validate_rev(
        used_fresh_context_window=True,
        subagent_spawned_child=True,
    )
    assert not ok_child
    assert "ContextForkedViolation" in err_child

    ok_clean, state_clean = validate_rev(
        copilot_unresolved=False,
        used_fresh_context_window=True,
        subagent_spawned_child=False,
        verified_finding_count=0,
        verify_patch_exit_code=0,
    )
    assert ok_clean
    assert state_clean == "ReviewApprovedClean"

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


def test_feat_rev_007_surface_diff_and_domain_eval_parity() -> None:
    """Verifies Surface Diff parity against features/INDEX.md and Evals baseline evaluation."""
    from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig

    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    features_idx = (
        repo_root
        / "packages"
        / "ccba-harness"
        / ".agents"
        / "skills"
        / "verify-ccba-code-review"
        / "features"
        / "INDEX.md"
    )
    suite_file = Path(__file__).resolve()
    missing_feats = runner.verify_surface_diff(features_idx, suite_file)  # type: ignore[attr-defined]
    assert not missing_feats, f"Uncovered features in INDEX.md: {missing_feats}"

    sync_sha, cov_paths, cov_hashes = _load_skill_provenance(
        features_idx.parent.parent / "SKILL.md"
    )
    assert set(cov_hashes.keys()) == set(cov_paths)
    changed = runner.check_git_provenance(  # type: ignore[attr-defined]
        sync_sha,
        cov_paths,
        expected_sha256=cov_hashes,
    )
    assert changed == []

    skill_file = repo_root / ".agents" / "skills" / "ccba-code-review" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-code-review")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score >= 82.5
    assert eval_rep.total_items == 2
