#!/usr/bin/env python3
"""
CLI entrypoint for CCBA Spoke Selective Skills Synchronizer.
Delegates execution to the SpokeSynchronizer deep module.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Ensure sys.path contains platform root
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke import list_project_backups, rollback_project, sync_all_spokes, sync_project


def main() -> None:
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Spoke Selective Skills Synchronizer (Safe-by-Default)"
    )
    parser.add_argument(
        "--spoke",
        default=".",
        help="Path to the target spoke project folder (defaults to current directory).",
    )
    parser.add_argument(
        "--sync-item",
        default=None,
        help="Name of a specific skill or workflow to synchronize on-demand.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Batch synchronize all registered Spokes from Hub Registry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files on disk.",
    )
    parser.add_argument(
        "--apply",
        "-y",
        action="store_true",
        help="Apply synchronization changes directly to disk without interactive confirmation.",
    )
    parser.add_argument(
        "--force",
        "--ignore-dirty",
        action="store_true",
        dest="force",
        help="Ignore uncommitted changes warning and proceed with sync.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable automatic snapshot backup of .agents/ directory.",
    )
    parser.add_argument(
        "--rollback",
        "--undo",
        action="store_true",
        dest="rollback",
        help="Restore .agents/ directory from the latest backup snapshot.",
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List available snapshot backups for the target Spoke.",
    )
    args = parser.parse_args()

    if args.list_backups:
        backups = list_project_backups(args.spoke)
        if not backups:
            print("[Backup] Không tìm thấy bản snapshot sao lưu nào.")
        else:
            print(f"[Backup] Danh sách {len(backups)} bản sao lưu:")
            for idx, b in enumerate(backups, 1):
                mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {idx}. {b.name} ({mtime}) -> {b}")
        sys.exit(0)

    if args.rollback:
        success = rollback_project(args.spoke)
        sys.exit(0 if success else 1)

    if args.all:
        if args.dry_run:
            sys.exit(
                sync_all_spokes(
                    sync_item=args.sync_item,
                    dry_run=True,
                    force=args.force,
                    backup=not args.no_backup,
                )
            )
        elif args.apply:
            sys.exit(
                sync_all_spokes(
                    sync_item=args.sync_item,
                    dry_run=False,
                    force=args.force,
                    backup=not args.no_backup,
                )
            )
        else:
            print(
                "[Safe-by-Default] Đang thực hiện Pha 1: Xem trước các thay đổi cho tất cả Spokes (Preview)..."
            )
            preview_code = sync_all_spokes(
                sync_item=args.sync_item,
                dry_run=True,
                force=args.force,
                backup=not args.no_backup,
            )
            if preview_code != 0:
                sys.exit(preview_code)

            if sys.stdin.isatty():
                try:
                    ans = input(
                        "\n[Safe-by-Default] Bạn có muốn áp dụng các thay đổi trên cho tất cả Spokes? [y/N]: "
                    )
                    if ans.strip().lower() in ("y", "yes", "dong y", "có", "co"):
                        sys.exit(
                            sync_all_spokes(
                                sync_item=args.sync_item,
                                dry_run=False,
                                force=args.force,
                                backup=not args.no_backup,
                            )
                        )
                    else:
                        print(
                            "[Safe-by-Default] Đã hủy bỏ thao tác. Không có tệp tin nào bị sửa đổi."
                        )
                        sys.exit(0)
                except (EOFError, KeyboardInterrupt):
                    print("\n[Safe-by-Default] Đã hủy bỏ thao tác.")
                    sys.exit(0)
            else:
                print(
                    "\n[Safe-by-Default] Quá trình xem trước hoàn tất. "
                    "Để áp dụng thay đổi cho tất cả Spokes, vui lòng truyền cờ '--apply' hoặc '-y'."
                )
                sys.exit(0)
    else:
        # Two-Phase Safe-by-Default CLI logic
        if args.dry_run:
            sys.exit(
                sync_project(
                    args.spoke,
                    args.sync_item,
                    dry_run=True,
                    force=args.force,
                    backup=not args.no_backup,
                )
            )
        elif args.apply:
            sys.exit(
                sync_project(
                    args.spoke,
                    args.sync_item,
                    dry_run=False,
                    force=args.force,
                    backup=not args.no_backup,
                )
            )
        else:
            # Phase 1: Preview simulation
            print("[Safe-by-Default] Đang thực hiện Pha 1: Xem trước các thay đổi (Preview)...")
            preview_code = sync_project(
                args.spoke,
                args.sync_item,
                dry_run=True,
                force=args.force,
                backup=not args.no_backup,
            )
            if preview_code != 0:
                sys.exit(preview_code)

            # Phase 2: Confirmation
            if sys.stdin.isatty():
                try:
                    ans = input(
                        "\n[Safe-by-Default] Bạn có muốn áp dụng các thay đổi trên vào Spoke? [y/N]: "
                    )
                    if ans.strip().lower() in ("y", "yes", "dong y", "có", "co"):
                        sys.exit(
                            sync_project(
                                args.spoke,
                                args.sync_item,
                                dry_run=False,
                                force=args.force,
                                backup=not args.no_backup,
                            )
                        )
                    else:
                        print(
                            "[Safe-by-Default] Đã hủy bỏ thao tác. Không có tệp tin nào bị sửa đổi."
                        )
                        sys.exit(0)
                except (EOFError, KeyboardInterrupt):
                    print("\n[Safe-by-Default] Đã hủy bỏ thao tác.")
                    sys.exit(0)
            else:
                print(
                    "\n[Safe-by-Default] Quá trình xem trước hoàn tất. "
                    "Để áp dụng thay đổi vào Spoke, vui lòng truyền cờ '--apply' hoặc '-y'."
                )
                sys.exit(0)


if __name__ == "__main__":
    main()
