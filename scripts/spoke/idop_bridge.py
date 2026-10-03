"""idop_bridge.py - Headless Python IDOPBridge SDK for CCBA Spoke Workspaces.

Architecture & Governance:
- Conforms to ADR 0042 (Headless Python IDOPBridge SDK)
- Conforms to ADR 0043 (Decoupled Resilience, Local Staging Queue, and Idempotent Replay)
- Conforms to ADR 0060 (Section 4: Python M365 Outbound Bridge Worker)
- Conforms to ADR 0061 (Platform-Aware KISS v2.0)
- Implements INV-SYNC-13 (IDOP Idempotent Replay & Composite Key)

Provides dual-mode operation:
- DEV mode (default): Local Mock Sandbox, zero credentials required.
- PROD mode: Entra ID App-Only Certificate pushing to SharePoint Online (59 Lists / CDE).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.spoke.ccba_m365_bridge import (
        BridgeConfig,
        CdeDocumentSyncService,
    )
except ModuleNotFoundError:
    _repo_root = Path(__file__).resolve().parent.parent.parent
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))
    from scripts.spoke.ccba_m365_bridge import (
        BridgeConfig,
        CdeDocumentSyncService,
    )

logger = logging.getLogger("idop_bridge")


def compute_composite_key(
    project_code: str,
    contract_id: str,
    stage_id: str,
    submittal_name: str,
) -> str:
    """Calculates deterministic composite SHA-256 key for a submittal.

    Ensures idempotent identity across multiple re-sync attempts and prevents
    duplicate entries in SharePoint Lists.

    Formula:
        sha256(lowercase(project_code:contract_id:stage_id:submittal_name))
    """
    p_code = (project_code or "UNKNOWN").strip().lower()
    c_id = (contract_id or "NONE").strip().lower()
    s_id = (stage_id or "TASK").strip().lower()
    s_name = (submittal_name or "UNTITLED").strip().lower()

    raw_token = f"{p_code}:{c_id}:{s_id}:{s_name}"
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 digest of a binary file in chunks."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


@dataclass
class StagedSubmittal:
    """Data transfer object for a staged submittal."""

    receipt_id: str
    composite_key: str
    task_id: str
    title: str
    project_code: str
    national_project_id: str
    contract_id: str
    author_name: str
    author_email: str
    department: str
    seat_role: str
    source_file: str
    file_name: str
    file_size_bytes: int
    sha256: str
    created_at: str
    status: str  # STAGED_LOCAL, SYNCED_SHAREPOINT, FAILED_DLQ
    notes: str = ""
    sharepoint_item_id: str | None = None
    synced_at: str | None = None
    error_message: str | None = None


class IDOPBridge:
    """Enterprise IDOP Integration Bridge for Spoke Workspaces."""

    def __init__(
        self,
        spoke_root: Path | None = None,
        config: BridgeConfig | None = None,
    ) -> None:
        self.spoke_root = Path(spoke_root).resolve() if spoke_root else Path.cwd().resolve()
        self.config = config or BridgeConfig.from_env()
        self.staged_dir = self.spoke_root / ".md" / "idop_staged"
        self.staged_files_dir = self.staged_dir / "files"
        self.sync_service = CdeDocumentSyncService(self.config)

    def _ensure_staged_dirs(self) -> None:
        self.staged_dir.mkdir(parents=True, exist_ok=True)
        self.staged_files_dir.mkdir(parents=True, exist_ok=True)

    def stage(
        self,
        file_path: Path,
        task_id: str,
        title: str | None = None,
        project_code: str = "UNKNOWN",
        national_project_id: str = "",
        contract_id: str = "",
        author_name: str = "",
        author_email: str = "",
        department: str = "",
        seat_role: str = "",
        notes: str = "",
        iso_doc_name: str = "",
        approval_status: str = "S1",
    ) -> StagedSubmittal:
        """Stages a submittal payload into Local Staging Queue (.md/idop_staged/).

        Conforms to ADR-0043 STAGED_LOCAL zero-downtime offline pattern.
        """
        self._ensure_staged_dirs()
        target_path = Path(file_path).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Submittal file does not exist: {target_path}")

        file_sha = compute_file_sha256(target_path)
        submittal_title = title or target_path.stem
        comp_key = compute_composite_key(
            project_code=project_code,
            contract_id=contract_id,
            stage_id=task_id,
            submittal_name=submittal_title,
        )

        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        receipt_id = f"PGV-{timestamp_str}-{task_id}"

        submittal = StagedSubmittal(
            receipt_id=receipt_id,
            composite_key=comp_key,
            task_id=task_id,
            title=submittal_title,
            project_code=project_code,
            national_project_id=national_project_id,
            contract_id=contract_id,
            author_name=author_name,
            author_email=author_email,
            department=department,
            seat_role=seat_role,
            source_file=str(target_path),
            file_name=target_path.name,
            file_size_bytes=target_path.stat().st_size,
            sha256=file_sha,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            status="STAGED_LOCAL",
            notes=notes,
        )

        receipt_file = self.staged_dir / f"{receipt_id}.json"
        with open(receipt_file, "w", encoding="utf-8") as f:
            json.dump(asdict(submittal), f, ensure_ascii=False, indent=2)

        logger.info(
            "Staged submittal %s (Key: %s) to %s",
            receipt_id,
            comp_key[:12],
            receipt_file.name,
        )
        return submittal

    def list_staged(self, status: str | None = None) -> list[StagedSubmittal]:
        """Lists all staged submittal records from .md/idop_staged/."""
        if not self.staged_dir.exists():
            return []

        results: list[StagedSubmittal] = []
        for json_file in sorted(self.staged_dir.glob("PGV-*.json")):
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                submittal = StagedSubmittal(**data)
                if status is None or submittal.status == status:
                    results.append(submittal)
            except Exception as e:
                logger.warning("Failed to parse staged receipt %s: %s", json_file.name, e)

        return results

    def flush(
        self,
        dry_run: bool | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Performs Idempotent Replay of all STAGED_LOCAL submittals to SharePoint Online.

        In DEV mode or with dry_run=True, simulates successful sync with mock IDs.
        In PROD mode, pushes to CDEDocuments and updates status to SYNCED_SHAREPOINT.
        """
        pending = self.list_staged(status="STAGED_LOCAL")
        is_dry = self.config.dry_run if dry_run is None else dry_run

        logger.info(
            "Found %d pending STAGED_LOCAL submittals to flush (Limit: %d)", len(pending), limit
        )

        synced_count = 0
        failed_count = 0
        results: list[dict[str, Any]] = []

        # Track processed composite keys in this run to guarantee deduplication
        processed_keys: set[str] = set()

        for item in pending[:limit]:
            receipt_file = self.staged_dir / f"{item.receipt_id}.json"

            # Check for intra-batch duplicate composite key
            if item.composite_key in processed_keys:
                logger.info(
                    "Skipping duplicate composite key %s for %s",
                    item.composite_key[:12],
                    item.receipt_id,
                )
                continue

            processed_keys.add(item.composite_key)

            doc_payload = {
                "Title": item.title,
                "ProjectCode": item.project_code,
                "DocumentCode": item.task_id,
                "IsoDocumentName": item.title,
                "ApprovalStatus": "S1",
                "CompositeKey": item.composite_key,
                "Originator": "CCBA",
            }

            sync_res = self.sync_service.sync_cde_document(doc_payload, dry_run=is_dry)

            if sync_res.success:
                item.status = "SYNCED_SHAREPOINT" if not is_dry else "SYNCED_MOCK_SANDBOX"
                item.sharepoint_item_id = sync_res.item_id
                item.synced_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                item.error_message = None

                with open(receipt_file, "w", encoding="utf-8") as f:
                    json.dump(asdict(item), f, ensure_ascii=False, indent=2)

                synced_count += 1
                results.append(
                    {
                        "receipt_id": item.receipt_id,
                        "composite_key": item.composite_key,
                        "status": item.status,
                        "item_id": item.sharepoint_item_id,
                    }
                )
            else:
                failed_count += 1
                item.error_message = sync_res.error_message
                with open(receipt_file, "w", encoding="utf-8") as f:
                    json.dump(asdict(item), f, ensure_ascii=False, indent=2)

                results.append(
                    {
                        "receipt_id": item.receipt_id,
                        "composite_key": item.composite_key,
                        "status": "FAILED",
                        "error": sync_res.error_message,
                    }
                )

        return {
            "total_pending": len(pending),
            "processed": len(results),
            "synced": synced_count,
            "failed": failed_count,
            "dry_run": is_dry,
            "results": results,
        }
