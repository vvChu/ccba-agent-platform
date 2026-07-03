"""HarnessGuard class, global hook installation, and thread wrappers.

Step 5 of harness.py decomposition:
  - _wrapped_thread_start / _wrapped_thread_start_new_thread / _wrapped_thread_start_new
  - _apply_global_hooks / _restore_global_hooks_internal / _restore_global_hooks
  - class HarnessGuard
"""
from __future__ import annotations

import _io
import _thread
import builtins
import fnmatch
import io
import os
import pathlib
import sqlite3
import subprocess
import sys
import threading
from collections.abc import Callable
from functools import wraps
from typing import Any

from ._file_monitor import (
    _scan_for_sensitive_inodes,
    _wrapped__io_open,
    _wrapped_builtins_open,
    _Wrapped_io_FileIO,
    _wrapped_io_open,
    _wrapped_os_link,
    _wrapped_os_open,
    _wrapped_os_rename,
    _wrapped_os_replace,
    _wrapped_os_symlink,
    _WrappedFileIO,
)
from ._process_monitor import (
    _audit_hook,
    _make_os_wrapper,
    _wrapped_popen,
)
from ._sql_monitor import (
    _wrapped_sqlite3_connect,
    _Wrappedsqlite3Connection,
)

# ---------------------------------------------------------------------------
# Module-level counters / flags — modified exclusively via 'global' within
# this module.  Imported initial values from _state for consistency.
# ---------------------------------------------------------------------------
from ._state import (  # noqa: E402
    _abs_path_cache,
    _active_count,
    _active_subthreads_count,
    _audit_hook_registered,
    _get_active_guards,
    _global_active_guards,
    _global_hooks_active,
    _local,
    _lock,
    _original_thread_start,
    _original_thread_start_new,
    _original_thread_start_new_thread,
    _Originals,
    _path_resolution_cache,
    _sensitive_inodes,
    _sensitivity_cache,
    _shared_temp_dir,
    _shared_temp_dir_lock,
)

# ---------------------------------------------------------------------------
# Thread wrappers — propagate active guards to child threads
# ---------------------------------------------------------------------------

def _wrapped_thread_start(self: threading.Thread, *args: Any, **kwargs: Any) -> Any:
    parent_guards = list(_get_active_guards())
    if parent_guards:
        global _active_subthreads_count
        with _lock:
            _active_subthreads_count += 1
    original_run = self.run

    def wrapped_run(*run_args: Any, **run_kwargs: Any) -> Any:
        _local.active_guards = list(parent_guards)
        try:
            return original_run(*run_args, **run_kwargs)
        finally:
            if parent_guards:
                global _active_subthreads_count, _active_count
                with _lock:
                    _active_subthreads_count -= 1
                    if _active_subthreads_count == 0 and _active_count == 0:
                        if _global_hooks_active:
                            _restore_global_hooks_internal()

    self.run = wrapped_run
    return _original_thread_start(self, *args, **kwargs)


def _wrapped_thread_start_new_thread(
    function: Callable, args: tuple, kwargs: dict | None = None
) -> int:
    parent_guards = list(_get_active_guards())
    if parent_guards:
        global _active_subthreads_count
        with _lock:
            _active_subthreads_count += 1
    if kwargs is None:
        kwargs = {}

    def thread_target_wrapper(*target_args: Any, **target_kwargs: Any) -> Any:
        _local.active_guards = list(parent_guards)
        try:
            return function(*target_args, **target_kwargs)
        finally:
            if parent_guards:
                global _active_subthreads_count, _active_count
                with _lock:
                    _active_subthreads_count -= 1
                    if _active_subthreads_count == 0 and _active_count == 0:
                        if _global_hooks_active:
                            _restore_global_hooks_internal()

    return _original_thread_start_new_thread(thread_target_wrapper, args, kwargs)


def _wrapped_thread_start_new(function: Callable, args: tuple, kwargs: dict | None = None) -> int:
    parent_guards = list(_get_active_guards())
    if parent_guards:
        global _active_subthreads_count
        with _lock:
            _active_subthreads_count += 1
    if kwargs is None:
        kwargs = {}

    def thread_target_wrapper(*target_args: Any, **target_kwargs: Any) -> Any:
        _local.active_guards = list(parent_guards)
        try:
            return function(*target_args, **target_kwargs)
        finally:
            if parent_guards:
                global _active_subthreads_count, _active_count
                with _lock:
                    _active_subthreads_count -= 1
                    if _active_subthreads_count == 0 and _active_count == 0:
                        if _global_hooks_active:
                            _restore_global_hooks_internal()

    if _original_thread_start_new is not None:
        return _original_thread_start_new(thread_target_wrapper, args, kwargs)
    else:
        return _original_thread_start_new_thread(thread_target_wrapper, args, kwargs)


# ---------------------------------------------------------------------------
# Global hook management
# ---------------------------------------------------------------------------

def _apply_global_hooks() -> None:
    global _active_count, _audit_hook_registered, _global_hooks_active
    with _lock:
        if not _audit_hook_registered:
            sys.addaudithook(_audit_hook)
            _audit_hook_registered = True

        if not _global_hooks_active:
            builtins.open = _wrapped_builtins_open
            io.open = _wrapped_io_open
            subprocess.Popen = _wrapped_popen
            threading.Thread.start = _wrapped_thread_start
            _thread.start_new_thread = _wrapped_thread_start_new_thread
            if _Originals.thread_start_new is not None:
                _thread.start_new = _wrapped_thread_start_new
            os.open = _wrapped_os_open
            os.rename = _wrapped_os_rename
            os.replace = _wrapped_os_replace
            io.FileIO = _WrappedFileIO
            sqlite3.connect = _wrapped_sqlite3_connect
            if _Originals.os_link is not None:
                os.link = _wrapped_os_link
            if _Originals.os_symlink is not None:
                os.symlink = _wrapped_os_symlink

            if _Originals._io_open is not None:
                _io.open = _wrapped__io_open
            if _Originals._io_FileIO is not None:
                _io.FileIO = _Wrapped_io_FileIO
            sqlite3.Connection = _Wrappedsqlite3Connection
            for name, orig in _Originals.os_funcs.items():
                setattr(os, name, _make_os_wrapper(name, orig))
            _global_hooks_active = True
        _active_count += 1


def _restore_global_hooks_internal() -> None:
    global _global_hooks_active
    builtins.open = _Originals.builtins_open
    io.open = _Originals.io_open
    subprocess.Popen = _Originals.popen
    threading.Thread.start = _Originals.thread_start
    _thread.start_new_thread = _Originals.thread_start_new_thread
    if _Originals.thread_start_new is not None:
        _thread.start_new = _Originals.thread_start_new
    os.open = _Originals.os_open
    os.rename = _Originals.os_rename
    os.replace = _Originals.os_replace
    io.FileIO = _Originals.io_FileIO
    sqlite3.connect = _Originals.sqlite3_connect
    if _Originals.os_link is not None:
        os.link = _Originals.os_link
    if _Originals.os_symlink is not None:
        os.symlink = _Originals.os_symlink

    if _Originals._io_open is not None:
        _io.open = _Originals._io_open
    if _Originals._io_FileIO is not None:
        _io.FileIO = _Originals._io_FileIO
    sqlite3.Connection = _Originals.sqlite3_Connection
    for name, orig in _Originals.os_funcs.items():
        setattr(os, name, orig)
    _global_hooks_active = False


def _restore_global_hooks() -> None:
    global _active_count
    with _lock:
        if _active_count > 0:
            _active_count -= 1
            if _active_count == 0 and _active_subthreads_count == 0:
                if _global_hooks_active:
                    _restore_global_hooks_internal()


# ---------------------------------------------------------------------------
# HarnessGuard
# ---------------------------------------------------------------------------

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
        global _shared_temp_dir
        with _shared_temp_dir_lock:
            if _shared_temp_dir is None:
                import tempfile

                _shared_temp_dir = tempfile.mkdtemp(prefix="harness_guard_")
                sitecustomize_path = os.path.join(_shared_temp_dir, "sitecustomize.py")
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
        self._temp_dir = _shared_temp_dir

        # Set environment variables for children to inherit/read
        if os.environ.get("HARNESS_ACTIVE") != "1":
            os.environ["HARNESS_ACTIVE"] = "1"
        new_approved = os.pathsep.join(self.approved_paths)
        if os.environ.get("HARNESS_APPROVED_PATHS") != new_approved:
            os.environ["HARNESS_APPROVED_PATHS"] = new_approved

        # Add this guard to thread-local active guards list
        guards.append(self)

        # Add to global active guards
        with _lock:
            if self not in _global_active_guards:
                _global_active_guards.append(self)

        # Apply global hooks if not already applied
        _apply_global_hooks()
        self._hooks_applied = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool | None:
        # Restore global hooks if they were applied by this guard
        if self._hooks_applied:
            _restore_global_hooks()
            self._hooks_applied = False

        # Remove this guard from thread-local active guards
        guards = _get_active_guards()
        if self in guards:
            guards.remove(self)

        # Remove from global active guards
        with _lock:
            if self in _global_active_guards:
                _global_active_guards.remove(self)

        # Clean up env variables and shared sitecustomize.py temp dir if no more active guards
        remaining = _get_active_guards()
        if not remaining:
            if "HARNESS_ACTIVE" in os.environ:
                os.environ.pop("HARNESS_ACTIVE", None)
            if "HARNESS_APPROVED_PATHS" in os.environ:
                os.environ.pop("HARNESS_APPROVED_PATHS", None)
            global _shared_temp_dir
            with _shared_temp_dir_lock:
                if _shared_temp_dir:
                    import shutil

                    try:
                        shutil.rmtree(_shared_temp_dir, ignore_errors=True)
                    except Exception:
                        pass
                    _shared_temp_dir = None
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
            if abs_path in _path_resolution_cache:
                abs_path = _path_resolution_cache[abs_path]
            else:
                orig_abs_path = abs_path
                # Resolve Windows 8.3 short paths if the path exists
                try:
                    resolved_path = str(pathlib.Path(abs_path).resolve())
                except Exception:
                    resolved_path = os.path.realpath(abs_path)
                abs_path = os.path.normpath(resolved_path)
                _path_resolution_cache[orig_abs_path] = abs_path
        except Exception:
            abs_path = path

        if abs_path in _sensitivity_cache:
            return _sensitivity_cache[abs_path]

        try:
            st = os.stat(abs_path)
            if (st.st_dev, st.st_ino) in _sensitive_inodes:
                _sensitivity_cache[abs_path] = True
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
                _sensitive_inodes.add((st.st_dev, st.st_ino))
            except Exception:
                pass
            _sensitivity_cache[abs_path] = True
            return True

        _sensitivity_cache[abs_path] = False
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
            if cache_key in _abs_path_cache:
                abs_file_path, abs_path = _abs_path_cache[cache_key]
            else:
                abs_file_path = os.path.normcase(os.path.abspath(file_str))
                abs_path = os.path.abspath(file_str)
                _abs_path_cache[cache_key] = (abs_file_path, abs_path)

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

        # 2. Run pytest on the package directory
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
