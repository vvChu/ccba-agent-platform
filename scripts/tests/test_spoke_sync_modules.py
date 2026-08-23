"""test_spoke_sync_modules.py - Scoped Fast Unit Tests for Modularized Spoke Sync Package.

Validates discovery, catalog merge, registry, backup, sdk inspector, coordinator, and cli.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.spoke.sync import (
    CatalogMerger,
    GitWorkingTreeGuard,
    HubDiscoverer,
    HubNotFoundError,
    SharedSdkInspector,
    SpokeBackupManager,
    SpokeRegistrar,
    SpokeSyncEngine,
    SpokeSynchronizer,
    TestGuardrailCopier,
    are_dirs_identical,
    are_files_identical,
    list_project_backups,
    load_yaml,
    run_spoke_sync_cli,
    safe_remove,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_base_utilities(tmp_path: Path):
    """Test load_yaml, are_files_identical, are_dirs_identical, and safe_remove."""
    f1 = tmp_path / "test1.yaml"
    f2 = tmp_path / "test2.yaml"
    f1.write_text("key: value\n", encoding="utf-8")
    f2.write_text("key: value\n", encoding="utf-8")

    data = load_yaml(f1)
    assert data == {"key": "value"}
    assert are_files_identical(f1, f2)

    f2.write_text("key: different\n", encoding="utf-8")
    assert not are_files_identical(f1, f2)

    d1 = tmp_path / "dir1"
    d2 = tmp_path / "dir2"
    d1.mkdir()
    d2.mkdir()
    (d1 / "sub.txt").write_text("hello", encoding="utf-8")
    (d2 / "sub.txt").write_text("hello", encoding="utf-8")
    assert are_dirs_identical(d1, d2)

    (d2 / "sub.txt").write_text("world", encoding="utf-8")
    assert not are_dirs_identical(d1, d2)

    safe_remove(d1)
    assert not d1.exists()


def test_hub_discoverer_success_and_not_found(tmp_path: Path):
    """Test HubDiscoverer resolution and HubNotFoundError."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()

    # When no valid hub is found anywhere
    discoverer = HubDiscoverer(spoke_root, context={})
    with patch.object(discoverer, "_is_valid_hub", return_value=False):
        with pytest.raises(HubNotFoundError):
            discoverer.discover()

    # Create mock hub with catalog
    hub_root = tmp_path / "hub"
    catalog_path = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_text("skills: []\n", encoding="utf-8")

    context = {"hub_path": str(hub_root)}
    discoverer2 = HubDiscoverer(spoke_root, context=context)
    discovered = discoverer2.discover()
    assert discovered.resolve() == hub_root.resolve()


def test_catalog_merger_atomic(tmp_path: Path):
    """Test CatalogMerger atomic YAML writing."""
    catalog_file = tmp_path / "catalog.yaml"
    merger = CatalogMerger(catalog_file)
    success = merger.atomic_write({"name": "test_hub", "bundles": ["_core"]})
    assert success is True
    assert catalog_file.exists()

    loaded = yaml.safe_load(catalog_file.read_text(encoding="utf-8"))
    assert loaded["name"] == "test_hub"


def test_spoke_registrar_metadata(tmp_path: Path):
    """Test SpokeRegistrar info builder."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    ctx_file = spoke_root / ".md" / "workspace_context.yaml"
    ctx_file.parent.mkdir(parents=True)
    ctx_file.write_text("project:\n  sub_type: personal_sandbox\n", encoding="utf-8")

    registrar = SpokeRegistrar()
    info = registrar.build_spoke_info(spoke_root, tmp_path, "TestSpoke", "Phần mềm")
    assert info["name"] == "TestSpoke"
    assert info["is_sandbox"] is True


def test_sdk_inspector_and_guardrail_copier(tmp_path: Path):
    """Test SharedSdkInspector and TestGuardrailCopier."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    hub_root = tmp_path / "hub"
    hub_root.mkdir()

    # Guardrail copier
    conftest = hub_root / "conftest.py"
    conftest.write_text("# pytest root conftest", encoding="utf-8")
    copier = TestGuardrailCopier(spoke_root, hub_root, "Phần mềm")
    copier.copy_if_needed(dry_run=False)
    assert (spoke_root / "conftest.py").exists()

    # SDK Inspector
    inspector = SharedSdkInspector(spoke_root, hub_root, "Phần mềm")
    assert inspector.is_python_project() is True
    assert isinstance(inspector.resolve_packages_to_check(), list)


def test_backup_and_git_guard(tmp_path: Path):
    """Test SpokeBackupManager and GitWorkingTreeGuard."""
    spoke_root = tmp_path / "spoke"
    agents_dir = spoke_root / ".agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "AGENTS.md").write_text("# Master", encoding="utf-8")

    mgr = SpokeBackupManager(spoke_root)
    backup_path = mgr.create_backup()
    assert backup_path is not None
    assert backup_path.exists()

    backups = mgr.list_backups()
    assert len(backups) == 1

    (agents_dir / "AGENTS.md").write_text("# Modified", encoding="utf-8")
    restored = mgr.restore_backup(backup_path)
    assert restored is True
    assert (agents_dir / "AGENTS.md").read_text(encoding="utf-8") == "# Master"

    guard = GitWorkingTreeGuard(spoke_root)
    assert guard.is_git_repo() is False
    is_clean, _ = guard.check_clean_working_tree()
    assert is_clean is True


def test_coordinator_alias_and_delegates(tmp_path: Path):
    """Test SpokeSynchronizer class, alias, and procedure delegates."""
    assert SpokeSyncEngine is SpokeSynchronizer

    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    (spoke_root / ".agents").mkdir()
    (spoke_root / ".agents" / "workspace_context.yaml").write_text("project_name: Test\n", encoding="utf-8")

    engine = SpokeSynchronizer(spoke_root)
    assert engine.spoke_root.resolve() == spoke_root.resolve()

    backups = list_project_backups(spoke_root)
    assert isinstance(backups, list)


def test_cli_runner_help(capsys):
    """Test run_spoke_sync_cli execution."""
    with pytest.raises(SystemExit) as exc_info:
        run_spoke_sync_cli(["--help"])
    assert exc_info.value.code == 0
