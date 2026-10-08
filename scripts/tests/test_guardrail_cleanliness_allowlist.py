"""Tests for PR-2: Declarative Guardrails in Catalog & Dynamic Cleanliness Allowlist (ADR-0062)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_missing_guardrails_key_uses_fallback(tmp_path: Path) -> None:
    """When catalog has no 'guardrails' key, TestGuardrailCopier uses TIER0_GUARDRAIL_FALLBACK."""
    from scripts.spoke.sync.sdk_inspector import TestGuardrailCopier

    hub = tmp_path / "hub"
    spoke = tmp_path / "spoke"
    hub.mkdir()
    spoke.mkdir()

    # Create dummy safe_pytest.py on hub
    scripts_dir = hub / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "safe_pytest.py").write_text("# dummy safe pytest", encoding="utf-8")

    copier = TestGuardrailCopier(spoke_root=spoke, hub_root=hub, project_type="Phần mềm")
    # Catalog dict without "guardrails" key
    catalog_data: dict[str, object] = {"hub_path": "."}

    actions = copier.copy_if_needed(catalog=catalog_data, dry_run=True)
    # Fallback should attempt to copy safe_pytest.py
    safe_pytest_actions = [a for a in actions if a["name"] == "safe_pytest.py"]
    assert len(safe_pytest_actions) == 1
    assert safe_pytest_actions[0]["status"] == "NEW"


def test_empty_guardrails_list_copies_nothing(tmp_path: Path) -> None:
    """When catalog explicitly specifies 'guardrails: []', copy NOTHING and do NOT fall back."""
    from scripts.spoke.sync.sdk_inspector import TestGuardrailCopier

    hub = tmp_path / "hub"
    spoke = tmp_path / "spoke"
    hub.mkdir()
    spoke.mkdir()

    # Create dummy safe_pytest.py on hub
    scripts_dir = hub / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "safe_pytest.py").write_text("# dummy safe pytest", encoding="utf-8")

    copier = TestGuardrailCopier(spoke_root=spoke, hub_root=hub, project_type="Phần mềm")
    # Catalog dict with explicit empty list
    catalog_data: dict[str, object] = {"guardrails": []}

    actions = copier.copy_if_needed(catalog=catalog_data, dry_run=False)
    assert actions == []
    assert not (spoke / "scripts" / "safe_pytest.py").exists()


def test_missing_src_reports_status(tmp_path: Path) -> None:
    """When a declared guardrail src does not exist on hub, report status='MISSING_SRC'."""
    from scripts.spoke.sync.sdk_inspector import TestGuardrailCopier

    hub = tmp_path / "hub"
    spoke = tmp_path / "spoke"
    hub.mkdir()
    spoke.mkdir()

    copier = TestGuardrailCopier(spoke_root=spoke, hub_root=hub, project_type="Phần mềm")
    catalog_data = {
        "guardrails": [
            {
                "name": "non_existent.py",
                "src": "scripts/non_existent.py",
                "dest": "scripts/non_existent.py",
                "applies_to": ["python"],
            }
        ]
    }

    actions = copier.copy_if_needed(catalog=catalog_data, dry_run=False)
    missing = [a for a in actions if a.get("status") == "MISSING_SRC"]
    assert len(missing) == 1
    assert missing[0]["name"] == "non_existent.py"
    assert not (spoke / "scripts" / "non_existent.py").exists()


def test_compile_rejects_missing_src_and_bad_dest(tmp_path: Path) -> None:
    """compile_guardrails rejects path traversal, disallowed dest, and missing src."""
    from scripts.governance.compile_catalog import CatalogCompileError, compile_guardrails

    hub = tmp_path / "hub"
    hub.mkdir()

    # 1. Traversal dest
    with pytest.raises(CatalogCompileError, match="traversal"):
        compile_guardrails(
            hub,
            {
                "guardrails": [
                    {
                        "name": "evil",
                        "src": "scripts/a.py",
                        "dest": "../evil.py",
                        "applies_to": ["python"],
                    }
                ]
            },
        )

    # 2. Missing src
    with pytest.raises(CatalogCompileError, match="missing"):
        compile_guardrails(
            hub,
            {
                "guardrails": [
                    {
                        "name": "missing",
                        "src": "scripts/missing.py",
                        "dest": "scripts/missing.py",
                        "applies_to": ["python"],
                    }
                ]
            },
        )


def test_new_guardrail_is_outside_script_budget(tmp_path: Path) -> None:
    """A guardrail declared in catalog is not counted towards the 15-script budget."""
    from scripts.spoke.check_spoke_cleanliness import (
        check_script_count,
        guardrail_script_basename,
    )

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    # Create 15 user scripts
    for i in range(15):
        (scripts_dir / f"user_worker_{i}.py").write_text("print(1)", encoding="utf-8")

    # Add a 16th script which is a new guardrail
    new_guardrail = scripts_dir / "new_compliance_gate.py"
    new_guardrail.write_text("print('gate')", encoding="utf-8")

    # Without catalog allowlist, counted is 16 (> 15)
    counted_raw, _ = check_script_count(scripts_dir, max_scripts=15)
    assert len(counted_raw) == 16

    # With catalog allowlist containing 'new_compliance_gate.py', counted is 15 (<= 15)
    catalog_allowlist = {guardrail_script_basename("scripts/new_compliance_gate.py") or ""}
    counted_with_cat, ignored = check_script_count(
        scripts_dir, max_scripts=15, catalog_allowlist=catalog_allowlist
    )
    assert len(counted_with_cat) == 15
    assert new_guardrail in ignored


def test_git_index_flag_runs_update_index(tmp_path: Path) -> None:
    """When git_index: true, TestGuardrailCopier calls git update-index --chmod=+x."""
    from scripts.spoke.sync.sdk_inspector import TestGuardrailCopier

    hub = tmp_path / "hub"
    spoke = tmp_path / "spoke"
    hub.mkdir()
    spoke.mkdir()
    (spoke / ".git").mkdir()

    hook_hub = hub / ".githooks"
    hook_hub.mkdir()
    (hook_hub / "pre-commit").write_text("#!/bin/sh\nexit 0", encoding="utf-8")

    copier = TestGuardrailCopier(spoke_root=spoke, hub_root=hub, project_type="Phần mềm")
    catalog_data = {
        "guardrails": [
            {
                "name": "pre-commit",
                "src": ".githooks/pre-commit",
                "dest": ".githooks/pre-commit",
                "chmod": "0o755",
                "git_index": True,
                "applies_to": ["all"],
            }
        ]
    }

    with patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(returncode=0, stdout="")
        copier.copy_if_needed(catalog=catalog_data, dry_run=False)

        # Verify git update-index --add --chmod=+x was called for .githooks/pre-commit
        update_calls = [
            call
            for call in mock_subproc.call_args_list
            if "update-index" in call[0][0] and "--chmod=+x" in call[0][0]
        ]
        assert len(update_calls) >= 1


def test_guardrail_migration_cleans_legacy_top_level_scripts(tmp_path: Path) -> None:
    """When a guardrail moves to scripts/_guardrails/, stale scripts/<name> on Spoke is unlinked."""
    from scripts.spoke.sync.sdk_inspector import TestGuardrailCopier

    hub = tmp_path / "hub"
    spoke = tmp_path / "spoke"
    hub.mkdir()
    spoke.mkdir()

    # Hub has safe_pytest.py under scripts/
    hub_scripts = hub / "scripts"
    hub_scripts.mkdir()
    (hub_scripts / "safe_pytest.py").write_text("# hub safe_pytest", encoding="utf-8")

    # Spoke already has legacy top-level scripts/safe_pytest.py
    spoke_scripts = spoke / "scripts"
    spoke_scripts.mkdir()
    legacy_file = spoke_scripts / "safe_pytest.py"
    legacy_file.write_text("# legacy spoke safe_pytest", encoding="utf-8")

    copier = TestGuardrailCopier(spoke_root=spoke, hub_root=hub, project_type="Phần mềm")
    catalog_data = {
        "guardrails": [
            {
                "name": "safe_pytest.py",
                "src": "scripts/safe_pytest.py",
                "dest": "scripts/_guardrails/safe_pytest.py",
                "applies_to": ["python"],
            }
        ]
    }

    copier.copy_if_needed(catalog=catalog_data, dry_run=False)

    # 1. New location exists
    assert (spoke / "scripts" / "_guardrails" / "safe_pytest.py").is_file()
    # 2. Legacy top-level file was removed
    assert not legacy_file.exists()
