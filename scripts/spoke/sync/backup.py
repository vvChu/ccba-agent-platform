"""backup.py - Git Working Tree Guard & Spoke Snapshot Backup/Rollback Manager.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import safe_remove


class GitWorkingTreeGuard:
    """Guard checking Spoke Git working tree for uncommitted changes to prevent accidental overwrites."""

    def __init__(self, spoke_root: Path) -> None:
        self.spoke_root = spoke_root

    def is_git_repo(self) -> bool:
        """Check if spoke is located inside a git repository."""
        return (self.spoke_root / ".git").exists() or (self.spoke_root.parent / ".git").exists()

    def check_clean_working_tree(self, path_filter: str = ".agents") -> tuple[bool, str]:
        """Check if working tree is clean under specified path filter.

        Returns:
            Tuple of (is_clean, dirty_details_str)
        """
        if not self.is_git_repo():
            return True, ""

        try:
            cmd = ["git", "status", "--porcelain"]
            if path_filter:
                cmd.append(path_filter)
            res = subprocess.run(
                cmd,
                cwd=str(self.spoke_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if res.returncode != 0:
                return True, ""

            output = res.stdout.strip()
            if output:
                return False, output
            return True, ""
        except Exception:
            return True, ""


class SpokeBackupManager:
    """Snapshot Backup & Rollback Engine for Spoke .agents workspace."""

    MAX_SNAPSHOTS: int = 5

    def __init__(self, spoke_root: Path) -> None:
        self.spoke_root = spoke_root
        self.backup_root = self._resolve_backup_dir()

    def _resolve_backup_dir(self) -> Path:
        """Determine backup root directory (.md/backups or .agents_backups)."""
        md_dir = self.spoke_root / ".md"
        if md_dir.exists():
            return md_dir / "backups"
        return self.spoke_root / ".md" / "backups"

    def prune_backups(self, max_snapshots: int = MAX_SNAPSHOTS) -> list[Path]:
        """Prunes oldest backup snapshots exceeding max_snapshots retention policy.

        Returns:
            List of removed backup paths.
        """
        backups = self.list_backups()
        removed: list[Path] = []
        if len(backups) > max_snapshots:
            for old_backup in backups[max_snapshots:]:
                try:
                    safe_remove(old_backup)
                    removed.append(old_backup)
                except Exception as e:
                    print(
                        f"[SpokeBackupManager] Warning: failed to prune old backup {old_backup}: {e}",
                        file=sys.stderr,
                    )
        return removed

    def create_backup(self) -> Path | None:
        """Create a timestamped snapshot backup of .agents/ directory.

        Returns:
            Path to created snapshot directory, or None if .agents/ does not exist.
        """
        agents_dir = self.spoke_root / ".agents"
        if not agents_dir.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_root.mkdir(parents=True, exist_ok=True)
        prefix = f"agents_backup_{timestamp}"
        existing_matches = list(self.backup_root.glob(f"{prefix}*"))
        if existing_matches:
            counters: list[int] = []
            pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
            for b in existing_matches:
                m = pattern.match(b.name)
                if m:
                    counters.append(int(m.group(1)))
            next_counter = (max(counters) + 1) if counters else 1
            backup_dest = self.backup_root / f"{prefix}_{next_counter}"
        else:
            backup_dest = self.backup_root / prefix

        shutil.copytree(agents_dir, backup_dest, dirs_exist_ok=True)
        self.prune_backups()
        return backup_dest

    @staticmethod
    def _backup_sort_key(p: Path) -> tuple[Any, ...]:
        """Extract sort key giving strict chronological ordering (newest first)."""
        m = re.search(r"(\d{8})_(\d{6})(?:_(\d+))?", p.name)
        if m:
            date_str, time_str, counter_str = m.groups()
            counter = int(counter_str) if counter_str else 0
            return (date_str, time_str, counter)
        try:
            return ("", "", int(p.stat().st_mtime))
        except Exception:
            return ("", "", 0)

    def list_backups(self) -> list[Path]:
        """List all available backup snapshots ordered by newest first."""
        if not self.backup_root.exists():
            return []
        backups = [
            p
            for p in self.backup_root.iterdir()
            if p.is_dir()
            and (p.name.startswith("agents_backup_") or p.name.startswith(".agents.bak"))
        ]
        return sorted(backups, key=self._backup_sort_key, reverse=True)

    def restore_backup(self, backup_path: Path | None = None) -> bool:
        """Restore .agents/ directory from a specific backup or latest snapshot.

        Returns:
            True if restored successfully, False otherwise.
        """
        target_backup = backup_path
        if target_backup is None:
            backups = self.list_backups()
            if not backups:
                print(f"[Backup] No backups found in {self.backup_root}", file=sys.stderr)
                return False
            target_backup = backups[0]

        if not target_backup.exists() or not target_backup.is_dir():
            print(f"[Backup] Backup directory does not exist: {target_backup}", file=sys.stderr)
            return False

        agents_dir = self.spoke_root / ".agents"
        try:
            if agents_dir.exists():
                safe_remove(agents_dir)
            shutil.copytree(target_backup, agents_dir, dirs_exist_ok=True)
            print(f"[Backup] Successfully restored .agents/ from {target_backup.name}")
            return True
        except Exception as e:
            print(f"[Backup] Failed to restore backup: {e}", file=sys.stderr)
            return False
