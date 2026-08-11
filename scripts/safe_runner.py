#!/usr/bin/env python3
"""safe_runner.py - Detached Process Runner for CCBA Agent Platform.

Executes long-running shell commands asynchronously in a detached process,
redirecting stdout/stderr to a local log file to prevent Antigravity Daemon
cancellations during server restarts or timeouts.
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
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


def _write_status(status_file: Path, data: dict) -> None:
    """Writes status atomically using a temporary file."""
    tmp_file = status_file.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_file, status_file)


def _cleanup_old_logs(scratch_dir: Path, max_age_hours: int = 24) -> None:
    """Removes log and status files older than max_age_hours."""
    now = time.time()
    for file in scratch_dir.glob("exec_*"):
        try:
            if now - file.stat().st_mtime > max_age_hours * 3600:
                file.unlink()
        except OSError:
            pass


def run_detached(command: str) -> None:
    """Launches command in a detached subprocess and records status."""
    scratch_dir = resolve_scratch_dir()
    _cleanup_old_logs(scratch_dir)

    run_id = str(uuid.uuid4())[:8]
    log_file = scratch_dir / f"exec_log_{run_id}.txt"
    status_file = scratch_dir / f"exec_status_{run_id}.json"

    # Initial status
    status_data = {
        "id": run_id,
        "command": command,
        "status": "running",
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "return_code": None,
        "pid": None,
        "error": None,
    }

    _write_status(status_file, status_data)

    log_file_handle = open(log_file, "w", encoding="utf-8")
    try:
        log_file_handle.write("=== Starting Detached Execution ===\n")
        log_file_handle.write(f"Command: {command}\n")
        log_file_handle.write(f"Timestamp: {status_data['start_time']}\n")
        log_file_handle.write("=" * 35 + "\n\n")
        log_file_handle.flush()

        try:
            cmd_args = shlex.split(command, posix=not sys.platform.startswith("win"))
        except ValueError as e:
            raise ValueError(f"Command parsing failed: {e}") from e

        creationflags = 0
        start_new_session = False
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            if hasattr(subprocess, "DETACHED_PROCESS"):
                creationflags |= subprocess.DETACHED_PROCESS
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags |= subprocess.CREATE_NO_WINDOW
        else:
            start_new_session = True

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        try:
            process = subprocess.Popen(
                cmd_args,
                stdout=log_file_handle,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
                start_new_session=start_new_session,
                env=env,
            )
        except (FileNotFoundError, OSError) as e:
            raise RuntimeError(f"Process launch failed: {e}") from e

        status_data["pid"] = process.pid
        _write_status(status_file, status_data)

        print(f"[SafeRunner] Process PID {process.pid} launched in background.")
        print(f"[SafeRunner] Log file: {log_file}")
        print(f"[SafeRunner] Status ID: {run_id}")

    except Exception as e:
        status_data["status"] = "failed"
        status_data["error"] = str(e)
        _write_status(status_file, status_data)
        print(f"[SafeRunner] Execution failed: {e}")
    finally:
        log_file_handle.close()


def check_status(status_id: str | None = None) -> None:
    """Reads and displays current execution status and log tail."""
    scratch_dir = resolve_scratch_dir()

    if status_id:
        status_file = scratch_dir / f"exec_status_{status_id}.json"
        if not status_file.exists():
            print(f"[SafeRunner] Status file not found for ID: {status_id}")
            return
    else:
        status_files = list(scratch_dir.glob("exec_status_*.json"))
        if not status_files:
            print("[SafeRunner] No active execution status found.")
            return
        status_file = max(status_files, key=lambda f: f.stat().st_mtime)

    with open(status_file, encoding="utf-8") as f:
        status_data = json.load(f)

    pid = status_data.get("pid")
    current_status = status_data.get("status")

    if current_status == "running" and pid:
        is_running = False
        if sys.platform.startswith("win"):
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if handle:
                exit_code = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    if exit_code.value == 259:  # STILL_ACTIVE
                        is_running = True
                    else:
                        status_data["return_code"] = exit_code.value
                kernel32.CloseHandle(handle)
        else:
            try:
                os.kill(pid, 0)
                is_running = True
            except OSError:
                is_running = False

        if not is_running:
            status_data["status"] = "completed"
            _write_status(status_file, status_data)

    print(json.dumps(status_data, indent=2))

    log_file = scratch_dir / f"exec_log_{status_data.get('id', '')}.txt"
    if log_file.exists():
        print("\n--- Recent Log Output ---")
        lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines[-20:]:
            print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detached Process Runner")
    parser.add_argument("--command", type=str, help="Command to run in detached background process")
    parser.add_argument(
        "--status", action="store_true", help="Check status of background execution"
    )
    parser.add_argument(
        "--status-id", type=str, help="Check status of a specific execution ID"
    )

    args = parser.parse_args()

    if args.status or args.status_id:
        check_status(args.status_id)
    elif args.command:
        run_detached(args.command)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
