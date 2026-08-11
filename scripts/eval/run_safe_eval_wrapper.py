#!/usr/bin/env python3
"""run_safe_eval_wrapper.py - Safe Execution Sandbox Wrapper cho CCBA Agent Platform.

Bọc thực thi các lệnh terminal kiểm thử/eval ngầm, áp dụng Timeout Watchdog cứng,
Singleton Process Lock, ghi nhật ký cô lập và trích xuất tệp chẩn đoán cấu trúc diagnostics.json.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def ensure_single_instance(script_keyword: str = "run_safe_eval_wrapper.py") -> None:
    """Kiểm tra và thu hồi tiến trình trùng lặp đang chạy script ngầm."""
    current_pid = os.getpid()
    try:
        import psutil

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                pid = proc.info["pid"]
                if pid == current_pid:
                    continue
                cmdline = " ".join(proc.info["cmdline"] or [])
                if script_keyword in cmdline:
                    print(f"🧹 [AUTO-LOCK] Thu hồi tiến trình cũ PID {pid} ({script_keyword})...")
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except ImportError:
        if sys.platform == "win32":
            try:
                res = subprocess.run(
                    [
                        "wmic",
                        "process",
                        "where",
                        "name='python.exe'",
                        "get",
                        "processid,commandline",
                    ],
                    capture_output=True,
                    text=True,
                )
                for line in res.stdout.splitlines():
                    if script_keyword in line:
                        parts = line.strip().rsplit(maxsplit=1)
                        if len(parts) == 2 and parts[1].isdigit():
                            pid = int(parts[1])
                            if pid != current_pid:
                                print(f"🧹 [AUTO-LOCK] Thu hồi tiến trình trùng lặp PID {pid}...")
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", str(pid)], capture_output=True
                                )
            except Exception:
                pass


def extract_summary_traceback(output: str, max_lines: int = 25) -> list[str]:
    """Trích xuất 20-25 dòng log lỗi/traceback quan trọng nhất từ output."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return []

    # Tìm các dòng chứa từ khóa lỗi
    error_indices = [
        i
        for i, line_str in enumerate(lines)
        if any(
            k in line_str.lower() for k in ["error", "exception", "failed", "traceback", "assert"]
        )
    ]
    if error_indices:
        last_err_idx = error_indices[-1]
        start = max(0, last_err_idx - max_lines + 5)
        end = min(len(lines), last_err_idx + 10)
        return lines[start:end]

    # Fallback: Trả về max_lines dòng cuối cùng
    return lines[-max_lines:]


def extract_failed_gate(output: str) -> str | None:
    """Trích xuất tên cổng kiểm tra bị thất bại nếu có trong output."""
    gate_match = re.search(r"-\s*(Gate\s*[^:\n]+):\s*❌\s*FAILED", output)
    if gate_match:
        return gate_match.group(1).strip()
    return None


def extract_culprit_file(output: str) -> str | None:
    """Trích xuất đường dẫn file gây ra lỗi chính từ traceback."""
    file_match = re.search(r'File "([^"]+\.py)"', output)
    if file_match:
        return file_match.group(1)
    pytest_file_match = re.search(r" (packages/[^\s:]+\.py|scripts/[^\s:]+\.py):", output)
    if pytest_file_match:
        return pytest_file_match.group(1)
    return None


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


def run_safe_wrapper(
    cmd: str,
    timeout_seconds: int = 90,
    output_dir: Path | None = None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Thực thi một lệnh terminal trong môi trường Sandbox cô lập và tạo báo cáo chẩn đoán."""
    if cwd is None:
        cwd = Path.cwd()
    if output_dir is None:
        output_dir = cwd / ".md" / "scratch" / "eval_runs"

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"run_{timestamp}.log"

    ensure_single_instance("run_safe_eval_wrapper.py")

    start_time = time.time()
    result: dict[str, Any] = {
        "status": "UNKNOWN",
        "command": cmd,
        "elapsed_seconds": 0.0,
        "error_type": "NONE",
        "failed_gate": None,
        "culprit_file": None,
        "summary_traceback": [],
        "log_file": str(log_file),
        "returncode": -1,
    }

    try:
        with tempfile.TemporaryFile() as tmp_out:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=cwd,
                stdout=tmp_out,
                stderr=subprocess.STDOUT,
            )

            try:
                retcode = proc.wait(timeout=timeout_seconds)
                result["returncode"] = retcode
            except subprocess.TimeoutExpired:
                kill_process_tree(proc.pid)
                proc.wait()
                result["status"] = "TIMEOUT"
                result["error_type"] = "TIMEOUT"
                result["returncode"] = -124
                result["summary_traceback"] = [
                    f"⚠️ Lỗi: Lệnh '{cmd}' đã vượt quá thời gian thực thi tối đa ({timeout_seconds}s) và bị ngắt chủ động."
                ]

            tmp_out.seek(0)
            full_output = tmp_out.read().decode("utf-8", errors="ignore")

        # Ghi log ra file cô lập
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== Command: {cmd} ===\n")
            f.write(f"=== Started: {timestamp} ===\n\n")
            f.write(full_output)

        result["elapsed_seconds"] = round(time.time() - start_time, 2)

        if result["status"] == "UNKNOWN":
            if result["returncode"] == 0:
                result["status"] = "PASS"
                result["error_type"] = "NONE"
            else:
                result["status"] = "FAILED"
                result["error_type"] = "EXECUTION_ERROR"
                result["summary_traceback"] = extract_summary_traceback(full_output)
                result["failed_gate"] = extract_failed_gate(full_output)
                result["culprit_file"] = extract_culprit_file(full_output)

    except Exception as e:
        result["elapsed_seconds"] = round(time.time() - start_time, 2)
        result["status"] = "FAILED"
        result["error_type"] = "WRAPPER_EXCEPTION"
        result["summary_traceback"] = [f"Lỗi khởi chạy Wrapper Exception: {e}"]

    # Xuất tệp diagnostics.json
    diag_file = output_dir / "diagnostics.json"
    with open(diag_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # In thông tin ngắn gọn ra stdout
    print("\n==================================================")
    print("🛡️ SAFE SANDBOX EXECUTION SUMMARY:")
    print("==================================================")
    print(f"- Lệnh thực thi   : {cmd}")
    print(f"- Trạng thái      : {result['status']}")
    print(f"- Thời gian chạy  : {result['elapsed_seconds']}s")
    print(f"- File nhật ký    : {log_file}")
    print(f"- File chẩn đoán  : {diag_file}")
    if result["status"] != "PASS":
        print("\n--- TRÍCH XUẤT VẾT LỖI (DIAGNOSTICS TRACEBACK) ---")
        for line in result["summary_traceback"]:
            print(f"  {line}")
        print("--------------------------------------------------")
    print("==================================================\n")

    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CCBA Safe Execution Sandbox Wrapper.")
    parser.add_argument("--cmd", required=True, help="Lệnh terminal cần bọc thực thi cô lập.")
    parser.add_argument(
        "--timeout", type=int, default=90, help="Thời gian tối đa (giây) trước khi ngắt tiến trình."
    )
    parser.add_argument("--output-dir", help="Thư mục chứa file log và diagnostics.json.")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.resolve()
    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else project_root / ".md" / "scratch" / "eval_runs"
    )

    res = run_safe_wrapper(
        cmd=args.cmd, timeout_seconds=args.timeout, output_dir=out_dir, cwd=project_root
    )
    sys.exit(0 if res["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
