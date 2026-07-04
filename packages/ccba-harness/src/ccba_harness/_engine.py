# ruff: noqa: F401
from __future__ import annotations

import _io
import _thread
import ast
import base64
import builtins
import fnmatch
import glob
import io
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import threading
import unicodedata
import urllib.parse
import zlib
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._file_monitor import (
    _check_value_for_sensitive,
    _get_workspace_files,
    _is_text_sensitive,
    _looks_like_path,
    _safe_escape_decode,
    _safe_record_written_file,
    _scan_ast_nodes,
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
    _check_subprocess_call,
    _check_subprocess_call_for_guards,
    _check_subprocess_call_internal,
    _extract_and_check_base64,
    _extract_exec_path,
    _extract_subprocess_parts,
    _inject_child_env,
    _make_os_wrapper,
    _normalize_cmd_args,
    _reconstruct_shell_variables,
    _split_command_to_words,
    _wrapped_popen,
    _wrapped_thread_start,
    _wrapped_thread_start_new,
    _wrapped_thread_start_new_thread,
)
from ._sql_monitor import (
    _check_db_path,
    _check_sql_query,
    _clean_and_decode_db_path,
    _extract_attached_db_paths,
    _strip_comments_from_sql,
    _wrapped_sqlite3_connect,
    _WrappedCursor,
    _Wrappedsqlite3Connection,
)

# Re-exports and orchestration logic for backward compatibility
from ._state import (
    _HOOK_TOKEN,
    HarnessLocal,
    HarnessState,
    _check_in_hook,
    _get_active_guards,
    _local,
    _lock,
    _original__io_FileIO,
    _original__io_open,
    _original_builtins_open,
    _original_io_FileIO,
    _original_io_open,
    _original_os_funcs,
    _original_os_link,
    _original_os_open,
    _original_os_rename,
    _original_os_replace,
    _original_os_symlink,
    _original_popen,
    _original_sqlite3_connect,
    _original_sqlite3_Connection,
    _original_thread_start,
    _original_thread_start_new,
    _original_thread_start_new_thread,
    _Originals,
    _safe_limit_iter,
)


def _audit_hook(event: str, args: tuple[Any, ...]) -> None:
    if event == "sys._getframe":
        return
    if getattr(HarnessState.local, "in_hook", None) is _HOOK_TOKEN:
        return
    guards = _get_active_guards()
    if not guards:
        return
    HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        if event == "open":
            if len(args) > 0:
                path = args[0]
                file_str = (
                    os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else str(path)
                )
                if isinstance(file_str, bytes):
                    file_str = file_str.decode("utf-8", errors="replace")
                for g in guards:
                    if g._is_sensitive(file_str) and not g._is_approved(file_str):
                        raise PermissionError(
                            f"Access to sensitive file blocked by audit hook: {file_str}"
                        )
        elif event in ("ctypes.dlopen", "ctypes.dlsym", "ctypes.call"):
            raise PermissionError(f"{event} is blocked under HarnessGuard")
        elif event in ("os.system", "subprocess.Popen", "os.spawn", "os.exec"):
            cmd_args = None
            env = None
            if event == "os.system":
                cmd_args = args[0]
            elif event == "subprocess.Popen":
                if len(args) > 1:
                    cmd_args = args[1]
                if len(args) > 3:
                    env = args[3]
            elif event == "os.spawn":
                if len(args) > 2:
                    cmd_args = args[2]
                if len(args) > 3:
                    env = args[3]
            elif event == "os.exec":
                if len(args) > 1:
                    cmd_args = args[1]
                if len(args) > 2:
                    env = args[2]
            _check_subprocess_call_for_guards(event, cmd_args, env, guards)
        elif event == "sqlite3.connect":
            if len(args) > 0:
                database = args[0]
                if database is not None:
                    db_str = (
                        os.fspath(database)
                        if isinstance(database, (str, bytes, os.PathLike))
                        else str(database)
                    )
                    if isinstance(db_str, bytes):
                        db_str = db_str.decode("utf-8", errors="replace")
                    if db_str != ":memory:" and db_str.lower() != ":memory:":
                        decoded = _clean_and_decode_db_path(db_str)
                        for g in guards:
                            if g._is_sensitive(decoded) and not g._is_approved(decoded):
                                raise PermissionError(
                                    f"Access to sensitive database blocked by audit hook: {db_str}"
                                )
        elif event in ("os.link", "os.symlink", "os.rename"):
            if len(args) > 1:
                src = args[0]
                dst = args[1]
                src_str = os.fspath(src) if isinstance(src, (str, bytes, os.PathLike)) else str(src)
                dst_str = os.fspath(dst) if isinstance(dst, (str, bytes, os.PathLike)) else str(dst)
                if isinstance(src_str, bytes):
                    src_str = src_str.decode("utf-8", errors="replace")
                if isinstance(dst_str, bytes):
                    dst_str = dst_str.decode("utf-8", errors="replace")
                for g in guards:
                    if g._is_sensitive(src_str) and not g._is_approved(src_str):
                        raise PermissionError(
                            f"Access to sensitive file blocked by audit hook: {src_str}"
                        )
                    if g._is_sensitive(dst_str) and not g._is_approved(dst_str):
                        raise PermissionError(
                            f"Access to sensitive file blocked by audit hook: {dst_str}"
                        )
    finally:
        HarnessState.local.__dict__["in_hook"] = None


class HarnessEngine:
    """Orchestrator for managing global system hooks and monkey patches."""

    @staticmethod
    def activate() -> None:
        """Register the audit hook and apply all global monkey patches."""
        with HarnessState.lock:
            if not HarnessState.audit_hook_registered:
                sys.addaudithook(_audit_hook)
                HarnessState.audit_hook_registered = True

            if not HarnessState.global_hooks_active:
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
                HarnessState.global_hooks_active = True
            HarnessState.active_count += 1

    @staticmethod
    def deactivate() -> None:
        """Decrement active guard count and restore original stdlib functions when no guards remain."""
        with HarnessState.lock:
            if HarnessState.active_count > 0:
                HarnessState.active_count -= 1
                if HarnessState.active_count == 0 and HarnessState.active_subthreads_count == 0:
                    if HarnessState.global_hooks_active:
                        HarnessEngine._restore_global_hooks_internal()

    @staticmethod
    def _restore_global_hooks_internal() -> None:
        """Internal helper to force restore stdlib hooks."""
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
        HarnessState.global_hooks_active = False


# Dynamic attribute resolution for backward compatibility with direct module imports
def __getattr__(name: str) -> Any:
    if name == "_active_count":
        return HarnessState.active_count
    if name == "_active_subthreads_count":
        return HarnessState.active_subthreads_count
    if name == "_global_hooks_active":
        return HarnessState.global_hooks_active
    if name == "_global_active_guards":
        return HarnessState.global_active_guards
    if name == "_sensitive_inodes":
        return HarnessState.sensitive_inodes
    if name == "_path_resolution_cache":
        return HarnessState.path_resolution_cache
    if name == "_shared_temp_dir":
        return HarnessState.shared_temp_dir
    if name == "_shared_temp_dir_lock":
        return HarnessState.shared_temp_dir_lock
    if name == "_sensitivity_cache":
        return HarnessState.sensitivity_cache
    if name == "_abs_path_cache":
        return HarnessState.abs_path_cache
    if name == "_caller_code_cache":
        return HarnessState.caller_code_cache
    if name == "_active_guarded_threads":
        return HarnessState.active_guarded_threads
    if name == "_scanned_dirs":
        return HarnessState.scanned_dirs
    if name == "_audit_hook_registered":
        return HarnessState.audit_hook_registered
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
