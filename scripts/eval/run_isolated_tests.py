#!/usr/bin/env python3
"""run_isolated_tests.py - CLI Helper kiểm thử cô lập siêu tốc cho CCBA Agent Platform.
Giúp Agent và Developer chạy kiểm thử cô lập chính xác 1 package hoặc 1 file test cụ thể,
tự động áp dụng timeout rào chắn và in báo cáo kết quả súc tích.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from scripts.eval.process_safety import get_venv_python

AVAILABLE_PACKAGES = [
    "ccba-ai",
    "ccba-harness",
    "ccba-legal-intel",
    "ccba-notebooklm",
    "ccba-ooxml",
    "ccba-pdf-prep",
    "mdconverter",
    "scripts",
]


def run_isolated_test(
    target_path: Path, project_root: Path, include_stress: bool = False, timeout_sec: int = 60
) -> bool:
    """Chạy pytest trên một đường dẫn cụ thể với rào chắn timeout."""
    python_exe = get_venv_python(project_root)
    cmd = [python_exe, "-m", "pytest", str(target_path), "-v", "--tb=short"]
    if not include_stress:
        cmd += ["-m", "not stress and not slow"]

    print(f"🎯 Kích hoạt kiểm thử cô lập trên: {target_path}")
    print(f"⚙️ Command: {' '.join(cmd)}")
    start_time = time.time()

    try:
        res = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout_sec,
        )
        elapsed = time.time() - start_time
        success = res.returncode == 0

        print(res.stdout)
        if not success and res.stderr:
            print("\n--- STDERR ---")
            print(res.stderr)

        status_icon = "✅ PASS" if success else "❌ FAILED"
        print("\n==================================================")
        print(f"📊 Kết quả kiểm thử cô lập ({status_icon}) - Thời gian: {elapsed:.2f}s")
        print("==================================================")
        return success

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(
            f"\n⚠️ [TIMEOUT ERROR] Lượt kiểm thử bị ngắt sau {elapsed:.2f}s (Giới hạn: {timeout_sec}s)."
        )
        return False
    except Exception as e:
        print(f"\n❌ [EXECUTION ERROR] Không thể thực thi pytest: {e}")
        return False


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    project_root = Path(__file__).resolve().parent.parent.parent

    parser = argparse.ArgumentParser(description="CCBA Isolated Test Helper.")
    parser.add_argument(
        "--package",
        "-p",
        choices=AVAILABLE_PACKAGES,
        help=f"Tên package cần test ({', '.join(AVAILABLE_PACKAGES)})",
    )
    parser.add_argument(
        "--file", "-f", help="Đường dẫn tương đối hoặc tuyệt đối tới file test cụ thể."
    )
    parser.add_argument(
        "--stress", action="store_true", help="Chạy cả các bài test tải nặng/stress."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Thời gian tối đa cho toàn bộ lượt run (giây). Default: 60s.",
    )

    args = parser.parse_args()

    if not args.package and not args.file:
        print("❌ Lỗi: Cần truyền --package (-p) hoặc --file (-f).")
        print("Ví dụ: python scripts/run_isolated_tests.py -p ccba-ai")
        print(
            "Ví dụ: python scripts/run_isolated_tests.py -f tests/test_agent_execution_guardrails.py"
        )
        sys.exit(1)

    if args.package:
        if args.package == "scripts":
            target_path = project_root / "scripts" / "tests"
        else:
            target_path = project_root / "packages" / args.package / "tests"
    else:
        target_path = Path(args.file)
        if not target_path.is_absolute():
            target_path = project_root / target_path

    if not target_path.exists():
        print(f"❌ Lỗi: Đường dẫn mục tiêu không tồn tại: {target_path}")
        sys.exit(1)

    success = run_isolated_test(
        target_path=target_path,
        project_root=project_root,
        include_stress=args.stress,
        timeout_sec=args.timeout,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
