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
    HubDiscoverer,
    HubNotFoundError,
    SpokeSynchronizer,
    TestGuardrailCopier,
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
        """Test TestGuardrailCopier copies conftest.py and safe_pytest.py for software spokes."""
        hub_dir = self.test_root / "hub"
        (hub_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (hub_dir / "conftest.py").write_text("# mock conftest", encoding="utf-8")
        (hub_dir / "scripts" / "safe_pytest.py").write_text("# mock safe_pytest", encoding="utf-8")

        spoke_dir = self.test_root / "spoke_software"
        spoke_dir.mkdir(parents=True, exist_ok=True)
        (spoke_dir / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")

        copier = TestGuardrailCopier(spoke_dir, hub_dir, "Phần mềm")
        copier.copy_if_needed()

        self.assertTrue((spoke_dir / "conftest.py").exists())
        self.assertTrue((spoke_dir / "scripts" / "safe_pytest.py").exists())


if __name__ == "__main__":
    unittest.main()
