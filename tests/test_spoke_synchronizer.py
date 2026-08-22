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
            "Thiết kế": ["_core", "_consulting"],
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

    # 2. Setup skill directories
    core_skill_dir = agents_dir / "skills" / "core-skill"
    core_skill_dir.mkdir(parents=True, exist_ok=True)
    (core_skill_dir / "SKILL.md").write_text("# Core Skill Hub Content", encoding="utf-8")

    software_skill_dir = agents_dir / "skills" / "software-skill"
    software_skill_dir.mkdir(parents=True, exist_ok=True)
    (software_skill_dir / "SKILL.md").write_text("# Software Skill Hub Content", encoding="utf-8")

    # 3. Setup workflows
    workflows_dir = agents_dir / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / "core-workflow.md").write_text("# Core Workflow v2.0", encoding="utf-8")
    (workflows_dir / "software-workflow.md").write_text(
        "# Software Workflow v2.0", encoding="utf-8"
    )

    # 4. Setup AGENTS.md
    (agents_dir / "AGENTS.md").write_text("# Hub Constitution", encoding="utf-8")

    return hub_dir


@pytest.fixture
def mock_spoke(tmp_path: Path, mock_hub: Path) -> Path:
    """Fixture creating a mock Spoke directory with context."""
    spoke_dir = tmp_path / "mock-spoke"
    spoke_dir.mkdir(parents=True, exist_ok=True)

    md_dir = spoke_dir / ".md"
    md_dir.mkdir(parents=True, exist_ok=True)

    context_data = {
        "project_name": "MOCK-TEST-SPOKE",
        "project_type": "Phần mềm",
        "hub_path": str(mock_hub),
    }
    with open(md_dir / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(context_data, f)

    return spoke_dir


def test_dry_run_does_not_modify_files(mock_spoke: Path, mock_hub: Path):
    """Verifies that --dry-run performs a simulation without creating or modifying any files."""
    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=True)

    assert result == 0
    spoke_agents_dir = mock_spoke / ".agents"
    # In dry-run mode, .agents directory should NOT even be created if it didn't exist
    assert not (spoke_agents_dir / "workflows" / "core-workflow.md").exists()
    assert not (spoke_agents_dir / "skills" / "core-skill").exists()


def test_selective_merge_preserves_custom_spoke_workflows(mock_spoke: Path, mock_hub: Path):
    """Verifies that non-destructive sync preserves custom internal Spoke workflows."""
    spoke_wf_dir = mock_spoke / ".agents" / "workflows"
    spoke_wf_dir.mkdir(parents=True, exist_ok=True)

    # User creates a custom workflow inside their Spoke
    custom_wf_file = spoke_wf_dir / "custom_spoke_internal_flow.md"
    custom_wf_file.write_text("# My Custom Internal Workflow", encoding="utf-8")

    # Run full sync
    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False)

    assert result == 0
    # 1. Hub workflows must be copied
    assert (spoke_wf_dir / "core-workflow.md").exists()
    assert (spoke_wf_dir / "software-workflow.md").exists()
    # 2. Custom internal workflow MUST be preserved 100%
    assert custom_wf_file.exists()
    assert custom_wf_file.read_text(encoding="utf-8") == "# My Custom Internal Workflow"


def test_selective_merge_updates_modified_hub_workflows(mock_spoke: Path, mock_hub: Path):
    """Verifies that outdated Hub workflows at Spoke are correctly updated with new content."""
    spoke_wf_dir = mock_spoke / ".agents" / "workflows"
    spoke_wf_dir.mkdir(parents=True, exist_ok=True)

    # Outdated workflow
    core_wf_file = spoke_wf_dir / "core-workflow.md"
    core_wf_file.write_text("# Core Workflow OLD v1.0", encoding="utf-8")

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False)

    assert result == 0
    # Outdated workflow should be updated to v2.0
    assert core_wf_file.read_text(encoding="utf-8") == "# Core Workflow v2.0"


def test_sync_single_item_on_demand(mock_spoke: Path, mock_hub: Path):
    """Verifies on-demand sync of a single skill."""
    synchronizer = SpokeSynchronizer(str(mock_spoke))

    # 1. Dry run single item
    dry_result = synchronizer.sync(sync_item="software-skill", dry_run=True)
    assert dry_result == 0
    assert not (mock_spoke / ".agents" / "skills" / "software-skill").exists()

    # 2. Execute single item
    exec_result = synchronizer.sync(sync_item="software-skill", dry_run=False)
    assert exec_result == 0
    assert (mock_spoke / ".agents" / "skills" / "software-skill" / "SKILL.md").exists()
    # Other skills should not be copied
    assert not (mock_spoke / ".agents" / "skills" / "core-skill").exists()


def test_sync_creates_backup_snapshot(mock_spoke: Path, mock_hub: Path):
    """Verifies that actual sync automatically creates a snapshot backup of .agents/."""
    spoke_agents_dir = mock_spoke / ".agents"
    spoke_agents_dir.mkdir(parents=True, exist_ok=True)
    (spoke_agents_dir / "original_file.txt").write_text("old version", encoding="utf-8")

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False, backup=True)
    assert result == 0

    backups = synchronizer.list_backups()
    assert len(backups) >= 1
    latest_backup = backups[0]
    assert (latest_backup / "original_file.txt").exists()
    assert (latest_backup / "original_file.txt").read_text(encoding="utf-8") == "old version"


def test_sync_blocks_on_dirty_working_tree_unless_forced(mock_spoke: Path, mock_hub: Path, monkeypatch: pytest.MonkeyPatch):
    """Verifies that sync blocks execution on dirty git working tree unless force=True."""
    from scripts.spoke.spoke_synchronizer import GitWorkingTreeGuard

    # Mock dirty working tree
    monkeypatch.setattr(
        GitWorkingTreeGuard,
        "check_clean_working_tree",
        lambda self, path_filter=".agents": (False, " M .agents/workflows/modified.md"),
    )

    synchronizer = SpokeSynchronizer(str(mock_spoke))

    # Without force -> should return 1 (blocked)
    res_blocked = synchronizer.sync(dry_run=False, force=False, check_git=True)
    assert res_blocked == 1

    # With force -> should proceed (return 0)
    res_forced = synchronizer.sync(dry_run=False, force=True, check_git=True)
    assert res_forced == 0


def test_rollback_restores_previous_agents_state(mock_spoke: Path, mock_hub: Path):
    """Verifies that rollback() restores the .agents directory from the snapshot."""
    spoke_wf_dir = mock_spoke / ".agents" / "workflows"
    spoke_wf_dir.mkdir(parents=True, exist_ok=True)
    custom_wf = spoke_wf_dir / "my_custom_doc.md"
    custom_wf.write_text("# Initial Custom Doc", encoding="utf-8")

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    # Sync creates a backup snapshot
    res = synchronizer.sync(dry_run=False, backup=True)
    assert res == 0

    # User accidentally corrupts or deletes a file
    custom_wf.write_text("# Corrupted Doc", encoding="utf-8")
    assert custom_wf.read_text(encoding="utf-8") == "# Corrupted Doc"

    # Rollback
    rollback_ok = synchronizer.rollback()
    assert rollback_ok is True
    assert custom_wf.read_text(encoding="utf-8") == "# Initial Custom Doc"

