"""Tests for Autonomous Self-Healing & Closed-Loop CI Patch Engine (P4.4).

Verifies failure diagnosis (ruff format, ruff check, catalog drift, pytest),
action generation, closed-loop execution, iteration ceiling, and atomic rollback.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.governance.self_healing import run_self_healing_cli

from ccba_harness.healing import (
    DiagnosticIssue,
    ErrorCategory,
    HealingAction,
    HealingReport,
    SelfHealingEngine,
)
from ccba_harness.verifier import CommandResult, PatchVerificationReport


class TestSelfHealingEngineDiagnosis:
    """Test diagnosis pattern recognition for various tool failures."""

    def test_diagnose_ruff_format_error(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        mock_res = CommandResult(
            command="python -m ruff format --check .",
            exit_code=1,
            passed=False,
            duration_ms=10.0,
            stdout="Would reformat: src/pkg/bad_format.py\n1 file would be reformatted",
            stderr="",
        )
        report = PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=10.0,
            results=[mock_res],
        )

        issues = engine.diagnose_failures(report)
        assert len(issues) == 1
        assert issues[0].category == ErrorCategory.FORMAT_STYLE.value
        assert issues[0].file_path == "src/pkg/bad_format.py"

    def test_diagnose_ruff_lint_error(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        mock_res = CommandResult(
            command="python -m ruff check src/",
            exit_code=1,
            passed=False,
            duration_ms=10.0,
            stdout="src/module.py:15:1: F401 `os` imported but unused\nFound 1 error.",
            stderr="",
        )
        report = PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=10.0,
            results=[mock_res],
        )

        issues = engine.diagnose_failures(report)
        assert len(issues) == 1
        assert issues[0].category == ErrorCategory.LINT_SYNTAX.value
        assert issues[0].file_path == "src/module.py"
        assert issues[0].line_number == 15
        assert issues[0].rule_code == "F401"

    def test_diagnose_catalog_drift(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        mock_res = CommandResult(
            command="python scripts/governance/compile_catalog.py --check",
            exit_code=1,
            passed=False,
            duration_ms=10.0,
            stdout="ERROR: Catalog drift detected! Differences found.",
            stderr="",
        )
        report = PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=10.0,
            results=[mock_res],
        )

        issues = engine.diagnose_failures(report)
        assert len(issues) == 1
        assert issues[0].category == ErrorCategory.METADATA_DRIFT.value
        assert "catalog" in issues[0].message.lower() and "out of sync" in issues[0].message.lower()

    def test_diagnose_adr_matrix_drift(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        mock_res = CommandResult(
            command="python scripts/sync_hub_adr_matrix.py --check",
            exit_code=1,
            passed=False,
            duration_ms=10.0,
            stdout="ERROR: ADR matrix out of sync!",
            stderr="",
        )
        report = PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=10.0,
            results=[mock_res],
        )

        issues = engine.diagnose_failures(report)
        assert len(issues) == 1
        assert issues[0].category == ErrorCategory.METADATA_DRIFT.value
        assert "adr matrix is out of sync" in issues[0].message.lower()

    def test_diagnose_pytest_failure(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        mock_res = CommandResult(
            command="python -m pytest tests/test_math.py",
            exit_code=1,
            passed=False,
            duration_ms=10.0,
            stdout="FAILED tests/test_math.py::test_add - assert 1 + 1 == 3",
            stderr="",
        )
        report = PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=10.0,
            results=[mock_res],
        )

        issues = engine.diagnose_failures(report)
        assert len(issues) == 1
        assert issues[0].category == ErrorCategory.TEST_ASSERTION.value
        assert issues[0].file_path == "tests/test_math.py"
        assert "test_add" in issues[0].message


class TestRemediationActions:
    """Test action generation and execution mapping."""

    def test_generate_actions_for_format_and_lint(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        issues = [
            DiagnosticIssue(
                category=ErrorCategory.FORMAT_STYLE.value,
                command="python -m ruff format --check .",
                file_path="src/a.py",
                message="Format error",
            ),
            DiagnosticIssue(
                category=ErrorCategory.LINT_SYNTAX.value,
                command="python -m ruff check .",
                file_path="src/b.py",
                rule_code="F401",
                message="Unused import",
            ),
            DiagnosticIssue(
                category=ErrorCategory.METADATA_DRIFT.value,
                command="python scripts/governance/compile_catalog.py --check",
                message="Catalog drift",
            ),
        ]

        actions = engine.generate_remediation_actions(issues)
        assert len(actions) == 3

        action_cmds = [a.command for a in actions if a.command]
        assert any("compile_catalog.py --write" in c for c in action_cmds)
        assert any("ruff check --fix" in c and '"src/b.py"' in c for c in action_cmds)
        assert any(
            "ruff format" in c and '"src/a.py"' in c and '"src/b.py"' in c for c in action_cmds
        )


class TestClosedLoopHealingExecution:
    """Test end-to-end closed loop healing flow, rollback safety, and limits."""

    def test_healing_already_passed(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        with patch("ccba_harness.healing.verify_patch_execution") as mock_verify:
            mock_verify.return_value = PatchVerificationReport(
                all_passed=True,
                total_commands=1,
                passed_count=1,
                failed_count=0,
                total_duration_ms=10.0,
            )
            report = engine.attempt_closed_loop_healing(["echo ok"])
            assert report.success is True
            assert report.iterations_run == 0
            assert report.final_verification_passed is True
            assert report.rollback_performed is False

    def test_healing_success_on_iteration_1(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path)
        test_file = tmp_path / "sample.py"
        test_file.write_text("x=1\ny=2\n", encoding="utf-8")

        initial_failed_report = PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=10.0,
            results=[
                CommandResult(
                    command="python -m ruff format --check sample.py",
                    exit_code=1,
                    passed=False,
                    duration_ms=10.0,
                    stdout="Would reformat: sample.py",
                )
            ],
        )

        subsequent_passed_report = PatchVerificationReport(
            all_passed=True,
            total_commands=1,
            passed_count=1,
            failed_count=0,
            total_duration_ms=10.0,
            results=[
                CommandResult(
                    command="python -m ruff format --check sample.py",
                    exit_code=0,
                    passed=True,
                    duration_ms=10.0,
                    stdout="1 file left unchanged",
                )
            ],
        )

        with patch(
            "ccba_harness.healing.verify_patch_execution",
            side_effect=[initial_failed_report, subsequent_passed_report],
        ):
            with patch.object(engine, "execute_action") as mock_exec:
                mock_exec.return_value = True
                report = engine.attempt_closed_loop_healing(
                    ["python -m ruff format --check sample.py"]
                )
                assert report.success is True
                assert report.iterations_run == 1
                assert report.final_verification_passed is True
                assert report.rollback_performed is False
                assert len(report.actions_taken) >= 1

    def test_healing_iteration_limit_and_rollback(self, tmp_path: Path):
        engine = SelfHealingEngine(base_dir=tmp_path, max_iterations=2)
        test_file = tmp_path / "broken.py"
        original_content = "def invalid_syntax(\n"
        test_file.write_text(original_content, encoding="utf-8")

        failing_report = PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=10.0,
            results=[
                CommandResult(
                    command="python -m ruff format --check broken.py",
                    exit_code=1,
                    passed=False,
                    duration_ms=10.0,
                    stdout="Would reformat: broken.py",
                )
            ],
        )

        # Snapshot provided by caller
        snapshot = {test_file: original_content}

        with patch("ccba_harness.healing.verify_patch_execution", return_value=failing_report):
            with patch.object(engine, "execute_action") as mock_exec:

                def modify_file(act: HealingAction):
                    act.executed = True
                    act.success = True
                    test_file.write_text("modified broken content", encoding="utf-8")
                    return True

                mock_exec.side_effect = modify_file
                report = engine.attempt_closed_loop_healing(
                    verify_commands=["python -m ruff format --check broken.py"],
                    snapshot=snapshot,
                )

                assert report.success is False
                assert report.iterations_run == 2
                assert report.final_verification_passed is False
                assert report.rollback_performed is True
                # Critical check: original content restored by rollback
                assert test_file.read_text(encoding="utf-8") == original_content


class TestSelfHealingSerializationAndCLI:
    """Test report formatting, CLI parser, and dry-run flag."""

    def test_healing_report_to_dict_and_markdown(self):
        report = HealingReport(
            success=True,
            iterations_run=1,
            diagnosed_issues=[
                DiagnosticIssue(
                    category=ErrorCategory.FORMAT_STYLE.value,
                    command="ruff format",
                    file_path="test.py",
                    message="Unformatted",
                )
            ],
            actions_taken=[
                HealingAction(
                    action_type="COMMAND_AUTORUN",
                    description="Format test.py",
                    command="python -m ruff format test.py",
                    executed=True,
                    success=True,
                )
            ],
            final_verification_passed=True,
            rollback_performed=False,
            duration_ms=120.5,
        )

        d = report.to_dict()
        assert d["success"] is True
        assert d["iterations_run"] == 1
        assert len(d["diagnosed_issues"]) == 1
        assert len(d["actions_taken"]) == 1

        md = report.to_markdown()
        assert "# 🩹 Autonomous Self-Healing Report: ✅ SELF-HEALING SUCCEEDED" in md
        assert "python -m ruff format test.py" in md

    def test_cli_dry_run_mode(self, capsys):
        with patch("scripts.governance.self_healing.verify_patch_execution") as mock_verify:
            mock_verify.return_value = PatchVerificationReport(
                all_passed=False,
                total_commands=1,
                passed_count=0,
                failed_count=1,
                total_duration_ms=10.0,
                results=[
                    CommandResult(
                        command="python -m ruff format --check foo.py",
                        exit_code=1,
                        passed=False,
                        duration_ms=10.0,
                        stdout="Would reformat: foo.py",
                    )
                ],
            )
            exit_code = run_self_healing_cli(
                ["-c", "python -m ruff format --check foo.py", "--dry-run"]
            )
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Self-Healing Dry-Run Diagnostics" in captured.out
            assert "Proposed Actions" in captured.out

    def test_apply_worker_patch_self_heal_success(self, tmp_path: Path):
        from scripts.governance.apply_worker_patch import PatchBlock, execute_swarm_patches

        target_file = tmp_path / "mod.py"
        target_file.write_text("a = 1\n", encoding="utf-8")

        patch_block = PatchBlock(
            file_path="mod.py",
            search_content="a = 1\n",
            replace_content="a = 1\nb = 2\n",
        )

        with patch("ccba_harness.healing.verify_patch_execution") as mock_verify:
            # 1. Initial verification fails
            # 2. Re-verification after healing passes
            mock_verify.side_effect = [
                PatchVerificationReport(
                    all_passed=False,
                    total_commands=1,
                    passed_count=0,
                    failed_count=1,
                    total_duration_ms=10.0,
                    results=[
                        CommandResult(
                            command="python -m ruff format --check mod.py",
                            exit_code=1,
                            passed=False,
                            duration_ms=10.0,
                            stdout="Would reformat: mod.py",
                        )
                    ],
                ),
                PatchVerificationReport(
                    all_passed=True,
                    total_commands=1,
                    passed_count=1,
                    failed_count=0,
                    total_duration_ms=10.0,
                    results=[
                        CommandResult(
                            command="python -m ruff format --check mod.py",
                            exit_code=0,
                            passed=True,
                            duration_ms=10.0,
                            stdout="1 file left unchanged",
                        )
                    ],
                ),
            ]
            with patch("ccba_harness.healing.SelfHealingEngine.execute_action", return_value=True):
                report = execute_swarm_patches(
                    patches=[patch_block],
                    base_dir=tmp_path,
                    apply=True,
                    verify=True,
                    verify_commands=["python -m ruff format --check mod.py"],
                    self_heal=True,
                )

                assert report.success is True
                assert report.semantic_conflict is False
                assert report.rollback_performed is False

    def test_cli_verify_patch_with_self_heal(self, capsys):
        from ccba_harness.cli import run_verify_patch_cli

        with patch("ccba_harness.healing.verify_patch_execution") as mock_verify:
            mock_verify.side_effect = [
                PatchVerificationReport(
                    all_passed=False,
                    total_commands=1,
                    passed_count=0,
                    failed_count=1,
                    total_duration_ms=10.0,
                    results=[
                        CommandResult(
                            command="python -m ruff format --check demo.py",
                            exit_code=1,
                            passed=False,
                            duration_ms=10.0,
                            stdout="Would reformat: demo.py",
                        )
                    ],
                ),
                PatchVerificationReport(
                    all_passed=True,
                    total_commands=1,
                    passed_count=1,
                    failed_count=0,
                    total_duration_ms=10.0,
                    results=[
                        CommandResult(
                            command="python -m ruff format --check demo.py",
                            exit_code=0,
                            passed=True,
                            duration_ms=10.0,
                            stdout="1 file left unchanged",
                        )
                    ],
                ),
            ]
            with patch("ccba_harness.healing.SelfHealingEngine.execute_action", return_value=True):
                exit_code = run_verify_patch_cli(
                    [
                        "-c",
                        "python -m ruff format --check demo.py",
                        "--self-heal",
                    ]
                )
                assert exit_code == 0
                captured = capsys.readouterr()
                assert "SELF-HEALING SUCCEEDED" in captured.out
