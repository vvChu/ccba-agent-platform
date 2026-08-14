"""compile_knowledge.py - CLI tool to compile Hub skills and workflows.

Combines separate skill and workflow markdown files into single consolidated
documents to bypass Google NotebookLM's source limits and optimize RAG context.
"""

import sys
from pathlib import Path


def compile_skills(skills_dir: Path, output_file: Path) -> None:
    """Scan all skill directories and merge their SKILL.md contents.

    Args:
        skills_dir: Path to the skills root directory.
        output_file: Path to the compiled markdown output file.
    """
    if not skills_dir.exists():
        print(f"Skills directory does not exist: {skills_dir}", file=sys.stderr)
        return

    output_content = []
    # Sorted for deterministic output
    for folder in sorted(skills_dir.iterdir()):
        if not folder.is_dir():
            continue
        skill_file = folder / "SKILL.md"
        if skill_file.exists():
            try:
                content = skill_file.read_text(encoding="utf-8")
                output_content.append(f"# Skill: {folder.name}\n\n{content}\n\n---\n")
            except Exception as e:
                print(f"Error reading skill {skill_file}: {e}", file=sys.stderr)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(output_content), encoding="utf-8")
    print(f"Successfully compiled skills to: {output_file}")


def compile_workflows(workflows_dir: Path, output_file: Path) -> None:
    """Scan all workflow files and merge their contents.

    Args:
        workflows_dir: Path to the workflows root directory.
        output_file: Path to the compiled markdown output file.
    """
    if not workflows_dir.exists():
        print(f"Workflows directory does not exist: {workflows_dir}", file=sys.stderr)
        return

    output_content = []
    # Sorted for deterministic output
    for file_path in sorted(workflows_dir.glob("*.md")):
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
            output_content.append(f"# Workflow: {file_path.stem}\n\n{content}\n\n---\n")
        except Exception as e:
            print(f"Error reading workflow {file_path}: {e}", file=sys.stderr)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(output_content), encoding="utf-8")
    print(f"Successfully compiled workflows to: {output_file}")


def main() -> None:
    """Main execution entry point."""
    project_root = Path(__file__).resolve().parents[2]
    agents_dir = project_root / ".agents"
    output_dir = project_root / ".md" / "knowledge"

    skills_dir = agents_dir / "skills"
    workflows_dir = agents_dir / "workflows"

    skills_output = output_dir / "skills_compiled.md"
    workflows_output = output_dir / "workflows_compiled.md"

    compile_skills(skills_dir, skills_output)
    compile_workflows(workflows_dir, workflows_output)


if __name__ == "__main__":
    main()
