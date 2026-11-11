"""test_create_pr_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-create-pr.

Covers all features declared in `verify-ccba-create-pr/features/INDEX.md`:
- FEAT-PR-001: Frontmatter, Slash Command & GPI Threshold (14.0 >= 12.0)
- FEAT-PR-002: Bước 0 Main Branch Guard & Bước 1 Local Shift-Left Gate (verify-patch Exit 0)
- FEAT-PR-003: Bước 3 Show-Me Visual & Merge Danger (## Summary, ## Evidence, ## Merge Danger)
- FEAT-PR-004: Bước 4-5 Dual-Gate CI & Copilot Review (audit_pr_comments.py, Zero-Polling RULE-4.8, .md/knowledge/reports/walkthrough.md)
- FEAT-PR-005: Spoke Sync Alias (create-pr -> ccba-contribute-to-hub) & PlatformToolingDomainSimulator Registration
- FEAT-PR-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-PR-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer (100.0%)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from scripts.spoke.sync.coordinator import SKILL_DEPRECATION_ALIASES

from ccba_harness.evals.simulators.platform_tooling import _PLATFORM_TOOLING_SKILLS
from ccba_harness.gpi import calculate_gpi
from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> object:
    """Dynamically loads run_verify_create_pr.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_create_pr.py"
    spec = importlib.util.spec_from_file_location("run_verify_create_pr", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_create_pr"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_feat_pr_001_frontmatter_and_gpi_contract() -> None:
    """Verifies FEAT-PR-001: SkillValidator compliance, slash command, and GPI == 14.0."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-create-pr" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-create-pr"
    assert fm["command"] == "/ccba-create-pr"
    assert fm["user-invocable"] is True
    assert fm["disable-model-invocation"] is True
    assert fm["bundle"] == "_core"
    assert fm["tier"] == "kernel"

    gpi = fm["gpi"]
    score = calculate_gpi(
        s=float(gpi["s"]),
        k=float(gpi["k"]),
        a=float(gpi["a"]),
        p=float(gpi["p"]),
    )
    assert score == 14.0 >= 12.0


def test_feat_pr_002_main_branch_guard_and_shift_left_gate() -> None:
    """Verifies FEAT-PR-002: Bước 0 Main Branch Guard & Bước 1 Shift-Left Gate."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-create-pr" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "## 🛡️ Bước 0: Main Branch Guard",
        "git symbolic-ref --short refs/remotes/origin/HEAD",
        "Retroactive Branch Creation",
        "## 🧪 Bước 1: Kiểm định Chất lượng Local Shift-Left Gate",
        "python -m ccba_harness verify-patch --preset skill",
        "python -m ccba_harness verify-patch --preset code",
    ):
        assert token in body, f"Missing /ccba-create-pr token: {token}"


def test_feat_pr_003_show_me_visual_and_merge_danger_template() -> None:
    """Verifies FEAT-PR-003: Show-Me Visual & Merge Danger sections in SKILL.md and PR template."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-create-pr" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Show-Me Visual & Merge Danger `v1.3.0 #1120`",
        "## Summary",
        "## Evidence",
        "- **Before:**",
        "- **After:**",
        "## Merge Danger",
        "**Door:**",
        "**Blast Radius:**",
    ):
        assert token in body, f"Missing /ccba-create-pr token: {token}"

    pr_tmpl = (repo_root / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    assert len(pr_tmpl.strip()) > 50


def test_feat_pr_004_dual_gate_ci_copilot_and_walkthrough_path() -> None:
    """Verifies FEAT-PR-004: Bước 4-5 Dual-Gate CI & Copilot Review, Zero-Polling, and walkthrough path."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-create-pr" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "## 🔄 Bước 4: Đồng Hành Dual-Gate CI & Copilot Review",
        "Zero-Polling Policy (RULE-4.8)",
        "python scripts/validation/audit_pr_comments.py --pr <PR_NUMBER>",
        ".github/bugbot-rules.md",
        ".md/knowledge/reports/walkthrough.md",
        "/ccba-release-feature",
    ):
        assert token in body, f"Missing /ccba-create-pr token: {token}"


def test_feat_pr_005_spoke_sync_alias_and_simulator_registration() -> None:
    """Verifies FEAT-PR-005: Spoke Sync alias and PlatformToolingDomainSimulator registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert SKILL_DEPRECATION_ALIASES.get("create-pr") == "ccba-contribute-to-hub"
    assert SKILL_DEPRECATION_ALIASES.get("ccba-create-pr") == "ccba-contribute-to-hub"
    assert "ccba-create-pr" in _PLATFORM_TOOLING_SKILLS

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
    pt_entry = next(
        item for item in catalog_data["archetypes"] if item["name"] == "platform_tooling"
    )
    assert "create-pr" in pt_entry["keywords"]


def test_feat_pr_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-PR-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
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
            "from": "MainBranchGuard",
            "to": "ShiftLeftGate",
            "when": "feature_branch_verified",
        },
        {
            "from": "ShiftLeftGate",
            "to": "ShiftLeftBlocked",
            "when": "verify_patch_nonzero_exit",
        },
    ]
    assert bug_path[0]["to"] == bug_path[1]["from"]

    validate_pr = runner.validate_pr_creation_flow  # type: ignore[attr-defined]
    ok_shift, err_shift = validate_pr(on_default_branch=False, verify_patch_exit_code=1)
    assert not ok_shift
    assert "ShiftLeftBlocked" in err_shift

    ok_poll, err_poll = validate_pr(
        on_default_branch=False, verify_patch_exit_code=0, used_manage_task_polling=True
    )
    assert not ok_poll
    assert "PollingViolationError" in err_poll

    ok_pass, state_pass = validate_pr(
        on_default_branch=False,
        verify_patch_exit_code=0,
        has_show_me_visual_sections=True,
        used_manage_task_polling=False,
    )
    assert ok_pass
    assert state_pass == "ReleaseReadyHandover"

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


def test_feat_pr_007_surface_diff_and_domain_eval_parity() -> None:
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
        / "verify-ccba-create-pr"
        / "features"
        / "INDEX.md"
    )
    suite_file = Path(__file__).resolve()
    missing_feats = runner.verify_surface_diff(features_idx, suite_file)  # type: ignore[attr-defined]
    assert not missing_feats, f"Uncovered features in INDEX.md: {missing_feats}"

    changed = runner.check_git_provenance(  # type: ignore[attr-defined]
        "c62cc569fe0a70a74dd8b86d339276186f0fde6f",
        [
            ".agents/skills/ccba-create-pr/SKILL.md",
            ".github/pull_request_template.md",
        ],
    )
    assert changed == []

    skill_file = repo_root / ".agents" / "skills" / "ccba-create-pr" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-create-pr")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score == 100.0
    assert eval_rep.passed_items == eval_rep.total_items == 2
