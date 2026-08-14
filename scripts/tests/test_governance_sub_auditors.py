"""test_governance_sub_auditors.py - Deep Unit Tests for Governance Sub-Auditors.

Verifies isolated behavior of LinkAuditor, SkillAuditor, RegistryAuditor,
EnvAuditor, DriftAuditor, and DocumentAuditor Coordinator.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.governance import (
    AuditIssue,
    AuditReport,
    BaseAuditor,
    DocumentAuditor,
    DriftAuditor,
    EnvAuditor,
    LinkAuditor,
    RegistryAuditor,
    SkillAuditor,
)


class TestGovernanceSubAuditors(unittest.TestCase):
    """Unit test suite for isolated governance sub-auditors."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_link_auditor_link_extraction_and_autofix(self) -> None:
        """Test LinkAuditor extracting links and auto-fixing non-portable file:/// links."""
        auditor = LinkAuditor(project_root=self.root)
        doc_dir = self.root / "docs"
        doc_dir.mkdir(parents=True)
        target_file = self.root / "README.md"
        target_file.write_text("# Readme\n", encoding="utf-8")

        test_md = doc_dir / "guide.md"
        # Content with absolute file:/// link
        abs_link = f"file:///{target_file.as_posix()}"
        content = f"# Guide\nSee [Readme]({abs_link}) for details.\n"
        test_md.write_text(content, encoding="utf-8")

        # 1. Validation without fix
        issues = auditor.validate_markdown_file(test_md, fix=False)
        self.assertTrue(len(issues["links"]) > 0)
        self.assertIn("Non-portable absolute file link", issues["links"][0][2])

        # 2. Validation with fix
        fixed, fix_issues = auditor.fix_relative_links(test_md)
        self.assertTrue(fixed)
        fixed_content = test_md.read_text(encoding="utf-8")
        self.assertIn("](../README.md)", fixed_content)
        self.assertNotIn("file:///", fixed_content)

    def test_link_auditor_code_symbol_extraction(self) -> None:
        """Test LinkAuditor extracting code symbols while ignoring keywords."""
        auditor = LinkAuditor(project_root=self.root)
        content = """
        Use `my_custom_function()` and `CustomClass` to build the app.
        Ignore `const`, `return`, `async`, and `true`.
        """
        refs = auditor.extract_code_references(content)
        symbols = [ref for _, ref in refs]
        self.assertIn("my_custom_function()", symbols)
        self.assertIn("CustomClass", symbols)
        self.assertNotIn("const", symbols)
        self.assertNotIn("return", symbols)
        self.assertNotIn("true", symbols)

    def test_skill_auditor_frontmatter_and_criteria(self) -> None:
        """Test SkillAuditor validating frontmatter and missing step criteria."""
        auditor = SkillAuditor(project_root=self.root)
        skill_dir = self.root / ".agents" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"

        # Missing completion criteria in workflow steps
        skill_md.write_text(
            """---
name: my-skill
description: Short description
---

# My Skill

## Workflow

1. Step one without criteria.
""",
            encoding="utf-8",
        )

        issues = auditor.audit_skill(skill_md)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("missing a Completion Criterion" in i.message for i in issues))

        # Add valid completion criterion
        skill_md.write_text(
            """---
name: my-skill
description: Short description
---

# My Skill

## Workflow

1. Step one with criteria.
   - **Completion Criterion:** Done.
""",
            encoding="utf-8",
        )
        issues = auditor.audit_skill(skill_md)
        self.assertEqual(len(issues), 0)

    def test_skill_auditor_character_limit(self) -> None:
        """Test SkillAuditor enforcing 180 character limit on model-invoked skills."""
        auditor = SkillAuditor(project_root=self.root)
        skill_file = self.root / "SKILL.md"
        long_desc = "A" * 200

        skill_file.write_text(
            f"""---
name: long-skill
description: {long_desc}
---
# Long Skill
""",
            encoding="utf-8",
        )

        issues = auditor.audit_skill(skill_file)
        self.assertTrue(any("exceeds 180 character limit" in i.message for i in issues))

        # If disable-model-invocation: true, no limit error
        skill_file.write_text(
            f"""---
name: long-skill
description: {long_desc}
disable-model-invocation: true
---
# Long Skill
""",
            encoding="utf-8",
        )
        issues = auditor.audit_skill(skill_file)
        self.assertFalse(any("exceeds 180 character limit" in i.message for i in issues))

    def test_registry_auditor_orphan_scan(self) -> None:
        """Test RegistryAuditor scanning orphan files in bundle."""
        auditor = RegistryAuditor(project_root=self.root)
        bundle_dir = self.root / "legal_docs" / "bundle_1"
        bundle_dir.mkdir(parents=True)

        index_md = bundle_dir / "index.md"
        ref_doc = bundle_dir / "referenced.md"
        orphan_doc = bundle_dir / "orphan.md"

        index_md.write_text("# Index\n[Ref](referenced.md)\n", encoding="utf-8")
        ref_doc.write_text("# Referenced doc\n", encoding="utf-8")
        orphan_doc.write_text("# Unreferenced orphan\n", encoding="utf-8")

        orphans = auditor.scan_orphan_files(bundle_dir)
        orphan_names = [p.name for p in orphans]
        self.assertIn("orphan.md", orphan_names)
        self.assertNotIn("referenced.md", orphan_names)
        self.assertNotIn("index.md", orphan_names)

    def test_env_auditor_missing_vars(self) -> None:
        """Test EnvAuditor detecting variables missing from .env.example."""
        auditor = EnvAuditor(project_root=self.root)
        env_example = self.root / ".env.example"
        env_example.write_text("KNOWN_API_KEY=xxx\n", encoding="utf-8")

        content = "Use `KNOWN_API_KEY` and `$SECRET_TOKEN` in requests."
        issues = auditor.audit(content)
        issue_subjects = [i.subject for i in issues]
        self.assertIn("SECRET_TOKEN", issue_subjects)
        self.assertNotIn("KNOWN_API_KEY", issue_subjects)

    def test_coordinator_integration(self) -> None:
        """Test DocumentAuditor coordinator delegating to sub-auditors."""
        coordinator = DocumentAuditor(project_root=self.root)
        self.assertIsInstance(coordinator, BaseAuditor)
        self.assertIsNotNone(coordinator.link_auditor)
        self.assertIsNotNone(coordinator.skill_auditor)
        self.assertIsNotNone(coordinator.registry_auditor)
        self.assertIsNotNone(coordinator.env_auditor)
        self.assertIsNotNone(coordinator.drift_auditor)

        # Ensure DocumentAuditor delegates correctly
        report = coordinator.audit_documents()
        self.assertIsInstance(report, AuditReport)
        self.assertIsInstance(report.issues, list)


if __name__ == "__main__":
    unittest.main()
