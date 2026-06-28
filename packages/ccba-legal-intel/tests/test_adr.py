import tempfile

from ccba_legal.adr import ADRGenerator


def test_adr_generation():
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
        assert "ADR: Test ADR Generation" in content
        assert "Bối cảnh" in content
        assert "Quyết định" in content
        assert "Hệ quả & Đánh đổi" in content


def test_detect_architectural_changes_empty():
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ADRGenerator(repo_dir=temp_dir)
        # Mock get_git_diff_summary to return empty string
        generator.get_git_diff_summary = lambda: ""
        changes = generator.detect_architectural_changes()
        assert len(changes) == 0


def test_detect_architectural_changes_mock():
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ADRGenerator(repo_dir=temp_dir)
        generator.get_git_diff_summary = lambda: (
            "M  pyproject.toml\nA  packages/ccba-legal-intel/ccba_legal/adr.py\nM  secret.db"
        )
        changes = generator.detect_architectural_changes()
        assert len(changes) == 3
        assert any("pyproject.toml" in c for c in changes)
        assert any("adr.py" in c for c in changes)
        assert any("secret.db" in c for c in changes)
