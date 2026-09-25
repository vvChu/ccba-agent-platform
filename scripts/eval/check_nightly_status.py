#!/usr/bin/env python3
"""CCBA Auto-Tuner Status Inspector (Dual-Mode Read-Only CLI).

Công cụ kiểm toán và giám sát trạng thái Auto-Tuner ban đêm (ADR-0023, ADR-0058).
Hỗ trợ cơ chế Dual-Mode Inspection:
1. Live Mode: Kiểm tra an toàn tiến trình daemon đang chạy, tail log và git worktree.
2. Post-Run Mode: Tự động fallback đọc báo cáo tiến hóa mới nhất khi worktree đã dọn dẹp.

Bất biến an toàn (Process & Git Safety Invariants):
- Tuyệt đối không kill tiến trình hoặc acquire write lock trên /tmp/ccba_nightly_runner.lock.
- Mọi truy vấn Git sử dụng cờ --no-optional-locks để không gây xung đột index.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple


class DaemonStatus(NamedTuple):
    """Thông tin trạng thái tiến trình Daemon."""

    is_running: bool
    pid: int | None
    uptime_str: str | None
    current_skill: str | None
    completed_skills_count: int
    total_skills_count: int
    recent_commits: list[str]
    matrix_warning: bool
    commits_count: int = 0


class PostRunSummary(NamedTuple):
    """Tóm tắt kết quả đợt chạy đã lưu trữ."""

    report_path: Path
    timestamp: str
    git_branch: str
    total_scanned: int
    improved_count: int
    commit_count: int
    total_tokens: str
    top_improvements: list[tuple[str, str, str, str]]


def get_repo_root() -> Path:
    """Xác định thư mục gốc của kho chứa Hub Monorepo.

    Returns:
        Path: Đường dẫn thư mục gốc.
    """
    return Path(__file__).resolve().parent.parent.parent


def find_daemon_pid() -> int | None:
    """Tìm PID của tiến trình nightly_tuner_daemon đang chạy.

    Returns:
        int | None: PID nếu tìm thấy.
    """
    try:
        res = subprocess.run(
            ["pgrep", "-f", "nightly_tuner_daemon.py"],
            capture_output=True,
            text=True,
            check=False,
        )
        pids = [int(p.strip()) for p in res.stdout.splitlines() if p.strip().isdigit()]
        if pids:
            return pids[0]
    except (subprocess.SubprocessError, ValueError):
        pass
    return None


def is_pid_alive(pid: int) -> bool:
    """Kiểm tra xem PID có thực sự đang chạy trên hệ điều hành không.

    Args:
        pid: Mã định danh tiến trình.

    Returns:
        bool: True nếu tiến trình đang tồn tại.
    """
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def check_daemon_lock(
    lock_file: Path = Path("/tmp/ccba_nightly_runner.lock"),
) -> tuple[bool, int | None]:
    """Kiểm tra lock không xâm lấn (Non-blocking probe).

    Tuyệt đối không acquire write-lock lâu dài để tránh kill hoặc chặn daemon.

    Args:
        lock_file: Đường dẫn file lock độc quyền của cron.

    Returns:
        tuple[bool, int | None]: (True nếu đang chạy, PID tương ứng).
    """
    pid = find_daemon_pid()

    if not lock_file.exists():
        return (True, pid) if (pid and is_pid_alive(pid)) else (False, None)

    try:
        with open(lock_file) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            if pid and is_pid_alive(pid):
                return True, pid
            return False, None
    except (BlockingIOError, OSError) as e:
        if isinstance(e, BlockingIOError) or e.errno in (
            errno.EAGAIN,
            errno.EACCES,
        ):
            # Lock đang bị nắm giữ bởi daemon
            return True, pid
        return False, pid


def get_process_uptime(pid: int) -> str:
    """Lấy thời gian chạy (uptime) của tiến trình từ ps.

    Args:
        pid: Mã định danh tiến trình.

    Returns:
        str: Chuỗi biểu diễn thời gian chạy.
    """
    try:
        res = subprocess.run(
            ["ps", "-p", str(pid), "-o", "etime="],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.SubprocessError:
        return "N/A"


def is_ratchet_commit(line: str) -> bool:
    """Kiểm tra xem commit có mang tiền tố ratchet(opt): chuẩn hay không.

    Định dạng git log --oneline: '<hash> <subject>'.
    Hàm đảm bảo subject phải bắt đầu bằng 'ratchet(opt):' để tránh nhận nhầm
    các commit bảo trì hoặc tài liệu chỉ đề cập chuỗi này trong commit message.

    Args:
        line: Dòng oneline của git log.

    Returns:
        bool: True nếu là commit ratchet của Auto-Tuner.
    """
    parts = line.strip().split(maxsplit=1)
    return len(parts) >= 2 and parts[1].startswith("ratchet(opt):")


def get_worktree_commit_stats(worktree_dir: Path) -> tuple[int, list[str]]:
    """Đếm chính xác tổng số commits đã tạo trên worktree và trích xuất commits gần nhất.

    Cơ chế đếm tuân thủ ADR-0023, ADR-0058:
    1. Xác định base_ref khả dụng (@{upstream} -> origin/main -> origin/master -> main -> master).
    2. So sánh phạm vi {base_ref}..HEAD để không bị chặn trên bởi giới hạn git log -n.
    3. Ưu tiên lọc đếm các commits mang nhãn ratchet(opt): của Auto-Tuner theo đúng prefix.
    4. Fallback an toàn nếu không xác định được base_ref với anchored grep ^ratchet(opt):.

    Args:
        worktree_dir: Đường dẫn tới thư mục git worktree.

    Returns:
        tuple[int, list[str]]: (commits_count, recent_commits tối đa 8 mục).
    """
    if not worktree_dir.exists():
        return 0, []

    current_branch = ""
    try:
        branch_res = subprocess.run(
            [
                "git",
                "-C",
                str(worktree_dir),
                "--no-optional-locks",
                "rev-parse",
                "--abbrev-ref",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if branch_res.returncode == 0:
            current_branch = branch_res.stdout.strip()
    except OSError:
        pass

    # 1. Tìm base_ref khả dụng (@{upstream} -> origin/main -> origin/master -> main -> master)
    for candidate in ("@{upstream}", "origin/main", "origin/master", "main", "master"):
        if candidate == current_branch:
            continue
        try:
            check = subprocess.run(
                [
                    "git",
                    "-C",
                    str(worktree_dir),
                    "--no-optional-locks",
                    "rev-parse",
                    "--verify",
                    candidate,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if check.returncode != 0:
                continue

            # Truy vấn danh sách commits trong phạm vi {candidate}..HEAD
            log_res = subprocess.run(
                [
                    "git",
                    "-C",
                    str(worktree_dir),
                    "--no-optional-locks",
                    "log",
                    "--oneline",
                    f"{candidate}..HEAD",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if log_res.returncode == 0:
                all_lines = [line.strip() for line in log_res.stdout.splitlines() if line.strip()]
                ratchet_lines = [line for line in all_lines if is_ratchet_commit(line)]

                if ratchet_lines:
                    return len(ratchet_lines), ratchet_lines[:8]
                if all_lines:
                    return len(all_lines), all_lines[:8]
                return 0, []
        except OSError:
            pass

    # 2. Fallback: Nếu không xác định được base_ref hoặc range lỗi, lọc trực tiếp theo grep ^ratchet(opt):
    try:
        fallback_res = subprocess.run(
            [
                "git",
                "-C",
                str(worktree_dir),
                "--no-optional-locks",
                "log",
                "--oneline",
                "--grep=^ratchet(opt):",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if fallback_res.returncode == 0:
            ratchet_lines = [
                line.strip() for line in fallback_res.stdout.splitlines() if is_ratchet_commit(line)
            ]
            return len(ratchet_lines), ratchet_lines[:8]
    except OSError:
        pass

    return 0, []


def inspect_live_daemon(root: Path, pid: int | None) -> DaemonStatus:
    """Quét và phân tích trạng thái của Daemon đang chạy trực tiếp.

    Args:
        root: Thư mục gốc của Monorepo.
        pid: Mã PID của daemon nếu tìm thấy.

    Returns:
        DaemonStatus: Cấu trúc thông tin live của daemon.
    """
    uptime_str = get_process_uptime(pid) if pid else "N/A"
    log_file = root / ".md" / "logs" / "nightly_cron.log"
    current_skill = None
    completed_skills_count = 0
    total_skills_count = 73

    if log_file.exists():
        try:
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            # Cắt lấy phân đoạn của phiên chạy gần nhất
            start_marker = "🚀 Khởi chạy Nightly Auto-Tuner Daemon:"
            last_start_idx = content.rfind(start_marker)
            session_log = content[last_start_idx:] if last_start_idx != -1 else content[-50000:]

            # Tìm tổng số kỹ năng được phát hiện trong phiên này
            m_total = re.search(r"🔍 Đã phát hiện (\d+) kỹ năng trong catalog", session_log)
            if m_total:
                total_skills_count = int(m_total.group(1))

            # Tìm danh sách kỹ năng đã được xử lý trong phiên này
            skills_found = re.findall(r"⚡ --- Tối ưu hóa Kỹ năng:\s+([\w-]+)\s+---", session_log)
            completed_skills_count = len(skills_found)
            if skills_found:
                current_skill = skills_found[-1]
        except OSError:
            pass

    # Quét git worktree
    worktree_dir = root / ".worktrees" / "nightly-runner"
    commits_count, recent_commits = get_worktree_commit_stats(worktree_dir)
    matrix_warning = False

    if worktree_dir.exists():
        try:
            # Kiểm tra nhanh tính toàn vẹn của TRACEABILITY_MATRIX.md
            check_matrix = subprocess.run(
                [
                    sys.executable,
                    "scripts/sync_hub_adr_matrix.py",
                    "--check",
                ],
                cwd=str(worktree_dir),
                capture_output=True,
                text=True,
                check=False,
            )
            if check_matrix.returncode != 0:
                matrix_warning = True
        except OSError:
            pass

    return DaemonStatus(
        is_running=True,
        pid=pid,
        uptime_str=uptime_str,
        current_skill=current_skill or "Đang khởi tạo / Hoàn tất",
        completed_skills_count=completed_skills_count,
        total_skills_count=total_skills_count,
        recent_commits=recent_commits,
        matrix_warning=matrix_warning,
        commits_count=commits_count,
    )


def inspect_post_run(root: Path) -> PostRunSummary | None:
    """Quét và phân tích báo cáo tiến hóa mới nhất trong thư mục tri thức.

    Args:
        root: Thư mục gốc của Monorepo.

    Returns:
        PostRunSummary | None: Tóm tắt báo cáo lưu trữ hoặc None nếu không tìm thấy.
    """
    reports_dir = root / ".md" / "knowledge" / "reports"
    if not reports_dir.exists():
        return None

    reports = sorted(
        reports_dir.glob("nightly_tuner_report_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not reports:
        return None

    latest_report = reports[0]
    content = latest_report.read_text(encoding="utf-8")

    timestamp = latest_report.stem.replace("nightly_tuner_report_", "")
    m_branch = re.search(r"\*\*Nhánh Git:\*\*\s+`([^`]+)`", content)
    git_branch = m_branch.group(1) if m_branch else "unknown"

    m_scanned = re.search(r"\*\*Tổng kỹ năng quét:\*\*\s+`(\d+)`", content)
    total_scanned = int(m_scanned.group(1)) if m_scanned else 0

    m_improved = re.search(r"\*\*Kỹ năng cải thiện:\*\*\s+`(\d+)`", content)
    improved_count = int(m_improved.group(1)) if m_improved else 0

    m_commits = re.search(r"\*\*Số Commits:\*\*\s+`(\d+)`", content)
    commit_count = int(m_commits.group(1)) if m_commits else 0

    m_tokens = re.search(r"\*\*Tổng Token Tiêu Thụ:\*\*\s+`([^`]+)`", content)
    total_tokens = m_tokens.group(1) if m_tokens else "N/A"

    top_improvements: list[tuple[str, str, str, str]] = []
    table_matches = re.findall(
        r"\|\s*`([^`]+)`\s*\|\s*([^\|]+)\|\s*([^\|]+)\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`?([^\|`]+)`?\s*\|\s*🟢 IMPROVED",
        content,
    )
    for match in table_matches:
        top_improvements.append(
            (match[0].strip(), match[1].strip(), match[2].strip(), match[3].strip())
        )

    return PostRunSummary(
        report_path=latest_report,
        timestamp=timestamp,
        git_branch=git_branch,
        total_scanned=total_scanned,
        improved_count=improved_count,
        commit_count=commit_count,
        total_tokens=total_tokens,
        top_improvements=top_improvements,
    )


def render_live_status(status: DaemonStatus) -> None:
    """In định dạng trực quan cho trạng thái Live Daemon."""
    pct = (
        (status.completed_skills_count / status.total_skills_count * 100)
        if status.total_skills_count > 0
        else 0
    )

    print("\n" + "=" * 70)
    print("🌙 CCBA AUTO-TUNER NIGHTLY STATUS INSPECTOR (LIVE MODE)")
    print("=" * 70)
    print(f"🟢 Trạng Thái Daemon: ĐANG CHẠY (PID: {status.pid})")
    print(f"⏱️  Thời Gian Chạy Liên Tục (Uptime): {status.uptime_str}")
    print(
        f"🎯 Kỹ Năng Đang Xử Lý: {status.current_skill} "
        f"({status.completed_skills_count}/{status.total_skills_count} ~ {pct:.1f}%)"
    )
    commits_num = status.commits_count if status.commits_count > 0 else len(status.recent_commits)
    print(f"🔨 Số Commits Đã Tạo Đêm Nay: {commits_num} commits")
    print("-" * 70)

    if status.recent_commits:
        print("📈 DANH SÁCH COMMITS CẢI TIẾN GẦN NHẤT:")
        for commit in status.recent_commits:
            print(f"   • {commit}")
        print("-" * 70)

    if status.matrix_warning:
        print("🚨 CẢNH BÁO NGUY CƠ HỦY PULL REQUEST:")
        print("   Tệp docs/adr/TRACEABILITY_MATRIX.md trong worktree bị LỆCH ĐỒNG BỘ!")
        print("   Nếu không đồng bộ trước khi daemon kết thúc, verify-patch sẽ FAIL")
        print("   và daemon sẽ tự động hủy tạo PR, sau đó xóa sạch worktree.")
        print("   👉 Khắc phục: Chạy 'python scripts/sync_hub_adr_matrix.py' trong worktree.")
        print("-" * 70)
    else:
        print("✅ Kiểm tra ma trận truy vết (Traceability Matrix): Bình thường")
        print("-" * 70)


def render_post_run_summary(summary: PostRunSummary) -> None:
    """In định dạng trực quan cho kết quả đã lưu trữ (Post-Run Mode)."""
    print("\n" + "=" * 70)
    print("🌙 CCBA AUTO-TUNER REPORT INSPECTOR (POST-RUN ARCHIVE MODE)")
    print("=" * 70)
    print(f"📁 Tệp Báo Cáo: {summary.report_path.name}")
    print(f"📅 Phiên Thực Thi: {summary.timestamp}")
    print(f"🌿 Nhánh Git: {summary.git_branch}")
    print(
        f"📊 Thống Kê: {summary.improved_count}/{summary.total_scanned} Kỹ Năng Cải Thiện "
        f"| {summary.commit_count} Commits | {summary.total_tokens} Tokens"
    )
    print("-" * 70)

    if summary.top_improvements:
        print("🏆 CÁC KỸ NĂNG CẢI THIỆN ĐIỂM SỐ NỔI BẬT:")
        for skill, init_score, final_score, delta in summary.top_improvements:
            print(f"   • `{skill}`: {init_score} ➔ {final_score} ({delta})")
        print("-" * 70)
    else:
        print("ℹ️  Không có kỹ năng nào cải thiện trong phiên này.")
        print("-" * 70)


def main() -> int:
    """Hàm điều phối chính của công cụ kiểm toán."""
    parser = argparse.ArgumentParser(
        description="Kiểm tra trạng thái hoạt động của CCBA Auto-Tuner (Dual-Mode Read-Only CLI)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Xuất kết quả ở định dạng JSON để tích hợp CI/CD.",
    )
    args = parser.parse_args()

    root = get_repo_root()
    is_running, pid = check_daemon_lock()

    if is_running:
        status = inspect_live_daemon(root, pid)
        if args.json:
            import json

            data: dict[str, Any] = {
                "mode": "live",
                "is_running": True,
                "pid": status.pid,
                "uptime": status.uptime_str,
                "current_skill": status.current_skill,
                "completed": status.completed_skills_count,
                "total": status.total_skills_count,
                "commits_count": (
                    status.commits_count if status.commits_count > 0 else len(status.recent_commits)
                ),
                "matrix_warning": status.matrix_warning,
            }
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            render_live_status(status)
        return 0

    # Chế độ Post-Run
    summary = inspect_post_run(root)
    if summary is None:
        print("❌ Không tìm thấy daemon đang chạy và cũng không có báo cáo lưu trữ.")
        return 1

    if args.json:
        import json

        data_post: dict[str, Any] = {
            "mode": "post_run",
            "is_running": False,
            "report_file": summary.report_path.name,
            "timestamp": summary.timestamp,
            "git_branch": summary.git_branch,
            "total_scanned": summary.total_scanned,
            "improved_count": summary.improved_count,
            "commit_count": summary.commit_count,
            "total_tokens": summary.total_tokens,
            "improvements": [
                {
                    "skill": s,
                    "init": i,
                    "final": f,
                    "delta": d,
                }
                for s, i, f, d in summary.top_improvements
            ],
        }
        print(json.dumps(data_post, indent=2, ensure_ascii=False))
    else:
        render_post_run_summary(summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
