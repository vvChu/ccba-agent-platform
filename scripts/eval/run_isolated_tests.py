#!/usr/bin/env python3
"""run_isolated_tests.py - CLI Helper kiểm thử cô lập siêu tốc cho CCBA Agent Platform.

Hỗ trợ chạy kiểm thử cô lập 1 package, 1 file test cụ thể, hoặc tự động phát hiện
toàn bộ packages trong platform (--all) kèm cờ --stress cho pre-release gate.
"""

import argparse
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path when running script directly
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.eval.process_safety import get_venv_python, kill_process_tree


def discover_test_targets(project_root: Path) -> dict[str, Path]:
    """Tự động quét và phát hiện toàn bộ các test suites trong codebase.

    Args:
        project_root: Đường dẫn gốc của repository.

    Returns:
        Dictionary ánh xạ tên target (package/domain) -> đường dẫn thư mục tests.
    """
    targets: dict[str, Path] = {}

    packages_dir = project_root / "packages"
    if packages_dir.is_dir():
        for pkg in sorted(packages_dir.iterdir()):
            tests_dir = pkg / "tests"
            if pkg.is_dir() and tests_dir.is_dir():
                targets[pkg.name] = tests_dir

    scripts_tests = project_root / "scripts" / "tests"
    if scripts_tests.is_dir():
        targets["scripts"] = scripts_tests

    root_tests = project_root / "tests"
    if root_tests.is_dir():
        targets["root-tests"] = root_tests

    return targets


def _enqueue_output(stream: Any, q: queue.Queue[str]) -> None:
    """Đọc từng dòng từ tiến trình con vào hàng đợi bất đồng bộ."""
    try:
        for line in iter(stream.readline, ""):
            q.put(line)
    except Exception:
        pass
    finally:
        try:
            stream.close()
        except Exception:
            pass


def run_isolated_test(
    target_path: Path, project_root: Path, include_stress: bool = False, timeout_sec: int = 60
) -> tuple[bool, float]:
    """Chạy lệnh pytest trong subprocess cô lập với timeout giám sát.

    Args:
        target_path: Đường dẫn mục tiêu test (thư mục hoặc file).
        project_root: Đường dẫn gốc repo.
        include_stress: Có chạy cả test slow/stress hay không.
        timeout_sec: Giới hạn thời gian (giây).

    Returns:
        Tuple (success: bool, elapsed_seconds: float).
    """
    pytest_cmd = [str(target_path), "-v", "--tb=short"]
    if not include_stress:
        pytest_cmd += ["-m", "not stress and not slow"]

    cmd = [get_venv_python(project_root), "-m", "pytest"] + pytest_cmd
    print(f"\n🎯 Kích hoạt kiểm thử cô lập trên: {target_path}")
    print(f"⚙️ Command: {' '.join(cmd)}")

    start_time = time.time()

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            bufsize=1,
        )

        out_queue: queue.Queue[str] = queue.Queue()
        if proc.stdout:
            t = threading.Thread(target=_enqueue_output, args=(proc.stdout, out_queue), daemon=True)
            t.start()

        while True:
            try:
                line = out_queue.get_nowait()
            except queue.Empty:
                line = ""

            if line:
                sys.stdout.write(line)
                sys.stdout.flush()
            else:
                time.sleep(0.05)

            elapsed = time.time() - start_time
            if elapsed > timeout_sec and proc.poll() is None:
                kill_process_tree(proc.pid)
                proc.wait()
                print(
                    f"\n⚠️ [TIMEOUT ERROR] Lượt kiểm thử bị ngắt sau {elapsed:.2f}s (Giới hạn: {timeout_sec}s)."
                )
                return False, elapsed

            if not line and proc.poll() is not None and out_queue.empty():
                break

        retcode = proc.poll() or 0
        elapsed = time.time() - start_time
        success = retcode == 0

        status_icon = "✅ PASS" if success else "❌ FAILED"
        print("==================================================")
        print(f"📊 Kết quả kiểm thử cô lập ({status_icon}) - Thời gian: {elapsed:.2f}s")
        print("==================================================")
        return success, elapsed

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(
            f"\n⚠️ [TIMEOUT ERROR] Lượt kiểm thử bị ngắt sau {elapsed:.2f}s (Giới hạn: {timeout_sec}s)."
        )
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ [EXECUTION ERROR] Không thể thực thi pytest: {e}")
        return False, elapsed


def main() -> None:
    """Entry point chính của CLI runner."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

    project_root = Path(__file__).resolve().parent.parent.parent
    discovered_targets = discover_test_targets(project_root)
    available_packages = list(discovered_targets.keys())

    parser = argparse.ArgumentParser(
        description="CCBA Isolated Test Helper với tính năng Dynamic Discovery."
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Tự động phát hiện và chạy kiểm thử cô lập tuần tự trên TẤT CẢ packages trong platform.",
    )
    parser.add_argument(
        "--package",
        "-p",
        choices=available_packages,
        help=f"Tên package cần test ({', '.join(available_packages)})",
    )
    parser.add_argument(
        "--file", "-f", help="Đường dẫn tương đối hoặc tuyệt đối tới file test cụ thể."
    )
    parser.add_argument(
        "--stress", action="store_true", help="Chạy cả các bài test tải nặng/stress/slow."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Thời gian tối đa cho mỗi lượt run (giây). Default: 60s.",
    )

    args = parser.parse_args()

    if not args.all and not args.package and not args.file:
        print("❌ Lỗi: Cần truyền --all (-a), --package (-p) hoặc --file (-f).")
        print(
            "Ví dụ 1 (Toàn bộ platform): python scripts/eval/run_isolated_tests.py --all --stress"
        )
        print("Ví dụ 2 (Từng package)    : python scripts/eval/run_isolated_tests.py -p ccba-ai")
        print(
            "Ví dụ 3 (File cụ thể)     : python scripts/eval/run_isolated_tests.py -f tests/test_agent_execution_guardrails.py"
        )
        sys.exit(1)

    if args.all:
        print(
            f"🔍 Phát hiện tự động {len(discovered_targets)} test targets: {', '.join(discovered_targets.keys())}"
        )
        summary_results: list[tuple[str, bool, float]] = []
        overall_success = True

        for name, target_path in discovered_targets.items():
            success, elapsed = run_isolated_test(
                target_path=target_path,
                project_root=project_root,
                include_stress=args.stress,
                timeout_sec=args.timeout,
            )
            summary_results.append((name, success, elapsed))
            if not success:
                overall_success = False

        print("\n" + "=" * 60)
        print("📊 TỔNG HỢP KẾT QUẢ KIỂM THỬ CÔ LẬP TOÀN BỘ PLATFORM:")
        print("=" * 60)
        for name, success, elapsed in summary_results:
            icon = "✅ PASS" if success else "❌ FAIL"
            print(f" - {name:<25}: {icon} ({elapsed:.2f}s)")
        print("=" * 60)
        if overall_success:
            print("🎉 TẤT CẢ CÁC PACKAGES ĐỀU VƯỢT QUA KIỂM THỬ AN TOÀN!")
        else:
            print("❌ CÓ TEST TARGET BỊ THẤT BẠI. VUI LÒNG KIỂM TRA LOG Ở TRÊN.")

        sys.exit(0 if overall_success else 1)

    elif args.package:
        target_path = discovered_targets[args.package]
    else:
        target_path = Path(args.file)
        if not target_path.is_absolute():
            target_path = project_root / target_path

    if not target_path.exists():
        print(f"❌ Lỗi: Đường dẫn mục tiêu không tồn tại: {target_path}")
        sys.exit(1)

    success, _ = run_isolated_test(
        target_path=target_path,
        project_root=project_root,
        include_stress=args.stress,
        timeout_sec=args.timeout,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
