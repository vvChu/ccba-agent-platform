#!/usr/bin/env python3
"""run_harness_evals.py - Tự động hóa việc chạy các chốt chặn kiểm chứng (CI Gates) cho CCBA Platform.
Hỗ trợ chạy kiểm tra toàn bộ codebase hoặc chỉ chạy trên các file bị thay đổi (Git Diff) để tối ưu hiệu suất.
"""

import argparse
import subprocess
import sys
from pathlib import Path


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


def run_command(cmd: list[str], cwd: Path, name: str) -> tuple[bool, str]:
    """Chạy một lệnh hệ thống và trả về trạng thái cùng stdout/stderr."""
    print(f"🚀 Chạy {name}...")
    try:
        res = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        success = res.returncode == 0
        output = res.stdout if success else res.stdout + "\n" + res.stderr
        return success, output.strip()
    except Exception as e:
        return False, f"Lỗi thực thi lệnh: {e}"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CCBA CI Eval Gates Runner.")
    parser.add_argument("--all", action="store_true", help="Chạy kiểm tra trên toàn bộ codebase.")
    parser.add_argument("--no-test", action="store_true", help="Bỏ qua phần chạy unit tests.")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.resolve()
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
    ruff_paths = ["."] if args.all else [str(f.relative_to(project_root)) for f in py_modified]
    if ruff_paths:
        # Check Ruff Lint
        success_lint, out_lint = run_command(
            [sys.executable, "-m", "ruff", "check"] + ruff_paths, project_root, "Ruff Linter"
        )
        gates_summary.append(("Gate 1a: Ruff Lint", success_lint, out_lint))
        all_success = all_success and success_lint

        # Check Ruff Format
        success_fmt, out_fmt = run_command(
            [sys.executable, "-m", "ruff", "format", "--check"] + ruff_paths,
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
            "packages/mdconverter/src",
            "scripts/run_harness_evals.py",
            ".agents/skills/youtube-learn/scripts/visual_extractor.py",
        ]
    else:
        mypy_paths = [str(f.relative_to(project_root)) for f in py_modified]
    if mypy_paths:
        # Mypy check
        mypy_cmd = [
            sys.executable,
            "-m",
            "mypy",
            "--exclude",
            "/tests/",
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
        pytest_cmd = [sys.executable, "-m", "pytest"] + (test_args if test_args else [])
        success_test, out_test = run_command(pytest_cmd, project_root, "Pytest Suite")
        gates_summary.append(("Gate 3: Pytest Unit Tests", success_test, out_test))
        all_success = all_success and success_test

    # ==========================================
    # GATE 5: Document Verification (validate_docs.py)
    # ==========================================
    # Chỉ chạy khi có thay đổi file markdown hoặc khi chạy tất cả
    if args.all or md_modified:
        # Chạy validate_docs
        validate_script = project_root / "scripts" / "validate_docs.py"
        if validate_script.exists():
            success_docs, out_docs = run_command(
                [sys.executable, str(validate_script)], project_root, "Validate Docs Check"
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
