"""env_auditor.py - Sub-Auditor for Environment Variables consistency & secrets protection.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import (
    ENV_VAR_RE,
    IGNORE_ENV_PREFIXES,
    IGNORE_ENV_VARS,
    AuditIssue,
    BaseAuditor,
)


class EnvAuditor(BaseAuditor):
    """Deep Sub-Auditor for Environment Variable documentation and .env.example parity."""

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

    def extract_env_variables(self, content: str) -> list[tuple[int, str]]:
        """Extract documented environment variables from markdown content."""
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

    def audit(self, target: Path | str, env_vars: set[str] | None = None) -> list[AuditIssue]:
        """Audit environment variables in target file or text content against .env.example."""
        if env_vars is None:
            env_vars = self.load_env_example()

        if isinstance(target, Path):
            if not target.exists():
                return []
            content = target.read_text(encoding="utf-8", errors="ignore")
            file_str = str(
                target.relative_to(self.project_root)
                if target.is_relative_to(self.project_root)
                else target
            )
        else:
            content = target
            file_str = "inline_content"

        extracted = self.extract_env_variables(content)
        issues: list[AuditIssue] = []
        for line_num, var in extracted:
            if env_vars and var not in env_vars:
                issues.append(
                    AuditIssue(
                        line_number=line_num,
                        subject=var,
                        message=f"Variable '{var}' is missing in .env.example",
                        category="env_vars",
                        file_path=file_str,
                    )
                )
        return issues
