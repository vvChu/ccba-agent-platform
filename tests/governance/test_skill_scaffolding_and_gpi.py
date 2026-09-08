"""test_skill_scaffolding_and_gpi.py - Tests for Skill Scaffolder and GPI Governance.

Verifies:
1. Gate 0 (Determinism Gate): --deterministic flags reject flat skill scaffolding.
2. Gate 1 (Orchestration Gate): --orchestrated flags reject flat skill scaffolding.
3. Stage 2 GPI Routing:
   - Sub-threshold (< 12.0) with valid --parent creates progressive reference (Tier 2A).
   - Sub-threshold (< 12.0) without --parent or nonexistent parent fails with clear exit code 1.
   - Partial GPI arguments (--s without --k, etc.) fail with error.
   - Standalone (>= 12.0) creates full skill (SKILL.md with gpi: frontmatter, cli_spec.yaml).
4. Deprecation / Architecture Cleanliness:
   - write_workflow_router is completely removed from skill_generator.py.
5. SkillAuditor & Governance CLI --enforce-gpi adapter:
   - Audit with enforce_gpi=False permits legacy skills without gpi frontmatter.
   - Audit with enforce_gpi=True flags missing or insufficient GPI.
   - CLI runner correctly wires --enforce-gpi flag.
6. Real codebase skills updated in Phase 1 pass --enforce-gpi validation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from scripts.governance import DocumentAuditor, SkillAuditor
from scripts.governance.cli import run_skills_validation_cli
from scripts.scaffolding import skill_generator

pytestmark = [pytest.mark.fast, pytest.mark.unit]
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _create_sample_script(path: Path) -> Path:
    """Helper to create a sample Python script for scaffolding tests."""
    content = '''"""sample_tool.py - A sample utility tool for testing."""

from __future__ import annotations

import argparse


def main() -> int:
    """Run sample tool."""
    parser = argparse.ArgumentParser(description="Sample tool CLI")
    parser.add_argument("--input", "-i", required=True, help="Input file path")
    parser.add_argument("--count", "-c", type=int, default=1, help="Count of items")
    args = parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    path.write_text(content, encoding="utf-8")
    return path


# =====================================================================
# 1. Gate 0 & Gate 1 (Determinism & Orchestration Gates)
# =====================================================================


def test_gate_0_deterministic_rejection(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that --deterministic flag causes Gate 0 rejection and package guidance."""
    script_file = _create_sample_script(tmp_path / "calc_hash.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-calc-hash",
        skills_base_dir=skills_dir,
        is_deterministic=True,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Cổng 0 (Determinism Gate) từ chối" in captured.err
    assert "packages/*/src/" in captured.err
    assert not (skills_dir / "ccba-calc-hash").exists()


def test_gate_1_orchestrated_rejection(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that --orchestrated flag causes Gate 1 rejection and workflow guidance."""
    script_file = _create_sample_script(tmp_path / "review_flow.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-review-flow",
        skills_base_dir=skills_dir,
        is_orchestrated=True,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Cổng 1 (Orchestration Gate) từ chối" in captured.err
    assert ".agents/workflows/" in captured.err
    assert not (skills_dir / "ccba-review-flow").exists()


# =====================================================================
# 2. Stage 2: GPI Evaluation & Routing
# =====================================================================


def test_gpi_partial_arguments_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that providing some but not all 4 GPI metrics triggers an error."""
    script_file = _create_sample_script(tmp_path / "partial_gpi.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-partial-gpi",
        skills_base_dir=skills_dir,
        s=3.0,
        k=2.0,
        # missing a and p
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "bắt buộc phải cung cấp đầy đủ cả 4 chỉ số" in captured.err


def test_gpi_sub_threshold_without_parent_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that sub-threshold GPI (< 12.0) without --parent fails with guidance."""
    script_file = _create_sample_script(tmp_path / "sub_tool.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # S=2.0, K=1.0, A=2.0, P=4.0 -> GPI = (2.0*2.5)+(1.0*2.0)+(2.0*2.0)-(4.0*1.5) = 5.0 < 12.0
    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-sub-tool",
        skills_base_dir=skills_dir,
        s=2.0,
        k=1.0,
        a=2.0,
        p=4.0,
        parent=None,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Chỉ số GPI" in captured.err
    assert "< 12.0" in captured.err
    assert "--parent" in captured.err
    assert not (skills_dir / "ccba-sub-tool").exists()


def test_gpi_sub_threshold_with_nonexistent_parent_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that sub-threshold GPI (< 12.0) with a nonexistent parent skill fails."""
    script_file = _create_sample_script(tmp_path / "sub_tool.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-sub-tool",
        skills_base_dir=skills_dir,
        s=2.0,
        k=1.0,
        a=2.0,
        p=4.0,
        parent="ccba-nonexistent-master",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Master Skill 'ccba-nonexistent-master' không tồn tại" in captured.err


def test_gpi_sub_threshold_creates_progressive_reference(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that sub-threshold GPI (< 12.0) creates references/<name>.md under parent skill."""
    script_file = _create_sample_script(tmp_path / "sub_tool.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Pre-create parent master skill
    parent_dir = skills_dir / "ccba-master-skill"
    parent_dir.mkdir()
    (parent_dir / "SKILL.md").write_text(
        "---\nname: ccba-master-skill\ndescription: Master skill\nbundle: _core\n---\n# Master\n",
        encoding="utf-8",
    )

    # S=2.0, K=1.0, A=2.0, P=4.0 -> GPI = 5.0
    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-sub-tool",
        skills_base_dir=skills_dir,
        s=2.0,
        k=1.0,
        a=2.0,
        p=4.0,
        parent="ccba-master-skill",
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Đã tạo Progressive Reference (Tier 2A)" in captured.out
    assert "5.00 < 12.0" in captured.out

    ref_file = parent_dir / "references" / "sub-tool.md"
    assert ref_file.exists()
    content = ref_file.read_text(encoding="utf-8")
    assert "# Progressive Reference: sub-tool" in content
    assert "ccba-master-skill" in content
    assert "5.00" in content


def test_gpi_sub_threshold_parent_is_file_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that sub-threshold GPI with a file (non-directory) as parent fails gracefully."""
    script_file = _create_sample_script(tmp_path / "sub_tool.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    parent_as_file = tmp_path / "not_a_dir.txt"
    parent_as_file.write_text("dummy file", encoding="utf-8")

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-sub-tool",
        skills_base_dir=skills_dir,
        s=2.0,
        k=1.0,
        a=2.0,
        p=4.0,
        parent=str(parent_as_file),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "không phải là thư mục" in captured.err


def test_gpi_parent_without_metrics_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that specifying --parent without GPI metrics fails instead of creating flat skill."""
    script_file = _create_sample_script(tmp_path / "sub_tool.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-sub-tool",
        skills_base_dir=skills_dir,
        parent="ccba-master-skill",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Khi chỉ định Master Skill sở hữu qua '--parent'" in captured.err
    assert not (skills_dir / "ccba-sub-tool").exists()


def test_platform_loader_namespace_preserved(tmp_path: Path) -> None:
    """Verify that platform-loader is preserved without ccba- prefix per ADR-0056."""
    script_file = _create_sample_script(tmp_path / "loader.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="platform-loader",
        skills_base_dir=skills_dir,
        s=3.0,
        k=3.0,
        a=3.0,
        p=1.0,
    )
    assert exit_code == 0
    assert (skills_dir / "platform-loader").exists()
    assert not (skills_dir / "ccba-platform-loader").exists()


def test_clean_sub_name_removes_md_and_sanitizes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that reference sub_name sanitizes .md suffix and underscores."""
    script_file = _create_sample_script(tmp_path / "helper.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    parent_dir = skills_dir / "ccba-master"
    parent_dir.mkdir()
    (parent_dir / "SKILL.md").write_text(
        "---\nname: ccba-master\ndescription: Master\nbundle: _core\n---\n# M\n",
        encoding="utf-8",
    )

    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="my_sub_tool.md",
        skills_base_dir=skills_dir,
        s=2.0,
        k=1.0,
        a=1.0,
        p=4.0,
        parent="ccba-master",
    )
    assert exit_code == 0
    ref_file = parent_dir / "references" / "my-sub-tool.md"
    assert ref_file.exists()


def test_gpi_standalone_kernel_skill_creation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that GPI >= 12.0 creates a Standalone Kernel Skill with gpi block."""
    script_file = _create_sample_script(tmp_path / "standalone_worker.py")
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # S=3.0, K=2.0, A=4.0, P=1.0 -> GPI = 7.5 + 4.0 + 8.0 - 1.5 = 18.0 >= 12.0
    exit_code = skill_generator.create_skill_from_script(
        script_path_str=script_file,
        skill_name="ccba-standalone-worker",
        skills_base_dir=skills_dir,
        s=3.0,
        k=2.0,
        a=4.0,
        p=1.0,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Tạo Skill 'ccba-standalone-worker' thành công" in captured.out

    skill_dir = skills_dir / "ccba-standalone-worker"
    assert skill_dir.exists()
    skill_md = skill_dir / "SKILL.md"
    assert skill_md.exists()
    assert (skill_dir / "cli_spec.yaml").exists()

    content = skill_md.read_text(encoding="utf-8")
    assert "gpi:" in content
    assert "s: 3.0" in content
    assert "k: 2.0" in content
    assert "a: 4.0" in content
    assert "p: 1.0" in content

    # Parse YAML frontmatter to verify correctness
    parts = content.split("---")
    assert len(parts) >= 3
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "ccba-standalone-worker"
    assert fm["gpi"] == {"s": 3.0, "k": 2.0, "a": 4.0, "p": 1.0}


# =====================================================================
# 3. Router Removal Check (Deprecation Verification)
# =====================================================================


def test_write_workflow_router_removed() -> None:
    """Verify that write_workflow_router function and references are completely eliminated."""
    assert not hasattr(skill_generator, "write_workflow_router")
    source_text = Path(skill_generator.__file__).read_text(encoding="utf-8")
    assert "def write_workflow_router" not in source_text
    assert "write_workflow_router(" not in source_text


# =====================================================================
# 4. Scaffolder CLI Entrypoint (main)
# =====================================================================


def test_scaffolder_cli_flags(tmp_path: Path) -> None:
    """Verify CLI parser behavior for scaffolding commands."""
    script_file = _create_sample_script(tmp_path / "test_cli.py")

    with patch.object(
        sys,
        "argv",
        ["skill_generator.py", "--script", str(script_file), "--deterministic"],
    ):
        exit_code = skill_generator.main()
        assert exit_code == 1

    with patch.object(
        sys,
        "argv",
        ["skill_generator.py", "--script", str(script_file), "--orchestrated"],
    ):
        exit_code = skill_generator.main()
        assert exit_code == 1

    with patch.object(sys, "argv", ["skill_generator.py"]):
        exit_code = skill_generator.main()
        assert exit_code == 1

    # Test direct args_list parameter without patching sys.argv
    exit_code_direct = skill_generator.main(["--script", str(script_file), "--deterministic"])
    assert exit_code_direct == 1


def test_main_bundle_parameter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that --bundle argument in main() creates SKILL.md with specified bundle."""
    script_file = _create_sample_script(tmp_path / "qc_helper.py")
    skills_dir = tmp_path / ".agents" / "skills"
    monkeypatch.chdir(tmp_path)

    exit_code = skill_generator.main(
        [
            "--script",
            str(script_file),
            "--name",
            "ccba-qc-tool",
            "--bundle",
            "_qc",
            "--s",
            "3.0",
            "--k",
            "2.0",
            "--a",
            "4.0",
            "--p",
            "1.0",
        ]
    )
    assert exit_code == 0
    skill_file = skills_dir / "ccba-qc-tool" / "SKILL.md"
    assert skill_file.exists()
    content = skill_file.read_text(encoding="utf-8")
    assert "bundle: _qc" in content


# =====================================================================
# 5. SkillAuditor & CLI --enforce-gpi Adapter
# =====================================================================


def test_skill_auditor_enforce_gpi_behavior(tmp_path: Path) -> None:
    """Verify SkillAuditor respect for enforce_gpi flag."""
    auditor = SkillAuditor(tmp_path)
    skill_file = tmp_path / "ccba-test-gpi" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)

    # 1. Skill without GPI block
    skill_file.write_text(
        "---\nname: ccba-test-gpi\ndescription: Test skill description\nbundle: _core\n---\n# Test\n\n"
        + "\n".join(f"Line {i}" for i in range(40)),
        encoding="utf-8",
    )

    # Without enforce_gpi -> no GPI issues
    issues_no_enforce = auditor.audit_skill(skill_file, enforce_gpi=False)
    assert not any("gpi" in i.category.lower() for i in issues_no_enforce)

    # With enforce_gpi -> raises MISSING_GPI_METRICS
    issues_enforce = auditor.audit_skill(skill_file, enforce_gpi=True)
    assert any(i.category == "MISSING_GPI_METRICS" for i in issues_enforce)

    # 2. Skill with sub-threshold GPI in standalone directory
    skill_file.write_text(
        "---\nname: ccba-test-gpi\ndescription: Test skill description\nbundle: _core\n"
        "gpi:\n  s: 1.0\n  k: 1.0\n  a: 1.0\n  p: 5.0\n---\n# Test\n\n"
        + "\n".join(f"Line {i}" for i in range(40)),
        encoding="utf-8",
    )
    issues_sub_gpi = auditor.audit_skill(skill_file, enforce_gpi=True)
    assert any(i.category == "INSUFFICIENT_GPI_SCORE" for i in issues_sub_gpi)

    # 3. Skill with valid standalone GPI >= 12.0
    skill_file.write_text(
        "---\nname: ccba-test-gpi\ndescription: Test skill description\nbundle: _core\n"
        "gpi:\n  s: 3.0\n  k: 2.0\n  a: 4.0\n  p: 1.0\n---\n# Test\n\n"
        + "\n".join(f"Line {i}" for i in range(40)),
        encoding="utf-8",
    )
    issues_valid_gpi = auditor.audit_skill(skill_file, enforce_gpi=True)
    assert not any("gpi" in i.category.lower() for i in issues_valid_gpi)


def test_run_skills_validation_cli_enforce_gpi(tmp_path: Path) -> None:
    """Verify run_skills_validation_cli behavior with --enforce-gpi."""
    auditor = DocumentAuditor(tmp_path)
    skill_file = tmp_path / "ccba-cli-gpi" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)

    # Skill without GPI
    skill_file.write_text(
        "---\nname: ccba-cli-gpi\ndescription: CLI test description\nbundle: _core\n---\n# CLI Test\n\n"
        + "\n".join(f"Line {i}" for i in range(40)),
        encoding="utf-8",
    )

    # Normal check -> passes
    code = run_skills_validation_cli(auditor, ["--file", str(skill_file)])
    assert code == 0

    # With --enforce-gpi -> fails
    code = run_skills_validation_cli(auditor, ["--file", str(skill_file), "--enforce-gpi"])
    assert code == 1

    # Update with valid GPI >= 12.0
    skill_file.write_text(
        "---\nname: ccba-cli-gpi\ndescription: CLI test description\nbundle: _core\n"
        "gpi:\n  s: 3.0\n  k: 2.0\n  a: 4.0\n  p: 1.0\n---\n# CLI Test\n\n"
        + "\n".join(f"Line {i}" for i in range(40)),
        encoding="utf-8",
    )
    code = run_skills_validation_cli(auditor, ["--file", str(skill_file), "--enforce-gpi"])
    assert code == 0


# =====================================================================
# 6. Real Codebase Skills Updated in Phase 1
# =====================================================================


def test_updated_phase1_skills_pass_enforce_gpi() -> None:
    """Verify that ccba-build-skill and ccba-writing-great-skills pass --enforce-gpi."""
    auditor = SkillAuditor(PROJECT_ROOT)

    build_skill = PROJECT_ROOT / ".agents" / "skills" / "ccba-build-skill" / "SKILL.md"
    assert build_skill.exists()
    issues_build = auditor.audit_skill(build_skill, enforce_gpi=True)
    assert len(issues_build) == 0, f"ccba-build-skill issues: {[i.message for i in issues_build]}"

    writing_skill = PROJECT_ROOT / ".agents" / "skills" / "ccba-writing-great-skills" / "SKILL.md"
    assert writing_skill.exists()
    issues_writing = auditor.audit_skill(writing_skill, enforce_gpi=True)
    assert len(issues_writing) == 0, (
        f"ccba-writing-great-skills issues: {[i.message for i in issues_writing]}"
    )


def test_updated_phase2_skills_pass_enforce_gpi() -> None:
    """Verify that ccba-review-skill passes --enforce-gpi validation."""
    auditor = SkillAuditor(PROJECT_ROOT)

    review_skill = PROJECT_ROOT / ".agents" / "skills" / "ccba-review-skill" / "SKILL.md"
    assert review_skill.exists()
    issues_review = auditor.audit_skill(review_skill, enforce_gpi=True)
    assert len(issues_review) == 0, f"ccba-review-skill issues: {[i.message for i in issues_review]}"


def test_ccba_review_skill_phase2_spec_contract() -> None:
    """Verify ccba-review-skill contains all Phase 2 ADR-0057 contractual requirements."""
    import yaml

    file_path = PROJECT_ROOT / ".agents" / "skills" / "ccba-review-skill" / "SKILL.md"
    assert file_path.exists()
    raw_text = file_path.read_text(encoding="utf-8")

    # Frontmatter verification
    parts = raw_text.split("---", 2)
    assert len(parts) >= 3
    fm = yaml.safe_load(parts[1])
    assert fm.get("user-invocable") is True
    assert fm.get("command") == "/ccba-review-skill"
    gpi = fm.get("gpi", {})
    assert float(gpi.get("s")) == 3.0
    assert float(gpi.get("k")) == 2.0
    assert float(gpi.get("a")) == 2.0
    assert float(gpi.get("p")) == 2.0

    calculated_gpi = (3.0 * 2.5) + (2.0 * 2.0) + (2.0 * 2.0) - (2.0 * 1.5)
    assert calculated_gpi == 12.5 >= 12.0

    # Content verification
    body = parts[2]
    assert "Cổng 0 (The Determinism Gate)" in body
    assert "Cổng 1 (The Orchestration Gate)" in body
    assert "python -m ccba_harness.cli evaluate-gpi --file <path-to-skill.md>" in body
    assert "GPI < 12.0" in body
    assert "Tier 2A" in body
    assert "> 100 LOC" in body


def test_ccba_skills_eval_phase2_spec_contract() -> None:
    """Verify ccba-skills-eval contains all Phase 2 ADR-0057 contractual requirements."""
    import yaml

    file_path = PROJECT_ROOT / ".agents" / "skills" / "ccba-skills-eval" / "SKILL.md"
    assert file_path.exists()
    raw_text = file_path.read_text(encoding="utf-8")

    parts = raw_text.split("---", 2)
    assert len(parts) >= 3
    fm = yaml.safe_load(parts[1])
    gpi = fm.get("gpi", {})
    assert float(gpi.get("s")) == 2.0
    assert float(gpi.get("k")) == 1.0
    assert float(gpi.get("a")) == 1.0
    assert float(gpi.get("p")) == 4.0

    body = parts[2]
    assert "python -m ccba_harness.cli eval --skill [tên-skill] --trials 3" in body


def test_ccba_sync_upstream_phase2_spec_contract() -> None:
    """Verify ccba-sync-upstream contains all Phase 2 ADR-0057 contractual requirements."""
    file_path = PROJECT_ROOT / ".agents" / "skills" / "ccba-sync-upstream" / "SKILL.md"
    assert file_path.exists()
    raw_text = file_path.read_text(encoding="utf-8")

    assert "ADR-0057 & RES-2026-ARCH-001 v1.2" in raw_text
    assert "100 skills" in raw_text
    assert "Tier 1: Package Function" in raw_text
    assert "Tier 2A: Progressive Reference" in raw_text
    assert "Tier 2B: Standalone Kernel Skill" in raw_text
    assert "Tier 3: Composite Orchestrator" in raw_text

