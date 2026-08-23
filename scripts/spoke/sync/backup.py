"""backup.py - Git Working Tree Guard & Spoke Snapshot Backup/Rollback Manager.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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

    def __init__(self, spoke_root: Path) -> None:
        self.spoke_root = spoke_root
        self.backup_root = self._resolve_backup_dir()

    def _resolve_backup_dir(self) -> Path:
        """Determine backup root directory (.md/backups or .agents_backups)."""
        md_dir = self.spoke_root / ".md"
        if md_dir.exists():
            return md_dir / "backups"
        return self.spoke_root / ".md" / "backups"

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
        backup_dest = self.backup_root / f"agents_backup_{timestamp}"

        counter = 1
        while backup_dest.exists():
            backup_dest = self.backup_root / f"agents_backup_{timestamp}_{counter}"
            counter += 1

        shutil.copytree(agents_dir, backup_dest, dirs_exist_ok=True)
        return backup_dest

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
        return sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)

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
