"""TDD Integration Tests for Greenfield Spoke Initialization & Single-Engine Sync."""

from pathlib import Path

import pytest
import yaml
from scripts.spoke.spoke_synchronizer import SpokeSynchronizer


@pytest.fixture
def mock_hub(tmp_path: Path) -> Path:
    """Fixture creating a mock Hub directory with platform catalog and sample skills/workflows."""
    hub_dir = tmp_path / "mock-hub"
    hub_dir.mkdir(parents=True, exist_ok=True)

    # 1. Setup catalog.yaml
    agents_dir = hub_dir / ".agents"
    platform_loader_dir = agents_dir / "skills" / "platform-loader"
    platform_loader_dir.mkdir(parents=True, exist_ok=True)

    catalog_data = {
        "bundles": {
            "Phần mềm": ["_core", "_software"],
            "Thẩm tra thiết kế": ["_core", "_qc", "_consulting"],
        },
        "skills": [
            {
                "name": "core-skill",
                "bundle": "_core",
                "skill_path": ".agents/skills/core-skill/SKILL.md",
            },
            {
                "name": "software-skill",
                "bundle": "_software",
                "skill_path": ".agents/skills/software-skill/SKILL.md",
            },
        ],
        "workflows": [
            {
                "name": "core-workflow",
                "bundle": "_core",
                "workflow_path": ".agents/workflows/core-workflow.md",
            },
            {
                "name": "software-workflow",
                "bundle": "_software",
                "workflow_path": ".agents/workflows/software-workflow.md",
            },
        ],
    }
    with open(platform_loader_dir / "catalog.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(catalog_data, f)

    # 2. Setup skills and workflows
    core_skill_dir = agents_dir / "skills" / "core-skill"
    core_skill_dir.mkdir(parents=True, exist_ok=True)
    (core_skill_dir / "SKILL.md").write_text("# Core Skill", encoding="utf-8")

    software_skill_dir = agents_dir / "skills" / "software-skill"
    software_skill_dir.mkdir(parents=True, exist_ok=True)
    (software_skill_dir / "SKILL.md").write_text("# Software Skill", encoding="utf-8")

    workflows_dir = agents_dir / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / "core-workflow.md").write_text("# Core Workflow", encoding="utf-8")
    (workflows_dir / "software-workflow.md").write_text("# Software Workflow", encoding="utf-8")

    # 3. Setup AGENTS.md, conftest.py, and scripts/safe_pytest.py
    (agents_dir / "AGENTS.md").write_text("# Hub AGENTS.md", encoding="utf-8")
    (hub_dir / "conftest.py").write_text("# Hub conftest.py", encoding="utf-8")
    scripts_dir = hub_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "safe_pytest.py").write_text("# Hub safe_pytest.py", encoding="utf-8")

    return hub_dir


def test_greenfield_spoke_init_and_sync_software(tmp_path: Path, mock_hub: Path):
    """Verifies that a newly initialized Greenfield software spoke receives bundles and test guardrails."""
    spoke_dir = tmp_path / "new-greenfield-software-spoke"
    spoke_dir.mkdir(parents=True, exist_ok=True)

    # Simulate steps 1-3 of /ccba-init-spoke
    md_dir = spoke_dir / ".md"
    md_dir.mkdir(parents=True, exist_ok=True)
    context_data = {
        "project": {
            "name": "new-greenfield-software-spoke",
            "type": "Phần mềm",
            "mode": "software",
            "hub_path": str(mock_hub),
        }
    }
    with open(md_dir / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(context_data, f)

    # Simulate step 5: execute sync_spoke
    synchronizer = SpokeSynchronizer(str(spoke_dir))
    exit_code = synchronizer.sync(dry_run=False)

    assert exit_code == 0
    # 1. Skills and workflows copied
    assert (spoke_dir / ".agents" / "skills" / "core-skill" / "SKILL.md").exists()
    assert (spoke_dir / ".agents" / "skills" / "software-skill" / "SKILL.md").exists()
    assert (spoke_dir / ".agents" / "workflows" / "core-workflow.md").exists()
    assert (spoke_dir / ".agents" / "workflows" / "software-workflow.md").exists()

    # 2. AGENTS.md copied
    assert (spoke_dir / ".agents" / "AGENTS.md").exists()

    # 3. Test guardrails copied for software project
    assert (spoke_dir / "conftest.py").exists()
    assert (spoke_dir / "scripts" / "safe_pytest.py").exists()


def test_greenfield_spoke_init_and_sync_consulting(tmp_path: Path, mock_hub: Path):
    """Verifies that a newly initialized Greenfield consulting spoke does NOT receive test guardrails."""
    spoke_dir = tmp_path / "new-greenfield-consulting-spoke"
    spoke_dir.mkdir(parents=True, exist_ok=True)

    # Setup context
    md_dir = spoke_dir / ".md"
    md_dir.mkdir(parents=True, exist_ok=True)
    context_data = {
        "project": {
            "name": "new-greenfield-consulting-spoke",
            "type": "Thẩm tra thiết kế",
            "mode": "delivery",
            "hub_path": str(mock_hub),
        }
    }
    with open(md_dir / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(context_data, f)

    synchronizer = SpokeSynchronizer(str(spoke_dir))
    exit_code = synchronizer.sync(dry_run=False)

    assert exit_code == 0
    # 1. Core skills and workflows copied, but software-skill NOT copied
    assert (spoke_dir / ".agents" / "skills" / "core-skill" / "SKILL.md").exists()
    assert not (spoke_dir / ".agents" / "skills" / "software-skill").exists()
    assert (spoke_dir / ".agents" / "workflows" / "core-workflow.md").exists()
    assert not (spoke_dir / ".agents" / "workflows" / "software-workflow.md").exists()

    # 2. Test guardrails not needed for delivery consulting spoke
    assert not (spoke_dir / "conftest.py").exists()
    assert not (spoke_dir / "scripts" / "safe_pytest.py").exists()
