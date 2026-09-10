"""base.py - Base Constants, Exceptions, and Utilities for Spoke Synchronization.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

HAS_CRYPTOGRAPHY = importlib.util.find_spec("cryptography") is not None
PLATFORM_ROOT = Path(__file__).resolve().parents[3]


class HubNotFoundError(Exception):
    """Raised when the CCBA Hub directory cannot be located."""

    pass


def load_yaml(file_path: Path) -> dict[str, Any]:
    """Safely load a YAML file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[Sync] Error reading {file_path.name}: {e}", file=sys.stderr)
        return {}


def are_files_identical(file1: Path, file2: Path) -> bool:
    """Compare two files by byte content."""
    if not file1.exists() or not file2.exists():
        return False
    try:
        return file1.read_bytes() == file2.read_bytes()
    except Exception:
        return False


def are_dirs_identical(dir1: Path, dir2: Path) -> bool:
    """Recursively compare two directories by file contents."""
    if not dir1.exists() or not dir2.exists():
        return False

    files1 = {p.relative_to(dir1): p for p in dir1.rglob("*") if p.is_file()}
    files2 = {p.relative_to(dir2): p for p in dir2.rglob("*") if p.is_file()}

    if set(files1.keys()) != set(files2.keys()):
        return False

    for rel_path, f1 in files1.items():
        f2 = files2[rel_path]
        try:
            if f1.read_bytes() != f2.read_bytes():
                return False
        except Exception:
            return False

    return True


def safe_remove(path: Path) -> None:
    """Safely remove a directory, file, or symlink without crashing on permission/type errors."""
    if not path.exists() and not path.is_symlink():
        return
    try:
        if path.is_file() or path.is_symlink():
            try:
                path.unlink()
            except PermissionError:
                path.chmod(0o777)
                path.unlink()
        else:
            shutil.rmtree(path, ignore_errors=False)
    except Exception:
        # Fallback for locked directories or files
        if path.is_file() or path.is_symlink():
            try:
                path.chmod(0o777)
                path.unlink()
            except Exception:
                pass
        elif path.is_dir():
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        os.chmod(file_path, 0o777)
                        os.remove(file_path)
                    except Exception:
                        pass
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        os.chmod(dir_path, 0o777)
                        os.rmdir(dir_path)
                    except Exception:
                        pass
            try:
                os.rmdir(path)
            except Exception:
                pass

