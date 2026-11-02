"""test_harness_suite.py - Contract & Statechart Verification Suite for ccba-harness.

Covers all features declared in `packages/ccba-harness/features/INDEX.md`:
- FEAT-001: CLI Dispatcher & Static Command Registry (`ccba_harness.cli.core.main`)
- FEAT-002: Two-Stage Decision Framework & GPI Engine (`ccba_harness.gpi`)
- FEAT-003: Deterministic Patch & Document Verifier (`ccba_harness.verifier`)
- FEAT-004: 3-Tier One-Way Door Classification (`ccba_harness.door_policy`)
- FEAT-005: 5-Block Verification Lifecycle Runner (`run_verify_harness.py`)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from ccba_harness.cli.core import COMMAND_MAP, main
from ccba_harness.door_policy import OneWayDoorCategory, classify_pr_door
from ccba_harness.gpi import (
    ArchitectureTier,
    DecisionRequest,
    GPIMetrics,
    calculate_gpi,
    evaluate_two_stage_decision,
)
from ccba_harness.verifier import verify_document_artifact, verify_patch_execution

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> object:
    """Dynamically loads run_verify_harness.py from the local harness folder."""
    runner_path = Path(__file__).resolve().parent / "run_verify_harness.py"
    spec = importlib.util.spec_from_file_location("run_verify_harness", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_harness"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_feat_001_cli_dispatcher_and_registry(capsys: pytest.CaptureFixture[str]) -> None:
    """Verifies FEAT-001: CLI root help and subcommand registry contracts."""
    exit_code = main(["--help"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "validate-skill" in captured.out
    assert "evaluate-gpi" in captured.out
    assert "verify-patch" in captured.out
    assert "door-triage" in captured.out

    for required_cmd in (
        "validate-skill",
        "evaluate-gpi",
        "verify-patch",
        "verify-doc",
        "door-triage",
    ):
        assert required_cmd in COMMAND_MAP

    bad_exit = main(["non-existent-subcommand"])
    assert bad_exit == 1


def test_feat_002_two_stage_gpi_decision_contracts() -> None:
    """Verifies FEAT-002: Stage 1 Gates, GPI math formula, and Stage 2 tier routing."""
    score = calculate_gpi(s=4.0, k=3.0, a=2.0, p=1.0)
    assert score == 18.5

    det_res = evaluate_two_stage_decision(
        DecisionRequest(name="pure-parser", is_deterministic=True)
    )
    assert det_res.tier == ArchitectureTier.TIER_1_PACKAGE
    assert not det_res.allow_standalone_skill

    orch_res = evaluate_two_stage_decision(
        DecisionRequest(name="multi-agent-flow", is_orchestrated=True)
    )
    assert orch_res.tier == ArchitectureTier.TIER_3_ORCHESTRATOR
    assert not orch_res.allow_standalone_skill

    low_res = evaluate_two_stage_decision(
        DecisionRequest(
            name="small-guide",
            gpi_metrics=GPIMetrics(s=2.0, k=1.0, a=1.0, p=3.0),
        )
    )
    assert low_res.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    assert not low_res.allow_standalone_skill

    high_res = evaluate_two_stage_decision(
        DecisionRequest(
            name="ccba-deep-skill",
            gpi_metrics=GPIMetrics(s=4.0, k=3.0, a=3.0, p=1.0),
        )
    )
    assert high_res.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    assert high_res.allow_standalone_skill


def test_feat_003_verifier_document_and_patch_contracts(tmp_path: Path) -> None:
    """Verifies FEAT-003: Deterministic document artifact and command verification."""
    artifact = tmp_path / "spec.md"
    artifact.write_text(
        "# Architecture Spec\n\n## Scope\n\nDetailed deterministic verification content exceeding hundred bytes.\n",
        encoding="utf-8",
    )
    doc_ok = verify_document_artifact(
        artifact, min_bytes=50, required_headings=["# Architecture Spec", "## Scope"]
    )
    assert doc_ok.passed
    assert doc_ok.exit_code == 0

    doc_missing = verify_document_artifact(
        artifact, min_bytes=50, required_headings=["## NonExistentHeading"]
    )
    assert not doc_missing.passed
    assert doc_missing.exit_code == 1

    report = verify_patch_execution(
        commands=[f'"{sys.executable}" -c "import sys; sys.exit(0)"'],
        cwd=tmp_path,
    )
    assert report.all_passed
    assert report.passed_count == 1
    assert report.failed_count == 0


def test_feat_004_one_way_door_classification_contracts() -> None:
    """Verifies FEAT-004: 3-tier PR classification (TWO_WAY_DOOR, PAVED_ROAD, ONE_WAY_DOOR)."""
    two_way = classify_pr_door(changed_files=["docs/guide.md", "README.md"], logic_loc=10)
    assert two_way.door_type == "TWO_WAY_DOOR"

    paved = classify_pr_door(
        changed_files=["packages/ccba-harness/tests/test_sample.py"], logic_loc=40
    )
    assert paved.door_type == "PAVED_ROAD"

    one_way = classify_pr_door(
        changed_files=["packages/ccba-harness/AGENTS.md", "pyproject.toml"], logic_loc=25
    )
    assert one_way.door_type == "ONE_WAY_DOOR"
    assert OneWayDoorCategory.PUBLIC_API_SEAM in one_way.matched_categories
    assert OneWayDoorCategory.DEPENDENCY_LICENSE in one_way.matched_categories


def test_feat_005_five_block_runner_primitives(tmp_path: Path) -> None:
    """Verifies FEAT-005: Port pre-flight, Dual-Mode server process group, probe, and cleanup."""
    runner = _load_runner_module()
    port = runner.find_free_port()  # type: ignore[attr-defined]
    assert not runner.is_port_in_use(port)  # type: ignore[attr-defined]

    proc = runner.start_probe_server(port, tmp_path)  # type: ignore[attr-defined]
    try:
        url = f"http://127.0.0.1:{port}/healthz"
        assert runner.poll_readiness(url, timeout_seconds=5.0)  # type: ignore[attr-defined]
        assert runner.is_port_in_use(port)  # type: ignore[attr-defined]
    finally:
        runner.cleanup_process_group(proc)  # type: ignore[attr-defined]

    assert proc.poll() is not None
    assert not runner.is_port_in_use(port)  # type: ignore[attr-defined]


def test_feat_006_statechart_bug_path_replay_and_drift_modes() -> None:
    """Verifies FEAT-006: Statechart bug_path replay (probe_timeout -> Cleanup) and 4-state drift provenance."""
    runner = _load_runner_module()
    dead_port = runner.find_free_port()  # type: ignore[attr-defined]
    dead_url = f"http://127.0.0.1:{dead_port}/healthz"

    bug_path = [
        {"from": "Preflight", "to": "ServerSpawn", "when": "port_free"},
        {"from": "ServerSpawn", "to": "HealthBarrier", "when": "proc_started"},
        {"from": "HealthBarrier", "to": "Cleanup", "when": "probe_timeout"},
    ]
    assert [step["to"] for step in bug_path[:-1]] == [step["from"] for step in bug_path[1:]]
    assert not runner.poll_readiness(dead_url, timeout_seconds=0.1, interval=0.02)  # type: ignore[attr-defined]

    classify = runner.classify_drift_status  # type: ignore[attr-defined]
    cases = [
        ((False, True, False, False), "in_sync"),
        ((False, True, True, True), "updated"),
        ((False, False, True, False), "bug"),
        ((True, False, False, False), "blocked"),
    ]
    for (blocked, passed, changed, intentional), expected in cases:
        actual = classify(
            env_blocked=blocked,
            suite_passed=passed,
            contract_changed=changed,
            intentional_change=intentional,
        )
        assert actual == expected
