"""Subprocess security inspection and obfuscation guard checks for HarnessGuard."""

from __future__ import annotations

import ast
import fnmatch
import glob
import os
import re
import subprocess
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._guard import HarnessGuard

from ._file_monitor import (
    _check_value_for_sensitive,
    _get_workspace_files,
    _looks_like_path,
    _scan_ast_nodes,
)
from ._proc_shell_parser import (
    _extract_exec_path,
    _extract_subprocess_parts,
    _normalize_cmd_args,
    _reconstruct_shell_variables,
    _split_command_to_words,
)
from ._state import _get_active_guards

_PYTHON_NAME_RE = re.compile(r"^(python[\d\.]*w?|pyw?[\d\.]*)$")
_INTERPRETERS = ("python", "sh", "bash", "cmd", "powershell", "pwsh", "zsh", "ash", "dash")
_SHELL_INTERPRETERS = ("cmd", "powershell", "pwsh", "sh", "bash", "zsh", "ash", "dash")


def _is_python_cmd_name(cmd: str) -> bool:
    """Return True if a command name refers to a Python interpreter binary."""
    base = os.path.basename(cmd.replace("^", "").lower())
    if base.endswith(".exe"):
        base = base[:-4]
    return bool(_PYTHON_NAME_RE.match(base))


def _resolve_candidate_exe(path: str) -> str:
    """Resolve bare command names via cwd or PATH into a candidate file path."""
    path_clean = path.replace("^", "").strip()
    if (path_clean.startswith('"') and path_clean.endswith('"')) or (
        path_clean.startswith("'") and path_clean.endswith("'")
    ):
        path_clean = path_clean[1:-1]
    if os.path.isabs(path_clean) or os.path.isfile(path_clean):
        return path_clean
    for p in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(p, path_clean)
        if os.path.isfile(candidate):
            return candidate
    return path_clean


def _is_copied_python_executable(path: str, *, deep_inspect: bool = False) -> bool:
    """Return True if an arbitrary executable path appears to be a copied Python binary."""
    try:
        actual_path = _resolve_candidate_exe(path)
        if not os.path.isfile(actual_path):
            return False
        size_diff = abs(os.path.getsize(actual_path) - os.path.getsize(sys.executable))
        if size_diff >= 1024 * 1024:
            return False
        if deep_inspect:
            with open(actual_path, "rb") as f1, open(sys.executable, "rb") as f2:
                if f1.read(1024) == f2.read(1024):
                    return True
        with open(actual_path, "rb") as f:
            data = f.read(65536).lower()
        return b"python" in data or (deep_inspect and b"cpy" in data)
    except Exception:
        return False


def _assert_not_written_during_guard(
    candidate_path: str, label: str, guards: list[HarnessGuard]
) -> None:
    """Block execution of files newly written while an active HarnessGuard is open."""
    abs_target = os.path.normcase(os.path.abspath(candidate_path))
    for g in guards:
        lock = getattr(g, "_write_lock", None)
        if lock:
            with lock:
                in_written = hasattr(g, "_written_files") and abs_target in g._written_files
        else:
            in_written = hasattr(g, "_written_files") and abs_target in g._written_files
        if in_written:
            raise PermissionError(f"Execution of written file during guard is blocked: {label}")


def _check_exec_path_and_stdin(
    cmd_args: Any, exec_path: Any, stdin: Any, guards: list[HarnessGuard]
) -> str:
    """Validate executable sensitivity and block piping stdin directly into interpreters."""
    exec_str = ""
    if exec_path is not None:
        try:
            raw_exec = os.fspath(exec_path)
        except Exception:
            raw_exec = str(exec_path)
        exec_str = (
            raw_exec.decode("utf-8", errors="replace") if isinstance(raw_exec, bytes) else raw_exec
        ).replace("^", "")
        for g in guards:
            if g._is_sensitive(exec_str) and not g._is_approved(exec_str):
                raise PermissionError(f"Access to sensitive file blocked in subprocess: {exec_str}")

    if stdin is not None and stdin != subprocess.DEVNULL:
        cmd_name = ""
        if exec_path is not None:
            cmd_name = os.path.basename(str(exec_path)).lower()
        elif cmd_args:
            args_list = _normalize_cmd_args(cmd_args)
            if args_list:
                first = args_list[0]
                words = (
                    _split_command_to_words(first)
                    if isinstance(cmd_args, (str, bytes))
                    else [first]
                )
                if words:
                    cmd_name = os.path.basename(words[0]).lower()
        if any(interp in cmd_name for interp in _INTERPRETERS):
            raise PermissionError(
                f"Piping stdin to interpreter '{cmd_name}' is blocked under HarnessGuard"
            )
    return exec_str


def _check_redirection_and_written_targets(
    normalized_args: list[str], exec_str: str, guards: list[HarnessGuard]
) -> None:
    """Block shell redirection combined with interpreters and execution of written files."""
    joined_lower = " ".join(arg.replace("^", "") for arg in normalized_args).lower()
    has_redirection = ">" in joined_lower or "|" in joined_lower or "<" in joined_lower
    interp_pat = r"\b(python\d*|cmd|bash|sh|powershell|pwsh|zsh|ash|dash)(?:\.exe)?\b"
    if has_redirection and re.search(interp_pat, joined_lower) is not None:
        raise PermissionError(
            "Shell redirection combined with interpreter execution is blocked under HarnessGuard"
        )
    for arg_str in normalized_args:
        cleaned = arg_str.replace("^", "")
        try:
            _assert_not_written_during_guard(cleaned, arg_str, guards)
        except PermissionError:
            raise
        except Exception:
            pass
        try:
            for word in _split_command_to_words(cleaned):
                _assert_not_written_during_guard(word, word, guards)
        except PermissionError:
            raise
        except Exception:
            pass
    if exec_str:
        try:
            _assert_not_written_during_guard(exec_str.replace("^", ""), exec_str, guards)
        except PermissionError:
            raise
        except Exception:
            pass


def _resolve_python_cmd_info(
    normalized_args: list[str], exec_str: str, cmd_args: Any
) -> tuple[str, bool, list[str] | None]:
    """Identify primary target command, whether Python is invoked, and mock `sys.argv`."""
    target_cmd = exec_str
    if not target_cmd and normalized_args:
        words = _split_command_to_words(normalized_args[0])
        if words:
            target_cmd = words[0]

    is_python = bool(
        target_cmd
        and (
            _is_python_cmd_name(target_cmd)
            or _is_copied_python_executable(target_cmd, deep_inspect=True)
        )
    )
    if not is_python and normalized_args:
        is_python = any(_is_python_cmd_name(arg) for arg in normalized_args)

    sys_argv_mock: list[str] | None = None
    if is_python and isinstance(cmd_args, list):
        try:
            idx_c = next((idx for idx, arg in enumerate(cmd_args) if arg == "-c"), -1)
            sys_argv_mock = ["-c", *cmd_args[idx_c + 2 :]] if idx_c != -1 else list(cmd_args[1:])
        except Exception:
            pass
    return target_cmd, is_python, sys_argv_mock


def _assert_python_args_safe(normalized_args: list[str]) -> None:
    """Block dynamic string reconstruction and obfuscation idioms in Python `-c` args."""
    blocked_lib = r"\b(reduce|functools|codecs|rot_13|rot13|rot-13|zlib|gzip|bz2|lzma|zipfile|tarfile|pickle|marshal)\b"
    for arg_str in normalized_args:
        clean = arg_str.replace("^", "")
        if re.search(blocked_lib, clean, re.IGNORECASE):
            raise PermissionError(
                f"Blocked library or function detected in python subprocess: {clean}"
            )
        if re.search(r"\[.*for.*in.*\]", clean):
            raise PermissionError(
                "List comprehension in python subprocess is blocked under HarnessGuard"
            )
        if re.search(r"\bfor\b", clean) or re.search(r"\bwhile\b", clean):
            raise PermissionError("Loop pattern in python subprocess is blocked under HarnessGuard")
        if re.search(r"\[[^\]]*:[^\]]*:[^\]]*\]", clean) or "::" in clean:
            raise PermissionError(
                "String slice with step in python subprocess is blocked under HarnessGuard"
            )
        if re.search(r"\.join\s*\(", clean) or re.search(r"\.replace\s*\(", clean):
            raise PermissionError(
                "Calling join/replace in python subprocess is blocked under HarnessGuard"
            )
        if re.search(r"\bgetattr\b", clean) and (
            re.search(r"['\"]replace['\"]", clean) or re.search(r"['\"]join['\"]", clean)
        ):
            raise PermissionError(
                "Calling getattr for join/replace in python subprocess is blocked under HarnessGuard"
            )
        if any(re.search(pat, clean) for pat in (r"\.format\s*\(", r"%\s*\(", r"%\s*\'", r'%\s*"')):
            raise PermissionError(
                "String formatting in python subprocess is blocked under HarnessGuard"
            )


def _scan_arg_ast_for_sensitive(
    arg_str: str,
    target_env: dict[str, str],
    sys_argv_mock: list[str] | None,
    guards: list[HarnessGuard],
) -> bool:
    """Parse `arg_str` as Python AST and scan reconstructed values; return True if parsed."""
    try:
        tree = ast.parse(arg_str)
        strs, bytes_list = _scan_ast_nodes(tree, target_env=target_env, sys_argv_mock=sys_argv_mock)
        for s in strs:
            _check_value_for_sensitive(s, guards)
            _check_value_for_sensitive(s.replace("^", ""), guards)
        for b in bytes_list:
            _check_value_for_sensitive(b, guards)
        if strs:
            concat_str = "".join(strs)
            _check_value_for_sensitive(concat_str, guards)
            _check_value_for_sensitive(concat_str.replace("^", ""), guards)
        if bytes_list:
            _check_value_for_sensitive(b"".join(bytes_list), guards)
        return True
    except PermissionError as pe:
        raise PermissionError(f"Access to sensitive file blocked in subprocess: {pe}") from pe
    except Exception:
        return False


def _scan_arg_words_and_globs(
    arg_str: str, workspace_files: list[str], guards: list[HarnessGuard]
) -> None:
    """Scan tokenized words and wildcard expansions in a subprocess argument."""
    for word in _split_command_to_words(arg_str):
        normalized_word = word.replace("'", "").replace('"', "")
        for g in guards:
            if g._is_sensitive(normalized_word) and not g._is_approved(normalized_word):
                raise PermissionError(f"Access to sensitive file blocked in subprocess: {arg_str}")
        if not any(ch in word for ch in ("*", "?", "[", "]")):
            continue
        try:
            for matched in glob.glob(word, recursive=True):
                for g in guards:
                    if g._is_sensitive(matched) and not g._is_approved(matched):
                        raise PermissionError(
                            f"Access to sensitive file blocked by wildcard expansion: {matched}"
                        )
        except Exception:
            pass
        try:
            for w_file in workspace_files:
                if fnmatch.fnmatch(w_file, word) or fnmatch.fnmatch(os.path.basename(w_file), word):
                    for g in guards:
                        if g._is_sensitive(w_file) and not g._is_approved(w_file):
                            raise PermissionError(
                                f"Access to sensitive file blocked by wildcard match: {w_file}"
                            )
        except Exception:
            pass


def _decode_env_val(val: Any) -> str:
    """Safely convert an env value into a decoded string."""
    try:
        raw = os.fspath(val)
    except Exception:
        raw = str(val)
    return raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw


def _check_subprocess_env_vars(env: Any, guards: list[HarnessGuard]) -> None:
    """Check modified subprocess environment variables individually and concatenated."""
    if env is None:
        return
    snapshot = guards[-1]._env_snapshot if hasattr(guards[-1], "_env_snapshot") else {}
    modified_keys = sorted(k for k in env if k not in snapshot or env[k] != snapshot[k])
    sorted_values = [_decode_env_val(env[k]) for k in modified_keys if env[k] is not None]
    if sorted_values:
        for combined in (" ".join(sorted_values), "".join(sorted_values)):
            try:
                _check_value_for_sensitive(combined, guards)
            except PermissionError as pe:
                raise PermissionError(
                    f"Access to sensitive path blocked via split env variable reconstruction: {pe}"
                ) from pe
    for val_str in sorted_values:
        try:
            _check_value_for_sensitive(val_str, guards)
        except PermissionError as pe:
            raise PermissionError(
                f"Access to sensitive path blocked in subprocess env: {pe}"
            ) from pe
        parts = [
            sub
            for p in (val_str.split(os.path.sep) if os.path.sep in val_str else [val_str])
            for sub in (p.split(os.pathsep) if os.pathsep in p else [p])
        ]
        for part in parts:
            if _looks_like_path(part):
                for g in guards:
                    if g._is_sensitive(part) and not g._is_approved(part):
                        raise PermissionError(
                            f"Access to sensitive path blocked in subprocess env: {part}"
                        )


def _scan_normalized_args(
    normalized_args: list[str],
    env: Any,
    sys_argv_mock: list[str] | None,
    guards: list[HarnessGuard],
) -> bool:
    """Scan normalized args for obfuscation, reconstructed shell vars, ASTs, and globs."""
    has_wildcard = any(any(ch in arg for ch in ("*", "?", "[", "]")) for arg in normalized_args)
    workspace_files = _get_workspace_files() if has_wildcard else []
    target_env: dict[str, str] = dict(env) if env is not None else dict(os.environ)
    ast_success = bool(normalized_args)

    for arg_str in normalized_args:
        arg_clean = arg_str.replace("^", "")
        try:
            _check_value_for_sensitive(arg_clean, guards)
            reconstructed = _reconstruct_shell_variables(arg_clean)
            if reconstructed != arg_clean:
                _check_value_for_sensitive(reconstructed, guards)
        except PermissionError as pe:
            raise PermissionError(f"Access to sensitive file blocked in subprocess: {pe}") from pe
        except Exception:
            pass
        if not _scan_arg_ast_for_sensitive(arg_str, target_env, sys_argv_mock, guards):
            ast_success = False
        _scan_arg_words_and_globs(arg_str, workspace_files, guards)

    if len(normalized_args) > 1:
        for combined in (
            " ".join(normalized_args).replace("^", ""),
            "".join(normalized_args).replace("^", ""),
        ):
            try:
                _check_value_for_sensitive(combined, guards)
            except PermissionError as pe:
                raise PermissionError(
                    f"Access to sensitive file blocked in subprocess via split-argument reconstruction: {pe}"
                ) from pe
    return ast_success


def _check_subprocess_call_internal(
    cmd_args: Any, env: Any, stdin: Any, exec_path: Any, guards: list[HarnessGuard]
) -> None:
    """Run full multi-layer security inspection before allowing subprocess execution."""
    if not guards:
        return
    exec_str = _check_exec_path_and_stdin(cmd_args, exec_path, stdin, guards)
    normalized_args = _normalize_cmd_args(cmd_args)
    _check_redirection_and_written_targets(normalized_args, exec_str, guards)

    target_cmd, is_python, sys_argv_mock = _resolve_python_cmd_info(
        normalized_args, exec_str, cmd_args
    )
    if is_python:
        _assert_python_args_safe(normalized_args)

    ast_success = _scan_normalized_args(normalized_args, env, sys_argv_mock, guards)
    _check_subprocess_env_vars(env, guards)
    is_shell = (
        bool(target_cmd)
        and any(sh in os.path.basename(target_cmd.lower()) for sh in _SHELL_INTERPRETERS)
    ) or any(
        any(sh in os.path.basename(arg.lower()) for sh in _SHELL_INTERPRETERS)
        for arg in normalized_args
    )
    if is_shell and not ast_success:
        try:
            _check_value_for_sensitive(" ".join(normalized_args).replace("^", ""), guards)
        except PermissionError as pe:
            raise PermissionError(f"Access to sensitive file blocked in subprocess: {pe}") from pe


def _check_subprocess_call_for_guards(
    event: str, cmd_args: Any, env: Any, guards: list[HarnessGuard]
) -> None:
    """Invoke subprocess guard validation from audit-hook event handlers."""
    del event
    _check_subprocess_call_internal(
        cmd_args=cmd_args, env=env, stdin=None, exec_path=None, guards=guards
    )


def _check_subprocess_call(name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
    """Validate subprocess/os spawn call when at least one HarnessGuard is active."""
    guards = _get_active_guards()
    if not guards:
        return
    exec_path = _extract_exec_path(name, args, kwargs)
    cmd_args, env = _extract_subprocess_parts(name, args, kwargs)
    _check_subprocess_call_internal(cmd_args, env, kwargs.get("stdin"), exec_path, guards)
