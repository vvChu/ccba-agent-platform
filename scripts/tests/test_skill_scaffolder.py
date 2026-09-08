"""test_skill_scaffolder.py - Unit tests for autonomous skill scaffolder.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.governance import SkillAuditor
from scripts.scaffolding import (
    create_skill_from_script,
    inspect_via_static_ast,
)


class TestSkillScaffolder(unittest.TestCase):
    """Unit test suite for skill generator and scaffolder."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_inspect_via_static_ast(self) -> None:
        """Test static AST parsing of an argparse script."""
        mock_script = self.root / "mock_tool.py"
        mock_script.write_text(
            '''"""Mock tool description for test."""
import argparse

parser = argparse.ArgumentParser(description="Mock CLI")
parser.add_argument("--source", required=True, help="Path to input source")
parser.add_argument("--count", type=int, default=10, help="Number of items")
parser.add_argument("--format", choices=["json", "yaml"], default="json", help="Output format")
''',
            encoding="utf-8",
        )

        cmd_base, commands, docstring = inspect_via_static_ast(mock_script)
        self.assertIn("mock_tool.py", cmd_base)
        self.assertEqual(docstring, "Mock tool description for test.")
        self.assertIn("default", commands)

        schema = commands["default"]["input_schema"]
        props = schema["properties"]
        self.assertIn("source", props)
        self.assertIn("count", props)
        self.assertIn("format", props)
        self.assertEqual(props["count"]["type"], "integer")
        self.assertEqual(props["format"]["enum"], ["json", "yaml"])
        self.assertIn("source", schema["required"])

    def test_create_skill_generation(self) -> None:
        """Test create_skill_from_script generating valid SKILL.md and cli_spec.yaml (no workflow router per ADR-0057)."""
        mock_script = self.root / "sample_converter.py"
        mock_script.write_text(
            '''"""Sample document converter script."""
import argparse

def get_parser():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Input file path")
    return p
''',
            encoding="utf-8",
        )

        skills_dir = self.root / "skills"
        workflows_dir = self.root / "workflows"

        res = create_skill_from_script(
            script_path_str=mock_script,
            skill_name="sample-converter",
            skills_base_dir=skills_dir,
            workflows_base_dir=workflows_dir,
        )
        self.assertEqual(res, 0)

        skill_dir = skills_dir / "ccba-sample-converter"
        skill_file = skill_dir / "SKILL.md"
        cli_spec_file = skill_dir / "cli_spec.yaml"
        workflow_file = workflows_dir / "ccba-sample-converter.md"

        self.assertTrue(skill_file.exists())
        self.assertTrue(cli_spec_file.exists())
        # Per ADR-0057, parallel workflow router is deprecated and no longer created
        self.assertFalse(workflow_file.exists())

        # Verify generated SKILL.md passes SkillAuditor with zero errors
        auditor = SkillAuditor(project_root=self.root)
        issues = auditor.audit_skill(skill_file)
        self.assertEqual(len(issues), 0, f"Generated SKILL.md had issues: {issues}")

    def test_create_skill_with_gpi_and_enforce_gpi(self) -> None:
        """Test skill generation with GPI >= 12.0 and verification with enforce_gpi=True."""
        mock_script = self.root / "smart_tool.py"
        mock_script.write_text(
            '''"""Smart analysis tool."""
import argparse
parser = argparse.ArgumentParser(description="Smart tool")
parser.add_argument("--query", required=True, help="Query")
''',
            encoding="utf-8",
        )
        skills_dir = self.root / "skills"
        res = create_skill_from_script(
            script_path_str=mock_script,
            skill_name="smart-tool",
            skills_base_dir=skills_dir,
            s=4.0,
            k=3.0,
            a=4.0,
            p=1.0,
        )
        self.assertEqual(res, 0)
        skill_file = skills_dir / "ccba-smart-tool" / "SKILL.md"
        self.assertTrue(skill_file.exists())
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("gpi:", content)
        self.assertIn("s: 4.0", content)

        auditor = SkillAuditor(project_root=self.root)
        issues = auditor.audit_skill(skill_file, enforce_gpi=True)
        self.assertEqual(len(issues), 0, f"GPI enforced audit failed: {issues}")

    def test_gate_0_and_1_invariants(self) -> None:
        """Test Gate 0 and Gate 1 rejection logic."""
        mock_script = self.root / "any_script.py"
        mock_script.write_text('"""Doc."""\n', encoding="utf-8")
        skills_dir = self.root / "skills"

        # Gate 0
        res0 = create_skill_from_script(
            mock_script, skills_base_dir=skills_dir, is_deterministic=True
        )
        self.assertEqual(res0, 1)

        # Gate 1
        res1 = create_skill_from_script(
            mock_script, skills_base_dir=skills_dir, is_orchestrated=True
        )
        self.assertEqual(res1, 1)

    def test_sub_threshold_gpi_creates_reference(self) -> None:
        """Test sub-threshold GPI creates reference under parent master skill."""
        mock_script = self.root / "table_extractor.py"
        mock_script.write_text('"""Extract tables."""\n', encoding="utf-8")
        skills_dir = self.root / "skills"

        parent_dir = skills_dir / "ccba-doc-processor"
        parent_dir.mkdir(parents=True)
        (parent_dir / "SKILL.md").write_text(
            "---\nname: ccba-doc-processor\n---\n", encoding="utf-8"
        )

        res = create_skill_from_script(
            mock_script,
            skill_name="table-extractor",
            skills_base_dir=skills_dir,
            s=1.0,
            k=1.0,
            a=1.0,
            p=5.0,
            parent="ccba-doc-processor",
        )
        self.assertEqual(res, 0)
        ref_file = parent_dir / "references" / "table-extractor.md"
        self.assertTrue(ref_file.exists())
        content = ref_file.read_text(encoding="utf-8")
        self.assertIn("Tier 2A (Progressive Reference)", content)


if __name__ == "__main__":
    unittest.main()
