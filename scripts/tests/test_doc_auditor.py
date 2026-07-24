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
