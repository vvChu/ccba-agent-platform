"""Hash and Port Utilities for Legal Sync Module."""

from __future__ import annotations

import hashlib
import os
import socket
import subprocess
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


def is_port_open(port: int) -> bool:
    """Check if TCP port is active."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


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
