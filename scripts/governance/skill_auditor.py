"""skill_auditor.py - Sub-Auditor for CCBA Agent Skills & Workflows compliance.

Enforces:
1. Skill frontmatter validity and description length (<= 180 chars for model-invoked skills).
2. Step completion criteria ('**Tiêu chí hoàn thành:**' or '**Completion Criterion:**').
3. Zero-Duplicate Gate: No duplicate skill names across the workspace.
4. Context Budget Ceiling Gate: <= 10 model-invoked skills per bundle (ADR-0040).
5. Taxonomy & Shallow Skill Inspection.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from .base import (
    EXCLUSION_HEADERS,
    FRONTMATTER_RE,
    STEP_LINE_RE,
    WORKFLOW_HEADERS,
    AuditIssue,
    BaseAuditor,
)

MAX_MODEL_INVOKED_PER_BUNDLE = 10


class SkillAuditor(BaseAuditor):
    """Deep Sub-Auditor for Agent skills, YAML frontmatters, character limits, step completion criteria and 4-Layer CI Gates."""

    def audit_skill(self, file_path: Path) -> list[AuditIssue]:
        """Audit a single SKILL.md or workflow file for CCBA compliance."""
        issues: list[AuditIssue] = []
        if not file_path.exists():
            return [AuditIssue(1, str(file_path), "File does not exist", category="MISSING_FILE", file_path=str(file_path))]

        content = file_path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(content)
        if not match:
            return [AuditIssue(1, str(file_path), "Missing YAML frontmatter '---'", category="MALFORMED_FRONTMATTER", file_path=str(file_path))]

        try:
            meta = yaml.safe_load(match.group(1))
        except Exception as e:
            return [AuditIssue(1, str(file_path), f"Failed to parse frontmatter YAML: {e}", category="YAML_PARSE_ERROR", file_path=str(file_path))]

        if not isinstance(meta, dict):
            return [AuditIssue(1, str(file_path), "Frontmatter YAML is not a valid dictionary", category="MALFORMED_FRONTMATTER", file_path=str(file_path))]

        name = meta.get("name")
        description = meta.get("description")
        disable_model_inv = meta.get("disable-model-invocation", False)

        if not name or not isinstance(name, str):
            issues.append(AuditIssue(1, str(file_path), "Missing or invalid 'name' in frontmatter", category="MISSING_NAME", file_path=str(file_path)))
        if not description or not isinstance(description, str):
            issues.append(
                AuditIssue(1, str(file_path), "Missing or invalid 'description' in frontmatter", category="MISSING_DESCRIPTION", file_path=str(file_path))
            )

        if description and isinstance(description, str) and not disable_model_inv:
            if len(description) > 180:
                issues.append(
                    AuditIssue(
                        1,
                        str(file_path),
                        f"Description length ({len(description)}) exceeds 180 character limit for model-invoked skill",
                        category="DESCRIPTION_TOO_LONG",
                        file_path=str(file_path),
                    )
                )

        frontmatter_lines = len(match.group(0).splitlines())
        body = content[match.end() :]

        step_errors = self._analyze_steps_completion_criteria(body)
        for line_offset, err_msg in step_errors:
            abs_line = line_offset + frontmatter_lines
            issues.append(AuditIssue(abs_line, str(file_path), err_msg, category="MISSING_COMPLETION_CRITERIA", file_path=str(file_path)))

        return issues

    def _analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
        """Helper to scan workflow steps for Completion Criteria."""
        errors: list[tuple[int, str]] = []
        lines = body.splitlines()
        in_workflow_section = False
        workflow_trigger_level = None
        header_stack: list[tuple[int, str, bool]] = []
        in_code_block = False
        current_step_line = None
        current_step_num = None
        current_step_content: list[str] = []

        for idx, line in enumerate(lines):
            line_strip = line.strip()
            if line_strip.startswith("```"):
                in_code_block = not in_code_block
                if current_step_line is not None:
                    current_step_content.append(line)
                continue

            if in_code_block:
                if current_step_line is not None:
                    current_step_content.append(line)
                continue

            if line_strip.startswith("#"):
                if current_step_line is not None:
                    step_body = "\n".join(current_step_content)
                    if not (
                        "**Completion Criterion:**" in step_body
                        or "**Tiêu chí hoàn thành:**" in step_body
                    ):
                        errors.append(
                            (
                                current_step_line,
                                f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                            )
                        )
                    current_step_line = None
                    current_step_num = None
                    current_step_content = []

                level = len(line_strip) - len(line_strip.lstrip("#"))
                header_text = line_strip.lstrip("#").strip().lower()

                while header_stack and header_stack[-1][0] >= level:
                    header_stack.pop()

                is_exclusion = any(kw in header_text for kw in EXCLUSION_HEADERS)
                is_workflow_keyword = any(kw in header_text for kw in WORKFLOW_HEADERS)

                if is_workflow_keyword and not is_exclusion:
                    is_workflow = True
                elif is_exclusion:
                    is_workflow = False
                else:
                    is_workflow = header_stack[-1][2] if header_stack else False

                header_stack.append((level, header_text, is_workflow))
                in_workflow_section = is_workflow
                if in_workflow_section:
                    if workflow_trigger_level is None:
                        workflow_trigger_level = level
                else:
                    workflow_trigger_level = None
                continue

            if not in_workflow_section:
                continue

            current_level = header_stack[-1][0] if header_stack else 0
            if current_level != workflow_trigger_level:
                continue

            step_match = STEP_LINE_RE.match(line)
            if step_match:
                if current_step_line is not None:
                    step_body = "\n".join(current_step_content)
                    if not (
                        "**Completion Criterion:**" in step_body
                        or "**Tiêu chí hoàn thành:**" in step_body
                    ):
                        errors.append(
                            (
                                current_step_line,
                                f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                            )
                        )

                current_step_line = idx + 1
                current_step_num = step_match.group(1)
                current_step_content = [line]
            elif current_step_line is not None:
                current_step_content.append(line)

        if current_step_line is not None:
            step_body = "\n".join(current_step_content)
            if not (
                "**Completion Criterion:**" in step_body or "**Tiêu chí hoàn thành:**" in step_body
            ):
                errors.append(
                    (
                        current_step_line,
                        f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                    )
                )

        return errors

    def audit_workspace_gates(self, skills_dir: Path | None = None) -> list[AuditIssue]:
        """Perform workspace-level Hard CI Gate checks across all skills."""
        issues: list[AuditIssue] = []
        if skills_dir is None:
            skills_dir = self.project_root / ".agents" / "skills"

        if not skills_dir.exists():
            return issues

        skill_files = list(skills_dir.rglob("SKILL.md"))
        seen_names: dict[str, list[Path]] = defaultdict(list)
        bundle_model_invoked_counts: dict[str, int] = defaultdict(int)

        for sf in skill_files:
            try:
                content = sf.read_text(encoding="utf-8")
                match = FRONTMATTER_RE.match(content)
                if match:
                    meta = yaml.safe_load(match.group(1))
                    if isinstance(meta, dict):
                        name = meta.get("name")
                        if name:
                            seen_names[str(name).strip().lower()].append(sf)

                        disable_model_inv = meta.get("disable-model-invocation", False)
                        bundle = meta.get("bundle") or meta.get("layer") or "_default"
                        if not disable_model_inv:
                            bundle_model_invoked_counts[str(bundle)] += 1
            except Exception:
                pass

        # 1. Zero-Duplicate Gate
        for skill_name, paths in seen_names.items():
            if len(paths) > 1:
                rel_paths = [str(p.relative_to(self.project_root) if p.is_relative_to(self.project_root) else p) for p in paths]
                issues.append(
                    AuditIssue(
                        1,
                        skill_name,
                        f"Duplicate skill name '{skill_name}' found across multiple locations: {', '.join(rel_paths)}",
                        category="ZERO_DUPLICATE_GATE_VIOLATION",
                        file_path=str(paths[0]),
                    )
                )

        # 2. Context Budget Ceiling Gate (<= 10 model_invoked per bundle)
        for bundle, count in bundle_model_invoked_counts.items():
            if count > MAX_MODEL_INVOKED_PER_BUNDLE:
                issues.append(
                    AuditIssue(
                        1,
                        bundle,
                        f"Context Budget Ceiling Exceeded: Bundle '{bundle}' has {count} model-invoked skills (Max allowed: {MAX_MODEL_INVOKED_PER_BUNDLE}). Convert ritual workflows to 'disable-model-invocation: true' per ADR-0040.",
                        category="CONTEXT_BUDGET_CEILING_EXCEEDED",
                        file_path=str(skills_dir),
                    )
                )

        return issues

    def audit_workspace(self) -> dict[str, Any]:
        """Audit all skills in the workspace."""
        skill_issues: list[AuditIssue] = []
        skills_dir = self.project_root / ".agents" / "skills"

        if skills_dir.exists():
            for skill_path in skills_dir.rglob("SKILL.md"):
                skill_issues.extend(self.audit_skill(skill_path))
            skill_issues.extend(self.audit_workspace_gates(skills_dir))

        return {
            "skills": skill_issues,
            "total_skill_issues": len(skill_issues),
        }

    def audit(self, target: Path) -> list[AuditIssue]:
        """Polymorphic entry point for auditing a skill or skills directory."""
        if target.is_file():
            return self.audit_skill(target)
        skill_issues: list[AuditIssue] = []
        for skill_path in target.rglob("SKILL.md"):
            skill_issues.extend(self.audit_skill(skill_path))
        skill_issues.extend(self.audit_workspace_gates(target))
        return skill_issues
