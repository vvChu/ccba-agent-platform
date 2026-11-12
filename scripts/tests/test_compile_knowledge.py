"""test_compile_knowledge.py - Unit tests for compile_knowledge.py"""

import sys
import tempfile
from pathlib import Path

# Add scripts directory to sys.path to allow running from any CWD
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from scripts.spoke.compile_knowledge import compile_skills, compile_workflows


def test_compile_skills() -> None:
    """Verify that compile_skills successfully merges SKILL.md files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        skills_dir = temp_path / "skills"
        skills_dir.mkdir()

        # Create dummy skill folders and SKILL.md files
        skill1_dir = skills_dir / "skill1"
        skill1_dir.mkdir()
        (skill1_dir / "SKILL.md").write_text("content of skill 1", encoding="utf-8")

        skill2_dir = skills_dir / "skill2"
        skill2_dir.mkdir()
        (skill2_dir / "SKILL.md").write_text("content of skill 2", encoding="utf-8")

        output_file = temp_path / "skills_compiled.md"

        # Execute
        compile_skills(skills_dir, output_file)

        # Verify
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "# Skill: skill1" in content
        assert "content of skill 1" in content
        assert "# Skill: skill2" in content
        assert "content of skill 2" in content
        assert "---" in content


def test_compile_workflows() -> None:
    """Verify that compile_workflows successfully merges workflow markdown files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        workflows_dir = temp_path / "workflows"
        workflows_dir.mkdir()

        # Create dummy workflow files
        (workflows_dir / "ccba-wf1.md").write_text("content of wf 1", encoding="utf-8")
        (workflows_dir / "ccba-wf2.md").write_text("content of wf 2", encoding="utf-8")

        output_file = temp_path / "workflows_compiled.md"

        # Execute
        compile_workflows(workflows_dir, output_file)

        # Verify
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "# Workflow: ccba-wf1" in content
        assert "content of wf 1" in content
        assert "# Workflow: ccba-wf2" in content
        assert "content of wf 2" in content
        assert "---" in content


def test_compile_workflows_archived_fallback() -> None:
    """Verify that compile_workflows falls back to *.md.bak files with ADR-0056 notice."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        workflows_dir = temp_path / "workflows"
        workflows_dir.mkdir()

        # Create dummy archived workflow files
        (workflows_dir / "ccba-legacy-wf1.md.bak").write_text(
            "content of legacy wf 1", encoding="utf-8"
        )
        (workflows_dir / "ccba-legacy-wf2.md.bak").write_text(
            "content of legacy wf 2", encoding="utf-8"
        )

        output_file = temp_path / "workflows_compiled.md"

        # Execute
        compile_workflows(workflows_dir, output_file)

        # Verify
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "ADR-0056" in content
        assert "# Archived Workflow: ccba-legacy-wf1" in content
        assert "content of legacy wf 1" in content
        assert "# Archived Workflow: ccba-legacy-wf2" in content
        assert "content of legacy wf 2" in content
        assert "---" in content


def test_compile_skills_includes_tier2a_references_deterministically(tmp_path: Path) -> None:
    """Verify compile_skills bundles sorted Tier 2A references/*.md and supports opt-out."""
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "ccba-sample"
    refs_dir = skill_dir / "references"
    sub_refs = refs_dir / "nested"
    sub_refs.mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text("root skill body", encoding="utf-8")
    (refs_dir / "zeta.md").write_text("zeta reference body", encoding="utf-8")
    (refs_dir / "alpha.md").write_text("alpha reference body", encoding="utf-8")
    (sub_refs / "beta.md").write_text("nested beta body", encoding="utf-8")
    (refs_dir / "ignore.txt").write_text("non-markdown ignored", encoding="utf-8")

    out_with_refs = tmp_path / "skills_with_refs.md"
    compile_skills(skills_dir, out_with_refs)
    compiled = out_with_refs.read_text(encoding="utf-8")

    idx_skill = compiled.index("# Skill: ccba-sample")
    idx_alpha = compiled.index("# Skill Reference: ccba-sample/references/alpha.md")
    idx_nested = compiled.index("# Skill Reference: ccba-sample/references/nested/beta.md")
    idx_zeta = compiled.index("# Skill Reference: ccba-sample/references/zeta.md")

    assert idx_skill < idx_alpha < idx_nested < idx_zeta
    assert "alpha reference body" in compiled
    assert "nested beta body" in compiled
    assert "zeta reference body" in compiled
    assert "non-markdown ignored" not in compiled

    out_no_refs = tmp_path / "skills_no_refs.md"
    compile_skills(skills_dir, out_no_refs, include_references=False)
    compiled_no_refs = out_no_refs.read_text(encoding="utf-8")
    assert "# Skill: ccba-sample" in compiled_no_refs
    assert "# Skill Reference:" not in compiled_no_refs
