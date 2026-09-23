"""wiki_health_linter.py - Deep Sub-Auditor for LLM-Wiki Knowledge Base Health & Schema Integrity.

Enforces Karpathy 3-tier LLM-Wiki invariants:
1. Index catalog integrity (.md/knowledge/index.md)
2. Append-only mutation log schema (.md/knowledge/log.md)
3. Zero-orphan knowledge notes (Every active note must be cataloged in index.md)
4. Internal link resolution without broken targets in active core docs

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    from .base import LINK_RE, AuditIssue, BaseAuditor
except ImportError:
    # Standalone execution
    _root = Path(__file__).resolve().parent.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from scripts.governance.base import LINK_RE, AuditIssue, BaseAuditor

LOG_HEADER_RE = re.compile(
    r"^##\s+\[(\d{4}-\d{2}-\d{2})\]\s+\[(ingest|synthesize|adr|guideline|archive|linter|update)\]\s+\|\s+(.+)$"
)


class WikiHealthLinter(BaseAuditor):
    """Deep Sub-Auditor for verifying .md/knowledge LLM-Wiki integrity and invariants."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__(project_root=project_root)
        self.knowledge_dir = self.project_root / ".md" / "knowledge"
        self.index_file = self.knowledge_dir / "index.md"
        self.log_file = self.knowledge_dir / "log.md"

    def check_index_integrity(self) -> list[AuditIssue]:
        """Verify that index.md exists, is non-empty, and contains master taxonomy."""
        issues: list[AuditIssue] = []
        if not self.knowledge_dir.exists():
            return issues

        if not self.index_file.exists():
            issues.append(
                AuditIssue(
                    line_number=1,
                    subject="Missing LLM-Wiki Index",
                    message="Missing master knowledge catalog '.md/knowledge/index.md'",
                    category="wiki_health",
                    file_path=str(self.index_file.relative_to(self.project_root)),
                )
            )
            return issues

        content = self.index_file.read_text(encoding="utf-8")
        if len(content.strip()) < 50:
            issues.append(
                AuditIssue(
                    line_number=1,
                    subject="Empty LLM-Wiki Index",
                    message="Master catalog '.md/knowledge/index.md' is essentially empty",
                    category="wiki_health",
                    file_path=str(self.index_file.relative_to(self.project_root)),
                )
            )

        return issues

    def check_log_schema(self) -> list[AuditIssue]:
        """Verify that log.md conforms to the mutation log schema."""
        issues: list[AuditIssue] = []
        if not self.knowledge_dir.exists() or not self.log_file.exists():
            return issues

        lines = self.log_file.read_text(encoding="utf-8").splitlines()
        found_entries = 0

        for line_num, line in enumerate(lines, start=1):
            if line.startswith("## "):
                match = LOG_HEADER_RE.match(line.strip())
                if not match:
                    issues.append(
                        AuditIssue(
                            line_number=line_num,
                            subject="Invalid Wiki Log Header",
                            message=(
                                f"Log entry header does not match schema '## [YYYY-MM-DD] [operation] | Title': '{line}'"
                            ),
                            category="wiki_log_schema",
                            file_path=str(self.log_file.relative_to(self.project_root)),
                        )
                    )
                else:
                    found_entries += 1

        if found_entries == 0 and len(lines) > 0 and len(issues) == 0:
            issues.append(
                AuditIssue(
                    line_number=1,
                    subject="No Wiki Log Entries",
                    message="No valid mutation entries found in '.md/knowledge/log.md'",
                    category="wiki_log_schema",
                    file_path=str(self.log_file.relative_to(self.project_root)),
                )
            )

        return issues

    def get_cataloged_files(self) -> set[Path]:
        """Extract all relative file targets referenced in index.md."""
        cataloged: set[Path] = set()
        if not self.index_file.exists():
            return cataloged

        content = self.index_file.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(content):
            raw_target = match.group(2).strip()
            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                continue

            target_clean = raw_target.split("#")[0].split("?")[0]
            if not target_clean:
                continue

            if target_clean.startswith("file://"):
                clean_path = target_clean.replace("file:///", "").replace("file://", "")
                resolved = Path(clean_path).resolve()
            else:
                resolved = (self.knowledge_dir / target_clean).resolve()

            cataloged.add(resolved)

        return cataloged

    def check_orphan_knowledge_files(self) -> list[AuditIssue]:
        """Identify markdown notes in .md/knowledge/ that are uncataloged in index.md."""
        issues: list[AuditIssue] = []
        if not self.knowledge_dir.exists() or not self.index_file.exists():
            return issues

        cataloged = self.get_cataloged_files()
        cataloged.add(self.index_file.resolve())
        cataloged.add(self.log_file.resolve())

        # Exclude archives, task trackers, reports, escalations, and snapshot notes
        exclude_dirs = {
            "archive",
            ".agents",
            ".git",
            "__pycache__",
            "issues",
            "teach",
            "reports",
            "escalations",
        }

        for p in self.knowledge_dir.rglob("*.md"):
            if not p.is_file():
                continue
            if p.name.endswith("_compiled.md") or p.name.startswith("."):
                continue
            if any(ex in p.parts for ex in exclude_dirs):
                continue

            resolved_path = p.resolve()
            # If the file or any of its parent directories is cataloged, accept it
            if resolved_path not in cataloged:
                if any(parent.resolve() in cataloged for parent in p.parents):
                    continue

                rel_path = (
                    p.relative_to(self.project_root) if p.is_relative_to(self.project_root) else p
                )
                issues.append(
                    AuditIssue(
                        line_number=1,
                        subject="Orphan Knowledge Note",
                        message=f"Knowledge file '{p.name}' is not cataloged in '.md/knowledge/index.md'",
                        category="orphan_knowledge",
                        file_path=str(rel_path),
                    )
                )

        return issues

    def check_broken_knowledge_links(self) -> list[AuditIssue]:
        """Check internal links in active core documents (index.md, log.md, guidelines, root notes)."""
        issues: list[AuditIssue] = []
        if not self.knowledge_dir.exists():
            return issues

        # Only check active knowledge files (exclude historical issues and research archives)
        active_files = [
            self.index_file,
            self.log_file,
            self.knowledge_dir / "CONTEXT.md",
            self.knowledge_dir / "session_learnings.md",
            self.knowledge_dir / "guidelines" / "domain_success_criteria_rubrics.md",
        ]

        for p in active_files:
            if not p.exists() or not p.is_file():
                continue

            content = p.read_text(encoding="utf-8")
            for line_idx, line in enumerate(content.splitlines(), start=1):
                for match in LINK_RE.finditer(line):
                    raw_target = match.group(2).strip()
                    if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    if (
                        "..." in raw_target
                        or "example.com" in raw_target
                        or "path/to/" in raw_target
                    ):
                        continue

                    target_clean = raw_target.split("#")[0].split("?")[0]
                    if not target_clean:
                        continue

                    if target_clean.startswith("file://"):
                        clean_path = target_clean.replace("file:///", "").replace("file://", "")
                        target_path = Path(clean_path).resolve()
                    else:
                        target_path = (p.parent / target_clean).resolve()

                    if not target_path.exists():
                        rel_path = (
                            p.relative_to(self.project_root)
                            if p.is_relative_to(self.project_root)
                            else p
                        )
                        issues.append(
                            AuditIssue(
                                line_number=line_idx,
                                subject="Broken Knowledge Link",
                                message=f"Broken link in active doc to non-existent target '{raw_target}'",
                                category="broken_knowledge_link",
                                file_path=str(rel_path),
                            )
                        )

        return issues

    def audit(self, target: Any = None) -> list[AuditIssue]:
        """Perform comprehensive LLM-Wiki health audit."""
        issues: list[AuditIssue] = []
        issues.extend(self.check_index_integrity())
        issues.extend(self.check_log_schema())
        issues.extend(self.check_orphan_knowledge_files())
        issues.extend(self.check_broken_knowledge_links())
        return issues


def main() -> int:
    """CLI execution entrypoint for wiki health linter."""
    linter = WikiHealthLinter()
    issues = linter.audit()

    print("=" * 60)
    print("🧠 CCBA LLM-WIKI KNOWLEDGE HEALTH LINTER")
    print("=" * 60)

    if not issues:
        print("✅ Tất cả các tệp tri thức LLM-Wiki đều đạt 100% chuẩn sức khỏe và liên kết!")
        return 0

    print(f"⚠️ Phát hiện {len(issues)} vấn đề trong LLM-Wiki:")
    for issue in issues:
        print(f"  - [{issue.category}] {issue.file_path}:{issue.line_number} -> {issue.message}")

    return 1 if any("Broken" in i.message or "Missing" in i.message for i in issues) else 0


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
