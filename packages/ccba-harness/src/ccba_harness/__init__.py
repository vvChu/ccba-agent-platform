"""CCBA Harness package — public re-export surface.

This file is intentionally a thin wrapper. All implementation lives in
the private sub-modules:

  _engine.py          — shared mutable state, monitors & hook engines
  _guard.py           — HarnessGuard class public interface

All imports below are intentional backward-compatibility re-exports.
"""

# ruff: noqa: F401
from __future__ import annotations

import subprocess

# Re-exports from _engine.py (for backward compatibility)
from ._engine import (
    # shared state
    _HOOK_TOKEN,
    # engine
    HarnessEngine,
    HarnessLocal,
    HarnessState,
    _abs_path_cache,
    _active_count,
    _active_guarded_threads,
    _active_subthreads_count,
    # process monitor utilities & hooks
    _audit_hook,
    _audit_hook_registered,
    _caller_code_cache,
    # sql monitor utilities & hooks
    _check_db_path,
    _check_sql_query,
    _check_subprocess_call,
    _check_subprocess_call_for_guards,
    _check_subprocess_call_internal,
    # file monitor utilities & hooks
    _check_value_for_sensitive,
    _clean_and_decode_db_path,
    _extract_and_check_base64,
    _extract_attached_db_paths,
    _extract_exec_path,
    _extract_subprocess_parts,
    _get_active_guards,
    _get_workspace_files,
    _global_active_guards,
    _global_hooks_active,
    _inject_child_env,
    _is_text_sensitive,
    _local,
    _lock,
    _looks_like_path,
    _make_os_wrapper,
    _normalize_cmd_args,
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
    # originals
    _Originals,
    _path_resolution_cache,
    _reconstruct_shell_variables,
    _safe_escape_decode,
    _safe_record_written_file,
    _scan_ast_nodes,
    _scan_for_sensitive_inodes,
    _scanned_dirs,
    _sensitive_inodes,
    _sensitivity_cache,
    _shared_temp_dir,
    _shared_temp_dir_lock,
    _split_command_to_words,
    _strip_comments_from_sql,
    _wrapped__io_open,
    _wrapped_builtins_open,
    _Wrapped_io_FileIO,
    _wrapped_io_open,
    _wrapped_os_link,
    _wrapped_os_open,
    _wrapped_os_rename,
    _wrapped_os_replace,
    _wrapped_os_symlink,
    _wrapped_popen,
    _wrapped_sqlite3_connect,
    _WrappedCursor,
    _WrappedFileIO,
    _Wrappedsqlite3Connection,
)

# Re-exports from _guard.py
from ._guard import HarnessGuard
from ._mutex import FileMutexLock

__all__ = ["HarnessGuard", "FileMutexLock"]

