"""HarnessGuard class.

Thin context manager and decorator to secure file access and run lint/tests.
Imports state and hook controllers from the private sub-module _engine.py.
"""

from __future__ import annotations

import fnmatch
import os
import pathlib
import sys
import threading
from collections.abc import Callable
from functools import wraps
from typing import Any

from ._engine import (
    HarnessEngine,
    HarnessState,
    _get_active_guards,
    _scan_for_sensitive_inodes,
)


class HarnessGuard:
    """Context Manager and Decorator to secure file access and run linter/tests on modifications.

    Intercepts file opens to prevent reading/writing of sensitive files, unless
    specifically approved. Tracks written Python files and triggers quality checks
    upon successful exit.
    """

    def __init__(self, approved_paths: list[str] | None = None) -> None:
        """Initialize the HarnessGuard.

        Args:
            approved_paths: List of paths (exact, parent directories, or glob patterns)
                            that are allowed to bypass the sensitive file checks.
        """
        self.approved_paths: list[str] = approved_paths or []
        self._write_lock = threading.Lock()
        self._written_py_files: set[str] = set()
        self._written_files: set[str] = set()
        self._hooks_applied: bool = False

    def __enter__(self) -> HarnessGuard:
        guards = _get_active_guards()
        is_outermost = len(guards) == 0
        if is_outermost:
            _scan_for_sensitive_inodes()
        self._env_snapshot = dict(os.environ)

        # Write sitecustomize.py for child-process PYTHONPATH enforcement using shared temp dir
        with HarnessState.shared_temp_dir_lock:
            if HarnessState.shared_temp_dir is None:
                import tempfile

                HarnessState.shared_temp_dir = tempfile.mkdtemp(prefix="harness_guard_")
                sitecustomize_path = os.path.join(HarnessState.shared_temp_dir, "sitecustomize.py")
                try:
                    with open(sitecustomize_path, "w", encoding="utf-8") as f:
                        f.write("""import os
import sys

active = os.environ.get("HARNESS_ACTIVE")
approved_paths_env = os.environ.get("HARNESS_APPROVED_PATHS")

if active == "1":
    try:
        from ccba_harness import HarnessGuard
        approved_paths = []
        if approved_paths_env:
            approved_paths = approved_paths_env.split(os.pathsep)
        guard = HarnessGuard(approved_paths=approved_paths)
        sys._harness_guard = guard
        guard.__enter__()
    except Exception:
        pass
""")
                except Exception:
                    pass
        self._temp_dir = HarnessState.shared_temp_dir

        # Set environment variables for children to inherit/read
        if os.environ.get("HARNESS_ACTIVE") != "1":
            os.environ["HARNESS_ACTIVE"] = "1"
        new_approved = os.pathsep.join(self.approved_paths)
        if os.environ.get("HARNESS_APPROVED_PATHS") != new_approved:
            os.environ["HARNESS_APPROVED_PATHS"] = new_approved

        # Add this guard to thread-local active guards list
        guards.append(self)

        # Add to global active guards
        with HarnessState.lock:
            if self not in HarnessState.global_active_guards:
                HarnessState.global_active_guards.append(self)

        # Apply global hooks if not already applied
        HarnessEngine.activate()
        self._hooks_applied = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool | None:
        # Restore global hooks if they were applied by this guard
        if self._hooks_applied:
            HarnessEngine.deactivate()
            self._hooks_applied = False

        # Remove this guard from thread-local active guards
        guards = _get_active_guards()
        if self in guards:
            guards.remove(self)

        # Remove from global active guards
        with HarnessState.lock:
            if self in HarnessState.global_active_guards:
                HarnessState.global_active_guards.remove(self)

        # Clean up env variables and shared sitecustomize.py temp dir if no more active guards
        remaining = _get_active_guards()
        if not remaining:
            if "HARNESS_ACTIVE" in os.environ:
                os.environ.pop("HARNESS_ACTIVE", None)
            if "HARNESS_APPROVED_PATHS" in os.environ:
                os.environ.pop("HARNESS_APPROVED_PATHS", None)
            with HarnessState.shared_temp_dir_lock:
                if HarnessState.shared_temp_dir:
                    import shutil

                    try:
                        shutil.rmtree(HarnessState.shared_temp_dir, ignore_errors=True)
                    except Exception:
                        pass
                    HarnessState.shared_temp_dir = None
        else:
            all_approved = []
            for g in remaining:
                if g.approved_paths:
                    all_approved.extend(g.approved_paths)
            new_approved = os.pathsep.join(all_approved)
            if os.environ.get("HARNESS_APPROVED_PATHS") != new_approved:
                os.environ["HARNESS_APPROVED_PATHS"] = new_approved

        # Post-action hook: only run if no exception was raised inside the block
        with self._write_lock:
            has_py_files = bool(self._written_py_files)
        if exc_type is None and has_py_files:
            # Note: at this point, the original hooks are restored, so subprocesses run safely
            self._run_post_action_checks()

        return None

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Use a fresh instance of HarnessGuard for each call to avoid state pollution
            guard = HarnessGuard(approved_paths=self.approved_paths)
            with guard:
                return func(*args, **kwargs)

        return wrapper

    def _is_sensitive(self, path: str) -> bool:
        """Check if a path is classified as sensitive."""
        try:
            abs_path = os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else str(path)
            if isinstance(abs_path, bytes):
                abs_path = abs_path.decode("utf-8", errors="replace")

            # Check cache first to optimize performance
            if abs_path in HarnessState.path_resolution_cache:
                abs_path = HarnessState.path_resolution_cache[abs_path]
            else:
                orig_abs_path = abs_path
                # Resolve Windows 8.3 short paths if the path exists
                try:
                    resolved_path = str(pathlib.Path(abs_path).resolve())
                except Exception:
                    resolved_path = os.path.realpath(abs_path)
                abs_path = os.path.normpath(resolved_path)
                HarnessState.path_resolution_cache[orig_abs_path] = abs_path
        except Exception:
            abs_path = path

        if abs_path in HarnessState.sensitivity_cache:
            return HarnessState.sensitivity_cache[abs_path]

        try:
            st = os.stat(abs_path)
            if (st.st_dev, st.st_ino) in HarnessState.sensitive_inodes:
                HarnessState.sensitivity_cache[abs_path] = True
                return True
        except Exception:
            pass

        sensitive_keywords_substring = [
            "credential",
            "secret",
            "private_key",
            "password",
            "api_key",
            "token",
        ]

        is_sens = False
        parts = pathlib.Path(abs_path).parts
        for part in parts:
            part_lower = part.lower()
            if sys.platform == "win32":
                part_lower = part_lower.rstrip(". ")
            if any(kw in part_lower for kw in sensitive_keywords_substring):
                is_sens = True
                break
            if part_lower == ".env" or part_lower.endswith(".env"):
                is_sens = True
                break

        if is_sens:
            try:
                st = os.stat(abs_path)
                HarnessState.sensitive_inodes.add((st.st_dev, st.st_ino))
            except Exception:
                pass
            HarnessState.sensitivity_cache[abs_path] = True
            return True

        HarnessState.sensitivity_cache[abs_path] = False
        return False

    def _is_approved(self, path: str) -> bool:
        """Check if a path is approved by the user configurations."""
        if not self.approved_paths:
            return False

        abs_file = os.path.abspath(path)
        file_path_obj = pathlib.Path(abs_file)

        for pattern in self.approved_paths:
            # 1. Check exact match or parent directory
            try:
                abs_pattern = os.path.abspath(pattern)
                pattern_path_obj = pathlib.Path(abs_pattern)
                if file_path_obj == pattern_path_obj or pattern_path_obj in file_path_obj.parents:
                    return True
            except Exception:
                pass

            # 2. Check wildcard / glob match
            if (
                fnmatch.fnmatch(abs_file, pattern)
                or fnmatch.fnmatch(path, pattern)
                or fnmatch.fnmatch(os.path.basename(abs_file), pattern)
            ):
                return True

        return False

    def _check_file_access(self, file: Any, args: tuple, kwargs: dict) -> None:
        """Intercept file access to perform security checking and track python file writing."""
        if isinstance(file, (str, bytes, os.PathLike)):
            file_str = os.fspath(file)
            if isinstance(file_str, bytes):
                file_str = file_str.decode("utf-8", errors="replace")

            # Check absolute path cache to avoid expensive os.path.abspath
            cache_key = file_str
            if cache_key in HarnessState.abs_path_cache:
                abs_file_path, abs_path = HarnessState.abs_path_cache[cache_key]
            else:
                abs_file_path = (
                    os.normcase(os.path.abspath(file_str))
                    if hasattr(os, "normcase")
                    else os.path.normcase(os.path.abspath(file_str))
                )
                abs_path = os.path.abspath(file_str)
                HarnessState.abs_path_cache[cache_key] = (abs_file_path, abs_path)

            # Exclude sitecustomize.py or guard's own temporary directory files from tracking
            if "harness_guard_" in abs_file_path or "sitecustomize.py" in abs_file_path:
                if self._is_sensitive(file_str):
                    if not self._is_approved(file_str):
                        raise PermissionError(f"Access to sensitive file blocked: {file_str}")
                return

            if self._is_sensitive(file_str):
                if not self._is_approved(file_str):
                    raise PermissionError(f"Access to sensitive file blocked: {file_str}")

            # Determine if the file is opened for writing
            mode_val = "r"
            if "mode" in kwargs:
                mode_val = kwargs["mode"]
            elif len(args) >= 1:
                mode_val = args[0]

            if isinstance(mode_val, bytes):
                mode_str = mode_val.decode("utf-8", errors="ignore")
            else:
                mode_str = str(mode_val)
            is_write = any(c in mode_str for c in ("w", "a", "x", "+"))

            if is_write:
                with self._write_lock:
                    self._written_files.add(abs_file_path)
            if file_str.lower().endswith(".py") and is_write:
                with self._write_lock:
                    self._written_py_files.add(abs_path)

    def _run_post_action_checks(self) -> None:
        """Run ruff and pytest on the modified python files."""
        import subprocess

        with self._write_lock:
            py_files = sorted(self._written_py_files)
        for file_path in py_files:
            if os.path.exists(file_path):
                cmd_ruff = [sys.executable, "-m", "ruff", "check", file_path]
                res_ruff = subprocess.run(cmd_ruff, capture_output=True, text=True)
                if res_ruff.returncode != 0:
                    raise RuntimeError(
                        f"ruff check failed for {file_path} (exit code {res_ruff.returncode}).\n"
                        f"STDOUT:\n{res_ruff.stdout}\n"
                        f"STDERR:\n{res_ruff.stderr}"
                    )

        # Run pytest on the package directory
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        package_dir = os.path.dirname(os.path.dirname(current_file_dir))

        cmd_pytest = [sys.executable, "-m", "pytest", package_dir]
        res_pytest = subprocess.run(cmd_pytest, capture_output=True, text=True)
        if res_pytest.returncode != 0:
            raise RuntimeError(
                f"pytest failed for package {package_dir} (exit code {res_pytest.returncode}).\n"
                f"STDOUT:\n{res_pytest.stdout}\n"
                f"STDERR:\n{res_pytest.stderr}"
            )
