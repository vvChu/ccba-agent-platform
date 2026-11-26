"""test_codebase_design_suite.py - 7-Feature Contract & Statechart Suite for /ccba-codebase-design.

Covers all features declared in `verify-ccba-codebase-design/features/INDEX.md`:
- FEAT-CBD-001: Frontmatter, Slash Command, GPI (16.5 >= 12.0) & Token Budget (<= 4,000)
- FEAT-CBD-002: 2-Mode Dispatch (Reference Mode vs Driver Mode), 7-Term Glossary & PEP 562 Seam
- FEAT-CBD-003: 5 Evidence-Backed Gates, <= 3 Candidates, Eliminated Record, research & Multi-OS HTML
- FEAT-CBD-004: Unified Step 4 Routing (/ccba-wayfinder, Impact Handoff, Pass 3) & design_it_twice Guard
- FEAT-CBD-005: Spoke Sync Legacy Aliases, Archetype Catalog & eval_codebase_engineering.json Cases
- FEAT-CBD-006: 5-Block Lifecycle, Statechart 18-Edge bug_path Replay & 4-State Drift Classifier
- FEAT-CBD-007: Surface Diff Parity (FEAT-CBD-001..007) & Fail-Closed LF SHA-256 Git Provenance
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.spoke.sync.coordinator import SKILL_DEPRECATION_ALIASES

from ccba_harness.economy import count_skill_tokens_lf
from ccba_harness.evals.archetypes import resolve_domain_dataset
from ccba_harness.gpi import calculate_gpi
from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically loads run_verify_codebase_design.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_codebase_design.py"
    spec = importlib.util.spec_from_file_location("run_verify_codebase_design", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_codebase_design"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_skill_provenance(skill_md: Path) -> tuple[str, list[str], dict[str, str]]:
    """Parses sync_commit, covered_paths, and covered_sha256 from SKILL.md frontmatter."""
    fm = yaml.safe_load(skill_md.read_text(encoding="utf-8").split("---", 2)[1])
    return str(fm["sync_commit"]), list(fm["covered_paths"]), dict(fm["covered_sha256"])


def test_feat_cbd_001_frontmatter_gpi_and_token_budget() -> None:
    """Verifies FEAT-CBD-001: SkillValidator compliance, GPI >= 12.0, and DMI token <= 4,000."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT
    skill_path = repo_root / ".agents" / "skills" / "ccba-codebase-design" / "SKILL.md"
    assert skill_path.is_file()

    issues = SkillValidator(project_root=repo_root).audit_skill(
        skill_path, check_shallow=True, enforce_gpi=True
    )
    assert not issues, f"SkillValidator reported issues: {issues}"

    raw = skill_path.read_text(encoding="utf-8")
    fm = yaml.safe_load(raw.split("---", 2)[1])
    assert fm["name"] == "ccba-codebase-design"
    assert fm["command"] == "/ccba-codebase-design"
    assert fm["metadata"]["version"] == "1.5.0"
    assert fm["disable-model-invocation"] is True
    assert fm["bundle"] == "_software"
    assert fm["posture"] == "seam-exempt"
    assert fm["tier"] == "kernel"
    gpi = fm["gpi"]
    assert calculate_gpi(s=gpi["s"], k=gpi["k"], a=gpi["a"], p=gpi["p"]) == 16.5 >= 12.0
    assert count_skill_tokens_lf(raw) <= 4000


def test_feat_cbd_002_dual_mode_glossary_and_pep562_pattern() -> None:
    """Verifies FEAT-CBD-002: Reference vs Driver mode markers, 7-term glossary, and PEP 562."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT
    body = (repo_root / ".agents" / "skills" / "ccba-codebase-design" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Reference Mode",
        "Hard Stopping Rule",
        "Driver Mode",
        "**Module**",
        "**Interface**",
        "**Implementation**",
        "**Depth**",
        "**Seam**",
        "**Adapter**",
        "**Leverage**",
        "**Locality**",
        "PEP 562",
        "_AUDIT_EXPORTS",
        "software_factory.md",
        "Software Factory",
    ):
        assert token in body, f"Missing required marker: {token}"

    assert runner.classify_codebase_design_mode("/ccba-codebase-design") == "ReferenceMode"
    assert (
        runner.classify_codebase_design_mode("/ccba-codebase-design Hãy nghiên cứu codebase")
        == "DriverMode"
    )


def test_feat_cbd_003_five_gates_research_and_cross_os_html() -> None:
    """Verifies FEAT-CBD-003: 5 Gates, <= 3 candidate cap, research subagent, and multi-OS HTML."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT
    guide_path = (
        repo_root
        / ".agents"
        / "skills"
        / "ccba-codebase-design"
        / "references"
        / "codebase_refactor_guide.md"
    )
    guide = guide_path.read_text(encoding="utf-8")
    assert "`Explore`" not in guide
    for token in (
        "research",
        "Cổng 1:",
        "Cổng 2:",
        "Cổng 3:",
        "Cổng 4:",
        "Cổng 5:",
        "KHÔNG ĐƯỢC VƯỢT QUÁ 3",
        "Ứng viên đã loại",
        "xdg-open",
        "Start-Process",
        "catch {",
    ):
        assert token in guide, f"Missing guide token: {token}"


def test_feat_cbd_004_step4_wayfinder_handoff_and_design_it_twice() -> None:
    """Verifies FEAT-CBD-004: Step 4 Wayfinder + Impact Handoff Gate and design_it_twice guard."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT
    ref_dir = repo_root / ".agents" / "skills" / "ccba-codebase-design" / "references"
    guide = (ref_dir / "codebase_refactor_guide.md").read_text(encoding="utf-8")
    dit = (ref_dir / "design_it_twice.md").read_text(encoding="utf-8")

    for token in (
        "/ccba-wayfinder",
        "/ccba-grilling",
        "Impact-Based Handoff Gate",
        "Pass 3",
        "/ccba-handoff",
        "tiếp tục tại đây",
        "Fast-Path",
    ):
        assert token in guide, f"Missing Step 4 routing token: {token}"

    assert "ONE_WAY_DOOR" in dit
    assert 'type_name="research"' in dit
    assert ".system_generated/scratch/design_variants/" not in dit


def test_feat_cbd_005_aliases_and_eval_dataset_cases() -> None:
    """Verifies FEAT-CBD-005: Legacy aliases, dataset routing, and Reference/Driver eval cases."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT
    assert SKILL_DEPRECATION_ALIASES.get("codebase-design") == "ccba-codebase-design"
    assert (
        SKILL_DEPRECATION_ALIASES.get("ccba-improve-codebase-architecture")
        == "ccba-codebase-design"
    )
    assert SKILL_DEPRECATION_ALIASES.get("improve-codebase-architecture") == "ccba-codebase-design"
    assert resolve_domain_dataset("ccba-codebase-design") == "eval_codebase_engineering.json"

    eval_path = (
        repo_root
        / ".agents"
        / "skills"
        / "ccba-eval-gate"
        / "test_cases"
        / "eval_codebase_engineering.json"
    )
    cases = json.loads(eval_path.read_text(encoding="utf-8"))
    ids = {c["id"] for c in cases}
    assert "test_codebase_engineering_reference_mode_hard_stop" in ids
    assert "test_codebase_engineering_driver_mode_five_gates_and_wayfinder" in ids


def test_feat_cbd_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-CBD-006: 5-block server lifecycle, bug_path replay, and drift classifier."""
    runner = _load_runner_module()
    port = runner.find_free_port()
    proc = runner.start_probe_server(port, tmp_path)
    try:
        assert runner.poll_readiness(f"http://127.0.0.1:{port}/healthz", timeout_seconds=5.0)
    finally:
        runner.cleanup_process_group(proc)
    assert not runner.is_port_in_use(port)

    ok_gate, msg_gate = runner.validate_codebase_design_transition(
        five_gates_passed=False,
        candidate_count=4,
        has_eliminated_record=False,
        is_arch_one_way=True,
        handoff_proposed=True,
    )
    assert not ok_gate and "GateViolation" in msg_gate

    ok_risk, msg_risk = runner.validate_codebase_design_transition(
        five_gates_passed=True,
        candidate_count=3,
        has_eliminated_record=True,
        is_arch_one_way=True,
        handoff_proposed=False,
    )
    assert not ok_risk and "DirectCodeRisk" in msg_risk

    ok_wf, msg_wf = runner.validate_codebase_design_transition(
        five_gates_passed=True,
        candidate_count=3,
        has_eliminated_record=True,
        is_arch_one_way=True,
        handoff_proposed=True,
    )
    assert ok_wf and msg_wf == "WayfinderMap->HandoffReady"

    assert (
        runner.classify_drift_status(
            env_blocked=False, suite_passed=True, contract_changed=False, intentional_change=False
        )
        == "in_sync"
    )
    assert (
        runner.classify_drift_status(
            env_blocked=True, suite_passed=False, contract_changed=False, intentional_change=False
        )
        == "blocked"
    )


def test_feat_cbd_007_surface_diff_and_provenance() -> None:
    """Verifies FEAT-CBD-007: Surface Diff parity against features/INDEX.md and SHA-256 lock."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT
    skill_dir = (
        repo_root
        / "packages"
        / "ccba-harness"
        / ".agents"
        / "skills"
        / "verify-ccba-codebase-design"
    )
    assert (
        runner.verify_surface_diff(skill_dir / "features" / "INDEX.md", Path(__file__).resolve())
        == []
    )

    sync_sha, cov_paths, cov_hashes = _load_skill_provenance(skill_dir / "SKILL.md")
    assert set(cov_hashes.keys()) == set(cov_paths)
    assert runner.check_git_provenance(sync_sha, cov_paths, expected_sha256=cov_hashes) == []
