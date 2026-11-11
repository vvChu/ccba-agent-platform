"""test_wayfinder_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-wayfinder.

Covers all features declared in `verify-ccba-wayfinder/features/INDEX.md`:
- FEAT-WF-001: Frontmatter, Slash Command & GPI Threshold (14.5 >= 12.0)
- FEAT-WF-002: Boundary (/ccba-grilling vs /ccba-wayfinder), Leading Words & Planning Rules
- FEAT-WF-003: 5-Section Map Contract & Fog vs. Ticket Test Classifier
- FEAT-WF-004: 4 Ticket Types (Research/Prototype/Grilling/Task), Parallel Dispatch & Claiming Lock
- FEAT-WF-005: Spoke Sync Legacy Alias, Archetype Catalog & Simulator Registration
- FEAT-WF-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-WF-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer
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
    """Dynamically loads run_verify_wayfinder.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_wayfinder.py"
    spec = importlib.util.spec_from_file_location("run_verify_wayfinder", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_wayfinder"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_skill_provenance(skill_md: Path) -> tuple[str, list[str], dict[str, str]]:
    """Parses sync_commit, covered_paths, and covered_sha256 from SKILL.md frontmatter."""
    fm = yaml.safe_load(skill_md.read_text(encoding="utf-8").split("---", 2)[1])
    return str(fm["sync_commit"]), list(fm["covered_paths"]), dict(fm["covered_sha256"])


def test_feat_wf_001_frontmatter_and_gpi_contract() -> None:
    """Verifies FEAT-WF-001: SkillValidator compliance, slash command, and GPI >= 12.0."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-wayfinder" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-wayfinder"
    assert fm["command"] == "/ccba-wayfinder"
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
    assert score == 14.5 >= 12.0


def test_feat_wf_002_boundary_leading_words_and_planning_rules() -> None:
    """Verifies FEAT-WF-002: /ccba-grilling boundary, Leading Words, and Plan/Refer rules."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-wayfinder" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    for marker in (
        "Single Session",
        "Multi-session Fog of War",
        "`Map` (Bản đồ tổng thể)",
        "`Ticket` (Công việc cụ thể)",
        "`Session` (Phiên làm việc con)",
        "100K token",
        "Plan, don't do",
        "Refer by name",
    ):
        assert marker in body, f"Missing required Wayfinder marker: {marker}"


def test_feat_wf_003_map_sections_and_fog_vs_ticket_classifier() -> None:
    """Verifies FEAT-WF-003: 5-section map structure and Fog vs. Ticket Test classifier."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-wayfinder" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for section_token in (
        "Điểm đích (Destination)",
        "Ghi chú (Notes)",
        "Quyết định đã chốt (Decisions so far)",
        "Sương mù chiến trận / Chưa xác định rõ (Not yet specified)",
        "Ngoài phạm vi (Out of scope)",
        "Fog vs. Ticket Test",
    ):
        assert section_token in body

    validate_map = runner.validate_wayfinder_map_sections  # type: ignore[attr-defined]
    real_map = (
        repo_root / ".md" / "wayfinder" / "parameter-externalization-and-kiss-governance" / "map.md"
    ).read_text(encoding="utf-8")
    assert validate_map(real_map) == []

    incomplete_map = "# Map\n## Destination\nDone.\n## Notes\nNone."
    missing = validate_map(incomplete_map)
    assert "Decisions" in missing
    assert "Not Yet Specified" in missing
    assert "Out of Scope" in missing

    classify_fog = runner.classify_fog_or_ticket  # type: ignore[attr-defined]
    assert classify_fog(has_sharp_question=True, is_blocked=False) == "CREATE_TICKET_FRONTIER"
    assert classify_fog(has_sharp_question=True, is_blocked=True) == "CREATE_TICKET_BLOCKED"
    assert classify_fog(has_sharp_question=False, is_blocked=False) == "NOT_YET_SPECIFIED"


def test_feat_wf_004_ticket_types_parallel_dispatch_and_claiming() -> None:
    """Verifies FEAT-WF-004: 4 Ticket types, Parallel Research Dispatch, and Assignee Claiming."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-wayfinder" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Research (Nghiên cứu) [AFK]",
        "Prototype (Mẫu thử) [HITL]",
        "Grilling (Chất vấn) [HITL]",
        "Task (Tác vụ) [HITL hoặc AFK]",
        "Parallel Research Dispatch",
        "/ccba-research",
        "Đăng ký nhận việc (Claiming)",
        "Assignee",
        "chạy tối đa 1 ticket mỗi phiên",
    ):
        assert token in body


def test_feat_wf_005_spoke_sync_alias_and_simulator_registration() -> None:
    """Verifies FEAT-WF-005: Legacy alias mapping, archetype catalog, and simulator registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert SKILL_DEPRECATION_ALIASES.get("wayfinder") == "ccba-wayfinder"
    assert "ccba-wayfinder" in _PLATFORM_TOOLING_SKILLS

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
    assert "wayfinder" in pt_entry["keywords"]


def test_feat_wf_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-WF-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
    runner = _load_runner_module()
    port = runner.find_free_port()  # type: ignore[attr-defined]
    proc = runner.start_probe_server(port, tmp_path)  # type: ignore[attr-defined]
    try:
        assert runner.poll_readiness(f"http://127.0.0.1:{port}/healthz", timeout_seconds=5.0)  # type: ignore[attr-defined]
    finally:
        runner.cleanup_process_group(proc)  # type: ignore[attr-defined]
    assert not runner.is_port_in_use(port)  # type: ignore[attr-defined]

    validate_transition = runner.validate_ticket_execution_transition  # type: ignore[attr-defined]

    # Replay Bug Path 1: FrontierReady -> RaceConditionCollision (worked_without_assignee_claim)
    bug_path_unclaimed = [
        {"from": "ChartMap", "to": "FrontierReady", "when": "fog_and_unblocked_tickets_charted"},
        {
            "from": "FrontierReady",
            "to": "RaceConditionCollision",
            "when": "worked_without_assignee_claim",
        },
    ]
    assert bug_path_unclaimed[0]["to"] == bug_path_unclaimed[1]["from"]
    ok_unclaimed, reason_unclaimed = validate_transition(
        has_fog=True, assignee_claimed=False, tickets_in_session=1
    )
    assert not ok_unclaimed
    assert "RaceConditionCollision" in reason_unclaimed

    # Replay Bug Path 2: ChartMap -> DirectExecutionHandoff (zero_fog_detected)
    ok_nofog, reason_nofog = validate_transition(
        has_fog=False, assignee_claimed=True, tickets_in_session=1
    )
    assert not ok_nofog
    assert "DirectExecutionHandoff" in reason_nofog

    # Valid transition
    ok_valid, state_valid = validate_transition(
        has_fog=True, assignee_claimed=True, tickets_in_session=1
    )
    assert ok_valid
    assert state_valid == "TicketResolved"

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


def test_feat_wf_007_surface_diff_and_domain_eval_parity() -> None:
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
        / "verify-ccba-wayfinder"
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

    skill_file = repo_root / ".agents" / "skills" / "ccba-wayfinder" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-wayfinder")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score == 100.0
    assert eval_rep.passed_items == eval_rep.total_items == 2
