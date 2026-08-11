#!/usr/bin/env python3
"""run_harness_evals.py - Tự động hóa việc chạy các chốt chặn kiểm chứng (CI Gates) cho CCBA Platform.
Hỗ trợ chạy kiểm tra toàn bộ codebase hoặc chỉ chạy trên các file bị thay đổi (Git Diff) để tối ưu hiệu suất.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_pre_eval_health(project_root: Path) -> None:
    """Kiểm tra sức khỏe môi trường (dung lượng đĩa trống và venv) trước khi chạy các CI Gates."""
    try:
        total, used, free = shutil.disk_usage(project_root)
        free_gb = free / (1024**3)
        if free_gb < 2.0:
            print(
                f"⚠️ [HEALTH WARNING] Dung lượng đĩa trống thấp ({free_gb:.2f} GB < 2.0 GB)! "
                "Khuyến nghị chạy 'python scripts/session_cleanup.py --execute' trước."
            )
        else:
            print(f"ℹ️ [HEALTH] Môi trường khả dụng: {free_gb:.2f} GB đĩa trống.")
    except Exception as e:
        print(f"⚠️ [HEALTH] Không thể kiểm tra dung lượng đĩa: {e}")


def ensure_single_instance() -> None:
    """Tự động kiểm tra và triệt hạ các tiến trình run_harness_evals.py bị trùng lặp/treo từ trước."""
    current_pid = os.getpid()
    parent_pid = getattr(os, "getppid", lambda: None)()
    try:
        import psutil

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                pid = proc.info["pid"]
                if pid == current_pid or (parent_pid and pid == parent_pid):
                    continue
                cmdline = " ".join(proc.info["cmdline"] or [])
                if "run_harness_evals.py" in cmdline:
                    print(
                        f"🧹 [AUTO-LOCK] Phát hiện tiến trình run_harness_evals.py cũ (PID {pid}). Đang thu hồi..."
                    )
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass


def get_git_modified_files(project_root: Path) -> set[Path]:
    """Lấy danh sách các tệp tin bị thay đổi hoặc thêm mới chưa commit trong git."""
    modified = set()
    try:
        # 1. Check local changes (staged + unstaged + untracked)
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in res.stdout.splitlines():
            if len(line) > 3:
                # Trích xuất đường dẫn file, bỏ qua trạng thái git (ví dụ: 'M ', '?? ')
                filepath = (project_root / line[3:].strip()).resolve()
                modified.add(filepath)

        # 2. Check commits in current branch relative to origin/main (nếu có)
        res_diff = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if res_diff.returncode == 0:
            for line in res_diff.stdout.splitlines():
                if line.strip():
                    filepath = (project_root / line.strip()).resolve()
                    modified.add(filepath)
    except Exception as e:
        print(f"⚠️ Không thể quét git diff: {e}. Sẽ chạy kiểm tra mặc định.")
    return modified


import tempfile


def kill_process_tree(pid: int) -> None:
    """Tiêu diệt đệ quy toàn bộ cây tiến trình (process tree) trên Windows/Linux."""
    try:
        import psutil

        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        parent.kill()
    except Exception:
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                )
            except Exception:
                pass


def run_command(
    cmd: list[str], cwd: Path, name: str, timeout_seconds: int = 60
) -> tuple[bool, str]:
    """Chạy một lệnh hệ thống và trả về trạng thái cùng stdout/stderr với rào chắn timeout an toàn."""
    print(f"🚀 Chạy {name}...")
    with tempfile.TemporaryFile() as tmp_out:
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=tmp_out,
                stderr=subprocess.STDOUT,
            )
            try:
                retcode = proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                kill_process_tree(proc.pid)
                proc.wait()
                tmp_out.seek(0)
                output = tmp_out.read().decode("utf-8", errors="ignore")
                return (
                    False,
                    f"⚠️ Lỗi: Tiến trình '{name}' vượt quá thời gian cho phép ({timeout_seconds}s) và đã bị hủy.\nOutput trước khi ngắt:\n{output.strip()}",
                )

            tmp_out.seek(0)
            output = tmp_out.read().decode("utf-8", errors="ignore")
            success = retcode == 0
            return success, output.strip()
        except Exception as e:
            return False, f"Lỗi thực thi lệnh '{name}': {e}"


def get_venv_python(project_root: Path) -> str:
    """Trả về đường dẫn tới python trong .venv nếu có, fallback sys.executable."""
    venv_win = project_root / ".venv" / "Scripts" / "python.exe"
    if venv_win.exists():
        return str(venv_win)
    venv_nix = project_root / ".venv" / "bin" / "python"
    if venv_nix.exists():
        return str(venv_nix)
    return sys.executable


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    ensure_single_instance()

    parser = argparse.ArgumentParser(description="CCBA CI Eval Gates Runner.")
    parser.add_argument("--all", action="store_true", help="Chạy kiểm tra trên toàn bộ codebase.")
    parser.add_argument("--no-test", action="store_true", help="Bỏ qua phần chạy unit tests.")
    parser.add_argument(
        "--stress",
        action="store_true",
        help="Kích hoạt chạy cả các bài test tải nặng (stress/adversarial).",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.resolve()
    py_exe = get_venv_python(project_root)
    check_pre_eval_health(project_root)

    modified_files = get_git_modified_files(project_root) if not args.all else set()

    # Phân loại file bị thay đổi
    py_modified = []
    md_modified = []

    if not args.all:
        for f in modified_files:
            if f.exists() and f.is_file():
                if f.suffix == ".py":
                    py_modified.append(f)
                elif f.suffix == ".md":
                    md_modified.append(f)

        print(
            f"ℹ️ Phát hiện {len(py_modified)} file Python và {len(md_modified)} file Markdown thay đổi."
        )
        if len(modified_files) == 0:
            print("✨ Không có file nào thay đổi. Codebase sạch sẽ.")
            # Chạy toàn bộ nếu không có file thay đổi và không chạy --all, để đảm bảo tính an toàn
            args.all = True

    # Danh sách các Gates kết quả
    gates_summary = []
    all_success = True

    # ==========================================
    # GATE 1 & 2: Linter & Formatter (Ruff)
    # ==========================================
    ruff_paths = (
        ["packages", "scripts"]
        if args.all
        else [str(f.relative_to(project_root)) for f in py_modified]
    )
    if ruff_paths:
        # Check Ruff Lint
        success_lint, out_lint = run_command(
            [py_exe, "-m", "ruff", "check"] + ruff_paths, project_root, "Ruff Linter"
        )
        gates_summary.append(("Gate 1a: Ruff Lint", success_lint, out_lint))
        all_success = all_success and success_lint

        # Check Ruff Format
        success_fmt, out_fmt = run_command(
            [py_exe, "-m", "ruff", "format", "--check"] + ruff_paths,
            project_root,
            "Ruff Formatter Check",
        )
        gates_summary.append(("Gate 1b: Ruff Format", success_fmt, out_fmt))
        all_success = all_success and success_fmt

    # ==========================================
    # GATE 3: Type Checking (Mypy)
    # ==========================================
    if args.all:
        # Chỉ chạy mypy trên các package và file quan trọng đã được gỡ lỗi type check hoàn chỉnh
        mypy_paths = [
            "packages/mdconverter/src/mdconverter",
            "scripts/run_harness_evals.py",
            ".agents/skills/youtube-learn/scripts/visual_extractor.py",
        ]

    else:
        mypy_paths = [
            str(f.relative_to(project_root))
            for f in py_modified
            if "tests" not in f.relative_to(project_root).parts
        ]
    if mypy_paths:
        # Mypy check
        mypy_cmd = [
            py_exe,
            "-m",
            "mypy",
            "--exclude",
            r"[\\/]tests[\\/]",
            "--ignore-missing-imports",
            "--follow-imports=silent",
        ] + mypy_paths
        success_mypy, out_mypy = run_command(mypy_cmd, project_root, "Mypy Type Checker")
        gates_summary.append(("Gate 2: Mypy Typecheck", success_mypy, out_mypy))
        all_success = all_success and success_mypy

    # ==========================================
    # GATE 4: Unit Testing (Pytest)
    # ==========================================
    if not args.no_test:
        test_args = []
        if not args.all:
            # Map thông minh từ file Python bị sửa đổi sang thư mục tests của package tương ứng
            test_dirs = set()
            for f in py_modified:
                # Ví dụ: packages/ccba-ooxml/src/ccba_ooxml/utils.py -> packages/ccba-ooxml/tests/
                parts = f.relative_to(project_root).parts
                if len(parts) >= 2 and parts[0] == "packages":
                    test_dir = project_root / parts[0] / parts[1] / "tests"
                    if test_dir.exists():
                        test_dirs.add(str(test_dir.relative_to(project_root)))
                elif len(parts) >= 2 and parts[0] == "scripts":
                    test_dir = project_root / "scripts" / "tests"
                    if test_dir.exists():
                        test_dirs.add(str(test_dir.relative_to(project_root)))

            if test_dirs:
                test_args = list(test_dirs)
                print(f"ℹ️ Chỉ chạy test cho các package bị ảnh hưởng: {test_args}")
            else:
                # Fallback: nếu không có packages cụ thể bị đổi (ví dụ đổi core script), chạy các test nhỏ của scripts
                test_args = ["scripts/tests"] if (project_root / "scripts/tests").exists() else []
        else:
            # Chạy các test suite ổn định và độc lập trên môi trường sandbox/CI
            test_args = [
                "packages/mdconverter/tests",
                "packages/ccba-ai/tests",
            ]
            if (project_root / "scripts/tests").exists():
                test_args.append("scripts/tests")

        # Chạy pytest
        pytest_cmd = [py_exe, "-m", "pytest"] + (test_args if test_args else [])
        if not args.stress:
            pytest_cmd += ["-m", "not stress and not slow"]

        import importlib.util

        if importlib.util.find_spec("pytest_cov") is not None:
            pytest_cmd += [
                "--cov=packages/mdconverter/src/mdconverter",
                "--cov=packages/ccba-ai/src/ccba_ai",
                "--cov-report=xml",
            ]

        success_test, out_test = run_command(
            pytest_cmd, project_root, "Pytest Suite", timeout_seconds=90
        )
        gates_summary.append(("Gate 3: Pytest Unit Tests", success_test, out_test))
        all_success = all_success and success_test

    # ==========================================
    # GATE 5: Document & Architecture Verification (validate_docs.py)
    # ==========================================
    # Luôn chạy để bắt Architecture Drift
    if True:
        # Chạy validate_docs
        validate_script = project_root / "scripts" / "validate_docs.py"
        if validate_script.exists():
            success_docs, out_docs = run_command(
                [py_exe, str(validate_script)], project_root, "Validate Docs Check"
            )

            gates_summary.append(("Gate 4: Documentation Integrity", success_docs, out_docs))
            all_success = all_success and success_docs

    # ==========================================
    # XUẤT KẾT QUẢ TỔNG HỢP (SUMMARY REPORT)
    # ==========================================
    print("\n==================================================")
    print("📊 BÁO CÁO KẾT QUẢ CI EVAL GATES:")
    print("==================================================")

    for name, success, out in gates_summary:
        status_str = "✅ PASS" if success else "❌ FAILED"
        print(f"- {name:<35}: {status_str}")
        if not success:
            print("\n--- CHI TIẾT LỖI ---")
            # In ra 25 dòng đầu và 25 dòng cuối của output lỗi để tránh ngập terminal
            lines = out.splitlines()
            if len(lines) > 50:
                truncated_out = "\n".join(
                    lines[:25] + ["\n... [TRUNCATED LOGS] ...\n"] + lines[-25:]
                )
            else:
                truncated_out = out
            print(truncated_out)
            print("--------------------\n")

    print("==================================================")
    if all_success:
        print("🎉 TẤT CẢ CÁC GATES ĐÃ PASS! CODEBASE ĐÃ SẴN SÀNG.")
        sys.exit(0)
    else:
        print("❌ CÓ CÁC CỔNG KIỂM TRA BỊ THẤT BẠI. VUI LÒNG SỬA LỖI.")
        sys.exit(1)


if __name__ == "__main__":
    main()
