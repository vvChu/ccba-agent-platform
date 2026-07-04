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


from ._state import (
    HarnessState,
    _Originals,
    _check_in_hook,
    _get_active_guards,
    _safe_limit_iter,
    _HOOK_TOKEN,
    _lock,
    _local,
    _original_builtins_open,
    _original_io_open,
    _original_popen,
    _original_thread_start,
    _original_os_open,
    _original_os_rename,
    _original_os_replace,
    _original_io_FileIO,
    _original_sqlite3_connect,
    _original_os_link,
    _original_os_symlink,
    _original__io_open,
    _original__io_FileIO,
    _original_sqlite3_Connection,
    _original_os_funcs,
    _original_thread_start_new_thread,
    _original_thread_start_new,
)
from ._file_monitor import (
    _check_value_for_sensitive,
    _get_workspace_files,
    _scan_ast_nodes,
)

# PROCESS MONITORING UTILITIES
# ===========================================================================
def _split_command_to_words(cmd_str: str) -> list[str]:
    try:
        return shlex.split(cmd_str, posix=(sys.platform != "win32"))
    except Exception:
        return cmd_str.split()


def _reconstruct_shell_variables(cmd_str: str) -> str:
    is_windows = sys.platform == "win32"
    vars_dict = {}

    stripped = cmd_str.strip()
    pattern = r'(?i)^(?:cmd(?:\.exe)?(?:\s+[\/\-][a-zA-Z]+)*\s+[\/\-][ckq]\s*|sh\s+\-c\s*|bash\s+\-c\s*|zsh\s+\-c\s*|ash\s+\-c\s*|dash\s+\-c\s*|powershell\s+\-c\s*|pwsh\s+\-c\s*)(["\'])(.*)\1\s*$'
    m = re.match(pattern, stripped)
    if m:
        stripped = m.group(2)

    for _ in range(5):
        new_stripped = re.sub(r"(['\"])(.*?)\1\s*\+\s*(['\"])(.*?)\3", r"\1\2\4\1", stripped)
        if new_stripped == stripped:
            break
        stripped = new_stripped

    commands = []
    current = []
    in_dquote = False
    in_squote = False
    escape = False
    i = 0
    n = len(stripped)
    while i < n:
        char = stripped[i]
        if escape:
            current.append(char)
            escape = False
            i += 1
            continue

        if char == "\\" and not is_windows and not in_squote:
            escape = True
            current.append(char)
            i += 1
            continue

        if char == "^" and is_windows and not in_squote and not in_dquote:
            escape = True
            current.append(char)
            i += 1
            continue

        if char == '"' and not in_squote:
            in_dquote = not in_dquote
            current.append(char)
            i += 1
            continue

        if char == "'" and not in_dquote:
            in_squote = not in_squote
            current.append(char)
            i += 1
            continue

        if not in_dquote and not in_squote:
            if char == "&" and i + 1 < n and stripped[i + 1] == "&":
                commands.append("".join(current))
                current = []
                i += 2
                continue
            elif char == "|" and i + 1 < n and stripped[i + 1] == "|":
                commands.append("".join(current))
                current = []
                i += 2
                continue
            elif char in (";", "&", "\n"):
                commands.append("".join(current))
                current = []
                i += 1
                continue

        current.append(char)
        i += 1

    if current:
        commands.append("".join(current))

    for cmd in commands:
        cmd_clean = cmd.strip()
        if cmd_clean.startswith("$"):
            cmd_clean = cmd_clean[1:]
        if not cmd_clean:
            continue

        if cmd_clean.lower().startswith("set "):
            content = cmd_clean[4:].strip()
            quoted_match = re.match(r'^"([^=]+)=(.*)"$', content)
            if quoted_match:
                var = quoted_match.group(1).strip()
                val = quoted_match.group(2)
                if is_windows:
                    var = var.replace("^", "")
                    val = val.replace("^", "")
                vars_dict[var] = val
                continue
            unquoted_match = re.match(r"^([^=]+)=(.*)$", content)
            if unquoted_match:
                var = unquoted_match.group(1).strip()
                val = unquoted_match.group(2)
                if is_windows:
                    var = var.replace("^", "")
                    val = val.replace("^", "")
                if val.count('"') % 2 != 0:
                    val = val.rstrip('"')
                vars_dict[var] = val
                continue

        assign_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(?:(["\'])(.*?)\2|([^"\'].*|))$', cmd_clean)
        if assign_match:
            var = assign_match.group(1).strip()
            if var.lower() not in ("set", "export"):
                val = assign_match.group(3) if assign_match.group(2) else assign_match.group(4)
                if is_windows:
                    var = var.replace("^", "")
                    val = val.replace("^", "")
                vars_dict[var] = val

    reconstructed = cmd_str
    for _ in range(5):
        orig_reconstructed = reconstructed

        def replace_delayed(m):
            var_name = m.group(1)
            val = None
            for k, v in vars_dict.items():
                if k.lower() == var_name.lower():
                    val = v
                    break
            if val is None:
                return m.group(0)

            if m.group(4) is not None:
                str1 = m.group(4)
                str2 = m.group(5) or ""
                if str1.startswith("*"):
                    target = str1[1:]
                    idx = val.lower().find(target.lower())
                    if idx != -1:
                        return str2 + val[idx + len(target) :]
                    else:
                        return val
                else:
                    return re.sub(re.escape(str1), lambda match_obj: str2, val, flags=re.IGNORECASE)

            start_str = m.group(2)
            len_str = m.group(3)
            if start_str is not None:
                start = int(start_str)
                if len_str is not None:
                    length = int(len_str)
                    if length >= 0:
                        return val[start : start + length]
                    else:
                        return val[start:length]
                else:
                    return val[start:]
            return val

        reconstructed = re.sub(
            r"!(\w+)(?:(?:~(-?\d+)(?:,(-?\d+))?)|(?::([^=!]+)=([^!]*)))!",
            replace_delayed,
            reconstructed,
            flags=re.IGNORECASE,
        )

        def replace_pct(m):
            var_name = m.group(1)
            val = None
            for k, v in vars_dict.items():
                if k.lower() == var_name.lower():
                    val = v
                    break
            if val is None:
                return m.group(0)

            if m.group(4) is not None:
                str1 = m.group(4)
                str2 = m.group(5) or ""
                if str1.startswith("*"):
                    target = str1[1:]
                    idx = val.lower().find(target.lower())
                    if idx != -1:
                        return str2 + val[idx + len(target) :]
                    else:
                        return val
                else:
                    return re.sub(re.escape(str1), lambda match_obj: str2, val, flags=re.IGNORECASE)

            start_str = m.group(2)
            len_str = m.group(3)
            if start_str is not None:
                start = int(start_str)
                if len_str is not None:
                    length = int(len_str)
                    if length >= 0:
                        return val[start : start + length]
                    else:
                        return val[start:length]
                else:
                    return val[start:]
            return val

        reconstructed = re.sub(
            r"%(\w+)(?:(?:~(-?\d+)(?:,(-?\d+))?)|(?::([^=%]+)=([^%]*)))?%",
            replace_pct,
            reconstructed,
            flags=re.IGNORECASE,
        )

        def replace_unix(m):
            var_name = m.group(1)
            val = vars_dict.get(var_name)
            if val is None:
                return m.group(0)

            start_str = m.group(2)
            len_str = m.group(3)
            if start_str is not None:
                start = int(start_str)
                if len_str is not None:
                    length = int(len_str)
                    if length >= 0:
                        return val[start : start + length]
                    else:
                        return val[start:length]
                else:
                    return val[start:]
            return val

        reconstructed = re.sub(
            r"\$\{(\w+)(?::(\-?\d+)(?::(\-?\d+))?)?\}", replace_unix, reconstructed
        )

        for var, val in vars_dict.items():
            reconstructed = re.sub(rf"\${var}\b", lambda m, val=val: val, reconstructed)

        if reconstructed == orig_reconstructed:
            break

    return reconstructed


def _check_subprocess_call_internal(
    cmd_args: Any, env: Any, stdin: Any, exec_path: Any, guards: list[HarnessGuard]
) -> None:
    if not guards:
        return

    exec_str = ""
    if exec_path is not None:
        try:
            exec_str = os.fspath(exec_path)
        except Exception:
            exec_str = str(exec_path)
        if isinstance(exec_str, bytes):
            exec_str = exec_str.decode("utf-8", errors="replace")

    if exec_str:
        exec_str = exec_str.replace("^", "")

    if exec_str:
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
                first_arg = args_list[0]
                if isinstance(cmd_args, (str, bytes)):
                    words = _split_command_to_words(first_arg)
                    if words:
                        cmd_name = os.path.basename(words[0]).lower()
                else:
                    cmd_name = os.path.basename(first_arg).lower()

        interpreters = ("python", "sh", "bash", "cmd", "powershell", "pwsh", "zsh", "ash", "dash")
        if any(interp in cmd_name for interp in interpreters):
            raise PermissionError(
                f"Piping stdin to interpreter '{cmd_name}' is blocked under HarnessGuard"
            )

    normalized_args = _normalize_cmd_args(cmd_args)

    joined_cmd_lower = " ".join(arg.replace("^", "") for arg in normalized_args).lower()
    has_redirection = ">" in joined_cmd_lower or "|" in joined_cmd_lower or "<" in joined_cmd_lower
    interpreters_pattern = r"\b(python\d*|cmd|bash|sh|powershell|pwsh|zsh|ash|dash)(?:\.exe)?\b"
    has_interpreter = re.search(interpreters_pattern, joined_cmd_lower) is not None
    if has_redirection and has_interpreter:
        raise PermissionError(
            "Shell redirection combined with interpreter execution is blocked under HarnessGuard"
        )

    for arg_str in normalized_args:
        arg_str_clean = arg_str.replace("^", "")
        try:
            abs_arg = os.path.normcase(os.path.abspath(arg_str_clean))
            for g in guards:
                lock = getattr(g, "_write_lock", None)
                in_written = False
                if lock:
                    with lock:
                        if hasattr(g, "_written_files"):
                            in_written = abs_arg in g._written_files
                else:
                    if hasattr(g, "_written_files"):
                        in_written = abs_arg in g._written_files
                if in_written:
                    raise PermissionError(
                        f"Execution of written file during guard is blocked: {arg_str}"
                    )
        except PermissionError:
            raise
        except Exception:
            pass

        try:
            words = _split_command_to_words(arg_str_clean)
            for w in words:
                abs_w = os.path.normcase(os.path.abspath(w))
                for g in guards:
                    lock = getattr(g, "_write_lock", None)
                    in_written = False
                    if lock:
                        with lock:
                            if hasattr(g, "_written_files"):
                                in_written = abs_w in g._written_files
                    else:
                        if hasattr(g, "_written_files"):
                            in_written = abs_w in g._written_files
                    if in_written:
                        raise PermissionError(
                            f"Execution of written file during guard is blocked: {w}"
                        )
        except PermissionError:
            raise
        except Exception:
            pass

    if exec_str:
        exec_str_clean = exec_str.replace("^", "")
        try:
            abs_exec = os.path.normcase(os.path.abspath(exec_str_clean))
            for g in guards:
                lock = getattr(g, "_write_lock", None)
                in_written = False
                if lock:
                    with lock:
                        if hasattr(g, "_written_files"):
                            in_written = abs_exec in g._written_files
                else:
                    if hasattr(g, "_written_files"):
                        in_written = abs_exec in g._written_files
                if in_written:
                    raise PermissionError(
                        f"Execution of written file during guard is blocked: {exec_str}"
                    )
        except PermissionError:
            raise
        except Exception:
            pass

    def _is_python_cmd_name(cmd: str) -> bool:
        cmd_clean = cmd.replace("^", "").lower()
        base = os.path.basename(cmd_clean)
        if base.endswith(".exe"):
            base = base[:-4]
        if re.match(r"^(python[\d\.]*w?|pyw?[\d\.]*)$", base):
            return True
        return False

    def _is_copied_python_executable(path: str) -> bool:
        try:
            path_clean = path.replace("^", "").strip()
            if (path_clean.startswith('"') and path_clean.endswith('"')) or (
                path_clean.startswith("'") and path_clean.endswith("'")
            ):
                path_clean = path_clean[1:-1]
            actual_path = path_clean
            if not os.path.isabs(path_clean):
                if os.path.isfile(path_clean):
                    actual_path = path_clean
                else:
                    for p in os.environ.get("PATH", "").split(os.pathsep):
                        candidate = os.path.join(p, path_clean)
                        if os.path.isfile(candidate):
                            actual_path = candidate
                            break
            if os.path.isfile(actual_path):
                size_diff = abs(os.path.getsize(actual_path) - os.path.getsize(sys.executable))
                if size_diff < 1024 * 1024:
                    with open(actual_path, "rb") as f1, open(sys.executable, "rb") as f2:
                        if f1.read(1024) == f2.read(1024):
                            return True
                    with open(actual_path, "rb") as f:
                        data = f.read(65536)
                    if b"python" in data.lower() or b"cpy" in data.lower():
                        return True
        except Exception:
            pass
        return False

    target_cmd = ""
    if exec_str:
        target_cmd = exec_str
    elif normalized_args:
        first_arg = normalized_args[0]
        words = _split_command_to_words(first_arg)
        if words:
            target_cmd = words[0]

    is_python_cmd = False
    if target_cmd:
        is_python_cmd = _is_python_cmd_name(target_cmd) or _is_copied_python_executable(target_cmd)
    if not is_python_cmd and normalized_args:
        is_python_cmd = any(_is_python_cmd_name(arg) for arg in normalized_args)

    if is_python_cmd:
        for arg_str in normalized_args:
            arg_str_clean = arg_str.replace("^", "")
            blocked_pattern = r"\b(reduce|functools|codecs|rot_13|rot13|rot-13|zlib|gzip|bz2|lzma|zipfile|tarfile|pickle|marshal)\b"
            if re.search(blocked_pattern, arg_str_clean, re.IGNORECASE):
                raise PermissionError(
                    f"Blocked library or function detected in python subprocess: {arg_str_clean}"
                )
            if re.search(r"\[.*for.*in.*\]", arg_str_clean):
                raise PermissionError(
                    "List comprehension in python subprocess is blocked under HarnessGuard"
                )
            if re.search(r"\bfor\b", arg_str_clean) or re.search(r"\bwhile\b", arg_str_clean):
                raise PermissionError(
                    "Loop pattern in python subprocess is blocked under HarnessGuard"
                )
            if re.search(r"\[[^\]]*:[^\]]*:[^\]]*\]", arg_str_clean) or "::" in arg_str_clean:
                raise PermissionError(
                    "String slice with step in python subprocess is blocked under HarnessGuard"
                )
            if re.search(r"\.join\s*\(", arg_str_clean) or re.search(
                r"\.replace\s*\(", arg_str_clean
            ):
                raise PermissionError(
                    "Calling join/replace in python subprocess is blocked under HarnessGuard"
                )
            if re.search(r"\bgetattr\b", arg_str_clean) and (
                re.search(r"['\"]replace['\"]", arg_str_clean)
                or re.search(r"['\"]join['\"]", arg_str_clean)
            ):
                raise PermissionError(
                    "Calling getattr for join/replace in python subprocess is blocked under HarnessGuard"
                )
            if (
                re.search(r"\.format\s*\(", arg_str_clean)
                or re.search(r"%\s*\(", arg_str_clean)
                or re.search(r"%\s*\'", arg_str_clean)
                or re.search(r"%\s*\"", arg_str_clean)
            ):
                raise PermissionError(
                    "String formatting in python subprocess is blocked under HarnessGuard"
                )

    workspace_files = []
    has_wildcard = False
    for arg_str in normalized_args:
        if any(char in arg_str for char in ("*", "?", "[", "]")):
            has_wildcard = True
            break
    if has_wildcard:
        workspace_files = _get_workspace_files()

    target_env = env if env is not None else os.environ
    sys_argv_mock = None
    if is_python_cmd and isinstance(cmd_args, list):
        try:
            idx_c = -1
            for idx, arg in enumerate(cmd_args):
                if arg == "-c":
                    idx_c = idx
                    break
            if idx_c != -1:
                sys_argv_mock = ["-c"] + cmd_args[idx_c + 2 :]
            else:
                sys_argv_mock = cmd_args[1:]
        except Exception:
            pass

    ast_success = True
    if not normalized_args:
        ast_success = False

    for arg_str in normalized_args:
        arg_str_clean = arg_str.replace("^", "")
        try:
            _check_value_for_sensitive(arg_str_clean, guards)
        except PermissionError as pe:
            raise PermissionError(f"Access to sensitive file blocked in subprocess: {pe}") from pe

        try:
            reconstructed_shell = _reconstruct_shell_variables(arg_str_clean)
            if reconstructed_shell != arg_str_clean:
                _check_value_for_sensitive(reconstructed_shell, guards)
        except PermissionError as pe:
            raise PermissionError(f"Access to sensitive file blocked in subprocess: {pe}") from pe
        except Exception:
            pass

        try:
            tree = ast.parse(arg_str)
            strs, bytes_list = _scan_ast_nodes(
                tree, target_env=target_env, sys_argv_mock=sys_argv_mock
            )
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
                concat_bytes = b"".join(bytes_list)
                _check_value_for_sensitive(concat_bytes, guards)
        except PermissionError as pe:
            raise PermissionError(f"Access to sensitive file blocked in subprocess: {pe}") from pe
        except Exception:
            ast_success = False

        words = _split_command_to_words(arg_str)
        for word in words:
            normalized_word = word
            for char in ("'", '"'):
                normalized_word = normalized_word.replace(char, "")
            for g in guards:
                if g._is_sensitive(normalized_word) and not g._is_approved(normalized_word):
                    raise PermissionError(
                        f"Access to sensitive file blocked in subprocess: {arg_str}"
                    )

            if any(char in word for char in ("*", "?", "[", "]")):
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
                        if fnmatch.fnmatch(w_file, word) or fnmatch.fnmatch(
                            os.path.basename(w_file), word
                        ):
                            for g in guards:
                                if g._is_sensitive(w_file) and not g._is_approved(w_file):
                                    raise PermissionError(
                                        f"Access to sensitive file blocked by wildcard match: {w_file}"
                                    )
                except Exception:
                    pass

    if len(normalized_args) > 1:
        joined_space = " ".join(normalized_args).replace("^", "")
        joined_nospace = "".join(normalized_args).replace("^", "")
        for combined in (joined_space, joined_nospace):
            try:
                _check_value_for_sensitive(combined, guards)
            except PermissionError as pe:
                raise PermissionError(
                    f"Access to sensitive file blocked in subprocess via split-argument reconstruction: {pe}"
                ) from pe

    if env is not None:
        snapshot = guards[-1]._env_snapshot if hasattr(guards[-1], "_env_snapshot") else {}
        modified_keys = []
        for k, _ in env.items():
            if k not in snapshot or env[k] != snapshot[k]:
                modified_keys.append(k)

        modified_keys.sort()

        sorted_values = []
        for k in modified_keys:
            v = env[k]
            if v is not None:
                try:
                    vs = os.fspath(v)
                except Exception:
                    vs = str(v)
                if isinstance(vs, bytes):
                    vs = vs.decode("utf-8", errors="replace")
                sorted_values.append(vs)

        if sorted_values:
            combined_space = " ".join(sorted_values)
            combined_nospace = "".join(sorted_values)
            for comb in (combined_space, combined_nospace):
                try:
                    _check_value_for_sensitive(comb, guards)
                except PermissionError as pe:
                    raise PermissionError(
                        f"Access to sensitive path blocked via split env variable reconstruction: {pe}"
                    ) from pe

        for k in modified_keys:
            v = env[k]
            if v is not None:
                try:
                    val_str = os.fspath(v)
                except Exception:
                    val_str = str(v)
                if isinstance(val_str, bytes):
                    val_str = val_str.decode("utf-8", errors="replace")

                try:
                    _check_value_for_sensitive(val_str, guards)
                except PermissionError as pe:
                    raise PermissionError(
                        f"Access to sensitive path blocked in subprocess env: {pe}"
                    ) from pe

                parts = val_str.split(os.path.sep) if os.path.sep in val_str else [val_str]
                final_parts = []
                for p in parts:
                    if os.pathsep in p:
                        final_parts.extend(p.split(os.pathsep))
                    else:
                        final_parts.append(p)

                for part in final_parts:
                    if _looks_like_path(part):
                        for g in guards:
                            if g._is_sensitive(part) and not g._is_approved(part):
                                raise PermissionError(
                                    f"Access to sensitive path blocked in subprocess env: {part}"
                                )

    is_shell_interpreter = False
    shell_interpreters = ("cmd", "powershell", "pwsh", "sh", "bash", "zsh", "ash", "dash")
    if target_cmd:
        base_cmd = os.path.basename(target_cmd.lower())
        if any(sh in base_cmd for sh in shell_interpreters):
            is_shell_interpreter = True
    if not is_shell_interpreter and normalized_args:
        for arg in normalized_args:
            base_arg = os.path.basename(arg.lower())
            if any(sh in base_arg for sh in shell_interpreters):
                is_shell_interpreter = True
                break

    if is_shell_interpreter and not ast_success:
        joined_cmd = " ".join(normalized_args)
        clean_joined = joined_cmd.replace("^", "")
        try:
            _check_value_for_sensitive(clean_joined, guards)
        except PermissionError as pe:
            raise PermissionError(f"Access to sensitive file blocked in subprocess: {pe}") from pe


def _check_subprocess_call_for_guards(
    event: str, cmd_args: Any, env: Any, guards: list[HarnessGuard]
) -> None:
    _check_subprocess_call_internal(
        cmd_args=cmd_args, env=env, stdin=None, exec_path=None, guards=guards
    )


def _check_subprocess_call(name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
    guards = _get_active_guards()
    if not guards:
        return
    exec_path = _extract_exec_path(name, args, kwargs)
    cmd_args, env = _extract_subprocess_parts(name, args, kwargs)
    stdin = kwargs.get("stdin")
    _check_subprocess_call_internal(cmd_args, env, stdin, exec_path, guards)





def _extract_and_check_base64(text: str, active_guard) -> bool:
    contains_b64_keywords = False
    text_lower = text.lower()
    if (
        "base64" in text_lower
        or "b64decode" in text_lower
        or "decode('base64')" in text_lower
        or 'decode("base64")' in text_lower
    ):
        contains_b64_keywords = True

    candidates = re.findall(r"[A-Za-z0-9+/=]{4,}", text)
    for cand in candidates:
        min_len = 4 if contains_b64_keywords else 8
        if len(cand) < min_len:
            continue

        for attempt in (cand, cand + "==", cand + "="):
            try:
                decoded_bytes = base64.b64decode(attempt)
                if not decoded_bytes:
                    continue
                try:
                    decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
                    if decoded_str:
                        if active_guard._is_sensitive(
                            decoded_str
                        ) and not active_guard._is_approved(decoded_str):
                            return True
                        sensitive_keywords = [
                            "credential",
                            "secret",
                            "private_key",
                            "password",
                            "api_key",
                            "token",
                            ".env",
                        ]
                        decoded_lower = decoded_str.lower()
                        if any(kw in decoded_lower for kw in sensitive_keywords):
                            return True
                except Exception:
                    pass
            except Exception:
                pass
    return False


def _extract_exec_path(name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    if name == "system":
        return None
    if name.startswith("spawn"):
        if len(args) > 1:
            return args[1]
        return kwargs.get("path")
    if name.startswith("exec"):
        if len(args) > 0:
            return args[0]
        return kwargs.get("path") or kwargs.get("file")
    if name in ("posix_spawn", "posix_spawnp"):
        if len(args) > 0:
            return args[0]
        return kwargs.get("path")
    return None


def _extract_subprocess_parts(
    name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[Any, Any]:
    cmd_args = None
    env = None

    if name == "Popen":
        cmd_args = args[0] if len(args) > 0 else kwargs.get("args")
        env = kwargs.get("env")
        if env is None and len(args) > 10:
            env = args[10]
    elif name == "system":
        if len(args) > 0:
            cmd_args = args[0]
        else:
            cmd_args = kwargs.get("command")
    elif name in ("posix_spawn", "posix_spawnp"):
        if len(args) > 1:
            cmd_args = args[1]
        else:
            cmd_args = kwargs.get("argv")
        if len(args) > 2:
            env = args[2]
        else:
            env = kwargs.get("env")
    elif name.startswith("spawn"):
        if "l" in name:
            if name.endswith("e") or name.endswith("e_"):
                if len(args) > 2:
                    env = args[-1]
                    cmd_args = args[2:-1]
            else:
                if len(args) > 2:
                    cmd_args = args[2:]
        elif "v" in name:
            if len(args) > 2:
                cmd_args = args[2]
            if name.endswith("e") or name.endswith("e_"):
                if len(args) > 3:
                    env = args[3]
                else:
                    env = kwargs.get("env")
    elif name.startswith("exec"):
        if "l" in name:
            if name.endswith("e") or name.endswith("e_"):
                if len(args) > 1:
                    env = args[-1]
                    cmd_args = args[1:-1]
            else:
                if len(args) > 1:
                    cmd_args = args[1:]
        elif "v" in name:
            if len(args) > 1:
                cmd_args = args[1]
            if name.endswith("e") or name.endswith("e_"):
                if len(args) > 2:
                    env = args[2]
                else:
                    env = kwargs.get("env")
    return cmd_args, env


def _normalize_cmd_args(cmd_args: Any) -> list[str]:
    normalized_args = []
    if cmd_args is not None:
        if isinstance(cmd_args, (str, bytes, os.PathLike)):
            file_str = os.fspath(cmd_args)
            if isinstance(file_str, bytes):
                file_str = file_str.decode("utf-8", errors="replace")
            normalized_args.append(file_str)
        elif isinstance(cmd_args, (list, tuple)):
            for arg in cmd_args:
                if isinstance(arg, (str, bytes, os.PathLike)):
                    arg_str = os.fspath(arg)
                    if isinstance(arg_str, bytes):
                        arg_str = arg_str.decode("utf-8", errors="replace")
                    normalized_args.append(arg_str)
                else:
                    normalized_args.append(str(arg))
        else:
            normalized_args.append(str(cmd_args))
    return normalized_args


def _inject_child_env(env_dict: Any, guards: list[HarnessGuard]) -> dict:
    if env_dict is None:
        new_env = dict(os.environ)
    else:
        new_env = dict(env_dict)

    temp_dirs = [g._temp_dir for g in guards if hasattr(g, "_temp_dir") and g._temp_dir]
    if temp_dirs:
        existing_pythonpath = new_env.get("PYTHONPATH", "")
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        package_root = os.path.dirname(current_file_dir)
        path_dirs = list(temp_dirs) + [package_root]

        if existing_pythonpath:
            path_dirs.append(existing_pythonpath)
        new_env["PYTHONPATH"] = os.pathsep.join(path_dirs)

        new_env["HARNESS_ACTIVE"] = "1"

        all_approved = []
        for g in guards:
            if g.approved_paths:
                all_approved.extend(g.approved_paths)
        new_env["HARNESS_APPROVED_PATHS"] = os.pathsep.join(all_approved)

    return new_env


def _wrapped_popen(*args: Any, **kwargs: Any) -> Any:
    args_list = list(args)
    cmd_args = None
    in_kwargs = False
    if len(args_list) > 0:
        cmd_args = args_list[0]
    elif "args" in kwargs:
        cmd_args = kwargs["args"]
        in_kwargs = True

    if (
        cmd_args is not None
        and not isinstance(cmd_args, (str, bytes))
        and hasattr(cmd_args, "__next__")
    ):
        cmd_args = list(cmd_args)
        if in_kwargs:
            kwargs["args"] = cmd_args
        elif len(args_list) > 0:
            args_list[0] = cmd_args

    _check_subprocess_call("Popen", tuple(args_list), kwargs)

    guards = _get_active_guards()
    if guards:
        exec_path = _extract_exec_path("Popen", tuple(args_list), kwargs)
        cmd_args_extracted, env_extracted = _extract_subprocess_parts(
            "Popen", tuple(args_list), kwargs
        )

        target_cmd = ""
        if exec_path is not None:
            target_cmd = exec_path
        elif cmd_args_extracted:
            normalized = _normalize_cmd_args(cmd_args_extracted)
            if normalized:
                target_cmd = normalized[0]
                if isinstance(cmd_args_extracted, (str, bytes)):
                    words = _split_command_to_words(target_cmd)
                    if words:
                        target_cmd = words[0]

        is_python_cmd = False

        def _is_python_cmd_name(cmd: str) -> bool:
            cmd_clean = cmd.replace("^", "").lower()
            base = os.path.basename(cmd_clean)
            if base.endswith(".exe"):
                base = base[:-4]
            if re.match(r"^(python[\d\.]*w?|pyw?[\d\.]*)$", base):
                return True
            return False

        def _is_copied_python_executable(path: str) -> bool:
            try:
                path_clean = path.replace("^", "").strip()
                actual_path = path_clean
                if not os.path.isabs(path_clean):
                    if os.path.isfile(path_clean):
                        actual_path = path_clean
                    else:
                        for p in os.environ.get("PATH", "").split(os.pathsep):
                            candidate = os.path.join(p, path_clean)
                            if os.path.isfile(candidate):
                                actual_path = candidate
                                break
                if os.path.isfile(actual_path):
                    size_diff = abs(os.path.getsize(actual_path) - os.path.getsize(sys.executable))
                    if size_diff < 1024 * 1024:
                        with open(actual_path, "rb") as f:
                            data = f.read(65536)
                        if b"python" in data.lower():
                            return True
            except Exception:
                pass
            return False

        if target_cmd:
            is_python_cmd = _is_python_cmd_name(target_cmd) or _is_copied_python_executable(
                target_cmd
            )
        if not is_python_cmd and cmd_args_extracted:
            normalized = _normalize_cmd_args(cmd_args_extracted)
            is_python_cmd = any(
                _is_python_cmd_name(arg) or _is_copied_python_executable(arg) for arg in normalized
            )

        if is_python_cmd:
            if "env" in kwargs:
                kwargs["env"] = _inject_child_env(kwargs["env"], guards)
            else:
                if len(args_list) > 10:
                    args_list[10] = _inject_child_env(args_list[10], guards)
                else:
                    kwargs["env"] = _inject_child_env(None, guards)

    old_in_hook = getattr(HarnessState.local, "in_hook", None)
    HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        return _original_popen(*args_list, **kwargs)
    finally:
        HarnessState.local.__dict__["in_hook"] = old_in_hook


def _make_os_wrapper(name: str, original_func: Callable) -> Callable:
    @wraps(original_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if _check_in_hook():
            return original_func(*args, **kwargs)

        args_list = list(args)
        HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
        try:
            _check_subprocess_call(name, tuple(args_list), kwargs)

            guards = _get_active_guards()
            if guards:
                exec_path = _extract_exec_path(name, tuple(args_list), kwargs)
                cmd_args_extracted, env_extracted = _extract_subprocess_parts(
                    name, tuple(args_list), kwargs
                )

                target_cmd = ""
                if exec_path is not None:
                    target_cmd = exec_path
                elif cmd_args_extracted:
                    normalized = _normalize_cmd_args(cmd_args_extracted)
                    if normalized:
                        target_cmd = normalized[0]
                        if isinstance(cmd_args_extracted, (str, bytes)):
                            words = _split_command_to_words(target_cmd)
                            if words:
                                target_cmd = words[0]

                is_python = False

                def _is_python_cmd_name(cmd: str) -> bool:
                    cmd_clean = cmd.replace("^", "").lower()
                    base = os.path.basename(cmd_clean)
                    if base.endswith(".exe"):
                        base = base[:-4]
                    if re.match(r"^(python[\d\.]*w?|pyw?[\d\.]*)$", base):
                        return True
                    return False

                def _is_copied_python_executable(path: str) -> bool:
                    try:
                        path_clean = path.replace("^", "").strip()
                        actual_path = path_clean
                        if not os.path.isabs(path_clean):
                            if os.path.isfile(path_clean):
                                actual_path = path_clean
                            else:
                                for p in os.environ.get("PATH", "").split(os.pathsep):
                                    candidate = os.path.join(p, path_clean)
                                    if os.path.isfile(candidate):
                                        actual_path = candidate
                                        break
                        if os.path.isfile(actual_path):
                            size_diff = abs(
                                os.path.getsize(actual_path) - os.path.getsize(sys.executable)
                            )
                            if size_diff < 1024 * 1024:
                                with open(actual_path, "rb") as f:
                                    data = f.read(65536)
                                if b"python" in data.lower():
                                    return True
                    except Exception:
                        pass
                    return False

                if target_cmd:
                    is_python = _is_python_cmd_name(target_cmd) or _is_copied_python_executable(
                        target_cmd
                    )
                if not is_python and cmd_args_extracted:
                    normalized = _normalize_cmd_args(cmd_args_extracted)
                    is_python = any(
                        _is_python_cmd_name(arg) or _is_copied_python_executable(arg)
                        for arg in normalized
                    )

                if is_python:
                    if name.endswith("e") or name.endswith("e_") or "env" in kwargs:
                        if "env" in kwargs:
                            kwargs["env"] = _inject_child_env(kwargs["env"], guards)
                        elif len(args_list) > 0:
                            args_list[-1] = _inject_child_env(args_list[-1], guards)

            return original_func(*args_list, **kwargs)
        finally:
            HarnessState.local.__dict__["in_hook"] = None

    return wrapper



# ===========================================================================
# MULTI-THREADING WRAPPERS
# ===========================================================================
def _wrapped_thread_start(self: threading.Thread, *args: Any, **kwargs: Any) -> Any:
    parent_guards = list(_get_active_guards())
    if parent_guards:
        with HarnessState.lock:
            HarnessState.active_subthreads_count += 1
    original_run = self.run

    def wrapped_run(*run_args: Any, **run_kwargs: Any) -> Any:
        HarnessState.local.active_guards = list(parent_guards)
        try:
            return original_run(*run_args, **run_kwargs)
        finally:
            if parent_guards:
                with HarnessState.lock:
                    HarnessState.active_subthreads_count -= 1
                    if HarnessState.active_subthreads_count == 0 and HarnessState.active_count == 0:
                        if HarnessState.global_hooks_active:
                            from ._engine import HarnessEngine
                            HarnessEngine._restore_global_hooks_internal()

    self.run = wrapped_run
    return _original_thread_start(self, *args, **kwargs)


def _wrapped_thread_start_new_thread(
    function: Callable, args: tuple, kwargs: dict | None = None
) -> int:
    parent_guards = list(_get_active_guards())
    if parent_guards:
        with HarnessState.lock:
            HarnessState.active_subthreads_count += 1
    if kwargs is None:
        kwargs = {}

    def thread_target_wrapper(*target_args: Any, **target_kwargs: Any) -> Any:
        HarnessState.local.active_guards = list(parent_guards)
        try:
            return function(*target_args, **target_kwargs)
        finally:
            if parent_guards:
                with HarnessState.lock:
                    HarnessState.active_subthreads_count -= 1
                    if HarnessState.active_subthreads_count == 0 and HarnessState.active_count == 0:
                        if HarnessState.global_hooks_active:
                            from ._engine import HarnessEngine
                            HarnessEngine._restore_global_hooks_internal()

    return _original_thread_start_new_thread(thread_target_wrapper, args, kwargs)


def _wrapped_thread_start_new(function: Callable, args: tuple, kwargs: dict | None = None) -> int:
    parent_guards = list(_get_active_guards())
    if parent_guards:
        with HarnessState.lock:
            HarnessState.active_subthreads_count += 1
    if kwargs is None:
        kwargs = {}

    def thread_target_wrapper(*target_args: Any, **target_kwargs: Any) -> Any:
        HarnessState.local.active_guards = list(parent_guards)
        try:
            return function(*target_args, **target_kwargs)
        finally:
            if parent_guards:
                with HarnessState.lock:
                    HarnessState.active_subthreads_count -= 1
                    if HarnessState.active_subthreads_count == 0 and HarnessState.active_count == 0:
                        if HarnessState.global_hooks_active:
                            from ._engine import HarnessEngine
                            HarnessEngine._restore_global_hooks_internal()

    if _original_thread_start_new is not None:
        return _original_thread_start_new(thread_target_wrapper, args, kwargs)
    else:
        return _original_thread_start_new_thread(thread_target_wrapper, args, kwargs)


# ===========================================================================
# HARNESS ENGINE
# ===========================================================================
