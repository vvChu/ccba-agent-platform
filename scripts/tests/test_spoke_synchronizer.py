"""
Unit tests for SpokeSynchronizer deep module.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure platform root is on sys.path
PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.spoke_synchronizer import (
    CatalogMerger,
    GitWorkingTreeGuard,
    HubDiscoverer,
    HubNotFoundError,
    SpokeBackupManager,
    TestGuardrailCopier,
    list_project_backups,
    rollback_project,
)


class TestSpokeSynchronizer(unittest.TestCase):
    """Test suite for SpokeSynchronizer engine components."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_hub_discoverer_success(self):
        """Test HubDiscoverer locates Hub when valid path is provided."""
        hub_dir = self.test_root / "hub"
        catalog_path = hub_dir / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text("bundles: {}", encoding="utf-8")

        spoke_dir = self.test_root / "spoke"
        spoke_dir.mkdir(parents=True, exist_ok=True)

        context = {"hub_path": str(hub_dir)}
        discoverer = HubDiscoverer(spoke_dir, context)
        found_hub = discoverer.discover()
        self.assertEqual(found_hub.resolve(), hub_dir.resolve())

    def test_hub_discoverer_not_found(self):
        """Test HubDiscoverer raises HubNotFoundError when Hub cannot be found."""
        spoke_dir = self.test_root / "spoke_isolated"
        spoke_dir.mkdir(parents=True, exist_ok=True)

        discoverer = HubDiscoverer(spoke_dir, {})
        with patch.object(discoverer, "_is_valid_hub", return_value=False):
            with self.assertRaises(HubNotFoundError):
                discoverer.discover()

    def test_catalog_merger_atomic(self):
        """Test CatalogMerger performs atomic replace and validation."""
        target_yaml = self.test_root / "catalog.yaml"
        target_yaml.write_text("skills: [{name: test1}]\n", encoding="utf-8")

        new_data = {"skills": [{"name": "test1"}, {"name": "test2"}]}
        merger = CatalogMerger(target_yaml)
        success = merger.atomic_write(new_data)

        self.assertTrue(success)
        content = target_yaml.read_text(encoding="utf-8")
        self.assertIn("test2", content)
        self.assertFalse((self.test_root / ".catalog.yaml.tmp").exists())

    def test_test_guardrail_copier(self):
        """Test TestGuardrailCopier copies conftest.py, safe_pytest.py, and safe_runner.py for software spokes."""
        hub_dir = self.test_root / "hub"
        (hub_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (hub_dir / "conftest.py").write_text("# mock conftest", encoding="utf-8")
        (hub_dir / "scripts" / "safe_pytest.py").write_text("# mock safe_pytest", encoding="utf-8")
        (hub_dir / "scripts" / "safe_runner.py").write_text("# mock safe_runner", encoding="utf-8")

        spoke_dir = self.test_root / "spoke_software"
        spoke_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")

        copier = TestGuardrailCopier(spoke_dir, hub_dir, "Phần mềm")
        copier.copy_if_needed()

        self.assertTrue((spoke_dir / "conftest.py").exists())
        self.assertTrue((spoke_dir / "scripts" / "safe_pytest.py").exists())
        self.assertTrue((spoke_dir / "scripts" / "safe_runner.py").exists())

    def test_git_working_tree_guard_non_git(self):
        """Test GitWorkingTreeGuard returns clean on non-git directory."""
        spoke_dir = self.test_root / "spoke_no_git"
        spoke_dir.mkdir(parents=True, exist_ok=True)

        guard = GitWorkingTreeGuard(spoke_dir)
        is_clean, details = guard.check_clean_working_tree()
        self.assertTrue(is_clean)
        self.assertEqual(details, "")

    def test_git_working_tree_guard_with_dirty_tree(self):
        """Test GitWorkingTreeGuard detects dirty working tree when git reports changes."""
        spoke_dir = self.test_root / "spoke_git"
        (spoke_dir / ".git").mkdir(parents=True, exist_ok=True)

        guard = GitWorkingTreeGuard(spoke_dir)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = " M .agents/workflows/test.md\n"
            is_clean, details = guard.check_clean_working_tree()
            self.assertFalse(is_clean)
            self.assertIn("test.md", details)

    def test_spoke_backup_manager_create_and_restore(self):
        """Test SpokeBackupManager creates snapshot and restores it accurately."""
        spoke_dir = self.test_root / "spoke_backup_test"
        spoke_agents = spoke_dir / ".agents"
        spoke_agents.mkdir(parents=True, exist_ok=True)
        (spoke_agents / "test_file.txt").write_text("initial version", encoding="utf-8")

        mgr = SpokeBackupManager(spoke_dir)
        backup_path = mgr.create_backup()
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue((backup_path / "test_file.txt").exists())

        backups = mgr.list_backups()
        self.assertEqual(len(backups), 1)

        # Modify original file
        (spoke_agents / "test_file.txt").write_text("modified corrupted version", encoding="utf-8")
        self.assertEqual(
            (spoke_agents / "test_file.txt").read_text(encoding="utf-8"),
            "modified corrupted version",
        )

        # Restore from backup
        restored = mgr.restore_backup()
        self.assertTrue(restored)
        self.assertEqual(
            (spoke_agents / "test_file.txt").read_text(encoding="utf-8"), "initial version"
        )

    def test_spoke_sync_engine_alias_and_method(self):
        """Test SpokeSyncEngine alias and sync() method integration."""
        from scripts.spoke import SpokeSyncEngine, SpokeSynchronizer, sync_project

        self.assertIs(SpokeSyncEngine, SpokeSynchronizer)

        spoke_dir = self.test_root / "spoke_engine_test"
        spoke_dir.mkdir(parents=True, exist_ok=True)

        engine = SpokeSyncEngine(spoke_dir)
        self.assertTrue(hasattr(engine, "sync"))
        self.assertTrue(hasattr(engine, "rollback"))
        self.assertTrue(hasattr(engine, "list_backups"))

        # Test sync_project wrapper with mock
        with patch.object(SpokeSynchronizer, "sync_spoke_bundle", return_value=0):
            exit_code = sync_project(spoke_dir)
            self.assertEqual(exit_code, 0)

        # Test rollback_project and list_project_backups wrapper with mock
        with patch.object(SpokeSynchronizer, "rollback", return_value=True):
            self.assertTrue(rollback_project(spoke_dir))

        with patch.object(SpokeSynchronizer, "list_backups", return_value=[]):
            self.assertEqual(list_project_backups(spoke_dir), [])


if __name__ == "__main__":
    unittest.main()
