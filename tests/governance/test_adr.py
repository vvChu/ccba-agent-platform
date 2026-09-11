import tempfile
from unittest.mock import patch

import pytest
from scripts.governance.adr_generator import ADRGenerator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_adr_generation() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ADRGenerator(repo_dir=temp_dir)

        # Test directory auto creation
        title = "Test ADR Generation"
        context = "We need to test the automated ADR creation."
        decision = "Implement unit tests for ADRGenerator."
        consequences = "ADR folder contains structured decisions."

        adr_file = generator.generate_adr(title, context, decision, consequences)
        assert adr_file is not None
        assert adr_file.exists()

        content = adr_file.read_text(encoding="utf-8")
        assert "HUB-ADR: Test ADR Generation" in content
        assert "Bối cảnh" in content
        assert "Quyết định" in content
        assert "Hệ quả & Đánh đổi" in content


def test_detect_architectural_changes_empty() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ADRGenerator(repo_dir=temp_dir)
        with patch.object(generator, "get_git_diff_summary", return_value=""):
            changes = generator.detect_architectural_changes()
            assert len(changes) == 0


def test_detect_architectural_changes_mock() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ADRGenerator(repo_dir=temp_dir)
        mock_diff = "M  pyproject.toml\nA  scripts/governance/adr_generator.py\nM  secret.db"
        with patch.object(generator, "get_git_diff_summary", return_value=mock_diff):
            changes = generator.detect_architectural_changes()
            assert len(changes) == 3
            assert any("pyproject.toml" in c for c in changes)
            assert any("adr_generator.py" in c for c in changes)
            assert any("secret.db" in c for c in changes)
