"""Unit tests for safe_pytest.py wrapper script."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from safe_pytest import find_modified_test_files, main

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_find_modified_test_files():
    """Test git status parsing for test files."""
    mock_git_output = (
        " M scripts/safe_pytest.py\n"
        " M scripts/tests/test_doc_auditor.py\n"
        "?? tests/test_new_feature.py\n"
        " M README.md\n"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_git_output, returncode=0)
        with patch("pathlib.Path.exists", return_value=True):
            test_files = find_modified_test_files()
            normalized = [Path(f).as_posix() for f in test_files]
            assert "scripts/tests/test_doc_auditor.py" in normalized
            assert "tests/test_new_feature.py" in normalized
            assert "scripts/safe_pytest.py" not in normalized


def test_dry_run_mode(capsys):
    """Test --dry-run option prints command without execution."""
    with patch(
        "sys.argv",
        ["safe_pytest.py", "-f", "tests/test_demo.py", "--dry-run"],
    ):
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert "[SafePytest DRY-RUN] Planned execution:" in captured.out
        assert "tests/test_demo.py" in captured.out
