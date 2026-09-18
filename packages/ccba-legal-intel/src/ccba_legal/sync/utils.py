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
from typing import Any


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


def safe_copy2(
    src: str | Path,
    dst: str | Path,
    max_retries: int = 3,
    retry_delay: float = 0.1,
) -> str | Path:
    """Copy file with self-copy guard, Windows Read-Only clearance, and retry on file locks."""
    src_p = Path(src)
    dst_p = Path(dst)

    try:
        if src_p.resolve() == dst_p.resolve():
            return dst
    except OSError:
        pass

    for attempt in range(max_retries):
        try:
            if dst_p.exists():
                try:
                    os.chmod(dst_p, stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass
            shutil.copy2(src, dst)
            return dst
        except (PermissionError, OSError):
            try:
                if dst_p.exists():
                    os.chmod(dst_p, stat.S_IWRITE | stat.S_IREAD)
            except Exception:
                pass
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)
    return dst


def _handle_remove_readonly(func: Any, path: str, exc_info: Any) -> None:
    """Clear Read-Only bit and reattempt removal for Python <= 3.11 onerror hook."""
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    func(path)


def _handle_remove_readonly_onexc(func: Any, path: str, exc: Exception) -> None:
    """Clear Read-Only bit and reattempt removal for Python 3.12+ onexc hook."""
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    func(path)


def safe_remove(
    path: str | Path,
    max_retries: int = 3,
    retry_delay: float = 0.1,
) -> None:
    """Safely remove a file, symlink, or directory handling Windows Read-Only permissions and locks (RULE-2.7)."""
    p = Path(path)
    if not p.exists() and not p.is_symlink():
        return

    if p.is_symlink() or p.is_file():
        for attempt in range(max_retries):
            try:
                try:
                    os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass
                p.unlink()
                return
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)
        return

    # Directory removal
    for attempt in range(max_retries):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(p, onexc=_handle_remove_readonly_onexc)
            else:
                shutil.rmtree(p, onerror=_handle_remove_readonly)
            return
        except Exception:
            if not p.exists():
                return
            # Fallback: reverse-walk, chmod, and delete
            for root, dirs, files in os.walk(p, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                        os.remove(file_path)
                    except Exception:
                        pass
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD)
                        os.rmdir(dir_path)
                    except Exception:
                        pass
            try:
                os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
                os.rmdir(p)
                return
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)


safe_rmtree = safe_remove
