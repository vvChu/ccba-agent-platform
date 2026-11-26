"""test_agent_envelope.py - TDD tests for Agent-First JSON Envelope & Semantic Exit Codes."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ccba_harness.cli import (
    run_door_triage_cli,
    run_verify_doc_cli,
    run_verify_patch_cli,
)
from ccba_harness.door_policy import DoorClassificationResult, OneWayDoorCategory
from ccba_harness.verifier import CommandResult, PatchVerificationReport

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _make_report(results: list[CommandResult]) -> PatchVerificationReport:
    passed = sum(1 for r in results if r.passed)
    return PatchVerificationReport(
        all_passed=(passed == len(results)),
        total_commands=len(results),
        passed_count=passed,
        failed_count=len(results) - passed,
        total_duration_ms=25.0,
        results=results,
    )


def test_verify_patch_json_and_report_file_parity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify --json stdout and --report-file *.json emit identical Additive Flat envelopes."""
    ok_res = [CommandResult(command="pytest -q", exit_code=0, passed=True, duration_ms=10.0)]
    report_path = tmp_path / "out.json"
    with patch("ccba_harness.verifier.verify_patch_execution", return_value=_make_report(ok_res)):
        code = run_verify_patch_cli(
            ["--json", "--report-file", str(report_path), "--cmd", "pytest -q"]
        )

    assert code == 0
    stdout_data = json.loads(capsys.readouterr().out)
    file_data = json.loads(report_path.read_text(encoding="utf-8"))
    assert stdout_data == file_data
    assert stdout_data["schema_version"] == "1"
    assert stdout_data["status"] == "ok"
    assert stdout_data["error"] is None
    assert stdout_data["next_actions"] == []
    assert stdout_data["all_passed"] is True
    assert len(stdout_data["results"]) == 1


def test_verify_patch_next_actions_reuses_self_healing_engine(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify next_actions reuses SelfHealingEngine commands and falls back on unknown errors."""
    diag_res = [
        CommandResult(
            command="python -m ruff format --check pkg/a.py",
            exit_code=1,
            passed=False,
            duration_ms=8.0,
            stdout="Would reformat: pkg/a.py",
        ),
        CommandResult(
            command="python scripts/governance/compile_catalog.py --check",
            exit_code=1,
            passed=False,
            duration_ms=7.0,
            stderr="Drift detected",
        ),
    ]
    with patch("ccba_harness.verifier.verify_patch_execution", return_value=_make_report(diag_res)):
        code = run_verify_patch_cli(["--json", "--cmd", "ruff"])
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "error"
    assert data["error"]["code"] == "CHECKS_FAILED"
    assert data["error"]["retryable"] is False
    cmds = [a["command"] for a in data["next_actions"]]
    assert any("python -m ruff format" in c for c in cmds)
    assert any("python scripts/governance/compile_catalog.py --write" in c for c in cmds)

    # Unmatched error regex -> fallback action re-runs first failed command
    unmatched = [
        CommandResult(command="custom_check --strict", exit_code=3, passed=False, duration_ms=5.0)
    ]
    with patch(
        "ccba_harness.verifier.verify_patch_execution", return_value=_make_report(unmatched)
    ):
        code_fb = run_verify_patch_cli(["--json", "--cmd", "custom_check --strict"])
    assert code_fb == 1
    fb_data = json.loads(capsys.readouterr().out)
    assert fb_data["next_actions"][0]["command"] == "custom_check --strict"


def test_verify_patch_timeout_priority_and_semantic_exit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify COND-TIMEOUT-TEST: timed_out takes precedence over category and yields semantic 124."""
    timed_res = [
        CommandResult(
            command="pytest slow_suite/",
            exit_code=124,
            passed=False,
            duration_ms=180000.0,
            timed_out=True,
            error_message="Command exceeded timeout limit of 180.0s",
        )
    ]
    with patch(
        "ccba_harness.verifier.verify_patch_execution", return_value=_make_report(timed_res)
    ):
        code_default = run_verify_patch_cli(["--json", "--cmd", "pytest slow_suite/"])
    assert code_default == 1
    data_default = json.loads(capsys.readouterr().out)
    assert data_default["error"]["code"] == "COMMAND_TIMEOUT"
    assert data_default["error"]["retryable"] is True
    assert any("--timeout" in a["command"] for a in data_default["next_actions"])

    with patch(
        "ccba_harness.verifier.verify_patch_execution", return_value=_make_report(timed_res)
    ):
        code_sem = run_verify_patch_cli(
            ["--json", "--semantic-exit-codes", "--cmd", "pytest slow_suite/"]
        )
    assert code_sem == 124
    capsys.readouterr()


def test_verify_patch_self_heal_ssot_envelope(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify COND-HEAL-SSOT: HealingReport keeps nested report clean and honors healed all_passed."""
    fail_rep = _make_report(
        [
            CommandResult(
                command="python -m ruff format --check demo.py",
                exit_code=1,
                passed=False,
                duration_ms=5.0,
                stdout="Would reformat: demo.py",
            )
        ]
    )
    pass_rep = _make_report(
        [
            CommandResult(
                command="python -m ruff format --check demo.py",
                exit_code=0,
                passed=True,
                duration_ms=5.0,
                stdout="1 file left unchanged",
            )
        ]
    )
    with (
        patch("ccba_harness.verifier.verify_patch_execution", return_value=fail_rep),
        patch("ccba_harness.healing.verify_patch_execution", side_effect=[fail_rep, pass_rep]),
        patch("ccba_harness.healing.SelfHealingEngine.execute_action", return_value=True),
    ):
        code = run_verify_patch_cli(
            ["--json", "--self-heal", "--cmd", "python -m ruff format --check demo.py"]
        )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema_version"] == "1"
    assert data["status"] == "ok"
    assert data["error"] is None
    assert data["next_actions"] == []
    assert data["success"] is True
    assert len(data["diagnosed_issues"]) >= 1
    assert "schema_version" not in data["final_verification_report"]

    # When self-heal fails, status=error & CHECKS_FAILED read post-heal report
    with (
        patch("ccba_harness.verifier.verify_patch_execution", return_value=fail_rep),
        patch("ccba_harness.healing.verify_patch_execution", return_value=fail_rep),
        patch("ccba_harness.healing.SelfHealingEngine.execute_action", return_value=True),
    ):
        code_fail = run_verify_patch_cli(
            ["--json", "--self-heal", "--cmd", "python -m ruff format --check demo.py"]
        )
    assert code_fail == 1
    fail_data = json.loads(capsys.readouterr().out)
    assert fail_data["status"] == "error"
    assert fail_data["error"]["code"] == "CHECKS_FAILED"
    assert "schema_version" not in fail_data["final_verification_report"]


def test_verify_doc_json_pass_and_fail_spec(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify COND-DOC-FAIL-SPEC: single JSON on stdout without raw stdout bleed on pass/fail."""
    doc = tmp_path / "note.md"
    doc.write_text("# Heading\n" + "Valid content. " * 10, encoding="utf-8")
    code_ok = run_verify_doc_cli(["--target", str(doc), "--min-bytes", "20", "--json"])
    assert code_ok == 0
    out_ok = capsys.readouterr()
    assert out_ok.err == ""
    data_ok = json.loads(out_ok.out)
    assert data_ok["schema_version"] == "1"
    assert data_ok["status"] == "ok"
    assert data_ok["passed"] is True
    assert data_ok["error"] is None
    assert data_ok["next_actions"] == []

    code_fail = run_verify_doc_cli(
        [
            "--target",
            str(doc),
            "--min-bytes",
            "5000",
            "--required-headings",
            "MissingSection",
            "--json",
            "--semantic-exit-codes",
        ]
    )
    assert code_fail == 1
    out_fail = capsys.readouterr()
    assert out_fail.err == ""
    data_fail = json.loads(out_fail.out)
    assert data_fail["status"] == "error"
    assert data_fail["passed"] is False
    assert data_fail["error"]["code"] == "CHECKS_FAILED"
    assert data_fail["error"]["retryable"] is False
    assert len(data_fail["next_actions"]) == 1
    assert "verify-doc" in data_fail["next_actions"][0]["command"]


def test_invalid_input_three_paths_and_help(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify COND-ARGPARSE-EXIT across Path A (verify-patch), Path B (argparse), Path C (--help)."""
    missing_report = tmp_path / "never_created.json"
    # Path A: without --json preserves stderr & return 1
    assert run_verify_patch_cli(["--report-file", str(missing_report)]) == 1
    assert "ERROR: No commands or preset specified" in capsys.readouterr().err
    assert not missing_report.exists()

    # Path A: with --json emits JSON INVALID_INPUT, suppresses stderr, exit 1 default / 2 semantic
    assert run_verify_patch_cli(["--json", "--report-file", str(missing_report)]) == 1
    cap = capsys.readouterr()
    assert cap.err == ""
    assert json.loads(cap.out)["error"]["code"] == "INVALID_INPUT"
    assert not missing_report.exists()

    assert run_verify_patch_cli(["--json", "--semantic-exit-codes", "--preset", "doc"]) == 2
    cap_val = capsys.readouterr()
    assert cap_val.err == ""
    assert json.loads(cap_val.out)["error"]["code"] == "INVALID_INPUT"

    # Path B: verify-doc missing --target preserves SystemExit(2) without --json
    with pytest.raises(SystemExit) as exc_plain:
        run_verify_doc_cli([])
    assert exc_plain.value.code == 2
    capsys.readouterr()

    # Path B: --json passed inside --cmd string or after -- must NOT trigger JSON error mode
    with pytest.raises(SystemExit) as exc_quoted:
        run_verify_patch_cli(["--unknown-flag", "--cmd", "echo --json"])
    assert exc_quoted.value.code == 2
    assert capsys.readouterr().out == ""

    with pytest.raises(SystemExit) as exc_after_dash:
        run_verify_patch_cli(["--unknown-flag", "--", "--json"])
    assert exc_after_dash.value.code == 2
    assert capsys.readouterr().out == ""

    # Path B: real --json flag on argparse error emits single JSON and exit 2
    assert run_verify_doc_cli(["--json"]) == 2
    cap_doc = capsys.readouterr()
    assert cap_doc.err == ""
    assert json.loads(cap_doc.out)["error"]["code"] == "INVALID_INPUT"

    # Path C: --json --help still prints help and raises SystemExit(0)
    for fn in (run_verify_patch_cli, run_verify_doc_cli, run_door_triage_cli):
        with pytest.raises(SystemExit) as exc_help:
            fn(["--json", "--help"])
        assert exc_help.value.code == 0
        assert "usage:" in capsys.readouterr().out.lower()


@pytest.mark.parametrize(
    (
        "door_type",
        "enforce",
        "body_mode",
        "sampled",
        "expected_status",
        "expected_valid",
        "exp_def",
        "exp_sem",
    ),
    [
        ("TWO_WAY_DOOR", False, "none", False, "ok", True, 0, 0),
        ("PAVED_ROAD", True, "missing", True, "ok", True, 0, 0),
        ("ONE_WAY_DOOR", False, "none", False, "approval_required", True, 0, 4),
        ("ONE_WAY_DOOR", False, "invalid", False, "approval_required", False, 0, 4),
        ("ONE_WAY_DOOR", True, "none", False, "error", False, 1, 1),
        ("ONE_WAY_DOOR", True, "missing", False, "error", False, 1, 1),
        ("ONE_WAY_DOOR", True, "oserror", False, "error", False, 1, 1),
        ("ONE_WAY_DOOR", True, "invalid", False, "error", False, 1, 1),
        ("ONE_WAY_DOOR", True, "valid", False, "approval_required", True, 0, 4),
    ],
)
def test_door_triage_complete_five_row_matrix(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    door_type: str,
    enforce: bool,
    body_mode: str,
    sampled: bool,
    expected_status: str,
    expected_valid: bool,
    exp_def: int,
    exp_sem: int,
) -> None:
    """Verify COND-DOOR-MATRIX across all door tiers, enforce flags, and file/OSError states."""
    cats = [OneWayDoorCategory.PUBLIC_API_SEAM] if door_type == "ONE_WAY_DOOR" else []
    mock_res = DoorClassificationResult(
        door_type=door_type,  # type: ignore[arg-type]
        matched_categories=cats,
        sampled_for_audit=sampled,
    )
    body_args: list[str] = []
    target_body = tmp_path / "pr_body.md"
    if body_mode == "missing":
        body_args = ["--pr-body-file", str(tmp_path / "does_not_exist.md")]
    elif body_mode == "invalid":
        target_body.write_text("# No Tradeoff Card", encoding="utf-8")
        body_args = ["--pr-body-file", str(target_body)]
    elif body_mode == "valid":
        target_body.write_text(
            "- **Core Invariant**: Keep compatibility.\n"
            "- **Invalidation Condition**: Any schema break.\n"
            "- **Git Hunk Reference**: `pkg/mod.py#L1-L5`\n",
            encoding="utf-8",
        )
        body_args = ["--pr-body-file", str(target_body)]
    elif body_mode == "oserror":
        target_body.mkdir()  # directory triggers IsADirectoryError (OSError) on read_text
        body_args = ["--pr-body-file", str(target_body)]

    base_args = ["pkg/mod.py", "--json", *body_args]
    if enforce:
        base_args.append("--enforce-tradeoff-card")

    with (
        patch("ccba_harness.door_policy.load_recent_merges_from_git", return_value=[]),
        patch("ccba_harness.door_policy.classify_pr_door", return_value=mock_res),
    ):
        code_def = run_door_triage_cli(base_args)
        cap_def = capsys.readouterr()
        data_def = json.loads(cap_def.out)
        code_sem = run_door_triage_cli([*base_args, "--semantic-exit-codes"])
        cap_sem = capsys.readouterr()
        data_sem = json.loads(cap_sem.out)

    assert cap_def.err == ""
    assert cap_sem.err == ""
    assert code_def == exp_def
    assert code_sem == exp_sem
    assert data_def == data_sem
    assert data_def["status"] == expected_status
    assert data_def["tradeoff_card_valid"] is expected_valid
    if expected_status == "ok":
        assert data_def["error"] is None
    elif expected_status == "approval_required":
        assert data_def["error"]["code"] == "HUMAN_APPROVAL_REQUIRED"
    else:
        assert data_def["error"]["code"] == "TRADEOFF_CARD_INVALID"
        assert len(data_def["tradeoff_card_errors"]) >= 1


def _build_triage_body_args(tmp_path: Path, body_mode: str) -> list[str]:
    """Create fixture PR body file for door-triage CLI test scenarios."""
    target_body = tmp_path / "pr_body.md"
    if body_mode == "none":
        return []
    if body_mode == "missing":
        return ["--pr-body-file", str(tmp_path / "does_not_exist.md")]
    if body_mode == "oserror":
        target_body.mkdir()
        return ["--pr-body-file", str(target_body)]
    if body_mode == "missing_card":
        target_body.write_text("# PR Summary\nNo tradeoff card here.\n", encoding="utf-8")
        return ["--pr-body-file", str(target_body)]
    if body_mode == "invalid_fields":
        target_body.write_text(
            "- **Core Invariant**: TBD\n"
            "- **Invalidation Condition**: N/A\n"
            "- **Git Hunk Reference**: `pkg/mod.py#L1-L80`\n",
            encoding="utf-8",
        )
        return ["--pr-body-file", str(target_body)]
    target_body.write_text(
        "- **Core Invariant**: Preserve JSON schema.\n"
        "- **Invalidation Condition**: Output format breaks.\n"
        "- **Git Hunk Reference**: `pkg/mod.py#L1-L10`\n",
        encoding="utf-8",
    )
    return ["--pr-body-file", str(target_body)]


@pytest.mark.parametrize(
    ("body_mode", "expected_substrings"),
    [
        ("none", ["Missing --pr-body-file for --enforce-tradeoff-card on ONE_WAY_DOOR."]),
        ("missing", ["Cannot read --pr-body-file"]),
        ("oserror", ["Cannot read --pr-body-file"]),
        ("missing_card", ["Missing Tradeoff Card section"]),
        (
            "invalid_fields",
            [
                "Tradeoff Card field 'Core Invariant' is missing or contains a placeholder.",
                "Tradeoff Card field 'Invalidation Condition' is missing or contains a placeholder.",
                "Git Hunk Reference line span exceeds 30 lines",
            ],
        ),
    ],
)
def test_door_triage_non_json_prints_tradeoff_card_errors_to_stderr(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    body_mode: str,
    expected_substrings: list[str],
) -> None:
    """Issue #917: non-JSON door-triage prints card errors & required fields to stderr on enforce failure."""
    mock_res = DoorClassificationResult(
        door_type="ONE_WAY_DOOR",
        matched_categories=[OneWayDoorCategory.PUBLIC_API_SEAM],
        cumulative_streak=7,
        sampled_for_audit=False,
    )
    cli_args = [
        "pkg/mod.py",
        "--enforce-tradeoff-card",
        *_build_triage_body_args(tmp_path, body_mode),
    ]

    with (
        patch("ccba_harness.door_policy.load_recent_merges_from_git", return_value=[]),
        patch("ccba_harness.door_policy.classify_pr_door", return_value=mock_res),
    ):
        code_def = run_door_triage_cli(cli_args)
        cap_def = capsys.readouterr()
        code_sem = run_door_triage_cli([*cli_args, "--semantic-exit-codes"])
        cap_sem = capsys.readouterr()
        code_json = run_door_triage_cli([*cli_args, "--json"])
        cap_json = capsys.readouterr()

    assert code_def == 1
    assert code_sem == 1
    assert code_json == 1
    assert cap_def.out.strip() == (
        "Door: ONE_WAY_DOOR | Categories: PUBLIC_API_SEAM | Streak: 7 | Sampled: False"
    )
    assert cap_def.err == cap_sem.err
    assert "Tradeoff Card validation failed:" in cap_def.err
    for sub in expected_substrings:
        assert sub in cap_def.err
    for field in ("Core Invariant", "Invalidation Condition", "Git Hunk Reference"):
        assert field in cap_def.err

    # Verify --json output remains unchanged and does not write to stderr
    assert cap_json.err == ""
    json_payload = json.loads(cap_json.out)
    assert json_payload["status"] == "error"
    assert json_payload["error"]["code"] == "TRADEOFF_CARD_INVALID"
    assert json_payload["tradeoff_card_valid"] is False
    assert len(json_payload["tradeoff_card_errors"]) == len(expected_substrings)


@pytest.mark.parametrize(
    ("door_type", "enforce", "body_mode", "exp_def", "exp_sem"),
    [
        ("ONE_WAY_DOOR", True, "valid", 0, 4),
        ("ONE_WAY_DOOR", False, "missing_card", 0, 4),
        ("PAVED_ROAD", True, "missing", 0, 0),
        ("TWO_WAY_DOOR", True, "none", 0, 0),
    ],
)
def test_door_triage_non_json_stderr_empty_when_not_failing_enforce(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    door_type: str,
    enforce: bool,
    body_mode: str,
    exp_def: int,
    exp_sem: int,
) -> None:
    """Issue #917: non-JSON door-triage keeps stderr empty when valid, unenforced, or non-ONE_WAY_DOOR."""
    cats = [OneWayDoorCategory.PUBLIC_API_SEAM] if door_type == "ONE_WAY_DOOR" else []
    mock_res = DoorClassificationResult(
        door_type=door_type,  # type: ignore[arg-type]
        matched_categories=cats,
        sampled_for_audit=False,
    )
    cli_args = ["pkg/mod.py", *_build_triage_body_args(tmp_path, body_mode)]
    if enforce:
        cli_args.append("--enforce-tradeoff-card")

    with (
        patch("ccba_harness.door_policy.load_recent_merges_from_git", return_value=[]),
        patch("ccba_harness.door_policy.classify_pr_door", return_value=mock_res),
    ):
        code_def = run_door_triage_cli(cli_args)
        cap_def = capsys.readouterr()
        code_sem = run_door_triage_cli([*cli_args, "--semantic-exit-codes"])
        cap_sem = capsys.readouterr()

    assert code_def == exp_def
    assert code_sem == exp_sem
    assert cap_def.err == ""
    assert cap_sem.err == ""
    assert cap_def.out.startswith(f"Door: {door_type} |")
