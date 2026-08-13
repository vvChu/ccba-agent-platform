"""test_maskara.py - Unit tests for MaskaraScanner deep module."""

import sys
import tempfile
import unittest
from pathlib import Path

# Ensure scripts directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from maskara import MaskaraScanner


class TestMaskaraScanner(unittest.TestCase):
    def setUp(self) -> None:
        self.scanner = MaskaraScanner()

    def test_scan_text_openai_key(self) -> None:
        content = "Here is my secret API key: sk-proj-1234567890abcdef1234567890 for testing."
        findings = self.scanner.scan_text(content, filepath="test.py", agent="test")
        self.assertTrue(len(findings) > 0)
        self.assertEqual(findings[0]["rule_id"], "openai-api-key")
        self.assertIn("sk-p...7890", findings[0]["preview"])

    def test_redact_text(self) -> None:
        content = "My token is ghp_1234567890abcdef1234567890abcdef123456."
        redacted = self.scanner.redact_text(content)
        self.assertNotIn("ghp_1234567890abcdef1234567890abcdef123456", redacted)
        self.assertIn("[MASKARA_REDACTED:github-token]", redacted)

    def test_scan_safe_strings_ignored(self) -> None:
        content = "Using mock key your_key_here or sk-spark-secure-key-2026."
        findings = self.scanner.scan_text(content)
        self.assertEqual(len(findings), 0)

    def test_scan_file_and_perform_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "session.log"
            file_path.write_text(
                "Database at postgresql://user:pass1234@localhost:5432/mydb\n", encoding="utf-8"
            )

            targets = [{"agent": "test", "root": Path(tmpdir)}]
            result = self.scanner.perform_scan(targets)
            self.assertEqual(result["files_scanned"], 1)
            self.assertTrue(len(result["findings"]) > 0)
            self.assertEqual(result["findings"][0]["rule_id"], "database-url")

    def test_cli_scan_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "clean.log"
            file_path.write_text("All clean content here without secrets.\n", encoding="utf-8")

            exit_code = self.scanner.run_cli(["scan", "--root", tmpdir])
            self.assertEqual(exit_code, 0)
