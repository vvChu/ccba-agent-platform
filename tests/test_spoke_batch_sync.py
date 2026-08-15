"""TDD Unit & Integration Tests for Multi-Spoke Batch Sync and Health Dashboard."""

from pathlib import Path

import pytest
import yaml
from scripts.ccba_platform_cli import display_spoke_health_dashboard
from scripts.spoke.spoke_synchronizer import sync_all_spokes


@pytest.fixture
def mock_hub_with_spokes(tmp_path: Path) -> tuple[Path, list[Path]]:
    """Fixture creating a mock Hub with multiple registered Spokes in decrypted cache."""
    hub_dir = tmp_path / "mock-hub"
    hub_dir.mkdir(parents=True, exist_ok=True)

    # Setup catalog
    agents_dir = hub_dir / ".agents"
    loader_dir = agents_dir / "skills" / "platform-loader"
    loader_dir.mkdir(parents=True, exist_ok=True)

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
            }
        ],
        "workflows": [
            {
                "name": "core-workflow",
                "bundle": "_core",
                "workflow_path": ".agents/workflows/core-workflow.md",
            }
        ],
    }
    with open(loader_dir / "catalog.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(catalog_data, f)

    (agents_dir / "skills" / "core-skill").mkdir(parents=True, exist_ok=True)
    (agents_dir / "skills" / "core-skill" / "SKILL.md").write_text("# Core", encoding="utf-8")

    (agents_dir / "workflows").mkdir(parents=True, exist_ok=True)
    (agents_dir / "workflows" / "core-workflow.md").write_text("# Workflow", encoding="utf-8")
    (agents_dir / "AGENTS.md").write_text("# Agents", encoding="utf-8")

    # Create 2 mock Spokes
    spoke1 = tmp_path / "mock-spoke-1"
    spoke1.mkdir(parents=True, exist_ok=True)
    (spoke1 / ".md").mkdir(parents=True, exist_ok=True)
    with open(spoke1 / ".md" / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {
                "project": {
                    "name": "mock-spoke-1",
                    "type": "Phần mềm",
                    "hub_path": str(hub_dir),
                }
            },
            f,
        )

    spoke2 = tmp_path / "mock-spoke-2"
    spoke2.mkdir(parents=True, exist_ok=True)
    (spoke2 / ".md").mkdir(parents=True, exist_ok=True)
    with open(spoke2 / ".md" / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {
                "project": {
                    "name": "mock-spoke-2",
                    "type": "Thiết kế",
                    "hub_path": str(hub_dir),
                }
            },
            f,
        )

    # Setup decrypted registry cache on Hub
    hub_md_data = hub_dir / ".md" / "data"
    hub_md_data.mkdir(parents=True, exist_ok=True)
    registry_cache = {
        "spokes": [
            {
                "name": "mock-spoke-1",
                "path": str(spoke1),
                "project_type": "Phần mềm",
                "last_sync": "2026-08-15T12:00:00.000000",
                "spoke_id": "id-1",
            },
            {
                "name": "mock-spoke-2",
                "path": str(spoke2),
                "project_type": "Thiết kế",
                "last_sync": "2026-07-01T10:00:00.000000",
                "spoke_id": "id-2",
            },
        ]
    }
    with open(hub_md_data / "spoke_registry_decrypted.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(registry_cache, f)

    return hub_dir, [spoke1, spoke2]


def test_sync_all_spokes_dry_run(mock_hub_with_spokes: tuple[Path, list[Path]]):
    """Verifies that batch sync --dry-run simulates sync across all registered spokes without file mutations."""
    hub_dir, spokes = mock_hub_with_spokes
    exit_code = sync_all_spokes(hub_root=hub_dir, dry_run=True)

    assert exit_code == 0
    # No files should have been copied to either spoke
    for sp in spokes:
        assert not (sp / ".agents" / "skills" / "core-skill").exists()
        assert not (sp / ".agents" / "workflows" / "core-workflow.md").exists()


def test_sync_all_spokes_batch_execution(mock_hub_with_spokes: tuple[Path, list[Path]]):
    """Verifies that batch sync executes successfully across all registered spokes."""
    hub_dir, spokes = mock_hub_with_spokes
    exit_code = sync_all_spokes(hub_root=hub_dir, dry_run=False)

    assert exit_code == 0
    # Both spokes should now have received the core skills and workflows
    for sp in spokes:
        assert (sp / ".agents" / "skills" / "core-skill" / "SKILL.md").exists()
        assert (sp / ".agents" / "workflows" / "core-workflow.md").exists()
        assert (sp / ".agents" / "AGENTS.md").exists()


def test_display_spoke_health_dashboard(mock_hub_with_spokes: tuple[Path, list[Path]], capsys):
    """Verifies that the health dashboard accurately displays active and outdated spoke statuses."""
    hub_dir, _ = mock_hub_with_spokes
    exit_code = display_spoke_health_dashboard(hub_root=hub_dir)

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "CCBA SPOKE HEALTH & DRIFT DASHBOARD" in captured
    assert "mock-spoke-1" in captured
    assert "mock-spoke-2" in captured
    assert "🟢 ACTIVE" in captured
    assert "⚠️ OUTDATED" in captured  # mock-spoke-2 last_sync is > 30 days ago
