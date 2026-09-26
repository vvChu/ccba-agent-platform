"""drift_auditor.py - Sub-Auditor for Architecture Drift detection and Git change tracking.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from scripts.scaffolding.arch_stats import ArchStatsUpdater

from .base import AuditIssue, BaseAuditor


def is_structural_path(filepath: str) -> bool:
    """Check if filepath represents a Level-1 platform structural element.

    Level-1 structural elements:
    - Root manifest: pyproject.toml
    - Package manifests: packages/<name>/pyproject.toml
    - Skill manifests: .agents/skills/<name>/SKILL.md
    - Workflow definitions: .agents/workflows/*.md (excluding .md.bak)
    - Direct Level-1 scripts: scripts/*.py (directly under scripts/, excluding subdirectories)

    Internal skill/package resources (test_cases/, references/, resources/, src/, tests/)
    are ignored.
    """
    clean_path = filepath.replace("\\", "/").strip().lstrip("/")
    parts = clean_path.split("/")

    # 1. Root configuration manifest
    if clean_path == "pyproject.toml":
        return True

    # 2. Package manifest: packages/<name>/pyproject.toml
    if len(parts) == 3 and parts[0] == "packages" and parts[2] == "pyproject.toml":
        return True

    # 3. Skill manifest: .agents/skills/<name>/SKILL.md
    if (
        len(parts) == 4
        and parts[0] == ".agents"
        and parts[1] == "skills"
        and parts[3] == "SKILL.md"
    ):
        return True

    # 4. Workflow definitions: .agents/workflows/*.md (ignoring .md.bak)
    if (
        len(parts) == 3
        and parts[0] == ".agents"
        and parts[1] == "workflows"
        and parts[2].endswith(".md")
        and not parts[2].endswith(".md.bak")
    ):
        return True

    # 5. Direct Level-1 scripts: scripts/*.py (directly under scripts/, excluding subdirectories)
    if len(parts) == 2 and parts[0] == "scripts" and parts[1].endswith(".py"):
        return True

    return False


class DriftAuditor(BaseAuditor):
    """Deep Sub-Auditor for Architecture Drift detection and Git workspace modification checks."""

    ARCH_DOCS = {
        "README.md",
        "PLATFORM.md",
        "CONTEXT.md",
        ".github/copilot-instructions.md",
        ".md/knowledge/CONTEXT.md",
        ".agents/skills/ccba-adr-lifecycle/references/architecture_sync_guide.md",
        ".agents/skills/ccba-adr-lifecycle/SKILL.md",
    }

    is_structural_path = staticmethod(is_structural_path)

    def get_modified_files(self) -> set[Path]:
        """Get set of modified files in the current git workspace or branch."""
        modified: set[Path] = set()
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
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

    def check_marker_drift(self, docs: list[Path] | None = None) -> list[str]:
        """Layer 1: Invariant Marker Drift Gate.

        Uses ArchStatsUpdater to compare actual filesystem counts against
        registered HTML invariant markers (<!-- KEY_START -->...<!-- KEY_END -->)
        in architecture documents (README.md, PLATFORM.md, etc.).
        """
        drift_errors: list[str] = []
        try:
            updater = ArchStatsUpdater(project_root=self.project_root)
            counts = updater.get_counts()
            target_docs = docs or [
                self.project_root / "README.md",
                self.project_root / "PLATFORM.md",
            ]

            for doc_item in target_docs:
                doc_path = doc_item if isinstance(doc_item, Path) else Path(doc_item)
                target = doc_path if doc_path.is_absolute() else self.project_root / doc_path
                if not target.exists():
                    continue
                try:
                    content = target.read_text(encoding="utf-8")
                except Exception:
                    continue

                try:
                    rel_name = target.relative_to(self.project_root).as_posix()
                except ValueError:
                    rel_name = target.name

                for key, expected_val in counts.items():
                    pattern = re.compile(
                        rf"<!--\s*{key}_START\s*-->(.*?)<!--\s*{key}_END\s*-->", re.DOTALL
                    )
                    for match in pattern.finditer(content):
                        actual_val = match.group(1).strip()
                        if actual_val != expected_val:
                            drift_errors.append(
                                f"Invariant marker drift in {rel_name}: {key} is '{actual_val}', "
                                f"but actual count is '{expected_val}'. Run 'python scripts/update_arch_stats.py' and commit."
                            )
                            break
        except Exception:
            pass
        return drift_errors

    def check_structural_git_drift(self) -> list[str]:
        """Layer 2: Hierarchy-Aware Structural Git Gate.

        Checks if Level-1 structural files were added/deleted/renamed without
        updating architecture documentation. Intentionally ignores internal
        sub-resources within skills or packages (e.g. test_cases/, references/,
        resources/, src/, tests/).
        """
        drift_errors: list[str] = []
        try:
            changes: list[str] = []
            res = subprocess.run(
                ["git", "diff", "--name-status", "origin/main...HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                changes.extend(res.stdout.splitlines())
            else:
                res_alt = subprocess.run(
                    ["git", "diff", "--name-status", "HEAD~1"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if res_alt.returncode == 0:
                    changes.extend(res_alt.stdout.splitlines())
                else:
                    res_cached = subprocess.run(
                        ["git", "diff", "--name-status", "--cached"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                    )
                    if res_cached.returncode == 0:
                        changes.extend(res_cached.stdout.splitlines())

            res2 = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res2.returncode == 0:
                changes.extend(res2.stdout.splitlines())

            structural_change = False
            arch_doc_updated = False

            for line in changes:
                line_str = line.strip()
                if not line_str:
                    continue
                parts = line_str.split()
                if not parts:
                    continue
                status = parts[0]
                paths = [p for p in parts[1:] if p != "->"]

                for filepath in paths:
                    norm_path = filepath.replace("\\", "/").strip().lstrip("/")

                    if norm_path in self.ARCH_DOCS:
                        arch_doc_updated = True

                    if (
                        status.startswith("A")
                        or status.startswith("D")
                        or status.startswith("R")
                        or status == "??"
                    ):
                        if self.is_structural_path(norm_path):
                            structural_change = True

            # Check if any commit in current branch history updated arch_docs
            ref_candidates = [
                "origin/main..HEAD",
                "origin/master..HEAD",
                "main..HEAD",
                "master..HEAD",
            ]
            for ref in ref_candidates:
                res_log = subprocess.run(
                    ["git", "log", ref, "--name-only"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if res_log.returncode == 0:
                    for log_line in res_log.stdout.splitlines():
                        clean_log_line = log_line.strip().replace("\\", "/").lstrip("/")
                        if clean_log_line in self.ARCH_DOCS:
                            arch_doc_updated = True
                    break

            if structural_change and not arch_doc_updated:
                drift_errors.append(
                    "Structural drift detected: You added/deleted/renamed Level-1 structural files "
                    "(skills, packages, workflows, root pyproject, scripts) but did not update "
                    "Architecture Docs (README.md, PLATFORM.md). Run 'python scripts/update_arch_stats.py' and commit."
                )
        except Exception:
            pass
        return drift_errors

    def check_architecture_drift(self) -> list[str]:
        """Check architecture drift across both Defense-in-Depth layers."""
        drift_errors: list[str] = []
        drift_errors.extend(self.check_marker_drift())
        drift_errors.extend(self.check_structural_git_drift())
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


__all__ = [
    "DriftAuditor",
    "is_structural_path",
]
