"""test_diagnosing_bugs_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-diagnosing-bugs.

Covers all features declared in `verify-ccba-diagnosing-bugs/features/INDEX.md`:
- FEAT-BUG-001: Frontmatter, Slash Command & GPI Threshold (14.5 >= 12.0)
- FEAT-BUG-002: ## Redact Guardrail (<REDACTED>) & Phase 1-2 Tight Red-Capable Feedback Loop
- FEAT-BUG-003: Phase 3-4 Ranked Falsifiable Hypotheses (3-5), /ccba-issue-tree & [DEBUG-...] Tagged Probes
- FEAT-BUG-004: Phase 5-6 Forced Mutation git diff Gate (v1.3.2 #1209), /ccba-session-retrospective & mock_debugging_patterns.md
- FEAT-BUG-005: Spoke Sync Legacy Aliases (diagnosing-bugs, mock-debugger) & Archetype Catalog Registration
- FEAT-BUG-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-BUG-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer
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
    """Dynamically loads run_verify_diagnosing_bugs.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_diagnosing_bugs.py"
    spec = importlib.util.spec_from_file_location("run_verify_diagnosing_bugs", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_diagnosing_bugs"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_skill_provenance(skill_md: Path) -> tuple[str, list[str], dict[str, str]]:
    """Parses sync_commit, covered_paths, and covered_sha256 from SKILL.md frontmatter."""
    fm = yaml.safe_load(skill_md.read_text(encoding="utf-8").split("---", 2)[1])
    return str(fm["sync_commit"]), list(fm["covered_paths"]), dict(fm["covered_sha256"])


def test_feat_bug_001_frontmatter_and_gpi_contract() -> None:
    """Verifies FEAT-BUG-001: SkillValidator compliance, slash command, and GPI >= 12.0."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-diagnosing-bugs" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-diagnosing-bugs"
    assert fm["command"] == "/ccba-diagnosing-bugs"
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


def test_feat_bug_002_redact_guardrail_and_tight_feedback_loop() -> None:
    """Verifies FEAT-BUG-002: ## Redact (<REDACTED>) and Phase 1-2 tight red-capable loop."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-diagnosing-bugs" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "## Redact",
        "<REDACTED>",
        "## Phase 1 — Build a feedback loop",
        "Red-capable",
        "Deterministic",
        "Fast",
        "Agent-runnable",
        "## Phase 2 — Reproduce + minimise",
        "every remaining element is load-bearing",
    ):
        assert token in body, f"Missing /ccba-diagnosing-bugs token: {token}"


def test_feat_bug_003_hypotheses_issue_tree_and_tagged_probes() -> None:
    """Verifies FEAT-BUG-003: Phase 3-4 falsifiable hypotheses (3-5) and [DEBUG-...] tags."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-diagnosing-bugs" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "## Phase 3 — Hypothesise",
        "3–5 ranked hypotheses",
        "/ccba-issue-tree",
        "falsifiable",
        "## Phase 4 — Instrument",
        "[DEBUG-a4f2]",
    ):
        assert token in body

    validate_phase = runner.validate_diagnosis_phase_transition  # type: ignore[attr-defined]
    ok_noloop, err_noloop = validate_phase(has_red_loop=False, hypothesis_count=3)
    assert not ok_noloop
    assert "PrematureHypothesisError" in err_noloop

    ok_single, err_single = validate_phase(has_red_loop=True, hypothesis_count=1)
    assert not ok_single
    assert "InvalidHypothesisCountError" in err_single


def test_feat_bug_004_forced_mutation_git_diff_and_mock_patterns() -> None:
    """Verifies FEAT-BUG-004: Phase 5 git diff gate, Phase 6 retro link, and mock_debugging_patterns.md."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-diagnosing-bugs" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "## Phase 5 — Fix + regression test",
        "Forced Mutation `git diff` Verification (`v1.3.2 #1209`)",
        "run `git diff` against a pristine copy before trusting the red result",
        "## Phase 6 — Cleanup + post-mortem",
        "/ccba-session-retrospective",
        "/ccba-codebase-design",
        "references/mock_debugging_patterns.md",
    ):
        assert token in body

    ref_path = (
        repo_root
        / ".agents"
        / "skills"
        / "ccba-diagnosing-bugs"
        / "references"
        / "mock_debugging_patterns.md"
    )
    assert ref_path.is_file()
    assert len(ref_path.read_text(encoding="utf-8").strip()) > 100


def test_feat_bug_005_spoke_sync_aliases_and_archetype_catalog() -> None:
    """Verifies FEAT-BUG-005: Legacy aliases (diagnosing-bugs, mock-debugger) & catalog registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert SKILL_DEPRECATION_ALIASES.get("diagnosing-bugs") == "ccba-diagnosing-bugs"
    assert SKILL_DEPRECATION_ALIASES.get("mock-debugger") == "ccba-diagnosing-bugs"
    assert SKILL_DEPRECATION_ALIASES.get("ccba-mock-debugger") == "ccba-diagnosing-bugs"

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
    assert "bug" in coding_entry["keywords"]
    assert "diagnos" in coding_entry["keywords"]


def test_feat_bug_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-BUG-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
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
            "from": "Phase4Instrument",
            "to": "Phase5RegressionFix",
            "when": "tagged_debug_probes_confirmed",
        },
        {
            "from": "Phase5RegressionFix",
            "to": "NoOpMutationFalseRedError",
            "when": "forced_mutation_git_diff_empty",
        },
    ]
    assert bug_path[0]["to"] == bug_path[1]["from"]

    validate_phase = runner.validate_diagnosis_phase_transition  # type: ignore[attr-defined]
    ok_noop, err_noop = validate_phase(
        has_red_loop=True,
        hypothesis_count=3,
        forced_mutation_tested=True,
        git_diff_non_empty=False,
    )
    assert not ok_noop
    assert "NoOpMutationFalseRedError" in err_noop

    ok_pass, state_pass = validate_phase(
        has_red_loop=True,
        hypothesis_count=4,
        forced_mutation_tested=True,
        git_diff_non_empty=True,
    )
    assert ok_pass
    assert state_pass == "Phase6CleanupPostMortem"

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


def test_feat_bug_007_surface_diff_and_domain_eval_parity() -> None:
    """Verifies Surface Diff parity against features/INDEX.md and Evals ratchet improvement."""
    from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig

    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    features_idx = (
        repo_root
        / "packages"
        / "ccba-harness"
        / ".agents"
        / "skills"
        / "verify-ccba-diagnosing-bugs"
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

    skill_file = repo_root / ".agents" / "skills" / "ccba-diagnosing-bugs" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-diagnosing-bugs")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    orig = skill_file.read_text(encoding="utf-8")
    base_rep = opt.evaluate_content(orig)
    assert base_rep.total_items == 2
    mut1 = opt.propose_mutation(orig, 1)
    mut2 = opt.propose_mutation(mut1, 2)
    ratcheted_rep = opt.evaluate_content(mut2)
    assert ratcheted_rep.overall_score == 100.0
    assert ratcheted_rep.passed_items == 2
