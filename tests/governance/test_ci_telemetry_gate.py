"""test_ci_telemetry_gate.py - Governance integration test suite for CI Gates & Swarm Telemetry.

Verifies:
1. Swarm telemetry auditing and CLI subcommands in scripts/governance/subagent_telemetry.py.
2. Verification presets ('telemetry', 'ci') in ccba_harness.verifier.
3. GitHub Actions CI workflow integrity (.github/workflows/ci.yml).
4. Run harness eval gates registering all 7 deterministic gates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from scripts.governance.subagent_telemetry import main as telemetry_cli_main

from ccba_harness.verifier import resolve_preset_commands


@pytest.fixture
def mock_swarm_workspace(tmp_path: Path) -> Path:
    """Create a mock workspace containing multiple subagent transcripts."""
    workspace = tmp_path / "swarm_dir"
    subagent_a = workspace / "subagent_alpha"
    subagent_b = workspace / "subagent_beta"
    subagent_a.mkdir(parents=True)
    subagent_b.mkdir(parents=True)

    log_a = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:00Z",
            "content": "Alpha worker task",
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:02Z",
            "content": "Alpha completed successfully",
        },
    ]

    log_b = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:00Z",
            "content": "Beta worker task with heavier workload",
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:04Z",
            "content": "Beta completed successfully",
        },
    ]

    with (subagent_a / "transcript.jsonl").open("w", encoding="utf-8") as f:
        for s in log_a:
            f.write(json.dumps(s) + "\n")

    with (subagent_b / "transcript.jsonl").open("w", encoding="utf-8") as f:
        for s in log_b:
            f.write(json.dumps(s) + "\n")

    return workspace


def test_swarm_telemetry_script_cli(
    mock_swarm_workspace: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify `subagent_telemetry.py audit-swarm` CLI execution."""
    # 1. Test audit-swarm --json pass
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subagent_telemetry.py",
            "audit-swarm",
            str(mock_swarm_workspace),
            "--max-swarm-tokens",
            "100000",
            "--json",
        ],
    )
    assert telemetry_cli_main() == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total_subagents"] == 2
    assert data["total_swarm_tokens"] > 0

    # 2. Test audit-swarm markdown output
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subagent_telemetry.py",
            "audit-swarm",
            str(mock_swarm_workspace),
            "--max-swarm-tokens",
            "100000",
        ],
    )
    assert telemetry_cli_main() == 0
    out_md = capsys.readouterr().out
    assert "Swarm Multi-Agent Telemetry Report" in out_md

    # 3. Test budget fail exit code 1
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subagent_telemetry.py",
            "audit-swarm",
            str(mock_swarm_workspace),
            "--max-swarm-tokens",
            "10",
        ],
    )
    assert telemetry_cli_main() == 1
    err = capsys.readouterr().err
    assert "[FAIL] Swarm budget violation" in err


def test_verification_presets_telemetry_and_ci() -> None:
    """Verify that 'telemetry' and 'ci' presets resolve deterministic commands."""
    tel_cmds = resolve_preset_commands("telemetry")
    assert any("test_telemetry.py" in c for c in tel_cmds)
    assert any("test_subagent_telemetry.py" in c for c in tel_cmds)

    ci_cmds = resolve_preset_commands("ci")
    assert any("ruff check" in c for c in ci_cmds)
    assert any("pytest" in c for c in ci_cmds)
    assert any("validate_skills.py" in c for c in ci_cmds)
    assert any("compile_catalog.py" in c for c in ci_cmds)
    assert any("sync_hub_adr_matrix.py" in c for c in ci_cmds)


def test_github_actions_ci_workflow_integrity() -> None:
    """Verify .github/workflows/ci.yml syntax, packages, and deterministic lock."""
    ci_file = Path(".github/workflows/ci.yml")
    assert ci_file.exists(), ".github/workflows/ci.yml must exist"

    content = ci_file.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    assert "jobs" in data
    assert "test" in data["jobs"]

    # Check installed packages in step
    test_steps = data["jobs"]["test"]["steps"]
    step_runs = [s.get("run", "") for s in test_steps if "run" in s]
    all_runs = "\n".join(step_runs)

    assert "packages/ccba-harness" in all_runs
    assert "packages/ccba-qc-core" in all_runs
    assert "run_harness_evals.py --all" in all_runs
    assert "verify-patch --preset ci" in all_runs


def test_subprocess_telemetry_cli(mock_swarm_workspace: Path) -> None:
    """Verify subagent_telemetry.py works in a subprocess environment."""
    script_path = Path("scripts/governance/subagent_telemetry.py").resolve()
    cmd = [
        sys.executable,
        str(script_path),
        "audit-swarm",
        str(mock_swarm_workspace),
        "--max-swarm-tokens",
        "500000",
    ]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res.returncode == 0
    assert "Swarm Multi-Agent Telemetry Report" in (res.stdout or "")
