"""Filesystem path normalization, inode scanning, and escape-decoding utilities."""

from __future__ import annotations

import os
import re
import threading
import unicodedata
from typing import Any

from ._state import HarnessState

_SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "credential",
    "secret",
    "private_key",
    "password",
    "api_key",
    "token",
)

_SIMPLE_ESCAPE_BYTES: dict[int, int] = {
    92: 92,
    39: 39,
    34: 34,
    97: 7,
    98: 8,
    102: 12,
    110: 10,
    114: 13,
    116: 9,
    118: 11,
}


def _scan_dir_for_sensitive_inodes(base_dir: str) -> None:
    """Walk one workspace directory up to 1000 files and record sensitive inodes."""
    HarnessState.scanned_dirs.add(base_dir)
    skip_dirs = (".git", "__pycache__", "node_modules", ".venv", "venv", "env")
    scanned = 0
    try:
        for root, dirs, files in os.walk(base_dir):
            if scanned > 1000:
                break
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for filename in files:
                scanned += 1
                if scanned > 1000:
                    break
                f_lower = filename.lower()
                if any(kw in f_lower for kw in (*_SENSITIVE_KEYWORDS, ".env")):
                    try:
                        st = os.stat(os.path.join(root, filename))
                        HarnessState.sensitive_inodes.add((st.st_dev, st.st_ino))
                    except Exception:
                        pass
    except Exception:
        pass


def _scan_for_sensitive_inodes() -> None:
    """Scan current working directory once for sensitive filenames and cache their inodes."""
    dirs_to_scan: list[str] = []
    try:
        abs_d = os.path.normcase(os.path.abspath("."))
        if abs_d not in HarnessState.scanned_dirs:
            dirs_to_scan.append(abs_d)
    except Exception:
        pass
    for base_dir in dirs_to_scan:
        _scan_dir_for_sensitive_inodes(base_dir)


def _safe_record_written_file(g: Any, file_str: str) -> None:
    """Record a written file path (and `.py` path) on an active HarnessGuard."""
    if "harness_guard_" in file_str or "sitecustomize.py" in file_str:
        return
    raw_path = (
        os.fspath(file_str) if isinstance(file_str, (str, bytes, os.PathLike)) else str(file_str)
    )
    decoded_path = (
        raw_path.decode("utf-8", errors="replace") if isinstance(raw_path, bytes) else raw_path
    )
    norm_path = os.path.normcase(os.path.abspath(decoded_path))
    abs_path = os.path.abspath(norm_path)
    is_py = norm_path.lower().endswith(".py")

    lock = getattr(g, "_write_lock", None)
    if not lock:
        with HarnessState.lock:
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
    """Return True when a candidate string structurally resembles a filesystem path."""
    if not val:
        return False
    try:
        if os.path.exists(val):
            return True
    except Exception:
        pass
    if "/" in val or "\\" in val or val.startswith((".", "~")):
        return True
    if "." in val:
        ext = val.split(".")[-1]
        if ext.isalnum() and len(ext) <= 4:
            return True
    return False


def _get_workspace_files() -> list[str]:
    """Collect up to 1000 non-ignored file paths relative to `.`."""
    files: list[str] = []
    skip_dirs = (".git", "__pycache__", "node_modules", "venv", ".venv", "env", ".agents")
    try:
        for root, dirs, filenames in os.walk(".", topdown=True):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for filename in filenames:
                files.append(os.path.join(root, filename))
                if len(files) > 1000:
                    return files
    except Exception:
        pass
    return files


def _decode_hex_unicode_escape(b: bytes, i: int, n: int, nxt: int, res: bytearray) -> int:
    """Decode `\\xHH`, `\\uHHHH`, or `\\UHHHHHHHH` byte escapes; preserve literal on error."""
    hex_lengths = {120: 2, 117: 4, 85: 8}
    digits_len = hex_lengths[nxt]
    if i + 1 + digits_len < n:
        hex_digits = b[i + 2 : i + 2 + digits_len]
        try:
            val = int(hex_digits, 16)
            if nxt == 120:
                res.append(val)
            else:
                res.extend(chr(val).encode("utf-8"))
            return i + 2 + digits_len
        except Exception:
            pass
    res.extend((92, nxt))
    return i + 2


def _decode_octal_escape(b: bytes, i: int, n: int, res: bytearray) -> int:
    """Decode 1-3 digit octal byte escape (`\\ooo`)."""
    oct_len = 1
    if i + 2 < n and 48 <= b[i + 2] <= 55:
        oct_len = 2
        if i + 3 < n and 48 <= b[i + 3] <= 55:
            oct_len = 3
    val = int(b[i + 1 : i + 1 + oct_len], 8)
    res.append(val & 255)
    return i + 1 + oct_len


def _safe_escape_decode(b: bytes) -> bytes:
    """Safely decode backslash escape sequences in raw bytes without codecs exceptions."""
    res = bytearray()
    i, n = 0, len(b)
    while i < n:
        if b[i] != 92:
            res.append(b[i])
            i += 1
            continue
        if i + 1 >= n:
            res.append(92)
            break
        nxt = b[i + 1]
        if nxt in _SIMPLE_ESCAPE_BYTES:
            res.append(_SIMPLE_ESCAPE_BYTES[nxt])
            i += 2
        elif nxt in (120, 117, 85):
            i = _decode_hex_unicode_escape(b, i, n, nxt, res)
        elif 48 <= nxt <= 55:
            i = _decode_octal_escape(b, i, n, res)
        else:
            res.extend((92, nxt))
            i += 2
    return bytes(res)


def _is_text_sensitive(text: str) -> bool:
    """Return True when normalized text references sensitive credential keywords or `.env`."""
    if not isinstance(text, str):
        return False
    normalized = unicodedata.normalize("NFKC", text).lower()
    if any(kw in normalized for kw in _SENSITIVE_KEYWORDS):
        return True
    parts = re.split(r'[/\\\'"\s=,;()\[\]{}]', normalized)
    return any(p == ".env" or p.endswith(".env") for p in parts)
