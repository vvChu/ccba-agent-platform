"""cli.py - CLI Entrypoint and 2-Phase Runner for Spoke Synchronization.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from .coordinator import list_project_backups, rollback_project, sync_all_spokes, sync_project


def run_spoke_sync_cli(args_list: list[str] | None = None) -> int:
    """CLI entrypoint with safe stream reconfigure and 2-Phase Confirmation."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="CCBA Spoke Synchronizer (Safe-by-Default)")
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
        "--include-sandboxes",
        action="store_true",
        help="Include personal sandboxes in batch synchronization (default: False).",
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
        help="Apply synchronization changes directly to disk.",
    )
    parser.add_argument(
        "--force",
        "--ignore-dirty",
        action="store_true",
        dest="force",
        help="Ignore uncommitted changes warning and proceed with sync.",
    )
    parser.add_argument(
        "--bootstrap",
        "-b",
        action="store_true",
        help="Automatically bootstrap Python packages and virtual environment after sync.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run deterministic ccba-harness verify-patch in Spoke post-sync (ADR-0058 Hard Completion Lock).",
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
    parser.add_argument(
        "--pull-assets",
        action="store_true",
        default=False,
        help="Physically copy OKF legal document bundles into Spoke (default: False, Reference-Only Zero-Bloat).",
    )
    args = parser.parse_args(args_list)

    if args.list_backups:
        backups = list_project_backups(args.spoke)
        if not backups:
            print("[Backup] Không tìm thấy bản snapshot sao lưu nào.")
        else:
            print(f"[Backup] Danh sách {len(backups)} bản sao lưu:")
            for idx, b in enumerate(backups, 1):
                mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {idx}. {b.name} ({mtime}) -> {b}")
        return 0

    if args.rollback:
        success = rollback_project(args.spoke)
        return 0 if success else 1

    if args.all:
        if args.dry_run:
            return sync_all_spokes(
                sync_item=args.sync_item,
                dry_run=True,
                force=args.force,
                backup=not args.no_backup,
                include_sandboxes=args.include_sandboxes,
                bootstrap=args.bootstrap,
                verify=args.verify,
                pull_assets=args.pull_assets,
            )
        elif args.apply:
            return sync_all_spokes(
                sync_item=args.sync_item,
                dry_run=False,
                force=args.force,
                backup=not args.no_backup,
                include_sandboxes=args.include_sandboxes,
                bootstrap=args.bootstrap,
                verify=args.verify,
                pull_assets=args.pull_assets,
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
                include_sandboxes=args.include_sandboxes,
                bootstrap=False,
                verify=False,
                pull_assets=args.pull_assets,
            )
            if preview_code != 0:
                return preview_code

            if sys.stdin.isatty():
                try:
                    ans = input(
                        "\n[Safe-by-Default] Bạn có muốn áp dụng các thay đổi trên cho tất cả Spokes? [y/N]: "
                    )
                    if ans.strip().lower() in ("y", "yes", "dong y", "có", "co"):
                        return sync_all_spokes(
                            sync_item=args.sync_item,
                            dry_run=False,
                            force=args.force,
                            backup=not args.no_backup,
                            include_sandboxes=args.include_sandboxes,
                            bootstrap=args.bootstrap,
                            verify=args.verify,
                            pull_assets=args.pull_assets,
                        )
                    else:
                        print(
                            "[Safe-by-Default] Đã hủy bỏ thao tác. Không có tệp tin nào bị sửa đổi."
                        )
                        return 0
                except (EOFError, KeyboardInterrupt):
                    print("\n[Safe-by-Default] Đã hủy bỏ thao tác.")
                    return 0
            else:
                print(
                    "\n[Safe-by-Default] Quá trình xem trước hoàn tất. "
                    "Để áp dụng thay đổi cho tất cả Spokes, vui lòng truyền cờ '--apply' hoặc '-y'."
                )
                return 0
    else:
        # Single Spoke Synchronization
        if args.dry_run:
            return sync_project(
                args.spoke,
                args.sync_item,
                dry_run=True,
                force=args.force,
                backup=not args.no_backup,
                bootstrap=args.bootstrap,
                verify=args.verify,
                pull_assets=args.pull_assets,
            )
        elif args.apply:
            return sync_project(
                args.spoke,
                args.sync_item,
                dry_run=False,
                force=args.force,
                backup=not args.no_backup,
                bootstrap=args.bootstrap,
                verify=args.verify,
                pull_assets=args.pull_assets,
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
                bootstrap=False,
                verify=False,
                pull_assets=args.pull_assets,
            )
            if preview_code != 0:
                return preview_code

            # Phase 2: Confirmation
            if sys.stdin.isatty():
                try:
                    ans = input(
                        "\n[Safe-by-Default] Bạn có muốn áp dụng các thay đổi trên vào Spoke? [y/N]: "
                    )
                    if ans.strip().lower() in ("y", "yes", "dong y", "có", "co"):
                        return sync_project(
                            args.spoke,
                            args.sync_item,
                            dry_run=False,
                            force=args.force,
                            backup=not args.no_backup,
                            bootstrap=args.bootstrap,
                            verify=args.verify,
                            pull_assets=args.pull_assets,
                        )
                    else:
                        print(
                            "[Safe-by-Default] Đã hủy bỏ thao tác. Không có tệp tin nào bị sửa đổi."
                        )
                        return 0
                except (EOFError, KeyboardInterrupt):
                    print("\n[Safe-by-Default] Đã hủy bỏ thao tác.")
                    return 0
            else:
                print(
                    "\n[Safe-by-Default] Quá trình xem trước hoàn tất. "
                    "Để áp dụng thay đổi vào Spoke, vui lòng truyền cờ '--apply' hoặc '-y'."
                )
                return 0
