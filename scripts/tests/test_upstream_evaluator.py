"""
Unit tests for UpstreamEvaluator module.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure platform root is on sys.path
PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.upstream_evaluator import (
    append_recommendation,
    call_ai_evaluation,
    get_existing_elements,
)


class TestUpstreamEvaluator(unittest.TestCase):
    """Test suite for UpstreamEvaluator functions and classes."""

    def test_get_existing_elements(self):
        """Test reading existing skills and workflows from catalog.yaml."""
        skills, workflows = get_existing_elements()
        self.assertIsInstance(skills, list)
        self.assertIsInstance(workflows, list)
        self.assertIn("platform-loader", skills)

    def test_call_ai_evaluation_duplicate(self):
        """Test evaluation behavior when skill already exists in local catalog."""
        result = call_ai_evaluation("engineer", "platform-loader", "description: test")
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("should_port", True))
        self.assertIn("IGNORE", result.get("reason", "").upper())

    def test_call_ai_evaluation_duplicate_prefix_normalization(self):
        """Test evaluation behavior when upstream skill name lacks ccba- prefix but local catalog has ccba-<name>."""
        result = call_ai_evaluation("engineer", "ask", "description: test ask")
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("should_port", True))
        self.assertIn("IGNORE", result.get("reason", "").upper())

    def test_append_recommendation_parse_protection(self):
        """Test append_recommendation preserves developer notes section."""
        tmp_dir = PLATFORM_ROOT / ".md" / "scratch" / "test_eval"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        rec_file = tmp_dir / "port_recommendations_test.md"

        initial_content = (
            "<!-- AUTO-GENERATED-START -->\n"
            "# Recommendations\n"
            "<!-- AUTO-GENERATED-END -->\n\n"
            "<!-- DEVELOPER-NOTES-START -->\n"
            "## 📝 Developer Notes\n"
            "Custom manual notes here\n"
            "<!-- DEVELOPER-NOTES-END -->"
        )
        rec_file.write_text(initial_content, encoding="utf-8")

        mock_result = {
            "should_port": True,
            "score": 90,
            "reason": "New valuable skill",
            "actionable_steps": ["Step 1", "Step 2"],
        }

        with patch("scripts.spoke.upstream_evaluator.RECOMMENDATIONS_FILE", rec_file):
            append_recommendation("engineer", "unique-new-skill", mock_result)

        updated_content = rec_file.read_text(encoding="utf-8")
        self.assertIn("`unique-new-skill`", updated_content)
        self.assertIn("Custom manual notes here", updated_content)

        # Clean up temporary test file
        if rec_file.exists():
            rec_file.unlink()


if __name__ == "__main__":
    unittest.main()
