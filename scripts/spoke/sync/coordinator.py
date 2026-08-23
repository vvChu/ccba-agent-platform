"""coordinator.py - Coordinator & Orchestration Engine for Spoke Synchronization.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .backup import GitWorkingTreeGuard, SpokeBackupManager
from .base import HubNotFoundError, are_dirs_identical, are_files_identical, load_yaml, safe_remove
from .discovery import HubDiscoverer
from .registry import SpokeRegistrar
from .sdk_inspector import SharedSdkInspector, TestGuardrailCopier


class SpokeSynchronizer:
    """Deep Engine managing Spoke workspace synchronization with non-destructive selective merge."""

    def __init__(
        self,
        spoke_path: str | Path | None = None,
        spoke_root: str | Path | None = None,
        hub_root: str | Path | None = None,
    ) -> None:
        target = spoke_path or spoke_root or "."
        self.spoke_root = Path(target).resolve()
        self.hub_root = Path(hub_root).resolve() if hub_root else None

    def _sync_single_item(
        self,
        spoke_root: Path,
        hub_root: Path,
        catalog: dict[str, Any],
        sync_item: str,
        dry_run: bool = False,
    ) -> int:
        """On-Demand synchronization for a single skill or workflow."""
        mode_str = " [DRY-RUN]" if dry_run else ""
        print(f"Mode: On-Demand Synchronization for '{sync_item}'{mode_str}")
        spoke_agents_dir = spoke_root / ".agents"
        spoke_skills_dir = spoke_agents_dir / "skills"
        spoke_workflows_dir = spoke_agents_dir / "workflows"

        found = False

        # Search Skills
        for skill_entry in catalog.get("skills", []):
            if skill_entry.get("name") == sync_item:
                skill_path_rel = skill_entry.get("skill_path")
                src = hub_root / Path(skill_path_rel).parent
                dest_name = Path(skill_path_rel).parent.name
                dest = spoke_skills_dir / dest_name

                if src.exists():
                    if src.resolve() == dest.resolve():
                        found = True
                        break
                    if dry_run:
                        print(
                            f"[Sync] [DRY-RUN] Would copy skill [{sync_item}] -> {dest.relative_to(spoke_root)}"
                        )
                    else:
                        print(
                            f"[Sync] Copying skill [{sync_item}] -> {dest.relative_to(spoke_root)}"
                        )
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        safe_remove(dest)
                        shutil.copytree(src, dest)
                    found = True
                    break
                else:
                    print(f"[Sync] Error: Skill source path not found at {src}", file=sys.stderr)
                    return 1

        # Search Workflows
        if not found:
            for wf_entry in catalog.get("workflows", []):
                if wf_entry.get("name") == sync_item:
                    wf_path_rel = wf_entry.get("workflow_path")
                    src = hub_root / wf_path_rel
                    filename = Path(wf_path_rel).name
                    dest = spoke_workflows_dir / filename

                    if src.exists():
                        if src.resolve() == dest.resolve():
                            found = True
                            break
                        if dry_run:
                            print(
                                f"[Sync] [DRY-RUN] Would copy workflow [{sync_item}] -> {dest.relative_to(spoke_root)}"
                            )
                        else:
                            print(
                                f"[Sync] Copying workflow [{sync_item}] -> {dest.relative_to(spoke_root)}"
                            )
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if dest.exists():
                                dest.unlink()
                            shutil.copy2(src, dest)
                        found = True
                        break
                    else:
                        print(
                            f"[Sync] Error: Workflow source file not found at {src}",
                            file=sys.stderr,
                        )
                        return 1

        if not found:
            print(
                f"[Sync] Error: Item '{sync_item}' not found in Hub catalog.yaml.", file=sys.stderr
            )
            return 1

        # Copy constitution AGENTS.md
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists():
            if dry_run:
                print(
                    f"[Sync] [DRY-RUN] Would copy constitutional rules -> {spoke_agents_md.relative_to(spoke_root)}"
                )
            else:
                spoke_agents_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(hub_agents_md, spoke_agents_md)

        if dry_run:
            print("\n=== [DRY-RUN] On-Demand Sync Simulation Completed ===")
        else:
            print("\n=== Sync Completed Successfully ===")
        return 0

    def _sync_full_bundle(
        self,
        spoke_root: Path,
        hub_root: Path,
        catalog: dict[str, Any],
        project_type: str,
        project_name: str,
        dry_run: bool = False,
    ) -> int:
        """Full synchronization with Non-Destructive Selective Merge."""
        if not project_type:
            print(
                "[Sync] Error: 'project_type' is not defined in workspace_context.yaml.",
                file=sys.stderr,
            )
            return 1

        mode_banner = " [DRY-RUN MODE]" if dry_run else ""
        print(f"Project Type: {project_type}{mode_banner}")

        bundle_defs = catalog.get("bundles", {})
        if project_type not in bundle_defs:
            available_types = ", ".join(bundle_defs.keys())
            print(
                f"[Sync] Error: Project type '{project_type}' is not registered in catalog.yaml.",
                file=sys.stderr,
            )
            print(f"[Sync] Registered types: {available_types}", file=sys.stderr)
            return 1

        required_bundles = bundle_defs[project_type]
        print(f"Required Bundles: {required_bundles}")

        spoke_agents_dir = spoke_root / ".agents"
        spoke_skills_dir = spoke_agents_dir / "skills"
        spoke_workflows_dir = spoke_agents_dir / "workflows"

        skills_to_sync = []
        wfs_to_sync = []

        # Filter Skills
        for skill_entry in catalog.get("skills", []):
            skill_name = skill_entry.get("name")
            skill_bundle = skill_entry.get("bundle")
            skill_path_rel = skill_entry.get("skill_path")

            if skill_bundle in required_bundles or skill_bundle == "_core":
                skills_to_sync.append(
                    {
                        "name": skill_name,
                        "src_dir": hub_root / Path(skill_path_rel).parent,
                        "dest_name": Path(skill_path_rel).parent.name,
                    }
                )

        # Filter Workflows
        for wf_entry in catalog.get("workflows", []):
            wf_name = wf_entry.get("name")
            wf_bundle = wf_entry.get("bundle")
            wf_path_rel = wf_entry.get("workflow_path")

            if wf_bundle in required_bundles or wf_bundle == "_core":
                wfs_to_sync.append(
                    {
                        "name": wf_name,
                        "src_file": hub_root / wf_path_rel,
                        "filename": Path(wf_path_rel).name,
                    }
                )

        # Status tracking
        actions: list[dict[str, Any]] = []

        # 1. Process Skills (Selective Merge)
        if not dry_run:
            spoke_skills_dir.mkdir(parents=True, exist_ok=True)

        synced_skill_folders = {sk["dest_name"] for sk in skills_to_sync}
        if spoke_skills_dir.exists():
            for existing_skill in spoke_skills_dir.iterdir():
                if existing_skill.is_dir() and existing_skill.name not in synced_skill_folders:
                    actions.append(
                        {
                            "type": "Skill",
                            "name": existing_skill.name,
                            "status": "PRESERVED",
                            "path": str(existing_skill.relative_to(spoke_root)),
                        }
                    )

        for sk in skills_to_sync:
            src = sk["src_dir"]
            dest = spoke_skills_dir / sk["dest_name"]
            if not src.exists():
                print(f"  - [Warning] Skill source path not found: {src}", file=sys.stderr)
                continue

            if src.resolve() == dest.resolve():
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                continue

            if not dest.exists():
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "NEW",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dest, dirs_exist_ok=True)
            elif are_dirs_identical(src, dest):
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
            else:
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UPDATED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    safe_remove(dest)
                    shutil.copytree(src, dest, dirs_exist_ok=True)

        # 2. Process Workflows (Non-Destructive Selective Merge)
        if not dry_run:
            spoke_workflows_dir.mkdir(parents=True, exist_ok=True)

        synced_wf_filenames = {wf["filename"] for wf in wfs_to_sync}
        if spoke_workflows_dir.exists():
            for existing_wf in spoke_workflows_dir.iterdir():
                if existing_wf.is_file() and existing_wf.name not in synced_wf_filenames:
                    actions.append(
                        {
                            "type": "Workflow",
                            "name": existing_wf.stem,
                            "status": "PRESERVED",
                            "path": str(existing_wf.relative_to(spoke_root)),
                        }
                    )

        for wf in wfs_to_sync:
            src = wf["src_file"]
            dest = spoke_workflows_dir / wf["filename"]
            if not src.exists():
                print(f"  - [Warning] Workflow source file not found: {src}", file=sys.stderr)
                continue

            if src.resolve() == dest.resolve():
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                continue

            if not dest.exists():
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "NEW",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
            elif are_files_identical(src, dest):
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
            else:
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UPDATED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)

        # 3. Copy AGENTS.md
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists() and hub_agents_md.resolve() != spoke_agents_md.resolve():
            if not spoke_agents_md.exists():
                rule_status = "NEW"
            elif are_files_identical(hub_agents_md, spoke_agents_md):
                rule_status = "UNCHANGED"
            else:
                rule_status = "UPDATED"

            actions.append(
                {
                    "type": "Rule",
                    "name": "AGENTS.md",
                    "status": rule_status,
                    "path": str(spoke_agents_md.relative_to(spoke_root)),
                }
            )
            if not dry_run and rule_status in ("NEW", "UPDATED"):
                spoke_agents_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(hub_agents_md, spoke_agents_md)

        # 4. Test guardrails
        TestGuardrailCopier(spoke_root, hub_root, project_type).copy_if_needed(dry_run=dry_run)

        # 5. Spoke registration
        SpokeRegistrar().register(spoke_root, hub_root, project_name, project_type, dry_run=dry_run)

        # 6. Print Structured Output & Summary Table
        new_count = sum(1 for a in actions if a["status"] == "NEW")
        updated_count = sum(1 for a in actions if a["status"] == "UPDATED")
        unchanged_count = sum(1 for a in actions if a["status"] == "UNCHANGED")
        preserved_count = sum(1 for a in actions if a["status"] == "PRESERVED")

        print("\n" + "=" * 90)
        print(f" CCBA SPOKE SYNC REPORT — {'[DRY-RUN SIMULATION]' if dry_run else '[EXECUTION]'}")
        print("=" * 90)
        print(f"{'Loại':<10} | {'Tên Kỹ Năng / Quy Trình':<30} | {'Trạng Thái':<12} | {'Đích Đến'}")
        print("-" * 90)
        for act in actions:
            status_symbol = {
                "NEW": "🟢 NEW",
                "UPDATED": "🔄 UPDATED",
                "UNCHANGED": "⚪ UNCHANGED",
                "PRESERVED": "🛡️ PRESERVED",
            }.get(act["status"], act["status"])
            print(f"{act['type']:<10} | {act['name']:<30} | {status_symbol:<12} | {act['path']}")
        print("-" * 90)
        print(
            f"Tổng kết: {new_count} mới, {updated_count} cập nhật, {unchanged_count} không đổi, {preserved_count} giữ nguyên nội bộ."
        )

        # 7. Zero-Latency Shared Python SDKs Inspection
        sdk_inspector = SharedSdkInspector(spoke_root, hub_root, project_type)
        sdk_recs = sdk_inspector.get_recommendations()
        if sdk_recs:
            print("\n💡 Gợi ý Shared SDKs cho Spoke Python:")
            print("   Để sử dụng AI Gateway hoặc Office Processing dùng chung từ Hub:")
            for cmd in sdk_recs:
                print(f"   -> {cmd}")

        if dry_run:
            print("\n[DRY-RUN] Quá trình mô phỏng hoàn tất. 0 tệp tin nào bị sửa đổi trên đĩa.")
        else:
            print("\n=== Sync Completed Successfully ===")
        return 0

    def sync_spoke_bundle(
        self,
        sync_item: str | None = None,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = True,
        check_git: bool = True,
        only: str | None = None,
    ) -> int:
        """Main entrypoint for Spoke synchronization."""
        mode_str = " [DRY-RUN]" if dry_run else ""
        print(f"\n=== CCBA Spoke Synchronization{mode_str} ===")
        print(f"Target Spoke: {self.spoke_root}")

        # Git Working Tree Guard (Execution mode only)
        if not dry_run and check_git and not force:
            guard = GitWorkingTreeGuard(self.spoke_root)
            is_clean, dirty_details = guard.check_clean_working_tree()
            if not is_clean:
                print("\n" + "!" * 80, file=sys.stderr)
                print(
                    "[Sync] ⚠️  CẢNH BÁO: Phát hiện uncommitted changes trong thư mục .agents/:",
                    file=sys.stderr,
                )
                for line in dirty_details.splitlines():
                    print(f"  {line}", file=sys.stderr)
                print(
                    "  Để tránh ghi đè dữ liệu ngoài ý muốn, vui lòng commit hoặc stash các thay đổi.",
                    file=sys.stderr,
                )
                print(
                    "  Hoặc truyền cờ '--force' / '--ignore-dirty' nếu muốn bỏ qua cảnh báo này.",
                    file=sys.stderr,
                )
                print("!" * 80 + "\n", file=sys.stderr)
                return 1

        context_file = self.spoke_root / ".agents" / "workspace_context.yaml"
        if not context_file.exists():
            context_file = self.spoke_root / ".md" / "workspace_context.yaml"

        if not context_file.exists():
            print(
                f"[Sync] Error: Could not find workspace_context.yaml in {self.spoke_root}/.agents/ or {self.spoke_root}/.md/",
                file=sys.stderr,
            )
            print(
                "[Sync] Please run 'init spoke' first in the target project folder.",
                file=sys.stderr,
            )
            return 1

        context = load_yaml(context_file)

        project_name_val = context.get("project_name")
        if not project_name_val:
            proj_dict = context.get("project")
            if isinstance(proj_dict, dict):
                project_name_val = proj_dict.get("name")
        if not project_name_val:
            project_name = self.spoke_root.name
        else:
            project_name = str(project_name_val).strip()

        project_type_val = context.get("project_type")
        if not project_type_val:
            proj_dict = context.get("project")
            if isinstance(proj_dict, dict):
                project_type_val = proj_dict.get("type")
        if not project_type_val:
            project_type = ""
        else:
            project_type = str(project_type_val).strip()

        if self.hub_root and self.hub_root.exists():
            hub_root = self.hub_root
        else:
            try:
                discoverer = HubDiscoverer(self.spoke_root, context, context_file)
                hub_root = discoverer.discover()
            except HubNotFoundError as e:
                print(str(e), file=sys.stderr)
                return 1

        print(f"Hub Location: {hub_root}")

        # Snapshot Backup before actual modification
        if not dry_run and backup:
            backup_mgr = SpokeBackupManager(self.spoke_root)
            snapshot_dir = backup_mgr.create_backup()
            if snapshot_dir:
                try:
                    rel_backup = snapshot_dir.relative_to(self.spoke_root)
                except ValueError:
                    rel_backup = snapshot_dir
                print(f"[Sync] 🛡️  Đã tạo snapshot sao lưu an toàn: {rel_backup}")

        # Auto git pull Hub if git repo (only when not dry_run)
        if (hub_root / ".git").exists() and not dry_run:
            print(
                "[Sync] Hub is a Git repository. Attempting to pull latest changes from GitHub..."
            )
            try:
                result = subprocess.run(
                    ["git", "pull"], cwd=str(hub_root), capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    print("[Sync] Git pull completed successfully.")
                    if result.stdout.strip():
                        print(f"  {result.stdout.strip()}")
                else:
                    print(
                        f"[Sync] Warning: Git pull failed with code {result.returncode}.",
                        file=sys.stderr,
                    )
                    if result.stderr.strip():
                        print(f"  {result.stderr.strip()}", file=sys.stderr)
                    print("[Sync] Continuing with local offline cache...", file=sys.stderr)
            except Exception as e:
                print(f"[Sync] Warning: Could not execute git pull: {e}", file=sys.stderr)
                print("[Sync] Continuing with local offline cache...", file=sys.stderr)

        catalog_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        if not catalog_file.exists():
            print(f"[Sync] Error: Could not find catalog.yaml at {catalog_file}", file=sys.stderr)
            return 1

        catalog = load_yaml(catalog_file)

        target_item = sync_item or only
        if target_item:
            return self._sync_single_item(
                self.spoke_root, hub_root, catalog, target_item, dry_run=dry_run
            )
        else:
            return self._sync_full_bundle(
                self.spoke_root,
                hub_root,
                catalog,
                project_type,
                project_name,
                dry_run=dry_run,
            )

    def sync(
        self,
        sync_item: str | None = None,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = True,
        check_git: bool = True,
        only: str | None = None,
    ) -> int:
        """Deep Seam entry point for syncing spoke bundle."""
        return self.sync_spoke_bundle(
            sync_item=sync_item or only,
            dry_run=dry_run,
            force=force,
            backup=backup,
            check_git=check_git,
            only=only,
        )

    def rollback(self, backup_path: Path | None = None) -> bool:
        """Restore .agents/ from latest snapshot or specified backup path."""
        return SpokeBackupManager(self.spoke_root).restore_backup(backup_path)

    def list_backups(self) -> list[Path]:
        """List available snapshots for this spoke."""
        return SpokeBackupManager(self.spoke_root).list_backups()


# Deep Seam Alias
SpokeSyncEngine = SpokeSynchronizer


def _get_synchronizer_cls() -> type[SpokeSynchronizer]:
    """Helper to dynamically resolve SpokeSynchronizer class, supporting monkeypatching on facade."""
    spoke_sync_mod = sys.modules.get("scripts.spoke.spoke_synchronizer")
    if spoke_sync_mod and hasattr(spoke_sync_mod, "SpokeSynchronizer"):
        cls = spoke_sync_mod.SpokeSynchronizer
        if isinstance(cls, type):
            return cls
    return SpokeSynchronizer


def sync_project(
    spoke_path: str | Path = ".",
    sync_item: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    backup: bool = True,
    check_git: bool = True,
) -> int:
    """Helper procedural delegate for spoke synchronization."""
    engine = _get_synchronizer_cls()(str(spoke_path))
    return engine.sync(
        sync_item=sync_item,
        dry_run=dry_run,
        force=force,
        backup=backup,
        check_git=check_git,
    )


def rollback_project(
    spoke_path: str | Path = ".",
    backup_path: Path | None = None,
) -> bool:
    """Helper procedural delegate for spoke rollback from snapshot."""
    engine = _get_synchronizer_cls()(str(spoke_path))
    return engine.rollback(backup_path=backup_path)


def list_project_backups(spoke_path: str | Path = ".") -> list[Path]:
    """Helper procedural delegate to list spoke backup snapshots."""
    engine = _get_synchronizer_cls()(str(spoke_path))
    return engine.list_backups()


def sync_all_spokes(
    hub_root: Path | None = None,
    sync_item: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    backup: bool = True,
    check_git: bool = True,
    include_sandboxes: bool = False,
) -> int:
    """Batch synchronize all registered active Spokes found in Hub Registry."""
    root = hub_root or Path(__file__).resolve().parents[3]
    from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

    spokes = get_registered_spokes(hub_root=root)
    if not include_sandboxes:
        spokes = [s for s in spokes if not s.get("is_sandbox", False)]

    if not spokes:
        print("[BatchSync] Warning: No registered Spokes found in Hub Registry.", file=sys.stderr)
        return 1

    mode_str = " [DRY-RUN SIMULATION]" if dry_run else ""
    print("\n" + "=" * 90)
    print(f" CCBA MULTI-SPOKE BATCH SYNCHRONIZATION{mode_str}")
    print(f" Tìm thấy {len(spokes)} Spoke(s) trong Hub Registry.")
    print("=" * 90)

    results: list[dict[str, Any]] = []
    total_exit_code = 0
    sync_cls = _get_synchronizer_cls()

    for idx, sp in enumerate(spokes, 1):
        sp_name = sp.get("name", "Unknown")
        sp_path = sp.get("path", "")
        sp_type = sp.get("project_type", "Unknown")

        print(f"\n[{idx}/{len(spokes)}] 🔄 Đang xử lý Spoke: '{sp_name}' ({sp_type})")
        print(f"  Đường dẫn: {sp_path}")

        if not os.path.exists(sp_path):
            print("  ⚠️ Cảnh báo: Spoke không tồn tại vật lý trên ổ đĩa. Bỏ qua.")
            results.append({"name": sp_name, "path": sp_path, "status": "MISSING", "code": 1})
            continue

        try:
            engine = sync_cls(sp_path)
            res = engine.sync(
                sync_item=sync_item,
                dry_run=dry_run,
                force=force,
                backup=backup,
                check_git=check_git,
            )
            status = "SUCCESS" if res == 0 else "FAILED"
            results.append({"name": sp_name, "path": sp_path, "status": status, "code": res})
            if res != 0:
                total_exit_code = 1
        except Exception as e:
            print(f"  ❌ Lỗi khi đồng bộ Spoke '{sp_name}': {e}", file=sys.stderr)
            results.append({"name": sp_name, "path": sp_path, "status": f"ERROR: {e}", "code": 1})
            total_exit_code = 1

    print("\n" + "=" * 90)
    print(f" BÁO CÁO TỔNG KẾT BATCH SYNC{mode_str}")
    print("=" * 90)
    print(f"{'Tên Spoke':<25} | {'Trạng Thái':<14} | {'Đường Dẫn Vật Lý'}")
    print("-" * 90)
    for r in results:
        status_icon = (
            "✅ SUCCESS"
            if r["status"] == "SUCCESS"
            else ("⚠️ MISSING" if r["status"] == "MISSING" else f"❌ {r['status']}")
        )
        print(f"{r['name']:<25} | {status_icon:<14} | {r['path']}")
    print("=" * 90)

    return total_exit_code
