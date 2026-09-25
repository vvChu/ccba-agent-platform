"""Unit tests for CCBA Auto-Tuner Status Inspector (Dual-Mode Read-Only CLI).

Tuân thủ ADR-0023, ADR-0058 và Quy chuẩn Code Quality:
- Kiểm tra tính toàn vẹn của get_worktree_commit_stats không bị chặn trên bởi -n 8.
- Kiểm tra fallback grep ratchet(opt):.
- Kiểm tra cơ chế hiển thị và định dạng JSON cho cả Live Mode và Post-Run Mode.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.eval.check_nightly_status import (
    DaemonStatus,
    PostRunSummary,
    check_daemon_lock,
    get_process_uptime,
    get_worktree_commit_stats,
    inspect_live_daemon,
    inspect_post_run,
    is_ratchet_commit,
    main,
    render_live_status,
    render_post_run_summary,
)


def _init_git_repo(path: Path) -> None:
    """Helper khởi tạo git repo thử nghiệm."""
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test Runner"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@ccba.local"],
        check=True,
        capture_output=True,
    )


def test_get_worktree_commit_stats_nonexistent_dir(tmp_path: Path) -> None:
    """Kiểm tra khi thư mục worktree không tồn tại."""
    non_existent = tmp_path / "does_not_exist"
    count, recent = get_worktree_commit_stats(non_existent)
    assert count == 0
    assert recent == []


def test_get_worktree_commit_stats_non_git_dir(tmp_path: Path) -> None:
    """Kiểm tra khi thư mục tồn tại nhưng không phải git repo."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    count, recent = get_worktree_commit_stats(empty_dir)
    assert count == 0
    assert recent == []


def test_get_worktree_commit_stats_with_base_ref_range(tmp_path: Path) -> None:
    """Kiểm tra đếm chính xác > 8 commits so với base_ref mà không bị chặn trên bởi -n 8."""
    _init_git_repo(tmp_path)

    # 1. Commit gốc trên nhánh main
    init_file = tmp_path / "init.txt"
    init_file.write_text("initial", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "init.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    # 2. Tạo nhánh feature của nightly runner
    branch_name = "auto-tune/nightly-test"
    subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-b", branch_name],
        check=True,
        capture_output=True,
    )

    # 3. Tạo 12 commits ratchet(opt): và 1 commit khác
    for i in range(12):
        f = tmp_path / f"skill_{i}.txt"
        f.write_text(f"content {i}", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp_path), "add", str(f)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "commit",
                "-m",
                f"ratchet(opt): skill_{i}.md 70.0% -> 80.0% (+10.0%)",
            ],
            check=True,
            capture_output=True,
        )

    # Commit phụ không mang nhãn ratchet(opt):
    matrix_file = tmp_path / "matrix.txt"
    matrix_file.write_text("matrix", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "matrix.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "docs(adr): sync matrix"],
        check=True,
        capture_output=True,
    )

    # Commit phụ có chứa chuỗi ratchet(opt): nhưng KHÔNG mang prefix ratchet(opt):
    non_ratchet_file = tmp_path / "non_ratchet.txt"
    non_ratchet_file.write_text("non_ratchet", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "non_ratchet.txt"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "commit",
            "-m",
            "chore: fix bug in ratchet(opt): evaluation parser",
        ],
        check=True,
        capture_output=True,
    )

    # 4. Thực thi get_worktree_commit_stats
    total_count, recent_commits = get_worktree_commit_stats(tmp_path)

    # Bất biến: Tổng commits phải là 12 (chính xác số ratchet commits, không tính chore và không bị chặn ở 8)
    assert total_count == 12
    # Bất biến: Danh sách commits gần nhất hiển thị tối đa 8 mục
    assert len(recent_commits) == 8
    # Bất biến: Commit gần nhất nằm ở đầu danh sách
    assert "skill_11" in recent_commits[0]
    assert "skill_4" in recent_commits[-1]


def test_is_ratchet_commit_helper() -> None:
    """Kiểm tra độ chính xác của hàm nhận diện tiền tố is_ratchet_commit."""
    assert is_ratchet_commit("5943e248 ratchet(opt): SKILL.md 93.1% -> 95.0% (+1.9%)") is True
    assert is_ratchet_commit("3c97b532 ratchet(opt): test.md") is True
    # Non-prefix cases containing ratchet(opt):
    assert is_ratchet_commit("884d5f34 chore: fix ratchet(opt): bug") is False
    assert is_ratchet_commit("abcdef01 Merge pull request #316: ratchet(opt): SKILL.md") is False
    assert is_ratchet_commit("12345678 docs: note about ratchet(opt): pattern") is False
    # Malformed or edge cases
    assert is_ratchet_commit("") is False
    assert is_ratchet_commit("5943e248") is False
    assert is_ratchet_commit("5943e248   ratchet(opt): with_spaces") is True


def test_get_worktree_commit_stats_detached_head(tmp_path: Path) -> None:
    """Kiểm tra worktree ở trạng thái detached HEAD (do git worktree add --detach)."""
    _init_git_repo(tmp_path)

    init_file = tmp_path / "init.txt"
    init_file.write_text("initial", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "init.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    # Detach HEAD
    subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "--detach"],
        check=True,
        capture_output=True,
    )

    # Thêm 5 ratchet commits
    for i in range(5):
        f = tmp_path / f"det_{i}.txt"
        f.write_text(str(i), encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp_path), "add", str(f)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "commit",
                "-m",
                f"ratchet(opt): detached_{i}.md 50% -> 60%",
            ],
            check=True,
            capture_output=True,
        )

    total_count, recent_commits = get_worktree_commit_stats(tmp_path)
    assert total_count == 5
    assert len(recent_commits) == 5
    assert "detached_4" in recent_commits[0]


def test_get_worktree_commit_stats_fallback_ignores_non_prefix(tmp_path: Path) -> None:
    """Kiểm tra fallback lọc chính xác prefix ^ratchet(opt): và bỏ qua commit chứa chuỗi ở vị trí khác."""
    subprocess.run(
        ["git", "init", "-b", "isolated-branch", str(tmp_path)], check=True, capture_output=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test Runner"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@ccba.local"], check=True
    )

    # Commit có chứa chuỗi ratchet(opt): nhưng không ở prefix
    f1 = tmp_path / "chore.txt"
    f1.write_text("chore", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", str(f1)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "commit",
            "-m",
            "chore: documentation for ratchet(opt): runner",
        ],
        check=True,
        capture_output=True,
    )

    # 3 ratchet commits hợp lệ
    for i in range(3):
        f = tmp_path / f"t_{i}.txt"
        f.write_text(str(i), encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp_path), "add", str(f)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "commit",
                "-m",
                f"ratchet(opt): item_{i}.md 80% -> 90%",
            ],
            check=True,
            capture_output=True,
        )

    total_count, recent_commits = get_worktree_commit_stats(tmp_path)
    assert total_count == 3
    assert len(recent_commits) == 3
    assert all(c.split(maxsplit=1)[1].startswith("ratchet(opt):") for c in recent_commits)


def test_get_worktree_commit_stats_fallback_grep(tmp_path: Path) -> None:
    """Kiểm tra cơ chế fallback khi nhánh không có base_ref thông thường."""
    subprocess.run(
        ["git", "init", "-b", "custom-branch", str(tmp_path)], check=True, capture_output=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test Runner"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@ccba.local"], check=True
    )

    # Tạo 10 commits ratchet trên nhánh custom-branch không có main/master
    for i in range(10):
        f = tmp_path / f"test_{i}.txt"
        f.write_text(f"val {i}", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp_path), "add", str(f)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "commit",
                "-m",
                f"ratchet(opt): test_{i}.md 60% -> 70% (+10%)",
            ],
            check=True,
            capture_output=True,
        )

    total_count, recent_commits = get_worktree_commit_stats(tmp_path)
    assert total_count == 10
    assert len(recent_commits) == 8
    assert "test_9" in recent_commits[0]


def test_inspect_live_daemon_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Kiểm tra inspect_live_daemon đọc log và trích xuất đúng tổng commit từ worktree."""
    log_dir = tmp_path / ".md" / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "nightly_cron.log"
    log_file.write_text(
        "🚀 Khởi chạy Nightly Auto-Tuner Daemon: auto-tune/nightly-test\n"
        "🔍 Đã phát hiện 25 kỹ năng trong catalog\n"
        "⚡ --- Tối ưu hóa Kỹ năng: ccba-sample-skill ---\n",
        encoding="utf-8",
    )

    worktree_dir = tmp_path / ".worktrees" / "nightly-runner"
    _init_git_repo(worktree_dir)

    init_file = worktree_dir / "base.txt"
    init_file.write_text("base", encoding="utf-8")
    subprocess.run(["git", "-C", str(worktree_dir), "add", "base.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(worktree_dir), "commit", "-m", "chore: base"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(worktree_dir), "checkout", "-b", "auto-tune/run"],
        check=True,
        capture_output=True,
    )

    for i in range(15):
        f = worktree_dir / f"f_{i}.txt"
        f.write_text(str(i), encoding="utf-8")
        subprocess.run(["git", "-C", str(worktree_dir), "add", str(f)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(worktree_dir),
                "commit",
                "-m",
                f"ratchet(opt): skill_{i}.md 70% -> 80%",
            ],
            check=True,
            capture_output=True,
        )

    # Mock uptime
    monkeypatch.setattr(
        "scripts.eval.check_nightly_status.get_process_uptime",
        lambda pid: "01:23:45",
    )

    status = inspect_live_daemon(root=tmp_path, pid=99999)
    assert status.is_running is True
    assert status.pid == 99999
    assert status.uptime_str == "01:23:45"
    assert status.current_skill == "ccba-sample-skill"
    assert status.completed_skills_count == 1
    assert status.total_skills_count == 25
    assert status.commits_count == 15
    assert len(status.recent_commits) == 8


def test_render_live_status_displays_true_commits_count(capsys: pytest.CaptureFixture[str]) -> None:
    """Kiểm tra render_live_status in đúng con số commits_count thay vì len(recent_commits)."""
    status = DaemonStatus(
        is_running=True,
        pid=12345,
        uptime_str="02:30:00",
        current_skill="bigbim-governance",
        completed_skills_count=10,
        total_skills_count=50,
        recent_commits=[f"commit_{i}" for i in range(8)],
        matrix_warning=False,
        commits_count=18,
    )

    render_live_status(status)
    out = capsys.readouterr().out
    assert "🔨 Số Commits Đã Tạo Đêm Nay: 18 commits" in out
    assert "• commit_0" in out
    assert "• commit_7" in out
    assert "Traceability Matrix): Bình thường" in out


def test_render_live_status_matrix_warning(capsys: pytest.CaptureFixture[str]) -> None:
    """Kiểm tra render_live_status in cảnh báo khi matrix_warning=True."""
    status = DaemonStatus(
        is_running=True,
        pid=12345,
        uptime_str="00:05:00",
        current_skill="ccba-ai-qc",
        completed_skills_count=2,
        total_skills_count=10,
        recent_commits=[],
        matrix_warning=True,
        commits_count=0,
    )

    render_live_status(status)
    out = capsys.readouterr().out
    assert "🚨 CẢNH BÁO NGUY CƠ HỦY PULL REQUEST:" in out
    assert "TRACEABILITY_MATRIX.md trong worktree bị LỆCH ĐỒNG BỘ!" in out


def test_inspect_post_run_and_render(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Kiểm tra inspect_post_run đọc chính xác báo cáo đã lưu trữ và render."""
    rep_dir = tmp_path / ".md" / "knowledge" / "reports"
    rep_dir.mkdir(parents=True)
    report_file = rep_dir / "nightly_tuner_report_20260925_020000.md"
    report_file.write_text(
        "# Báo cáo Tiến hóa Đêm\n\n"
        "> **Nhánh Git:** `auto-tune/nightly-20260925`  \n"
        "> **Tổng kỹ năng quét:** `73` | **Kỹ năng cải thiện:** `4` | **Số Commits:** `6`  \n"
        "> **Tổng Token Tiêu Thụ:** `125,000`  \n\n"
        "| Kỹ Năng | Baseline | Final | Delta | Commits | Token Tiêu Thụ | Trạng Thái |\n"
        "|---|---|---|---|---|---|---|\n"
        "| `ccba-ai-qc` | 65.0% | **85.0%** | `+20.0%` | 2 | `25,000` | 🟢 IMPROVED |\n"
        "| `bigbim-rase` | 70.0% | **90.0%** | `+20.0%` | 4 | `35,000` | 🟢 IMPROVED |\n",
        encoding="utf-8",
    )

    summary = inspect_post_run(tmp_path)
    assert summary is not None
    assert isinstance(summary, PostRunSummary)
    assert summary.git_branch == "auto-tune/nightly-20260925"
    assert summary.total_scanned == 73
    assert summary.improved_count == 4
    assert summary.commit_count == 6
    assert summary.total_tokens == "125,000"
    assert len(summary.top_improvements) == 2
    assert summary.top_improvements[0][0] == "ccba-ai-qc"

    render_post_run_summary(summary)
    out = capsys.readouterr().out
    assert "ccba-ai-qc`: 65.0% ➔ **85.0%** (+20.0%)" in out
    assert "73 Kỹ Năng Cải Thiện | 6 Commits" in out


def test_get_process_uptime_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kiểm tra hàm get_process_uptime."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args, returncode=0, stdout="02:15:30\n"
        ),
    )
    assert get_process_uptime(1234) == "02:15:30"


def test_check_daemon_lock_nonexistent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Kiểm tra probe lock khi file lock không tồn tại và không có process daemon."""
    monkeypatch.setattr("scripts.eval.check_nightly_status.find_daemon_pid", lambda: None)
    is_running, pid = check_daemon_lock(tmp_path / "nonexistent.lock")
    assert is_running is False
    assert pid is None


def test_main_cli_json_live_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kiểm tra cờ --json trong Live Mode xuất đúng schema và commits_count."""
    monkeypatch.setattr(
        "scripts.eval.check_nightly_status.get_repo_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "scripts.eval.check_nightly_status.check_daemon_lock",
        lambda: (True, 55555),
    )
    mock_status = DaemonStatus(
        is_running=True,
        pid=55555,
        uptime_str="01:10:00",
        current_skill="ccba-legal-advisor",
        completed_skills_count=5,
        total_skills_count=20,
        recent_commits=["c1", "c2", "c3"],
        matrix_warning=False,
        commits_count=14,
    )
    monkeypatch.setattr(
        "scripts.eval.check_nightly_status.inspect_live_daemon",
        lambda root, pid: mock_status,
    )
    monkeypatch.setattr(sys, "argv", ["check_nightly_status.py", "--json"])

    code = main()
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "live"
    assert payload["is_running"] is True
    assert payload["commits_count"] == 14
    assert payload["current_skill"] == "ccba-legal-advisor"
