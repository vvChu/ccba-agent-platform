#!/usr/bin/env python3
"""Verification script for Legal Intelligence Pipeline.

Validates that cleaning utilities, slug generation, and key imports
function correctly in the pipeline.
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path to import legal_intelligence

from legal_intelligence import Cleaners, OKFBundlePackager


class TestLegalIntelligence(unittest.TestCase):
    """Unit tests for cleaning utilities and packager."""

    def test_strip_think_tags(self) -> None:
        """Verify that <think> blocks are stripped correctly."""
        raw_text = "<think>\nAnalyzing legal definitions...\n</think>\nActual legal text content."
        expected = "Actual legal text content."
        self.assertEqual(Cleaners.strip_think_tags(raw_text), expected)

    def test_strip_unclosed_think_tags(self) -> None:
        """Verify that unclosed <think> blocks are stripped."""
        raw_text = "Standard text\n<think>\nAnalyzing..."
        expected = "Standard text"
        self.assertEqual(Cleaners.strip_think_tags(raw_text), expected)

    def test_extract_json_markdown(self) -> None:
        """Verify extraction of JSON wrapped in Markdown code blocks."""
        raw_text = """
Random thoughts from model...
```json
{
  "key": "value",
  "num": 42
}
```
"""
        extracted = Cleaners.extract_json(raw_text)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("key"), "value")
        self.assertEqual(extracted.get("num"), 42)

    def test_extract_raw_json(self) -> None:
        """Verify extraction of raw JSON dictionary."""
        raw_text = '{"name": "test"}'
        extracted = Cleaners.extract_json(raw_text)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("name"), "test")

    def test_sanitize_slug(self) -> None:
        """Verify that slug generator removes accents and special characters."""
        packager = OKFBundlePackager(Path())
        title = "Luật Xây dựng 2025 số 135/2025/QH15"
        expected = "luat_xay_dung_2025_so_135_2025_qh15"
        self.assertEqual(packager.sanitize_slug(title), expected)


def main() -> None:
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLegalIntelligence)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("\n[Verify] All tests passed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
