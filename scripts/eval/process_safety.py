#!/usr/bin/env python3
"""process_safety.py - Process Safety Infrastructure Utilities for CCBA Platform.

Tập trung các hàm dùng chung về an toàn tiến trình:
- Singleton Process Lock (bảo vệ tuyệt đối os.getpid() và os.getppid())
- Recursive Process Tree Termination (psutil + taskkill fallback)
- Venv Python Interpreter Resolution
"""

import os
import subprocess
import sys
from pathlib import Path


def ensure_single_instance(script_keyword: str) -> None:
    """Tự động kiểm tra và triệt hạ các tiến trình chạy ngầm bị trùng lặp/treo từ trước.
    
    CRITICAL INVARIANT: Bắt buộc loại trừ cả os.getpid() (tiến trình hiện tại)
    và os.getppid() (tiến trình cha/Agent host) để không làm sập Agent Server.
    """
    current_pid = os.getpid()
    parent_pid = getattr(os, "getppid", lambda: None)()

    try:
        import psutil

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                pid = proc.info["pid"]
                if pid == current_pid or (parent_pid and pid == parent_pid):
                    continue
                cmdline = " ".join(proc.info["cmdline"] or [])
                if script_keyword in cmdline:
                    print(
                        f"🧹 [AUTO-LOCK] Phát hiện tiến trình {script_keyword} cũ (PID {pid}). Đang thu hồi..."
                    )
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except ImportError:
        if sys.platform == "win32":
            try:
                res = subprocess.run(
                    [
                        "wmic",
                        "process",
                        "where",
                        "name='python.exe'",
                        "get",
                        "processid,commandline",
                    ],
                    capture_output=True,
                    text=True,
                )
                for line in res.stdout.splitlines():
                    if script_keyword in line:
                        parts = line.strip().rsplit(maxsplit=1)
                        if len(parts) == 2 and parts[1].isdigit():
                            pid = int(parts[1])
                            if pid != current_pid and (not parent_pid or pid != parent_pid):
                                print(f"🧹 [AUTO-LOCK] Thu hồi tiến trình trùng lặp PID {pid}...")
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", str(pid)], capture_output=True
                                )
            except Exception:
                pass


def kill_process_tree(pid: int) -> None:
    """Tiêu diệt đệ quy toàn bộ cây tiến trình (process tree) trên Windows/Linux."""
    try:
        import psutil

        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        parent.kill()
    except Exception:
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                )
            except Exception:
                pass


def get_venv_python(project_root: Path) -> str:
    """Trả về đường dẫn tới python trong .venv nếu có, fallback sys.executable."""
    venv_win = project_root / ".venv" / "Scripts" / "python.exe"
    if venv_win.exists():
        return str(venv_win)
    venv_nix = project_root / ".venv" / "bin" / "python"
    if venv_nix.exists():
        return str(venv_nix)
    return sys.executable
