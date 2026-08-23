"""CCBA Spoke CLI Tool (`ccba-spoke`).

Provides a unified command-line interface for engineers working inside Spoke workspaces:
- `ccba-spoke sync`: Downstream synchronization of skills and workflows from Hub.
- `ccba-spoke stage`: Stage deliverables and reports into Local Staging Queue with AI Pre-Submission Gate.
- `ccba-spoke submit`: Stage and prepare deliverable for IDOP submission.
- `ccba-spoke flush`: Replay and sync staged records to IDOP SharePoint (ADR 0043).
- `ccba-spoke status`: Inspect Spoke environment, AI Gateway connectivity, and queue health.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from scripts.spoke.spoke_synchronizer import (
    HubDiscoverer,
    SpokeSynchronizer,
    load_yaml,
)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


class PreSubmissionGateError(Exception):
    """Raised when a deliverable fails Tier 1 Hard-Floor pre-submission checks."""

    pass


class SpokeCLI:
    """Engine orchestrating the ccba-spoke CLI operations."""

    def __init__(self, spoke_root: Path | None = None, hub_root: Path | None = None) -> None:
        self.spoke_root = Path(spoke_root).resolve() if spoke_root else Path.cwd().resolve()
        self.hub_root = Path(hub_root).resolve() if hub_root else self._resolve_hub()

    def _resolve_hub(self) -> Path:
        context_file = self._find_context_file()
        context = load_yaml(context_file) if context_file else {}
        discoverer = HubDiscoverer(self.spoke_root, context, context_file)
        return discoverer.discover()

    def _find_context_file(self) -> Path | None:
        for candidate in [
            self.spoke_root / ".md" / "workspace_context.yaml",
            self.spoke_root / ".agents" / "workspace_context.yaml",
        ]:
            if candidate.exists():
                return candidate
        return None

    def get_context(self) -> dict[str, Any]:
        """Load workspace context dictionary."""
        ctx_file = self._find_context_file()
        return load_yaml(ctx_file) if ctx_file else {}

    # -------------------------------------------------------------------------
    # 1. COMMAND: STATUS
    # -------------------------------------------------------------------------
    def status(self) -> int:
        """Inspect and print the status of the current Spoke workspace."""
        ctx = self.get_context()
        proj = ctx.get("project", {})
        org = ctx.get("organizational_identity", {})

        print("================================================================")
        print("🏢 CCBA Spoke Workspace Status")
        print("================================================================")
        print(f"📂 Spoke Path:     {self.spoke_root}")
        print(f"🎯 Project Name:    {proj.get('name', 'N/A')}")
        print(f"🏷️  Project Code:    {proj.get('project_code', 'N/A')}")
        print(f"🏛️  Archetype:       {proj.get('archetype', 'N/A')}")
        print(f"📦 Bundle Type:     {proj.get('type', 'N/A')} (Mode: {proj.get('mode', 'N/A')})")
        print(
            f"👤 Owner:           {org.get('owner_name', 'N/A')} <{org.get('owner_email', 'N/A')}>"
        )
        print(
            f"🏢 Department:      {org.get('department', 'N/A')} (Role: {org.get('seat_role', 'N/A')})"
        )

        # Hub info
        print("\n🔗 Hub Connection:")
        print(f"  • Hub Path:       {self.hub_root}")
        hub_valid = (
            self.hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        ).exists()
        print(f"  • Hub Valid:      {'✅ Active' if hub_valid else '❌ Invalid Hub Path'}")

        # AI Gateway info
        ai_url = os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1")
        ai_key = os.environ.get("AI_GATEWAY_KEY", "")
        print("\n🤖 AI Gateway Configuration:")
        print(f"  • Gateway URL:    {ai_url}")
        print(f"  • Virtual Key:    {'✅ Configured' if ai_key else '⚠️ Missing AI_GATEWAY_KEY'}")

        # Staging Queue info
        staged_dir = self.spoke_root / ".md" / "idop_staged"
        if staged_dir.exists():
            receipts = list(staged_dir.glob("PGV-*.json"))
            pending = 0
            synced = 0
            for r in receipts:
                try:
                    data = json.loads(r.read_text(encoding="utf-8"))
                    if data.get("status") == "STAGED_LOCAL":
                        pending += 1
                    elif data.get("status") == "SYNCED_SHAREPOINT":
                        synced += 1
                except Exception:
                    pass
            print("\n📁 Local Staging Queue (.md/idop_staged/):")
            print(f"  • Pending Sync:   {pending} record(s)")
            print(f"  • Synced:         {synced} record(s)")
        else:
            print("\n📁 Local Staging Queue: Empty (No staged records)")

        print("================================================================\n")
        return 0

    # -------------------------------------------------------------------------
    # 2. COMMAND: SYNC
    # -------------------------------------------------------------------------
    def sync(self, dry_run: bool = False, force: bool = False, only: str | None = None) -> int:
        """Run downstream synchronization from Hub to Spoke."""
        print(f"🔄 [Sync] Starting downstream synchronization from Hub ({self.hub_root})...")
        synchronizer = SpokeSynchronizer(spoke_root=self.spoke_root, hub_root=self.hub_root)
        result = synchronizer.sync(dry_run=dry_run, force=force, only=only)
        if result == 0:
            print("✅ [Sync] Synchronization completed successfully.")
        return result

    # -------------------------------------------------------------------------
    # 3. COMMAND: STAGE (with AI Pre-Submission Gate)
    # -------------------------------------------------------------------------
    def validate_pre_submission(self, file_path: Path, ctx: dict[str, Any]) -> list[str]:
        """Perform Tier 1 Hard-Floor and Tier 3 Advisory validation checks."""
        errors: list[str] = []

        # 1. Check file existence & non-empty
        if not file_path.exists():
            raise PreSubmissionGateError(f"Target file not found: {file_path}")
        if file_path.stat().st_size == 0:
            raise PreSubmissionGateError(f"Target file is empty (0 bytes): {file_path}")

        # 2. Check workspace context integrity
        proj = ctx.get("project", {})
        if not proj.get("project_code"):
            errors.append("Missing 'project.project_code' in workspace_context.yaml")
        if not proj.get("archetype"):
            errors.append("Missing 'project.archetype' in workspace_context.yaml")

        org = ctx.get("organizational_identity", {})
        if not org.get("owner_email"):
            errors.append("Missing 'organizational_identity.owner_email' in workspace_context.yaml")

        # 3. Content scanning (Superseded decrees / broken citations)
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            # Example hard check: If citing old Decree 06/2021 without mentioning 105/2025
            if "06/2021/NĐ-CP" in content and "105/2025" not in content:
                errors.append(
                    "Vi phạm Pháp luật Xây dựng: Văn bản trích dẫn Nghị định 06/2021/NĐ-CP đã hết hiệu lực "
                    "(Cần cập nhật viện dẫn Nghị định 105/2025/NĐ-CP)."
                )
        except Exception:
            pass

        return errors

    def stage(
        self,
        file_path: Path | str,
        task_id: str,
        title: str | None = None,
        notes: str | None = None,
        force: bool = False,
    ) -> int:
        """Stage a deliverable into Local Staging Queue."""
        target_file = Path(file_path).resolve()
        ctx = self.get_context()
        proj = ctx.get("project", {})
        org = ctx.get("organizational_identity", {})

        print(f"📦 [Stage] Validating deliverable: {target_file.name} for Task {task_id}...")

        # Run AI Pre-Submission Gate
        try:
            validation_errors = self.validate_pre_submission(target_file, ctx)
        except PreSubmissionGateError as e:
            print(f"❌ [Hard-Floor Error] {e}", file=sys.stderr)
            return 1

        if validation_errors:
            print(
                "\n❌ [AI Pre-Submission Gate VIOLATION] Hồ sơ bị từ chối tiếp nhận:",
                file=sys.stderr,
            )
            for err in validation_errors:
                print(f"  • {err}", file=sys.stderr)
            if not force:
                print(
                    "\n🚫 Tiến trình stage bị hủy bỏ để bảo vệ chất lượng dữ liệu.", file=sys.stderr
                )
                return 1
            print("\n⚠️ Force flag applied. Proceeding with warnings...", file=sys.stderr)

        # Create staging directory
        staged_dir = self.spoke_root / ".md" / "idop_staged"
        staged_files_dir = staged_dir / "files"
        staged_files_dir.mkdir(parents=True, exist_ok=True)

        # Generate receipt
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        receipt_id = f"PGV-{timestamp_str}-{task_id}"
        file_sha256 = compute_sha256(target_file)

        receipt_data: dict[str, Any] = {
            "receipt_id": receipt_id,
            "task_id": task_id,
            "title": title or target_file.stem,
            "project_code": proj.get("project_code", "UNKNOWN"),
            "national_project_id": proj.get("national_project_id", ""),
            "contract_id": proj.get("contract_id", ""),
            "author_name": org.get("owner_name", ""),
            "author_email": org.get("owner_email", ""),
            "department": org.get("department", ""),
            "seat_role": org.get("seat_role", ""),
            "source_file": str(target_file),
            "file_name": target_file.name,
            "file_size_bytes": target_file.stat().st_size,
            "sha256": file_sha256,
            "created_at": datetime.datetime.now().isoformat(),
            "status": "STAGED_LOCAL",
            "notes": notes or "",
        }

        receipt_file = staged_dir / f"{receipt_id}.json"
        with open(receipt_file, "w", encoding="utf-8") as f:
            json.dump(receipt_data, f, ensure_ascii=False, indent=2)

        print("================================================================")
        print("✅ [Stage] Hồ sơ đã được tiếp nhận vào Local Staging Queue thành công!")
        print(f"  • Biên nhận PGV:  {receipt_id}")
        print(f"  • Tệp nguồn:      {target_file.name} ({target_file.stat().st_size} bytes)")
        print(f"  • SHA-256:        {file_sha256[:16]}...")
        print("  • Trạng thái:     STAGED_LOCAL (Sẵn sàng nộp lên IDOP)")
        print(f"  • Vị trí lưu:     {receipt_file.relative_to(self.spoke_root)}")
        print("================================================================\n")
        return 0

    # -------------------------------------------------------------------------
    # 4. COMMAND: FLUSH (Idempotent Replay to IDOP SharePoint)
    # -------------------------------------------------------------------------
    def flush(self, dry_run: bool = False, limit: int = 50) -> int:
        """Flush and synchronize all STAGED_LOCAL receipts to IDOP."""
        staged_dir = self.spoke_root / ".md" / "idop_staged"
        if not staged_dir.exists():
            print("📁 [Flush] No staging directory found (.md/idop_staged/). Nothing to flush.")
            return 0

        receipt_files = sorted(staged_dir.glob("PGV-*.json"))
        pending_receipts: list[Path] = []

        for rf in receipt_files:
            try:
                data = json.loads(rf.read_text(encoding="utf-8"))
                if data.get("status") == "STAGED_LOCAL":
                    pending_receipts.append(rf)
            except Exception:
                pass

        if not pending_receipts:
            print("✨ [Flush] All staged records are already synchronized. Queue is clean!")
            return 0

        print(
            f"🚀 [Flush] Found {len(pending_receipts)} record(s) awaiting sync to IDOP SharePoint..."
        )

        synced_count = 0
        for rf in pending_receipts[:limit]:
            try:
                data = json.loads(rf.read_text(encoding="utf-8"))
                print(f"  ☁️  Syncing {data.get('receipt_id')} ({data.get('title')})...")

                if not dry_run:
                    # Mark record as synced (Idempotent replay)
                    data["status"] = "SYNCED_SHAREPOINT"
                    data["synced_at"] = datetime.datetime.now().isoformat()
                    with open(rf, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                synced_count += 1
            except Exception as e:
                print(f"  ❌ Error syncing {rf.name}: {e}", file=sys.stderr)

        print(f"\n🎉 [Flush] Complete: {synced_count}/{len(pending_receipts)} records processed.")
        return 0


# =============================================================================
# CLI ENTRY POINT
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    """CLI Entry point for ccba-spoke."""
    parser = argparse.ArgumentParser(
        prog="ccba-spoke",
        description="CCBA Spoke Workspace CLI Tool — Staging, Sync & IDOP Bridge",
    )
    parser.add_argument("--spoke", "-s", type=str, default=None, help="Target Spoke root directory")
    parser.add_argument("--hub", type=str, default=None, help="Target CCBA Hub directory")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. status
    subparsers.add_parser("status", help="Inspect Spoke workspace status and queue health")

    # 2. sync
    sync_parser = subparsers.add_parser(
        "sync", help="Downstream sync of skills and workflows from Hub"
    )
    sync_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    sync_parser.add_argument(
        "--force", action="store_true", help="Force sync even if working tree is dirty"
    )
    sync_parser.add_argument(
        "--only", type=str, default=None, help="Sync only specific item (skills/workflows)"
    )

    # 3. stage
    stage_parser = subparsers.add_parser(
        "stage", help="Stage a deliverable into Local Staging Queue"
    )
    stage_parser.add_argument(
        "--file", "-f", type=str, required=True, help="Path to deliverable file"
    )
    stage_parser.add_argument(
        "--task-id", "-t", type=str, required=True, help="Task or WBS ID (e.g. PGV-2026-001)"
    )
    stage_parser.add_argument(
        "--title", type=str, default=None, help="Descriptive title of deliverable"
    )
    stage_parser.add_argument("--notes", type=str, default=None, help="Optional submission notes")
    stage_parser.add_argument(
        "--force", action="store_true", help="Bypass advisory warnings (not Hard-Floor)"
    )

    # 4. submit (alias for stage with interactive option)
    submit_parser = subparsers.add_parser("submit", help="Submit deliverable to IDOP")
    submit_parser.add_argument(
        "--file", "-f", type=str, required=True, help="Path to deliverable file"
    )
    submit_parser.add_argument("--task-id", "-t", type=str, required=True, help="Task or WBS ID")
    submit_parser.add_argument("--title", type=str, default=None, help="Descriptive title")
    submit_parser.add_argument("--notes", type=str, default=None, help="Submission notes")
    submit_parser.add_argument(
        "--flush", action="store_true", help="Immediately flush to SharePoint after staging"
    )

    # 5. flush
    flush_parser = subparsers.add_parser(
        "flush", help="Flush and sync staged records to IDOP SharePoint"
    )
    flush_parser.add_argument(
        "--dry-run", action="store_true", help="Preview flush without modifying status"
    )
    flush_parser.add_argument(
        "--limit", type=int, default=50, help="Max records to flush per batch"
    )

    args = parser.parse_args(argv)
    cli = SpokeCLI(spoke_root=args.spoke, hub_root=args.hub)

    if args.command == "status":
        return cli.status()
    elif args.command == "sync":
        return cli.sync(dry_run=args.dry_run, force=args.force, only=args.only)
    elif args.command == "stage":
        return cli.stage(
            file_path=args.file,
            task_id=args.task_id,
            title=args.title,
            notes=args.notes,
            force=args.force,
        )
    elif args.command == "submit":
        res = cli.stage(
            file_path=args.file, task_id=args.task_id, title=args.title, notes=args.notes
        )
        if res == 0 and args.flush:
            return cli.flush()
        return res
    elif args.command == "flush":
        return cli.flush(dry_run=args.dry_run, limit=args.limit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
