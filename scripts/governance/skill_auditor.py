"""skill_auditor.py - Sub-Auditor for CCBA Agent Skills & Workflows compliance.

Enforces:
1. Skill frontmatter validity and description length (<= 180 chars for model-invoked skills).
2. Step completion criteria ('**Tiêu chí hoàn thành:**' or '**Completion Criterion:**').
3. Zero-Duplicate Gate: No duplicate skill names across the workspace.
4. Context Budget Ceiling Gate: <= 10 model-invoked skills per bundle (ADR-0040).
5. Taxonomy & Shallow Skill Inspection (ADR-0040).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ccba_harness.skill_validator import (
    DEFAULT_VALID_BUNDLES,
    MAX_MODEL_INVOKED_PER_BUNDLE,
    SHALLOW_SKILL_MIN_LINES,
    SkillValidator,
)

from .base import AuditIssue, BaseAuditor


class SkillAuditor(BaseAuditor):
    """Deep Sub-Auditor for Agent skills, YAML frontmatters, character limits, step completion criteria and 4-Layer CI Gates."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize skill auditor with project root."""
        super().__init__(project_root)
        self._validator = SkillValidator(project_root=self.project_root)

    @property
    def _cached_valid_bundles(self) -> set[str] | None:
        return self._validator._cached_valid_bundles

    @_cached_valid_bundles.setter
    def _cached_valid_bundles(self, value: set[str] | None) -> None:
        self._validator._cached_valid_bundles = value

    def get_valid_bundles(self) -> set[str]:
        """Load valid bundles from catalog.yaml or fallback to known taxonomy."""
        return self._validator.get_valid_bundles()

    def check_shallow_skill(self, file_path: Path, content: str | None = None) -> list[AuditIssue]:
        """Verify that a skill has at least SHALLOW_SKILL_MIN_LINES content lines (ADR-0040)."""
        raw_issues = self._validator.check_shallow_skill(file_path, content)
        return [AuditIssue(*i) for i in raw_issues]

    def audit_skill(
        self,
        file_path: Path,
        check_shallow: bool = False,
        enforce_gpi: bool = False,
    ) -> list[AuditIssue]:
        """Audit a single SKILL.md or workflow file for CCBA compliance."""
        raw_issues = self._validator.audit_skill(
            file_path, check_shallow=check_shallow, enforce_gpi=enforce_gpi
        )
        if not enforce_gpi:
            raw_issues = [i for i in raw_issues if i.category != "INSUFFICIENT_GPI_SCORE"]
        return [AuditIssue(*i) for i in raw_issues]

    def _analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
        """Helper to scan workflow steps for Completion Criteria."""
        return self._validator._analyze_steps_completion_criteria(body)

    def audit_workspace_gates(self, skills_dir: Path | None = None) -> list[AuditIssue]:
        """Perform workspace-level Hard CI Gate checks across all skills."""
        raw_issues = self._validator.audit_workspace_gates(skills_dir)
        return [AuditIssue(*i) for i in raw_issues]

    def audit_workflow(self, file_path: Path) -> list[AuditIssue]:
        """Audit a single workflow file for CCBA compliance."""
        raw_issues = self._validator.audit_workflow(file_path)
        return [AuditIssue(*i) for i in raw_issues]

    def audit_workspace(self) -> dict[str, Any]:
        """Audit all skills and workflows in the workspace."""
        skill_issues: list[AuditIssue] = []
        workflow_issues: list[AuditIssue] = []
        skills_dir = self.project_root / ".agents" / "skills"
        workflows_dir = self.project_root / ".agents" / "workflows"

        if skills_dir.exists():
            for skill_path in skills_dir.rglob("SKILL.md"):
                skill_issues.extend(self.audit_skill(skill_path))
            skill_issues.extend(self.audit_workspace_gates(skills_dir))

        if workflows_dir.exists():
            for wf_path in workflows_dir.glob("*.md"):
                workflow_issues.extend(self.audit_workflow(wf_path))

        all_issues = skill_issues + workflow_issues
        return {
            "skills": skill_issues,
            "workflows": workflow_issues,
            "total_skill_issues": len(skill_issues),
            "total_workflow_issues": len(workflow_issues),
            "total_issues": len(all_issues),
        }

    def audit(self, target: Path) -> list[AuditIssue]:
        """Polymorphic entry point for auditing a skill/workflow file or directory."""
        if target.is_file():
            if target.name == "SKILL.md":
                return self.audit_skill(target)
            return self.audit_workflow(target)
        issues: list[AuditIssue] = []
        for skill_path in target.rglob("SKILL.md"):
            issues.extend(self.audit_skill(skill_path))
        for wf_path in target.rglob("*.md"):
            if wf_path.name != "SKILL.md" and "workflows" in wf_path.parts:
                issues.extend(self.audit_workflow(wf_path))
        issues.extend(self.audit_workspace_gates(target))
        return issues


__all__ = [
    "DEFAULT_VALID_BUNDLES",
    "MAX_MODEL_INVOKED_PER_BUNDLE",
    "SHALLOW_SKILL_MIN_LINES",
    "SkillAuditor",
]
