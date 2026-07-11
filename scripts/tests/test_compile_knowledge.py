"""test_compile_knowledge.py - Unit tests for compile_knowledge.py"""

import sys
import tempfile
from pathlib import Path

# Add scripts directory to sys.path to allow running from any CWD
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from compile_knowledge import compile_skills, compile_workflows


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
