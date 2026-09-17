"""Unit tests for check_release_cleanliness script.

Verifies pre-flight cleanliness gate (Cổng 0.1) and post-test hermetic
scoped teardown gate (Cổng 0.3) for release workflows.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validation.check_release_cleanliness import (
    get_porcelain_status,
    is_known_artifact,
    run_post_check,
    run_pre_check,
)


class TestCheckReleaseCleanliness(unittest.TestCase):
    """Test suite for check_release_cleanliness functions."""

    def test_is_known_artifact(self) -> None:
        """Test recognition of known test artifacts and caches."""
        self.assertTrue(is_known_artifact("packages/ccba-legal-intel/tests/fixtures/mock_local_bundles/vn_hn/embeddings.npy"))
        self.assertTrue(is_known_artifact("mock_local_bundles/embeddings.sha256"))
        self.assertTrue(is_known_artifact("ci_log.txt"))
        self.assertTrue(is_known_artifact(".pytest_cache/v/cache/nodeids"))
        self.assertTrue(is_known_artifact("tmp_test_data.json"))
        self.assertTrue(is_known_artifact("scratch/run.tmp"))
        self.assertTrue(is_known_artifact("test_temp_cache"))

        # Negative checks: source files must NEVER be classified as known artifacts
        self.assertFalse(is_known_artifact("packages/ccba-ai/src/ccba_ai/client.py"))
        self.assertFalse(is_known_artifact(".agents/skills/ccba-release-feature/SKILL.md"))
        self.assertFalse(is_known_artifact("docs/adr/0058-deterministic-hard-completion-lock.md"))
        self.assertFalse(is_known_artifact("scripts/validation/check_release_cleanliness.py"))

    @patch("subprocess.run")
    def test_get_porcelain_status_parsing(self, mock_run) -> None:
        """Test parsing of git status --porcelain -z null-terminated output."""
        # Simulated git status -z output: " M file1.py\x00?? new_file.txt\x00"
        mock_run.return_value.stdout = b" M file1.py\x00?? new_file.txt\x00"
        entries = get_porcelain_status()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0], ("M", "file1.py"))
        self.assertEqual(entries[1], ("??", "new_file.txt"))

    @patch("scripts.validation.check_release_cleanliness.get_porcelain_status")
    def test_run_pre_check_clean(self, mock_status) -> None:
        """Test pre-check returns 0 when working tree is completely clean."""
        mock_status.return_value = []
        code = run_pre_check()
        self.assertEqual(code, 0)

    @patch("scripts.validation.check_release_cleanliness.get_porcelain_status")
    def test_run_pre_check_dirty_blocks(self, mock_status) -> None:
        """Test pre-check returns 1 and blocks when working tree has dirty files."""
        mock_status.return_value = [("M", "src/client.py"), ("??", "draft.txt")]
        code = run_pre_check()
        self.assertEqual(code, 1)

    @patch("scripts.validation.check_release_cleanliness.get_porcelain_status")
    def test_run_post_check_clean(self, mock_status) -> None:
        """Test post-check returns 0 when working tree is hermetically clean."""
        mock_status.return_value = []
        code = run_post_check()
        self.assertEqual(code, 0)

    @patch("scripts.validation.check_release_cleanliness.get_porcelain_status")
    def test_run_post_check_with_unknown_source_modifications_blocks(self, mock_status) -> None:
        """Test post-check returns 1 when unknown or source files were modified."""
        mock_status.return_value = [("M", "packages/ccba-ai/src/ccba_ai/client.py")]
        code = run_post_check()
        self.assertEqual(code, 1)

    @patch("scripts.validation.check_release_cleanliness.get_porcelain_status")
    def test_run_post_check_purges_known_artifacts_safely(self, mock_status) -> None:
        """Test post-check safely purges known test artifacts and exits with 0."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            # Create a mock known artifact file inside tmp_root
            artifact_rel = "ci_log.txt"
            artifact_file = tmp_root / artifact_rel
            artifact_file.write_text("temporary test log", encoding="utf-8")
            self.assertTrue(artifact_file.exists())

            mock_status.return_value = [("??", artifact_rel)]
            code = run_post_check(repo_root=tmp_root)
            self.assertEqual(code, 0)
            # Verify file was safely deleted
            self.assertFalse(artifact_file.exists())


if __name__ == "__main__":
    unittest.main()
