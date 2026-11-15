"""base.py - Base Constants, Exceptions, and Utilities for Spoke Synchronization.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import tempfile
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


def are_text_files_identical(file1: Path, file2: Path) -> bool:
    """Compare two text files normalizing newline differences (CRLF vs LF)."""
    if not file1.exists() or not file2.exists():
        return False
    try:
        content1 = file1.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        content2 = file2.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        return content1 == content2
    except Exception:
        return False


SKILL_SYNC_IGNORE_DIRS: frozenset[str] = frozenset({".skill_versions", "__pycache__"})
SKILL_SYNC_IGNORE_PATTERNS = shutil.ignore_patterns(".skill_versions", "__pycache__", "*.pyc")


def _is_ignored_sync_path(rel_path: Path) -> bool:
    """Return True if a relative path inside a skill directory should be ignored during sync."""
    return bool(set(rel_path.parts) & SKILL_SYNC_IGNORE_DIRS) or rel_path.suffix == ".pyc"


def are_dirs_identical(dir1: Path, dir2: Path) -> bool:
    """Recursively compare two directories by file contents, ignoring transient local directories."""
    if not dir1.exists() or not dir2.exists():
        return False

    files1 = {
        p.relative_to(dir1): p
        for p in dir1.rglob("*")
        if p.is_file() and not _is_ignored_sync_path(p.relative_to(dir1))
    }
    files2 = {
        p.relative_to(dir2): p
        for p in dir2.rglob("*")
        if p.is_file() and not _is_ignored_sync_path(p.relative_to(dir2))
    }

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


_EPHEMERAL_POSIX_EXACT: frozenset[str] = frozenset({"/tmp", "/var/tmp", "/private/tmp"})
_EPHEMERAL_POSIX_PREFIXES: tuple[str, ...] = ("/tmp/", "/var/tmp/", "/private/tmp/")


def _is_under_os_temp_dir(candidate: Path) -> bool:
    """Return True when candidate resides strictly inside OS tempfile.gettempdir()."""
    try:
        temp_raw = Path(tempfile.gettempdir())
        temp_roots = {temp_raw, temp_raw.resolve()}
        candidates = {candidate}
        if candidate.is_absolute():
            candidates.add(candidate.resolve())
        for item in candidates:
            for root in temp_roots:
                if item != root and item.is_relative_to(root):
                    return True
    except (OSError, RuntimeError, ValueError):
        return False
    return False


def is_ephemeral_spoke_path(path_value: str | Path) -> bool:
    """Return True if path_value points to a pytest fixture, mock spoke, or OS temp worktree.

    Args:
        path_value: Spoke filesystem path string or Path object.

    Returns:
        True if the path matches pytest/mock markers or resides under an OS temporary directory.
    """
    raw = str(path_value).strip()
    if not raw:
        return False
    norm = raw.replace("\\", "/")
    if (
        "/pytest-of-" in norm
        or "/pytest-" in norm
        or "MOCK-TEST-SPOKE" in raw
        or norm in _EPHEMERAL_POSIX_EXACT
        or norm.startswith(_EPHEMERAL_POSIX_PREFIXES)
    ):
        return True
    return _is_under_os_temp_dir(Path(raw))


def prune_ephemeral_heartbeats(heartbeats: dict[str, Any]) -> dict[str, Any]:
    """Filter out ephemeral pytest/mock/OS-temp spoke entries from a heartbeats mapping.

    Args:
        heartbeats: Mapping of spoke_id to heartbeat metadata dicts.

    Returns:
        Sanitized dictionary containing only non-ephemeral dict entries.
    """
    return {
        k: v
        for k, v in heartbeats.items()
        if isinstance(v, dict) and not is_ephemeral_spoke_path(str(v.get("path", "")))
    }
