"""test_tdd_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-tdd.

Covers all features declared in `verify-ccba-tdd/features/INDEX.md`:
- FEAT-TDD-001: Frontmatter, Slash Command & GPI Threshold (12.0 >= 12.0)
- FEAT-TDD-002: Red -> Green -> Refactor Phases & ADR-0058 verify-patch --preset code Hard Lock
- FEAT-TDD-003: Public Seam Tradeoffs (what it catches / what it misses), Anti-Patterns & 5-Cycle Loop Budget
- FEAT-TDD-004: Level 3 Progressive References references/tests.md & references/mocking.md
- FEAT-TDD-005: Spoke Sync Legacy Alias (tdd -> ccba-tdd) & Archetype Catalog Registration
- FEAT-TDD-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-TDD-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer
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
    """Dynamically loads run_verify_tdd.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_tdd.py"
    spec = importlib.util.spec_from_file_location("run_verify_tdd", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_tdd"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_skill_provenance(skill_md: Path) -> tuple[str, list[str], dict[str, str]]:
    """Parses sync_commit, covered_paths, and covered_sha256 from SKILL.md frontmatter."""
    fm = yaml.safe_load(skill_md.read_text(encoding="utf-8").split("---", 2)[1])
    return str(fm["sync_commit"]), list(fm["covered_paths"]), dict(fm["covered_sha256"])


def test_feat_tdd_001_frontmatter_and_gpi_contract() -> None:
    """Verifies FEAT-TDD-001: SkillValidator compliance, slash command, and GPI == 12.0."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-tdd" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-tdd"
    assert fm["command"] == "/ccba-tdd"
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
    assert score == 12.0 >= 12.0


def test_feat_tdd_002_red_green_refactor_and_hard_lock() -> None:
    """Verifies FEAT-TDD-002: Red -> Green -> Refactor phases and verify-patch --preset code."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-tdd" / "SKILL.md").read_text(encoding="utf-8")
    for token in (
        "### 1. Xác định Seam và viết Test thất bại (Red Phase)",
        "### 2. Viết mã nguồn tối giản để Pass test (Green Phase)",
        "### 3. Tái cấu trúc mã nguồn (Refactor Phase & Deterministic Gate)",
        "python -m ccba_harness verify-patch --preset code --target <package_or_dir>",
        "Quy tắc Khóa Cứng (ADR-0058)",
    ):
        assert token in body, f"Missing /ccba-tdd token: {token}"


def test_feat_tdd_003_seam_tradeoffs_antipatterns_and_loop_budget() -> None:
    """Verifies FEAT-TDD-003: Seam catches/misses note, anti-patterns, and 5-cycle loop budget."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-tdd" / "SKILL.md").read_text(encoding="utf-8")
    for token in (
        "what it catches",
        "what it misses",
        "Ràng buộc Implementation (Implementation-coupled)",
        "Trùng lặp logic (Tautological)",
        "Lát cắt ngang (Horizontal slicing)",
        "Ngân sách Vòng lặp (Loop Budget)",
        "Tối đa **5 vòng** Red→Green→Refactor",
        "python scripts/safe_pytest.py -f <test_file>",
    ):
        assert token in body, f"Missing /ccba-tdd token: {token}"

    validate_cycle = runner.validate_tdd_cycle_transition  # type: ignore[attr-defined]
    ok_priv, err_priv = validate_cycle(
        is_public_seam=False, has_catches_and_misses_note=True, cycle_count=1
    )
    assert not ok_priv
    assert "PrivateInternalTestError" in err_priv

    ok_loop, err_loop = validate_cycle(
        is_public_seam=True, has_catches_and_misses_note=True, cycle_count=6
    )
    assert not ok_loop
    assert "LoopBudgetExhausted" in err_loop


def test_feat_tdd_004_level3_references_tests_and_mocking() -> None:
    """Verifies FEAT-TDD-004: Level 3 progressive references tests.md and mocking.md."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    tests_ref = repo_root / ".agents" / "skills" / "ccba-tdd" / "references" / "tests.md"
    mocking_ref = repo_root / ".agents" / "skills" / "ccba-tdd" / "references" / "mocking.md"
    assert tests_ref.is_file()
    assert mocking_ref.is_file()
    assert len(tests_ref.read_text(encoding="utf-8").strip()) > 100
    assert len(mocking_ref.read_text(encoding="utf-8").strip()) > 100


def test_feat_tdd_005_spoke_sync_alias_and_archetype_catalog() -> None:
    """Verifies FEAT-TDD-005: Legacy alias (tdd -> ccba-tdd) & archetype catalog registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert SKILL_DEPRECATION_ALIASES.get("tdd") == "ccba-tdd"
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
    assert "tdd" in coding_entry["keywords"]


def test_feat_tdd_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-TDD-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
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
            "from": "RedPhase",
            "to": "GreenPhase",
            "when": "minimal_test_fails_for_expected_reason",
        },
        {
            "from": "GreenPhase",
            "to": "LoopBudgetExhausted",
            "when": "cycle_count_exceeded_5",
        },
    ]
    assert bug_path[0]["to"] == bug_path[1]["from"]

    validate_cycle = runner.validate_tdd_cycle_transition  # type: ignore[attr-defined]
    ok_lock, err_lock = validate_cycle(
        is_public_seam=True,
        has_catches_and_misses_note=True,
        cycle_count=3,
        verify_patch_exit_code=1,
    )
    assert not ok_lock
    assert "HardLockBlocked" in err_lock

    ok_pass, state_pass = validate_cycle(
        is_public_seam=True,
        has_catches_and_misses_note=True,
        cycle_count=2,
        verify_patch_exit_code=0,
    )
    assert ok_pass
    assert state_pass == "RefactorVerifiedGreen"

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


def test_feat_tdd_007_surface_diff_and_domain_eval_parity() -> None:
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
        / "verify-ccba-tdd"
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

    skill_file = repo_root / ".agents" / "skills" / "ccba-tdd" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-tdd")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score >= 82.5
    assert eval_rep.total_items == 2
