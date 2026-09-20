"""test_tuner_daemon.py - Unit tests for ccba_harness.evals.daemon Deep Seam."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest

from ccba_harness.evals.daemon import (
    NightlyDaemonReport,
    NightlyTunerDaemon,
    SkillEvolutionSummary,
    WeightedPriorityQueue,
    find_project_root,
    send_telegram_alert,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_find_project_root() -> None:
    """Verify find_project_root resolves repo root with .git or .agents."""
    root = find_project_root()
    assert (root / ".agents").exists() or (root / ".git").exists()


def test_daemon_exports_and_priority_queue() -> None:
    """Verify priority queue ordering preserves failing and mediocre skills first."""
    skills = [
        {"skill_name": "s_100", "baseline_score": 100.0},
        {"skill_name": "s_70", "baseline_score": 70.0},
        {"skill_name": "s_92", "baseline_score": 92.0},
    ]
    ranked = WeightedPriorityQueue.rank_skills(skills)
    names = [s["skill_name"] for s in ranked]
    assert names == ["s_70", "s_92", "s_100"]


def test_daemon_custom_alert_emitter() -> None:
    """Verify NightlyTunerDaemon respects custom injected alert_emitter."""
    captured: list[str] = []

    def mock_emitter(msg: str) -> bool:
        captured.append(msg)
        return True

    daemon = NightlyTunerDaemon(alert_emitter=mock_emitter)
    report = NightlyDaemonReport(
        timestamp="20260919_120000",
        branch_name="auto-tune/test",
        total_skills_scanned=1,
        skills_optimized=1,
        total_commits=1,
        results=[
            SkillEvolutionSummary(
                skill_name="test-skill",
                target_file=Path("SKILL.md"),
                baseline_score=80.0,
                final_score=95.0,
                commits_kept=1,
                rollbacks=0,
                status="IMPROVED",
            )
        ],
    )
    result = daemon.send_telegram_notification(report)
    assert result is True
    assert len(captured) == 1
    assert "test-skill" in captured[0]


def test_daemon_send_telegram_alert_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify send_telegram_alert with mock fallback."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    res = send_telegram_alert("Hello test", mock_fallback=True)
    assert res is True


def test_daemon_target_ref_initialization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify target_ref defaults and fallback to main when origin/main cannot be verified."""
    class MockResult:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    # When origin/main fails to verify
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockResult(1))
    daemon = NightlyTunerDaemon()
    assert daemon.target_ref == "main"

    # When origin/main succeeds
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockResult(0))
    daemon2 = NightlyTunerDaemon()
    assert daemon2.target_ref == "origin/main"

    # Explicit target_ref
    daemon3 = NightlyTunerDaemon(target_ref="custom/branch")
    assert daemon3.target_ref == "custom/branch"


def test_daemon_create_pull_request_cancels_on_whitespace_diff(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify _create_pull_request cancels when git diff -w shows no semantic changes."""
    import logging

    daemon = NightlyTunerDaemon(target_ref="origin/main")

    class MockResult:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def mock_run(cmd: list[str] | str, *args: object, **kwargs: object) -> MockResult:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if "verify-patch" in cmd_str:
            return MockResult(0, "PASSED", "")
        if "git" in cmd_str and "diff" in cmd_str:
            return MockResult(0, "", "")  # exit code 0 = no diff
        return MockResult(0, "", "")

    monkeypatch.setattr("subprocess.run", mock_run)

    with caplog.at_level(logging.WARNING):
        res = daemon._create_pull_request("auto-tune/test", "body")
    assert res is None
    assert "Nhánh không có thay đổi ngữ nghĩa nào ngoài khoảng trắng. Hủy tạo PR." in caplog.text


def test_daemon_create_pull_request_real_git_whitespace(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify _create_pull_request cancels on a real git branch with only whitespace changes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True)

    file_txt = repo / "sample.txt"
    file_txt.write_text("line 1\nline 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True)

    # Create auto-tune branch with whitespace only changes
    subprocess.run(["git", "checkout", "-b", "auto-tune/test-ws"], cwd=repo, check=True)
    file_txt.write_text("line 1   \n   line 2\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "whitespace change"], cwd=repo, check=True)

    # Mock verify-patch so it passes without needing full harness dependencies in tmp repo
    original_run = subprocess.run

    def mock_run(cmd: list[str] | str, *args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if "verify-patch" in cmd_str:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PASSED", stderr="")
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr("subprocess.run", mock_run)

    daemon = NightlyTunerDaemon(root=repo, target_ref="main")
    with caplog.at_level(logging.WARNING):
        res = daemon._create_pull_request("auto-tune/test-ws", "report body")

    assert res is None
    assert "Nhánh không có thay đổi ngữ nghĩa nào ngoài khoảng trắng. Hủy tạo PR." in caplog.text


def test_daemon_create_pull_request_real_git_semantic_change(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify _create_pull_request proceeds when real git branch has semantic changes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True)

    file_txt = repo / "sample.txt"
    file_txt.write_text("line 1\nline 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True)

    # Create auto-tune branch with semantic changes
    subprocess.run(["git", "checkout", "-b", "auto-tune/test-semantic"], cwd=repo, check=True)
    file_txt.write_text("line 1\nline 2 - substantive logic enhancement\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "semantic enhancement"], cwd=repo, check=True)

    original_run = subprocess.run

    def mock_run(cmd: list[str] | str, *args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if "verify-patch" in cmd_str:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PASSED", stderr="")
        if "git" in cmd_str and "push" in cmd_str:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="pushed", stderr="")
        if "gh" in cmd_str and "pr" in cmd_str and "create" in cmd_str:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="https://github.com/vvChu/ccba-agent-platform/pull/999\n", stderr=""
            )
        # Real git diff runs natively
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr("subprocess.run", mock_run)

    daemon = NightlyTunerDaemon(root=repo, target_ref="main")
    res = daemon._create_pull_request("auto-tune/test-semantic", "report body")

    assert res == "https://github.com/vvChu/ccba-agent-platform/pull/999"
    assert "Nhánh không có thay đổi ngữ nghĩa nào ngoài khoảng trắng." not in caplog.text
