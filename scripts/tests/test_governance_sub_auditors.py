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
    AuditReport,
    BaseAuditor,
    DocumentAuditor,
    DriftAuditor,
    EnvAuditor,
    LinkAuditor,
    RegistryAuditor,
    SkillAuditor,
    is_structural_path,
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
        skill_dir = self.root / ".agents" / "skills" / "ccba-my-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"

        # Missing completion criteria in workflow steps
        skill_md.write_text(
            """---
name: ccba-my-skill
description: Short description
bundle: _core
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
name: ccba-my-skill
description: Short description
bundle: _core
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
name: ccba-long-skill
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
name: ccba-long-skill
description: {long_desc}
disable-model-invocation: true
---
# Long Skill
""",
            encoding="utf-8",
        )
        issues = auditor.audit_skill(skill_file)
        self.assertFalse(any("exceeds 180 character limit" in i.message for i in issues))

    def test_skill_auditor_namespace_purity(self) -> None:
        """Test SkillAuditor enforcing ADR-0056 namespace purity gate."""
        auditor = SkillAuditor(project_root=self.root)
        skill_file = self.root / "SKILL.md"

        # Invalid namespaces: legacy skills and prefixed platform-loader-*
        for invalid_name in [
            "unapproved-legacy-skill",
            "platform-loader-fake",
            "platform-loader-something",
            "ask",
        ]:
            skill_file.write_text(
                f"""---
name: {invalid_name}
description: Valid description
---
# Test
""",
                encoding="utf-8",
            )
            issues = auditor.audit_skill(skill_file)
            self.assertTrue(
                any(i.category == "INVALID_NAMESPACE" for i in issues),
                f"Invalid name '{invalid_name}' was unexpectedly accepted",
            )

        # Valid namespaces: ccba-*, bigbim-*, platform-loader
        for valid_name in ["ccba-valid-skill", "bigbim-test", "platform-loader"]:
            skill_file.write_text(
                f"""---
name: {valid_name}
description: Valid description
---
# Test
""",
                encoding="utf-8",
            )
            issues = auditor.audit_skill(skill_file)
            self.assertFalse(
                any(i.category == "INVALID_NAMESPACE" for i in issues),
                f"Valid name {valid_name} unexpectedly failed namespace purity",
            )

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

    def test_link_auditor_dynamic_skill_scope(self) -> None:
        """Test LinkAuditor dynamically discovering skill scripts for skill docs but not global docs."""
        auditor = LinkAuditor(project_root=self.root)

        # 1. Create a skill with internal script
        skill_dir = self.root / ".agents" / "skills" / "demo-skill"
        skill_scripts = skill_dir / "scripts"
        skill_scripts.mkdir(parents=True)
        (skill_scripts / "helper.py").write_text("def demo_skill_func(): pass\n", encoding="utf-8")

        # Skill doc referencing demo_skill_func
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Demo Skill\nCall `demo_skill_func()` here.\n", encoding="utf-8")

        # Global doc outside .agents referencing demo_skill_func
        docs_dir = self.root / "docs"
        docs_dir.mkdir(parents=True)
        global_md = docs_dir / "guide.md"
        global_md.write_text("# Global Guide\nCall `demo_skill_func()` here.\n", encoding="utf-8")

        # 2. Skill doc should find the symbol
        skill_issues = auditor.validate_markdown_file(skill_md)
        self.assertEqual(len(skill_issues["code_refs"]), 0)

        # 3. Global doc should NOT find the symbol (isolated)
        global_issues = auditor.validate_markdown_file(global_md)
        self.assertEqual(len(global_issues["code_refs"]), 1)
        self.assertIn("Symbol is not defined in codebase", global_issues["code_refs"][0][2])

    def test_link_auditor_scoped_cache_isolation(self) -> None:
        """Test that symbol cache is scoped to search_dirs and does not leak across scopes."""
        auditor = LinkAuditor(project_root=self.root)

        skill_dir = self.root / ".agents" / "skills" / "cache-skill"
        skill_scripts = skill_dir / "scripts"
        skill_scripts.mkdir(parents=True)
        (skill_scripts / "worker.py").write_text(
            "class UniqueSkillWorker: pass\n", encoding="utf-8"
        )

        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Cache Skill\nUse `UniqueSkillWorker` here.\n", encoding="utf-8")

        global_md = self.root / "README.md"
        global_md.write_text("# Project\nUse `UniqueSkillWorker` here.\n", encoding="utf-8")

        # 1. Audit skill doc first -> caches (UniqueSkillWorker, (skill_scope...)) = True
        skill_issues = auditor.validate_markdown_file(skill_md)
        self.assertEqual(len(skill_issues["code_refs"]), 0)

        # 2. Audit global doc immediately -> must check (UniqueSkillWorker, (global_scope...)) -> False
        global_issues = auditor.validate_markdown_file(global_md)
        self.assertEqual(len(global_issues["code_refs"]), 1)
        self.assertIn("Symbol is not defined in codebase", global_issues["code_refs"][0][2])

    def test_link_auditor_excludes_safety(self) -> None:
        """Test LinkAuditor safely excludes non-code directories like .md/ and .git/."""
        auditor = LinkAuditor(project_root=self.root)

        # Create valid core package code
        pkg_dir = self.root / "packages" / "pkg1" / "src" / "pkg1"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "core.py").write_text("class ValidCoreClass: pass\n", encoding="utf-8")

        # Create fake code in .md directory
        md_scratch = self.root / ".md" / "scratch"
        md_scratch.mkdir(parents=True)
        (md_scratch / "temp.py").write_text("class ExcludedTempClass: pass\n", encoding="utf-8")

        self.assertTrue(auditor.search_codebase_for_symbol("ValidCoreClass"))
        self.assertFalse(auditor.search_codebase_for_symbol("ExcludedTempClass"))

    def test_link_auditor_dynamic_skill_scope_with_explicit_search_dirs(self) -> None:
        """Test Dynamic Skill Scope activates even when search_dirs is explicitly provided."""
        auditor = LinkAuditor(project_root=self.root)

        skill_dir = self.root / ".agents" / "skills" / "explicit-skill"
        skill_scripts = skill_dir / "scripts"
        skill_scripts.mkdir(parents=True)
        (skill_scripts / "helper.py").write_text(
            "class ExplicitSkillHelper: pass\n", encoding="utf-8"
        )

        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Skill\nCall `ExplicitSkillHelper` here.\n", encoding="utf-8")

        # Explicit search_dirs passed (e.g. from CLI or custom runner)
        custom_search_dirs = [self.root / "src"]
        issues = auditor.validate_markdown_file(skill_md, search_dirs=custom_search_dirs)
        self.assertEqual(len(issues["code_refs"]), 0)

    def test_link_auditor_project_root_search_excludes_agents(self) -> None:
        """Test scanning project_root excludes .agents to prevent leaking skill symbols into global scope."""
        auditor = LinkAuditor(project_root=self.root)

        skill_dir = self.root / ".agents" / "skills" / "isolated-skill"
        skill_scripts = skill_dir / "scripts"
        skill_scripts.mkdir(parents=True)
        (skill_scripts / "isolated.py").write_text(
            "class IsolatedSkillLocalClass: pass\n", encoding="utf-8"
        )

        # Direct search with project_root must NOT find symbol inside .agents
        self.assertFalse(
            auditor.search_codebase_for_symbol("IsolatedSkillLocalClass", search_dirs=[self.root])
        )

    def test_drift_auditor_structural_path_classification(self) -> None:
        """Test is_structural_path correctly classifies Level-1 paths vs internal sub-resources."""
        # Level-1 structural paths
        self.assertTrue(is_structural_path("pyproject.toml"))
        self.assertTrue(is_structural_path("packages/ccba-core/pyproject.toml"))
        self.assertTrue(is_structural_path(".agents/skills/ccba-test-skill/SKILL.md"))
        self.assertTrue(is_structural_path(".agents/workflows/deploy.md"))
        self.assertTrue(is_structural_path("scripts/update_arch_stats.py"))

        # Level-1 structural paths with quotes or whitespace
        self.assertTrue(is_structural_path('"pyproject.toml"'))
        self.assertTrue(is_structural_path('  ".agents/skills/ccba-test-skill/SKILL.md"  '))
        self.assertTrue(is_structural_path("  scripts/update_arch_stats.py  "))

        # Ignored non-structural or internal paths
        self.assertFalse(is_structural_path(".agents/workflows/deploy.md.bak"))
        self.assertFalse(is_structural_path(".agents/skills/ccba-test-skill/test_cases/case1.py"))
        self.assertFalse(is_structural_path(".agents/skills/ccba-test-skill/references/doc.md"))
        self.assertFalse(is_structural_path(".agents/skills/ccba-test-skill/resources/schema.json"))
        self.assertFalse(is_structural_path(".agents/skills/ccba-test-skill/scripts/helper.py"))
        self.assertFalse(is_structural_path("packages/ccba-core/src/ccba_core/main.py"))
        self.assertFalse(is_structural_path("packages/ccba-core/tests/test_main.py"))
        self.assertFalse(is_structural_path("packages/ccba-core/test_cases/sample.json"))
        self.assertFalse(is_structural_path("scripts/governance/drift_auditor.py"))
        self.assertFalse(is_structural_path("scripts/tests/test_governance_sub_auditors.py"))
        self.assertFalse(is_structural_path("README.md"))

    def test_drift_auditor_detects_marker_mismatch(self) -> None:
        """Test DriftAuditor detecting mismatch between filesystem counts and doc markers."""
        auditor = DriftAuditor(project_root=self.root)

        # Create 1 skill and 0 packages
        skill_dir = self.root / ".agents" / "skills" / "ccba-test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: ccba-test-skill\n---\n", encoding="utf-8")

        # Create README.md with outdated marker SKILL_COUNT=10 (actual is 1)
        readme = self.root / "README.md"
        readme.write_text(
            "# Platform\nSkills: <!-- SKILL_COUNT_START -->10<!-- SKILL_COUNT_END -->\n",
            encoding="utf-8",
        )

        # Create PLATFORM.md with outdated marker PACKAGE_COUNT=5 (actual is 0)
        platform_md = self.root / "PLATFORM.md"
        platform_md.write_text(
            "# Architecture\nPackages: <!-- PACKAGE_COUNT_START -->5<!-- PACKAGE_COUNT_END -->\n",
            encoding="utf-8",
        )

        # 1. Layer 1 check detects mismatch
        marker_issues = auditor.check_marker_drift(docs=[readme, platform_md])
        self.assertEqual(len(marker_issues), 2)
        self.assertTrue(
            any("SKILL_COUNT is '10', but actual count is '1'" in err for err in marker_issues)
        )
        self.assertTrue(
            any("PACKAGE_COUNT is '5', but actual count is '0'" in err for err in marker_issues)
        )

        # Combined check also reports marker drift
        combined_issues = auditor.check_architecture_drift()
        self.assertTrue(any("SKILL_COUNT is '10'" in err for err in combined_issues))

        # 2. Fix markers -> zero drift
        readme.write_text(
            "# Platform\nSkills: <!-- SKILL_COUNT_START -->1<!-- SKILL_COUNT_END -->\n",
            encoding="utf-8",
        )
        platform_md.write_text(
            "# Architecture\nPackages: <!-- PACKAGE_COUNT_START -->0<!-- PACKAGE_COUNT_END -->\n",
            encoding="utf-8",
        )
        clean_issues = auditor.check_marker_drift(docs=[readme, platform_md])
        self.assertEqual(len(clean_issues), 0)

    def test_drift_auditor_ignores_intra_skill_test_cases(self) -> None:
        """Test DriftAuditor ignoring internal sub-resources (test_cases/, references/, src/)."""
        import subprocess

        # Initialize git repo in self.root
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=self.root, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.root,
            capture_output=True,
            check=True,
        )

        # Create initial baseline commit with README
        readme = self.root / "README.md"
        readme.write_text("# Readme\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"], cwd=self.root, capture_output=True, check=True
        )

        # Add subdirectories and internal files inside skill
        skill_dir = self.root / ".agents" / "skills" / "ccba-skill-repair"
        (skill_dir / "test_cases").mkdir(parents=True)
        (skill_dir / "references").mkdir(parents=True)
        (skill_dir / "resources").mkdir(parents=True)

        (skill_dir / "test_cases" / "test_sample.json").write_text("{}", encoding="utf-8")
        (skill_dir / "references" / "guide.md").write_text("# Guide", encoding="utf-8")
        (skill_dir / "resources" / "data.csv").write_text("a,b", encoding="utf-8")

        # Also add internal files in an existing package
        pkg_src = self.root / "packages" / "ccba-test" / "src" / "ccba_test"
        pkg_src.mkdir(parents=True)
        (pkg_src / "module.py").write_text("x = 1\n", encoding="utf-8")

        auditor = DriftAuditor(project_root=self.root)
        structural_errors = auditor.check_structural_git_drift()
        self.assertEqual(len(structural_errors), 0)

    def test_drift_auditor_detects_new_skill_without_doc_update(self) -> None:
        """Test DriftAuditor detecting new skill SKILL.md without updating architecture docs."""
        import subprocess

        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=self.root, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.root,
            capture_output=True,
            check=True,
        )

        readme = self.root / "README.md"
        readme.write_text("# Readme\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"], cwd=self.root, capture_output=True, check=True
        )

        # Add new skill SKILL.md
        new_skill = self.root / ".agents" / "skills" / "ccba-brand-new-skill"
        new_skill.mkdir(parents=True)
        (new_skill / "SKILL.md").write_text(
            "---\nname: ccba-brand-new-skill\n---\n", encoding="utf-8"
        )

        auditor = DriftAuditor(project_root=self.root)
        drift_errors = auditor.check_structural_git_drift()
        self.assertTrue(len(drift_errors) > 0)
        self.assertIn("Structural drift detected", drift_errors[0])

    def test_drift_auditor_detects_new_package_without_doc_update(self) -> None:
        """Test DriftAuditor detecting new package pyproject.toml without updating architecture docs."""
        import subprocess

        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=self.root, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.root,
            capture_output=True,
            check=True,
        )

        readme = self.root / "README.md"
        readme.write_text("# Readme\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"], cwd=self.root, capture_output=True, check=True
        )

        # Add new package pyproject.toml
        new_pkg = self.root / "packages" / "ccba-new-package"
        new_pkg.mkdir(parents=True)
        (new_pkg / "pyproject.toml").write_text(
            "[project]\nname = 'ccba-new-package'\n", encoding="utf-8"
        )

        auditor = DriftAuditor(project_root=self.root)
        drift_errors = auditor.check_structural_git_drift()
        self.assertTrue(len(drift_errors) > 0)
        self.assertIn("Structural drift detected", drift_errors[0])

    def test_drift_auditor_detects_default_docs_marker_mismatch(self) -> None:
        """Test DriftAuditor checking all ArchStatsUpdater DEFAULT_DOCS including CONTEXT.md."""
        auditor = DriftAuditor(project_root=self.root)

        # Create CONTEXT.md with mismatched count
        context_md = self.root / "CONTEXT.md"
        context_md.write_text(
            "# Context\n<!-- SKILL_COUNT_START -->99<!-- SKILL_COUNT_END -->\n",
            encoding="utf-8",
        )

        # Should be checked by default check_marker_drift without passing explicit docs
        issues = auditor.check_marker_drift()
        self.assertTrue(any("CONTEXT.md" in err and "SKILL_COUNT is '99'" in err for err in issues))

    def test_drift_auditor_handles_spaces_and_quotes_in_git_paths(self) -> None:
        """Test DriftAuditor correctly parses git status paths containing spaces or quotes."""
        import subprocess

        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=self.root, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.root,
            capture_output=True,
            check=True,
        )

        readme = self.root / "README.md"
        readme.write_text("# Readme\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"], cwd=self.root, capture_output=True, check=True
        )

        # Add a Level-1 script with space in name
        space_script = self.root / "scripts" / "new test script.py"
        space_script.parent.mkdir(parents=True, exist_ok=True)
        space_script.write_text("print('test')\n", encoding="utf-8")

        auditor = DriftAuditor(project_root=self.root)
        drift_errors = auditor.check_structural_git_drift()
        self.assertTrue(len(drift_errors) > 0)
        self.assertIn("Structural drift detected", drift_errors[0])

    def test_drift_auditor_detects_structural_deletion_and_rename(self) -> None:
        """Test DriftAuditor detecting unstaged deletion and rename of Level-1 files."""
        import subprocess

        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=self.root, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.root,
            capture_output=True,
            check=True,
        )

        readme = self.root / "README.md"
        readme.write_text("# Readme\n", encoding="utf-8")
        workflow = self.root / ".agents" / "workflows" / "deploy.md"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text("# Deploy workflow\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.root, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"], cwd=self.root, capture_output=True, check=True
        )

        # Delete workflow file in working tree (unstaged ' D' status)
        workflow.unlink()

        auditor = DriftAuditor(project_root=self.root)
        drift_errors = auditor.check_structural_git_drift()
        self.assertTrue(len(drift_errors) > 0)
        self.assertIn("Structural drift detected", drift_errors[0])


if __name__ == "__main__":
    unittest.main()
