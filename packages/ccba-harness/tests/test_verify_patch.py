"""test_verify_patch.py - Unit & Integration Tests for Deterministic Patch Verification.

Tests:
1. Core Python API (ccba_harness.verifier):
   - verify_patch_execution with passing commands.
   - verify_patch_execution with failing exit codes.
   - verify_patch_execution with timeout handling.
   - verify_patch_execution with fail_fast=True.
   - PatchVerificationReport to_dict() and to_markdown() format.
2. Standalone CLI (ccba-harness verify-patch):
   - CLI execution with passing and failing commands.
   - CLI JSON output flag (--json).
   - CLI report file generation (--report-file).
   - Commands file loading (--file with plaintext and JSON array).
   - Missing commands error handling.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from ccba_harness import (
    CommandResult,
    PatchVerificationReport,
    resolve_preset_commands,
    verify_document_artifact,
    verify_patch_execution,
)
from ccba_harness.cli import main, run_verify_doc_cli, run_verify_patch_cli

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_verify_patch_execution_passing() -> None:
    """Verify that exit 0 commands report all_passed=True."""
    cmds = [
        f'"{sys.executable}" -c "import sys; sys.exit(0)"',
        f'"{sys.executable}" -c "print(\'Hello World\')"',
    ]
    report = verify_patch_execution(cmds)
    assert report.all_passed is True
    assert report.total_commands == 2
    assert report.passed_count == 2
    assert report.failed_count == 0
    assert report.total_duration_ms > 0
    assert len(report.results) == 2
    for r in report.results:
        assert r.passed is True
        assert r.exit_code == 0
        assert r.timed_out is False


def test_verify_patch_execution_failing() -> None:
    """Verify that non-zero exit codes report all_passed=False and capture error code."""
    cmds = [
        f'"{sys.executable}" -c "import sys; sys.exit(42)"',
    ]
    report = verify_patch_execution(cmds)
    assert report.all_passed is False
    assert report.total_commands == 1
    assert report.passed_count == 0
    assert report.failed_count == 1
    assert report.results[0].exit_code == 42
    assert report.results[0].passed is False


def test_verify_patch_execution_timeout() -> None:
    """Verify that hanging commands trigger timeout and return exit_code=124."""
    # Sleep 3 seconds with 0.2s timeout
    cmds = [
        f'"{sys.executable}" -c "import time; time.sleep(3)"',
    ]
    report = verify_patch_execution(cmds, timeout=0.2)
    assert report.all_passed is False
    assert report.results[0].timed_out is True
    assert report.results[0].exit_code == 124
    assert "timeout" in (report.results[0].error_message or "").lower()


def test_verify_patch_fail_fast() -> None:
    """Verify that fail_fast=True stops execution upon first failure."""
    cmds = [
        f'"{sys.executable}" -c "import sys; sys.exit(0)"',
        f'"{sys.executable}" -c "import sys; sys.exit(1)"',
        f'"{sys.executable}" -c "import sys; sys.exit(0)"',
    ]
    report = verify_patch_execution(cmds, fail_fast=True)
    assert report.all_passed is False
    assert report.total_commands == 2  # Third command should NOT run
    assert report.results[0].passed is True
    assert report.results[1].passed is False


def test_report_to_dict_and_markdown() -> None:
    """Verify that report dictionary and markdown exports are properly formatted."""
    results = [
        CommandResult(
            command="pytest tests/",
            exit_code=0,
            passed=True,
            duration_ms=123.45,
            stdout="1 passed",
        ),
        CommandResult(
            command="ruff check",
            exit_code=1,
            passed=False,
            duration_ms=45.67,
            stderr="Found 1 error",
        ),
    ]
    report = PatchVerificationReport(
        all_passed=False,
        total_commands=2,
        passed_count=1,
        failed_count=1,
        total_duration_ms=169.12,
        results=results,
    )

    # Test dictionary conversion
    d = report.to_dict()
    assert d["all_passed"] is False
    assert d["total_commands"] == 2
    assert len(d["results"]) == 2

    # Test Markdown rendering
    md = report.to_markdown()
    assert "Deterministic Patch Verification Report" in md
    assert "VERIFICATION FAILED" in md
    assert "`pytest tests/`" in md
    assert "`ruff check`" in md
    assert "Failure Diagnostics" in md
    assert "Found 1 error" in md


def test_cli_verify_patch_passing(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI exit 0 when commands pass."""
    cmd = f'"{sys.executable}" -c "import sys; sys.exit(0)"'
    code = run_verify_patch_cli(["--cmd", cmd])
    assert code == 0
    captured = capsys.readouterr()
    assert "ALL PASSED" in captured.out


def test_cli_verify_patch_failing(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI exit 1 when command fails."""
    cmd = f'"{sys.executable}" -c "import sys; sys.exit(7)"'
    code = run_verify_patch_cli(["--cmd", cmd])
    assert code == 1
    captured = capsys.readouterr()
    assert "VERIFICATION FAILED" in captured.out
    assert "- **Exit Code:** 7" in captured.out


def test_cli_verify_patch_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI produces valid JSON with --json."""
    cmd = f'"{sys.executable}" -c "print(\'JSON test\')"'
    code = run_verify_patch_cli(["--json", "--cmd", cmd])
    assert code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["all_passed"] is True
    assert data["total_commands"] == 1
    assert data["results"][0]["passed"] is True


def test_cli_verify_patch_report_file(tmp_path: Path) -> None:
    """Verify CLI writes report files to target path in md and json formats."""
    cmd = f'"{sys.executable}" -c "import sys; sys.exit(0)"'
    md_file = tmp_path / "report.md"
    json_file = tmp_path / "report.json"

    # Test markdown report
    code_md = run_verify_patch_cli(["--report-file", str(md_file), "--cmd", cmd])
    assert code_md == 0
    assert md_file.exists()
    assert "Deterministic Patch Verification Report" in md_file.read_text(encoding="utf-8")

    # Test JSON report
    code_json = run_verify_patch_cli(["--report-file", str(json_file), "--cmd", cmd])
    assert code_json == 0
    assert json_file.exists()
    json_data = json.loads(json_file.read_text(encoding="utf-8"))
    assert json_data["all_passed"] is True


def test_cli_verify_patch_commands_from_file(tmp_path: Path) -> None:
    """Verify reading commands from text and JSON files."""
    # Text file
    txt_file = tmp_path / "commands.txt"
    txt_file.write_text(
        f'# Comment line\n"{sys.executable}" -c "import sys; sys.exit(0)"\n\n',
        encoding="utf-8",
    )
    code_txt = run_verify_patch_cli(["--file", str(txt_file)])
    assert code_txt == 0

    # JSON file
    json_file = tmp_path / "commands.json"
    json_file.write_text(
        json.dumps([f'"{sys.executable}" -c "import sys; sys.exit(0)"']),
        encoding="utf-8",
    )
    code_json = run_verify_patch_cli(["--file", str(json_file)])
    assert code_json == 0


def test_cli_verify_patch_no_commands(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that running without any commands returns exit code 1."""
    code = run_verify_patch_cli([])
    assert code == 1
    captured = capsys.readouterr()
    assert "ERROR: No commands or preset specified" in captured.err


def test_main_dispatch_verify_patch(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that `ccba-harness verify-patch` dispatches properly via main()."""
    cmd = f'"{sys.executable}" -c "import sys; sys.exit(0)"'
    code = main(["verify-patch", "--cmd", cmd])
    assert code == 0
    captured = capsys.readouterr()
    assert "ALL PASSED" in captured.out


def test_verify_document_artifact_success(tmp_path: Path) -> None:
    """Verify that a valid document artifact passes checks."""
    doc = tmp_path / "test_report.md"
    content = "# Legal Opinion Report\n\n## Căn cứ pháp lý\nTheo Luật Xây dựng...\n\n## Đánh giá rủi ro\nRủi ro thấp."
    doc.write_text(content, encoding="utf-8")

    res = verify_document_artifact(
        target_path=doc,
        min_bytes=50,
        required_headings=["Căn cứ pháp lý", "Đánh giá rủi ro"],
    )
    assert res.passed is True
    assert res.exit_code == 0
    assert "Artifact verified:" in res.stdout


def test_verify_document_artifact_missing_file(tmp_path: Path) -> None:
    """Verify that a non-existent document returns exit code 1."""
    doc = tmp_path / "non_existent.md"
    res = verify_document_artifact(target_path=doc)
    assert res.passed is False
    assert res.exit_code == 1
    assert "Artifact not found" in (res.error_message or "")


def test_verify_document_artifact_size_too_small(tmp_path: Path) -> None:
    """Verify that a document below min_bytes fails."""
    doc = tmp_path / "small.md"
    doc.write_text("# Short", encoding="utf-8")
    res = verify_document_artifact(target_path=doc, min_bytes=500)
    assert res.passed is False
    assert res.exit_code == 1
    assert "below minimum threshold" in (res.error_message or "")


def test_verify_document_artifact_missing_heading(tmp_path: Path) -> None:
    """Verify that missing a required heading fails validation."""
    doc = tmp_path / "report.md"
    doc.write_text(
        "# Overview\nContent goes here with sufficient bytes to exceed min bytes threshold easily.",
        encoding="utf-8",
    )
    res = verify_document_artifact(
        target_path=doc,
        min_bytes=20,
        required_headings=["Kết luận pháp lý"],
    )
    assert res.passed is False
    assert res.exit_code == 1
    assert "missing required heading" in (res.error_message or "").lower()


def test_resolve_preset_commands() -> None:
    """Verify preset command resolution for all supported types."""
    code_cmds = resolve_preset_commands("code", "packages/ccba-qc-core")
    assert any("ruff check" in c for c in code_cmds)
    assert any("mypy" in c for c in code_cmds)
    assert any("pytest" in c for c in code_cmds)

    doc_cmds = resolve_preset_commands(
        "doc", "report.md", min_bytes=200, required_headings=["Section A"]
    )
    assert len(doc_cmds) == 1
    assert "verify-doc" in doc_cmds[0]
    assert "--min-bytes 200" in doc_cmds[0]

    skill_cmds = resolve_preset_commands("skill", ".agents/skills/ccba-implement")
    assert any("validate_skills.py" in c for c in skill_cmds)
    assert any("compile_catalog.py" in c for c in skill_cmds)

    adr_cmds = resolve_preset_commands("adr")
    assert any("test_adr.py" in c for c in adr_cmds)

    telemetry_cmds = resolve_preset_commands("telemetry", "sample_log.jsonl")
    assert any("test_telemetry.py" in c for c in telemetry_cmds)
    assert any("budget-check" in c for c in telemetry_cmds)

    ci_cmds = resolve_preset_commands("ci")
    assert any("ruff check" in c for c in ci_cmds)
    assert any("validate_skills.py" in c for c in ci_cmds)
    assert any("compile_catalog.py" in c for c in ci_cmds)
    assert any("sync_hub_adr_matrix.py" in c for c in ci_cmds)

    with pytest.raises(ValueError, match="Unknown verification preset"):
        resolve_preset_commands("unknown_preset")


def test_cli_verify_doc_subcommand(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify standalone `verify-doc` subcommand via CLI and main()."""
    doc = tmp_path / "opinion.md"
    doc.write_text(
        "# Phiếu Ý Kiến Pháp Lý\nNội dung đầy đủ vượt quá ngưỡng tối thiểu.", encoding="utf-8"
    )

    code = run_verify_doc_cli(["--target", str(doc), "--min-bytes", "30"])
    assert code == 0

    code_main = main(["verify-doc", "--target", str(doc), "--min-bytes", "30"])
    assert code_main == 0


def test_cli_verify_patch_with_doc_preset(tmp_path: Path) -> None:
    """Verify `ccba-harness verify-patch --preset doc` integration."""
    doc = tmp_path / "valid.md"
    doc.write_text(
        "# Title\n## Scope\nDetailed content for testing verify-patch doc preset.", encoding="utf-8"
    )

    code = run_verify_patch_cli(
        [
            "--preset",
            "doc",
            "--target",
            str(doc),
            "--min-bytes",
            "20",
            "--required-headings",
            "Scope",
        ]
    )
    assert code == 0
