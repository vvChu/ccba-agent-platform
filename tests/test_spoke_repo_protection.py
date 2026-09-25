"""Unit tests for automated Spoke repository protection and security guardrails.

Complies with ADR-0058, CCBA-SOP-SEC-001, and Session Learning invariants.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from scripts.spoke.spoke_adopter import install_security_guardrails
from scripts.spoke.spoke_bootstrap import SpokeBootstrapper
from scripts.spoke.spoke_initializer import SpokeInitializer


@pytest.fixture
def temp_spoke(tmp_path: Path) -> Path:
    """Provides an isolated spoke repository workspace."""
    spoke_dir = tmp_path / "test_spoke"
    spoke_dir.mkdir(parents=True, exist_ok=True)
    return spoke_dir


@pytest.fixture
def temp_hub(tmp_path: Path) -> Path:
    """Provides an isolated hub directory."""
    hub_dir = tmp_path / "test_hub"
    hub_dir.mkdir(parents=True, exist_ok=True)
    (hub_dir / "scripts").mkdir()
    (hub_dir / "scripts" / "maskara.py").write_text("# maskara\n", encoding="utf-8")
    return hub_dir


def test_install_guardrails_no_git_skips_safely(temp_spoke: Path, temp_hub: Path):
    """Gracefully skips when directory does not have a .git entry (OneDrive/SharePoint mode)."""
    installed = install_security_guardrails(temp_spoke, temp_hub, dry_run=False)
    assert installed is False
    assert not (temp_spoke / ".githooks").exists()
    assert not (temp_spoke / ".github").exists()


def test_install_guardrails_dry_run_creates_no_files(temp_spoke: Path, temp_hub: Path):
    """Ensures dry-run mode returns True without modifying filesystem."""
    (temp_spoke / ".git").mkdir()
    installed = install_security_guardrails(temp_spoke, temp_hub, dry_run=True)
    assert installed is True
    assert not (temp_spoke / ".githooks").exists()
    assert not (temp_spoke / ".github").exists()


def test_install_guardrails_full_setup(temp_spoke: Path, temp_hub: Path):
    """Verifies complete creation of .githooks, CODEOWNERS, and .gitattributes."""
    (temp_spoke / ".git").mkdir()

    installed = install_security_guardrails(
        temp_spoke, temp_hub, dry_run=False, code_owner="@maintainer"
    )
    assert installed is True

    # 1. Check .githooks/pre-commit
    pre_commit = temp_spoke / ".githooks" / "pre-commit"
    assert pre_commit.exists()
    pre_commit_content = pre_commit.read_text(encoding="utf-8")
    assert "Maskara" in pre_commit_content
    assert "CCBA Guardrail" in pre_commit_content

    # 2. Check .githooks/pre-push
    pre_push = temp_spoke / ".githooks" / "pre-push"
    assert pre_push.exists()
    pre_push_content = pre_push.read_text(encoding="utf-8")
    assert "refs/heads/main" in pre_push_content
    assert "Direct push to" in pre_push_content

    # 3. Check executable bits on POSIX
    if os.name == "posix":
        assert pre_commit.stat().st_mode & 0o111 != 0
        assert pre_push.stat().st_mode & 0o111 != 0

    # 4. Check .github/CODEOWNERS
    codeowners = temp_spoke / ".github" / "CODEOWNERS"
    assert codeowners.exists()
    codeowners_content = codeowners.read_text(encoding="utf-8")
    assert "* @maintainer" in codeowners_content

    # 5. Check .gitattributes
    gitattributes = temp_spoke / ".gitattributes"
    assert gitattributes.exists()
    gitattr_content = gitattributes.read_text(encoding="utf-8")
    assert ".githooks/* text eol=lf" in gitattr_content


def test_codeowners_preservation(temp_spoke: Path, temp_hub: Path):
    """Ensures existing custom CODEOWNERS file is preserved 100% (non-destructive)."""
    (temp_spoke / ".git").mkdir()
    github_dir = temp_spoke / ".github"
    github_dir.mkdir(parents=True)
    custom_content = "# Custom Charter\n* @custom_lead\n"
    (github_dir / "CODEOWNERS").write_text(custom_content, encoding="utf-8")

    install_security_guardrails(
        temp_spoke, temp_hub, dry_run=False, code_owner="@overwriting_attempt"
    )

    # Assert content was not modified
    assert (github_dir / "CODEOWNERS").read_text(encoding="utf-8") == custom_content


def test_gitattributes_idempotency(temp_spoke: Path, temp_hub: Path):
    """Ensures multiple runs do not duplicate the .githooks/* rule in .gitattributes."""
    (temp_spoke / ".git").mkdir()

    install_security_guardrails(temp_spoke, temp_hub, dry_run=False)
    install_security_guardrails(temp_spoke, temp_hub, dry_run=False)

    gitattr_content = (temp_spoke / ".gitattributes").read_text(encoding="utf-8")
    assert gitattr_content.count(".githooks/* text eol=lf") == 1


def test_spoke_bootstrapper_ensure_githooks_configured(temp_spoke: Path, temp_hub: Path):
    """Tests that SpokeBootstrapper configures core.hooksPath when .githooks exists."""
    bootstrapper = SpokeBootstrapper(spoke_path=temp_spoke, hub_path=temp_hub)

    # 1. No git or .githooks -> returns False
    assert bootstrapper.ensure_githooks_configured(dry_run=False) is False

    # 2. Both exist -> dry-run returns True
    (temp_spoke / ".git").mkdir()
    (temp_spoke / ".githooks").mkdir()
    assert bootstrapper.ensure_githooks_configured(dry_run=True) is True


def test_spoke_initializer_delegates_guardrails(temp_spoke: Path, temp_hub: Path):
    """Tests that SpokeInitializer delegates to install_security_guardrails properly."""
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    (temp_spoke / ".git").mkdir()

    # Dry-run
    res_dry = init.install_security_guardrails(dry_run=True)
    assert res_dry is True
    assert not (temp_spoke / ".githooks").exists()

    # Real run
    res_real = init.install_security_guardrails(dry_run=False, code_owner="@team")
    assert res_real is True
    assert (temp_spoke / ".githooks" / "pre-commit").exists()
    assert (temp_spoke / ".github" / "CODEOWNERS").exists()
    assert "* @team" in (temp_spoke / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
