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

        step_errors = self._analyze_steps_completion_criteria(body)
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
        is_orchestrated = meta.get(
            "is-orchestrated",
            meta.get("is_orchestrated", meta.get("orchestrated", False)),
        )
        if isinstance(is_orchestrated, str):
            is_orchestrated = is_orchestrated.lower() in ("true", "1", "yes")
        if is_orchestrated:
            issues.append(
                SkillAuditIssue(
                    1,
                    str(file_path),
                    f"Skill '{skill_name}' violates Gate 1 (Orchestration Gate): task coordinates "
                    f"multiple agents, StateGraph checkpoints, or requires HITL approval, "
                    f"and must be implemented as Tier 3 (Composite Orchestrator).",
                    category="ORCHESTRATION_GATE_VIOLATION",
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
                        if enforce_gpi and decision.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE:
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
        override_metrics: GPIMetrics | None = None,
        override_parent: str | None = None,
    ) -> DecisionResult:
        """Evaluate an existing SKILL.md file directly through the Two-Stage Decision Framework.

        Args:
            file_path: Path to the SKILL.md file.
            override_metrics: Optional fallback/override GPIMetrics if not in frontmatter.
            override_parent: Optional fallback/override parent skill name.

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

        is_orchestrated = meta.get(
            "is-orchestrated",
            meta.get("is_orchestrated", meta.get("orchestrated", False)),
        )
        if isinstance(is_orchestrated, str):
            is_orchestrated = is_orchestrated.lower() in ("true", "1", "yes")

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

        request = DecisionRequest(
            name=skill_name,
            is_deterministic=bool(is_deterministic),
            is_orchestrated=bool(is_orchestrated),
            gpi_metrics=metrics,
            parent_skill=parent_skill,
            metadata={"file_path": str(file_path)},
        )
        return evaluate_two_stage_decision(request)

    def evaluate_two_stage_decision(self, request: DecisionRequest) -> DecisionResult:
        """Evaluate capability architecture placement using Two-Stage Decision Framework."""
        return evaluate_two_stage_decision(request)

    def calculate_gpi(self, s: float, k: float, a: float, p: float) -> float:
        """Calculate Granularity & Placement Index (GPI)."""
        return calculate_gpi(s, k, a, p)

    def _analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
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

        return issues

    def run_cli(self, args_list: list[str] | None = None) -> int:
        """Run CLI validation on target paths."""
        from .cli import run_skill_validation_cli

        return run_skill_validation_cli(args_list, validator=self)
