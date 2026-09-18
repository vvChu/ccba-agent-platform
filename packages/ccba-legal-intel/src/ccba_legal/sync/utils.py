"""Hash, Port, and Filesystem Hardening Utilities for Legal Sync Module."""

from __future__ import annotations

import hashlib
import os
import shutil
import socket
import stat
import subprocess
import sys
import time
from pathlib import Path


def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 hash of file for Google Drive matching."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of file for local cache audit."""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def is_port_open(port: int, timeout: float = 1.0) -> bool:
    """Check if TCP port is active with enforced Windows socket timeout ceiling."""
    try:
        safe_timeout = max(0.05, min(float(timeout), 1.0))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(safe_timeout)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def ensure_chrome_debug_port() -> bool:
    """Detect and launch Google Chrome in debug port 9222 mode if inactive."""
    if is_port_open(9222):
        return True

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    if not chrome_path:
        return False

    try:
        user_data_dir = os.path.join(
            os.path.expanduser("~"), ".gemini", "antigravity", "chrome-debug-profile"
        )
        os.makedirs(user_data_dir, exist_ok=True)

        cmd = [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for _ in range(10):
            time.sleep(0.5)
            if is_port_open(9222):
                return True
        return False
    except Exception:
        return False


def _is_link_or_junction(path: Path) -> bool:
    """Check if path is a symlink or Windows NTFS directory junction / reparse point."""
    try:
        st = os.lstat(path)
        if stat.S_ISLNK(st.st_mode):
            return True
        if sys.platform == "win32":
            reparse_attr = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
            if (
                getattr(st, "st_file_attributes", 0) & reparse_attr
                and getattr(st, "st_reparse_tag", 0) == mount_point_tag
            ):
                return True
    except OSError:
        pass
    return path.is_symlink()


def safe_copy2(
    src: str | Path,
    dst: str | Path,
    max_retries: int = 3,
    retry_delay: float = 0.1,
    *,
    follow_symlinks: bool = True,
) -> str | Path:
    """Copy file with self-copy guard, Windows Read-Only clearance, and retry on file locks."""
    src_p = Path(src)
    dst_p = Path(dst)

    # Determine actual target file path (handling case where dst is an existing directory)
    if dst_p.is_dir():
        actual_dst_p = dst_p / src_p.name
    else:
        actual_dst_p = dst_p

    try:
        if src_p.resolve() == actual_dst_p.resolve():
            return str(actual_dst_p) if isinstance(dst, str) else actual_dst_p
    except OSError:
        pass

    # Ensure destination parent directory exists
    actual_dst_p.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries):
        try:
            if actual_dst_p.exists() and not _is_link_or_junction(actual_dst_p):
                try:
                    os.chmod(actual_dst_p, stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass
            copied = shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
            return copied
        except (PermissionError, OSError):
            try:
                if actual_dst_p.exists() and not _is_link_or_junction(actual_dst_p):
                    os.chmod(actual_dst_p, stat.S_IWRITE | stat.S_IREAD)
            except Exception:
                pass
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)
    return str(actual_dst_p) if isinstance(dst, str) else actual_dst_p


def _safe_remove_leaf(p: Path) -> None:
    """Safely remove a leaf item (file, symlink, or NTFS junction) without mutating target permissions."""
    if not p.is_symlink():
        try:
            os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass
    try:
        if os.name == "nt" and p.is_dir() and not p.is_symlink():
            os.rmdir(p)
        else:
            p.unlink()
    except FileNotFoundError:
        pass


def _safe_remove_dir(p: Path) -> None:
    """Safely remove an empty directory after clearing read-only attributes."""
    try:
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
    except Exception:
        pass
    try:
        os.rmdir(p)
    except FileNotFoundError:
        pass


def _safe_rmtree_tree(p: Path) -> None:
    """Recursively remove directory contents, treating symlinks and NTFS junctions as non-traversed leaves."""
    if not p.exists() and not _is_link_or_junction(p):
        return
    try:
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
    except Exception:
        pass
    try:
        with os.scandir(p) as it:
            for entry in it:
                entry_path = Path(entry.path)
                if _is_link_or_junction(entry_path) or not entry.is_dir(follow_symlinks=False):
                    _safe_remove_leaf(entry_path)
                else:
                    _safe_rmtree_tree(entry_path)
    except FileNotFoundError:
        return
    _safe_remove_dir(p)


def safe_remove(
    path: str | Path,
    max_retries: int = 3,
    retry_delay: float = 0.1,
) -> None:
    """Safely remove a file, symlink, junction, or directory handling Windows Read-Only permissions and locks (RULE-2.7)."""
    p = Path(path)
    if not p.exists() and not _is_link_or_junction(p):
        return

    # Handle symlinks, Windows directory junctions, and files
    if _is_link_or_junction(p) or p.is_file():
        for attempt in range(max_retries):
            try:
                _safe_remove_leaf(p)
                return
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)
        return

    # Directory tree removal (junction and symlink safe)
    for attempt in range(max_retries):
        try:
            _safe_rmtree_tree(p)
            if not p.exists() and not _is_link_or_junction(p):
                return
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)


safe_rmtree = safe_remove
