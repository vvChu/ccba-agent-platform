"""test_xia_suite.py - 6-Phase Contract & Statechart Verification Suite for /ccba-xia.

Covers all features declared in `verify-ccba-xia/features/INDEX.md`:
- FEAT-XIA-001: Frontmatter, Slash Command & GPI Threshold (16.5 >= 12.0)
- FEAT-XIA-002: Pha 1 Recon, Shallow Clone & License Classification Gate
- FEAT-XIA-003: Pha 2 Hub Catalog Duplicate Check & Gate 0 Determinism
- FEAT-XIA-004: Pha 4 Challenge Hard Gate & ADR-0022 Mode Restrictions
- FEAT-XIA-005: Pha 5 & 6 Plan, 1-Click Command, [XIA-COPY-RAW] & Cleanup
- FEAT-XIA-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from scripts.spoke.upstream_evaluator import (
    check_is_duplicate,
    check_repo_license,
    generate_xia_command,
)

from ccba_harness.gpi import calculate_gpi
from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> object:
    """Dynamically loads run_verify_xia.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_xia.py"
    spec = importlib.util.spec_from_file_location("run_verify_xia", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_xia"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_feat_xia_001_frontmatter_and_gpi_contract() -> None:
    """Verifies FEAT-XIA-001: SkillValidator compliance, slash command, and GPI >= 12.0."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-xia" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-xia"
    assert fm["command"] == "/ccba-xia"
    assert fm["user-invocable"] is True
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


def test_feat_xia_002_recon_and_license_classification_gate(tmp_path: Path) -> None:
    """Verifies FEAT-XIA-002: Pha 1 Recon shallow clone rules and license classifier."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-xia" / "SKILL.md").read_text(encoding="utf-8")
    assert "--depth 1" in body
    assert ".md/scratch/xia_sources/" in body
    assert "source manifest" in body
    assert "health_posture" in body
    modes_body = (
        repo_root / ".agents" / "skills" / "ccba-xia" / "references" / "modes.md"
    ).read_text(encoding="utf-8")
    for posture in ("FRESH", "STALE", "ARCHIVED", "UNKNOWN"):
        assert posture in modes_body

    mit_repo = tmp_path / "mit_repo"
    mit_repo.mkdir()
    (mit_repo / "LICENSE").write_text(
        "MIT License\nPermission is hereby granted...", encoding="utf-8"
    )
    lic_type, _ = check_repo_license(mit_repo)
    assert lic_type == "PERMISSIVE"

    gpl_repo = tmp_path / "gpl_repo"
    gpl_repo.mkdir()
    (gpl_repo / "COPYING").write_text("GNU General Public License v3.0", encoding="utf-8")
    gpl_type, _ = check_repo_license(gpl_repo)
    assert gpl_type == "COPYLEFT"

    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()
    unk_type, _ = check_repo_license(empty_repo)
    assert unk_type == "UNKNOWN"


def test_feat_xia_003_map_catalog_check_and_gate0_contract() -> None:
    """Verifies FEAT-XIA-003: Pha 2 Hub Catalog duplicate detector and Gate 0 determinism."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-xia" / "SKILL.md").read_text(encoding="utf-8")
    assert ".agents/skills/platform-loader/catalog.yaml" in body
    assert "Cổng 0 (The Determinism Gate" in body
    assert "packages/*/src/" in body
    assert "Reuse Assessment" in body

    is_dup, matched = check_is_duplicate(
        "ck:xia", existing_skills=["ccba-xia", "ccba-tdd"], existing_workflows=[]
    )
    assert is_dup is True
    assert matched == "ccba-xia"

    is_new, matched_new = check_is_duplicate(
        "brand-new-quantum-router", existing_skills=["ccba-xia"], existing_workflows=[]
    )
    assert is_new is False
    assert matched_new is None


def test_feat_xia_004_challenge_hard_gate_and_adr_0022_modes() -> None:
    """Verifies FEAT-XIA-004: Pha 4 Challenge Hard Gate, ADR-0022, and modes.md invariants."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_text = (repo_root / ".agents" / "skills" / "ccba-xia" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    modes_text = (
        repo_root / ".agents" / "skills" / "ccba-xia" / "references" / "modes.md"
    ).read_text(encoding="utf-8")
    adr_text = (
        repo_root / "docs" / "adr" / "0022-restrict-fast-flag-in-xia-challenge-gate.md"
    ).read_text(encoding="utf-8")

    assert (
        "Chức năng này có phải là 100% thuật toán thuần túy cần đưa vào packages/ không?"
        in skill_text
    )
    assert "Progressive Reference (Tier 2A) trong references/*.md" in skill_text
    assert "[!WARNING] Kế hoạch này được tạo ở chế độ --fast." in skill_text
    assert "`--copy-raw` + `--fast`: **BỊ CẤM**" in modes_text
    assert "`--copy-raw` mode cannot be combined with `--fast`" in adr_text

    validate_combo = runner.validate_xia_mode_combination  # type: ignore[attr-defined]
    ok_raw_fast, reason = validate_combo("--copy-raw", fast=True)
    assert not ok_raw_fast
    assert "REJECTED_COMBO" in reason

    ok_port_fast, fast_policy = validate_combo("--port", fast=True)
    assert ok_port_fast
    assert "FAST_WARNING_REQUIRED" in fast_policy


def test_feat_xia_005_plan_deliver_and_command_generation() -> None:
    """Verifies FEAT-XIA-005: Pha 5 & 6 contracts and 1-click /ccba-xia command builder."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_text = (repo_root / ".agents" / "skills" / "ccba-xia" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "scan_dependencies",
        "Bảng điểm GPI định lượng",
        "[XIA-COPY-RAW]",
        ".github/pull_request_template.md",
        "/ccba-implement",
        "architectural evaluation follow-up",
    ):
        assert token in skill_text

    cmd_compare = generate_xia_command("https://github.com/org/repo", "auth-flow", "--compare")
    assert cmd_compare == "/ccba-xia https://github.com/org/repo auth-flow --compare"

    cmd_port = generate_xia_command(".md/scratch/repos/demo", "scheduler", "--port")
    assert cmd_port == "/ccba-xia .md/scratch/repos/demo scheduler --port"


def test_feat_xia_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-XIA-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
    runner = _load_runner_module()
    port = runner.find_free_port()  # type: ignore[attr-defined]
    proc = runner.start_probe_server(port, tmp_path)  # type: ignore[attr-defined]
    try:
        assert runner.poll_readiness(f"http://127.0.0.1:{port}/healthz", timeout_seconds=5.0)  # type: ignore[attr-defined]
    finally:
        runner.cleanup_process_group(proc)  # type: ignore[attr-defined]
    assert not runner.is_port_in_use(port)  # type: ignore[attr-defined]

    bug_path_copyleft = [
        {"from": "Recon", "to": "LicenseCheck", "when": "clone_depth_1"},
        {"from": "LicenseCheck", "to": "HaltedCopyleft", "when": "license_copyleft_or_unknown"},
    ]
    assert bug_path_copyleft[0]["to"] == bug_path_copyleft[1]["from"]
    agpl_dir = tmp_path / "agpl_src"
    agpl_dir.mkdir()
    (agpl_dir / "LICENSE").write_text("GNU Affero General Public License (AGPL)", encoding="utf-8")
    lic_status, _ = check_repo_license(agpl_dir)
    assert lic_status == "COPYLEFT"

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


def test_feat_xia_007_surface_diff_and_domain_eval_parity() -> None:
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
        / "verify-ccba-xia"
        / "features"
        / "INDEX.md"
    )
    suite_file = Path(__file__).resolve()
    missing_feats = runner.verify_surface_diff(features_idx, suite_file)  # type: ignore[attr-defined]
    assert not missing_feats, f"Uncovered features in INDEX.md: {missing_feats}"

    changed = runner.check_git_provenance(  # type: ignore[attr-defined]
        "e3104aace4239f6659caa698f142111772ffe1b8",
        [
            ".agents/skills/ccba-xia/SKILL.md",
            ".agents/skills/ccba-xia/references/modes.md",
            "scripts/spoke/upstream_evaluator.py",
            "scripts/spoke/_upstream_helpers.py",
            "docs/adr/0022-restrict-fast-flag-in-xia-challenge-gate.md",
        ],
    )
    assert changed == []

    skill_file = repo_root / ".agents" / "skills" / "ccba-xia" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-xia")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score == 100.0
    assert eval_rep.passed_items == eval_rep.total_items == 2


def test_feat_xia_008_mattpocock_v132_hybrid_adopt_and_tier2a_references() -> None:
    """Verifies /ccba-xia mattpocock/skills v1.3.2 adaptation and Grok COND-01..COND-04."""
    runner = _load_runner_module()
    skills_dir: Path = runner.REPO_ROOT / ".agents" / "skills"  # type: ignore[attr-defined]
    expected_markers: dict[str, tuple[str, ...]] = {
        "ccba-implement/references/implement-spec.md": (
            "First-Unit Canary",
            "Single-Writer",
            "integration branch",
            "Task Graph",
        ),
        "ccba-knowledge-loop/references/llm-wiki.md": (
            ".md/knowledge/wiki/index.md",
            "Ingest",
            "Query",
            "Lint",
            "ccba-agent-platform@",
        ),
        "ccba-grilling/references/to-questionnaire.md": (
            ".md/knowledge/questionnaires/to-questionnaire-",
            "Grill the send, not the subject",
        ),
        "ccba-build-skill/references/skill_authoring_guide.md": (
            "Context Pointers",
            "Post-Completion Pull",
            "Leading Words",
            "Shared Reference",
        ),
        "ccba-implement/references/prototype_logic.md": ("Shareable HTML", "Guided Walkthroughs"),
        "ccba-diagnosing-bugs/SKILL.md": ("<REDACTED>", "git diff", "/ccba-session-retrospective"),
        "ccba-tdd/SKILL.md": ("catches", "misses"),
        "ccba-code-review/SKILL.md": (
            "fresh context window",
            "docs/rules/code_quality_standards.md",
        ),
        "ccba-create-pr/SKILL.md": ("## Summary", "## Evidence", "## Merge Danger"),
        "ccba-implement/SKILL.md": ("references/implement-spec.md",),
        "ccba-knowledge-loop/SKILL.md": ("references/llm-wiki.md",),
        "ccba-grilling/SKILL.md": ("references/to-questionnaire.md",),
    }
    for rel_path, markers in expected_markers.items():
        path = skills_dir / rel_path
        assert path.is_file(), f"Missing target file: {rel_path}"
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"Missing marker {marker!r} in {rel_path}"
