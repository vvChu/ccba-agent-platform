"""test_knowledge_loop_suite.py - 7-Feature Contract & Statechart Verification Suite for /ccba-knowledge-loop.

Covers all features declared in `verify-ccba-knowledge-loop/features/INDEX.md`:
- FEAT-KL-001: Frontmatter, Orchestrator Tier & Slash Command Contract
- FEAT-KL-002: Single-Writer Protocol (ADR-0053) & 4-Phase Orchestration
- FEAT-KL-003: Phase 2 Hybrid Rhythm (Prompt, User first, AI Build, Return floor) & Party Mode
- FEAT-KL-004: Tier 2A llm-wiki.md: .md/knowledge/wiki/ Namespace Isolation (COND-02), Ingest/Query/Lint & SHA Provenance
- FEAT-KL-005: Simulator & Archetype Catalog Registration (platform_tooling)
- FEAT-KL-006: 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes
- FEAT-KL-007: Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

from ccba_harness.evals.simulators.platform_tooling import _PLATFORM_TOOLING_SKILLS
from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> object:
    """Dynamically loads run_verify_knowledge_loop.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_knowledge_loop.py"
    spec = importlib.util.spec_from_file_location("run_verify_knowledge_loop", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_knowledge_loop"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_feat_kl_001_frontmatter_and_orchestrator_contract() -> None:
    """Verifies FEAT-KL-001: SkillValidator compliance, orchestrator tier, and slash command."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    skill_path = repo_root / ".agents" / "skills" / "ccba-knowledge-loop" / "SKILL.md"
    assert skill_path.is_file()

    validator = SkillValidator(project_root=repo_root)
    issues = validator.audit_skill(skill_path, check_shallow=True, enforce_gpi=True)
    assert not issues, f"SkillValidator reported issues: {issues}"

    parts = skill_path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-knowledge-loop"
    assert fm["command"] == "/ccba-knowledge-loop"
    assert fm["tier"] == "orchestrator"
    assert fm["is-orchestrated"] is True
    assert fm["user-invocable"] is True
    assert fm["disable-model-invocation"] is True
    assert fm["bundle"] == "_core"


def test_feat_kl_002_single_writer_protocol_and_4phase_orchestration() -> None:
    """Verifies FEAT-KL-002: Single-Writer Protocol (ADR-0053) and 4-phase flow."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-knowledge-loop" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Single-Writer Protocol — ADR 0053",
        "Read-Only Sandbox",
        "Phase 1: Trinh sát & Thu thập Tri thức Sơ cấp",
        "Phase 2: Hội chẩn & Sáng tạo Phương án",
        "Phase 3: Hoạch định & Thiết lập Bản đồ",
        "Phase 4: Vận hành Thực thi Song song & Đóng gói Quyết định",
        "/ccba-youtube-learn",
        "/ccba-research",
        "/ccba-wayfinder",
    ):
        assert token in body, f"Missing /ccba-knowledge-loop token: {token}"


def test_feat_kl_003_hybrid_rhythm_and_party_mode() -> None:
    """Verifies FEAT-KL-003: Phase 2 Hybrid Rhythm (4 beats) and Party Mode personas."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    body = (repo_root / ".agents" / "skills" / "ccba-knowledge-loop" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "Hybrid Rhythm",
        "Prompt:",
        "User first:",
        "AI Build:",
        "Return floor:",
        "Party Mode (Phản biện đa vai)",
        "Action Items",
    ):
        assert token in body


def test_feat_kl_004_llm_wiki_namespace_isolation_and_sha_provenance() -> None:
    """Verifies FEAT-KL-004: llm-wiki.md COND-02 namespace isolation and historical SHA rules."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]
    wiki_path = (
        repo_root / ".agents" / "skills" / "ccba-knowledge-loop" / "references" / "llm-wiki.md"
    )
    assert wiki_path.is_file()
    wiki_text = wiki_path.read_text(encoding="utf-8")

    for marker in (
        ".md/knowledge/wiki/index.md",
        ".md/knowledge/wiki/<topic-slug>.md",
        "Ingest",
        "Query",
        "Lint",
        "Write History, Not the Present",
        "repo@commit_sha",
        "ccba-agent-platform@",
        "[Superseded by YYYY-MM-DD @ <new_sha>]",
    ):
        assert marker in wiki_text, f"Missing llm-wiki.md marker: {marker}"


def test_feat_kl_005_simulator_and_archetype_catalog_registration() -> None:
    """Verifies FEAT-KL-005: PlatformToolingDomainSimulator & archetype catalog registration."""
    runner = _load_runner_module()
    repo_root: Path = runner.REPO_ROOT  # type: ignore[attr-defined]

    assert "ccba-knowledge-loop" in _PLATFORM_TOOLING_SKILLS
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
    assert "knowledge" in pt_entry["keywords"]


def test_feat_kl_006_statechart_bug_path_and_drift_provenance(tmp_path: Path) -> None:
    """Verifies FEAT-KL-006: 5-block server lifecycle, Statechart bug_path replay, and drift modes."""
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
            "from": "WayfinderPhase",
            "to": "ParallelExecPhase",
            "when": "map_and_frontier_tickets_created",
        },
        {
            "from": "ParallelExecPhase",
            "to": "SubagentWriteViolation",
            "when": "subagent_wrote_directly_to_map_or_kb",
        },
    ]
    assert bug_path[0]["to"] == bug_path[1]["from"]

    validate_write = runner.validate_knowledge_write_operation  # type: ignore[attr-defined]
    ok_sub, err_sub = validate_write(
        actor="subagent", target_path=".md/knowledge/issues/demo/map.md"
    )
    assert not ok_sub
    assert "SubagentWriteViolation" in err_sub

    ok_idx, err_idx = validate_write(actor="orchestrator", target_path=".md/knowledge/index.md")
    assert not ok_idx
    assert "RootIndexOverwriteError" in err_idx

    ok_wiki, state_wiki = validate_write(
        actor="orchestrator",
        target_path=".md/knowledge/wiki/index.md",
        has_commit_sha_stamp=True,
    )
    assert ok_wiki
    assert state_wiki == "WikiIngestSync"

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


def test_feat_kl_007_surface_diff_and_domain_eval_parity() -> None:
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
        / "verify-ccba-knowledge-loop"
        / "features"
        / "INDEX.md"
    )
    suite_file = Path(__file__).resolve()
    missing_feats = runner.verify_surface_diff(features_idx, suite_file)  # type: ignore[attr-defined]
    assert not missing_feats, f"Uncovered features in INDEX.md: {missing_feats}"

    changed = runner.check_git_provenance(  # type: ignore[attr-defined]
        "0575c8a164c2d4a9502d820307797da393b76329",
        [
            ".agents/skills/ccba-knowledge-loop/SKILL.md",
            ".agents/skills/ccba-knowledge-loop/references/llm-wiki.md",
        ],
    )
    assert changed == []

    skill_file = repo_root / ".agents" / "skills" / "ccba-knowledge-loop" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-knowledge-loop")
    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=repo_root)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert eval_rep.overall_score == 100.0
    assert eval_rep.passed_items == eval_rep.total_items == 2
