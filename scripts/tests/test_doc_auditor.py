"""test_doc_auditor.py - Unit tests for DocumentAuditor deep module."""

import sys
import tempfile
import unittest
from pathlib import Path

# Ensure scripts directory is in sys.path
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from doc_auditor import DocumentAuditor


class TestDocumentAuditor(unittest.TestCase):
    def setUp(self) -> None:
        self.auditor = DocumentAuditor()

    def test_parse_frontmatter(self) -> None:
        content = "---\nname: test-skill\ndescription: Test description\n---\n# Header"
        fm, body = self.auditor.parse_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("name"), "test-skill")
        self.assertIn("# Header", body)

    def test_extract_code_references(self) -> None:
        content = "Call `process_data()` or use `DataProcessor` class."
        refs = self.auditor.extract_code_references(content)
        ref_names = [r[1] for r in refs]
        self.assertIn("process_data()", ref_names)
        self.assertIn("DataProcessor", ref_names)

    def test_extract_internal_links(self) -> None:
        content = "See [doc](file.md) and [site](https://example.com) and [anchor](#section)."
        links = self.auditor.extract_internal_links(content)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0][1], "doc")
        self.assertEqual(links[0][2], "file.md")

    def test_extract_env_variables(self) -> None:
        content = "Use `MY_CUSTOM_VAR` or `$OTHER_SECRET_KEY` in environment."
        env_vars = self.auditor.extract_env_variables(content)
        var_names = [v[1] for v in env_vars]
        self.assertIn("MY_CUSTOM_VAR", var_names)
        self.assertIn("OTHER_SECRET_KEY", var_names)

    def test_audit_valid_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: my-skill\ndescription: Valid short description.\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertEqual(len(issues), 0)

    def test_audit_skill_missing_completion_criterion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: my-skill\ndescription: Short description.\n---\n"
                "# Workflow\n1. Step without completion criterion",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertTrue(any("missing a Completion Criterion" in i.message for i in issues))

    def test_validate_markdown_file_broken_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("[link](non_existent_file.md)", encoding="utf-8")
            auditor = DocumentAuditor(project_root=Path(tmpdir))
            issues = auditor.validate_markdown_file(file_path)
            self.assertTrue(len(issues["links"]) > 0)
            self.assertIn("File does not exist", issues["links"][0][2])

    def test_run_skills_validation_cli_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills" / "my-skill"
            skills_dir.mkdir(parents=True)
            skill_file = skills_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: my-skill\ndescription: Short description.\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            auditor = DocumentAuditor(project_root=Path(tmpdir))
            exit_code = auditor.run_skills_validation_cli([str(skills_dir.parent)])
            self.assertEqual(exit_code, 0)
