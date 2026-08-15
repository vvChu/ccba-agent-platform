"""base.py - Base abstractions, DTOs, and common regex constants for Governance Engine.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple

# Core Regex Patterns
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
CODE_REF_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*(?:\(\))?)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ENV_VAR_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,})`|\$([A-Z][A-Z0-9_]{2,})")
STEP_LINE_RE = re.compile(r"^\s*([0-9]+)\.\s+(.*)$")


class AuditIssue(NamedTuple):
    """Container for a single audit issue."""

    line_number: int
    subject: str
    message: str
    category: str = ""
    file_path: str = ""


@dataclass
class AuditReport:
    """Structured report container for workspace audit results."""

    issues: list[AuditIssue] = field(default_factory=list)
    total_issues: int = 0
    has_hard_errors: bool = False
    scanned_files: int = 0

    def by_category(self, category: str) -> list[AuditIssue]:
        """Filter issues by category name."""
        return [i for i in self.issues if i.category == category]

    def by_file(self, file_path: str) -> list[AuditIssue]:
        """Filter issues by file path."""
        return [i for i in self.issues if i.file_path == file_path]


# Common Keywords to Ignore in Code Symbol Audit
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
IGNORE_ENV_VARS: set[str] = {"ARGUMENTS", "SLF001", "B023", "B904", "I001", "F401", "E501"}

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


class BaseAuditor(ABC):
    """Abstract base class for all domain sub-auditors."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize base auditor with project root."""
        if project_root is None:
            # Fallback to repository root
            project_root = Path(__file__).resolve().parent.parent.parent
        self.project_root = project_root

    @abstractmethod
    def audit(self, target: Any) -> list[AuditIssue]:
        """Audit target and return a list of AuditIssues."""
        raise NotImplementedError
