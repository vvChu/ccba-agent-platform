"""Unit Tests for CCBA Scaffolding Tools (ADR-020).

Tests ArchStatsUpdater and RepomixPackager along with backward-compatible forwarding facades.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.scaffolding import (
    ArchStatsUpdater,
    RepomixPackager,
    run_repomix_pack,
)
from scripts.security.repomix_pack import run_repomix


class TestArchStatsUpdater(unittest.TestCase):
    def test_get_counts_structure(self) -> None:
        updater = ArchStatsUpdater()
        counts = updater.get_counts()
        self.assertIn("SKILL_COUNT", counts)
        self.assertIn("WORKFLOW_COUNT", counts)
        self.assertIn("PACKAGE_COUNT", counts)
        self.assertTrue(counts["SKILL_COUNT"].isdigit())
        self.assertTrue(counts["WORKFLOW_COUNT"].isdigit())
        self.assertTrue(counts["PACKAGE_COUNT"].isdigit())

    def test_update_file_marker_replacement(self) -> None:
        updater = ArchStatsUpdater()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_doc = Path(tmpdir) / "README.md"
            tmp_doc.write_text(
                "Total Skills: <!-- SKILL_COUNT_START -->10<!-- SKILL_COUNT_END -->\n"
                "Total Workflows: <!-- WORKFLOW_COUNT_START -->5<!-- WORKFLOW_COUNT_END -->\n",
                encoding="utf-8",
            )

            counts = {"SKILL_COUNT": "42", "WORKFLOW_COUNT": "15", "PACKAGE_COUNT": "8"}
            changed = updater.update_file(tmp_doc, counts)
            self.assertTrue(changed)

            new_content = tmp_doc.read_text(encoding="utf-8")
            self.assertIn("<!-- SKILL_COUNT_START -->42<!-- SKILL_COUNT_END -->", new_content)
            self.assertIn("<!-- WORKFLOW_COUNT_START -->15<!-- WORKFLOW_COUNT_END -->", new_content)

            # Idempotent re-run with same counts returns False
            changed_again = updater.update_file(tmp_doc, counts)
            self.assertFalse(changed_again)

    def test_update_all_documents_with_mock_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            updater = ArchStatsUpdater(project_root=tmp_path)

            doc1 = tmp_path / "PLATFORM.md"
            doc1.write_text(
                "Skills: <!-- SKILL_COUNT_START -->999<!-- SKILL_COUNT_END -->", encoding="utf-8"
            )

            counts, modified = updater.update_all_documents(docs=[doc1])
            self.assertEqual(len(modified), 1)
            self.assertIn("SKILL_COUNT", counts)

    def test_root_facade_cli_entry_point(self) -> None:
        """Verify scripts.update_arch_stats exposes a callable main entry point."""
        import scripts.update_arch_stats as root_shim

        self.assertTrue(callable(root_shim.main))


class TestRepomixPackager(unittest.TestCase):
    def setUp(self) -> None:
        self.packager = RepomixPackager()

    def test_build_config_schema(self) -> None:
        out_file = Path("dist/pack.xml")
        config = self.packager.build_config(out_file, exclude_patterns=["*.tmp", "custom_dir"])

        self.assertEqual(config["output"]["style"], "xml")
        self.assertTrue(config["output"]["parsable"])
        self.assertTrue(config["ignore"]["useGitignore"])

        patterns = config["ignore"]["customPatterns"]
        self.assertIn("node_modules", patterns)
        self.assertIn("*.tmp", patterns)
        self.assertIn("custom_dir", patterns)

    def test_check_npx_available_resilience(self) -> None:
        # Fast unit test with mocked subprocess
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            self.assertTrue(self.packager.check_npx_available())

            mock_run.side_effect = FileNotFoundError()
            self.assertFalse(self.packager.check_npx_available())

    def test_security_facade_backward_compatibility(self) -> None:
        self.assertTrue(callable(run_repomix))
        self.assertTrue(callable(run_repomix_pack))


if __name__ == "__main__":
    unittest.main()
