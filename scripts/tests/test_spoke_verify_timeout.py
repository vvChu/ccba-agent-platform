"""Unit tests for configurable --verify timeout and timeout diagnostics (Issue #889)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ccba_harness.verifier import CommandResult, PatchVerificationReport
from scripts.spoke.sync import (
    DEFAULT_VERIFY_TIMEOUT,
    VERIFY_TIMEOUT_ENV_VAR,
    SpokeSynchronizer,
    parse_positive_verify_timeout,
    resolve_verify_timeout,
    sync_all_spokes,
    sync_project,
)
from scripts.spoke.sync.cli import run_spoke_sync_cli


def _setup_minimal_hub_and_spoke(tmp_path: Path) -> tuple[Path, Path]:
    """Create minimal isolated Hub and Spoke directories with a sample test file."""
    hub_root = tmp_path / "mock_hub"
    cat_dir = hub_root / ".agents" / "skills" / "platform-loader"
    cat_dir.mkdir(parents=True)
    (cat_dir / "catalog.yaml").write_text(
        "bundles:\n  Phần mềm: [_core]\nskills: []\nworkflows: []\n",
        encoding="utf-8",
    )

    spoke_root = tmp_path / "mock_spoke"
    (spoke_root / ".agents").mkdir(parents=True)
    (spoke_root / ".agents" / "workspace_context.yaml").write_text(
        "project:\n  name: TimeoutTestSpoke\n  type: Phần mềm\n",
        encoding="utf-8",
    )
    (spoke_root / "tests").mkdir()
    (spoke_root / "tests" / "test_smoke.py").write_text(
        "def test_ok():\n    pass\n", encoding="utf-8"
    )
    return hub_root, spoke_root


def test_resolve_verify_timeout_precedence_and_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify timeout precedence: CLI > CCBA_VERIFY_TIMEOUT > 180.0s with whitespace stripping."""
    monkeypatch.delenv(VERIFY_TIMEOUT_ENV_VAR, raising=False)
    assert resolve_verify_timeout() == DEFAULT_VERIFY_TIMEOUT == 180.0

    monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, " 300 ")
    assert resolve_verify_timeout() == 300.0

    monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, "245.5")
    assert resolve_verify_timeout() == 245.5
    assert resolve_verify_timeout(420) == 420.0

    monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, "invalid")
    assert resolve_verify_timeout(360.0) == 360.0


@pytest.mark.parametrize(
    "bad_value",
    [
        True,
        False,
        "",
        "   ",
        "abc",
        0,
        0.0,
        -5,
        "-12.5",
        float("nan"),
        float("inf"),
        float("-inf"),
        "nan",
        "inf",
        "-inf",
    ],
)
def test_parse_positive_verify_timeout_rejects_invalid(bad_value: object) -> None:
    """Verify parser rejects bool, empty/whitespace, non-numeric, NaN, inf, and <= 0 values."""
    with pytest.raises(ValueError, match="--verify-timeout"):
        parse_positive_verify_timeout(bad_value, source="--verify-timeout")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=VERIFY_TIMEOUT_ENV_VAR):
        parse_positive_verify_timeout(bad_value, source=VERIFY_TIMEOUT_ENV_VAR)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_env", ["", "   ", "0", "-10", "nan", "inf", "-inf", "abc"])
def test_resolve_verify_timeout_env_fail_closed(
    monkeypatch: pytest.MonkeyPatch, bad_env: str
) -> None:
    """Verify declared empty, whitespace, or invalid CCBA_VERIFY_TIMEOUT fails closed."""
    monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, bad_env)
    with pytest.raises(ValueError, match=VERIFY_TIMEOUT_ENV_VAR):
        resolve_verify_timeout()


def test_cli_verify_timeout_forwarding_and_omission(tmp_path: Path) -> None:
    """Verify CLI forwards --verify-timeout for single/--all and omits kwarg when unset."""
    with patch("scripts.spoke.sync.cli.sync_project", return_value=0) as mock_sync:
        code = run_spoke_sync_cli(
            ["--spoke", str(tmp_path), "--apply", "--verify", "--verify-timeout", "360"]
        )
        assert code == 0
        assert mock_sync.call_args.kwargs.get("verify_timeout") == 360.0

    with patch("scripts.spoke.sync.cli.sync_project", return_value=0) as mock_sync:
        code = run_spoke_sync_cli(["--spoke", str(tmp_path), "--apply", "--verify"])
        assert code == 0
        assert "verify_timeout" not in mock_sync.call_args.kwargs

    with patch("scripts.spoke.sync.cli.sync_all_spokes", return_value=0) as mock_all:
        code = run_spoke_sync_cli(["--all", "--apply", "--verify", "--verify-timeout", " 240.5 "])
        assert code == 0
        assert mock_all.call_args.kwargs.get("verify_timeout") == 240.5


@pytest.mark.parametrize("bad_cli", ["0", "-1", "nan", "inf", "-inf", "abc", "", "   "])
def test_cli_verify_timeout_rejects_invalid_with_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], bad_cli: str
) -> None:
    """Verify invalid --verify-timeout CLI values fail closed at parse time with exit code 2."""
    with pytest.raises(SystemExit) as exc_info:
        run_spoke_sync_cli(
            ["--spoke", str(tmp_path), "--apply", "--verify", "--verify-timeout", bad_cli]
        )
    assert exc_info.value.code == 2
    assert "--verify-timeout" in capsys.readouterr().err


def test_verify_spoke_gate_ordering_broken_link_vs_broken_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify markdown link audit runs before timeout resolver when both link and env are broken."""
    spoke_root = tmp_path / "broken_spoke"
    md_dir = spoke_root / ".md"
    md_dir.mkdir(parents=True)
    (md_dir / "INDEX.md").write_text("# Index\n- [Broken](missing.md)\n", encoding="utf-8")

    monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, "invalid")
    engine = SpokeSynchronizer(spoke_root, tmp_path)
    assert engine.verify_spoke(hub_root=tmp_path) == 1
    err = capsys.readouterr().err
    assert "broken links" in err
    assert "Invalid verify timeout configuration" not in err


def test_verify_spoke_empty_cmds_valid_and_invalid_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify empty command list returns 0 for valid env and fails closed (1) for invalid env."""
    spoke_root = tmp_path / "empty_spoke"
    spoke_root.mkdir()
    engine = SpokeSynchronizer(spoke_root, tmp_path)

    monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, "250")
    assert engine.verify_spoke(hub_root=tmp_path) == 0

    monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, "bad")
    assert engine.verify_spoke(hub_root=tmp_path) == 1
    err = capsys.readouterr().err
    assert "Invalid verify timeout configuration" in err
    assert VERIFY_TIMEOUT_ENV_VAR in err


def test_sync_project_propagates_verify_timeout_and_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify sync_project propagates CCBA_VERIFY_TIMEOUT and explicit verify_timeout."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    monkeypatch.setenv("CCBA_HUB_PATH", str(hub_root))
    captured_timeouts: list[float] = []

    def fake_verify(commands: list[str], cwd: Path, fail_fast: bool = True, timeout: float = 180.0):
        captured_timeouts.append(timeout)
        return PatchVerificationReport(
            all_passed=True,
            total_commands=len(commands),
            passed_count=len(commands),
            failed_count=0,
            total_duration_ms=10.0,
            results=[CommandResult(c, 0, True, 10.0) for c in commands],
        )

    with patch("ccba_harness.verifier.verify_patch_execution", side_effect=fake_verify):
        monkeypatch.setenv(VERIFY_TIMEOUT_ENV_VAR, "315")
        rc_env = sync_project(
            spoke_root,
            dry_run=False,
            check_git=False,
            backup=False,
            verify=True,
            pull_hub=False,
            allow_stale_catalog=True,
        )
        rc_cli = sync_project(
            spoke_root,
            dry_run=False,
            check_git=False,
            backup=False,
            verify=True,
            pull_hub=False,
            allow_stale_catalog=True,
            verify_timeout=420.0,
        )
    assert rc_env == 0
    assert rc_cli == 0
    assert captured_timeouts == [315.0, 420.0]


def test_sync_all_spokes_timeout_diagnostics_and_batch_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify sync_all_spokes forwards verify_timeout, logs 124 diagnostics, and returns batch 1."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    monkeypatch.setenv("CCBA_HUB_PATH", str(hub_root))
    captured_timeouts: list[float] = []

    def fake_timeout_verify(
        commands: list[str], cwd: Path, fail_fast: bool = True, timeout: float = 180.0
    ) -> PatchVerificationReport:
        captured_timeouts.append(timeout)
        failed = CommandResult(
            command=commands[-1],
            exit_code=124,
            passed=False,
            duration_ms=180010.0,
            stdout="...",
            stderr="",
            timed_out=True,
            error_message=f"Command exceeded timeout limit of {timeout}s",
        )
        return PatchVerificationReport(False, 1, 0, 1, 180010.0, [failed])

    mock_spokes = [{"name": "timeout_spoke", "path": str(spoke_root), "project_type": "Phần mềm"}]
    with (
        patch(
            "scripts.spoke.decrypt_spoke_registry.get_registered_spokes", return_value=mock_spokes
        ),
        patch("ccba_harness.verifier.verify_patch_execution", side_effect=fake_timeout_verify),
    ):
        rc = sync_all_spokes(
            hub_root=hub_root,
            dry_run=False,
            check_git=False,
            backup=False,
            verify=True,
            allow_stale_catalog=True,
            verify_timeout=210.0,
        )

    assert rc == 1
    assert captured_timeouts == [210.0]
    err = capsys.readouterr().err
    assert "exit code 124" in err
    assert "Command exceeded timeout limit of 210.0s" in err
    assert "180010ms" in err
    assert "--durations=15" in err
    assert "--verify-timeout" in err


def test_execute_verification_commands_diagnostic_variants(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify stderr output for timed_out=True, error_message-only, and normal test failures."""
    engine = SpokeSynchronizer(tmp_path, tmp_path)

    timed_out_res = CommandResult(
        command="pytest -q",
        exit_code=124,
        passed=False,
        duration_ms=180012.4,
        stdout="partial output",
        timed_out=True,
        error_message="Command exceeded timeout limit of 180.0s",
    )
    with patch(
        "ccba_harness.verifier.verify_patch_execution",
        return_value=PatchVerificationReport(False, 1, 0, 1, 180012.4, [timed_out_res]),
    ):
        assert engine._execute_verification_commands(["pytest -q"], timeout=180.0) == 124
    err_timeout = capsys.readouterr().err
    assert "Reason: Command exceeded timeout limit of 180.0s (duration: 180012ms)" in err_timeout
    assert "--durations=15" in err_timeout
    assert "--verify-timeout" in err_timeout
    assert VERIFY_TIMEOUT_ENV_VAR in err_timeout

    err_only_res = CommandResult(
        command="pytest -q",
        exit_code=1,
        passed=False,
        duration_ms=12.0,
        timed_out=False,
        error_message="FileNotFoundError: pytest",
    )
    with patch(
        "ccba_harness.verifier.verify_patch_execution",
        return_value=PatchVerificationReport(False, 1, 0, 1, 12.0, [err_only_res]),
    ):
        assert engine._execute_verification_commands(["pytest -q"]) == 1
    err_only = capsys.readouterr().err
    assert "Reason: FileNotFoundError: pytest (duration: 12ms)" in err_only
    assert "Hint:" not in err_only

    normal_fail = CommandResult(
        command="pytest -q",
        exit_code=1,
        passed=False,
        duration_ms=500.0,
        stderr="1 failed in 0.50s",
        timed_out=False,
        error_message=None,
    )
    with patch(
        "ccba_harness.verifier.verify_patch_execution",
        return_value=PatchVerificationReport(False, 1, 0, 1, 500.0, [normal_fail]),
    ):
        assert engine._execute_verification_commands(["pytest -q"]) == 1
    err_normal = capsys.readouterr().err
    assert "Failed Command: pytest -q" in err_normal
    assert "Output Snippet:\n1 failed in 0.50s" in err_normal
    assert "Reason:" not in err_normal
    assert "Hint:" not in err_normal


def test_execute_verification_commands_handles_bad_duration_ms(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify non-numeric duration_ms falls back to 0ms and preserves exit code 124."""
    engine = SpokeSynchronizer(tmp_path, tmp_path)
    malformed = SimpleNamespace(
        command="pytest -q",
        exit_code=124,
        passed=False,
        duration_ms="not-a-number",
        stdout="",
        stderr="",
        timed_out=True,
        error_message="Timed out",
    )
    report = SimpleNamespace(all_passed=False, results=[malformed])
    with patch("ccba_harness.verifier.verify_patch_execution", return_value=report):
        assert engine._execute_verification_commands(["pytest -q"]) == 124
    err = capsys.readouterr().err
    assert "Reason: Timed out (duration: 0ms)" in err
    assert "Hint:" in err
