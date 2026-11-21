"""skill_validator.py - Standalone Quality & Compliance Validator Facade for CCBA Skills.

Enforces:
1. Frontmatter validity, YAML schema, and description limits (<= 180 chars for model-invoked skills).
2. Bundle taxonomy validation and namespace governance (ccba-, bigbim-, platform-loader).
3. Slash command contract (user-invocable: true requires command: /... per ADR-0056).
4. Step completion criteria ('**Tiêu chí hoàn thành:**' or '**Completion Criterion:**').
5. Shallow Skill Warning Gate (< 35 non-empty content lines per ADR-0040).
6. Workspace Gates: Zero-Duplicate Gate and Context Budget Ceiling Gate (<= 10 model-invoked skills/bundle).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._skill_content_checks import (
    ALLOWED_HOST_COMMANDS,
    COMMON_PATH_SEGMENTS,
    EXCLUSION_HEADERS,
    GITLAB_QUICK_ACTIONS,
    LINK_EXTRACT_RE,
    SLASH_CMD_RE,
    STEP_LINE_RE,
    WORKFLOW_HEADERS,
    audit_slash_commands_in_file,
    audit_workflow_file,
    is_exclusion_header,
    validate_markdown_links_in_file,
)
from ._skill_content_checks import (
    analyze_steps_completion_criteria as _analyze_steps_completion_criteria_fn,
)
from ._skill_frontmatter import (
    DEFAULT_VALID_BUNDLES,
    FRONTMATTER_RE,
    MAX_MODEL_INVOKED_PER_BUNDLE,
    SHALLOW_SKILL_MIN_LINES,
    AuditIssueString,
    SkillAuditIssue,
    check_shallow_skill_content,
    load_registered_commands,
    load_valid_bundles,
    parse_frontmatter_dict,
    validate_skill_frontmatter_metadata,
)
from ._skill_gpi_gates import (
    audit_granularity_and_gpi_impl,
    audit_workspace_gates_impl,
    evaluate_skill_file_decision,
)
from .gpi import (
    ArchitectureTier,
    DecisionRequest,
    DecisionResult,
    GPIMetrics,
    calculate_gpi,
    evaluate_two_stage_decision,
)

try:
    import yaml
except ImportError:
    yaml = None

__all__ = [
    "ALLOWED_HOST_COMMANDS",
    "COMMON_PATH_SEGMENTS",
    "DEFAULT_VALID_BUNDLES",
    "EXCLUSION_HEADERS",
    "FRONTMATTER_RE",
    "GITLAB_QUICK_ACTIONS",
    "LINK_EXTRACT_RE",
    "MAX_MODEL_INVOKED_PER_BUNDLE",
    "SHALLOW_SKILL_MIN_LINES",
    "SLASH_CMD_RE",
    "STEP_LINE_RE",
    "WORKFLOW_HEADERS",
    "AuditIssueString",
    "SkillAuditIssue",
    "SkillValidator",
    "is_exclusion_header",
]


class SkillValidator:
    """Standalone validator facade for CCBA skills, workflows, and workspace gates."""

    def __init__(
        self,
        project_root: Path | None = None,
        valid_bundles: set[str] | None = None,
    ) -> None:
        self.project_root = Path.cwd() if project_root is None else Path(project_root).resolve()
        self._custom_valid_bundles = valid_bundles
        self._cached_valid_bundles: set[str] | None = None

    def get_valid_bundles(self) -> set[str]:
        """Load valid bundles from catalog.yaml, custom set, or fallback taxonomy."""
        if self._custom_valid_bundles is not None:
            return set(self._custom_valid_bundles)
        if self._cached_valid_bundles is not None:
            return self._cached_valid_bundles
        self._cached_valid_bundles = load_valid_bundles(self.project_root, yaml_module=yaml)
        return self._cached_valid_bundles

    def get_registered_commands(self) -> set[str]:
        """Retrieve canonical registered slash commands from catalog.yaml plus host commands."""
        extra = set(ALLOWED_HOST_COMMANDS) | set(GITLAB_QUICK_ACTIONS)
        return load_registered_commands(self.project_root, extra, yaml_module=yaml)

    def validate_markdown_links(self, file_path: Path, content: str | None = None) -> list[str]:
        """Validate that relative markdown links in a file resolve to valid on-disk files."""
        return validate_markdown_links_in_file(file_path, content)

    def audit_slash_commands(
        self,
        file_path: Path,
        content: str | None = None,
        registered_commands: set[str] | None = None,
    ) -> list[str]:
        """Audit markdown content for unregistered slash command references."""
        if registered_commands is None:
            allowed_cmds = self.get_registered_commands()
        else:
            allowed_cmds = set(registered_commands) | set(ALLOWED_HOST_COMMANDS)
        return audit_slash_commands_in_file(file_path, content, allowed_cmds)

    def audit_skill_directory(self, skill_dir: Path) -> list[str]:
        """Audit all markdown files in a skill directory for links, slash commands, and compliance."""
        target_dir = skill_dir.parent if skill_dir.is_file() else skill_dir
        if not target_dir.exists():
            return []
        issues: list[str] = []
        registered_cmds = self.get_registered_commands()
        for md_file in sorted(target_dir.rglob("*.md")):
            if md_file.name == "SKILL.md":
                for si in self.audit_skill(md_file):
                    msg = f"{md_file}:{si.line_number}: [{si.category}] {si.message}"
                    issues.append(
                        AuditIssueString(msg, si.line_number, si.subject, si.category, si.file_path)
                    )
            issues.extend(self.validate_markdown_links(md_file))
            issues.extend(self.audit_slash_commands(md_file, registered_commands=registered_cmds))
        return issues

    def check_shallow_skill(
        self, file_path: Path, content: str | None = None
    ) -> list[SkillAuditIssue]:
        """Verify that a skill has at least SHALLOW_SKILL_MIN_LINES content lines (ADR-0040)."""
        return check_shallow_skill_content(file_path, content, yaml_module=yaml)

    def audit_skill(
        self,
        file_path: Path,
        check_shallow: bool = False,
        enforce_gpi: bool = False,
        *,
        require_scope: bool = False,
        require_posture: bool = False,
    ) -> list[SkillAuditIssue]:
        """Audit a single SKILL.md file for CCBA compliance."""
        fp = str(file_path)
        if not file_path.exists():
            return [SkillAuditIssue(1, fp, "File does not exist", "MISSING_FILE", fp)]
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            return [SkillAuditIssue(1, fp, f"Failed to read file: {exc}", "READ_ERROR", fp)]

        match, meta, fm_issues = parse_frontmatter_dict(fp, content, yaml_module=yaml)
        if fm_issues or match is None or meta is None:
            return fm_issues

        issues = validate_skill_frontmatter_metadata(
            fp,
            content,
            meta,
            self.get_valid_bundles(),
            require_scope=require_scope,
            require_posture=require_posture,
        )
        issues.extend(
            self._audit_granularity_and_gpi(
                file_path, meta.get("name"), meta, enforce_gpi, content=content
            )
        )
        fm_lines = len(match.group(0).splitlines())
        for offset, err_msg in self.analyze_steps_completion_criteria(content[match.end() :]):
            issues.append(
                SkillAuditIssue(offset + fm_lines, fp, err_msg, "MISSING_COMPLETION_CRITERIA", fp)
            )
        if check_shallow:
            issues.extend(self.check_shallow_skill(file_path, content))
        return issues

    def _audit_granularity_and_gpi(
        self,
        file_path: Path,
        name: str | None,
        meta: dict[str, Any],
        enforce_gpi: bool = False,
        content: str | None = None,
    ) -> list[SkillAuditIssue]:
        """Audit skill against Two-Stage Granularity Decision Framework (RES-2026-ARCH-001)."""
        return audit_granularity_and_gpi_impl(file_path, name, meta, enforce_gpi, content=content)

    def evaluate_skill_file(
        self,
        file_path: Path,
        override_deterministic: bool | None = None,
        override_orchestrated: bool | None = None,
        override_metrics: GPIMetrics | None = None,
        override_parent: str | None = None,
        override_existing_tier: ArchitectureTier | str | None = None,
        override_force_tier_flip: bool = False,
    ) -> DecisionResult:
        """Evaluate an existing SKILL.md file directly through the Two-Stage Decision Framework."""
        return evaluate_skill_file_decision(
            file_path,
            override_deterministic=override_deterministic,
            override_orchestrated=override_orchestrated,
            override_metrics=override_metrics,
            override_parent=override_parent,
            override_existing_tier=override_existing_tier,
            override_force_tier_flip=override_force_tier_flip,
            yaml_module=yaml,
        )

    def evaluate_two_stage_decision(self, request: DecisionRequest) -> DecisionResult:
        """Evaluate capability architecture placement using Two-Stage Decision Framework."""
        return evaluate_two_stage_decision(request)

    def calculate_gpi(self, s: float, k: float, a: float, p: float) -> float:
        """Calculate Granularity & Placement Index (GPI)."""
        return calculate_gpi(s, k, a, p)

    def analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
        """Scan workflow steps in body for Completion Criteria."""
        return _analyze_steps_completion_criteria_fn(body)

    _analyze_steps_completion_criteria = analyze_steps_completion_criteria

    def audit_workflow(self, file_path: Path) -> list[SkillAuditIssue]:
        """Audit a single workflow file for CCBA compliance."""
        return audit_workflow_file(file_path, yaml_module=yaml)

    def audit_workspace_gates(self, skills_dir: Path | None = None) -> list[SkillAuditIssue]:
        """Perform workspace-level CI Gate checks across all skills."""
        target_dir = (
            self.project_root / ".agents" / "skills"
            if skills_dir is None or skills_dir.is_file()
            else skills_dir
        )
        if not target_dir.exists():
            return []
        return audit_workspace_gates_impl(
            target_dir,
            self.project_root,
            yaml,
            self.check_shallow_skill,
            self.validate_markdown_links,
            lambda md, cmds: self.audit_slash_commands(md, registered_commands=cmds),
            self.get_registered_commands(),
        )

    def run_cli(self, args_list: list[str] | None = None) -> int:
        """Run CLI validation on target paths."""
        from .cli import run_skill_validation_cli

        return int(run_skill_validation_cli(args_list, validator=self))
