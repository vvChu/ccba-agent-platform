"""Unit tests for scripts/governance/protect_repo.py CLI tool.

Complies with ADR-0058, CCBA-SOP-SEC-001, and Session Learning invariants.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from scripts.governance.protect_repo import (
    build_parser,
    build_ruleset_payload,
    check_admin_permission,
    check_gh_auth,
    check_gh_cli,
    get_ruleset_id_by_name,
    protect_repository,
    resolve_target_repo,
)


def test_build_parser_defaults():
    """Tests CLI argument parser default values."""
    parser = build_parser()
    args = parser.parse_args([])
    assert args.repo is None
    assert args.branch is None
    assert args.checks is None
    assert args.approvals == 0
    assert args.ruleset_name == "Protect Main Branch"
    assert args.no_dependabot is False
    assert args.dry_run is False


def test_build_parser_custom_args():
    """Tests CLI argument parser with explicit flags."""
    parser = build_parser()
    args = parser.parse_args(
        [
            "--repo",
            "my-org/my-project",
            "--branch",
            "master",
            "--checks",
            "test-unit",
            "lint",
            "--approvals",
            "2",
            "--ruleset-name",
            "Custom Ruleset",
            "--no-dependabot",
            "--dry-run",
        ]
    )
    assert args.repo == "my-org/my-project"
    assert args.branch == "master"
    assert args.checks == ["test-unit", "lint"]
    assert args.approvals == 2
    assert args.ruleset_name == "Custom Ruleset"
    assert args.no_dependabot is True
    assert args.dry_run is True


def test_build_ruleset_payload_omits_checks_when_empty():
    """Ensures empty checks list does NOT include required_status_checks rule (prevents HTTP 422)."""
    payload = build_ruleset_payload(
        branch="main",
        checks=None,
        approvals=1,
        ruleset_name="Protect Main Branch",
    )
    rule_types = [r["type"] for r in payload["rules"]]
    assert "deletion" in rule_types
    assert "non_fast_forward" in rule_types
    assert "pull_request" in rule_types
    assert "required_status_checks" not in rule_types

    # Also test empty list
    payload_empty = build_ruleset_payload(branch="main", checks=[])
    rule_types_empty = [r["type"] for r in payload_empty["rules"]]
    assert "required_status_checks" not in rule_types_empty


def test_build_ruleset_payload_includes_checks_when_provided():
    """Ensures status checks are properly formatted with strict policy when provided."""
    checks = ["Test - Python 3.12", "scan"]
    payload = build_ruleset_payload(branch="main", checks=checks, approvals=0)
    rule_types = [r["type"] for r in payload["rules"]]
    assert "required_status_checks" in rule_types

    check_rule = next(r for r in payload["rules"] if r["type"] == "required_status_checks")
    assert check_rule["parameters"]["strict_required_status_checks_policy"] is True
    assert len(check_rule["parameters"]["required_status_checks"]) == 2
    assert check_rule["parameters"]["required_status_checks"][0]["context"] == "Test - Python 3.12"
    assert check_rule["parameters"]["required_status_checks"][1]["context"] == "scan"

    # Verify admin bypass actor
    assert payload["bypass_actors"][0]["actor_id"] == 5
    assert payload["bypass_actors"][0]["actor_type"] == "RepositoryRole"


def test_resolve_target_repo():
    """Tests target repository resolution from arg and git URL formats."""
    # 1. Direct owner/repo argument
    assert resolve_target_repo("vvChu/ccba-agent-platform") == "vvChu/ccba-agent-platform"

    # 2. None when empty and git fails
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert resolve_target_repo(None) is None

    # 3. SSH git origin URL
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="git@github.com:vvChu/my-repo.git\n")
        assert resolve_target_repo(None) == "vvChu/my-repo"

    # 4. HTTPS git origin URL
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="https://github.com/my-org/spoke-project.git\n"
        )
        assert resolve_target_repo(None) == "my-org/spoke-project"


def test_check_gh_cli_and_auth():
    """Tests GitHub CLI presence and auth detection."""
    with patch("shutil.which", return_value="/usr/bin/gh"):
        assert check_gh_cli() is True

    with patch("shutil.which", return_value=None):
        assert check_gh_cli() is False

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert check_gh_auth() is True

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert check_gh_auth() is False


def test_check_admin_permission():
    """Tests repository admin permission verification."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="true\n")
        assert check_admin_permission("owner/repo") is True

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="false\n")
        assert check_admin_permission("owner/repo") is False


def test_get_ruleset_id_by_name():
    """Tests parsing ruleset ID from gh api json response."""
    fake_rulesets = [
        {"id": 101, "name": "Other Ruleset"},
        {"id": 202, "name": "Protect Main Branch"},
    ]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(fake_rulesets))
        assert get_ruleset_id_by_name("owner/repo", "Protect Main Branch") == 202
        assert get_ruleset_id_by_name("owner/repo", "Nonexistent") is None


def test_protect_repository_dry_run_success():
    """Tests that dry-run mode completes successfully without remote mutations."""
    with (
        patch("scripts.governance.protect_repo.check_gh_cli", return_value=True),
        patch("scripts.governance.protect_repo.check_gh_auth", return_value=True),
    ):
        code = protect_repository(
            repo="vvChu/test-repo",
            branch="main",
            dry_run=True,
        )
        assert code == 0


def test_protect_repository_missing_gh_exits_1():
    """Tests that missing gh CLI returns exit code 1."""
    with patch("scripts.governance.protect_repo.check_gh_cli", return_value=False):
        code = protect_repository(repo="vvChu/test-repo")
        assert code == 1


def test_protect_repository_unauthenticated_exits_1():
    """Tests that unauthenticated gh CLI returns exit code 1."""
    with (
        patch("scripts.governance.protect_repo.check_gh_cli", return_value=True),
        patch("scripts.governance.protect_repo.check_gh_auth", return_value=False),
    ):
        code = protect_repository(repo="vvChu/test-repo")
        assert code == 1


def test_protect_repository_non_admin_exits_1():
    """Tests that non-admin user receives clear error and exits with code 1."""
    with (
        patch("scripts.governance.protect_repo.check_gh_cli", return_value=True),
        patch("scripts.governance.protect_repo.check_gh_auth", return_value=True),
        patch("scripts.governance.protect_repo.check_admin_permission", return_value=False),
    ):
        code = protect_repository(repo="vvChu/test-repo", dry_run=False)
        assert code == 1
