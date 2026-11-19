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
import subprocess
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
    assert any("ruff format --check" in c for c in code_cmds)
    assert any("mypy" in c for c in code_cmds)
    assert any("pytest" in c for c in code_cmds)

    code_no_target = resolve_preset_commands("code")
    assert any("ruff check ." in c for c in code_no_target)
    assert any("ruff format --check ." in c for c in code_no_target)
    assert any("pytest tests/ -q" in c for c in code_no_target)

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
    assert any("ruff format --check" in c for c in ci_cmds)
    assert any("mypy" in c for c in ci_cmds)
    assert any("validate_skills.py" in c for c in ci_cmds)
    assert any("compile_catalog.py" in c for c in ci_cmds)
    assert any("sync_hub_adr_matrix.py" in c for c in ci_cmds)

    eval_cmds = resolve_preset_commands("eval")
    assert any("test_evals_engine.py" in c for c in eval_cmds)

    eval_skill_cmds = resolve_preset_commands("eval", "copywriting")
    assert any("eval --skill copywriting" in c for c in eval_skill_cmds)

    eval_ds_cmds = resolve_preset_commands("eval", "test_cases.json")
    assert any("eval --dataset test_cases.json" in c for c in eval_ds_cmds)

    lex_cmds = resolve_preset_commands("lexicon", "docs/")
    assert any("lint_construction_terminology.py --path docs/ --check" in c for c in lex_cmds)

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


def test_cli_verify_patch_with_eval_preset() -> None:
    """Verify `ccba-harness verify-patch --preset eval` integration."""
    code = run_verify_patch_cli(["--preset", "eval"])
    assert code == 0


def test_cli_verify_patch_missing_target_returns_1(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify `ccba-harness verify-patch --preset doc` without --target prints ERROR and exits 1."""
    code = run_verify_patch_cli(["--preset", "doc"])
    assert code == 1
    captured = capsys.readouterr()
    assert "ERROR: Preset 'doc' requires a target file path" in captured.err


def test_shell_command_to_argv_glob_and_win32_quotes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify glob expansion, -c inline code protection, and win32 quote stripping."""
    from ccba_harness.verifier import shell_command_to_argv

    (tmp_path / "test_tuner_a.py").write_text("", encoding="utf-8")
    (tmp_path / "test_tuner_b.py").write_text("", encoding="utf-8")

    argv_glob = shell_command_to_argv("pytest test_tuner*.py -k 'test_foo[bar*]'", cwd=tmp_path)
    assert argv_glob == ["pytest", "test_tuner_a.py", "test_tuner_b.py", "-k", "test_foo[bar*]"]

    monkeypatch.setattr(sys, "platform", "win32")
    win_cmd = '"C:\\\\Python\\\\python.exe" -c "import sys; sys.exit(42)"'
    argv_win = shell_command_to_argv(win_cmd, cwd=tmp_path)
    assert argv_win == ["C:\\\\Python\\\\python.exe", "-c", "import sys; sys.exit(42)"]


def test_cli_verify_patch_repeated_and_multi_token_cmd(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify C2: repeated --cmd/--commands accumulate in order without overwriting."""
    cmd1 = f'"{sys.executable}" -c "print(\'FIRST_CMD\')"'
    cmd2 = f'"{sys.executable}" -c "print(\'SECOND_CMD\')"'
    cmd3 = f'"{sys.executable}" -c "print(\'THIRD_CMD\')"'

    code = run_verify_patch_cli(["--json", "--cmd", cmd1, "--commands", cmd2, cmd3])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total_commands"] == 3
    assert [r["stdout"].strip() for r in data["results"]] == [
        "FIRST_CMD",
        "SECOND_CMD",
        "THIRD_CMD",
    ]


def test_verify_patch_execution_user_commands_precede_preset(tmp_path: Path) -> None:
    """Verify C2: user commands execute first and preset commands are appended after."""
    doc = tmp_path / "spec.md"
    doc.write_text("# Heading\n" + "Valid content body. " * 10, encoding="utf-8")
    user_cmd = f'"{sys.executable}" -c "print(\'USER_FIRST\')"'
    report = verify_patch_execution(
        commands=[user_cmd],
        preset="doc",
        target=doc,
        min_bytes=20,
    )
    assert report.all_passed is True
    assert report.total_commands == 2
    assert "USER_FIRST" in report.results[0].stdout
    assert "verify-doc" in report.results[1].command


def test_resolve_code_preset_single_file_and_test_file(tmp_path: Path) -> None:
    """Verify C3 & C5: single source file resolves pytest via recommend_tests while test_*.py stays intact."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    daemon_file = tmp_path / "scripts" / "chatops_daemon.py"
    leaf_file = tmp_path / "scripts" / "_chatops_telegram.py"
    hermes_file = tmp_path / "scripts" / "hermes_executive_mcp.py"
    chatops_test = tmp_path / "tests" / "test_chatops.py"
    hermes_test = tmp_path / "tests" / "test_executive_ops_mcp.py"

    for f in (daemon_file, leaf_file, hermes_file, chatops_test, hermes_test):
        f.write_text("# stub\n", encoding="utf-8")

    cmds_daemon = resolve_preset_commands("code", "scripts/chatops_daemon.py", cwd=tmp_path)
    assert cmds_daemon[-1].endswith("-m pytest tests/test_chatops.py -q")

    cmds_leaf = resolve_preset_commands("code", "scripts/_chatops_telegram.py", cwd=tmp_path)
    assert cmds_leaf[-1].endswith("-m pytest tests/test_chatops.py -q")

    cmds_hermes = resolve_preset_commands("code", "scripts/hermes_executive_mcp.py", cwd=tmp_path)
    assert cmds_hermes[-1].endswith("-m pytest tests/test_executive_ops_mcp.py -q")

    cmds_test = resolve_preset_commands("code", "tests/test_chatops.py", cwd=tmp_path)
    assert cmds_test[-1].endswith("-m pytest tests/test_chatops.py -q")


def test_compute_file_lf_sha256_and_provenance_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify LF-normalized SHA-256 parity and fail-closed git provenance checks."""
    from ccba_harness import verifier
    from ccba_harness.verifier import check_harness_git_provenance, compute_file_lf_sha256

    lf_file = tmp_path / "doc_lf.md"
    crlf_file = tmp_path / "doc_crlf.md"
    lf_file.write_bytes(b"line1\nline2\n")
    crlf_file.write_bytes(b"line1\r\nline2\r\n")
    digest = compute_file_lf_sha256(lf_file)
    assert digest == compute_file_lf_sha256(crlf_file)

    monkeypatch.setattr(verifier, "_is_git_shallow_repo", lambda _root: False)
    bad_sha = "deadbeef" * 5
    assert check_harness_git_provenance(
        tmp_path, bad_sha, ["doc_lf.md"], expected_sha256={"doc_lf.md": digest}
    ) == [f"UNVERIFIABLE_SYNC_COMMIT:{bad_sha}"]

    monkeypatch.setattr(verifier, "_is_git_shallow_repo", lambda _root: True)
    assert (
        check_harness_git_provenance(
            tmp_path, bad_sha, ["doc_lf.md"], expected_sha256={"doc_lf.md": digest}
        )
        == []
    )
    assert check_harness_git_provenance(
        tmp_path, bad_sha, ["doc_lf.md"], expected_sha256={"doc_lf.md": "0" * 64}
    ) == ["doc_lf.md"]


def _init_fake_hub_repo(root: Path, files: tuple[str, ...]) -> None:
    """Create an isolated Hub-like git repository with pyproject.toml and contract files."""
    from ccba_harness.verifier import _git_clean_env

    env = _git_clean_env()
    subprocess.run(["git", "init"], cwd=str(root), env=env, capture_output=True, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/vvChu/ccba-agent-platform.git"],
        cwd=str(root),
        env=env,
        capture_output=True,
        check=True,
    )
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    for rel in files:
        fpath = root / rel
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text("# stub\n", encoding="utf-8")


def test_skill_contract_ssot_paths_exist_on_hub() -> None:
    """Verify all SSOT live-skill contract test files exist at the Hub repository root."""
    from ccba_harness.verifier import SKILL_CONTRACT_TEST_PATHS

    hub_root = Path(__file__).resolve().parents[3]
    assert len(SKILL_CONTRACT_TEST_PATHS) == 10
    for rel_path in SKILL_CONTRACT_TEST_PATHS:
        assert (hub_root / rel_path).is_file(), f"Missing SSOT contract test: {rel_path}"


def test_preset_skill_and_ci_include_ssot_and_pyproject(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify skill/ci presets include SSOT pytest targets on Hub and safely filter on non-Hub."""
    from ccba_harness.verifier import SKILL_CONTRACT_TEST_PATHS, shell_command_to_argv

    hub_root = Path(__file__).resolve().parents[3]
    for target in (None, ".agents/skills/ccba-new-feature/SKILL.md"):
        cmds = resolve_preset_commands("skill", target=target, cwd=hub_root)
        pytest_cmds = [c for c in cmds if " -m pytest " in c]
        assert len(pytest_cmds) == 1
        argv = shell_command_to_argv(pytest_cmds[0], cwd=hub_root)
        assert "-c" in argv and (hub_root / "pyproject.toml").as_posix() in argv
        for rel in SKILL_CONTRACT_TEST_PATHS:
            assert rel in argv

    ci_cmds = resolve_preset_commands("ci", cwd=hub_root)
    ci_pytest = [c for c in ci_cmds if " -m pytest " in c]
    assert len(ci_pytest) == 1
    ci_argv = shell_command_to_argv(ci_pytest[0], cwd=hub_root)
    assert "-c" in ci_argv and (hub_root / "pyproject.toml").as_posix() in ci_argv
    assert ci_argv.count("tests/governance/") == 1
    for rel in SKILL_CONTRACT_TEST_PATHS:
        if rel.startswith("tests/governance/"):
            assert rel not in ci_argv
        else:
            assert ci_argv.count(rel) == 1

    non_hub_cmds = resolve_preset_commands("skill", cwd=tmp_path)
    assert not any(" -m pytest " in c for c in non_hub_cmds)
    assert "Skipping absent skill contract test path(s)" in capsys.readouterr().err


def test_preset_skill_and_ci_hub_fail_closed_on_missing_ssot(tmp_path: Path) -> None:
    """Verify Hub repos fail closed when any SSOT skill or governance path is missing."""
    from ccba_harness.verifier import SKILL_CONTRACT_TEST_PATHS

    _init_fake_hub_repo(tmp_path, SKILL_CONTRACT_TEST_PATHS)
    root_test = tmp_path / "tests" / "test_upstream_workflows.py"
    root_test.unlink()

    with pytest.raises(ValueError, match="tests/test_upstream_workflows.py"):
        resolve_preset_commands("skill", cwd=tmp_path)

    assert run_verify_patch_cli(["--preset", "skill", "--cwd", str(tmp_path)]) == 1
    assert (
        run_verify_patch_cli(
            ["--preset", "skill", "--cwd", str(tmp_path), "--json", "--semantic-exit-codes"]
        )
        == 2
    )

    root_test.write_text("# restored\n", encoding="utf-8")
    (tmp_path / "tests" / "governance" / "test_orchestrator_parity.py").unlink()
    with pytest.raises(ValueError, match="tests/governance/test_orchestrator_parity.py"):
        resolve_preset_commands("ci", cwd=tmp_path)


def test_verify_patch_execution_runs_skill_preset_at_git_toplevel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify preset commands run at Hub toplevel even when invoked from a subdirectory."""
    from ccba_harness import verifier

    hub_root = Path(__file__).resolve().parents[3]
    hub_subdir = hub_root / "packages" / "ccba-harness"
    captured: list[tuple[str, Path | str | None]] = []

    def _fake_exec(command: str, cwd: Path | str | None, timeout: float) -> CommandResult:
        captured.append((command, cwd))
        return CommandResult(command=command, exit_code=0, passed=True, duration_ms=1.0)

    monkeypatch.setattr(verifier, "_execute_single_command", _fake_exec)
    report = verify_patch_execution(
        commands=['"python" -c "pass"'],
        preset="skill",
        cwd=hub_subdir,
    )
    assert report.all_passed is True
    assert captured[0][1] == hub_subdir
    assert len(captured) > 1
    for _, exec_cwd in captured[1:]:
        assert exec_cwd == hub_root


def test_cli_verify_patch_self_heal_uses_hub_toplevel_from_subdir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify --self-heal anchors SelfHealingEngine base_dir to git toplevel for skill/ci presets."""
    from ccba_harness import healing, verifier

    hub_root = Path(__file__).resolve().parents[3]
    hub_subdir = hub_root / "packages" / "ccba-harness"
    seen_base_dirs: list[Path] = []

    def _fake_verify_patch(**_kwargs: object) -> PatchVerificationReport:
        return PatchVerificationReport(
            all_passed=False,
            total_commands=1,
            passed_count=0,
            failed_count=1,
            total_duration_ms=1.0,
            results=[CommandResult(command="cmd", exit_code=1, passed=False, duration_ms=1.0)],
        )

    class _DummyHealResult:
        final_verification_report = None

        def to_dict(self) -> dict[str, object]:
            return {"all_passed": False, "results": []}

        def to_markdown(self) -> str:
            return "# Heal Report\n"

    class _DummyHealer:
        def __init__(self, base_dir: Path, max_iterations: int = 3) -> None:
            seen_base_dirs.append(base_dir)

        def attempt_closed_loop_healing(self, **_kwargs: object) -> _DummyHealResult:
            return _DummyHealResult()

    monkeypatch.setattr(verifier, "verify_patch_execution", _fake_verify_patch)
    monkeypatch.setattr(healing, "SelfHealingEngine", _DummyHealer)

    code = run_verify_patch_cli(["--preset", "skill", "--self-heal", "--cwd", str(hub_subdir)])
    assert code == 1
    assert seen_base_dirs == [hub_root]
