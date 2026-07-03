from __future__ import annotations

import ast
import base64
import os
import re
import threading
import unicodedata
import zlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._guard import HarnessGuard

from ._state import (
    _HOOK_TOKEN,
    _check_in_hook,
    _get_active_guards,
    _local,
    _lock,
    _original__io_FileIO,
    _original__io_open,
    _original_builtins_open,
    _original_io_FileIO,
    _original_io_open,
    _original_os_link,
    _original_os_open,
    _original_os_rename,
    _original_os_replace,
    _original_os_symlink,
    _scanned_dirs,
    _sensitive_inodes,
    _sensitivity_cache,
)


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


def _check_value_for_sensitive(val: Any, guards: list[HarnessGuard]) -> None:
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


def _wrapped_builtins_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    if getattr(_local, "in_hook", None) is _HOOK_TOKEN:
        return _original_builtins_open(file, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_builtins_open(file, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        for g in guards:
            g._check_file_access(file, args, kwargs)
        return _original_builtins_open(file, *args, **kwargs)
    finally:
        _local.__dict__["in_hook"] = None


def _wrapped_io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    if getattr(_local, "in_hook", None) is _HOOK_TOKEN:
        return _original_io_open(file, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_io_open(file, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        for g in guards:
            g._check_file_access(file, args, kwargs)
        return _original_io_open(file, *args, **kwargs)
    finally:
        _local.__dict__["in_hook"] = None


def _wrapped__io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    if getattr(_local, "in_hook", None) is _HOOK_TOKEN:
        return _original__io_open(file, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original__io_open(file, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        for g in guards:
            g._check_file_access(file, args, kwargs)
        return _original__io_open(file, *args, **kwargs)
    finally:
        _local.__dict__["in_hook"] = None


def _wrapped_os_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
    if _check_in_hook():
        return _original_os_open(path, flags, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_open(path, flags, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
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
        _local.__dict__["in_hook"] = None


def _wrapped_os_rename(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_rename(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_rename(src, dst, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
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
        _local.__dict__["in_hook"] = None


def _wrapped_os_replace(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_replace(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_replace(src, dst, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
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
        _local.__dict__["in_hook"] = None


class _WrappedFileIO(_original_io_FileIO):
    def __init__(self, file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(file, mode, *args, **kwargs)
            return

        guards = _get_active_guards()
        if not guards:
            super().__init__(file, mode, *args, **kwargs)
            return

        _local.__dict__["in_hook"] = _HOOK_TOKEN
        try:
            for g in guards:
                g._check_file_access(file, (mode,), kwargs)
            super().__init__(file, mode, *args, **kwargs)
        finally:
            _local.__dict__["in_hook"] = None


class _Wrapped_io_FileIO(_original__io_FileIO):
    def __init__(self, file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(file, mode, *args, **kwargs)
            return

        guards = _get_active_guards()
        if not guards:
            super().__init__(file, mode, *args, **kwargs)
            return

        _local.__dict__["in_hook"] = _HOOK_TOKEN
        try:
            for g in guards:
                g._check_file_access(file, (mode,), kwargs)
            super().__init__(file, mode, *args, **kwargs)
        finally:
            _local.__dict__["in_hook"] = None


def _wrapped_os_link(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_link(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_link(src, dst, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
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
        _local.__dict__["in_hook"] = None


def _wrapped_os_symlink(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    if _check_in_hook():
        return _original_os_symlink(src, dst, *args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_os_symlink(src, dst, *args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
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
        _local.__dict__["in_hook"] = None
