"""Migration Tool: Remove `sys.path.insert` Boilerplate from Spoke Python Codebases.

Scans all Python files in a Spoke workspace, detects anti-pattern sys.path manipulations,
and cleans them up to use standard package imports provided by editable installs (ADR 0044).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SYS_PATH_PATTERNS = [
    # Match HUB_SRC = Path(...)
    re.compile(r"^\s*HUB_SRC\s*=\s*Path\(.*?\).*?$", re.MULTILINE),
    # Match sys.path.insert(0, str(HUB_SRC))
    re.compile(r"^\s*sys\.path\.insert\(\s*0\s*,\s*str\(\s*HUB_SRC\s*\)\s*\).*?$", re.MULTILINE),
    # Match sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) or similar
    re.compile(
        r"^\s*sys\.path\.insert\(\s*0\s*,\s*str\(Path\(__file__\).*?\)\s*\).*?$", re.MULTILINE
    ),
    # Match sys.path.insert(0, str(root_dir)) where root_dir is parent
    re.compile(r"^\s*sys\.path\.insert\(\s*0\s*,\s*str\(\s*root_dir\s*\)\s*\).*?$", re.MULTILINE),
]


class SysPathMigration:
    """Scans and refactors Spoke python scripts removing sys.path hacks."""

    def __init__(self, spoke_root: Path | str):
        self.spoke_root = Path(spoke_root).resolve()

    def scan_and_clean_file(
        self, py_file: Path, dry_run: bool = False, backup: bool = True
    ) -> bool:
        """Cleans a single python file. Returns True if file was modified."""
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            return False

        original_content = content
        cleaned = content

        for pattern in SYS_PATH_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # Clean up consecutive empty lines that might have been left behind
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        if cleaned != original_content:
            rel_path = py_file.relative_to(self.spoke_root)
            print(f"  ✨ Detected sys.path boilerplate in: {rel_path}")

            if not dry_run:
                if backup:
                    backup_file = py_file.with_suffix(".py.bak")
                    shutil.copy2(py_file, backup_file)
                py_file.write_text(cleaned, encoding="utf-8")
                print(f"     -> Cleaned successfully{' (backup created)' if backup else ''}")
            else:
                print("     -> [DRY-RUN] Would remove boilerplate lines")
            return True
        return False

    def run(self, dry_run: bool = False, backup: bool = True) -> int:
        print("\n=== CCBA Spoke sys.path Migration Tool ===")
        print(f"Target Spoke: {self.spoke_root}")

        modified_count = 0
        total_scanned = 0

        # Scan all .py files in spoke (excluding .venv, venv, .git, etc.)
        for py_file in self.spoke_root.rglob("*.py"):
            # Skip virtualenvs and caches
            parts = py_file.parts
            if any(
                p
                in [
                    ".venv",
                    "venv",
                    ".git",
                    "__pycache__",
                    ".pytest_cache",
                    ".ruff_cache",
                    "build",
                    "dist",
                ]
                for p in parts
            ):
                continue

            total_scanned += 1
            if self.scan_and_clean_file(py_file, dry_run=dry_run, backup=backup):
                modified_count += 1

        print(
            f"\nTổng kết: Đã quét {total_scanned} tệp .py, phát hiện và xử lý {modified_count} tệp."
        )
        if dry_run and modified_count > 0:
            print("Chạy lại mà không có cờ `--dry-run` để áp dụng thay đổi.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Spoke sys.path hacks to standard imports")
    parser.add_argument(
        "--spoke", "-s", default=".", help="Path to Spoke repository (default: current dir)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument("--no-backup", action="store_true", help="Do not create .bak backup files")

    args = parser.parse_args()
    migration = SysPathMigration(spoke_root=args.spoke)
    return migration.run(dry_run=args.dry_run, backup=not args.no_backup)


if __name__ == "__main__":
    sys.exit(main())
