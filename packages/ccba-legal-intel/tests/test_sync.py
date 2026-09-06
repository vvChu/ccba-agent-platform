import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ccba_legal import LegalSyncEngine
from ccba_legal.sync import (
    calculate_md5,
    calculate_sha256,
    get_credentials_dir,
    migrate_drive_credentials,
)


class TestLegalSyncEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = LegalSyncEngine()

    def test_calculate_file_hashes(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write("Hello Legal Sync Engine")
            tmp_path = Path(f.name)

        try:
            hashes = self.engine.calculate_file_hashes(tmp_path)
            self.assertIn("md5", hashes)
            self.assertIn("sha256", hashes)
            self.assertEqual(hashes["md5"], calculate_md5(tmp_path))
            self.assertEqual(hashes["sha256"], calculate_sha256(tmp_path))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_verify_environment(self) -> None:
        env_status = self.engine.verify_environment()
        self.assertIn("google_api", env_status)
        self.assertIn("chrome_cdp", env_status)
        self.assertIn("chrome_port_open", env_status)

    def test_get_credentials_dir_default_and_env(self) -> None:
        """Verify get_credentials_dir respects CCBA_CREDENTIALS_DIR override."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCBA_CREDENTIALS_DIR", None)
            default_dir = get_credentials_dir()
            self.assertTrue(str(default_dir).endswith(os.path.join(".ccba", "credentials")))

            os.environ["CCBA_CREDENTIALS_DIR"] = "/tmp/custom_creds"
            custom_dir = get_credentials_dir()
            self.assertEqual(custom_dir, Path("/tmp/custom_creds"))

    def test_migrate_drive_credentials_no_op_when_empty(self) -> None:
        """Verify migrate_drive_credentials handles missing legacy files cleanly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "creds"
            # Should not crash or create folder if no legacy files exist
            migrate_drive_credentials(target_dir=target_dir)
            self.assertFalse(target_dir.exists())
