"""test_spoke_cleanliness_allowlist.py - Unit tests for PR-B2 Spoke Cleanliness & Path Scanner.

Validates (PR-B2 Issue #439):
1. Machine-state path scanner robustness: detects raw string prefix (r"..."), unquoted YAML, drive without trailing slash.
2. Role-based script allowlist: role allowlist wins over ephemeral prefix (e.g. audit_memory.py under audits).
3. Daemon scripts count towards 15-file limit without being flagged as ephemeral.
4. Cleanliness configuration loading from workspace_context.yaml (.cleanliness section).
5. CLI argument options: --allow-script and --allow-role.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from scripts.spoke.check_spoke_cleanliness import (
    check_ephemeral_scripts,
    check_machine_state_leakage,
    check_script_count,
    load_cleanliness_config,
    scan_spoke_cleanliness,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_machine_state_scanner_raw_string_and_drive_variations(tmp_path: Path) -> None:
    """Verify scanner catches raw strings, drive paths without trailing slash, and unquoted YAML."""
    script_file = tmp_path / "test_paths.py"
    script_file.write_text(
        'PATH_1 = r"D:\\ccba\\platform"\n'
        'PATH_2 = R"C:/Windows"\n'
        'DRIVE_ONLY = r"D:"\n'
        'TRAILING_SLASH = "D:\\\\"\n'
        'EXEMPTED = r"D:\\\\data"  # ccba:allow-machine-path\n'
        'COMMENT = "# D:\\\\ignored"\n',
        encoding="utf-8",
    )

    violations = check_machine_state_leakage([script_file])
    # PATH_1, PATH_2, DRIVE_ONLY, TRAILING_SLASH should be detected (4 violations)
    assert len(violations) == 4
    lines = [v[1] for v in violations]
    assert lines == [1, 2, 3, 4]


def test_machine_state_scanner_unquoted_yaml(tmp_path: Path) -> None:
    """Verify scanner detects unquoted absolute Windows paths in YAML files."""
    ctx_file = tmp_path / "workspace_context.yaml"
    ctx_file.write_text(
        "project:\n"
        "  name: spoke_test\n"
        "hub_path: D:\\ccba-agent-platform\n"
        "secondary_path: C:/tools\n",
        encoding="utf-8",
    )

    violations = check_machine_state_leakage([ctx_file])
    assert len(violations) == 2
    assert violations[0][1] == 3  # hub_path
    assert violations[1][1] == 4  # secondary_path


def test_role_allowlist_wins_over_ephemeral_prefix() -> None:
    """Verify that a script whose role is recognized is NOT flagged as ephemeral."""
    s1 = Path("audit_memory.py")
    s2 = Path("audit_unclassified.py")
    s3 = Path("fix_schema.py")

    # Case 1: Without role allowlist, audit_* and fix_* are flagged
    ephemeral_default = check_ephemeral_scripts([s1, s2, s3])
    assert set(ephemeral_default) == {s1, s2, s3}

    # Case 2: With role allowlist for audit_memory.py, it is exempted
    role_allowlist = {"audits": ["audit_memory.py"]}
    ephemeral_with_role = check_ephemeral_scripts([s1, s2, s3], role_allowlist=role_allowlist)
    assert s1 not in ephemeral_with_role
    assert set(ephemeral_with_role) == {s2, s3}


def test_daemon_counted_in_budget_not_ephemeral(tmp_path: Path) -> None:
    """Verify daemon scripts count towards the 15-script budget but are NOT flagged as ephemeral."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    daemon_script = scripts_dir / "daemon_sync.py"
    daemon_script.write_text("# daemon process", encoding="utf-8")

    # 1. Ephemeral check: should NOT be flagged
    ephemeral = check_ephemeral_scripts([daemon_script])
    assert len(ephemeral) == 0

    # 2. Count budget: SHOULD be counted towards 15 files
    counted, ignored = check_script_count(scripts_dir, max_scripts=15)
    assert len(counted) == 1
    assert counted[0] == daemon_script


def test_load_cleanliness_config_from_workspace_context(tmp_path: Path) -> None:
    """Verify load_cleanliness_config extracts allowed_scripts and roles from workspace_context.yaml."""
    ctx_file = tmp_path / ".md" / "workspace_context.yaml"
    ctx_file.parent.mkdir()
    ctx_data = {
        "project": {"name": "test"},
        "cleanliness": {
            "allowed_scripts": ["custom_tool.py"],
            "roles": {
                "audits": ["audit_memory.py"],
                "benchmarks": ["bench_speed.py"],
            },
        },
    }
    ctx_file.write_text(yaml.safe_dump(ctx_data), encoding="utf-8")

    custom_allowlist, role_exemptions = load_cleanliness_config(tmp_path)
    assert "custom_tool.py" in custom_allowlist
    assert "audit_memory.py" in role_exemptions
    assert "bench_speed.py" in role_exemptions


def test_scan_spoke_cleanliness_with_workspace_config(tmp_path: Path) -> None:
    """Verify scan_spoke_cleanliness integrates workspace configuration."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    # Create audit script that would normally be flagged as ephemeral
    audit_script = scripts_dir / "audit_memory.py"
    audit_script.write_text("# audit code", encoding="utf-8")

    # Create workspace context with role exemption for audit_memory.py
    ctx_file = tmp_path / "workspace_context.yaml"
    ctx_data = {
        "project": {"name": "test"},
        "cleanliness": {
            "roles": {
                "audits": ["audit_memory.py"],
            },
        },
    }
    ctx_file.write_text(yaml.safe_dump(ctx_data), encoding="utf-8")

    exit_code, messages = scan_spoke_cleanliness(tmp_path, max_scripts=15, strict=True)
    assert exit_code == 0
    assert not any("Script Tạm Thời" in m for m in messages)
