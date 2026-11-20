"""Thin process & multi-threading monitor facade for HarnessGuard."""

from __future__ import annotations

from ._proc_guard_checks import (
    _check_subprocess_call,
    _check_subprocess_call_for_guards,
    _check_subprocess_call_internal,
)
from ._proc_shell_parser import (
    _extract_and_check_base64,
    _extract_exec_path,
    _extract_subprocess_parts,
    _normalize_cmd_args,
    _reconstruct_shell_variables,
    _split_command_to_words,
)
from ._proc_wrappers import (
    _inject_child_env,
    _make_os_wrapper,
    _wrapped_popen,
    _wrapped_thread_start,
    _wrapped_thread_start_new,
    _wrapped_thread_start_new_thread,
)
from ._state import _Originals

__all__ = [
    "_Originals",
    "_check_subprocess_call",
    "_check_subprocess_call_for_guards",
    "_check_subprocess_call_internal",
    "_extract_and_check_base64",
    "_extract_exec_path",
    "_extract_subprocess_parts",
    "_inject_child_env",
    "_make_os_wrapper",
    "_normalize_cmd_args",
    "_reconstruct_shell_variables",
    "_split_command_to_words",
    "_wrapped_popen",
    "_wrapped_thread_start",
    "_wrapped_thread_start_new",
    "_wrapped_thread_start_new_thread",
]
