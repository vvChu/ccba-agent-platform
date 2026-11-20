"""Command-line parsing, shell variable reconstruction, and argument extraction helpers."""

from __future__ import annotations

import base64
import os
import re
import shlex
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._guard import HarnessGuard


def _split_command_to_words(cmd_str: str) -> list[str]:
    """Split a shell command string using platform-appropriate shlex rules."""
    try:
        return shlex.split(cmd_str, posix=(sys.platform != "win32"))
    except Exception:
        return cmd_str.split()


def _split_shell_commands(stripped: str, is_windows: bool) -> list[str]:
    """Split a shell command string on unquoted separators (`&&`, `||`, `;`, `&`, newline)."""
    commands: list[str] = []
    current: list[str] = []
    in_dquote = in_squote = escape = False
    i, n = 0, len(stripped)
    while i < n:
        char = stripped[i]
        if escape:
            current.append(char)
            escape = False
        elif (char == "\\" and not is_windows and not in_squote) or (
            char == "^" and is_windows and not in_squote and not in_dquote
        ):
            escape = True
            current.append(char)
        elif char == '"' and not in_squote:
            in_dquote = not in_dquote
            current.append(char)
        elif char == "'" and not in_dquote:
            in_squote = not in_squote
            current.append(char)
        elif (
            not in_dquote
            and not in_squote
            and (
                (char in ("&", "|") and i + 1 < n and stripped[i + 1] == char)
                or char in (";", "&", "\n")
            )
        ):
            commands.append("".join(current))
            current = []
            i += 2 if (char in ("&", "|") and i + 1 < n and stripped[i + 1] == char) else 1
            continue
        else:
            current.append(char)
        i += 1
    if current:
        commands.append("".join(current))
    return commands


def _clean_caret(var: str, val: str, is_windows: bool) -> tuple[str, str]:
    """Strip Windows CMD caret escapes (`^`) from variable name and value when on win32."""
    return (var.replace("^", ""), val.replace("^", "")) if is_windows else (var, val)


def _parse_shell_assignments(commands: list[str], is_windows: bool) -> dict[str, str]:
    """Extract `set VAR=val` and `VAR=val` assignments from split shell segments."""
    vars_dict: dict[str, str] = {}
    for cmd in commands:
        cmd_clean = cmd.strip()
        if cmd_clean.startswith("$"):
            cmd_clean = cmd_clean[1:]
        if not cmd_clean:
            continue
        if cmd_clean.lower().startswith("set "):
            content = cmd_clean[4:].strip()
            quoted = re.match(r'^"([^=]+)=(.*)"$', content)
            unquoted = None if quoted else re.match(r"^([^=]+)=(.*)$", content)
            match_obj = quoted or unquoted
            if match_obj:
                var, val = _clean_caret(match_obj.group(1).strip(), match_obj.group(2), is_windows)
                if unquoted and val.count('"') % 2 != 0:
                    val = val.rstrip('"')
                vars_dict[var] = val
            continue
        assign = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(?:(["\'])(.*?)\2|([^"\'].*|))$', cmd_clean)
        if assign and assign.group(1).strip().lower() not in ("set", "export"):
            raw_val = assign.group(3) if assign.group(2) else assign.group(4)
            var, val = _clean_caret(assign.group(1).strip(), raw_val, is_windows)
            vars_dict[var] = val
    return vars_dict


def _apply_var_expansion_modifiers(
    val: str,
    start_str: str | None,
    len_str: str | None,
    str1: str | None = None,
    str2: str | None = None,
) -> str:
    """Apply substring slicing (`~s,l` / `:s:l`) or pattern replacement (`:old=new`)."""
    if str1 is not None:
        repl = str2 or ""
        if str1.startswith("*"):
            target = str1[1:]
            idx = val.lower().find(target.lower())
            return repl + val[idx + len(target) :] if idx != -1 else val
        return re.sub(re.escape(str1), lambda _m: repl, val, flags=re.IGNORECASE)
    if start_str is not None:
        start = int(start_str)
        if len_str is not None:
            length = int(len_str)
            return val[start : start + length] if length >= 0 else val[start:length]
        return val[start:]
    return val


def _replace_win_var(m: re.Match[str], vars_dict: dict[str, str]) -> str:
    """Expand a `%VAR%` or `!VAR!` Windows CMD match against `vars_dict`."""
    var_name = m.group(1)
    val = next((v for k, v in vars_dict.items() if k.lower() == var_name.lower()), None)
    if val is None:
        return m.group(0)
    return _apply_var_expansion_modifiers(val, m.group(2), m.group(3), m.group(4), m.group(5))


def _replace_unix_var(m: re.Match[str], vars_dict: dict[str, str]) -> str:
    """Expand a `${VAR...}` POSIX shell match against `vars_dict`."""
    val = vars_dict.get(m.group(1))
    if val is None:
        return m.group(0)
    return _apply_var_expansion_modifiers(val, m.group(2), m.group(3))


def _reconstruct_shell_variables(cmd_str: str) -> str:
    """Reconstruct obfuscated CMD/POSIX variable concatenations in a shell command."""
    is_windows = sys.platform == "win32"
    stripped = cmd_str.strip()
    prefix_re = (
        r"(?i)^(?:cmd(?:\.exe)?(?:\s+[\/\-][a-zA-Z]+)*\s+[\/\-][ckq]\s*|sh\s+\-c\s*"
        r"|bash\s+\-c\s*|zsh\s+\-c\s*|ash\s+\-c\s*|dash\s+\-c\s*|powershell\s+\-c\s*|pwsh\s+\-c\s*)"
        r'(["\'])(.*)\1\s*$'
    )
    prefix_match = re.match(prefix_re, stripped)
    if prefix_match:
        stripped = prefix_match.group(2)

    for _ in range(5):
        updated = re.sub(r"(['\"])(.*?)\1\s*\+\s*(['\"])(.*?)\3", r"\1\2\4\1", stripped)
        if updated == stripped:
            break
        stripped = updated

    vars_dict = _parse_shell_assignments(_split_shell_commands(stripped, is_windows), is_windows)
    reconstructed = cmd_str
    for _ in range(5):
        orig = reconstructed
        reconstructed = re.sub(
            r"!(\w+)(?:(?:~(-?\d+)(?:,(-?\d+))?)|(?::([^=!]+)=([^!]*)))!",
            lambda m: _replace_win_var(m, vars_dict),
            reconstructed,
            flags=re.IGNORECASE,
        )
        reconstructed = re.sub(
            r"%(\w+)(?:(?:~(-?\d+)(?:,(-?\d+))?)|(?::([^=%]+)=([^%]*)))?%",
            lambda m: _replace_win_var(m, vars_dict),
            reconstructed,
            flags=re.IGNORECASE,
        )
        reconstructed = re.sub(
            r"\$\{(\w+)(?::(\-?\d+)(?::(\-?\d+))?)?\}",
            lambda m: _replace_unix_var(m, vars_dict),
            reconstructed,
        )
        for var, val in vars_dict.items():
            reconstructed = re.sub(rf"\${var}\b", val.replace("\\", "\\\\"), reconstructed)
        if reconstructed == orig:
            break
    return reconstructed


def _extract_and_check_base64(text: str, active_guard: HarnessGuard) -> bool:
    """Return True if any decoded base64 substring matches unapproved sensitive content."""
    text_lower = text.lower()
    b64_hints = ("base64", "b64decode", "decode('base64')", 'decode("base64")')
    min_len = 4 if any(h in text_lower for h in b64_hints) else 8
    kws = ("credential", "secret", "private_key", "password", "api_key", "token", ".env")
    for cand in re.findall(r"[A-Za-z0-9+/=]{4,}", text):
        if len(cand) < min_len:
            continue
        for attempt in (cand, cand + "==", cand + "="):
            try:
                decoded_bytes = base64.b64decode(attempt)
                if not decoded_bytes:
                    continue
                decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
                if not decoded_str:
                    continue
                if active_guard._is_sensitive(decoded_str) and not active_guard._is_approved(
                    decoded_str
                ):
                    return True
                if any(kw in decoded_str.lower() for kw in kws):
                    return True
            except Exception:
                pass
    return False


def _extract_exec_path(name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """Extract executable path argument from OS spawn/exec call arguments."""
    if name == "system":
        return None
    if name.startswith("spawn"):
        return args[1] if len(args) > 1 else kwargs.get("path")
    if name.startswith("exec"):
        return args[0] if len(args) > 0 else (kwargs.get("path") or kwargs.get("file"))
    if name in ("posix_spawn", "posix_spawnp"):
        return args[0] if len(args) > 0 else kwargs.get("path")
    return None


def _extract_spawn_exec_family(
    name: str, args: tuple[Any, ...], kwargs: dict[str, Any], offset: int
) -> tuple[Any, Any]:
    """Extract `(cmd_args, env)` for `os.spawn*` (`offset=2`) or `os.exec*` (`offset=1`)."""
    cmd_args, env = None, None
    has_env = name.endswith(("e", "e_"))
    if "l" in name and len(args) > offset:
        if has_env:
            env = args[-1]
            cmd_args = args[offset:-1]
        else:
            cmd_args = args[offset:]
    elif "v" in name:
        if len(args) > offset:
            cmd_args = args[offset]
        if has_env:
            env = args[offset + 1] if len(args) > offset + 1 else kwargs.get("env")
    return cmd_args, env


def _extract_subprocess_parts(
    name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[Any, Any]:
    """Extract `(cmd_args, env)` across Popen, os.system, posix_spawn*, os.spawn*, os.exec*."""
    if name == "Popen":
        cmd_args = args[0] if len(args) > 0 else kwargs.get("args")
        env = (
            kwargs.get("env")
            if kwargs.get("env") is not None
            else (args[10] if len(args) > 10 else None)
        )
        return cmd_args, env
    if name == "system":
        return (args[0] if len(args) > 0 else kwargs.get("command")), None
    if name in ("posix_spawn", "posix_spawnp"):
        cmd_args = args[1] if len(args) > 1 else kwargs.get("argv")
        env = args[2] if len(args) > 2 else kwargs.get("env")
        return cmd_args, env
    if name.startswith("spawn"):
        return _extract_spawn_exec_family(name, args, kwargs, offset=2)
    if name.startswith("exec"):
        return _extract_spawn_exec_family(name, args, kwargs, offset=1)
    return None, None


def _normalize_cmd_args(cmd_args: Any) -> list[str]:
    """Normalize string/PathLike/sequence command arguments into a list of strings."""
    if cmd_args is None:
        return []
    if isinstance(cmd_args, (str, bytes, os.PathLike)):
        val = os.fspath(cmd_args)
        return [val.decode("utf-8", errors="replace") if isinstance(val, bytes) else val]
    if isinstance(cmd_args, (list, tuple)):
        normalized: list[str] = []
        for arg in cmd_args:
            if isinstance(arg, (str, bytes, os.PathLike)):
                item = os.fspath(arg)
                normalized.append(
                    item.decode("utf-8", errors="replace") if isinstance(item, bytes) else item
                )
            else:
                normalized.append(str(arg))
        return normalized
    return [str(cmd_args)]
