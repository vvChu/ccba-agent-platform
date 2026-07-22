#!/usr/bin/env python3
"""safe_runner.py - Detached Process Runner for CCBA Agent Platform.

Executes long-running shell commands asynchronously in a detached process,
redirecting stdout/stderr to a local log file to prevent Antigravity Daemon
cancellations during server restarts or timeouts.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def resolve_scratch_dir() -> Path:
    """Finds or creates the .md/scratch directory relative to project root."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            scratch = parent / ".md" / "scratch"
            scratch.mkdir(parents=True, exist_ok=True)
            return scratch
    scratch = Path.cwd() / ".md" / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    return scratch


def run_detached(command: str) -> None:
    """Launches command in a detached subprocess and records status."""
    scratch_dir = resolve_scratch_dir()
    log_file = scratch_dir / "exec_log.txt"
    status_file = scratch_dir / "exec_status.json"

    # Initial status
    status_data = {
        "command": command,
        "status": "running",
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "return_code": None,
    }

    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    log_file_handle = open(log_file, "w", encoding="utf-8")
    log_file_handle.write(f"=== Starting Detached Execution ===\n")
    log_file_handle.write(f"Command: {command}\n")
    log_file_handle.write(f"Timestamp: {status_data['start_time']}\n")
    log_file_handle.write("=" * 35 + "\n\n")
    log_file_handle.flush()

    import shlex
    cmd_args = shlex.split(command, posix=False)

    process = subprocess.Popen(
        cmd_args,
        stdout=log_file_handle,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
        env=env,
    )

    status_data["pid"] = process.pid
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    # Wait for process to complete in background task
    ret = process.wait()
    log_file_handle.close()

    status_data["status"] = "completed"
    status_data["return_code"] = ret
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    print(f"[SafeRunner] Process PID {process.pid} completed with return code {ret}.")
    print(f"[SafeRunner] Log file saved at: {log_file}")


def check_status() -> None:
    """Reads and displays current execution status and log tail."""
    scratch_dir = resolve_scratch_dir()
    log_file = scratch_dir / "exec_log.txt"
    status_file = scratch_dir / "exec_status.json"

    if not status_file.exists():
        print("[SafeRunner] No active execution status found.")
        return

    with open(status_file, encoding="utf-8") as f:
        status_data = json.load(f)

    pid = status_data.get("pid")
    is_running = False

    if pid:
        if sys.platform.startswith("win"):
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if handle:
                exit_code = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    is_running = (exit_code.value == 259)  # STILL_ACTIVE = 259
                kernel32.CloseHandle(handle)
        else:
            try:
                os.kill(pid, 0)
                is_running = True
            except OSError:
                is_running = False

    status_data["status"] = "running" if is_running else "completed"
    print(json.dumps(status_data, indent=2))

    if log_file.exists():
        print("\n--- Recent Log Output ---")
        lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines[-20:]:
            print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detached Process Runner")
    parser.add_argument("--command", type=str, help="Command to run in detached background process")
    parser.add_argument("--status", action="store_true", help="Check status of background execution")

    args = parser.parse_args()

    if args.status:
        check_status()
    elif args.command:
        run_detached(args.command)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
