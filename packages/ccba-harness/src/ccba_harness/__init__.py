"""CCBA Harness package — public re-export surface.

This file is intentionally a thin wrapper. All implementation lives in
the private sub-modules:

  _state.py          — shared mutable state (counters, caches, originals)
  _sql_monitor.py    — SQLite connection/query interception
  _file_monitor.py   — file-open hooks, AST scanning, inode tracking
  _process_monitor.py— subprocess & OS-call monitoring
  _guard.py          — HarnessGuard class, global hook installation

All imports below are intentional backward-compatibility re-exports.
"""
# ruff: noqa: F401
from __future__ import annotations

# NOTE: 'subprocess' is intentionally re-exported so that tests can mock
# 'ccba_harness.subprocess.run' (used in HarnessGuard._run_post_action_checks).
# Since Python modules are singletons, patching via this alias affects the
# same module object referenced in _guard.py.
import subprocess

# ---------------------------------------------------------------------------
# Step 3: file monitor
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Step 5: guard class + hook management
# ---------------------------------------------------------------------------
from ._guard import (
    HarnessGuard,
    _apply_global_hooks,
    _restore_global_hooks,
    _restore_global_hooks_internal,
    _wrapped_thread_start,
    _wrapped_thread_start_new,
    _wrapped_thread_start_new_thread,
)

# ---------------------------------------------------------------------------
# Step 4: process monitor
# ---------------------------------------------------------------------------
from ._process_monitor import (
    _audit_hook,
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
)

# ---------------------------------------------------------------------------
# Step 2: SQL monitor
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Step 1: shared state
# ---------------------------------------------------------------------------
from ._state import (
    _HOOK_TOKEN,
    HarnessLocal,
    _abs_path_cache,
    _active_count,
    _active_guarded_threads,
    _active_subthreads_count,
    _audit_hook_registered,
    _caller_code_cache,
    _check_in_hook,
    _get_active_guards,
    _global_active_guards,
    _global_hooks_active,
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
    _path_resolution_cache,
    _safe_limit_iter,
    _scanned_dirs,
    _sensitive_inodes,
    _sensitivity_cache,
    _shared_temp_dir,
    _shared_temp_dir_lock,
)

__all__ = ["HarnessGuard"]
