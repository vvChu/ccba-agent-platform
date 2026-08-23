"""CCBA Personal Sandbox Deliverable Promotion Engine (ADR 0046).

Coordinates the 3-step deliverable promotion pipeline from personal sandbox
workspaces to official project delivery repositories and IDOP task staging.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

WATERMARK_HEADER = "[CCBA SANDBOX DRAFT — BẢN THẢO NGHIÊN CỨU NỘI BỘ — CHƯA PHÁT HÀNH CHÍNH THỨC]"


@dataclass
class PromotionResult:
    """Outcome of deliverable promotion from a personal sandbox."""

    success: bool
    promoted_files: list[str] = field(default_factory=list)
    staged_receipt_path: Path | None = None
    message: str = ""


class SandboxPromoter:
    """Engine executing the 3-step promotion pipeline defined in ADR 0046."""

    def __init__(self, sandbox_root: Path | str = ".") -> None:
        """Initialize SandboxPromoter with sandbox workspace root."""
        self.sandbox_root = Path(sandbox_root).resolve()
        self.context_path = self.sandbox_root / ".md" / "workspace_context.yaml"
        self.context_data = self._load_context()
        self._validate_source_sandbox()

    def _load_context(self) -> dict[str, Any]:
        """Load and parse workspace_context.yaml."""
        if not self.context_path.exists():
            return {}
        try:
            with open(self.context_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _validate_source_sandbox(self) -> None:
        """Ensure current workspace is configured as a personal sandbox."""
        project = self.context_data.get("project", {})
        sub_type = project.get("sub_type", "")
        archetype = project.get("archetype", "")

        is_sandbox = (
            sub_type == "personal_sandbox"
            or self.context_data.get("guardrails", {}).get("sandbox_mode", False)
        )
        if not is_sandbox and archetype != "specialized_extension":
            raise ValueError(
                f"Source workspace '{self.sandbox_root.name}' is not a personal_sandbox "
                f"(archetype: {archetype}, sub_type: {sub_type}). Promotion aborted."
            )

    @staticmethod
    def _cleanse_content(text: str) -> str:
        """Strip sandbox watermark header and trailing artifact noise."""
        if WATERMARK_HEADER in text:
            text = text.replace(f"{WATERMARK_HEADER}\n\n", "")
            text = text.replace(f"{WATERMARK_HEADER}\n", "")
            text = text.replace(WATERMARK_HEADER, "")
        return text.lstrip("\n")

    @staticmethod
    def _compute_sha256(content: str) -> str:
        """Compute SHA-256 hex digest of string content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _stage_pgv_handover(
        self,
        target_spoke: Path,
        promoted_file_records: list[dict[str, str]],
        pgv_code: str | None,
        dry_run: bool,
    ) -> Path | None:
        """Create a staged PGV sign-off receipt for IDOP."""
        if not pgv_code:
            return None

        staged_dir = self.sandbox_root / ".md" / "idop_staged"
        if not dry_run:
            staged_dir.mkdir(parents=True, exist_ok=True)

        identity = self.context_data.get("organizational_identity", {})
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        receipt_filename = f"pgv_handover_{pgv_code}_{timestamp}.json"
        receipt_path = staged_dir / receipt_filename

        receipt_payload = {
            "pgv_code": pgv_code,
            "status": "AWAITING_PM_APPROVAL",
            "timestamp": timestamp,
            "target_spoke": target_spoke.name,
            "author": {
                "owner_name": identity.get("owner_name", "Unknown Engineer"),
                "owner_email": identity.get("owner_email", "unknown@ibst-bim.vn"),
                "department": identity.get("department", "PHONG_RD_HTQT"),
                "seat_role": identity.get("seat_role", "KY_SU_THUC_THI"),
            },
            "deliverables": promoted_file_records,
        }

        if not dry_run:
            receipt_path.write_text(
                json.dumps(receipt_payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        return receipt_path

    def promote(
        self,
        target_spoke_path: Path | str,
        files: list[str],
        pgv_code: str | None = None,
        dry_run: bool = False,
    ) -> PromotionResult:
        """Execute the 3-step promotion pipeline for selected files.

        Args:
            target_spoke_path: Destination spoke root directory.
            files: Relative paths of files to promote.
            pgv_code: Optional Phiếu Giao Việc code for IDOP staging.
            dry_run: If True, simulates operations without writing files.

        Returns:
            PromotionResult detailing success, files copied, and staged receipt path.
        """
        target_spoke = Path(target_spoke_path).resolve()
        if not target_spoke.exists():
            raise FileNotFoundError(f"Target spoke not found: {target_spoke}")

        promoted_records: list[dict[str, str]] = []
        promoted_files: list[str] = []

        for rel_file in files:
            source_file = self.sandbox_root / rel_file
            if not source_file.exists():
                continue

            target_file = target_spoke / rel_file
            content = source_file.read_text(encoding="utf-8")
            cleansed = self._cleanse_content(content)
            sha256_hash = self._compute_sha256(cleansed)

            if not dry_run:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(cleansed, encoding="utf-8")

            promoted_files.append(rel_file)
            promoted_records.append(
                {
                    "relative_path": rel_file,
                    "sha256": sha256_hash,
                    "lines_count": str(len(cleansed.splitlines())),
                }
            )

        staged_path = self._stage_pgv_handover(
            target_spoke=target_spoke,
            promoted_file_records=promoted_records,
            pgv_code=pgv_code,
            dry_run=dry_run,
        )

        msg = (
            f"Successfully promoted {len(promoted_files)} file(s) to '{target_spoke.name}'."
        )
        if dry_run:
            msg = f"[DRY-RUN] Would promote {len(promoted_files)} file(s) to '{target_spoke.name}'."

        return PromotionResult(
            success=True,
            promoted_files=promoted_files,
            staged_receipt_path=staged_path,
            message=msg,
        )
