"""test_sync.py - Unit tests for LegalSyncEngine in ccba_legal."""

import tempfile
import unittest
from pathlib import Path

from ccba_legal import LegalSyncEngine
from ccba_legal.sync import calculate_md5, calculate_sha256


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
