"""execution.py - Detached Process Execution Engine for CCBA Agent Platform.

Provides safe, detached background process execution, status tracking,
log resolution, and scoped test execution for Hub and Spokes.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

_TWO_TOKEN_PYTEST_FLAGS: frozenset[str] = frozenset(
    {
        "-n",
        "--numprocesses",
        "--maxprocesses",
        "--dist",
        "-m",
        "-k",
        "-c",
        "-o",
        "-p",
        "-W",
        "--tb",
        "--maxfail",
        "--rootdir",
        "--confcutdir",
        "--basetemp",
        "--durations",
        "--durations-min",
        "--junitxml",
        "--override-ini",
        "--import-mode",
        "--log-level",
        "--log-cli-level",
        "--capture",
    }
)


class DetachedExecutionEngine:
    """Deep module orchestrating detached process execution, log resolution, and scoped test discovery."""

    @staticmethod
    def resolve_scratch_dir(root: Path | None = None) -> Path:
        """Finds or creates the .md/scratch directory relative to project root.

        If root is provided, resolves relative to root.
        Otherwise, searches upward from Path.cwd() for .git or pyproject.toml markers,
        falling back to Path.cwd() / ".md" / "scratch".
        """
        if root is not None:
            scratch = Path(root).resolve() / ".md" / "scratch"
            scratch.mkdir(parents=True, exist_ok=True)
            return scratch

        current = Path.cwd().resolve()
        for parent in [current, *current.parents]:
            if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
                scratch = parent / ".md" / "scratch"
                scratch.mkdir(parents=True, exist_ok=True)
                return scratch

        scratch = current / ".md" / "scratch"
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
    def run_detached(cls, command: str, scratch_dir: Path | None = None) -> dict[str, Any]:
        """Launches command in a detached subprocess and records status."""
        if scratch_dir is None:
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
                    creationflags = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
                    if hasattr(subprocess, "CREATE_NO_WINDOW"):
                        creationflags |= int(getattr(subprocess, "CREATE_NO_WINDOW", 0))

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
    def check_status(cls, status_id: str | None = None, scratch_dir: Path | None = None) -> None:
        """Reads and displays current execution status and log tail."""
        if scratch_dir is None:
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
                try:
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
                except Exception:
                    is_running = False
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
                encoding="utf-8",
                errors="replace",
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
                if " -> " in filepath:
                    filepath = filepath.split(" -> ")[-1].strip()
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

    @staticmethod
    def _extract_extra_positional_targets(extra_args: list[str]) -> list[str]:
        """Extract existing filesystem targets from extra_args while skipping flag values."""
        extracted: list[str] = []
        skip_next = False
        for arg in extra_args:
            if skip_next:
                skip_next = False
                continue
            if arg in _TWO_TOKEN_PYTEST_FLAGS:
                skip_next = True
                continue
            if arg.startswith("-"):
                continue
            try:
                p = Path(arg)
                if p.exists():
                    extracted.append(str(p))
            except OSError:
                pass
        return extracted

    @staticmethod
    def _resolve_xdist_worker_args(workers: str | None, extra_args: list[str]) -> list[str]:
        """Build opt-in pytest-xdist worker CLI flags when requested and available."""
        if workers is None or str(workers).strip() in ("", "1"):
            return []
        if any(
            a in ("-n", "--numprocesses") or a.startswith(("-n=", "--numprocesses="))
            for a in extra_args
        ):
            return []
        if importlib.util.find_spec("xdist") is None:
            sys.stderr.write(
                "[SafePytest Warning] pytest-xdist is not installed; falling back to single-process execution.\n"
            )
            return []
        args = ["-n", str(workers).strip()]
        if not any(a == "--dist" or a.startswith("--dist=") for a in extra_args):
            args.append("--dist=loadfile")
        return args

    @classmethod
    def _resolve_safe_pytest_targets(
        cls,
        target_file: str | list[str] | None,
        package: str | None,
        allow_unscoped: bool,
        extra_targets: list[str],
    ) -> tuple[list[str], set[str], int | None]:
        """Resolve explicit, modified, or default unscoped pytest targets."""
        targets: list[str] = []
        if target_file:
            targets.extend(target_file if isinstance(target_file, list) else [target_file])
        elif package:
            pkg_path = Path("packages") / package / "tests"
            if not pkg_path.exists():
                pkg_path = Path("packages") / f"ccba-{package}" / "tests"
            if not pkg_path.exists():
                print(f"[SafePytest Error] Package tests directory not found: {package}")
                return [], set(), 1
            targets.append(str(pkg_path))

        added_from_extra: set[str] = set()
        for t in extra_targets:
            if t not in targets:
                targets.append(t)
                added_from_extra.add(t)

        if targets:
            return targets, added_from_extra, None
        if not allow_unscoped:
            git_targets = cls.find_modified_test_files()
            if git_targets:
                print(f"[SafePytest] Auto-detected modified test files: {', '.join(git_targets)}")
                return git_targets, added_from_extra, None
            print("[SafePytest] ℹ️ Không phát hiện file test nào bị sửa đổi qua git status.")
            print(
                "[SafePytest] 💡 Sử dụng '-f <file>', truyền tên package, hoặc '--allow-unscoped' để chạy toàn diện."
            )
            return [], added_from_extra, 0

        default_paths = ["tests", "scripts/tests"] + [
            p.as_posix() for p in sorted(Path("packages").glob("*/tests")) if p.is_dir()
        ]
        return [dp for dp in default_paths if Path(dp).exists()], added_from_extra, None

    @staticmethod
    def _targets_have_slow_marker(targets: list[str]) -> bool:
        """Return True if any resolved target file declares pytest.mark.slow."""
        for target in targets:
            try:
                p = Path(target)
                files = [p] if p.is_file() else (list(p.glob("**/*.py")) if p.is_dir() else [])
                for py_file in files:
                    if "pytest.mark.slow" in py_file.read_text(encoding="utf-8", errors="ignore"):
                        return True
            except OSError:
                pass
        return False

    @classmethod
    def run_safe_pytest(
        cls,
        target_file: str | list[str] | None = None,
        package: str | None = None,
        fast: bool = False,
        dry_run: bool = False,
        allow_unscoped: bool = False,
        extra_args: list[str] | None = None,
        scratch_dir: Path | None = None,
        workers: str | None = None,
    ) -> int:
        """Executes scoped pytest via detached execution engine."""
        extra_args = extra_args or []
        extra_targets = cls._extract_extra_positional_targets(extra_args)
        targets, added_from_extra, early_rc = cls._resolve_safe_pytest_targets(
            target_file, package, allow_unscoped, extra_targets
        )
        if early_rc is not None:
            return early_rc

        cmd_parts = [sys.executable, "-m", "pytest", "--maxfail=1"]
        if fast:
            cmd_parts.extend(
                ["-m", "fast or (unit and not slow and not integration and not stress)"]
            )
        elif not any(a.startswith("-m") for a in extra_args) and not cls._targets_have_slow_marker(
            targets
        ):
            cmd_parts.extend(["-m", "not slow and not stress"])

        cmd_parts.extend(cls._resolve_xdist_worker_args(workers, extra_args))
        cmd_parts.extend(targets)
        for ea in extra_args:
            if ea not in added_from_extra and ea not in cmd_parts:
                cmd_parts.append(ea)

        cmd_str = " ".join(
            (f'"{p}"' if (" " in p or "\t" in p) else p)
            if sys.platform.startswith("win")
            else shlex.quote(p)
            for p in cmd_parts
        )
        if dry_run:
            print(f"[SafePytest DRY-RUN] Planned execution:\n  Command: {cmd_str}")
            return 0
        print(f"[SafePytest] Executing detached runner:\n  Command: {cmd_str}")
        res = cls.run_detached(cmd_str, scratch_dir=scratch_dir)
        return int(res.get("return_code") or 0)
