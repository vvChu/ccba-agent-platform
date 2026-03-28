"""Tests for VN Legal Linter."""

from pathlib import Path

from mdconverter.plugins.vn_legal.linter import LintIssue, VNLegalLinter


class TestLintIssue:
    """Test LintIssue dataclass."""

    def test_lint_issue_creation(self) -> None:
        """Test LintIssue can be created."""
        issue = LintIssue(
            file=Path("test.md"),
            line=10,
            rule_id="VN001",
            message="Test message",
        )
        assert issue.file == Path("test.md")
        assert issue.line == 10
        assert issue.rule_id == "VN001"
        assert issue.message == "Test message"

    def test_lint_issue_default_severity(self) -> None:
        """Test LintIssue has default severity."""
        issue = LintIssue(
            file=Path("test.md"),
            line=1,
            rule_id="VN001",
            message="Test",
        )
        assert issue.severity == "warning"


class TestVNLegalLinter:
    """Test VNLegalLinter class."""

    def test_lint_file_nonexistent(self) -> None:
        """Test linting non-existent file returns empty list."""
        linter = VNLegalLinter()
        issues = linter.lint_file(Path("nonexistent.md"))
        assert issues == []

    def test_lint_directory_empty(self, tmp_path: Path) -> None:
        """Test linting empty directory returns empty list."""
        linter = VNLegalLinter()
        issues = linter.lint_directory(tmp_path)
        assert issues == []

    def test_linter_has_lint_file_method(self) -> None:
        """Test VNLegalLinter has lint_file method."""
        linter = VNLegalLinter()
        assert hasattr(linter, "lint_file")
        assert callable(linter.lint_file)

    def test_linter_has_lint_directory_method(self) -> None:
        """Test VNLegalLinter has lint_directory method."""
        linter = VNLegalLinter()
        assert hasattr(linter, "lint_directory")
        assert callable(linter.lint_directory)
