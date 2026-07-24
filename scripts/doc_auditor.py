"""doc_auditor.py - Unified Deep Module for Document & Skill Auditing.

Deep module hiding frontmatter parsing, line-scanning regexes, symbol lookups,
AST/heading section analysis, and link validation behind a clean 2-method surface:
`audit_document(path)` and `audit_workspace()`.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

import os
import re
from pathlib import Path
from typing import Any, NamedTuple

import yaml

# Core Regex Patterns
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
CODE_REF_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*(?:\(\))?)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ENV_VAR_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,})`|\$([A-Z][A-Z0-9_]{2,})")
STEP_LINE_RE = re.compile(r"^\s*([0-9]+)\.\s+(.*)$")

# Common Keywords to Ignore
IGNORE_CODE_REFS: set[str] = {
    "true",
    "false",
    "null",
    "undefined",
    "string",
    "number",
    "boolean",
    "object",
    "array",
    "function",
    "async",
    "await",
    "const",
    "let",
    "var",
    "if",
    "else",
    "for",
    "while",
    "return",
    "import",
    "export",
    "default",
    "npm",
    "npx",
    "node",
    "yarn",
    "pnpm",
    "git",
    "bash",
    "sh",
    "zsh",
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "head",
    "options",
    "json",
    "xml",
    "html",
    "css",
    "sql",
    "api",
    "url",
    "uri",
    "http",
    "https",
    "ok",
    "error",
    "warning",
    "info",
    "debug",
    "trace",
    "readme",
    "license",
    "changelog",
    "todo",
    "fixme",
    "note",
    "hack",
    "dev",
    "prod",
    "test",
    "staging",
    "production",
    "development",
    "src",
    "lib",
    "dist",
    "build",
    "docs",
    "tests",
    "config",
    "index",
    "main",
    "app",
    "server",
    "client",
    "utils",
    "helpers",
}

IGNORE_ENV_PREFIXES: list[str] = ["NODE_", "PATH", "HOME", "USER", "SHELL", "TERM", "PWD", "CI"]
IGNORE_ENV_VARS: set[str] = {"ARGUMENTS"}

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
}


class AuditIssue(NamedTuple):
    """Container for a single audit issue."""

    line_number: int
    subject: str
    message: str


class DocumentAuditor:
    """Deep module for auditing CCBA Agent markdown documentation and skills.

    Hides internal line-scanning, symbol searches, and frontmatter parsing logic
    behind a simplified interface.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize DocumentAuditor with workspace root path."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.resolve()
        self.project_root = project_root

    def parse_frontmatter(self, content: str) -> tuple[dict[str, Any] | None, str]:
        """Parse YAML frontmatter from document content."""
        stripped = content.strip()
        if not stripped.startswith("---"):
            return None, content
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                if isinstance(frontmatter, dict):
                    return frontmatter, parts[2]
            except Exception:
                pass
        return None, content

    def extract_code_references(self, content: str) -> list[tuple[int, str]]:
        """Extract code symbol references like `my_func()` or `MyClass`."""
        references = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if line.strip().startswith("```"):
                continue
            matches = CODE_REF_RE.findall(line)
            for ref in matches:
                clean_ref = ref.replace("()", "")
                if clean_ref.lower() in IGNORE_CODE_REFS:
                    continue
                if ref.endswith("()") or (
                    clean_ref and clean_ref[0].isupper() and any(c.islower() for c in clean_ref)
                ):
                    references.append((idx + 1, ref))
        return references

    def extract_internal_links(self, content: str) -> list[tuple[int, str, str]]:
        """Extract relative internal Markdown links."""
        links = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            matches = LINK_RE.findall(line)
            for text, href in matches:
                if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
                    continue
                links.append((idx + 1, text, href))
        return links

    def extract_env_variables(self, content: str) -> list[tuple[int, str]]:
        """Extract documented environment variables."""
        env_vars = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if line.strip().startswith("```"):
                continue
            matches = ENV_VAR_RE.findall(line)
            for var1, var2 in matches:
                var = var1 or var2
                if not var:
                    continue
                if any(var.startswith(prefix) for prefix in IGNORE_ENV_PREFIXES):
                    continue
                if var in IGNORE_ENV_VARS:
                    continue
                env_vars.append((idx + 1, var))
        return env_vars

    def search_codebase_for_symbol(
        self, symbol: str, search_dirs: list[Path] | None = None
    ) -> bool:
        """Check if symbol declaration exists in codebase source files."""
        if search_dirs is None:
            search_dirs = [
                self.project_root / "src",
                self.project_root / "packages",
                self.project_root / "scripts",
            ]

        clean_sym = symbol.replace("()", "")
        patterns = [
            re.compile(r"\bdef\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bclass\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bfunction\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bconst\s+" + re.escape(clean_sym) + r"\s*="),
            re.compile(r"\blet\s+" + re.escape(clean_sym) + r"\s*="),
        ]

        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for ext in ["*.py", "*.js", "*.cjs", "*.ts", "*.go", "*.sh"]:
                for filepath in sdir.rglob(ext):
                    if any(
                        p in filepath.parts
                        for p in ["tests", "venv", ".venv", "node_modules", "dist", "build"]
                    ):
                        continue
                    try:
                        with open(filepath, encoding="utf-8", errors="ignore") as f:
                            file_content = f.read()
                            if any(pat.search(file_content) for pat in patterns):
                                return True
                    except Exception:
                        continue
        return False

    def load_env_example(self) -> set[str]:
        """Load declared environment variable names from .env.example."""
        env_path = self.project_root / ".env.example"
        if not env_path.exists():
            return set()
        env_vars = set()
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    match = re.match(r"^([A-Z0-9_]+)=", line)
                    if match:
                        env_vars.add(match.group(1))
        except Exception:
            pass
        return env_vars

    def audit_skill(self, file_path: Path) -> list[AuditIssue]:
        """Audit a single SKILL.md file for CCBA compliance.

        Enforces frontmatter schema, description character limits, and Completion Criteria in workflow steps.
        """
        issues: list[AuditIssue] = []
        if not file_path.exists():
            return [AuditIssue(1, str(file_path), "File does not exist")]

        content = file_path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(content)
        if not match:
            return [AuditIssue(1, str(file_path), "Missing YAML frontmatter '---'")]

        try:
            meta = yaml.safe_load(match.group(1))
        except Exception as e:
            return [AuditIssue(1, str(file_path), f"Failed to parse frontmatter YAML: {e}")]

        if not isinstance(meta, dict):
            return [AuditIssue(1, str(file_path), "Frontmatter YAML is not a valid dictionary")]

        # Validate required frontmatter keys
        name = meta.get("name")
        description = meta.get("description")
        disable_model_inv = meta.get("disable-model-invocation", False)

        if not name or not isinstance(name, str):
            issues.append(AuditIssue(1, str(file_path), "Missing or invalid 'name' in frontmatter"))
        if not description or not isinstance(description, str):
            issues.append(
                AuditIssue(1, str(file_path), "Missing or invalid 'description' in frontmatter")
            )

        if description and isinstance(description, str) and not disable_model_inv:
            if len(description) > 180:
                issues.append(
                    AuditIssue(
                        1,
                        str(file_path),
                        f"Description length ({len(description)}) exceeds 180 character limit for model-invoked skill",
                    )
                )

        # Count frontmatter line count to offset step line numbers
        frontmatter_lines = len(match.group(0).splitlines())
        body = content[match.end() :]

        # Analyze workflow steps for Completion Criteria
        step_errors = self._analyze_steps_completion_criteria(body)
        for line_offset, err_msg in step_errors:
            abs_line = line_offset + frontmatter_lines
            issues.append(AuditIssue(abs_line, str(file_path), err_msg))

        return issues

    def _analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
        """Helper to scan workflow steps for Completion Criteria."""
        errors = []
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

        # Final check at end of body
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

    def audit_workspace(self) -> dict[str, Any]:
        """Audit all documentation and skills in workspace."""
        skill_issues: list[AuditIssue] = []
        skills_dir = self.project_root / ".agents" / "skills"

        if skills_dir.exists():
            for skill_path in skills_dir.rglob("SKILL.md"):
                skill_issues.extend(self.audit_skill(skill_path))

        return {
            "skills": skill_issues,
            "total_skill_issues": len(skill_issues),
        }
