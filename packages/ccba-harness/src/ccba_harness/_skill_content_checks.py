"""_skill_content_checks.py - Markdown link, slash command, step criteria, and workflow checks.

Internal decomposition module for `ccba_harness.skill_validator`.
Not a standalone package boundary for external callers unless explicitly re-exported.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._skill_frontmatter import (
    AuditIssueString,
    SkillAuditIssue,
    normalize_bool_flag,
    parse_frontmatter_dict,
)

STEP_LINE_RE = re.compile(
    r"^\s*(?:([0-9]+)\.\s+(.*)|#{1,6}\s+(?:[^\w\s]*\s*)?(?:bước|step|phase|pha|giai đoạn)\s*([0-9]+(?:\.[0-9]+)*|[ivxlcdm]+)(?:[:.\-—\s]+(.*)|$))",
    re.IGNORECASE,
)

WORKFLOW_HEADERS: set[str] = set(
    "workflow|quy trình|các bước|steps|hành động|chuyển đổi|tiến hành|thực hiện".split("|")
)

EXCLUSION_HEADERS: set[str] = set(
    "lưu ý|chú ý|notes|yêu cầu|rules|quy tắc|tham chiếu|reference|giới thiệu|introduction|"
    "tổng quan|overview|chuẩn bị|setup|tiêu chí hoàn thành|completion criteria|definition of done".split(
        "|"
    )
)

COMMON_PATH_SEGMENTS: set[str] = set(
    "bin usr etc dev tmp var proc sys mnt opt src packages scripts tests docs references "
    "templates standards examples appendices output scratch legal_docs sources lib build "
    "dist node_modules artifacts".split()
)

ALLOWED_HOST_COMMANDS: set[str] = set(
    "/boost /browser /clear /compact /goal /grill-me /init /learn /schedule /ship /skill-repair /teamwork-preview /ui-ux-pro-max".split()
)

GITLAB_QUICK_ACTIONS: set[str] = set(
    "/blocked_by /close /reopen /assign /milestone /label /cc".split()
)

LINK_EXTRACT_RE = re.compile(r"\[.*?\]\(([^)]+)\)")
SLASH_CMD_RE = re.compile(r"(?<![a-zA-Z0-9_./\\<])(/([a-z][a-z0-9_\-]*))(?![a-zA-Z0-9_./\\-])")

_IGNORED_LINK_SCHEMES = ("http://", "https://", "mailto:", "conversation:", "file://", "#")
_IGNORED_LINK_CHARS = ("<", ">", "{", "}", "*", "...", "[")
_FILE_EXT_HINTS = (
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
_PLACEHOLDER_SLASH_CMDS = {
    "/<cmd>",
    "/<name>",
    "/<command>",
    "/<skill-name>",
    "/<canonical-name>",
    "/ccba-",
}


@dataclass
class _StepScanState:
    """Mutable state tracking workflow heading hierarchy and active step content."""

    header_stack: list[tuple[int, str, bool]] = field(default_factory=list)
    in_workflow_section: bool = False
    workflow_trigger_level: int | None = None
    in_code_block: bool = False
    current_step_line: int | None = None
    current_step_num: str | None = None
    current_step_content: list[str] = field(default_factory=list)
    in_heading_step: bool = False
    step_level: int | None = None


def is_exclusion_header(header_text: str) -> bool:
    """Check if header is an exclusion header, ignoring step execution headers."""
    if re.search(
        r"(?:bước|step|phase|pha|giai đoạn)\s*(?:[0-9]+(?:\.[0-9]+)*|[ivxlcdm]+)",
        header_text,
        re.IGNORECASE,
    ):
        return False
    return any(kw in header_text.lower() for kw in EXCLUSION_HEADERS)


def _extract_broken_links_in_line(line: str, idx: int, file_path: Path) -> list[str]:
    """Return AuditIssueString items for unresolved relative markdown links in one line."""
    issues: list[str] = []
    line_no_code = re.sub(r"`[^`]+`", "", line)
    for target in LINK_EXTRACT_RE.findall(line_no_code):
        target = target.strip()
        if target.startswith(_IGNORED_LINK_SCHEMES) or any(
            char in target for char in _IGNORED_LINK_CHARS
        ):
            continue
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


def validate_markdown_links_in_file(file_path: Path, content: str | None = None) -> list[str]:
    """Validate that relative markdown links in a file resolve to valid on-disk files."""
    if content is None:
        if not file_path.exists():
            return []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            return [
                AuditIssueString(
                    f"{file_path}:1: Failed to read file: {exc}",
                    line_number=1,
                    subject=str(file_path),
                    category="READ_ERROR",
                    file_path=str(file_path),
                )
            ]

    issues: list[str] = []
    in_code_block = False
    for idx, line in enumerate(content.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            issues.extend(_extract_broken_links_in_line(line, idx, file_path))
    return issues


def _find_unregistered_commands_in_line(
    line: str, idx: int, file_path: Path, allowed_cmds: set[str]
) -> list[str]:
    """Scan a sanitized non-code markdown line for unregistered slash command references."""
    clean = re.sub(r"https?://[^\s)]+", "", line)
    clean = re.sub(r"</[a-zA-Z0-9_\-:]+>", "", clean)
    clean = re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", clean)
    clean = re.sub(r"/[a-z0-9_\-]+:[a-z0-9_\-]+", "", clean)
    clean = re.sub(r"/[<{][^>}]*[>}]", "", clean)
    clean = re.sub(r"/ccba-[<{][^>}]*[>}]", "", clean)

    issues: list[str] = []
    for m in SLASH_CMD_RE.finditer(clean):
        full_cmd, base, start = m.group(1), m.group(2), m.start(1)
        if start > 0 and clean[start - 1].isalpha():
            continue
        if base in COMMON_PATH_SEGMENTS or len(base) <= 1 or full_cmd in _PLACEHOLDER_SLASH_CMDS:
            continue
        remainder = clean[start + 1 :].split()[0]
        if any(ext in remainder for ext in _FILE_EXT_HINTS):
            continue
        if full_cmd not in allowed_cmds:
            msg = (
                f"{file_path}:{idx}: Unregistered slash command '{full_cmd}' referenced in document. "
                "Must be a registered command in catalog.yaml (or replace with canonical command)."
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


def audit_slash_commands_in_file(
    file_path: Path,
    content: str | None = None,
    allowed_cmds: set[str] | None = None,
) -> list[str]:
    """Audit markdown content for unregistered slash command references."""
    if not allowed_cmds:
        return []
    if content is None:
        if not file_path.exists():
            return []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

    issues: list[str] = []
    in_code_block = False
    for idx, line in enumerate(content.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            issues.extend(_find_unregistered_commands_in_line(line, idx, file_path, allowed_cmds))
    return issues


def _flush_pending_step(state: _StepScanState, errors: list[tuple[int, str]]) -> None:
    """Emit a missing-completion-criterion error if the buffered step lacks one."""
    if state.current_step_line is None:
        return
    step_body = "\n".join(state.current_step_content)
    if "**Completion Criterion:**" not in step_body and "**Tiêu chí hoàn thành:**" not in step_body:
        errors.append(
            (
                state.current_step_line,
                f"Step {state.current_step_num} is missing a Completion Criterion "
                "('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
            )
        )
    state.current_step_line = None
    state.current_step_num = None
    state.current_step_content = []
    state.in_heading_step = False
    state.step_level = None


def _handle_markdown_header_line(
    state: _StepScanState, line: str, idx: int, errors: list[tuple[int, str]]
) -> None:
    """Update workflow-section stack and heading-step state for a markdown header line."""
    line_strip = line.strip()
    level = len(line_strip) - len(line_strip.lstrip("#"))
    header_text = line_strip.lstrip("#").strip().lower()
    step_match = STEP_LINE_RE.match(line)
    is_step_header = bool(step_match)

    if (
        state.in_heading_step
        and state.step_level is not None
        and level > state.step_level
        and not is_step_header
    ):
        if state.current_step_line is not None:
            state.current_step_content.append(line)
        return

    _flush_pending_step(state, errors)
    while state.header_stack and state.header_stack[-1][0] >= level:
        state.header_stack.pop()

    is_exclusion = is_exclusion_header(header_text)
    in_excl_ancestor = any(is_exclusion_header(h[1]) for h in state.header_stack)
    is_wf_kw = any(kw in header_text for kw in WORKFLOW_HEADERS)
    if (is_wf_kw or is_step_header) and not is_exclusion and not in_excl_ancestor:
        is_wf = True
    elif is_exclusion or level == 2:
        is_wf = False
    else:
        is_wf = state.header_stack[-1][2] if state.header_stack else False

    state.header_stack.append((level, header_text, is_wf))
    state.in_workflow_section = is_wf
    if is_wf:
        if state.workflow_trigger_level is None or level <= state.workflow_trigger_level:
            state.workflow_trigger_level = level
    else:
        state.workflow_trigger_level = None

    if is_wf and is_step_header and step_match:
        state.current_step_line = idx + 1
        state.current_step_num = step_match.group(1) or step_match.group(3)
        state.current_step_content = [line]
        state.in_heading_step = True
        state.step_level = level


def analyze_steps_completion_criteria(body: str) -> list[tuple[int, str]]:
    """Scan workflow steps in markdown body for Completion Criteria."""
    errors: list[tuple[int, str]] = []
    state = _StepScanState()
    for idx, line in enumerate(body.splitlines()):
        line_strip = line.strip()
        if line_strip.startswith("```"):
            state.in_code_block = not state.in_code_block
            if state.current_step_line is not None:
                state.current_step_content.append(line)
            continue
        if state.in_code_block or not line_strip:
            if state.current_step_line is not None:
                state.current_step_content.append(line)
            continue
        if line_strip.startswith("#"):
            _handle_markdown_header_line(state, line, idx, errors)
            continue
        if not state.in_workflow_section:
            continue
        if state.in_heading_step:
            if state.current_step_line is not None:
                state.current_step_content.append(line)
            continue
        step_match = STEP_LINE_RE.match(line)
        if step_match:
            _flush_pending_step(state, errors)
            state.current_step_line = idx + 1
            state.current_step_num = step_match.group(1) or step_match.group(3)
            state.current_step_content = [line]
        elif state.current_step_line is not None:
            state.current_step_content.append(line)

    _flush_pending_step(state, errors)
    return errors


def _read_workflow_content(file_path: Path) -> tuple[str | None, list[SkillAuditIssue]]:
    """Read workflow file or return missing/read error SkillAuditIssue."""
    fp = str(file_path)
    if not file_path.exists():
        return None, [SkillAuditIssue(1, fp, "File does not exist", "MISSING_FILE", fp)]
    try:
        return file_path.read_text(encoding="utf-8"), []
    except Exception as exc:
        return None, [SkillAuditIssue(1, fp, f"Failed to read file: {exc}", "READ_ERROR", fp)]


def _validate_workflow_rules(
    fp: str, content: str, fm_end: int, fm_lines: int, meta: dict[str, Any]
) -> list[SkillAuditIssue]:
    """Validate workflow metadata and body constraints (description, 0-token, length, H1)."""
    issues: list[SkillAuditIssue] = []
    description = meta.get("description")
    if not description or not isinstance(description, str):
        issues.append(
            SkillAuditIssue(
                1,
                fp,
                "Missing or invalid 'description' in workflow frontmatter",
                "MISSING_DESCRIPTION",
                fp,
            )
        )
    if normalize_bool_flag(meta.get("disable-model-invocation", False)) is not True:
        issues.append(
            SkillAuditIssue(
                1,
                fp,
                "Workflow must have 'disable-model-invocation: true' to enforce 0-token system prompt invariant (ADR-0040)",
                "WORKFLOW_MODEL_INVOCATION_NOT_DISABLED",
                fp,
            )
        )
    lines = content.splitlines()
    if len(lines) > 150:
        issues.append(
            SkillAuditIssue(
                1,
                fp,
                f"Workflow length ({len(lines)} lines) exceeds maximum 150 lines limit. Extract large scripts/templates to Deep Seams per ADR-0011.",
                "WORKFLOW_TOO_LONG",
                fp,
            )
        )
    if not re.search(r"^#\s+", content[fm_end:], re.MULTILINE):
        issues.append(
            SkillAuditIssue(
                fm_lines + 1,
                fp,
                "Missing H1 heading '# Workflow: ...' in workflow body",
                "MISSING_H1_HEADING",
                fp,
            )
        )
    return issues


def audit_workflow_file(file_path: Path, yaml_module: Any = None) -> list[SkillAuditIssue]:
    """Audit a single workflow markdown file for CCBA compliance."""
    fp = str(file_path)
    content, read_issues = _read_workflow_content(file_path)
    if content is None:
        return read_issues

    match, meta, fm_issues = parse_frontmatter_dict(
        fp,
        content,
        yaml_module=yaml_module,
        missing_yaml_msg="PyYAML package is required to parse workflow frontmatter.",
    )
    if fm_issues or match is None or meta is None:
        return fm_issues
    return _validate_workflow_rules(
        fp, content, match.end(), len(match.group(0).splitlines()), meta
    )
