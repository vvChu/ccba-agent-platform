"""test_doc_auditor.py - Unit tests for DocumentAuditor deep module."""

import sys
import tempfile
import unittest
from pathlib import Path

# Ensure scripts directory is in sys.path
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from doc_auditor import DocumentAuditor  # type: ignore[import-not-found]


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
                "---\nname: ccba-my-skill\ndescription: Valid short description.\nbundle: _core\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertEqual(len(issues), 0)

    def test_audit_skill_missing_completion_criterion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-my-skill\ndescription: Short description.\nbundle: _core\n---\n"
                "# Workflow\n1. Step without completion criterion",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertTrue(any("missing a Completion Criterion" in i.message for i in issues))

    def test_audit_skill_missing_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-my-skill\ndescription: Short description.\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertTrue(any(i.category == "MISSING_BUNDLE_FIELD" for i in issues))

    def test_audit_skill_invalid_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-my-skill\ndescription: Short description.\nbundle: invalid_bundle_xyz\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertTrue(any(i.category == "INVALID_BUNDLE_FIELD" for i in issues))

    def test_audit_skill_heading_step_completion_criterion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-my-skill\ndescription: Short description.\nbundle: _core\n---\n"
                "## Quy trình thực hiện\n"
                "### Bước 1: Chuẩn bị dữ liệu\n"
                "1. Làm sạch file đầu vào\n"
                "2. Kiểm tra format\n"
                "- **Tiêu chí hoàn thành:** Dữ liệu chuẩn hóa hoàn tất\n"
                "### Bước 2: Xử lý\n"
                "Nội dung xử lý\n"
                "- **Tiêu chí hoàn thành:** Kết quả đã xuất\n",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertEqual(len(issues), 0)

    def test_audit_skill_missing_command_when_user_invocable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-invocable-skill\ndescription: Short description.\nuser-invocable: true\nbundle: _core\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertTrue(any(i.category == "MISSING_COMMAND_FIELD" for i in issues))

    def test_audit_skill_invalid_command_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-invocable-skill\ndescription: Short description.\nuser-invocable: true\ncommand: /wrong-cmd\nbundle: _core\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertTrue(any(i.category == "INVALID_COMMAND_FIELD" for i in issues))

    def test_audit_skill_valid_slash_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-invocable-skill\ndescription: Short description.\nuser-invocable: true\ncommand: /ccba-invocable-skill\nbundle: _core\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertEqual(len(issues), 0)

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
            skills_dir = Path(tmpdir) / "skills" / "ccba-my-skill"
            skills_dir.mkdir(parents=True)
            skill_file = skills_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: ccba-my-skill\ndescription: Short description.\nbundle: _core\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            auditor = DocumentAuditor(project_root=Path(tmpdir))
            exit_code = auditor.run_skills_validation_cli([str(skills_dir.parent)])
            self.assertEqual(exit_code, 0)

    def test_run_skills_validation_cli_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir1 = Path(tmpdir) / "skills" / "ccba-skill-1"
            skills_dir1.mkdir(parents=True)
            skill_file1 = skills_dir1 / "SKILL.md"
            skill_file1.write_text(
                "---\nname: ccba-skill-1\ndescription: Skill 1.\nbundle: _core\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            skills_dir2 = Path(tmpdir) / "skills" / "ccba-skill-2"
            skills_dir2.mkdir(parents=True)
            skill_file2 = skills_dir2 / "SKILL.md"
            skill_file2.write_text(
                "---\nname: ccba-skill-2\ndescription: Skill 2.\nbundle: _core\n---\n"
                "# Workflow\n1. Step 1\n**Completion Criterion:** Done",
                encoding="utf-8",
            )
            auditor = DocumentAuditor(project_root=Path(tmpdir))
            exit_code = auditor.run_skills_validation_cli([str(skill_file1), str(skill_file2)])
            self.assertEqual(exit_code, 0)

    def test_audit_issue_extended_backward_compatibility(self) -> None:
        from doc_auditor import AuditIssue

        # 3 positional args (old usage)
        issue1 = AuditIssue(1, "subject", "message")
        self.assertEqual(issue1.line_number, 1)
        self.assertEqual(issue1.subject, "subject")
        self.assertEqual(issue1.message, "message")
        self.assertEqual(issue1.category, "")
        self.assertEqual(issue1.file_path, "")

        # 5 args (new extended usage)
        issue2 = AuditIssue(10, "doc.md", "Broken link", category="link", file_path="doc.md")
        self.assertEqual(issue2.category, "link")
        self.assertEqual(issue2.file_path, "doc.md")

    def test_audit_report_structure(self) -> None:
        from doc_auditor import AuditIssue, AuditReport

        issue_a = AuditIssue(5, "file1.md", "Broken link", category="link", file_path="file1.md")
        issue_b = AuditIssue(
            12, "file1.md", "Missing var", category="env_vars", file_path="file1.md"
        )

        report = AuditReport(
            issues=[issue_a, issue_b],
            total_issues=2,
            has_hard_errors=True,
            scanned_files=1,
        )
        self.assertEqual(report.total_issues, 2)
        self.assertTrue(report.has_hard_errors)
        self.assertEqual(len(report.by_category("link")), 1)
        self.assertEqual(len(report.by_file("file1.md")), 2)

    def test_step_regex_and_exclusion_header_variations(self) -> None:
        from scripts.governance.base import STEP_LINE_RE, is_exclusion_header

        # Valid step lines
        test_cases = [
            ("### Step 1.2.3: Multi-level sub-step", "1.2.3"),
            ("### Step IV: Roman numeral", "IV"),
            ("### Phase 1: Planning", "1"),
            ("### Pha 2: Thực thi", "2"),
            ("### Giai đoạn 3: Đánh giá", "3"),
            ("## 📋 Bước 1: Thu thập thông tin", "1"),
            ("1. Numbered step item", "1"),
        ]
        for line, expected_num in test_cases:
            m = STEP_LINE_RE.match(line)
            self.assertIsNotNone(m, f"Failed to match: {line}")
            assert m is not None
            matched_num = m.group(1) or m.group(3)
            self.assertEqual(matched_num, expected_num, f"Wrong step num for {line}")

        # Exclusion header collisions: step headers must NOT be excluded
        self.assertFalse(is_exclusion_header("bước 1: chuẩn bị môi trường"))
        self.assertFalse(is_exclusion_header("step 2: lưu ý an toàn"))
        self.assertFalse(is_exclusion_header("phase 3: yêu cầu kỹ thuật"))
        self.assertFalse(is_exclusion_header("step 1.2.3: chuẩn bị"))
        self.assertFalse(is_exclusion_header("step iv: lưu ý"))

        # Actual exclusion headers SHOULD be excluded
        self.assertTrue(is_exclusion_header("lưu ý chung"))
        self.assertTrue(is_exclusion_header("chuẩn bị"))
        self.assertTrue(is_exclusion_header("yêu cầu hệ thống"))
        self.assertTrue(is_exclusion_header("quy tắc phát triển"))

    def test_audit_skill_with_nested_subsections_and_exclusion_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-nested-skill\ndescription: Short description.\nbundle: _core\n---\n"
                "## Quy trình thực hiện\n"
                "### Bước 1: Chuẩn bị môi trường\n"
                "#### Lưu ý quan trọng:\n"
                "Không được bỏ qua bước này.\n"
                "- **Tiêu chí hoàn thành:** Môi trường đã sẵn sàng\n"
                "### Bước 2: Triển khai\n"
                "Nội dung triển khai\n"
                "- **Tiêu chí hoàn thành:** Triển khai thành công\n",
                encoding="utf-8",
            )
            issues = self.auditor.audit_skill(file_path)
            self.assertEqual(len(issues), 0, f"Unexpected issues: {issues}")

    def test_catalog_in_sync_detects_metadata_drift(self) -> None:
        from scripts.governance.compile_catalog import check_catalog_in_sync, generate_catalog_yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            skills_dir = tmp_root / ".agents" / "skills" / "platform-loader"
            skills_dir.mkdir(parents=True)
            my_skill_dir = tmp_root / ".agents" / "skills" / "ccba-test-skill"
            my_skill_dir.mkdir(parents=True)

            (my_skill_dir / "SKILL.md").write_text(
                "---\nname: ccba-test-skill\ndescription: Original desc.\nbundle: _core\ncommand: /ccba-test-skill\ntriggers:\n  - test\n---\n# Test",
                encoding="utf-8",
            )
            (skills_dir / "catalog_base.yaml").write_text(
                "hub_path: .\nbundles:\n  Phần mềm:\n    - _core\n",
                encoding="utf-8",
            )

            # Generate initial catalog
            cat_yaml = generate_catalog_yaml(tmp_root)
            (skills_dir / "catalog.yaml").write_text(cat_yaml, encoding="utf-8")

            # Initially 100% in sync
            in_sync, _ = check_catalog_in_sync(tmp_root)
            self.assertTrue(in_sync)

            # Simulate drift in description
            (my_skill_dir / "SKILL.md").write_text(
                "---\nname: ccba-test-skill\ndescription: Mutated description.\nbundle: _core\ncommand: /ccba-test-skill\ntriggers:\n  - test\n---\n# Test",
                encoding="utf-8",
            )
            in_sync, msg = check_catalog_in_sync(tmp_root)
            self.assertFalse(in_sync)
            self.assertIn("metadata drift in field 'description'", msg)

            # Simulate drift in command
            (my_skill_dir / "SKILL.md").write_text(
                "---\nname: ccba-test-skill\ndescription: Original desc.\nbundle: _core\ncommand: /ccba-other-cmd\ntriggers:\n  - test\n---\n# Test",
                encoding="utf-8",
            )
            in_sync, msg = check_catalog_in_sync(tmp_root)
            self.assertFalse(in_sync)
            self.assertIn("metadata drift in field 'command'", msg)

            # Simulate drift in triggers
            (my_skill_dir / "SKILL.md").write_text(
                "---\nname: ccba-test-skill\ndescription: Original desc.\nbundle: _core\ncommand: /ccba-test-skill\ntriggers:\n  - new_trigger\n---\n# Test",
                encoding="utf-8",
            )
            in_sync, msg = check_catalog_in_sync(tmp_root)
            self.assertFalse(in_sync)
            self.assertIn("metadata drift in field 'triggers'", msg)

            # Restore skill, mutate catalog_base.yaml
            (my_skill_dir / "SKILL.md").write_text(
                "---\nname: ccba-test-skill\ndescription: Original desc.\nbundle: _core\ncommand: /ccba-test-skill\ntriggers:\n  - test\n---\n# Test",
                encoding="utf-8",
            )
            (skills_dir / "catalog_base.yaml").write_text(
                "hub_path: .\nhub_repo: https://github.com/mutated/repo\nbundles:\n  Phần mềm:\n    - _core\n",
                encoding="utf-8",
            )
            in_sync, msg = check_catalog_in_sync(tmp_root)
            self.assertFalse(in_sync)
            self.assertIn("Base config drift in field 'hub_repo'", msg)

    def test_shallow_skill_warning_gate_triggers_under_35_lines(self) -> None:
        """Verify shallow skill (< 35 lines) triggers SHALLOW_SKILL_WARNING per ADR-0040."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            file_path.write_text(
                "---\nname: ccba-short-skill\ndescription: Short.\nbundle: _core\n---\n"
                "# Short Skill\n"
                "1. Step 1\n"
                "- **Tiêu chí hoàn thành:** Xong\n",
                encoding="utf-8",
            )
            # When check_shallow=True, triggers warning
            issues = self.auditor.audit_skill(file_path, check_shallow=True)
            shallow_warnings = [i for i in issues if i.category == "SHALLOW_SKILL_WARNING"]
            self.assertEqual(len(shallow_warnings), 1)
            self.assertIn("is too shallow", shallow_warnings[0].message)
            self.assertIn("ADR-0040", shallow_warnings[0].message)

            # Direct check_shallow_skill method
            direct_issues = self.auditor.skill_auditor.check_shallow_skill(file_path)
            self.assertEqual(len(direct_issues), 1)

    def test_shallow_skill_passes_at_or_above_35_lines(self) -> None:
        """Verify skill with >= 35 lines passes without SHALLOW_SKILL_WARNING."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SKILL.md"
            lines = [
                "---",
                "name: ccba-full-skill",
                "description: A fully specified skill with comprehensive documentation.",
                "bundle: _core",
                "---",
                "# Full Skill Documentation",
                "",
                "## Quy trình thực hiện",
                "### Bước 1: Khảo sát",
                "Nội dung thực thi bước 1.",
                "- **Tiêu chí hoàn thành:** Khảo sát xong.",
                "",
            ]
            for i in range(30):
                lines.append(
                    f"Dòng hướng dẫn chi tiết số {i + 1} nhằm đáp ứng tiêu chuẩn ADR-0040."
                )
            file_path.write_text("\n".join(lines), encoding="utf-8")

            issues = self.auditor.audit_skill(file_path, check_shallow=True)
            shallow_warnings = [i for i in issues if i.category == "SHALLOW_SKILL_WARNING"]
            self.assertEqual(len(shallow_warnings), 0)

    def test_workspace_gate_detects_shallow_skills(self) -> None:
        """Verify audit_workspace_gates flags shallow skills in the workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            skills_dir = tmp_root / ".agents" / "skills"
            short_skill_dir = skills_dir / "ccba-short-gate"
            short_skill_dir.mkdir(parents=True)
            (short_skill_dir / "SKILL.md").write_text(
                "---\nname: ccba-short-gate\ndescription: Desc.\nbundle: _core\n---\n# Short",
                encoding="utf-8",
            )
            auditor = DocumentAuditor(project_root=tmp_root)
            gate_issues = auditor.audit_workspace_gates(skills_dir)
            shallow = [g for g in gate_issues if g.category == "SHALLOW_SKILL_WARNING"]
            self.assertEqual(len(shallow), 1)
            self.assertIn("ccba-short-gate", shallow[0].message)


if __name__ == "__main__":
    unittest.main()
