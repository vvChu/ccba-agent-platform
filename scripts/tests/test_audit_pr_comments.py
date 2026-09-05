"""Unit tests for audit_pr_comments script.

Verifies detection of pending reviews, recommended changes in review bodies,
and inline comments from GitHub Copilot.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.validation.audit_pr_comments import (
    audit_pull_request,
    get_current_pr_number,
    is_copilot_user,
)


class TestAuditPRComments(unittest.TestCase):
    """Test suite for audit_pr_comments functions."""

    def test_is_copilot_user(self):
        """Test identification of Copilot reviewer logins."""
        self.assertTrue(is_copilot_user({"login": "copilot-pull-request-reviewer"}))
        self.assertTrue(is_copilot_user({"login": "copilot-pull-request-reviewer[bot]"}))
        self.assertTrue(is_copilot_user({"login": "github-copilot[bot]"}))
        self.assertTrue(is_copilot_user({"login": "Copilot"}))

        self.assertFalse(is_copilot_user({"login": "vvChu"}))
        self.assertFalse(is_copilot_user({"login": "octocat"}))
        self.assertFalse(is_copilot_user(None))
        self.assertFalse(is_copilot_user({}))

    def test_get_current_pr_number_from_cli_args(self):
        """Test parsing PR number from various CLI arguments."""
        with patch("sys.argv", ["audit_pr_comments.py", "241"]):
            self.assertEqual(get_current_pr_number(), 241)

        with patch("sys.argv", ["audit_pr_comments.py", "--pr=240"]):
            self.assertEqual(get_current_pr_number(), 240)

        with patch("sys.argv", ["audit_pr_comments.py", "--pr", "239"]):
            self.assertEqual(get_current_pr_number(), 239)

    @patch("scripts.validation.audit_pr_comments.fetch_inline_comments")
    @patch("scripts.validation.audit_pr_comments.fetch_pr_overview")
    def test_audit_pull_request_pending_review(self, mock_overview, mock_inline):
        """Test that pending review request from Copilot returns exit code 2."""
        mock_overview.return_value = {
            "reviewRequests": [{"login": "copilot-pull-request-reviewer"}],
            "reviews": [],
            "comments": [],
        }
        mock_inline.return_value = []

        code, res = audit_pull_request(100)
        self.assertEqual(code, 2)
        self.assertEqual(res["status"], "PENDING")

    @patch("scripts.validation.audit_pr_comments.fetch_inline_comments")
    @patch("scripts.validation.audit_pr_comments.fetch_pr_overview")
    def test_audit_pull_request_changes_recommended(self, mock_overview, mock_inline):
        """Test that review with 'Changes recommended' returns exit code 1."""
        mock_overview.return_value = {
            "reviewRequests": [],
            "reviews": [
                {
                    "id": "PRR_1",
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "state": "COMMENTED",
                    "body": "### 🟡 Changes recommended\n\nPlease fix the path.",
                }
            ],
            "comments": [],
        }
        mock_inline.return_value = []

        code, res = audit_pull_request(101)
        self.assertEqual(code, 1)
        self.assertEqual(res["status"], "CHANGES_RECOMMENDED")
        self.assertEqual(len(res["review_issues"]), 1)

    @patch("scripts.validation.audit_pr_comments.fetch_inline_comments")
    @patch("scripts.validation.audit_pr_comments.fetch_pr_overview")
    def test_audit_pull_request_inline_comments(self, mock_overview, mock_inline):
        """Test that inline comments from Copilot trigger exit code 1."""
        mock_overview.return_value = {
            "reviewRequests": [],
            "reviews": [],
            "comments": [],
        }
        mock_inline.return_value = [
            {
                "id": "12345",
                "user": {"login": "copilot-pull-request-reviewer[bot]"},
                "path": "test.py",
                "line": 10,
                "body": "Potential bug here.",
            }
        ]

        code, res = audit_pull_request(102)
        self.assertEqual(code, 1)
        self.assertEqual(res["status"], "CHANGES_RECOMMENDED")
        self.assertEqual(len(res["inline_issues"]), 1)

    @patch("scripts.validation.audit_pr_comments.fetch_inline_comments")
    @patch("scripts.validation.audit_pr_comments.fetch_pr_overview")
    def test_audit_pull_request_clean(self, mock_overview, mock_inline):
        """Test that clean Copilot review returns exit code 0."""
        mock_overview.return_value = {
            "reviewRequests": [],
            "reviews": [
                {
                    "id": "PRR_2",
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "state": "APPROVED",
                    "body": "Looks good to me!",
                }
            ],
            "comments": [],
        }
        mock_inline.return_value = []

        code, res = audit_pull_request(103)
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "CLEAN")


if __name__ == "__main__":
    unittest.main()
