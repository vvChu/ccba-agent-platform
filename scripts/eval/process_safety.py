#!/usr/bin/env python3
"""process_safety.py - Process Safety Infrastructure Utilities for CCBA Platform.

Tập trung các hàm dùng chung về an toàn tiến trình:
- Singleton Process Lock (bảo vệ tuyệt đối os.getpid() và os.getppid())
- Recursive Process Tree Termination (psutil + taskkill fallback)
- Venv Python Interpreter Resolution
"""

import os
import subprocess
import sys
from pathlib import Path


def ensure_single_instance(script_keyword: str) -> None:
    """Tự động kiểm tra và triệt hạ các tiến trình chạy ngầm bị trùng lặp/treo từ trước.

    CRITICAL INVARIANT: Bắt buộc loại trừ cả os.getpid() (tiến trình hiện tại)
    và os.getppid() (tiến trình cha/Agent host) để không làm sập Agent Server.
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(line_buffering=True)
        except Exception:
            pass

    current_pid = os.getpid()
    parent_pid = getattr(os, "getppid", lambda: None)()

    try:
        import psutil  # type: ignore[import-untyped]

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                pid = proc.info["pid"]
                if pid == current_pid or (parent_pid and pid == parent_pid):
                    continue
                cmdline = " ".join(proc.info["cmdline"] or [])
                if script_keyword in cmdline:
                    print(
                        f"🧹 [AUTO-LOCK] Phát hiện tiến trình {script_keyword} cũ (PID {pid}). Đang thu hồi..."
                    )
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
                            if pid != current_pid and (not parent_pid or pid != parent_pid):
                                print(f"🧹 [AUTO-LOCK] Thu hồi tiến trình trùng lặp PID {pid}...")
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", str(pid)], capture_output=True
                                )
            except Exception:
                pass


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


def get_venv_python(project_root: Path) -> str:
    """Trả về đường dẫn tới python trong .venv nếu có, fallback sys.executable."""
    venv_win = project_root / ".venv" / "Scripts" / "python.exe"
    if venv_win.exists():
        return str(venv_win)
    venv_nix = project_root / ".venv" / "bin" / "python"
    if venv_nix.exists():
        return str(venv_nix)
    return sys.executable


# ---------------------------------------------------------------------------
# Detached Process Execution Engine
# ---------------------------------------------------------------------------
import json
import shlex
import time
import uuid
from typing import Any


class DetachedExecutionEngine:
    """Deep module orchestrating detached process execution, log resolution, and scoped test discovery."""

    @staticmethod
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

    @staticmethod
    def cleanup_old_logs(scratch_dir: Path | None = None, max_age_hours: int = 24) -> None:
        """Removes log and status files older than max_age_hours."""
        if scratch_dir is None:
            scratch_dir = DetachedExecutionEngine.resolve_scratch_dir()
        now = time.time()
        for file in scratch_dir.glob("exec_*"):
            try:
                if now - file.stat().st_mtime > max_age_hours * 3600:
                    file.unlink()
            except OSError:
                pass

    @staticmethod
    def _write_status(status_file: Path, data: dict[str, Any]) -> None:
        """Writes status atomically using a temporary file."""
        tmp_file = status_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, status_file)

    @classmethod
    def run_detached(cls, command: str) -> dict[str, Any]:
        """Launches command in a detached subprocess and records status."""
        scratch_dir = cls.resolve_scratch_dir()
        cls.cleanup_old_logs(scratch_dir)

        run_id = str(uuid.uuid4())[:8]
        log_file = scratch_dir / f"exec_log_{run_id}.txt"
        status_file = scratch_dir / f"exec_status_{run_id}.json"

        status_data: dict[str, Any] = {
            "id": run_id,
            "command": command,
            "status": "running",
            "start_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "return_code": None,
            "pid": None,
            "error": None,
        }

        cls._write_status(status_file, status_data)

        with open(log_file, "ab") as log_file_handle:
            try:
                header = (
                    f"=== Starting Detached Execution ===\nCommand: {command}\nTimestamp: {status_data['start_time']}\n"
                    + "=" * 35
                    + "\n\n"
                )
                log_file_handle.write(header.encode("utf-8"))
                log_file_handle.flush()

                cmd_args = shlex.split(command, posix=not sys.platform.startswith("win"))
                cmd_args = [arg.strip("\"'") for arg in cmd_args]

                creationflags = 0
                if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
                    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                    if hasattr(subprocess, "CREATE_NO_WINDOW"):
                        creationflags |= subprocess.CREATE_NO_WINDOW

                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"

                try:
                    process = subprocess.Popen(
                        cmd_args,
                        stdout=log_file_handle,
                        stderr=log_file_handle,
                        creationflags=creationflags,
                        env=env,
                        close_fds=False if sys.platform.startswith("win") else True,
                    )
                except (FileNotFoundError, OSError) as e:
                    raise RuntimeError(f"Process launch failed: {e}") from e

                status_data["pid"] = process.pid
                cls._write_status(status_file, status_data)

                print(f"[SafeRunner] Process PID {process.pid} launched in background.")
                print(f"[SafeRunner] Log file: {log_file}")
                print(f"[SafeRunner] Status ID: {run_id}")

                retcode = process.wait()
                retcode_val = int(retcode) if isinstance(retcode, (int, float)) else 0
                log_file_handle.flush()

                status_data["status"] = "completed" if retcode_val == 0 else "failed"
                status_data["return_code"] = retcode_val
                cls._write_status(status_file, status_data)

            except Exception as e:
                status_data["status"] = "failed"
                status_data["error"] = str(e)
                cls._write_status(status_file, status_data)
                print(f"[SafeRunner] Execution failed: {e}")

        return status_data

    @classmethod
    def check_status(cls, status_id: str | None = None) -> None:
        """Reads and displays current execution status and log tail."""
        scratch_dir = cls.resolve_scratch_dir()

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
                cls._write_status(status_file, status_data)

        print(json.dumps(status_data, indent=2))

        log_file = scratch_dir / f"exec_log_{status_data.get('id', '')}.txt"
        if log_file.exists():
            print("\n--- Recent Log Output ---")
            lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines[-20:]:
                print(line)

    @staticmethod
    def find_modified_test_files() -> list[str]:
        """Finds modified or newly added test files via git status."""
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            test_files: list[str] = []
            for line in res.stdout.splitlines():
                if not line.strip():
                    continue
                parts = line.strip().split(maxsplit=1)
                if len(parts) < 2:
                    continue
                filepath = parts[1].strip()
                path_obj = Path(filepath)
                if (
                    path_obj.suffix == ".py"
                    and path_obj.name != "conftest.py"
                    and (path_obj.name.startswith("test_") or "tests" in path_obj.parts)
                ):
                    if path_obj.exists():
                        test_files.append(str(path_obj))
            return test_files
        except Exception as e:
            sys.stderr.write(f"[SafePytest Warning] Could not check git status: {e}\n")
            return []

    @classmethod
    def run_safe_pytest(
        cls,
        target_file: str | None = None,
        package: str | None = None,
        fast: bool = False,
        dry_run: bool = False,
        allow_unscoped: bool = False,
        extra_args: list[str] | None = None,
    ) -> int:
        """Executes scoped pytest via detached execution engine."""
        extra_args = extra_args or []
        targets: list[str] = []

        if target_file:
            targets.append(target_file)
        elif package:
            pkg_path = Path("packages") / package / "tests"
            if not pkg_path.exists():
                pkg_path = Path("packages") / f"ccba-{package}" / "tests"
            if pkg_path.exists():
                targets.append(str(pkg_path))
            else:
                print(f"[SafePytest Error] Package tests directory not found: {package}")
                return 1
        elif extra_args and any(not a.startswith("-") for a in extra_args):
            pass
        elif not allow_unscoped:
            git_targets = cls.find_modified_test_files()
            if git_targets:
                targets.extend(git_targets)
                print(f"[SafePytest] Auto-detected modified test files: {', '.join(targets)}")
        else:
            # Unscoped run across default test paths if no targets specified
            default_paths = [
                "packages/ccba-ai/tests",
                "scripts/tests",
            ]
            for dp in default_paths:
                if Path(dp).exists():
                    targets.append(dp)

        python_exec = sys.executable
        cmd_parts = [python_exec, "-m", "pytest", "--maxfail=1"]

        if fast:
            cmd_parts.extend(["-m", "fast or (unit and not slow and not integration and not stress)"])
        elif not any(a.startswith("-m") for a in extra_args):
            target_has_slow = False
            for t in targets:
                try:
                    p = Path(t)
                    if p.exists() and (
                        "pytest.mark.slow" in p.read_text(encoding="utf-8", errors="ignore")
                    ):
                        target_has_slow = True
                        break
                except Exception:
                    pass
            if not target_has_slow:
                cmd_parts.extend(["-m", "not slow and not stress"])

        if targets:
            cmd_parts.extend(targets)

        def safe_quote(arg: str) -> str:
            if sys.platform.startswith("win"):
                return f'"{arg}"' if (" " in arg or "\t" in arg) else arg
            return shlex.quote(arg)

        cmd_str = " ".join(safe_quote(p) for p in cmd_parts)

        if dry_run:
            print(f"[SafePytest DRY-RUN] Planned execution:\n  Command: {cmd_str}")
            return 0

        print(f"[SafePytest] Executing detached runner:\n  Command: {cmd_str}")
        res = cls.run_detached(cmd_str)
        return int(res.get("return_code") or 0)
