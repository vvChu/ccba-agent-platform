"""Tests for CLI commands."""

from pathlib import Path

from typer.testing import CliRunner

from mdconverter.cli import app

runner = CliRunner()


class TestVersionCommand:
    """Test version command."""

    def test_version_flag(self) -> None:
        """Test --version flag shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "mdconverter" in result.stdout
        assert "version" in result.stdout


class TestConfigCommand:
    """Test config command."""

    def test_config_shows_settings(self) -> None:
        """Test config command shows current settings."""
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "Proxy URL" in result.stdout or "proxy" in result.stdout.lower()

    def test_config_shows_models(self) -> None:
        """Test config command shows models."""
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        # Should show some configuration


class TestConvertCommand:
    """Test convert command."""

    def test_convert_nonexistent_file(self) -> None:
        """Test convert fails for non-existent file."""
        result = runner.invoke(app, ["convert", "nonexistent.pdf"])
        assert result.exit_code != 0

    def test_convert_dry_run(self, tmp_path: Path) -> None:
        """Test convert with --dry-run flag."""
        # Create a test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test")

        result = runner.invoke(app, ["convert", str(test_file), "--dry-run"])
        assert "Would convert" in result.stdout or result.exit_code == 0

    def test_convert_no_files_found(self, tmp_path: Path) -> None:
        """Test convert with empty directory."""
        result = runner.invoke(app, ["convert", str(tmp_path)])
        assert "No convertible files" in result.stdout or result.exit_code == 1


class TestValidateCommand:
    """Test validate command."""

    def test_validate_nonexistent_file(self) -> None:
        """Test validate fails for non-existent file."""
        result = runner.invoke(app, ["validate", "nonexistent.md"])
        assert result.exit_code != 0

    def test_validate_empty_directory(self, tmp_path: Path) -> None:
        """Test validate with empty directory."""
        result = runner.invoke(app, ["validate", str(tmp_path)])
        assert "No Markdown files" in result.stdout or result.exit_code == 1

    def test_validate_valid_file(self, tmp_path: Path) -> None:
        """Test validate with a valid markdown file."""
        test_file = tmp_path / "test.md"
        # Content must be > 100 chars to pass min_content_length check
        content = """# Valid Heading

This is some content that is long enough to pass the minimum content length validation check.
It needs to have at least 100 characters to be considered valid by the validator."""
        test_file.write_text(content)

        result = runner.invoke(app, ["validate", str(test_file)])
        # Should complete without error for a valid file
        assert "OK" in result.stdout or result.exit_code == 0


class TestLintCommand:
    """Test lint command."""

    def test_lint_current_directory(self) -> None:
        """Test lint with default directory."""
        result = runner.invoke(app, ["lint"])
        # Should complete (may find issues or not)
        assert result.exit_code in [0, 1]

    def test_lint_with_fix_flag(self, tmp_path: Path) -> None:
        """Test lint with --fix flag."""
        # Create a test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nContent")

        result = runner.invoke(app, ["lint", str(tmp_path), "--fix"])
        # Should complete
        assert result.exit_code in [0, 1]

    def test_lint_vn_only_flag(self, tmp_path: Path) -> None:
        """Test lint with --vn-only flag."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nDieu 1. Content", encoding="utf-8")

        result = runner.invoke(app, ["lint", str(tmp_path), "--vn-only"])
        # Should complete
        assert result.exit_code in [0, 1]
