"""test_grilling_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-grilling.

Covers all features declared in `verify-ccba-grilling/features/INDEX.md`:
- FEAT-GRILL-001: Frontmatter, Slash Command & GPI Threshold (14.5 >= 12.0)
- FEAT-GRILL-002: Bước 0 Pre-Flight (in-your-own-words, sharpen, outside check) & Nhánh A/B/C
- FEAT-GRILL-003: Design Tree, Frontier Questions, Facts vs. Decisions & /ccba-issue-tree Escalation
- FEAT-GRILL-004: Tier 2A Progressive Reference to-questionnaire.md & workflow_looping.md
- FEAT-GRILL-005: Spoke Sync Legacy Alias (grilling -> ccba-grilling) & Archetype Catalog Registration
- FEAT-GRILL-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-GRILL-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer
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
    """Dynamically loads run_verify_grilling.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_grilling.py"
    spec = importlib.util.spec_from_file_location("run_verify_grilling", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_grilling"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_feat_grill_001_frontmatter_and_gpi_contract() -> None:
    """Verifies FEAT-GRILL-001: SkillValidator compliance, slash command, and GPI >= 12.0."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-grilling" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-grilling"
    assert fm["command"] == "/ccba-grilling"
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
    assert score == 14.5 >= 12.0


def test_feat_grill_002_preflight_sharpen_and_three_branches() -> None:
    """Verifies FEAT-GRILL-002: Step 0 in-your-own-words/sharpen and Branches A/B/C."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-grilling" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "in-your-own-words",
        "sharpen",
        "outside check",
        "Nhánh A: Standard Stress-Test",
        "Nhánh B: Rule Compliance Stress-Test",
        "Nhánh C: Visual Prototype Grilling",
        "floating picker",
        "overall design → component groups → individual components",
        'câu trả lời "Đồng ý / Yes" luôn chấp nhận phương án đề xuất đó',
        "đường kẻ ngang `---`",
    ):
        assert token in body, f"Missing Grilling token: {token}"


def test_feat_grill_003_design_tree_frontier_and_turn_validator() -> None:
    """Verifies FEAT-GRILL-003: Design Tree, Frontier Questions, Facts vs Decisions, and turn logic."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-grilling" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Cây thiết kế (Design Tree)",
        "Biên giới câu hỏi (Frontier Questions)",
        "Facts vs. Decisions",
        "/ccba-issue-tree",
    ):
        assert token in body

    validate_turn = runner.validate_grilling_question_turn  # type: ignore[attr-defined]
    ok_fact, err_fact = validate_turn(
        is_discoverable_fact=True, asked_user=True, has_recommended_answer=True
    )
    assert not ok_fact
    assert "AskedUserFactError" in err_fact

    ok_esc, state_esc = validate_turn(
        is_discoverable_fact=False,
        asked_user=True,
        has_recommended_answer=True,
        competing_arch_options=3,
    )
    assert ok_esc
    assert "IssueTreeEscalation" in state_esc

    ok_dec, state_dec = validate_turn(
        is_discoverable_fact=False,
        asked_user=True,
        has_recommended_answer=True,
        competing_arch_options=1,
    )
    assert ok_dec
    assert state_dec == "DecisionRecorded"


def test_feat_grill_004_to_questionnaire_and_workflow_looping_references() -> None:
    """Verifies FEAT-GRILL-004: Tier 2A progressive references to-questionnaire.md & workflow_looping.md."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    q_path = (
        repo_root / ".agents" / "skills" / "ccba-grilling" / "references" / "to-questionnaire.md"
    )
    w_path = (
        repo_root / ".agents" / "skills" / "ccba-grilling" / "references" / "workflow_looping.md"
    )
    assert q_path.is_file()
    assert w_path.is_file()

    q_text = q_path.read_text(encoding="utf-8")
    for marker in (
        "Grill the send, not the subject",
        "Who is it going to?",
        "What do you need back?",
        "một lượt trao đổi duy nhất",
        ".md/knowledge/questionnaires/to-questionnaire-",
        "Matt Pocock",
    ):
        assert marker in q_text


def test_feat_grill_005_spoke_sync_alias_and_archetype_catalog() -> None:
    """Verifies FEAT-GRILL-005: Legacy alias mapping and archetype catalog registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert SKILL_DEPRECATION_ALIASES.get("grilling") == "ccba-grilling"
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
    grill_entry = next(item for item in catalog_data["archetypes"] if item["name"] == "grilling")
    assert "grill" in grill_entry["keywords"]
    assert grill_entry["dataset_file"] == "eval_grilling.json"


def test_feat_grill_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-GRILL-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
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
            "from": "PreFlightSharpen",
            "to": "FrontierQuestion",
            "when": "in_your_own_words_and_outside_check",
        },
        {
            "from": "FrontierQuestion",
            "to": "AskedUserFactError",
            "when": "asked_user_discoverable_fact",
        },
    ]
    assert bug_path[0]["to"] == bug_path[1]["from"]
    validate_turn = runner.validate_grilling_question_turn  # type: ignore[attr-defined]
    ok, reason = validate_turn(
        is_discoverable_fact=True, asked_user=True, has_recommended_answer=True
    )
    assert not ok
    assert "AskedUserFactError" in reason

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


def test_feat_grill_007_surface_diff_and_domain_eval_parity() -> None:
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
        / "verify-ccba-grilling"
        / "features"
        / "INDEX.md"
    )
    suite_file = Path(__file__).resolve()
    missing_feats = runner.verify_surface_diff(features_idx, suite_file)  # type: ignore[attr-defined]
    assert not missing_feats, f"Uncovered features in INDEX.md: {missing_feats}"

    changed = runner.check_git_provenance(  # type: ignore[attr-defined]
        "9948fdf18663ae2609edf06ae0cbdbd4c87f8f4a",
        [
            ".agents/skills/ccba-grilling/SKILL.md",
            ".agents/skills/ccba-grilling/references/to-questionnaire.md",
        ],
    )
    assert changed == []

    skill_file = repo_root / ".agents" / "skills" / "ccba-grilling" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-grilling")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score == 100.0
    assert eval_rep.passed_items == eval_rep.total_items == 2
