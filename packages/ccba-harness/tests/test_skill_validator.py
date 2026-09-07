"""test_skill_validator.py - Unit tests for ccba-harness standalone SkillValidator & CLI."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ccba_harness.cli import main, run_skill_validation_cli
from ccba_harness.skill_validator import (
    SHALLOW_SKILL_MIN_LINES,
    SkillValidator,
)


def _make_dummy_skill_content(
    name: str = "ccba-test-skill",
    description: str = "A valid test skill description.",
    bundle: str = "_core",
    user_invocable: bool = False,
    command: str | None = None,
    disable_model_invocation: bool = False,
    extra_lines: int = 40,
    with_completion_criteria: bool = True,
) -> str:
    """Helper to generate dummy skill content with controlled line count and criteria."""
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        f"bundle: {bundle}",
    ]
    if user_invocable:
        lines.append("user-invocable: true")
    if command:
        lines.append(f"command: {command}")
    if disable_model_invocation:
        lines.append("disable-model-invocation: true")
    lines.append("---")
    lines.append(f"# {name.title()}")
    lines.append("")
    lines.append("## Quy trình thực hiện")
    lines.append("### Bước 1: Khởi tạo môi trường")
    lines.append("Nội dung thực thi bước 1.")
    if with_completion_criteria:
        lines.append("- **Tiêu chí hoàn thành:** Môi trường đã sẵn sàng.")
    else:
        lines.append("Thiếu tiêu chí hoàn thành.")
    lines.append("")

    for i in range(extra_lines):
        lines.append(f"Dòng nội dung bổ sung số {i+1} để kiểm thử quy chuẩn độ dài.")

    return "\n".join(lines)


def test_valid_skill_passes() -> None:
    """Test that a compliant skill with >= 35 lines passes with 0 issues."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        file_path.write_text(_make_dummy_skill_content(extra_lines=30), encoding="utf-8")
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path, check_shallow=True)
        assert len(issues) == 0


def test_missing_frontmatter() -> None:
    """Test missing frontmatter detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        file_path.write_text("# Just Header Without Frontmatter\nLine 2\nLine 3", encoding="utf-8")
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "MALFORMED_FRONTMATTER" for i in issues)


def test_malformed_yaml() -> None:
    """Test malformed YAML frontmatter syntax."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        file_path.write_text("---\nname: [unclosed list\n---\n# Body", encoding="utf-8")
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "YAML_PARSE_ERROR" for i in issues)


def test_missing_name_and_invalid_namespace() -> None:
    """Test missing name and namespace violation per ADR-0056."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # Missing name
        file_path.write_text(
            "---\ndescription: Desc.\nbundle: _core\n---\n# Title",
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "MISSING_NAME" for i in issues)

        # Invalid namespace (not ccba-, bigbim-, or platform-loader)
        file_path.write_text(
            "---\nname: random-unprefixed-skill\ndescription: Desc.\nbundle: _core\n---\n# Title",
            encoding="utf-8",
        )
        issues = validator.audit_skill(file_path)
        assert any(i.category == "INVALID_NAMESPACE" for i in issues)


def test_description_length_limit() -> None:
    """Test description <= 180 chars for model-invoked skills."""
    long_desc = "A" * 185
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # Model-invoked with long description -> should fail
        file_path.write_text(
            _make_dummy_skill_content(description=long_desc, disable_model_invocation=False),
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "DESCRIPTION_TOO_LONG" for i in issues)

        # Ritual workflow (disable-model-invocation: true) allows longer description
        file_path.write_text(
            _make_dummy_skill_content(description=long_desc, disable_model_invocation=True),
            encoding="utf-8",
        )
        issues = validator.audit_skill(file_path)
        assert not any(i.category == "DESCRIPTION_TOO_LONG" for i in issues)


def test_bundle_validation() -> None:
    """Test bundle requirement and taxonomy check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # Missing bundle
        file_path.write_text(
            "---\nname: ccba-test\ndescription: Desc.\n---\n# Test",
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "MISSING_BUNDLE_FIELD" for i in issues)

        # Invalid bundle
        file_path.write_text(
            "---\nname: ccba-test\ndescription: Desc.\nbundle: unknown_bundle_xyz\n---\n# Test",
            encoding="utf-8",
        )
        issues = validator.audit_skill(file_path)
        assert any(i.category == "INVALID_BUNDLE_FIELD" for i in issues)


def test_slash_command_contract() -> None:
    """Test ADR-0056 slash command contract."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # user-invocable without command
        file_path.write_text(
            "---\nname: ccba-test\ndescription: Desc.\nbundle: _core\nuser-invocable: true\n---\n# Test",
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "MISSING_COMMAND_FIELD" for i in issues)

        # user-invocable with mismatched command
        file_path.write_text(
            "---\nname: ccba-test\ndescription: Desc.\nbundle: _core\nuser-invocable: true\ncommand: /unrelated-cmd\n---\n# Test",
            encoding="utf-8",
        )
        issues = validator.audit_skill(file_path)
        assert any(i.category == "INVALID_COMMAND_FIELD" for i in issues)

        # valid slash command
        file_path.write_text(
            _make_dummy_skill_content(
                name="ccba-my-tool",
                user_invocable=True,
                command="/ccba-my-tool",
                extra_lines=30,
            ),
            encoding="utf-8",
        )
        issues = validator.audit_skill(file_path, check_shallow=True)
        assert len(issues) == 0


def test_completion_criteria_detection() -> None:
    """Test step completion criteria enforcement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        file_path.write_text(
            _make_dummy_skill_content(with_completion_criteria=False),
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "MISSING_COMPLETION_CRITERIA" for i in issues)


def test_shallow_skill_warning_gate() -> None:
    """Test shallow skill warning gate (< 35 content lines per ADR-0040)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # Short skill: only 15 lines
        file_path.write_text(
            "---\nname: ccba-short\ndescription: Short.\nbundle: _core\n---\n"
            "# Short Skill\n"
            "## Các bước\n"
            "1. Bước 1\n"
            "- **Tiêu chí hoàn thành:** Xong\n",
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))

        # Default audit_skill(check_shallow=False) does not flag shallow
        issues_no_shallow = validator.audit_skill(file_path, check_shallow=False)
        assert not any(i.category == "SHALLOW_SKILL_WARNING" for i in issues_no_shallow)

        # Explicit check_shallow=True triggers SHALLOW_SKILL_WARNING
        issues_shallow = validator.audit_skill(file_path, check_shallow=True)
        shallow_issues = [i for i in issues_shallow if i.category == "SHALLOW_SKILL_WARNING"]
        assert len(shallow_issues) == 1
        assert f"< {SHALLOW_SKILL_MIN_LINES} lines minimum per ADR-0040" in shallow_issues[0].message

        # Dedicated check_shallow_skill method
        issues_direct = validator.check_shallow_skill(file_path)
        assert len(issues_direct) == 1

        # Skill with >= 35 content lines does NOT trigger warning
        long_content = _make_dummy_skill_content(extra_lines=35)
        file_path.write_text(long_content, encoding="utf-8")
        assert len(validator.check_shallow_skill(file_path)) == 0


def test_workspace_gates_duplicate_and_context_budget() -> None:
    """Test Zero-Duplicate Gate and Context Budget Ceiling Gate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        skills_dir = tmp_root / ".agents" / "skills"
        skill1_dir = skills_dir / "ccba-dup"
        skill2_dir = skills_dir / "sub" / "ccba-dup"
        skill1_dir.mkdir(parents=True)
        skill2_dir.mkdir(parents=True)

        content = _make_dummy_skill_content(name="ccba-dup", extra_lines=30)
        (skill1_dir / "SKILL.md").write_text(content, encoding="utf-8")
        (skill2_dir / "SKILL.md").write_text(content, encoding="utf-8")

        validator = SkillValidator(project_root=tmp_root)
        gate_issues = validator.audit_workspace_gates(skills_dir)
        assert any(i.category == "ZERO_DUPLICATE_GATE_VIOLATION" for i in gate_issues)


def test_workflow_audit() -> None:
    """Test workflow validation constraints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = Path(tmpdir) / "test_wf.md"
        # Missing disable-model-invocation
        wf_path.write_text(
            "---\nname: my-wf\ndescription: Workflow desc.\n---\n# Workflow: Test\nBody",
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_workflow(wf_path)
        assert any(i.category == "WORKFLOW_MODEL_INVOCATION_NOT_DISABLED" for i in issues)

        # Valid workflow
        wf_path.write_text(
            "---\nname: my-wf\ndescription: Valid workflow.\ndisable-model-invocation: true\n---\n# Workflow: Test\nBody content.",
            encoding="utf-8",
        )
        issues = validator.audit_workflow(wf_path)
        assert len(issues) == 0


def test_cli_runner_success_and_strict_modes() -> None:
    """Test CLI runner via run_skill_validation_cli and main."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        skill_dir = tmp_root / ".agents" / "skills" / "ccba-good"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            _make_dummy_skill_content(name="ccba-good", extra_lines=35),
            encoding="utf-8",
        )

        # Test CLI success
        code = run_skill_validation_cli(["--root", str(tmp_root)])
        assert code == 0

        # Test main CLI entry point
        code_main = main(["validate-skill", "--root", str(tmp_root)])
        assert code_main == 0

        # Test shallow skill warning in normal mode (exit 0) vs strict mode (exit 1)
        short_dir = tmp_root / ".agents" / "skills" / "ccba-short"
        short_dir.mkdir(parents=True)
        short_file = short_dir / "SKILL.md"
        short_file.write_text(
            "---\nname: ccba-short\ndescription: Desc.\nbundle: _core\n---\n"
            "# Short\n"
            "## Steps\n"
            "1. Step\n"
            "- **Tiêu chí hoàn thành:** Done\n",
            encoding="utf-8",
        )

        # Normal mode: warning does not block exit 0
        code_normal = run_skill_validation_cli(["--file", str(short_file), "--root", str(tmp_root)])
        assert code_normal == 0

        # Strict mode: warning becomes hard error (exit 1)
        code_strict = run_skill_validation_cli(
            ["--file", str(short_file), "--root", str(tmp_root), "--strict"]
        )
        assert code_strict == 1


def test_cli_runner_nonexistent_targets() -> None:
    """Test CLI runner correctly fails with exit code 1 on non-existent targets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)

        # Non-existent file via --file
        code_file = run_skill_validation_cli(
            ["--file", "nonexistent.md", "--root", str(tmp_root)]
        )
        assert code_file == 1

        # Non-existent file via positional arg
        code_pos = run_skill_validation_cli(
            ["nonexistent_pos.md", "--root", str(tmp_root)]
        )
        assert code_pos == 1


def test_cli_runner_workflow_file() -> None:
    """Test CLI runner validating a workflow file directly via --file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        wf_dir = tmp_root / ".agents" / "workflows"
        wf_dir.mkdir(parents=True)
        wf_file = wf_dir / "my-workflow.md"
        wf_file.write_text(
            "---\nname: my-workflow\ndescription: Test workflow.\ndisable-model-invocation: true\n---\n# Workflow: Test\nBody",
            encoding="utf-8",
        )
        code = run_skill_validation_cli(["--file", str(wf_file), "--root", str(tmp_root)])
        assert code == 0


def test_audit_workflow_missing_file() -> None:
    """Test audit_workflow reporting MISSING_FILE for non-existent file."""
    validator = SkillValidator()
    issues = validator.audit_workflow(Path("does_not_exist_workflow_xyz.md"))
    assert len(issues) == 1
    assert issues[0].category == "MISSING_FILE"


def test_yaml_package_missing_graceful_handling(monkeypatch) -> None:
    """Test graceful handling and clear error message when PyYAML is not installed."""
    import ccba_harness.skill_validator as sv

    monkeypatch.setattr(sv, "yaml", None)
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        file_path.write_text(
            "---\nname: ccba-test\ndescription: Test.\nbundle: _core\n---\n# Test",
            encoding="utf-8",
        )
        validator = sv.SkillValidator(project_root=Path(tmpdir))

        # audit_skill should return YAML_PACKAGE_MISSING
        issues = validator.audit_skill(file_path)
        assert any(i.category == "YAML_PACKAGE_MISSING" for i in issues)

        # audit_workflow should return YAML_PACKAGE_MISSING
        wf_path = Path(tmpdir) / "test_wf.md"
        wf_path.write_text(
            "---\nname: test-wf\ndescription: Test.\ndisable-model-invocation: true\n---\n# Workflow: Test",
            encoding="utf-8",
        )
        wf_issues = validator.audit_workflow(wf_path)
        assert any(i.category == "YAML_PACKAGE_MISSING" for i in wf_issues)

        # get_valid_bundles gracefully falls back to DEFAULT_VALID_BUNDLES
        bundles = validator.get_valid_bundles()
        assert sv.DEFAULT_VALID_BUNDLES.issubset(bundles)


def test_boolean_string_normalization() -> None:
    """Test that boolean values declared as strings are correctly normalized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # disable-model-invocation: "false" string should not be treated as True
        long_desc = "B" * 200
        file_path.write_text(
            f"---\nname: ccba-bool-test\ndescription: {long_desc}\nbundle: _core\ndisable-model-invocation: 'false'\n---\n# Title",
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        # Should flag description too long since disable-model-invocation is effectively false
        assert any(i.category == "DESCRIPTION_TOO_LONG" for i in issues)

