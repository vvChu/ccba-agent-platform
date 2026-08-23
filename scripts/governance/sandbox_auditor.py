"""sandbox_auditor.py - Auditing Sandbox Watermarks and QC Level Authorization Caps (ADR 0046).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.governance.base import AuditIssue, BaseAuditor, GovernanceAuditReport
from scripts.spoke.sandbox_promoter import WATERMARK_HEADER


class SandboxAuditor(BaseAuditor):
    """Audits personal sandboxes for watermark presence and QC level authorization caps."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        if isinstance(project_root, str):
            project_root = Path(project_root)
        super().__init__(project_root=project_root)
        self.context_file = self.project_root / ".md" / "workspace_context.yaml"
        if not self.context_file.exists():
            self.context_file = self.project_root / ".agents" / "workspace_context.yaml"

    def _load_context(self) -> dict[str, Any]:
        """Load and parse workspace_context.yaml safely."""
        if not self.context_file.exists():
            return {}
        try:
            with open(self.context_file, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _is_sandbox(self, context: dict[str, Any]) -> bool:
        """Determine whether current workspace is a personal sandbox."""
        proj = context.get("project", {})
        sub_type = proj.get("sub_type", "")
        guardrails = context.get("guardrails", {})
        return sub_type == "personal_sandbox" or guardrails.get("sandbox_mode") is True

    def _audit_qc_cap(self, context: dict[str, Any], issues: list[AuditIssue]) -> None:
        """Ensure personal sandbox does not claim QC authorization > LEVEL_1."""
        qc_gov = context.get("qc_governance", {})
        auth_level = qc_gov.get("authorized_qc_level", "")
        can_approve_iso = qc_gov.get("can_approve_iso_documents", False)

        forbidden_levels = {
            "LEVEL_2_MANAGEMENT_APPROVAL",
            "LEVEL_3_DEPARTMENT_REVIEW",
            "LEVEL_4_COMPLIANCE_QA",
            "LEVEL_5_FINAL_APPROVAL",
        }
        if auth_level in forbidden_levels:
            issues.append(
                AuditIssue(
                    line_number=1,
                    subject="qc_governance.authorized_qc_level",
                    message=f"[QC_CAP_VIOLATION] Personal sandbox authorization cannot exceed LEVEL_1_TECHNICAL_CHECK (found: {auth_level}).",
                    category="SandboxGuardrail",
                    file_path=str(self.context_file),
                )
            )
        if can_approve_iso is True:
            issues.append(
                AuditIssue(
                    line_number=1,
                    subject="qc_governance.can_approve_iso_documents",
                    message="[ISO_CAP_VIOLATION] Personal sandbox cannot approve ISO documents directly.",
                    category="SandboxGuardrail",
                    file_path=str(self.context_file),
                )
            )

    def _audit_watermarks(self, issues: list[AuditIssue]) -> int:
        """Verify that deliverables in output folders contain draft watermark header."""
        scanned = 0
        output_dirs = [
            self.project_root / "output",
            self.project_root / "deliverables",
            self.project_root / "reports",
        ]
        for out_dir in output_dirs:
            if not out_dir.exists():
                continue
            for doc_file in out_dir.glob("**/*"):
                if not doc_file.is_file() or doc_file.suffix.lower() not in (".md", ".txt"):
                    continue
                scanned += 1
                try:
                    content = doc_file.read_text(encoding="utf-8")
                    if WATERMARK_HEADER not in content:
                        issues.append(
                            AuditIssue(
                                line_number=1,
                                subject=doc_file.name,
                                message=f"[MISSING_SANDBOX_WATERMARK] Draft file must include the sandbox draft watermark header: {WATERMARK_HEADER}",
                                category="SandboxGuardrail",
                                file_path=str(doc_file),
                            )
                        )
                except Exception:
                    continue
        return scanned

    def audit(self, target: Any = None) -> GovernanceAuditReport:
        """Execute sandbox governance audits."""
        issues: list[AuditIssue] = []
        context = self._load_context()

        if not self._is_sandbox(context):
            return GovernanceAuditReport(issues=[], total_issues=0, has_hard_errors=False, scanned_files=0)

        self._audit_qc_cap(context, issues)
        scanned = self._audit_watermarks(issues)

        return GovernanceAuditReport(
            issues=issues,
            total_issues=len(issues),
            has_hard_errors=len(issues) > 0,
            scanned_files=scanned + 1,
        )
