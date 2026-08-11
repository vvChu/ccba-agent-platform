import os
import sys
import time
import subprocess
import atexit
from pathlib import Path

LOCK_FILE = Path(__file__).resolve().parent / "run_isolated_tests.lock"

def ensure_single_instance() -> None:
    """Singleton process lock ensuring only one test runner instance executes at a time."""
    current_pid = os.getpid()
    parent_pid = os.getppid()
    
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text().strip())
            if old_pid not in (current_pid, parent_pid):
                print(f"[ProcessLock] Existing runner process active with PID {old_pid}. Aborting execution.")
                sys.exit(0)
        except Exception:
            pass
            
    LOCK_FILE.write_text(str(current_pid), encoding="utf-8")
    
    def cleanup_lock():
        try:
            if LOCK_FILE.exists() and LOCK_FILE.read_text().strip() == str(current_pid):
                LOCK_FILE.unlink()
        except Exception:
            pass
            
    atexit.register(cleanup_lock)

def main() -> None:
    ensure_single_instance()
    
    workspace_root = Path(__file__).resolve().parent.parent.parent
    tests_dir = workspace_root / "packages" / "ccba-legal-intel" / "tests"
    
    if not tests_dir.exists():
        print(f"Error: Directory {tests_dir} does not exist.")
        sys.exit(1)
        
    test_files = sorted(list(tests_dir.glob("test_*.py")))
    print(f"Found {len(test_files)} test files in {tests_dir}")
    
    results = []
    
    python_exe = sys.executable
    venv_pytest = workspace_root / ".venv" / "Scripts" / "pytest.exe"
    pytest_cmd = str(venv_pytest) if venv_pytest.exists() else [python_exe, "-m", "pytest"]

    for idx, test_file in enumerate(test_files, start=1):
        rel_path = test_file.relative_to(workspace_root)
        print(f"[{idx}/{len(test_files)}] Running {test_file.name}...", end=" ", flush=True)
        
        start_time = time.perf_counter()
        status = "UNKNOWN"
        duration = 0.0
        
        if isinstance(pytest_cmd, str):
            cmd = [pytest_cmd, str(test_file), "-q", "--maxfail=1"]
        else:
            cmd = pytest_cmd + [str(test_file), "-q", "--maxfail=1"]
            
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(workspace_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5.0
            )
            duration = time.perf_counter() - start_time
            if proc.returncode == 0:
                status = "PASSED"
            else:
                status = f"FAILED ({proc.returncode})"
        except subprocess.TimeoutExpired:
            duration = time.perf_counter() - start_time
            status = "TIMEOUT (> 5s)"
        except Exception as e:
            duration = time.perf_counter() - start_time
            status = f"ERROR ({type(e).__name__})"
            
        print(f"{status} in {duration:.2f}s")
        results.append({
            "name": test_file.name,
            "rel_path": str(rel_path),
            "status": status,
            "duration": duration
        })

    # Generate benchmark report
    total_files = len(results)
    passed_count = sum(1 for r in results if r["status"] == "PASSED")
    failed_count = sum(1 for r in results if "FAILED" in r["status"])
    timeout_count = sum(1 for r in results if "TIMEOUT" in r["status"])
    total_duration = sum(r["duration"] for r in results)
    
    report_lines = [
        "# Báo cáo Benchmark Cô lập Test Suite `ccba-legal-intel`",
        "",
        f"- **Tổng số test file**: {total_files}",
        f"- **PASSED**: {passed_count}",
        f"- **FAILED**: {failed_count}",
        f"- **TIMEOUT**: {timeout_count}",
        f"- **Tổng thời gian chạy**: {total_duration:.2f} giây",
        "",
        "## Chi tiết thời gian phản hồi từng test file",
        "",
        "| # | Tệp Test | Trạng thái | Thời gian (giây) | Ngưỡng < 3s |",
        "|---|---|---|---|---|"
    ]
    
    for idx, r in enumerate(results, start=1):
        pass_threshold = "✅ Đạt" if r["duration"] < 3.0 and r["status"] == "PASSED" else "⚠️ Vượt / Lỗi"
        report_lines.append(f"| {idx} | `{r['name']}` | {r['status']} | {r['duration']:.2f}s | {pass_threshold} |")

    report_path = workspace_root / ".md" / "wayfinder" / "test_benchmark_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    
    print("\nBenchmark completed successfully!")
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    main()
