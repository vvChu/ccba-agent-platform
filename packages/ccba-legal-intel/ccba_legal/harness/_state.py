"""
Shared state and low-level utilities for the harness sub-package.

All monitors (_file_monitor, _sql_monitor, _process_monitor) and the
HarnessGuard orchestrator import from this module. It MUST be imported
before any other harness sub-module, and it MUST NOT import from any of them.

Design note: all mutable globals live here in one place so that there is a
single source of truth for the lock, thread-local, and the active-guard list.
Splitting them across sub-modules would create independent objects and break
the anti-re-entrancy logic in _check_in_hook().
"""

from __future__ import annotations

import _io
import _thread
import builtins
import io
import os
import sqlite3
import subprocess
import sys
import threading
from typing import Any

# ---------------------------------------------------------------------------
# _Originals — capture real stdlib functions before any monkeypatching
# ---------------------------------------------------------------------------


class _Originals:
    """Immutable snapshot of stdlib functions, captured at import time.

    Stored here so that every hook wrapper can call the *real* function
    regardless of the patch state.
    """

    builtins_open = builtins.open
    io_open = io.open
    popen = subprocess.Popen
    thread_start = threading.Thread.start
    os_open = os.open
    os_rename = os.rename
    os_replace = os.replace
    io_FileIO = io.FileIO
    sqlite3_connect = sqlite3.connect
    os_link = getattr(os, "link", None)
    os_symlink = getattr(os, "symlink", None)
    _io_open = getattr(_io, "open", None)
    _io_FileIO = getattr(_io, "FileIO", None)
    sqlite3_Connection = sqlite3.Connection
    thread_start_new_thread = _thread.start_new_thread
    thread_start_new = getattr(_thread, "start_new", None)
    os_funcs: dict[str, Any] = {}


for _name in dir(os):
    if (
        _name == "system"
        or _name.startswith("exec")
        or _name.startswith("spawn")
        or _name in ("posix_spawn", "posix_spawnp")
    ):
        _attr = getattr(os, _name)
        if callable(_attr):
            _Originals.os_funcs[_name] = _attr

# Backward-compat aliases expected by existing test files
_original_builtins_open = _Originals.builtins_open
_original_io_open = _Originals.io_open
_original_popen = _Originals.popen
_original_thread_start = _Originals.thread_start
_original_os_open = _Originals.os_open
_original_os_rename = _Originals.os_rename
_original_os_replace = _Originals.os_replace
_original_io_FileIO = _Originals.io_FileIO
_original_sqlite3_connect = _Originals.sqlite3_connect
_original_os_link = _Originals.os_link
_original_os_symlink = _Originals.os_symlink
_original__io_open = _Originals._io_open
_original__io_FileIO = _Originals._io_FileIO
_original_sqlite3_Connection = _Originals.sqlite3_Connection
_original_os_funcs = _Originals.os_funcs
_original_thread_start_new_thread = _Originals.thread_start_new_thread
_original_thread_start_new = _Originals.thread_start_new


# ---------------------------------------------------------------------------
# Anti-tamper token + HarnessLocal
# ---------------------------------------------------------------------------

_HOOK_TOKEN = object()


class HarnessLocal(threading.local):
    """Thread-local storage with tamper-detection on the ``in_hook`` flag.

    Only code running inside harness sub-modules is allowed to set
    ``in_hook = _HOOK_TOKEN``. Any external attempt is silently ignored,
    preventing re-entrancy bypass attacks.
    """

    def __setattr__(self, name: str, value: object) -> None:
        if name == "in_hook" and value is _HOOK_TOKEN:
            try:
                frame = sys._getframe(1)
                code_obj = frame.f_code
                if code_obj in _caller_code_cache:
                    if not _caller_code_cache[code_obj]:
                        return
                else:
                    co_fn = code_obj.co_filename
                    # Accept any file that belongs to the harness sub-package
                    is_harness = (
                        "harness.py" in co_fn
                        or "harness\\_state" in co_fn
                        or "harness/_state" in co_fn
                        or "harness\\_sql_monitor" in co_fn
                        or "harness/_sql_monitor" in co_fn
                        or "harness\\_file_monitor" in co_fn
                        or "harness/_file_monitor" in co_fn
                        or "harness\\_process_monitor" in co_fn
                        or "harness/_process_monitor" in co_fn
                        or "harness\\guard" in co_fn
                        or "harness/guard" in co_fn
                    )
                    if not is_harness:
                        _caller_code_cache[code_obj] = False
                        return
                    is_own_globals = (
                        frame.f_globals is globals()
                        or frame.f_globals.get("__name__", "").startswith("ccba_legal.harness")
                    )
                    if not is_own_globals:
                        _caller_code_cache[code_obj] = False
                        return
                    _caller_code_cache[code_obj] = True
            except Exception:
                pass
        super().__setattr__(name, value)


# ---------------------------------------------------------------------------
# Process-wide mutable state — single source of truth
# ---------------------------------------------------------------------------

_local = HarnessLocal()
_lock = threading.Lock()
_active_count: int = 0
_audit_hook_registered: bool = False

_global_active_guards: list[Any] = []
_active_subthreads_count: int = 0
_global_hooks_active: bool = False
_sensitive_inodes: set[tuple[int, int]] = set()
_path_resolution_cache: dict[str, str] = {}
_shared_temp_dir: str | None = None
_shared_temp_dir_lock = threading.Lock()
_sensitivity_cache: dict[str, bool] = {}
_abs_path_cache: dict[str, tuple[str, str]] = {}
_caller_code_cache: dict[Any, bool] = {}
_active_guarded_threads: set[int] = set()
_scanned_dirs: set[str] = set()


# ---------------------------------------------------------------------------
# Utility: check re-entrancy
# ---------------------------------------------------------------------------


def _check_in_hook() -> bool:
    """Return True if the current call stack is already inside a harness hook.

    This prevents infinite recursion when hook wrappers call stdlib functions
    that would otherwise trigger more hooks.
    """
    val = getattr(_local, "in_hook", None)
    if val is not _HOOK_TOKEN:
        return False
    try:
        frame = sys._getframe(1)
        while frame:
            co_fn = frame.f_code.co_filename
            is_harness = (
                "harness.py" in co_fn
                or "harness\\_state" in co_fn
                or "harness/_state" in co_fn
                or "harness\\_sql_monitor" in co_fn
                or "harness/_sql_monitor" in co_fn
                or "harness\\_file_monitor" in co_fn
                or "harness/_file_monitor" in co_fn
                or "harness\\_process_monitor" in co_fn
                or "harness/_process_monitor" in co_fn
                or "harness\\guard" in co_fn
                or "harness/guard" in co_fn
            )
            if is_harness:
                is_own_globals = (
                    frame.f_globals is globals()
                    or frame.f_globals.get("__name__", "").startswith("ccba_legal.harness")
                )
                if is_own_globals:
                    return True
            frame = frame.f_back
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Utility: active guard list
# ---------------------------------------------------------------------------


def _get_active_guards() -> list[Any]:
    """Return the active HarnessGuard list for the current thread.

    Falls back to the global guard list when thread-local state is absent
    (e.g., in child threads started before the guard was entered) or when
    the thread-local value is not a genuine ``list`` (tamper protection:
    an attacker may set ``_local.active_guards`` to a FakeList that is
    truthy but iterates over nothing, bypassing file checks).
    """
    if not hasattr(_local, "active_guards"):
        _local.active_guards = []
    active_guards = _local.active_guards
    # CRITICAL security check: reject any non-list substitute.
    # FakeList attacks set __bool__=True and __iter__=[] to sneak past an
    # ordinary `if active_guards:` check while making the for-loop a no-op.
    if type(active_guards) is list and active_guards:
        return active_guards
    with _lock:
        if _global_active_guards:
            return list(_global_active_guards)
    return []



# ---------------------------------------------------------------------------
# Utility: safe bounded iteration
# ---------------------------------------------------------------------------


def _safe_limit_iter(iterable: Any, max_size: int = 1000) -> list:
    """Iterate *iterable* but return at most *max_size* items.

    Never raises — silently truncates or returns [] on any error.
    """
    if iterable is None:
        return []
    res: list = []
    try:
        if isinstance(iterable, (str, bytes, bytearray, dict, set, list, tuple)):
            return list(iterable)[:max_size]
        iterator = iter(iterable)
        for _ in range(max_size):
            try:
                res.append(next(iterator))
            except StopIteration:
                break
    except Exception:
        pass
    return res
