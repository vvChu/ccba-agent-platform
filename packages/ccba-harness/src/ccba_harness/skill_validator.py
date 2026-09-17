"""skill_validator.py - Standalone Quality & Compliance Validator for CCBA Skills.

Enforces:
1. Frontmatter validity, YAML schema, and description limits (<= 180 chars for model-invoked skills).
2. Bundle taxonomy validation and namespace governance (ccba-, bigbim-, platform-loader).
3. Slash command contract (user-invocable: true requires command: /... per ADR-0056).
4. Step completion criteria ('**Tiêu chí hoàn thành:**' or '**Completion Criterion:**').
5. Shallow Skill Warning Gate (< 35 non-empty content lines per ADR-0040).
6. Workspace Gates: Zero-Duplicate Gate and Context Budget Ceiling Gate (<= 10 model-invoked skills/bundle).

This module is completely decoupled from the Hub codebase, allowing offline and
air-gapped Spoke installations to validate skills independently.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, NamedTuple

from .gpi import (
    GPI_STANDALONE_THRESHOLD,
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
    yaml = None  # type: ignore[assignment]

# Core Regular Expressions
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
STEP_LINE_RE = re.compile(
    r"^\s*(?:([0-9]+)\.\s+(.*)|#{1,6}\s+(?:[^\w\s]*\s*)?(?:bước|step|phase|pha|giai đoạn)\s*([0-9]+(?:\.[0-9]+)*|[ivxlcdm]+)(?:[:.\-—\s]+(.*)|$))",
    re.IGNORECASE,
)

WORKFLOW_HEADERS: set[str] = {
    "workflow",
    "quy trình",
    "các bước",
    "steps",
    "hành động",
    "chuyển đổi",
    "tiến hành",
    "thực hiện",
}

EXCLUSION_HEADERS: set[str] = {
    "lưu ý",
    "chú ý",
    "notes",
    "yêu cầu",
    "rules",
    "quy tắc",
    "tham chiếu",
    "reference",
    "giới thiệu",
    "introduction",
    "tổng quan",
    "overview",
    "chuẩn bị",
    "setup",
    "tiêu chí hoàn thành",
    "completion criteria",
    "definition of done",
}

DEFAULT_VALID_BUNDLES: set[str] = {
    "_core",
    "_software",
    "_qc",
    "_consulting",
    "_bim",
    "_governance",
}

SHALLOW_SKILL_MIN_LINES = 35
MAX_MODEL_INVOKED_PER_BUNDLE = 10

COMMON_PATH_SEGMENTS: set[str] = {
    "bin",
    "usr",
    "etc",
    "dev",
    "tmp",
    "var",
    "proc",
    "sys",
    "mnt",
    "opt",
    "src",
    "packages",
    "scripts",
    "tests",
    "docs",
    "references",
    "templates",
    "standards",
    "examples",
    "appendices",
    "output",
    "scratch",
    "legal_docs",
    "sources",
    "lib",
    "build",
    "dist",
    "node_modules",
    "artifacts",
}

ALLOWED_HOST_COMMANDS: set[str] = {
    "/boost",
    "/skill-repair",
    "/clear",
    "/compact",
    "/init",
    "/ui-ux-pro-max",
    "/ship",
}

GITLAB_QUICK_ACTIONS: set[str] = {
    "/blocked_by",
    "/close",
    "/reopen",
    "/assign",
    "/milestone",
    "/label",
    "/cc",
}


LINK_EXTRACT_RE = re.compile(r"\[.*?\]\(([^)]+)\)")
SLASH_CMD_RE = re.compile(r"(?<![a-zA-Z0-9_./\\<])(/([a-z][a-z0-9_\-]*))(?![a-zA-Z0-9_./\\-])")


def is_exclusion_header(header_text: str) -> bool:
    """Check if header is an exclusion header, ignoring step execution headers."""
    if re.search(
        r"(?:bước|step|phase|pha|giai đoạn)\s*(?:[0-9]+(?:\.[0-9]+)*|[ivxlcdm]+)",
        header_text,
        re.IGNORECASE,
    ):
        return False
    return any(kw in header_text.lower() for kw in EXCLUSION_HEADERS)


class SkillAuditIssue(NamedTuple):
    """Container for a single skill or workflow audit issue."""

    line_number: int
    subject: str
    message: str
    category: str = ""
    file_path: str = ""


class AuditIssueString(str):
    """String subclass representing an audit issue with structured metadata."""

    line_number: int
    subject: str
    message: str
    category: str
    file_path: str

    def __new__(
        cls,
        message: str,
        line_number: int = 1,
        subject: str = "",
        category: str = "",
        file_path: str = "",
    ) -> AuditIssueString:
        obj = super().__new__(cls, message)
        obj.line_number = line_number
        obj.subject = subject
        obj.message = message
        obj.category = category
        obj.file_path = file_path
        return obj

    def to_audit_issue(self) -> SkillAuditIssue:
        """Convert to SkillAuditIssue NamedTuple."""
        return SkillAuditIssue(
            line_number=self.line_number,
            subject=self.subject,
            message=self.message,
            category=self.category,
            file_path=self.file_path,
        )


class SkillValidator:
    """Standalone validator for CCBA skills, workflows, and workspace gates."""

    def __init__(
        self,
        project_root: Path | None = None,
        valid_bundles: set[str] | None = None,
    ) -> None:
        if project_root is None:
            self.project_root = Path.cwd()
        else:
            self.project_root = Path(project_root).resolve()
        self._custom_valid_bundles = valid_bundles
        self._cached_valid_bundles: set[str] | None = None

    def get_valid_bundles(self) -> set[str]:
        """Load valid bundles from catalog.yaml, custom set, or fallback taxonomy."""
        if self._custom_valid_bundles is not None:
            return set(self._custom_valid_bundles)

        if self._cached_valid_bundles is not None:
            return self._cached_valid_bundles

        valid: set[str] = set(DEFAULT_VALID_BUNDLES)
        catalog_candidates = [
            self.project_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml",
            self.project_root / "catalog.yaml",
            self.project_root / ".agents" / "catalog.yaml",
        ]

        for catalog_path in catalog_candidates:
            if catalog_path.exists() and yaml is not None:
                try:
                    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
                    bundles_map = data.get("bundles", {})
                    if isinstance(bundles_map, dict):
                        for b_list in bundles_map.values():
                            if isinstance(b_list, list):
                                for b in b_list:
                                    valid.add(str(b))
                    notebook_ids = data.get("notebook_ids", {})
                    if isinstance(notebook_ids, dict):
                        for nb_key in notebook_ids.keys():
                            valid.add(str(nb_key))
                    break
                except Exception:
                    pass

        self._cached_valid_bundles = valid
        return self._cached_valid_bundles

    def get_registered_commands(self) -> set[str]:
        """Retrieve all canonical registered slash commands from catalog.yaml, including aliases and host commands."""
        catalog_candidates = [
            self.project_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml",
            self.project_root / "catalog.yaml",
            self.project_root / ".agents" / "catalog.yaml",
        ]
        commands: set[str] = set()
        for cat_path in catalog_candidates:
            if cat_path.exists() and yaml is not None:
                try:
                    data = yaml.safe_load(cat_path.read_text(encoding="utf-8")) or {}
                    for item in data.get("skills", []):
                        if isinstance(item, dict) and item.get("command"):
                            cmd = str(item["command"]).strip()
                            commands.add(cmd)
                            if cmd.startswith("/ccba-"):
                                commands.add("/" + cmd[6:])
                            elif cmd.startswith("/bigbim-"):
                                commands.add("/" + cmd[8:])
                    for item in data.get("workflows", []):
                        if isinstance(item, dict) and item.get("command"):
                            commands.add(str(item["command"]).strip())
                    break
                except Exception:
                    pass

        commands.update(ALLOWED_HOST_COMMANDS)
        commands.update(GITLAB_QUICK_ACTIONS)
        return commands

    def validate_markdown_links(self, file_path: Path, content: str | None = None) -> list[str]:
        """Validate that relative markdown links in a file resolve to valid on-disk files."""
        issues: list[str] = []
        if content is None:
            if not file_path.exists():
                return issues
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                return [
                    AuditIssueString(
                        f"{file_path}:1: Failed to read file: {e}",
                        line_number=1,
                        subject=str(file_path),
                        category="READ_ERROR",
                        file_path=str(file_path),
                    )
                ]

        lines = content.splitlines()
        in_code_block = False

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Strip inline code spans
            line_no_code = re.sub(r"`[^`]+`", "", line)

            for target in LINK_EXTRACT_RE.findall(line_no_code):
                target = target.strip()
                # Ignore external URL schemes, anchors, or variable/wildcard placeholders
                if target.startswith(
                    (
                        "http://",
                        "https://",
                        "mailto:",
                        "conversation:",
                        "file://",
                        "#",
                    )
                ) or any(char in target for char in ("<", ">", "{", "}", "*", "...", "[")):
                    continue

                # Strip anchor fragment
                clean_target = target.split("#")[0].strip()
                if not clean_target:
                    continue

                resolved_path = (file_path.parent / clean_target).resolve()
                if not resolved_path.exists():
                    msg = (
                        f"{file_path}:{idx}: Broken relative link '{target}' "
                        f"(resolved to '{resolved_path}' which does not exist)."
                    )
                    issues.append(
                        AuditIssueString(
                            msg,
                            line_number=idx,
                            subject=target,
                            category="BROKEN_MARKDOWN_LINK",
                            file_path=str(file_path),
                        )
                    )

        return issues

    def audit_slash_commands(
        self,
        file_path: Path,
        content: str | None = None,
        registered_commands: set[str] | None = None,
    ) -> list[str]:
        """Audit markdown content for unregistered slash command references."""
        issues: list[str] = []
        if registered_commands is None:
            allowed_cmds = self.get_registered_commands()
        else:
            allowed_cmds = set(registered_commands)
            allowed_cmds.update(ALLOWED_HOST_COMMANDS)
        if not allowed_cmds:
            return issues

        if content is None:
            if not file_path.exists():
                return issues
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return issues

        lines = content.splitlines()
        in_code_block = False

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Strip full URLs
            clean_line = re.sub(r"https?://[^\s)]+", "", line)
            # Strip HTML/XML closing tags
            clean_line = re.sub(r"</[a-zA-Z0-9_\-:]+>", "", clean_line)
            # Strip markdown link targets [text](target)
            clean_line = re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", clean_line)
            # Strip colon commands like /ck:ship, /ckm:brand
            clean_line = re.sub(r"/[a-z0-9_\-]+:[a-z0-9_\-]+", "", clean_line)
            # Strip generic placeholders like /<cmd>, /<name>, /{cmd}
            clean_line = re.sub(r"/[<{][^>}]*[>}]", "", clean_line)
            clean_line = re.sub(r"/ccba-[<{][^>}]*[>}]", "", clean_line)

            for m in SLASH_CMD_RE.finditer(clean_line):
                full_cmd = m.group(1)
                base = m.group(2)
                start = m.start(1)

                # Vietnamese compound word separated by slash (e.g. ngữ/khái, chuẩn/quy)
                if start > 0 and clean_line[start - 1].isalpha():
                    continue
                # Common filesystem directory names or single-letter flags
                if base in COMMON_PATH_SEGMENTS or len(base) <= 1:
                    continue
                # Part of filename with extension or path (e.g. /research-[slug].md, /main.py)
                remainder = clean_line[m.start(1) + 1 :].split()[0]
                if any(
                    ext in remainder
                    for ext in (
                        ".md",
                        ".py",
                        ".json",
                        ".yaml",
                        ".yml",
                        ".txt",
                        ".docx",
                        ".pdf",
                        ".png",
                        ".jpg",
                        ".ts",
                        ".js",
                    )
                ):
                    continue
                # Generic placeholders
                if full_cmd in {
                    "/<cmd>",
                    "/<name>",
                    "/<command>",
                    "/<skill-name>",
                    "/<canonical-name>",
                    "/ccba-",
                }:
                    continue

                if full_cmd not in allowed_cmds:
                    msg = (
                        f"{file_path}:{idx}: Unregistered slash command '{full_cmd}' referenced in document. "
                        f"Must be a registered command in catalog.yaml (or replace with canonical command)."
                    )
                    issues.append(
                        AuditIssueString(
                            msg,
                            line_number=idx,
                            subject=full_cmd,
                            category="UNREGISTERED_SLASH_COMMAND",
                            file_path=str(file_path),
                        )
                    )

        return issues

    def audit_skill_directory(self, skill_dir: Path) -> list[str]:
        """Audit all markdown files in a skill directory for links, slash commands, and compliance."""
        issues: list[str] = []
        if skill_dir.is_file():
            skill_dir = skill_dir.parent

        if not skill_dir.exists():
            return issues

        registered_cmds = self.get_registered_commands()
        md_files = sorted(skill_dir.rglob("*.md"))

        for md_file in md_files:
            if md_file.name == "SKILL.md":
                skill_issues = self.audit_skill(md_file)
                for si in skill_issues:
                    msg = f"{md_file}:{si.line_number}: [{si.category}] {si.message}"
                    issues.append(
                        AuditIssueString(
                            msg,
                            line_number=si.line_number,
                            subject=si.subject,
                            category=si.category,
                            file_path=si.file_path,
                        )
                    )

            issues.extend(self.validate_markdown_links(md_file))
            issues.extend(self.audit_slash_commands(md_file, registered_commands=registered_cmds))

        return issues

    def check_shallow_skill(
        self, file_path: Path, content: str | None = None
    ) -> list[SkillAuditIssue]:
        """Verify that a skill has at least SHALLOW_SKILL_MIN_LINES content lines (ADR-0040)."""
        issues: list[SkillAuditIssue] = []
        if content is None:
            if not file_path.exists():
                return issues
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                return issues

        non_empty_lines = [line for line in content.splitlines() if line.strip()]
        line_count = len(non_empty_lines)

        if line_count < SHALLOW_SKILL_MIN_LINES:
            skill_name = file_path.parent.name
            match = FRONTMATTER_RE.match(content)
            if match and yaml is not None:
                try:
                    meta = yaml.safe_load(match.group(1))
                    if isinstance(meta, dict) and meta.get("name"):
                        skill_name = str(meta["name"])
                except Exception:
                    pass

            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Skill '{skill_name}' is too shallow ({line_count} content lines < "
                    f"{SHALLOW_SKILL_MIN_LINES} lines minimum per ADR-0040). "
                    f"Provide detailed workflow instructions and complete step criteria.",
                    category="SHALLOW_SKILL_WARNING",
                    file_path=str(file_path),
                )
            )

        return issues

    def audit_skill(
        self,
        file_path: Path,
        check_shallow: bool = False,
        enforce_gpi: bool = False,
    ) -> list[SkillAuditIssue]:
        """Audit a single SKILL.md file for CCBA compliance."""
        issues: list[SkillAuditIssue] = []
        if not file_path.exists():
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "File does not exist",
                    category="MISSING_FILE",
                    file_path=str(file_path),
                )
            ]

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Failed to read file: {e}",
                    category="READ_ERROR",
                    file_path=str(file_path),
                )
            ]

        match = FRONTMATTER_RE.match(content)
        if not match:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Missing YAML frontmatter '---'",
                    category="MALFORMED_FRONTMATTER",
                    file_path=str(file_path),
                )
            ]

        if yaml is None:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "PyYAML package is required to parse skill frontmatter. Run: pip install pyyaml",
                    category="YAML_PACKAGE_MISSING",
                    file_path=str(file_path),
                )
            ]

        try:
            meta = yaml.safe_load(match.group(1))
        except Exception as e:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Failed to parse frontmatter YAML: {e}",
                    category="YAML_PARSE_ERROR",
                    file_path=str(file_path),
                )
            ]

        if not isinstance(meta, dict):
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Frontmatter YAML is not a valid dictionary",
                    category="MALFORMED_FRONTMATTER",
                    file_path=str(file_path),
                )
            ]

        name = meta.get("name")
        description = meta.get("description")
        disable_model_inv = meta.get("disable-model-invocation", False)
        if isinstance(disable_model_inv, str):
            disable_model_inv = disable_model_inv.lower() in ("true", "1", "yes")

        # Name validation
        if not name or not isinstance(name, str):
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Missing or invalid 'name' in frontmatter",
                    category="MISSING_NAME",
                    file_path=str(file_path),
                )
            )
        else:
            is_valid_namespace = name.startswith(("ccba-", "bigbim-")) or name == "platform-loader"
            if not is_valid_namespace:
                issues.append(
                    SkillAuditIssue(
                        1,
                        str(file_path),
                        f"Skill name '{name}' violates ADR-0056 namespace rules. "
                        f"Must start with 'ccba-' (or 'bigbim-', or exactly 'platform-loader')",
                        category="INVALID_NAMESPACE",
                        file_path=str(file_path),
                    )
                )

        # Description validation
        if not description or not isinstance(description, str):
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Missing or invalid 'description' in frontmatter",
                    category="MISSING_DESCRIPTION",
                    file_path=str(file_path),
                )
            )
        elif not disable_model_inv:
            if len(description) > 180:
                issues.append(
                    SkillAuditIssue(
                        1,
                        str(file_path),
                        f"Description length ({len(description)}) exceeds 180 character limit "
                        f"for model-invoked skill",
                        category="DESCRIPTION_TOO_LONG",
                        file_path=str(file_path),
                    )
                )

        # Bundle field validation (ADR-0041, ADR-0044)
        bundle = meta.get("bundle")
        if not bundle or not isinstance(bundle, str):
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Skill is missing required 'bundle' field in frontmatter",
                    category="MISSING_BUNDLE_FIELD",
                    file_path=str(file_path),
                )
            )
        else:
            valid_bundles = self.get_valid_bundles()
            if bundle not in valid_bundles:
                issues.append(
                    SkillAuditIssue(
                        1,
                        str(file_path),
                        f"Skill bundle '{bundle}' is invalid. Must be one of: {sorted(valid_bundles)}",
                        category="INVALID_BUNDLE_FIELD",
                        file_path=str(file_path),
                    )
                )

        # Slash Command validation (ADR-0056)
        user_invocable = meta.get("user-invocable", False)
        if isinstance(user_invocable, str):
            user_invocable = user_invocable.lower() in ("true", "1", "yes")
        command = meta.get("command")

        if user_invocable:
            expected_cmd = f"/{name}" if name else ""
            if not command:
                issues.append(
                    SkillAuditIssue(
                        1,
                        str(file_path),
                        f"Skill '{name}' has 'user-invocable: true' but is missing "
                        f"'command: {expected_cmd}' in frontmatter (ADR-0056 Slash Command contract)",
                        category="MISSING_COMMAND_FIELD",
                        file_path=str(file_path),
                    )
                )
            elif name:
                cmd_base = str(command).strip().split()[0]
                allowed_prefixes = (
                    f"/{name}",
                    f"/{name.replace('ccba-', '')}",
                    f"/workflow_{name.replace('ccba-', '').replace('-', '_')}",
                )
                if not any(cmd_base == prefix for prefix in allowed_prefixes):
                    issues.append(
                        SkillAuditIssue(
                            1,
                            str(file_path),
                            f"Skill '{name}' command '{command}' does not match "
                            f"expected Slash Command name '{expected_cmd}'",
                            category="INVALID_COMMAND_FIELD",
                            file_path=str(file_path),
                        )
                    )
        elif command and name:
            cmd_base = str(command).strip().split()[0]
            expected_cmd = f"/{name}"
            allowed_prefixes = (
                f"/{name}",
                f"/{name.replace('ccba-', '')}",
                f"/workflow_{name.replace('ccba-', '').replace('-', '_')}",
            )
            if not any(cmd_base == prefix for prefix in allowed_prefixes):
                issues.append(
                    SkillAuditIssue(
                        1,
                        str(file_path),
                        f"Skill '{name}' command '{command}' does not match "
                        f"expected Slash Command name '{expected_cmd}'",
                        category="INVALID_COMMAND_FIELD",
                        file_path=str(file_path),
                    )
                )

        # Stage 1 and Stage 2: Two-Stage Granularity Decision & GPI validation
        issues.extend(self._audit_granularity_and_gpi(file_path, name, meta, enforce_gpi))

        # Step completion criteria validation
        frontmatter_lines = len(match.group(0).splitlines())
        body = content[match.end() :]

        step_errors = self.analyze_steps_completion_criteria(body)
        for line_offset, err_msg in step_errors:
            abs_line = line_offset + frontmatter_lines
            issues.append(
                SkillAuditIssue(
                    abs_line,
                    str(file_path),
                    err_msg,
                    category="MISSING_COMPLETION_CRITERIA",
                    file_path=str(file_path),
                )
            )

        # Shallow Skill Check (Gate 4 per ADR-0040)
        if check_shallow:
            issues.extend(self.check_shallow_skill(file_path, content))

        return issues

    def _audit_granularity_and_gpi(
        self,
        file_path: Path,
        name: str | None,
        meta: dict[str, Any],
        enforce_gpi: bool = False,
    ) -> list[SkillAuditIssue]:
        """Audit skill against Two-Stage Granularity Decision Framework (RES-2026-ARCH-001)."""
        issues: list[SkillAuditIssue] = []
        skill_name = name or file_path.parent.name

        # Gate 0: Determinism Gate
        is_deterministic = meta.get(
            "is-deterministic",
            meta.get("is_deterministic", meta.get("deterministic", False)),
        )
        if isinstance(is_deterministic, str):
            is_deterministic = is_deterministic.lower() in ("true", "1", "yes")
        if is_deterministic:
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Skill '{skill_name}' violates Gate 0 (Determinism Gate): task can be solved 100% "
                    f"deterministically (regex, AST parse, math, file I/O) and must be implemented as "
                    f"Tier 1 (Package Function / Deep Seam in packages/*), not a standalone skill.",
                    category="DETERMINISM_GATE_VIOLATION",
                    file_path=str(file_path),
                )
            )

        # Gate 1: Orchestration Gate
        tier_val = str(meta.get("tier", "")).lower()
        is_tier3_orchestrator = tier_val in (
            "orchestrator",
            "composite-orchestrator",
            "tier 3",
            "tier-3",
        )

        is_orchestrated = meta.get(
            "is-orchestrated",
            meta.get("is_orchestrated", meta.get("orchestrated", False)),
        )
        if isinstance(is_orchestrated, str):
            is_orchestrated = is_orchestrated.lower() in ("true", "1", "yes")

        if is_tier3_orchestrator:
            is_orchestrated = True

        if is_orchestrated and not is_tier3_orchestrator:
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Skill '{skill_name}' violates Gate 1 (Orchestration Gate): task coordinates "
                    f"multiple agents, StateGraph checkpoints, or requires HITL approval, "
                    f"and must be implemented as Tier 3 (Composite Orchestrator) with 'tier: orchestrator'.",
                    category="ORCHESTRATION_GATE_VIOLATION",
                    file_path=str(file_path),
                )
            )
        elif is_tier3_orchestrator:
            # Valid Tier 3 Composite Orchestrator
            # Orchestrators bypass Stage 2 GPI calculation (RES-2026-ARCH-001 Section 6.2).
            # Verify Single-Writer Protocol if multi-agent workflow
            raw_content = file_path.read_text(encoding="utf-8").lower()
            coordinates_subagents = any(
                k in raw_content
                for k in (
                    "dispatch worker",
                    "phân công worker",
                    "worker subagent",
                    "team_sheet",
                    "spawn subagent",
                    "giao cho subagent",
                    "workers thực thi",
                )
            )
            if coordinates_subagents:
                has_single_writer = any(
                    k in raw_content
                    for k in (
                        "single-writer",
                        "single writer",
                        "read-only",
                        "read only",
                        "duy nhất orchestrator",
                        "duy nhất có quyền ghi",
                        "scratch",
                    )
                )
                if not has_single_writer:
                    issues.append(
                        SkillAuditIssue(
                            1,
                            str(file_path),
                            f"Tier 3 Orchestrator '{skill_name}' coordinates workers/subagents but lacks "
                            "Single-Writer Protocol (ADR-0053) specification (exclusive writer or read-only workers).",
                            category="SINGLE_WRITER_PROTOCOL_VIOLATION",
                            file_path=str(file_path),
                        )
                    )

        # Stage 2: Granularity & Placement Index (GPI)
        # Stage 2 is only evaluated if Stage 1 invariant gates (Gate 0 and Gate 1) are traversed.
        if is_deterministic or is_orchestrated:
            return issues

        gpi_data = meta.get("gpi") or meta.get("GPI")
        if gpi_data is not None:
            if not isinstance(gpi_data, dict):
                issues.append(
                    SkillAuditIssue(
                        1,
                        str(file_path),
                        "Frontmatter 'gpi' field must be a dictionary containing s, k, a, p metrics.",
                        category="INVALID_GPI_METRICS",
                        file_path=str(file_path),
                    )
                )
            else:
                normalized_gpi = {str(k).lower(): v for k, v in gpi_data.items()}
                missing_keys = [k for k in ("s", "k", "a", "p") if k not in normalized_gpi]
                if missing_keys:
                    issues.append(
                        SkillAuditIssue(
                            1,
                            str(file_path),
                            f"Frontmatter 'gpi' is missing required metric keys: {missing_keys}",
                            category="INVALID_GPI_METRICS",
                            file_path=str(file_path),
                        )
                    )
                else:
                    try:
                        # Reject explicit booleans
                        for m_key in ("s", "k", "a", "p"):
                            raw_val = normalized_gpi[m_key]
                            if isinstance(raw_val, bool):
                                raise TypeError(
                                    f"Metric '{m_key}' must be numeric (int or float), got bool"
                                )

                        metrics = GPIMetrics(
                            s=float(normalized_gpi["s"]),
                            k=float(normalized_gpi["k"]),
                            a=float(normalized_gpi["a"]),
                            p=float(normalized_gpi["p"]),
                        )
                        parent_skill = meta.get("parent-skill", meta.get("parent_skill"))
                        req = DecisionRequest(
                            name=skill_name,
                            is_deterministic=False,
                            is_orchestrated=False,
                            gpi_metrics=metrics,
                            parent_skill=parent_skill,
                        )
                        decision = evaluate_two_stage_decision(req)
                        if (
                            enforce_gpi
                            and decision.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
                        ):
                            score = decision.gpi_score or 0.0
                            issues.append(
                                SkillAuditIssue(
                                    1,
                                    str(file_path),
                                    f"Skill '{skill_name}' has GPI {score:.2f} < {GPI_STANDALONE_THRESHOLD} "
                                    f"minimum threshold for Standalone Kernel Skill (Tier 2B). "
                                    f"Must be placed in references/*.md of owning Master Skill as Tier 2A.",
                                    category="INSUFFICIENT_GPI_SCORE",
                                    file_path=str(file_path),
                                )
                            )
                    except (TypeError, ValueError) as err:
                        issues.append(
                            SkillAuditIssue(
                                1,
                                str(file_path),
                                f"Invalid GPI metric values in frontmatter: {err}",
                                category="INVALID_GPI_METRICS",
                                file_path=str(file_path),
                            )
                        )
        elif enforce_gpi:
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Skill '{skill_name}' is missing required 'gpi' metrics block under strict GPI enforcement.",
                    category="MISSING_GPI_METRICS",
                    file_path=str(file_path),
                )
            )

        return issues

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
        """Evaluate an existing SKILL.md file directly through the Two-Stage Decision Framework.

        Args:
            file_path: Path to the SKILL.md file.
            override_deterministic: Optional override for Gate 0.
            override_orchestrated: Optional override for Gate 1.
            override_metrics: Optional fallback/override GPIMetrics if not in frontmatter.
            override_parent: Optional fallback/override parent skill name.
            override_existing_tier: Optional override for prior architecture tier (Hysteresis).
            override_force_tier_flip: Force tier transition within hysteresis deadband.

        Returns:
            DecisionResult: Architectural tier, target location, and rationale.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If YAML frontmatter is missing or invalid.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Skill file does not exist: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(content)
        if not match:
            raise ValueError(f"File '{file_path}' has no valid YAML frontmatter '---'")

        if yaml is None:
            raise RuntimeError("PyYAML package is required to parse skill frontmatter.")

        meta = yaml.safe_load(match.group(1))
        if not isinstance(meta, dict):
            raise ValueError(f"Frontmatter in '{file_path}' is not a valid dictionary.")

        skill_name = str(meta.get("name") or file_path.parent.name)

        is_deterministic = meta.get(
            "is-deterministic",
            meta.get("is_deterministic", meta.get("deterministic", False)),
        )
        if isinstance(is_deterministic, str):
            is_deterministic = is_deterministic.lower() in ("true", "1", "yes")
        if override_deterministic is not None:
            is_deterministic = override_deterministic

        tier_val = str(meta.get("tier", "")).lower()
        is_tier3_orchestrator = tier_val in (
            "orchestrator",
            "composite-orchestrator",
            "tier 3",
            "tier-3",
        )

        is_orchestrated = meta.get(
            "is-orchestrated",
            meta.get("is_orchestrated", meta.get("orchestrated", False)),
        )
        if isinstance(is_orchestrated, str):
            is_orchestrated = is_orchestrated.lower() in ("true", "1", "yes")
        if is_tier3_orchestrator:
            is_orchestrated = True
        if override_orchestrated is not None:
            is_orchestrated = override_orchestrated

        parent_skill = override_parent or meta.get("parent-skill", meta.get("parent_skill"))

        gpi_data = meta.get("gpi") or meta.get("GPI")
        metrics: GPIMetrics | None = None
        if gpi_data and isinstance(gpi_data, dict):
            normalized_gpi = {str(k).lower(): v for k, v in gpi_data.items()}
            if all(k in normalized_gpi for k in ("s", "k", "a", "p")):
                metrics = GPIMetrics(
                    s=float(normalized_gpi["s"]),
                    k=float(normalized_gpi["k"]),
                    a=float(normalized_gpi["a"]),
                    p=float(normalized_gpi["p"]),
                )
        if metrics is None and override_metrics is not None:
            metrics = override_metrics

        existing_tier = (
            override_existing_tier or meta.get("existing-tier") or meta.get("existing_tier")
        )

        request = DecisionRequest(
            name=skill_name,
            is_deterministic=bool(is_deterministic),
            is_orchestrated=bool(is_orchestrated),
            gpi_metrics=metrics,
            parent_skill=parent_skill,
            existing_tier=existing_tier,
            force_tier_flip=override_force_tier_flip,
            metadata={"file_path": str(file_path)},
        )
        return evaluate_two_stage_decision(request)

    def evaluate_two_stage_decision(self, request: DecisionRequest) -> DecisionResult:
        """Evaluate capability architecture placement using Two-Stage Decision Framework."""
        return evaluate_two_stage_decision(request)

    def calculate_gpi(self, s: float, k: float, a: float, p: float) -> float:
        """Calculate Granularity & Placement Index (GPI)."""
        return calculate_gpi(s, k, a, p)

    def analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
        """Scan workflow steps in body for Completion Criteria."""
        errors: list[tuple[int, str]] = []
        lines = body.splitlines()

        header_stack: list[tuple[int, str, bool]] = []
        in_workflow_section = False
        workflow_trigger_level = None
        in_code_block = False
        current_step_line = None
        current_step_num = None
        current_step_content: list[str] = []
        in_heading_step = False
        step_level = None

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

            if not line_strip:
                if current_step_line is not None:
                    current_step_content.append(line)
                continue

            if line_strip.startswith("#"):
                level = len(line_strip) - len(line_strip.lstrip("#"))
                header_text = line_strip.lstrip("#").strip().lower()

                step_match = STEP_LINE_RE.match(line)
                is_step_header = bool(step_match)
                is_exclusion = is_exclusion_header(header_text)
                is_workflow_keyword = any(kw in header_text for kw in WORKFLOW_HEADERS)

                # If inside a heading step and this is a sub-heading (deeper level) that is neither a step nor exclusion
                if (
                    in_heading_step
                    and step_level is not None
                    and level > step_level
                    and not is_step_header
                ):
                    if current_step_line is not None:
                        current_step_content.append(line)
                    continue

                if current_step_line is not None:
                    step_body = "\n".join(current_step_content)
                    if not (
                        "**Completion Criterion:**" in step_body
                        or "**Tiêu chí hoàn thành:**" in step_body
                    ):
                        errors.append(
                            (
                                current_step_line,
                                f"Step {current_step_num} is missing a Completion Criterion "
                                f"('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                            )
                        )
                    current_step_line = None
                    current_step_num = None
                    current_step_content = []
                    in_heading_step = False
                    step_level = None

                while header_stack and header_stack[-1][0] >= level:
                    header_stack.pop()

                in_exclusion_ancestor = any(is_exclusion_header(h[1]) for h in header_stack)

                if is_workflow_keyword and not is_exclusion and not in_exclusion_ancestor:
                    is_workflow = True
                elif is_step_header and not is_exclusion and not in_exclusion_ancestor:
                    is_workflow = True
                elif is_exclusion:
                    is_workflow = False
                else:
                    if level == 2:
                        is_workflow = False
                    else:
                        is_workflow = header_stack[-1][2] if header_stack else False

                header_stack.append((level, header_text, is_workflow))
                in_workflow_section = is_workflow
                if in_workflow_section:
                    if workflow_trigger_level is None or level <= workflow_trigger_level:
                        workflow_trigger_level = level
                else:
                    workflow_trigger_level = None

                if in_workflow_section and is_step_header and step_match:
                    current_step_line = idx + 1
                    current_step_num = step_match.group(1) or step_match.group(3)
                    current_step_content = [line]
                    in_heading_step = True
                    step_level = level
                else:
                    in_heading_step = False
                    step_level = None
                continue

            if not in_workflow_section:
                continue

            if in_heading_step:
                if current_step_line is not None:
                    current_step_content.append(line)
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
                                f"Step {current_step_num} is missing a Completion Criterion "
                                f"('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                            )
                        )

                current_step_line = idx + 1
                current_step_num = step_match.group(1) or step_match.group(3)
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
                        f"Step {current_step_num} is missing a Completion Criterion "
                        f"('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                    )
                )

        return errors

    _analyze_steps_completion_criteria = analyze_steps_completion_criteria

    def audit_workflow(self, file_path: Path) -> list[SkillAuditIssue]:
        """Audit a single workflow file for CCBA compliance."""
        issues: list[SkillAuditIssue] = []
        if not file_path.exists():
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "File does not exist",
                    category="MISSING_FILE",
                    file_path=str(file_path),
                )
            ]

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Failed to read file: {e}",
                    category="READ_ERROR",
                    file_path=str(file_path),
                )
            ]

        match = FRONTMATTER_RE.match(content)
        if not match:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Missing YAML frontmatter '---'",
                    category="MALFORMED_FRONTMATTER",
                    file_path=str(file_path),
                )
            ]

        if yaml is None:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "PyYAML package is required to parse workflow frontmatter.",
                    category="YAML_PACKAGE_MISSING",
                    file_path=str(file_path),
                )
            ]

        try:
            meta = yaml.safe_load(match.group(1))
        except Exception as e:
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Failed to parse frontmatter YAML: {e}",
                    category="YAML_PARSE_ERROR",
                    file_path=str(file_path),
                )
            ]

        if not isinstance(meta, dict):
            return [
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Frontmatter YAML is not a valid dictionary",
                    category="MALFORMED_FRONTMATTER",
                    file_path=str(file_path),
                )
            ]

        description = meta.get("description")
        disable_model_inv = meta.get("disable-model-invocation", False)
        if isinstance(disable_model_inv, str):
            disable_model_inv = disable_model_inv.lower() in ("true", "1", "yes")

        if not description or not isinstance(description, str):
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Missing or invalid 'description' in workflow frontmatter",
                    category="MISSING_DESCRIPTION",
                    file_path=str(file_path),
                )
            )

        # Workflows must be 0-token (disable-model-invocation: true per ADR-0040)
        if disable_model_inv is not True:
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    "Workflow must have 'disable-model-invocation: true' to enforce "
                    "0-token system prompt invariant (ADR-0040)",
                    category="WORKFLOW_MODEL_INVOCATION_NOT_DISABLED",
                    file_path=str(file_path),
                )
            )

        lines = content.splitlines()
        if len(lines) > 150:
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Workflow length ({len(lines)} lines) exceeds maximum 150 lines limit. "
                    f"Extract large scripts/templates to Deep Seams per ADR-0011.",
                    category="WORKFLOW_TOO_LONG",
                    file_path=str(file_path),
                )
            )

        body = content[match.end() :]
        if not re.search(r"^#\s+", body, re.MULTILINE):
            issues.append(
                SkillAuditIssue(
                    len(match.group(0).splitlines()) + 1,
                    str(file_path),
                    "Missing H1 heading '# Workflow: ...' in workflow body",
                    category="MISSING_H1_HEADING",
                    file_path=str(file_path),
                )
            )

        return issues

    def audit_workspace_gates(self, skills_dir: Path | None = None) -> list[SkillAuditIssue]:
        """Perform workspace-level CI Gate checks across all skills."""
        issues: list[SkillAuditIssue] = []
        if skills_dir is None or skills_dir.is_file():
            skills_dir = self.project_root / ".agents" / "skills"

        if not skills_dir.exists():
            return issues

        skill_files = list(skills_dir.rglob("SKILL.md"))
        seen_names: dict[str, list[Path]] = defaultdict(list)
        bundle_model_invoked_counts: dict[str, int] = defaultdict(int)

        for sf in skill_files:
            try:
                content = sf.read_text(encoding="utf-8")
                # Shallow skill check across workspace
                issues.extend(self.check_shallow_skill(sf, content))

                match = FRONTMATTER_RE.match(content)
                if match and yaml is not None:
                    meta = yaml.safe_load(match.group(1))
                    if isinstance(meta, dict):
                        name = meta.get("name")
                        if name:
                            seen_names[str(name).strip().lower()].append(sf)

                        disable_model_inv = meta.get("disable-model-invocation", False)
                        if isinstance(disable_model_inv, str):
                            disable_model_inv = disable_model_inv.lower() in ("true", "1", "yes")
                        bundle = meta.get("bundle") or meta.get("layer") or "_default"
                        if not disable_model_inv:
                            bundle_model_invoked_counts[str(bundle)] += 1
            except Exception:
                pass

        # 1. Zero-Duplicate Gate
        for skill_name, paths in seen_names.items():
            if len(paths) > 1:
                rel_paths = [
                    str(
                        p.relative_to(self.project_root)
                        if p.is_relative_to(self.project_root)
                        else p
                    )
                    for p in paths
                ]
                issues.append(
                    SkillAuditIssue(
                        1,
                        skill_name,
                        f"Duplicate skill name '{skill_name}' found across multiple locations: "
                        f"{', '.join(rel_paths)}",
                        category="ZERO_DUPLICATE_GATE_VIOLATION",
                        file_path=str(paths[0]),
                    )
                )

        # 2. Context Budget Ceiling Gate (<= 10 model_invoked per bundle)
        for bundle, count in bundle_model_invoked_counts.items():
            if count > MAX_MODEL_INVOKED_PER_BUNDLE:
                issues.append(
                    SkillAuditIssue(
                        1,
                        bundle,
                        f"Context Budget Ceiling Exceeded: Bundle '{bundle}' has {count} "
                        f"model-invoked skills (Max allowed: {MAX_MODEL_INVOKED_PER_BUNDLE}). "
                        f"Convert ritual workflows to 'disable-model-invocation: true' per ADR-0040.",
                        category="CONTEXT_BUDGET_CEILING_EXCEEDED",
                        file_path=str(skills_dir),
                    )
                )

        # 3. Relative Link Integrity Gate across all skill markdown files
        all_md_files = sorted(skills_dir.rglob("*.md"))
        for md_file in all_md_files:
            for link_issue in self.validate_markdown_links(md_file):
                if hasattr(link_issue, "to_audit_issue"):
                    issues.append(link_issue.to_audit_issue())
                else:
                    issues.append(
                        SkillAuditIssue(
                            1,
                            str(md_file),
                            str(link_issue),
                            category="BROKEN_MARKDOWN_LINK",
                            file_path=str(md_file),
                        )
                    )

        # 4. Slash Command Registry Parity Gate across all skill markdown files
        registered_cmds = self.get_registered_commands()
        for md_file in all_md_files:
            for cmd_issue in self.audit_slash_commands(
                md_file, registered_commands=registered_cmds
            ):
                if hasattr(cmd_issue, "to_audit_issue"):
                    issues.append(cmd_issue.to_audit_issue())
                else:
                    issues.append(
                        SkillAuditIssue(
                            1,
                            str(md_file),
                            str(cmd_issue),
                            category="UNREGISTERED_SLASH_COMMAND",
                            file_path=str(md_file),
                        )
                    )

        return issues

    def run_cli(self, args_list: list[str] | None = None) -> int:
        """Run CLI validation on target paths."""
        from .cli import run_skill_validation_cli

        return run_skill_validation_cli(args_list, validator=self)
