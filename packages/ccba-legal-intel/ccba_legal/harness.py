import _io
import _thread
import ast
import base64
import builtins
import fnmatch
import glob
import io
import os
import pathlib
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
from typing import Any


# Store process-wide original functions to prevent re-wrapping and hide them inside _Originals class
class _Originals:
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
    os_funcs = {}


for name in dir(os):
    if (
        name == "system"
        or name.startswith("exec")
        or name.startswith("spawn")
        or name in ("posix_spawn", "posix_spawnp")
    ):
        attr = getattr(os, name)
        if callable(attr):
            _Originals.os_funcs[name] = attr

# Expose private module variables for testing compatibility
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

# Thread-local state for tracking active guards and preventing recursion
_local = threading.local()
_lock = threading.Lock()
_active_count = 0
_audit_hook_registered = False

_HOOK_TOKEN = object()
_global_active_guards = []
_active_subthreads_count = 0
_global_hooks_active = False
_sensitive_inodes = set()
_path_resolution_cache = {}
_shared_temp_dir = None
_shared_temp_dir_lock = threading.Lock()
_sensitivity_cache = {}
_active_guarded_threads = set()


def _safe_limit_iter(iterable: Any, max_size: int = 1000) -> list:
    if iterable is None:
        return []
    res = []
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


def _check_in_hook() -> bool:
    val = getattr(_local, "in_hook", None)
    if val is not _HOOK_TOKEN:
        return False
    try:
        frame = sys._getframe(1)
        while frame:
            fn = os.path.basename(frame.f_code.co_filename)
            if fn == "harness.py" or fn.startswith("harness.py"):
                if frame.f_globals is globals() or frame.f_globals.get("__name__") == "ccba_legal.harness":
                    return True
            frame = frame.f_back
    except Exception:
        pass
    return False


def _get_active_guards() -> list["HarnessGuard"]:
    global _active_count
    if not hasattr(_local, "active_guards"):
        _local.active_guards = []
    active_guards = _local.active_guards
    harness_guard_cls = globals().get("HarnessGuard")
    if harness_guard_cls is not None and isinstance(active_guards, list) and all(isinstance(g, harness_guard_cls) for g in active_guards):
        if active_guards:
            return active_guards
    with _lock:
        if _global_active_guards:
            return list(_global_active_guards)
    return []


_scanned_dirs = set()


def _scan_for_sensitive_inodes() -> None:
    global _sensitive_inodes

    dirs_to_scan = []
    try:
        abs_d = os.path.normcase(os.path.abspath("."))
        if abs_d not in _scanned_dirs:
            dirs_to_scan.append(abs_d)
    except Exception:
        pass

    if not dirs_to_scan:
        return

    sensitive_keywords = [
        "credential",
        "secret",
        "private_key",
        "password",
        "api_key",
        "token",
        ".env",
    ]
    scanned = 0
    for base_dir in dirs_to_scan:
        _scanned_dirs.add(base_dir)
        try:
            for root, dirs, files in os.walk(base_dir):
                if scanned > 1000:
                    break
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in (".git", "__pycache__", "node_modules", ".venv", "venv", "env")
                ]
                for f in files:
                    scanned += 1
                    if scanned > 1000:
                        break
                    f_lower = f.lower()
                    if any(kw in f_lower for kw in sensitive_keywords):
                        try:
                            p = os.path.join(root, f)
                            st = os.stat(p)
                            _sensitive_inodes.add((st.st_dev, st.st_ino))
                        except Exception:
                            pass
        except Exception:
            pass


def _safe_record_written_file(g: Any, file_str: str) -> None:
    if "harness_guard_" in file_str or "sitecustomize.py" in file_str:
        return

    norm_path = (
        os.fspath(file_str) if isinstance(file_str, (str, bytes, os.PathLike)) else str(file_str)
    )
    if isinstance(norm_path, bytes):
        norm_path = norm_path.decode("utf-8", errors="replace")
    norm_path = os.path.normcase(os.path.abspath(norm_path))
    abs_path = os.path.abspath(norm_path)
    is_py = norm_path.lower().endswith(".py")

    lock = getattr(g, "_write_lock", None)
    if not lock:
        with _lock:
            if not hasattr(g, "_write_lock"):
                g._write_lock = threading.Lock()
            lock = g._write_lock
    with lock:
        if not hasattr(g, "_written_files"):
            g._written_files = set()
        g._written_files.add(norm_path)
        if is_py:
            if not hasattr(g, "_written_py_files"):
                g._written_py_files = set()
            g._written_py_files.add(abs_path)


def _looks_like_path(val: str) -> bool:
    if not val:
        return False
    try:
        if os.path.exists(val):
            return True
    except Exception:
        pass
    if "/" in val or "\\" in val:
        return True
    if val.startswith((".", "~")):
        return True
    if "." in val:
        ext = val.split(".")[-1]
        if ext.isalnum() and len(ext) <= 4:
            return True
    return False


def _get_workspace_files() -> list[str]:
    files = []
    try:
        for root, dirs, filenames in os.walk(".", topdown=True):
            dirs[:] = [
                d
                for d in dirs
                if d
                not in (".git", "__pycache__", "node_modules", "venv", ".venv", "env", ".agents")
            ]
            for f in filenames:
                files.append(os.path.join(root, f))
                if len(files) > 1000:
                    break
            if len(files) > 1000:
                break
    except Exception:
        pass
    return files


def _split_command_to_words(cmd_str: str) -> list[str]:
    try:
        return shlex.split(cmd_str, posix=(sys.platform != "win32"))
    except Exception:
        return cmd_str.split()


def _strip_comments_from_sql(sql: str) -> str:
    # First, strip block comments /* ... */
    # Replace with a space to preserve separation
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # Then strip line comments -- ...
    sql = re.sub(r"--.*?(?=\r?\n|$)", " ", sql)
    return sql


def _extract_attached_db_paths(sql: str) -> list[str]:
    sql = _strip_comments_from_sql(sql)
    quoted = re.findall(r'(?i)\bATTACH\b\s+(?:DATABASE\s+)?([\'"])(.*?)\1', sql)
    paths = [q[1] for q in quoted]
    unquoted = re.findall(r'(?i)\bATTACH\b\s+(?:DATABASE\s+)?([^\s\'"]+)', sql)
    for p in unquoted:
        if p and not p.startswith(("'", '"')):
            if p.lower() != "database":
                paths.append(p)
    return paths


def _clean_and_decode_db_path(path: str) -> str:
    decoded = path
    for _ in range(10):
        next_decoded = urllib.parse.unquote(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    if decoded.lower().startswith("file:"):
        decoded = decoded[5:]
        if decoded.startswith("///"):
            decoded = decoded[3:]
        elif decoded.startswith("//"):
            decoded = decoded[2:]
        if "?" in decoded:
            decoded = decoded.split("?")[0]
    return decoded


def _check_db_path(path_str: str) -> None:
    guards = _get_active_guards()
    if not guards:
        return
    decoded = _clean_and_decode_db_path(path_str)
    for g in guards:
        if g._is_sensitive(decoded) and not g._is_approved(decoded):
            raise PermissionError(f"Access to sensitive database blocked: {path_str}")


def _check_sql_query(sql: Any) -> None:
    if sql is None:
        return
    try:
        sql_str = str(sql)
    except Exception:
        return
    sql_upper = sql_str.upper()

    if "VACUUM" in sql_upper and "INTO" in sql_upper:
        sql_clean = _strip_comments_from_sql(sql_str)
        for m in re.finditer(r"(?i)\bINTO\b\s*(?:'([^']*)'|\"([^\"]*)\"|([^\s;'\"]+))", sql_clean):
            path = m.group(1) or m.group(2) or m.group(3)
            if path:
                _check_db_path(path)

    # Block ATTACH expression / concatenation bypasses
    if "ATTACH" in sql_upper:
        guards = _get_active_guards()
        if guards:
            # Scan the entire query text for sensitive keywords regardless of quotes or concat operators
            try:
                _check_value_for_sensitive(sql_str, guards)
            except PermissionError as pe:
                raise PermissionError(
                    f"Access to sensitive database blocked in ATTACH query: {pe}"
                ) from pe

            # Strip concat operators, quotes, comments, parentheses, spaces to detect reconstruct bypasses
            sql_clean = _strip_comments_from_sql(sql_str)
            stripped = re.sub(r"[\s+|'\"(),;/\*#\-]+", "", sql_clean)
            try:
                _check_value_for_sensitive(stripped, guards)
            except PermissionError as pe:
                raise PermissionError(
                    f"Access to sensitive database blocked in ATTACH query: {pe}"
                ) from pe

        cleaned_sql = _strip_comments_from_sql(sql_str)
        match = re.search(r"(?i)\bATTACH\b\s+(?:DATABASE\s+)?(.*?)\bAS\b", cleaned_sql, re.DOTALL)
        if match:
            expr = match.group(1).strip()
            expr_upper = expr.upper()
            if "CHAR" in expr_upper and re.search(r"(?i)\bchar\s*\(", expr):
                raise PermissionError("SQLite ATTACH with char() is blocked")
            if "CAST" in expr_upper and re.search(r"(?i)\bcast\s*\(", expr):
                raise PermissionError("SQLite ATTACH with CAST() is blocked")
            if "||" in expr or "+" in expr:
                raise PermissionError("SQLite ATTACH with concatenation is blocked")
            if "(" in expr or ")" in expr:
                raise PermissionError("SQLite ATTACH with parentheses is blocked")
            if re.search(r"(?i)\bx\s*'", expr):
                raise PermissionError("SQLite ATTACH with hex literal is blocked")

        literals = re.findall(r"'([^']*)'|\"([^\"]*)\"", sql_str)
        lit_strings = []
        for g1, g2 in literals:
            lit_strings.append(g1 or g2 or "")
        for s in lit_strings:
            _check_db_path(s)
        concat_lits = "".join(lit_strings)
        _check_db_path(concat_lits)

    attached_paths = _extract_attached_db_paths(sql_str)
    for p in attached_paths:
        _check_db_path(p)


class _WrappedCursor:
    def __init__(self, original_cursor: Any) -> None:
        self._orig_cursor = original_cursor

    def execute(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        res = self._orig_cursor.execute(sql, *args, **kwargs)
        if res is self._orig_cursor:
            return self
        return res

    def executemany(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        res = self._orig_cursor.executemany(sql, *args, **kwargs)
        if res is self._orig_cursor:
            return self
        return res

    def executescript(self, sql_script: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql_script)
        res = self._orig_cursor.executescript(sql_script, *args, **kwargs)
        if res is self._orig_cursor:
            return self
        return res

    def __getattr__(self, name: str) -> Any:
        return getattr(self._orig_cursor, name)

    def __iter__(self) -> Any:
        return iter(self._orig_cursor)


class _Wrappedsqlite3Connection(_Originals.sqlite3_Connection):
    def __init__(self, database: Any, *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(database, *args, **kwargs)
            return

        guards = _get_active_guards()
        if not guards:
            super().__init__(database, *args, **kwargs)
            return

        _local.in_hook = _HOOK_TOKEN
        try:
            if database is not None:
                db_str = (
                    os.fspath(database)
                    if isinstance(database, (str, bytes, os.PathLike))
                    else str(database)
                )
                if isinstance(db_str, bytes):
                    db_str = db_str.decode("utf-8", errors="replace")

                if db_str != ":memory:" and db_str.lower() != ":memory:":
                    _check_db_path(db_str)
            super().__init__(database, *args, **kwargs)
        finally:
            _local.in_hook = None

    def execute(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        return super().execute(sql, *args, **kwargs)

    def executemany(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        return super().executemany(sql, *args, **kwargs)

    def executescript(self, sql_script: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql_script)
        return super().executescript(sql_script, *args, **kwargs)

    def cursor(self, *args: Any, **kwargs: Any) -> Any:
        cursor_obj = super().cursor(*args, **kwargs)
        return _WrappedCursor(cursor_obj)


def _safe_escape_decode(b: bytes) -> bytes:
    res = bytearray()
    i = 0
    n = len(b)
    while i < n:
        if b[i] == 92:  # ord('\\')
            if i + 1 >= n:
                res.append(92)
                break
            nxt = b[i + 1]
            if nxt in (92, 39, 34):  # \\, \', \"
                res.append(nxt)
                i += 2
            elif nxt == 97:  # \a
                res.append(7)
                i += 2
            elif nxt == 98:  # \b
                res.append(8)
                i += 2
            elif nxt == 102:  # \f
                res.append(12)
                i += 2
            elif nxt == 110:  # \n
                res.append(10)
                i += 2
            elif nxt == 114:  # \r
                res.append(13)
                i += 2
            elif nxt == 116:  # \t
                res.append(9)
                i += 2
            elif nxt == 118:  # \v
                res.append(11)
                i += 2
            elif nxt == 120:  # \x
                # Hex escape: next two chars should be hex digits
                if i + 3 < n:
                    hex_digits = b[i + 2 : i + 4]
                    try:
                        val = int(hex_digits, 16)
                        res.append(val)
                        i += 4
                        continue
                    except ValueError:
                        pass
                res.append(92)
                res.append(120)
                i += 2
            elif nxt == 117:  # \u
                if i + 5 < n:
                    hex_digits = b[i + 2 : i + 6]
                    try:
                        val = int(hex_digits, 16)
                        res.extend(chr(val).encode("utf-8"))
                        i += 6
                        continue
                    except Exception:
                        pass
                res.append(92)
                res.append(117)
                i += 2
            elif nxt == 85:  # \U
                if i + 9 < n:
                    hex_digits = b[i + 2 : i + 10]
                    try:
                        val = int(hex_digits, 16)
                        res.extend(chr(val).encode("utf-8"))
                        i += 10
                        continue
                    except Exception:
                        pass
                res.append(92)
                res.append(85)
                i += 2
            elif 48 <= nxt <= 55:  # \ooo
                oct_len = 1
                if i + 2 < n and 48 <= b[i + 2] <= 55:
                    oct_len = 2
                    if i + 3 < n and 48 <= b[i + 3] <= 55:
                        oct_len = 3
                oct_digits = b[i + 1 : i + 1 + oct_len]
                val = int(oct_digits, 8)
                res.append(val & 255)
                i += 1 + oct_len
            else:
                # Invalid or unsupported escape. Keep it.
                res.append(92)
                res.append(nxt)
                i += 2
        else:
            res.append(b[i])
            i += 1
    return bytes(res)


def _is_text_sensitive(text: str) -> bool:
    if not isinstance(text, str):
        return False
    text = unicodedata.normalize("NFKC", text)
    sensitive_keywords = ["credential", "secret", "private_key", "password", "api_key", "token"]
    text_lower = text.lower()
    if any(kw in text_lower for kw in sensitive_keywords):
        return True

    # Check for ".env" exactly as a filename or path component
    parts = re.split(r'[/\\\'"\s=,;()\[\]{}]', text_lower)
    for p in parts:
        if p == ".env" or p.endswith(".env"):
            return True

    return False


def _check_value_for_sensitive(val: Any, guards: list["HarnessGuard"]) -> None:
    if not val:
        return

    # Check cache first to optimize performance
    if isinstance(val, str) and val in _sensitivity_cache:
        if _sensitivity_cache[val]:
            if not any(g._is_approved(val) for g in guards):
                raise PermissionError(f"Access to sensitive keyword blocked (cached): {val}")
            return

    # First, always check the raw input as-is (both string and bytes representation)
    raw_str = ""
    raw_bytes = b""
    if isinstance(val, str):
        raw_str = unicodedata.normalize("NFKC", val)
        try:
            raw_bytes = raw_str.encode("utf-8")
        except Exception:
            pass
    elif isinstance(val, bytes):
        raw_bytes = val
        try:
            raw_str = val.decode("utf-8", errors="ignore")
            raw_str = unicodedata.normalize("NFKC", raw_str)
        except Exception:
            pass
    else:
        return

    # Ensure raw string is always scanned
    if raw_str and _is_text_sensitive(raw_str):
        if not any(g._is_approved(raw_str) for g in guards):
            raise PermissionError(f"Access to sensitive keyword blocked: {raw_str}")

    # 7. File system link resolve:
    from pathlib import Path

    try:
        if raw_str and isinstance(raw_str, str):
            try:
                canonical_path = os.path.realpath(raw_str)
            except Exception:
                canonical_path = raw_str

            for path_to_check in {raw_str, canonical_path}:
                if os.path.exists(path_to_check):
                    try:
                        st = os.stat(path_to_check)
                        if (st.st_dev, st.st_ino) in _sensitive_inodes:
                            if not any(g._is_approved(path_to_check) for g in guards):
                                raise PermissionError(
                                    f"Access to sensitive file blocked: {path_to_check}"
                                )
                    except PermissionError:
                        raise
                    except Exception:
                        pass

                    try:
                        resolved_path = Path(path_to_check).resolve()
                        resolved_str = str(resolved_path)
                        if resolved_str != path_to_check:
                            _check_value_for_sensitive(resolved_str, guards)
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass

    # Now decode escape sequences using our safe helper
    decoded_bytes = b""
    if raw_bytes:
        try:
            decoded_bytes = _safe_escape_decode(raw_bytes)
        except Exception:
            decoded_bytes = raw_bytes

    decoded_str = ""
    if decoded_bytes:
        try:
            decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
            decoded_str = unicodedata.normalize("NFKC", decoded_str)
        except Exception:
            pass

    # If decoded string is different and sensitive, check/raise
    if decoded_str and decoded_str != raw_str:
        try:
            if _is_text_sensitive(decoded_str):
                if not any(g._is_approved(decoded_str) for g in guards):
                    raise PermissionError(f"Access to sensitive keyword blocked: {decoded_str}")
        except PermissionError:
            raise
        except Exception:
            pass

    # Base64 check on both raw and decoded strings
    try:
        base64_candidates = {raw_str, decoded_str}
        if raw_str:
            base64_candidates.add(re.sub(r"\s+", "", raw_str))
        if decoded_str:
            base64_candidates.add(re.sub(r"\s+", "", decoded_str))
        for candidate_str in filter(None, base64_candidates):
            cleaned_cand = re.sub(r"\s+", "", candidate_str)
            b64_cands = re.findall(r"[A-Za-z0-9+/=]{4,}", cleaned_cand)
            for cand in b64_cands:
                for attempt in (cand, cand + "==", cand + "="):
                    try:
                        decoded = base64.b64decode(attempt)
                        if decoded:
                            dec_s = decoded.decode("utf-8", errors="ignore")
                            dec_s = unicodedata.normalize("NFKC", dec_s)
                            if _is_text_sensitive(dec_s):
                                if not any(g._is_approved(dec_s) for g in guards):
                                    raise PermissionError(
                                        f"Access to sensitive keyword blocked in base64: {dec_s}"
                                    )
                            try:
                                decomp = zlib.decompress(decoded)
                                if decomp:
                                    decomp_s = decomp.decode("utf-8", errors="ignore")
                                    decomp_s = unicodedata.normalize("NFKC", decomp_s)
                                    if _is_text_sensitive(decomp_s):
                                        if not any(g._is_approved(decomp_s) for g in guards):
                                            raise PermissionError(
                                                f"Access to sensitive keyword blocked in compressed base64: {decomp_s}"
                                            )
                            except PermissionError:
                                raise
                            except Exception:
                                pass
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass

    # Base32 check on both raw and decoded strings
    try:
        for candidate_str in filter(None, {raw_str, decoded_str}):
            cleaned_cand = re.sub(r"\s+", "", candidate_str)
            b32_cands = re.findall(r"[A-Z2-7=]{4,}", cleaned_cand, flags=re.IGNORECASE)
            for cand in b32_cands:
                for attempt in (cand, cand + "====", cand + "===", cand + "==", cand + "="):
                    try:
                        decoded = base64.b32decode(attempt.upper().encode("utf-8"))
                        if decoded:
                            dec_s = decoded.decode("utf-8", errors="ignore")
                            dec_s = unicodedata.normalize("NFKC", dec_s)
                            if _is_text_sensitive(dec_s):
                                if not any(g._is_approved(dec_s) for g in guards):
                                    raise PermissionError(
                                        f"Access to sensitive keyword blocked in base32: {dec_s}"
                                    )
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass

    # Base85/Ascii85 check on both raw and decoded strings
    try:
        for candidate_str in filter(None, {raw_str, decoded_str}):
            cleaned_cand = re.sub(r"\s+", "", candidate_str)
            b85_cands = re.findall(r"[A-Za-z0-9!#$%&()*+-;<=>?@^_`{|}~]{4,}", cleaned_cand)
            for cand in b85_cands:
                try:
                    decoded = base64.b85decode(cand)
                    if decoded:
                        dec_s = decoded.decode("utf-8", errors="ignore")
                        dec_s = unicodedata.normalize("NFKC", dec_s)
                        if _is_text_sensitive(dec_s):
                            if not any(g._is_approved(dec_s) for g in guards):
                                raise PermissionError(
                                    f"Access to sensitive keyword blocked in base85: {dec_s}"
                                )
                except PermissionError:
                    raise
                except Exception:
                    pass
                try:
                    decoded = base64.a85decode(cand)
                    if decoded:
                        dec_s = decoded.decode("utf-8", errors="ignore")
                        dec_s = unicodedata.normalize("NFKC", dec_s)
                        if _is_text_sensitive(dec_s):
                            if not any(g._is_approved(dec_s) for g in guards):
                                raise PermissionError(
                                    f"Access to sensitive keyword blocked in a85: {dec_s}"
                                )
                except PermissionError:
                    raise
                except Exception:
                    pass
    except PermissionError:
        raise
    except Exception:
        pass

    # Hex check on both raw and decoded strings
    try:
        for candidate_str in filter(None, {raw_str, decoded_str}):
            cleaned_cand = re.sub(r"\s+", "", candidate_str)
            hex_cands = re.findall(r"[0-9a-fA-F]{4,}", cleaned_cand)
            for cand in hex_cands:
                for c in (cand, cand[1:] if len(cand) % 2 != 0 else cand):
                    try:
                        decoded = bytes.fromhex(c)
                        if decoded:
                            dec_s = decoded.decode("utf-8", errors="ignore")
                            dec_s = unicodedata.normalize("NFKC", dec_s)
                            if _is_text_sensitive(dec_s):
                                if not any(g._is_approved(dec_s) for g in guards):
                                    raise PermissionError(
                                        f"Access to sensitive keyword blocked in hex: {dec_s}"
                                    )
                            try:
                                decomp = zlib.decompress(decoded)
                                if decomp:
                                    decomp_s = decomp.decode("utf-8", errors="ignore")
                                    decomp_s = unicodedata.normalize("NFKC", decomp_s)
                                    if _is_text_sensitive(decomp_s):
                                        if not any(g._is_approved(decomp_s) for g in guards):
                                            raise PermissionError(
                                                f"Access to sensitive keyword blocked in compressed hex: {decomp_s}"
                                            )
                            except PermissionError:
                                raise
                            except Exception:
                                pass
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass

    # Zlib check on raw and decoded bytes
    try:
        for candidate_bytes in filter(None, {raw_bytes, decoded_bytes}):
            try:
                decomp = zlib.decompress(candidate_bytes)
                if decomp:
                    decomp_str = decomp.decode("utf-8", errors="ignore")
                    decomp_str = unicodedata.normalize("NFKC", decomp_str)
                    if _is_text_sensitive(decomp_str):
                        if not any(g._is_approved(decomp_str) for g in guards):
                            raise PermissionError(
                                f"Access to sensitive keyword blocked in compressed data: {decomp_str}"
                            )
            except PermissionError:
                raise
            except Exception:
                pass
    except PermissionError:
        raise
    except Exception:
        pass


def _scan_ast_nodes(
    node: ast.AST, target_env: dict[str, str] | None = None, sys_argv_mock: list[str] | None = None
) -> tuple[list[str], list[bytes]]:
    strs = []
    bytes_list = []
    local_vars = {}
    MAX_DEPTH = 100

    def eval_node(n: ast.AST, depth: int = 0) -> Any:
        if n is None or depth > MAX_DEPTH:
            return None
        if isinstance(n, ast.Constant):
            return n.value
        elif isinstance(n, ast.Name):
            if n.id in local_vars:
                return local_vars[n.id]
            if n.id == "os":
                import os

                return os
            if n.id == "sys":
                import sys

                return sys
            if n.id == "getattr":
                return getattr
            import sys as _sys

            if n.id in _sys.modules:
                return _sys.modules[n.id]
            try:
                return __import__(n.id)
            except Exception:
                pass
            return None
        elif isinstance(n, ast.Assign):
            val = eval_node(n.value, depth + 1)
            for target in n.targets:
                if isinstance(target, ast.Name):
                    local_vars[target.id] = val
            return val
        elif isinstance(n, ast.Subscript):
            val = eval_node(n.value, depth + 1)
            sl = n.slice
            if isinstance(sl, ast.Slice):
                lower = eval_node(sl.lower, depth + 1) if sl.lower is not None else None
                upper = eval_node(sl.upper, depth + 1) if sl.upper is not None else None
                step = eval_node(sl.step, depth + 1) if sl.step is not None else None
                if val is not None:
                    try:
                        return val[slice(lower, upper, step)]
                    except Exception:
                        pass
            else:
                idx = eval_node(sl, depth + 1)
                if val is not None and idx is not None:
                    try:
                        return val[idx]
                    except Exception:
                        pass
        elif isinstance(n, ast.Attribute):
            val = eval_node(n.value, depth + 1)
            import os
            import sys

            if val is os and n.attr == "environ":
                return target_env
            elif val is sys and n.attr == "argv":
                return sys_argv_mock
            elif val is not None:
                try:
                    return getattr(val, n.attr)
                except Exception:
                    pass
            return None
        elif isinstance(n, ast.BinOp):
            left_val = eval_node(n.left, depth + 1)
            right_val = eval_node(n.right, depth + 1)
            if left_val is not None and right_val is not None:
                # Support all binary operations cleanly using a lookup mapping
                _OP_MAP = {
                    ast.Add: lambda left, right: left + right,
                    ast.Sub: lambda left, right: left - right,
                    ast.Mult: lambda left, right: left * right,
                    ast.Div: lambda left, right: left / right,
                    ast.FloorDiv: lambda left, right: left // right,
                    ast.Mod: lambda left, right: left % right,
                    ast.Pow: lambda left, right: left**right,
                    ast.LShift: lambda left, right: left << right,
                    ast.RShift: lambda left, right: left >> right,
                    ast.BitOr: lambda left, right: left | right,
                    ast.BitAnd: lambda left, right: left & right,
                    ast.BitXor: lambda left, right: left ^ right,
                }
                op_type = type(n.op)
                if op_type in _OP_MAP:
                    try:
                        return _OP_MAP[op_type](left_val, right_val)
                    except Exception:
                        pass
        elif isinstance(n, ast.UnaryOp):
            operand_val = eval_node(n.operand, depth + 1)
            if operand_val is not None:
                if isinstance(n.op, ast.USub):
                    try:
                        return -operand_val
                    except Exception:
                        pass
                elif isinstance(n.op, ast.UAdd):
                    return operand_val
        elif isinstance(n, ast.Call):
            func_val = eval_node(n.func, depth + 1)
            if func_val is getattr and len(n.args) == 2:
                obj = eval_node(n.args[0], depth + 1)
                attr = eval_node(n.args[1], depth + 1)
                if obj is not None and attr is not None:
                    try:
                        return getattr(obj, attr)
                    except Exception:
                        pass

            if isinstance(n.func, ast.Attribute):
                val = eval_node(n.func.value, depth + 1)
                attr = n.func.attr
                if attr == "decode" and isinstance(val, bytes):
                    try:
                        return val.decode("utf-8", errors="ignore")
                    except Exception:
                        pass
                elif attr == "encode" and isinstance(val, str):
                    try:
                        return val.encode("utf-8")
                    except Exception:
                        pass
                elif attr == "join" and isinstance(val, (str, bytes)):
                    if len(n.args) == 1:
                        arg_val = eval_node(n.args[0], depth + 1)
                        if isinstance(arg_val, (list, tuple)):
                            try:
                                return val.join(arg_val)
                            except Exception:
                                pass
                elif attr in (
                    "__or__",
                    "__and__",
                    "__xor__",
                    "__lshift__",
                    "__rshift__",
                    "__add__",
                    "__sub__",
                    "__mul__",
                    "__truediv__",
                    "__floordiv__",
                    "__mod__",
                    "__pow__",
                ):
                    if len(n.args) == 1:
                        arg_val = eval_node(n.args[0], depth + 1)
                        if arg_val is not None:
                            try:
                                method = getattr(val, attr, None)
                                if method is not None:
                                    return method(arg_val)
                            except Exception:
                                pass
            elif isinstance(n.func, ast.Name):
                func_name = n.func.id
                if func_name == "bytes":
                    if len(n.args) == 0:
                        return b""
                    elif len(n.args) == 1:
                        arg_val = eval_node(n.args[0], depth + 1)
                        if arg_val is not None:
                            try:
                                return bytes(arg_val)
                            except Exception:
                                pass
                    elif len(n.args) == 2:
                        arg_val = eval_node(n.args[0], depth + 1)
                        enc_val = eval_node(n.args[1], depth + 1)
                        if arg_val is not None and enc_val is not None:
                            try:
                                return bytes(arg_val, enc_val)
                            except Exception:
                                pass
                elif func_name == "int":
                    if len(n.args) == 0:
                        return 0
                    elif len(n.args) == 1:
                        arg_val = eval_node(n.args[0], depth + 1)
                        if arg_val is not None:
                            try:
                                return int(arg_val)
                            except Exception:
                                pass
                    elif len(n.args) == 2:
                        arg_val = eval_node(n.args[0], depth + 1)
                        base_val = eval_node(n.args[1], depth + 1)
                        if arg_val is not None and base_val is not None:
                            try:
                                return int(arg_val, base_val)
                            except Exception:
                                pass
                elif func_name == "list":
                    if len(n.args) == 0:
                        return []
                    elif len(n.args) == 1:
                        arg_val = eval_node(n.args[0], depth + 1)
                        if arg_val is not None:
                            try:
                                return list(arg_val)
                            except Exception:
                                pass
                elif func_name == "chr" and len(n.args) == 1:
                    arg_val = eval_node(n.args[0], depth + 1)
                    if isinstance(arg_val, int):
                        try:
                            return chr(arg_val)
                        except Exception:
                            pass
                elif func_name == "ord" and len(n.args) == 1:
                    arg_val = eval_node(n.args[0], depth + 1)
                    if isinstance(arg_val, str) and len(arg_val) == 1:
                        try:
                            return ord(arg_val)
                        except Exception:
                            pass
                elif func_name == "map" and len(n.args) == 2:
                    func_node = n.args[0]
                    iter_node = n.args[1]
                    iter_val = eval_node(iter_node, depth + 1)
                    if iter_val is not None:
                        if isinstance(func_node, ast.Lambda):
                            lambda_args = func_node.args.args
                            if len(lambda_args) == 1:
                                arg_name = lambda_args[0].arg
                                results = []
                                old_val = local_vars.get(arg_name)
                                try:
                                    count = 0
                                    for item in iter_val:
                                        count += 1
                                        if count > 1000:
                                            break
                                        local_vars[arg_name] = item
                                        res = eval_node(func_node.body, depth + 1)
                                        if res is not None:
                                            results.append(res)
                                        else:
                                            break
                                    if all(isinstance(x, int) and 0 <= x <= 255 for x in results):
                                        return bytes(results)
                                    return results
                                finally:
                                    if old_val is not None:
                                        local_vars[arg_name] = old_val
                                    else:
                                        local_vars.pop(arg_name, None)
                        elif isinstance(func_node, ast.Name):
                            mapped_func = func_node.id
                            if mapped_func == "chr":
                                try:
                                    res_list = []
                                    for idx, x in enumerate(iter_val):
                                        if idx >= 1000:
                                            break
                                        res_list.append(chr(x))
                                    return "".join(res_list)
                                except Exception:
                                    pass
                            elif mapped_func == "ord":
                                try:
                                    res_list = []
                                    for idx, x in enumerate(iter_val):
                                        if idx >= 1000:
                                            break
                                        res_list.append(ord(x))
                                    return res_list
                                except Exception:
                                    pass

            pass
        elif isinstance(n, ast.List):
            elts_vals = [eval_node(elt, depth + 1) for elt in n.elts]
            if all(v is not None for v in elts_vals):
                return elts_vals
        elif isinstance(n, ast.Tuple):
            elts_vals = [eval_node(elt, depth + 1) for elt in n.elts]
            if all(v is not None for v in elts_vals):
                return tuple(elts_vals)
        elif isinstance(n, (ast.ListComp, ast.GeneratorExp)):
            if len(n.generators) == 1:
                gen = n.generators[0]
                if isinstance(gen.target, ast.Name):
                    iter_val = eval_node(gen.iter, depth + 1)
                    if iter_val is not None:
                        target_name = gen.target.id
                        results = []
                        old_val = local_vars.get(target_name)
                        try:
                            count = 0
                            for item in iter_val:
                                count += 1
                                if count > 1000:
                                    break
                                local_vars[target_name] = item
                                keep = True
                                for f in gen.ifs:
                                    f_val = eval_node(f, depth + 1)
                                    if f_val is not None and not f_val:
                                        keep = False
                                        break
                                if keep:
                                    res = eval_node(n.elt, depth + 1)
                                    if res is not None:
                                        results.append(res)
                            return results
                        finally:
                            if old_val is not None:
                                local_vars[target_name] = old_val
                            else:
                                local_vars.pop(target_name, None)
        elif isinstance(n, ast.JoinedStr):
            parts = []
            for val_node in n.values:
                part = eval_node(val_node, depth + 1)
                if part is not None:
                    parts.append(str(part))
                else:
                    return None
            return "".join(parts)
        elif isinstance(n, ast.FormattedValue):
            return eval_node(n.value, depth + 1)
        return None

    def visit(n: ast.AST, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            return
        val = eval_node(n, depth)
        if val is not None:
            if isinstance(val, str):
                strs.append(val)
            elif isinstance(val, bytes):
                bytes_list.append(val)
            elif isinstance(val, int):
                if 0 <= val <= 255:
                    bytes_list.append(bytes([val]))
            elif isinstance(val, (list, tuple)):
                if all(isinstance(x, int) and 0 <= x <= 255 for x in val):
                    bytes_list.append(bytes(val))
                for x in val:
                    if isinstance(x, str):
                        strs.append(x)
                    elif isinstance(x, bytes):
                        bytes_list.append(x)

        for child in ast.iter_child_nodes(n):
            visit(child, depth + 1)

    visit(node)
    return strs, bytes_list


def _reconstruct_shell_variables(cmd_str: str) -> str:
    import re
    import sys

    is_windows = sys.platform == "win32"
    vars_dict = {}

    # 1. Strip outer shell execution quotes first
    stripped = cmd_str.strip()
    pattern = r'(?i)^(?:cmd(?:\.exe)?(?:\s+[\/\-][a-zA-Z]+)*\s+[\/\-][ckq]\s*|sh\s+\-c\s*|bash\s+\-c\s*|zsh\s+\-c\s*|ash\s+\-c\s*|dash\s+\-c\s*|powershell\s+\-c\s*|pwsh\s+\-c\s*)(["\'])(.*)\1\s*$'
    m = re.match(pattern, stripped)
    if m:
        stripped = m.group(2)
    print(f"DEBUG_RECONSTRUCT: cmd_str={cmd_str!r} stripped={stripped!r}")

    # 2. Split command strings into individual commands respecting quotes and escapes using a state-machine lexical scanner
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

    # 3. Clean carets (if Windows) and extract variable assignments to vars_dict
    for cmd in commands:
        cmd_clean = cmd.strip()
        if not cmd_clean:
            continue

        # Parse Windows SET syntax: set "VAR=VALUE" or set VAR=VALUE
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

        # Unix-like assignment or assignments without set prefix: VAR=VALUE or VAR='VALUE' or VAR="VALUE"
        assign_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(?:(["\'])(.*?)\2|([^"\'].*|))$', cmd_clean)
        if assign_match:
            var = assign_match.group(1).strip()
            if var.lower() not in ("set", "export"):
                val = assign_match.group(3) if assign_match.group(2) else assign_match.group(4)
                if is_windows:
                    var = var.replace("^", "")
                    val = val.replace("^", "")
                vars_dict[var] = val

    # 3. Perform substitutions
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
                        return str2 + val[idx + len(target):]
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
            r"!(\w+)(?:(?:~(-?\d+)(?:,(-?\d+))?)|(?::([^=!]+)=([^!]*)))?!",
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
                        return str2 + val[idx + len(target):]
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

    print(f"DEBUG_RECONSTRUCT: vars_dict={vars_dict} reconstructed={reconstructed!r}")
    return reconstructed


def _check_subprocess_call_internal(
    cmd_args: Any, env: Any, stdin: Any, exec_path: Any, guards: list["HarnessGuard"]
) -> None:
    print(f"DEBUG_CONCAT: cmd_args={cmd_args} guards={len(guards)}")
    if not guards:
        return

    # Extract exec_str first to use in checks
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

    # 1. Check executable path
    if exec_str:
        for g in guards:
            if g._is_sensitive(exec_str) and not g._is_approved(exec_str):
                raise PermissionError(f"Access to sensitive file blocked in subprocess: {exec_str}")

    # 2. Check stdin piping to python/shell interpreters
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

    # A. Check shell redirection bypass combined with interpreter execution
    joined_cmd_lower = " ".join(arg.replace("^", "") for arg in normalized_args).lower()
    has_redirection = ">" in joined_cmd_lower or "|" in joined_cmd_lower or "<" in joined_cmd_lower
    interpreters_pattern = r"\b(python\d*|cmd|bash|sh|powershell|pwsh|zsh|ash|dash)(?:\.exe)?\b"
    has_interpreter = re.search(interpreters_pattern, joined_cmd_lower) is not None
    if has_redirection and has_interpreter:
        raise PermissionError(
            "Shell redirection combined with interpreter execution is blocked under HarnessGuard"
        )

    # B. Check for execution of written files during active guard context
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

    # C. Check list comprehension and dynamic AST string builders in python child commands
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
            # Check for blocked libraries/functions
            blocked_pattern = r"\b(reduce|functools|codecs|rot_13|rot13|rot-13|zlib|gzip|bz2|lzma|zipfile|tarfile|pickle|marshal)\b"
            if re.search(blocked_pattern, arg_str_clean, re.IGNORECASE):
                raise PermissionError(
                    f"Blocked library or function detected in python subprocess: {arg_str_clean}"
                )
            # Check list comprehension
            if re.search(r"\[.*for.*in.*\]", arg_str_clean):
                raise PermissionError(
                    "List comprehension in python subprocess is blocked under HarnessGuard"
                )
            # Check loop patterns
            if re.search(r"\bfor\b", arg_str_clean) or re.search(r"\bwhile\b", arg_str_clean):
                raise PermissionError(
                    "Loop pattern in python subprocess is blocked under HarnessGuard"
                )
            # Check string slice with step
            if re.search(r"\[[^\]]*:[^\]]*:[^\]]*\]", arg_str_clean) or "::" in arg_str_clean:
                raise PermissionError(
                    "String slice with step in python subprocess is blocked under HarnessGuard"
                )
            # Check calls to .join(), .replace(), etc.
            if re.search(r"\.join\s*\(", arg_str_clean) or re.search(
                r"\.replace\s*\(", arg_str_clean
            ):
                raise PermissionError(
                    "Calling join/replace in python subprocess is blocked under HarnessGuard"
                )
            # Check getattr(..., 'replace'/'join') calls
            if re.search(r"\bgetattr\b", arg_str_clean) and (
                re.search(r"['\"]replace['\"]", arg_str_clean)
                or re.search(r"['\"]join['\"]", arg_str_clean)
            ):
                raise PermissionError(
                    "Calling getattr for join/replace in python subprocess is blocked under HarnessGuard"
                )
            # Check format calls or modulo operator
            if (
                re.search(r"\.format\s*\(", arg_str_clean)
                or re.search(r"%\s*\(", arg_str_clean)
                or re.search(r"%\s*\'", arg_str_clean)
                or re.search(r"%\s*\"", arg_str_clean)
            ):
                raise PermissionError(
                    "String formatting in python subprocess is blocked under HarnessGuard"
                )

    # 3. Check individual command arguments and obfuscation FIRST to ensure correct error category
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
            tree = ast.parse(arg_str)  # Parse original arg_str with carets intact!
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

        # Split into words for wildcard/standard checking
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

    # Combine list arguments to detect split-path/split-keyword reconstruction AFTER individual argument checks
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

    # 4. Check environment variables (modified/new keys compared with snapshot taken at enter)
    if env is not None:
        snapshot = guards[-1]._env_snapshot if hasattr(guards[-1], "_env_snapshot") else {}
        modified_keys = []
        for k, _ in env.items():
            if k not in snapshot or env[k] != snapshot[k]:
                modified_keys.append(k)

        # Sort modified/new keys alphabetically
        modified_keys.sort()

        # Concatenate modified environment variable values
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

        # Run checks on individual modified environment variable values
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

    # Check if a shell interpreter is executed and AST parsing failed/was skipped
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
    event: str, cmd_args: Any, env: Any, guards: list["HarnessGuard"]
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


def _audit_hook(event: str, args: tuple[Any, ...]) -> None:
    if getattr(_local, "in_hook", None) is _HOOK_TOKEN:
        return
    guards = _get_active_guards()
    if not guards:
        return
    _local.in_hook = _HOOK_TOKEN
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
        _local.in_hook = None


def _wrapped_builtins_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    if getattr(_local, "in_hook", None) is _HOOK_TOKEN:
        return _original_builtins_open(file, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_builtins_open(file, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        for g in guards:
            g._check_file_access(file, args, kwargs)
        return _original_builtins_open(file, *args, **kwargs)
    finally:
        _local.in_hook = None


def _wrapped_io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    if getattr(_local, "in_hook", None) is _HOOK_TOKEN:
        return _original_io_open(file, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_io_open(file, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        for g in guards:
            g._check_file_access(file, args, kwargs)
        return _original_io_open(file, *args, **kwargs)
    finally:
        _local.in_hook = None


def _wrapped__io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    if getattr(_local, "in_hook", None) is _HOOK_TOKEN:
        return _original__io_open(file, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original__io_open(file, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        for g in guards:
            g._check_file_access(file, args, kwargs)
        return _original__io_open(file, *args, **kwargs)
    finally:
        _local.in_hook = None


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


def _inject_child_env(env_dict: Any, guards: list["HarnessGuard"]) -> dict:
    if env_dict is None:
        new_env = dict(os.environ)
    else:
        new_env = dict(env_dict)

    temp_dirs = [g._temp_dir for g in guards if hasattr(g, "_temp_dir") and g._temp_dir]
    if temp_dirs:
        # Prepend to PYTHONPATH
        existing_pythonpath = new_env.get("PYTHONPATH", "")
        # Add the package root directory too so the package can be imported in sitecustomize.py
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        package_root = os.path.dirname(current_file_dir)
        path_dirs = list(temp_dirs) + [package_root]

        if existing_pythonpath:
            path_dirs.append(existing_pythonpath)
        new_env["PYTHONPATH"] = os.pathsep.join(path_dirs)

        # Ensure HARNESS_ACTIVE and HARNESS_APPROVED_PATHS are set
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

    # After checking, if it is a python command, inject environment
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

        # normalized python matcher name
        def _is_python_cmd_name(cmd: str) -> bool:
            cmd_clean = cmd.replace("^", "").lower()
            base = os.path.basename(cmd_clean)
            if base.endswith(".exe"):
                base = base[:-4]
            if re.match(r"^(python[\d\.]*w?|pyw?[\d\.]*)$", base):
                return True
            return False

        # copied python detection
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

    old_in_hook = getattr(_local, "in_hook", None)
    _local.in_hook = _HOOK_TOKEN
    try:
        return _original_popen(*args_list, **kwargs)
    finally:
        _local.in_hook = old_in_hook


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


def _wrapped_os_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
    if _check_in_hook():
        return _original_os_open(path, flags, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_open(path, flags, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        file_str = os.fspath(path)
        if isinstance(file_str, bytes):
            file_str = file_str.decode("utf-8", errors="replace")

        for g in guards:
            if g._is_sensitive(file_str):
                if not g._is_approved(file_str):
                    raise PermissionError(f"Access to sensitive file blocked: {file_str}")

        is_write = (flags & (os.O_WRONLY | os.O_RDWR)) != 0
        if is_write:
            for g in guards:
                _safe_record_written_file(g, file_str)

        return _original_os_open(path, flags, *args, **kwargs)
    finally:
        _local.in_hook = None


def _wrapped_os_rename(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_rename(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_rename(src, dst, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        dst_str = os.fspath(dst)
        if isinstance(dst_str, bytes):
            dst_str = dst_str.decode("utf-8", errors="replace")

        for g in guards:
            if g._is_sensitive(dst_str):
                if not g._is_approved(dst_str):
                    raise PermissionError(f"Access to sensitive file blocked: {dst_str}")

        for g in guards:
            _safe_record_written_file(g, dst_str)

        return _original_os_rename(src, dst, *args, **kwargs)
    finally:
        _local.in_hook = None


def _wrapped_os_replace(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_replace(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_replace(src, dst, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        dst_str = os.fspath(dst)
        if isinstance(dst_str, bytes):
            dst_str = dst_str.decode("utf-8", errors="replace")

        for g in guards:
            if g._is_sensitive(dst_str):
                if not g._is_approved(dst_str):
                    raise PermissionError(f"Access to sensitive file blocked: {dst_str}")

        for g in guards:
            _safe_record_written_file(g, dst_str)

        return _original_os_replace(src, dst, *args, **kwargs)
    finally:
        _local.in_hook = None


class _WrappedFileIO(_original_io_FileIO):
    def __init__(self, file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(file, mode, *args, **kwargs)
            return

        guards = _get_active_guards()
        if not guards:
            super().__init__(file, mode, *args, **kwargs)
            return

        _local.in_hook = _HOOK_TOKEN
        try:
            for g in guards:
                g._check_file_access(file, (mode,), kwargs)
            super().__init__(file, mode, *args, **kwargs)
        finally:
            _local.in_hook = None


class _Wrapped_io_FileIO(_original__io_FileIO):
    def __init__(self, file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(file, mode, *args, **kwargs)
            return

        guards = _get_active_guards()
        if not guards:
            super().__init__(file, mode, *args, **kwargs)
            return

        _local.in_hook = _HOOK_TOKEN
        try:
            for g in guards:
                g._check_file_access(file, (mode,), kwargs)
            super().__init__(file, mode, *args, **kwargs)
        finally:
            _local.in_hook = None


def _wrapped_sqlite3_connect(*args: Any, **kwargs: Any) -> Any:
    if _check_in_hook():
        return _original_sqlite3_connect(*args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_sqlite3_connect(*args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        database = args[0] if len(args) > 0 else kwargs.get("database")
        if database is not None:
            db_str = os.fspath(database)
            if isinstance(db_str, bytes):
                db_str = db_str.decode("utf-8", errors="replace")

            if db_str != ":memory:" and db_str.lower() != ":memory:":
                _check_db_path(db_str)

        kwargs["factory"] = _Wrappedsqlite3Connection
        return _original_sqlite3_connect(*args, **kwargs)
    finally:
        _local.in_hook = None


def _wrapped_os_link(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_link(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_link(src, dst, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        src_str = os.fspath(src)
        if isinstance(src_str, bytes):
            src_str = src_str.decode("utf-8", errors="replace")
        dst_str = os.fspath(dst)
        if isinstance(dst_str, bytes):
            dst_str = dst_str.decode("utf-8", errors="replace")

        for g in guards:
            if g._is_sensitive(src_str) and not g._is_approved(src_str):
                raise PermissionError(f"Access to sensitive file blocked: {src_str}")
            if g._is_sensitive(dst_str) and not g._is_approved(dst_str):
                raise PermissionError(f"Access to sensitive file blocked: {dst_str}")

        for g in guards:
            _safe_record_written_file(g, dst_str)

        return _original_os_link(src, dst, *args, **kwargs)
    finally:
        _local.in_hook = None


def _wrapped_os_symlink(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_symlink(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_symlink(src, dst, *args, **kwargs)

    _local.in_hook = _HOOK_TOKEN
    try:
        src_str = os.fspath(src)
        if isinstance(src_str, bytes):
            src_str = src_str.decode("utf-8", errors="replace")
        dst_str = os.fspath(dst)
        if isinstance(dst_str, bytes):
            dst_str = dst_str.decode("utf-8", errors="replace")

        for g in guards:
            if g._is_sensitive(src_str) and not g._is_approved(src_str):
                raise PermissionError(f"Access to sensitive file blocked: {src_str}")
            if g._is_sensitive(dst_str) and not g._is_approved(dst_str):
                raise PermissionError(f"Access to sensitive file blocked: {dst_str}")

        for g in guards:
            _safe_record_written_file(g, dst_str)

        return _original_os_symlink(src, dst, *args, **kwargs)
    finally:
        _local.in_hook = None


def _make_os_wrapper(name: str, original_func: Callable) -> Callable:
    @wraps(original_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if _check_in_hook():
            return original_func(*args, **kwargs)

        args_list = list(args)
        _local.in_hook = _HOOK_TOKEN
        try:
            _check_subprocess_call(name, tuple(args_list), kwargs)

            # Inject PYTHONPATH env for os.spawn/exec if python command
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
            _local.in_hook = None

    return wrapper


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

    def __enter__(self) -> "HarnessGuard":
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
        from ccba_legal.harness import HarnessGuard
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
        os.environ["HARNESS_ACTIVE"] = "1"
        os.environ["HARNESS_APPROVED_PATHS"] = os.pathsep.join(self.approved_paths)

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
            os.environ.pop("HARNESS_ACTIVE", None)
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
            os.environ["HARNESS_APPROVED_PATHS"] = os.pathsep.join(all_approved)

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

        try:
            st = os.stat(abs_path)
            if (st.st_dev, st.st_ino) in _sensitive_inodes:
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
            return True

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

            # Exclude sitecustomize.py or guard's own temporary directory files from tracking
            abs_file_path = os.path.normcase(os.path.abspath(file_str))
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
                    self._written_files.add(os.path.normcase(os.path.abspath(file_str)))
            if file_str.lower().endswith(".py") and is_write:
                with self._write_lock:
                    self._written_py_files.add(os.path.abspath(file_str))

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
        package_dir = os.path.dirname(current_file_dir)

        cmd_pytest = [sys.executable, "-m", "pytest", package_dir]
        res_pytest = subprocess.run(cmd_pytest, capture_output=True, text=True)
        if res_pytest.returncode != 0:
            raise RuntimeError(
                f"pytest failed for package {package_dir} (exit code {res_pytest.returncode}).\n"
                f"STDOUT:\n{res_pytest.stdout}\n"
                f"STDERR:\n{res_pytest.stderr}"
            )
