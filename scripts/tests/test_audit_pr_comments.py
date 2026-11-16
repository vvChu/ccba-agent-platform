"""Unit tests for audit_pr_comments script.

Verifies detection of pending reviews, recommended changes in review bodies,
and inline comments from GitHub Copilot.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.validation.audit_pr_comments import (
    audit_pull_request,
    fetch_inline_comments,
    fetch_pr_overview,
    get_current_pr_number,
    is_copilot_user,
    parse_cli_args,
    run_command,
)
from scripts.validation.audit_pr_comments import (
    main as audit_main,
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
    def test_audit_pull_request_pr_comments(self, mock_overview, mock_inline):
        """Test that top-level conversation comments from Copilot trigger exit code 1."""
        mock_overview.return_value = {
            "reviewRequests": [],
            "reviews": [],
            "comments": [
                {
                    "id": "conv_123",
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "body": "Please address this PR conversation note.",
                }
            ],
        }
        mock_inline.return_value = []

        code, res = audit_pull_request(104)
        self.assertEqual(code, 1)
        self.assertEqual(res["status"], "CHANGES_RECOMMENDED")
        self.assertEqual(len(res["pr_comment_issues"]), 1)

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

    @patch("scripts.validation.audit_pr_comments.run_command")
    def test_fetch_inline_comments_pagination_and_placeholder(self, mock_run):
        """Test that fetch_inline_comments uses repos/:owner/:repo and --paginate."""
        mock_run.return_value = '[{"id": 1, "body": "test"}]'
        comments = fetch_inline_comments(42)
        self.assertEqual(len(comments), 1)
        cmd_called = mock_run.call_args[0][0]
        self.assertIn("--paginate", cmd_called)
        self.assertIn("repos/:owner/:repo/pulls/42/comments", cmd_called)

    def test_parse_cli_args_variants_and_fail_closed_validation(self):
        """Verify --repo / -R parsing and fail-closed ValueError on invalid CLI flags."""
        self.assertEqual(
            parse_cli_args(["--repo", "vvChu/ccba-agent-platform", "--pr", "770"]),
            (770, "vvChu/ccba-agent-platform"),
        )
        self.assertEqual(
            parse_cli_args(["-R=vvChu/ccba-agent-platform", "770"]),
            (770, "vvChu/ccba-agent-platform"),
        )
        self.assertEqual(
            parse_cli_args(["-R", "vvChu/idop-ccba-way"]), (None, "vvChu/idop-ccba-way")
        )
        for bad_argv in (
            ["--pr", "0"],
            ["--pr=-3"],
            ["--pr", "abc"],
            ["--repo", "badslug"],
            ["--repo"],
            ["--unknown-flag"],
            ["770", "771"],
        ):
            with self.subTest(bad_argv=bad_argv), self.assertRaises(ValueError):
                parse_cli_args(bad_argv)

    @patch(
        "scripts.validation.audit_pr_comments.subprocess.run",
        side_effect=FileNotFoundError("no gh"),
    )
    def test_run_command_wraps_missing_gh_binary(self, _mock_sub):
        """Missing gh executable must raise RuntimeError rather than propagating OSError."""
        with self.assertRaises(RuntimeError):
            run_command(["gh", "pr", "view"])

    @patch("scripts.validation.audit_pr_comments.run_command")
    def test_get_current_pr_number_distinguishes_no_pr_from_repo_or_api_errors(self, mock_run):
        """Return 0 only when --pr absent, repo empty, and gh reports 'no pull requests found'."""
        mock_run.side_effect = RuntimeError(
            'Command gh failed: no pull requests found for branch "main"'
        )
        with patch("sys.argv", ["audit_pr_comments.py"]):
            self.assertEqual(get_current_pr_number(), 0)

        with (
            patch("sys.argv", ["audit_pr_comments.py", "--repo", "vvChu/ccba-agent-platform"]),
            self.assertRaises(RuntimeError),
        ):
            get_current_pr_number()

        mock_run.side_effect = RuntimeError("Command gh failed: HTTP 404: Not Found")
        with patch("sys.argv", ["audit_pr_comments.py"]), self.assertRaises(RuntimeError):
            get_current_pr_number()

    @patch("scripts.validation.audit_pr_comments.run_command")
    def test_cross_repo_fetch_and_paginated_concatenation(self, mock_run):
        """Cross-repo fetches pass --repo / unencoded repos/<repo> and flatten concatenated pages."""
        mock_run.return_value = '{"reviewRequests": [], "reviews": [], "comments": []}'
        fetch_pr_overview(770, repo="vvChu/ccba-agent-platform")
        self.assertEqual(
            mock_run.call_args[0][0][:5],
            ["gh", "pr", "view", "770", "--repo"],
        )
        self.assertEqual(mock_run.call_args[0][0][5], "vvChu/ccba-agent-platform")

        mock_run.return_value = '[{"id": 1, "body": "p1"}]\n[{"id": 2, "body": "p2"}]'
        comments = fetch_inline_comments(770, repo="vvChu/ccba-agent-platform")
        self.assertEqual([c["id"] for c in comments], [1, 2])
        self.assertIn(
            "repos/vvChu/ccba-agent-platform/pulls/770/comments", mock_run.call_args[0][0]
        )

        mock_run.return_value = '[[{"id": 1}]]'
        with self.assertRaises(RuntimeError):
            fetch_inline_comments(770, repo="vvChu/ccba-agent-platform")

    @patch("scripts.validation.audit_pr_comments.fetch_inline_comments")
    @patch("scripts.validation.audit_pr_comments.fetch_pr_overview")
    def test_audit_pull_request_fail_closed_and_pending_short_circuit(self, mock_ov, mock_in):
        """Fetch errors yield (1, FETCH_ERROR) and pending review returns 2 before inline fetch."""
        mock_ov.side_effect = RuntimeError("HTTP 404")
        code, res = audit_pull_request(999999, repo="vvChu/ccba-agent-platform")
        self.assertEqual(code, 1)
        self.assertEqual(res["status"], "FETCH_ERROR")

        mock_ov.side_effect = None
        mock_ov.return_value = {"reviewRequests": [{"login": "copilot-pull-request-reviewer"}]}
        code, res = audit_pull_request(770, repo="vvChu/ccba-agent-platform")
        self.assertEqual(code, 2)
        self.assertEqual(res["status"], "PENDING")
        mock_in.assert_not_called()

        with (
            patch("sys.argv", ["audit_pr_comments.py", "--pr", "0"]),
            self.assertRaises(SystemExit) as cm,
        ):
            audit_main()
        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
