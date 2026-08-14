"""drift_auditor.py - Sub-Auditor for Architecture Drift detection and Git change tracking.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import AuditIssue, BaseAuditor


class DriftAuditor(BaseAuditor):
    """Deep Sub-Auditor for Architecture Drift detection and Git workspace modification checks."""

    def get_modified_files(self) -> set[Path]:
        """Get set of modified files in the current git workspace or branch."""
        modified = set()
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if len(line) > 3:
                        filepath = (self.project_root / line[3:].strip()).resolve()
                        modified.add(filepath)

            res = subprocess.run(
                ["git", "diff", "--name-only", "origin/main...HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if line.strip():
                        filepath = (self.project_root / line.strip()).resolve()
                        modified.add(filepath)
        except Exception:
            pass
        return modified

    def check_architecture_drift(self) -> list[str]:
        """Check if structural files were added/deleted without updating architecture docs."""
        drift_errors = []
        try:
            res = subprocess.run(
                ["git", "diff", "--name-status", "origin/main...HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                res = subprocess.run(
                    ["git", "diff", "--name-status", "HEAD~1"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

            changes = res.stdout.splitlines()
            res2 = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            changes.extend(res2.stdout.splitlines())

            structural_change = False
            arch_doc_updated = False
            arch_docs = {"README.md", "PLATFORM.md", ".agents/skills/architecture-sync/SKILL.md"}
            tracked_prefixes = ("packages/", "scripts/", ".agents/skills/", ".agents/workflows/")

            for line in changes:
                if not line.strip():
                    continue
                parts = line.split()
                status = parts[0]
                filepath = parts[-1].strip().replace("\\", "/")

                if filepath in arch_docs or (status.startswith("M") and filepath in arch_docs):
                    arch_doc_updated = True

            # Also check if any commit in the current branch history updated arch_docs
            res_log = subprocess.run(
                ["git", "log", "origin/main..HEAD", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res_log.returncode == 0:
                for line in res_log.stdout.splitlines():
                    if line.strip() in arch_docs:
                        arch_doc_updated = True

                if (
                    status.startswith("A")
                    or status.startswith("D")
                    or status.startswith("R")
                    or status == "??"
                ):
                    if filepath == "pyproject.toml" or filepath.startswith(tracked_prefixes):
                        structural_change = True

            if structural_change and not arch_doc_updated:
                drift_errors.append(
                    "Structural drift detected: You added/deleted/renamed files in core directories (packages, scripts, skills, workflows) but did not update Architecture Docs (README.md, PLATFORM.md, architecture-sync). Run 'python scripts/update_arch_stats.py' and commit."
                )
        except Exception:
            pass
        return drift_errors

    def audit(self, target: Any = None) -> list[AuditIssue]:
        """Audit architecture drift and return AuditIssue list."""
        drift_messages = self.check_architecture_drift()
        issues: list[AuditIssue] = []
        for msg in drift_messages:
            issues.append(
                AuditIssue(
                    line_number=0,
                    subject="Architecture Drift",
                    message=msg,
                    category="architecture_drift",
                    file_path="README.md",
                )
            )
        return issues
