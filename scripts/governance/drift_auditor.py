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
    clean_path = filepath.strip(" \t\n\r\"'").replace("\\", "/").strip().lstrip("/")
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
                        raw = line[3:].strip()
                        if " -> " in raw:
                            raw = raw.split(" -> ")[-1].strip()
                        raw = raw.strip(" \t\n\r\"'")
                        if raw:
                            modified.add((self.project_root / raw).resolve())

            for ref in [
                "origin/main...HEAD",
                "main...HEAD",
                "origin/master...HEAD",
                "master...HEAD",
            ]:
                res_diff = subprocess.run(
                    ["git", "diff", "--name-only", ref],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if res_diff.returncode == 0:
                    for line in res_diff.stdout.splitlines():
                        raw = line.strip().strip(" \t\n\r\"'")
                        if raw:
                            modified.add((self.project_root / raw).resolve())
                    break
        except Exception:
            pass
        return modified

    def check_marker_drift(self, docs: list[Path] | None = None) -> list[str]:
        """Layer 1: Invariant Marker Drift Gate.

        Uses ArchStatsUpdater to compare actual filesystem counts against
        registered HTML invariant markers (<!-- KEY_START -->...<!-- KEY_END -->)
        in architecture documents (README.md, PLATFORM.md, CONTEXT.md, etc.).
        """
        drift_errors: list[str] = []
        try:
            updater = ArchStatsUpdater(project_root=self.project_root)
            counts = updater.get_counts()
            target_docs = docs or [self.project_root / p for p in ArchStatsUpdater.DEFAULT_DOCS]

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

        Checks if Level-1 structural files were added/deleted/renamed/copied without
        updating architecture documentation. Intentionally ignores internal
        sub-resources within skills or packages (e.g. test_cases/, references/,
        resources/, src/, tests/).
        """
        drift_errors: list[str] = []
        try:
            structural_change = False
            arch_doc_updated = False

            # 1. Collect branch diff changes (handling tabs, renames, and quotes)
            diff_success = False
            ref_candidates = [
                "origin/main...HEAD",
                "main...HEAD",
                "origin/master...HEAD",
                "master...HEAD",
                "HEAD~1",
            ]
            for ref in ref_candidates:
                res = subprocess.run(
                    ["git", "diff", "--name-status", ref],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if res.returncode == 0:
                    diff_success = True
                    for line in res.stdout.splitlines():
                        line_str = line.strip()
                        if not line_str:
                            continue
                        parts = line_str.split("\t")
                        if not parts:
                            continue
                        status = parts[0].strip()
                        paths = [p.strip(" \t\n\r\"'") for p in parts[1:] if p.strip(" \t\n\r\"'")]
                        is_mutation = (
                            status.startswith("A")
                            or status.startswith("D")
                            or status.startswith("R")
                            or status.startswith("C")
                        )
                        for filepath in paths:
                            norm_path = filepath.replace("\\", "/").lstrip("/")
                            if norm_path in self.ARCH_DOCS:
                                arch_doc_updated = True
                            if is_mutation and self.is_structural_path(norm_path):
                                structural_change = True
                    break

            if not diff_success:
                res_cached = subprocess.run(
                    ["git", "diff", "--name-status", "--cached"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if res_cached.returncode == 0:
                    for line in res_cached.stdout.splitlines():
                        line_str = line.strip()
                        if not line_str:
                            continue
                        parts = line_str.split("\t")
                        if not parts:
                            continue
                        status = parts[0].strip()
                        paths = [p.strip(" \t\n\r\"'") for p in parts[1:] if p.strip(" \t\n\r\"'")]
                        is_mutation = (
                            status.startswith("A")
                            or status.startswith("D")
                            or status.startswith("R")
                            or status.startswith("C")
                        )
                        for filepath in paths:
                            norm_path = filepath.replace("\\", "/").lstrip("/")
                            if norm_path in self.ARCH_DOCS:
                                arch_doc_updated = True
                            if is_mutation and self.is_structural_path(norm_path):
                                structural_change = True

            # 2. Collect porcelain status (uncommitted, unstaged, untracked, composite states)
            res2 = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res2.returncode == 0:
                for line in res2.stdout.splitlines():
                    if len(line) < 3:
                        continue
                    status = line[:2].strip()
                    rest = line[3:].strip()
                    if " -> " in rest:
                        raw_paths = rest.split(" -> ")
                    else:
                        raw_paths = [rest]
                    paths = [p.strip(" \t\n\r\"'") for p in raw_paths if p.strip(" \t\n\r\"'")]
                    is_mutation = status == "??" or any(ch in status for ch in ("A", "D", "R", "C"))
                    for filepath in paths:
                        norm_path = filepath.replace("\\", "/").lstrip("/")
                        if norm_path in self.ARCH_DOCS:
                            arch_doc_updated = True
                        if is_mutation and self.is_structural_path(norm_path):
                            structural_change = True

            # 3. Check if any commit in current branch history updated arch_docs via name-only diff
            if not arch_doc_updated:
                for ref in [
                    "origin/main...HEAD",
                    "main...HEAD",
                    "origin/master...HEAD",
                    "master...HEAD",
                ]:
                    res_diff_names = subprocess.run(
                        ["git", "diff", "--name-only", ref],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                    )
                    if res_diff_names.returncode == 0:
                        for fname in res_diff_names.stdout.splitlines():
                            clean_name = fname.strip(" \t\n\r\"'").replace("\\", "/").lstrip("/")
                            if clean_name in self.ARCH_DOCS:
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
