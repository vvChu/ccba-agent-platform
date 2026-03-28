"""
Vietnamese Legal Document Linter.

Custom lint rules for Vietnamese legal documents (VN001-VN004).
"""

import re
from dataclasses import dataclass
from pathlib import Path

from mdconverter.plugins.vn_legal.detector import is_legal_document


@dataclass
class LintIssue:
    """A lint issue found in a document."""

    file: Path
    line: int
    rule_id: str
    message: str
    severity: str = "warning"


class VNLegalLinter:
    """Linter for Vietnamese legal documents."""

    def lint_file(self, file_path: Path) -> list[LintIssue]:
        """
        Lint a single file for Vietnamese legal document issues.

        Args:
            file_path: Path to the Markdown file.

        Returns:
            List of lint issues found.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

        if not is_legal_document(content):
            return []  # Only lint legal documents

        lines = content.splitlines()
        issues: list[LintIssue] = []

        issues.extend(self._check_vn001_merged_items(file_path, lines))
        issues.extend(self._check_vn002_numbering_reset(file_path, content))
        issues.extend(self._check_vn003_dieu_spacing(file_path, lines))
        issues.extend(self._check_vn004_diem_format(file_path, lines))

        return issues

    def _check_vn001_merged_items(self, file_path: Path, lines: list[str]) -> list[LintIssue]:
        """VN001: Detect merged list items (a, b, c on same line)."""
        issues: list[LintIssue] = []
        pattern = re.compile(r"^[a-d]\).*\s+[b-e]\)")

        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                issues.append(
                    LintIssue(
                        file=file_path,
                        line=i,
                        rule_id="VN001",
                        message="Merged list items detected. Items a), b), c) should be on separate lines.",
                    )
                )

        return issues

    def _check_vn002_numbering_reset(self, file_path: Path, content: str) -> list[LintIssue]:
        """VN002: Detect suspicious numbering resets."""
        issues: list[LintIssue] = []

        count_1 = len(re.findall(r"^1\.\s", content, re.MULTILINE))
        count_2 = len(re.findall(r"^2\.\s", content, re.MULTILINE))

        if count_1 > 5 and count_2 == 0:
            issues.append(
                LintIssue(
                    file=file_path,
                    line=1,
                    rule_id="VN002",
                    message=f"Suspicious numbering: {count_1}x '1.' found but no '2.'. Possible reset issue.",
                )
            )

        return issues

    def _check_vn003_dieu_spacing(self, file_path: Path, lines: list[str]) -> list[LintIssue]:
        """VN003: Check for missing blank line before 'Điều' headers."""
        issues: list[LintIssue] = []
        pattern = re.compile(r"^###\s+Điều\s+\d+")

        for i, line in enumerate(lines):
            if pattern.match(line):
                if i > 0 and lines[i - 1].strip() != "":
                    issues.append(
                        LintIssue(
                            file=file_path,
                            line=i + 1,
                            rule_id="VN003",
                            message="Missing blank line before 'Điều' header.",
                        )
                    )

        return issues

    def _check_vn004_diem_format(self, file_path: Path, lines: list[str]) -> list[LintIssue]:
        """VN004: Check for incorrect 'Điểm' format."""
        issues: list[LintIssue] = []
        pattern = re.compile(r"^-\s*[a-d]\)")

        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                issues.append(
                    LintIssue(
                        file=file_path,
                        line=i,
                        rule_id="VN004",
                        message="Incorrect 'Điểm' format. Use 'a)' instead of '- a)'.",
                    )
                )

        return issues

    def lint_directory(self, directory: Path) -> list[LintIssue]:
        """Lint all Markdown files in a directory."""
        all_issues: list[LintIssue] = []

        for md_file in directory.rglob("*.md"):
            if "legacy" in str(md_file) or "node_modules" in str(md_file):
                continue
            all_issues.extend(self.lint_file(md_file))

        return all_issues
