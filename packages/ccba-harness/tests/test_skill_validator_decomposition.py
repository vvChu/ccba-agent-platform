"""test_skill_validator_decomposition.py - Parity and structural budget tests for PR-2a.

Verifies:
1. Public API, constants, and helper exports preserved on `ccba_harness.skill_validator`.
2. Parity across valid skills, invalid YAML/namespace/bundle/command, Tier 3 orchestrators,
   GPI enforcement, workflow checks, and workspace gates.
3. Single disk read per `audit_skill` invocation (eliminating redundant L778 re-read).
4. Decomposition structural budgets across the 4 modules (`<= 450` LOC/file and `<= 50` LOC/func).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness import skill_validator as sv
from ccba_harness.peer_gate import check_ast_function_length
from ccba_harness.skill_validator import (
    ALLOWED_HOST_COMMANDS,
    COMMON_PATH_SEGMENTS,
    DEFAULT_VALID_BUNDLES,
    EXCLUSION_HEADERS,
    FRONTMATTER_RE,
    GITLAB_QUICK_ACTIONS,
    LINK_EXTRACT_RE,
    MAX_MODEL_INVOKED_PER_BUNDLE,
    SHALLOW_SKILL_MIN_LINES,
    SLASH_CMD_RE,
    STEP_LINE_RE,
    WORKFLOW_HEADERS,
    AuditIssueString,
    SkillAuditIssue,
    SkillValidator,
    is_exclusion_header,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]

_HARNESS_PKG_DIR = Path(__file__).resolve().parents[1] / "src" / "ccba_harness"
_DECOMPOSED_MODULES = (
    "skill_validator.py",
    "_skill_frontmatter.py",
    "_skill_content_checks.py",
    "_skill_gpi_gates.py",
)


def _compliant_skill_text(
    name: str = "ccba-parity-skill",
    extra_frontmatter: str = "",
    extra_lines: int = 35,
) -> str:
    """Build a compliant SKILL.md payload for parity tests."""
    fm_lines = [
        "---",
        f"name: {name}",
        "description: Compliant skill for decomposition parity.",
        "bundle: _core",
        "gpi:",
        "  s: 4.0",
        "  k: 3.0",
        "  a: 3.0",
        "  p: 1.0",
    ]
    if extra_frontmatter:
        fm_lines.append(extra_frontmatter.rstrip())
    fm_lines.extend(
        [
            "---",
            f"# {name}",
            "## Quy trình thực hiện",
            "### Bước 1: Kiểm tra",
            "Thực thi kiểm tra chuẩn.",
            "- **Tiêu chí hoàn thành:** Hoàn tất bước 1.",
        ]
    )
    fm_lines.extend([f"Dòng nội dung bổ sung {idx}" for idx in range(extra_lines)])
    return "\n".join(fm_lines) + "\n"


def test_public_symbols_and_methods_preserved() -> None:
    """Ensure every historical module constant, type, and method remains exported."""
    assert FRONTMATTER_RE is sv.FRONTMATTER_RE
    assert STEP_LINE_RE is sv.STEP_LINE_RE
    assert WORKFLOW_HEADERS is sv.WORKFLOW_HEADERS
    assert EXCLUSION_HEADERS is sv.EXCLUSION_HEADERS
    assert DEFAULT_VALID_BUNDLES is sv.DEFAULT_VALID_BUNDLES
    assert SHALLOW_SKILL_MIN_LINES == 35
    assert MAX_MODEL_INVOKED_PER_BUNDLE == 10
    assert COMMON_PATH_SEGMENTS is sv.COMMON_PATH_SEGMENTS
    assert ALLOWED_HOST_COMMANDS is sv.ALLOWED_HOST_COMMANDS
    assert GITLAB_QUICK_ACTIONS is sv.GITLAB_QUICK_ACTIONS
    assert LINK_EXTRACT_RE is sv.LINK_EXTRACT_RE
    assert SLASH_CMD_RE is sv.SLASH_CMD_RE
    assert is_exclusion_header("## Lưu ý") is True
    assert is_exclusion_header("## Bước 1: Thực thi") is False
    assert issubclass(AuditIssueString, str)
    issue = SkillAuditIssue(line_number=1, subject="s", message="msg", category="CAT")
    assert issue.category == "CAT"

    required_methods = (
        "get_valid_bundles",
        "get_registered_commands",
        "validate_markdown_links",
        "audit_slash_commands",
        "audit_skill_directory",
        "check_shallow_skill",
        "audit_skill",
        "_audit_granularity_and_gpi",
        "evaluate_skill_file",
        "evaluate_two_stage_decision",
        "calculate_gpi",
        "analyze_steps_completion_criteria",
        "_analyze_steps_completion_criteria",
        "audit_workflow",
        "audit_workspace_gates",
        "run_cli",
    )
    for method_name in required_methods:
        assert hasattr(SkillValidator, method_name), f"Missing SkillValidator.{method_name}"


def test_parity_across_skill_gpi_workflow_and_gates(tmp_path: Path) -> None:
    """Verify decomposed validator produces identical audit classifications across core scenarios."""
    skills_dir = tmp_path / ".agents" / "skills"
    good_skill = skills_dir / "ccba-parity-skill" / "SKILL.md"
    good_skill.parent.mkdir(parents=True)
    good_skill.write_text(_compliant_skill_text(), encoding="utf-8")

    validator = SkillValidator(project_root=tmp_path)
    assert validator.audit_skill(good_skill, check_shallow=True, enforce_gpi=True) == []

    # Invalid YAML, namespace, bundle, command, GPI mismatch
    bad_yaml = tmp_path / "bad_yaml.md"
    bad_yaml.write_text("---\nname: [broken\n---\n# Body", encoding="utf-8")
    assert any(i.category == "YAML_PARSE_ERROR" for i in validator.audit_skill(bad_yaml))

    bad_meta = tmp_path / "bad_meta.md"
    bad_meta.write_text(
        "---\nname: unknown-ns\ndescription: x\nbundle: bogus_bundle\nuser-invocable: true\n"
        "gpi:\n  s: 1\n  k: 1\n  a: 1\n  p: 4\n---\n# Bad",
        encoding="utf-8",
    )
    meta_cats = {i.category for i in validator.audit_skill(bad_meta, enforce_gpi=True)}
    assert {
        "INVALID_NAMESPACE",
        "INVALID_BUNDLE_FIELD",
        "MISSING_COMMAND_FIELD",
        "INSUFFICIENT_GPI_SCORE",
    }.issubset(meta_cats)

    # GPI mismatch triggers COND-01 when score != computed
    mismatched = tmp_path / "mismatch.md"
    mismatched.write_text(
        "---\nname: ccba-mismatch\ndescription: x\nbundle: _core\n"
        "gpi:\n  s: 4\n  k: 3\n  a: 3\n  p: 1\n  score: 99.0\n---\n# Mismatch\n"
        "## Quy trình thực hiện\n### Bước 1: A\n- **Tiêu chí hoàn thành:** OK\n",
        encoding="utf-8",
    )
    assert any(
        i.category == "MISMATCHED_GPI_SCORE"
        for i in validator.audit_skill(mismatched, enforce_gpi=True)
    )

    # Tier 3 orchestrator missing Single-Writer protocol
    orch_bad = tmp_path / "orch_bad.md"
    orch_bad.write_text(
        "---\nname: ccba-orch-bad\ndescription: Orchestrates worker subagents.\n"
        "tier: orchestrator\nis-orchestrated: true\ndisable-model-invocation: true\n"
        "bundle: _core\ncommand: /ccba-orch-bad\n---\n"
        "# Bad Orchestrator\nLaunch parallel worker subagent here.\n",
        encoding="utf-8",
    )
    assert any(
        i.category == "SINGLE_WRITER_PROTOCOL_VIOLATION"
        for i in validator.audit_skill(orch_bad, enforce_gpi=True)
    )

    # Workflow validation
    wf_bad = tmp_path / "wf_bad.md"
    wf_bad.write_text("---\nname: wf\ndescription: wf\n---\n# Workflow: X\nBody", encoding="utf-8")
    assert any(
        i.category == "WORKFLOW_MODEL_INVOCATION_NOT_DISABLED"
        for i in validator.audit_workflow(wf_bad)
    )

    # Workspace gates: duplicate name + dangling dependency
    dup_skill = skills_dir / "nested" / "ccba-parity-skill" / "SKILL.md"
    dup_skill.parent.mkdir(parents=True)
    dup_skill.write_text(_compliant_skill_text(), encoding="utf-8")
    dangling = skills_dir / "ccba-dangling" / "SKILL.md"
    dangling.parent.mkdir(parents=True)
    dangling.write_text(
        "---\nname: ccba-dangling\ndescription: x\nbundle: _core\nmaster_skill: missing-skill\n---\n# D\n",
        encoding="utf-8",
    )
    gate_cats = {i.category for i in validator.audit_workspace_gates(skills_dir)}
    assert {"ZERO_DUPLICATE_GATE_VIOLATION", "DANGLING_SKILL_DEPENDENCY"}.issubset(gate_cats)


def test_audit_skill_reads_target_file_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify audit_skill does not perform redundant disk re-reads in _audit_granularity_and_gpi."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        _compliant_skill_text(
            name="ccba-single-read",
            extra_frontmatter=(
                "tier: orchestrator\nis-orchestrated: true\ndisable-model-invocation: true\n"
                "command: /ccba-single-read"
            ),
        )
        + "Launch worker subagent here.\n",
        encoding="utf-8",
    )

    original_read_text = Path.read_text
    target_resolved = skill_file.resolve()
    reads = 0

    def counting_read_text(self: Path, *args: object, **kwargs: object) -> str:
        nonlocal reads
        if self.resolve() == target_resolved:
            reads += 1
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counting_read_text)
    validator = SkillValidator(project_root=tmp_path)
    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    assert any(i.category == "SINGLE_WRITER_PROTOCOL_VIOLATION" for i in issues)
    assert reads == 1, f"Expected exactly 1 read_text on target SKILL.md, got {reads}"


def test_decomposed_modules_satisfy_line_and_function_budgets() -> None:
    """Enforce <= 450 LOC per decomposed module and <= 50 LOC per function via AST gate."""
    target_files: list[Path] = []
    for mod_name in _DECOMPOSED_MODULES:
        mod_path = _HARNESS_PKG_DIR / mod_name
        assert mod_path.exists(), f"Expected decomposed module missing: {mod_path}"
        line_count = len(mod_path.read_text(encoding="utf-8").splitlines())
        assert line_count <= 450, f"{mod_name} exceeds 450 LOC budget ({line_count} LOC)"
        target_files.append(mod_path)

    gate = check_ast_function_length(target_files, max_lines=50)
    assert gate.passed, f"AST function length violation:\n{gate.stdout_tail}"
