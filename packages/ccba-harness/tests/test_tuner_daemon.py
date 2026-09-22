"""test_tuner_daemon.py - Unit tests for ccba_harness.evals.daemon Deep Seam."""

from __future__ import annotations

import datetime
import json
import logging
import subprocess
import urllib.error
from pathlib import Path
from typing import Any

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


def test_daemon_send_telegram_notification_chatops_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify send_telegram_notification dispatches to ChatOps Gateway when secret and stagnant skills exist."""
    monkeypatch.setenv("CHATOPS_INTERNAL_SECRET", "test_chatops_secret_123")
    monkeypatch.setenv("CHATOPS_GATEWAY_URL", "http://127.0.0.1:8095")

    captured_requests: list[dict[str, Any]] = []

    class MockHTTPResponse:
        def __init__(self, status: int = 200) -> None:
            self.status = status

        def __enter__(self) -> MockHTTPResponse:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

    def mock_urlopen(req: Any, timeout: float = 5.0) -> MockHTTPResponse:
        captured_requests.append(
            {
                "url": req.full_url,
                "headers": dict(req.headers),
                "data": json.loads(req.data.decode("utf-8")),
                "timeout": timeout,
            }
        )
        return MockHTTPResponse(200)

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    daemon = NightlyTunerDaemon()
    report = NightlyDaemonReport(
        timestamp="20260922_150000",
        branch_name="auto-tune/test",
        total_skills_scanned=2,
        skills_optimized=0,
        total_commits=0,
        results=[
            SkillEvolutionSummary(
                skill_name="stagnant-skill",
                target_file=Path("SKILL.md"),
                baseline_score=60.0,
                final_score=60.0,
                commits_kept=0,
                rollbacks=1,
                status="PLATEAU",
            ),
            SkillEvolutionSummary(
                skill_name="passing-skill",
                target_file=Path("SKILL.md"),
                baseline_score=95.0,
                final_score=95.0,
                commits_kept=0,
                rollbacks=0,
                status="UNCHANGED",
            ),
        ],
    )

    result = daemon.send_telegram_notification(report)
    assert result is True
    assert len(captured_requests) == 1
    req_info = captured_requests[0]
    assert req_info["url"] == "http://127.0.0.1:8095/api/v1/notify"
    headers_lower = {k.lower(): v for k, v in req_info["headers"].items()}
    assert headers_lower.get("x-chatops-secret") == "test_chatops_secret_123"

    payload = req_info["data"]
    assert payload["title"] == "CCBA NIGHTLY AUTO-TUNER REPORT"
    assert payload["severity"] == "WARNING"
    assert len(payload["actions"]) == 1
    action = payload["actions"][0]
    assert action["action_id"] == "boost_stagnant-skill"
    assert action["command"] == "ccba.skill.boost"
    assert action["params"] == {"skill": "stagnant-skill"}
    assert action["ttl_seconds"] == 86400
    assert action["timeout"] == 600


def test_daemon_send_telegram_notification_chatops_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify fallback to direct send_telegram_alert when ChatOps Gateway fails or is unreachable."""
    monkeypatch.setenv("CHATOPS_INTERNAL_SECRET", "test_chatops_secret_123")
    monkeypatch.setenv("CHATOPS_GATEWAY_URL", "http://127.0.0.1:8095")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    # 1. Network exception on urlopen
    def mock_urlopen_err(req: Any, timeout: float = 5.0) -> Any:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_err)

    daemon = NightlyTunerDaemon()
    report = NightlyDaemonReport(
        timestamp="20260922_150000",
        branch_name="auto-tune/test",
        total_skills_scanned=1,
        skills_optimized=0,
        total_commits=0,
        results=[
            SkillEvolutionSummary(
                skill_name="stagnant-skill",
                target_file=Path("SKILL.md"),
                baseline_score=50.0,
                final_score=50.0,
                commits_kept=0,
                rollbacks=2,
                status="PLATEAU",
            )
        ],
    )

    # When ChatOps throws, fallback sends mock telegram alert successfully
    res1 = daemon.send_telegram_notification(report)
    assert res1 is True

    # 2. When Gateway returns HTTP 500
    class Mock500Response:
        def __init__(self) -> None:
            self.status = 500

        def __enter__(self) -> Mock500Response:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=5.0: Mock500Response())
    res2 = daemon.send_telegram_notification(report)
    assert res2 is True


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

    def mock_run(
        cmd: list[str] | str, *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if any(
            k in cmd_str for k in ("verify-patch", "validate_docs", "test_audit_skills_hygiene")
        ):
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

    def mock_run(
        cmd: list[str] | str, *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if any(
            k in cmd_str for k in ("verify-patch", "validate_docs", "test_audit_skills_hygiene")
        ):
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PASSED", stderr="")
        if "git" in cmd_str and "push" in cmd_str:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="pushed", stderr="")
        if "gh" in cmd_str and "pr" in cmd_str and "create" in cmd_str:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="https://github.com/vvChu/ccba-agent-platform/pull/999\n",
                stderr="",
            )
        # Real git diff runs natively
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr("subprocess.run", mock_run)

    daemon = NightlyTunerDaemon(root=repo, target_ref="main")
    res = daemon._create_pull_request("auto-tune/test-semantic", "report body")

    assert res == "https://github.com/vvChu/ccba-agent-platform/pull/999"
    assert "Nhánh không có thay đổi ngữ nghĩa nào ngoài khoảng trắng." not in caplog.text


def test_weighted_priority_queue_cooldown() -> None:
    """Verify that in_cooldown skills are placed in tier after non-cooldown skills."""
    skills = [
        {"skill_name": "s_weak_cooldown", "baseline_score": 50.0, "in_cooldown": True},
        {"skill_name": "s_weak_active", "baseline_score": 60.0, "in_cooldown": False},
        {"skill_name": "s_mid_active", "baseline_score": 95.0, "in_cooldown": False},
        {"skill_name": "s_perfect_active", "baseline_score": 100.0, "in_cooldown": False},
        {"skill_name": "s_mid_cooldown", "baseline_score": 92.0, "in_cooldown": True},
    ]
    ranked = WeightedPriorityQueue.rank_skills(skills)
    names = [s["skill_name"] for s in ranked]
    # Non-cooldown skills come first: s_weak_active (tier 0), s_mid_active (tier 1), s_perfect_active (tier 2).
    # Then cooldown skills: s_weak_cooldown (tier 0), s_mid_cooldown (tier 1).
    assert names == [
        "s_weak_active",
        "s_mid_active",
        "s_perfect_active",
        "s_weak_cooldown",
        "s_mid_cooldown",
    ]


def test_load_historical_metrics_cooldown_and_real_llm_filter(tmp_path: Path) -> None:
    """Verify _load_historical_metrics parses scores and filters cooldown based on REAL_LLM and date."""
    reports_dir = tmp_path / ".md" / "knowledge" / "reports"
    reports_dir.mkdir(parents=True)

    today = datetime.date.today()
    today_str = today.strftime("%Y%m%d")
    yesterday_str = (today - datetime.timedelta(days=1)).strftime("%Y%m%d")
    five_days_ago_str = (today - datetime.timedelta(days=5)).strftime("%Y%m%d")

    # 1. Report from today with REAL_LLM engine
    rep1 = reports_dir / f"nightly_tuner_report_{today_str}_010000.md"
    rep1.write_text(
        f"""# 🌙 CCBA Nightly Auto-Tuner Evolution Report
> **Thời gian thực thi:** `{today_str}_010000` | **Engine:** `REAL_LLM`
### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)
| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `skill_stuck` | 75.0% | **75.0%** | `0.0%` | 0 | `250,000` | ⚪ UNCHANGED |
| `skill_halted` | 80.0% | **80.0%** | `0.0%` | 0 | `250,000` | ⚠️ HALT_PER_SKILL_TOKEN_BUDGET_EXCEEDED |
| `skill_improved` | 70.0% | **95.0%** | `+25.0%` | 2 | `100,000` | 🟢 IMPROVED |
""",
        encoding="utf-8",
    )

    # 2. Report from yesterday with MOCK engine
    rep2 = reports_dir / f"nightly_tuner_report_{yesterday_str}_020000.md"
    rep2.write_text(
        f"""# 🌙 CCBA Nightly Auto-Tuner Evolution Report
> **Thời gian thực thi:** `{yesterday_str}_020000` | **Engine:** `MOCK`
### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)
| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `skill_mock` | 60.0% | **60.0%** | `0.0%` | 0 | `-` | ⚪ UNCHANGED |
""",
        encoding="utf-8",
    )

    # 3. Report from 5 days ago (older than 3-day cutoff) with REAL_LLM engine
    rep3 = reports_dir / f"nightly_tuner_report_{five_days_ago_str}_030000.md"
    rep3.write_text(
        f"""# 🌙 CCBA Nightly Auto-Tuner Evolution Report
> **Thời gian thực thi:** `{five_days_ago_str}_030000` | **Engine:** `REAL_LLM`
### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)
| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `skill_old` | 55.0% | **55.0%** | `0.0%` | 0 | `250,000` | ⚪ UNCHANGED |
""",
        encoding="utf-8",
    )

    daemon = NightlyTunerDaemon(root=tmp_path)
    scores, cooldown_skills = daemon._load_historical_metrics(cooldown_days=3)

    # Scores loaded across all reports
    assert scores.get("skill_stuck") == 75.0
    assert scores.get("skill_halted") == 80.0
    assert scores.get("skill_improved") == 95.0
    assert scores.get("skill_mock") == 60.0
    assert scores.get("skill_old") == 55.0

    # Cooldown filtered strictly by: REAL_LLM, within 3 days, commits == 0, and score < 90 or UNCHANGED/HALT_
    assert "skill_stuck" in cooldown_skills
    assert "skill_halted" in cooldown_skills
    assert "skill_improved" not in cooldown_skills  # commits > 0
    assert "skill_mock" not in cooldown_skills  # MOCK engine
    assert "skill_old" not in cooldown_skills  # Older than 3 days


def test_remove_stale_plateau_brief(tmp_path: Path) -> None:
    """Verify stale plateau briefs are deleted when skill improves or crosses 90.0% threshold."""
    escalations_dir = tmp_path / ".md" / "knowledge" / "escalations"
    escalations_dir.mkdir(parents=True)
    brief_file = escalations_dir / "test_skill_plateau.md"
    brief_file.write_text("# Old Plateau Brief", encoding="utf-8")
    assert brief_file.exists()

    daemon = NightlyTunerDaemon(root=tmp_path)
    removed = daemon._remove_stale_plateau_brief("test_skill")
    assert removed is True
    assert not brief_file.exists()

    # Calling again on nonexistent file returns False without raising error
    assert daemon._remove_stale_plateau_brief("test_skill") is False


def test_resolve_dataset_file_completion_checklist() -> None:
    """Verify ccba-completion-checklist maps to eval_legal_intel.json."""
    daemon = NightlyTunerDaemon()
    ds = daemon._resolve_dataset_file("ccba-completion-checklist")
    assert ds == "eval_legal_intel.json"


def test_weighted_priority_queue_safe_with_none_score() -> None:
    """Verify WeightedPriorityQueue safely handles skills with baseline_score=None."""
    skills = [
        {"skill_name": "s_none", "baseline_score": None, "in_cooldown": False},
        {"skill_name": "s_active", "baseline_score": 70.0, "in_cooldown": False},
    ]
    ranked = WeightedPriorityQueue.rank_skills(skills)
    # s_none has score 0.0 (tier 0), so it ranks before 70.0
    assert ranked[0]["skill_name"] == "s_none"
    assert ranked[1]["skill_name"] == "s_active"


def test_load_historical_metrics_unbolded_scores_and_date_sort(tmp_path: Path) -> None:
    """Verify _load_historical_metrics handles plain unbolded scores and sorts by actual date."""
    reports_dir = tmp_path / ".md" / "knowledge" / "reports"
    reports_dir.mkdir(parents=True)

    # Older report (2026-09-20) with no hyphens
    rep_older = reports_dir / "nightly_tuner_report_20260920_010000.md"
    rep_older.write_text(
        """# 🌙 CCBA Nightly Auto-Tuner Evolution Report
> **Thời gian thực thi:** `20260920_010000` | **Engine:** `REAL_LLM`
### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)
| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `skill_mixed` | 60.0% | **60.0%** | `0.0%` | 0 | `100,000` | ⚪ UNCHANGED |
""",
        encoding="utf-8",
    )

    # Newer report (2026-09-21) with hyphens in date AND unbolded final score AND backticks on commits
    rep_newer = reports_dir / "nightly_tuner_report_2026-09-21_010000.md"
    rep_newer.write_text(
        """# 🌙 CCBA Nightly Auto-Tuner Evolution Report
> **Thời gian thực thi:** `2026-09-21_010000` | **Engine:** `REAL_LLM`
### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)
| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `skill_mixed` | 85.0% | 85.0% | `0.0%` | `0` | `-` | ⚪ UNCHANGED |
""",
        encoding="utf-8",
    )

    daemon = NightlyTunerDaemon(root=tmp_path)
    scores, cooldown_skills = daemon._load_historical_metrics(cooldown_days=3)

    # The newer report (85.0%) should win over the older report (60.0%)
    assert scores.get("skill_mixed") == 85.0
    assert "skill_mixed" in cooldown_skills


def test_remove_stale_plateau_brief_worktree(tmp_path: Path) -> None:
    """Verify _remove_stale_plateau_brief removes brief from main repo root when executed in a worktree."""
    main_repo = tmp_path / "main_repo"
    worktree = tmp_path / "worktree"

    main_escalations = main_repo / ".md" / "knowledge" / "escalations"
    main_escalations.mkdir(parents=True)
    main_brief = main_escalations / "test_wt_skill_plateau.md"
    main_brief.write_text("# Main Brief", encoding="utf-8")

    wt_escalations = worktree / ".md" / "knowledge" / "escalations"
    wt_escalations.mkdir(parents=True)
    wt_brief = wt_escalations / "test_wt_skill_plateau.md"
    wt_brief.write_text("# WT Brief", encoding="utf-8")

    # Simulate worktree .git file structure:
    # main_repo/.git/worktrees/nightly-runner
    gitdir = main_repo / ".git" / "worktrees" / "nightly-runner"
    gitdir.mkdir(parents=True)
    wt_git = worktree / ".git"
    wt_git.write_text(f"gitdir: {gitdir}\n", encoding="utf-8")

    daemon = NightlyTunerDaemon(root=worktree)
    assert daemon._get_main_repo_root() == main_repo

    removed = daemon._remove_stale_plateau_brief("test_wt_skill")
    assert removed is True
    assert not wt_brief.exists()
    assert not main_brief.exists()


def test_cleanup_empty_branch_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _cleanup_empty_branch detaches and deletes branch without checking out target_ref in worktree."""
    daemon = NightlyTunerDaemon(root=tmp_path, target_ref="main")
    monkeypatch.setattr(daemon, "_get_main_repo_root", lambda: Path("/fake/main/repo"))

    executed_cmds: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        executed_cmds.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", mock_run)

    daemon._cleanup_empty_branch("auto-tune/test-branch")

    assert ["git", "checkout", "--detach"] in executed_cmds
    assert ["git", "branch", "-D", "auto-tune/test-branch"] in executed_cmds
    assert ["git", "checkout", "main"] not in executed_cmds


def test_cleanup_empty_branch_main_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _cleanup_empty_branch detaches, deletes branch, and checks out target_ref on main repo."""
    daemon = NightlyTunerDaemon(root=tmp_path, target_ref="main")
    monkeypatch.setattr(daemon, "_get_main_repo_root", lambda: None)

    executed_cmds: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        executed_cmds.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", mock_run)

    daemon._cleanup_empty_branch("auto-tune/test-branch")

    assert ["git", "checkout", "--detach"] in executed_cmds
    assert ["git", "branch", "-D", "auto-tune/test-branch"] in executed_cmds
    assert ["git", "checkout", "main"] in executed_cmds


def test_daemon_no_telegram_flag_skips_notification(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify no_telegram=True suppresses telegram notification in run_nightly_batch."""
    daemon = NightlyTunerDaemon(root=tmp_path, no_telegram=True)

    telegram_called = False

    def mock_send(report):
        nonlocal telegram_called
        telegram_called = True
        return True

    monkeypatch.setattr(daemon, "send_telegram_notification", mock_send)
    monkeypatch.setattr(daemon, "discover_skills_and_datasets", lambda: [])

    report = daemon.run_nightly_batch(dry_run=True)
    assert not telegram_called
    assert report.telegram_notified is False


def test_daemon_run_nightly_batch_cleans_empty_branch_when_total_commits_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify run_nightly_batch cleans up empty branch when not dry_run and total_commits == 0."""
    daemon = NightlyTunerDaemon(root=tmp_path, no_telegram=True)

    cleaned_branches: list[str] = []
    monkeypatch.setattr(daemon, "_cleanup_old_empty_branches", lambda days: 0)
    monkeypatch.setattr(daemon, "_create_git_branch", lambda b: None)
    monkeypatch.setattr(daemon, "discover_skills_and_datasets", lambda: [])
    monkeypatch.setattr(daemon, "_cleanup_empty_branch", lambda b: cleaned_branches.append(b))

    report = daemon.run_nightly_batch(dry_run=False)
    assert report.total_commits == 0
    assert len(cleaned_branches) == 1
    assert cleaned_branches[0] == report.branch_name

