"""Unit tests for check_spoke_cleanliness.py (Issue #215 / ADR 0044)."""

from __future__ import annotations

from pathlib import Path

from scripts.spoke.check_spoke_cleanliness import (
    check_ephemeral_scripts,
    check_hub_duplications,
    check_script_count,
    scan_spoke_cleanliness,
)


def test_check_script_count_allowlist(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    # Core scripts
    for i in range(5):
        (scripts_dir / f"core_task_{i}.py").write_text("# core", encoding="utf-8")

    # Allowlist scripts
    (scripts_dir / "__init__.py").write_text("", encoding="utf-8")
    (scripts_dir / "conftest.py").write_text("", encoding="utf-8")
    (scripts_dir / "safe_pytest.py").write_text("", encoding="utf-8")
    (scripts_dir / "check_hub_import_depth.py").write_text("", encoding="utf-8")
    (scripts_dir / "check_spoke_cleanliness.py").write_text("", encoding="utf-8")

    counted, ignored = check_script_count(scripts_dir, max_scripts=15)
    assert len(counted) == 5
    assert len(ignored) == 5


def test_check_script_count_exceeded(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    # Create 16 scripts
    for i in range(16):
        (scripts_dir / f"task_{i}.py").write_text("# task", encoding="utf-8")

    counted, ignored = check_script_count(scripts_dir, max_scripts=15)
    assert len(counted) == 16

    exit_code, messages = scan_spoke_cleanliness(tmp_path, max_scripts=15)
    assert exit_code == 1
    assert any("Script Budget Vượt Ngưỡng" in m for m in messages)


def test_check_ephemeral_scripts(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    s1 = scripts_dir / "fix_missing_dates.py"
    s2 = scripts_dir / "audit_vbhn_duplicates.py"
    s3 = scripts_dir / "patch_registry.py"
    s4 = scripts_dir / "main_pipeline.py"
    for s in [s1, s2, s3, s4]:
        s.write_text("# code", encoding="utf-8")

    ephemeral = check_ephemeral_scripts([s1, s2, s3, s4])
    assert set(ephemeral) == {s1, s2, s3}


def test_check_hub_duplications_sys_path(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    bad_script = scripts_dir / "bad_loader.py"
    bad_script.write_text("import sys\nsys.path.insert(0, str(HUB_SRC))\n", encoding="utf-8")

    good_script = scripts_dir / "good_loader.py"
    good_script.write_text("from ccba_ai import ai\n", encoding="utf-8")

    violations = check_hub_duplications([bad_script, good_script])
    assert len(violations) == 1
    assert violations[0][0] == bad_script
    assert violations[0][1] == 2


def test_scan_spoke_cleanliness_clean_project(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    for i in range(3):
        (scripts_dir / f"pipeline_{i}.py").write_text("from ccba_ai import ai\n", encoding="utf-8")

    exit_code, messages = scan_spoke_cleanliness(tmp_path, max_scripts=15, strict=True)
    assert exit_code == 0
    assert any("3/15 tệp hợp lệ" in m for m in messages)


def test_check_machine_state_leakage(tmp_path: Path) -> None:
    """Test detection of hardcoded Windows drive letters and user home directories."""
    from scripts.spoke.check_spoke_cleanliness import check_machine_state_leakage

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    bad_script = scripts_dir / "bad_path.py"
    bad_script.write_text(
        'HUB_DIR = "D:\\\\GitHubProjects\\\\ccba-agent-platform"\n'
        '# This comment with D:\\\\is\\\\ignored\n'
        'ALLOWED = "C:\\\\dummy"  # ccba:allow-machine-path\n',
        encoding="utf-8",
    )

    bad_ctx = tmp_path / "workspace_context.yaml"
    bad_ctx.write_text(
        'project:\n  name: test\nhub_path: "D:\\\\GitHubProjects\\\\ccba-agent-platform"\n',
        encoding="utf-8",
    )

    clean_script = scripts_dir / "clean.py"
    clean_script.write_text(
        'HUB_DIR = os.environ.get("CCBA_HUB_PATH", "../ccba-agent-platform")\n',
        encoding="utf-8",
    )

    violations = check_machine_state_leakage([bad_script, bad_ctx, clean_script])
    assert len(violations) == 2
    assert violations[0][0] == bad_script
    assert violations[0][1] == 1  # line 1
    assert violations[1][0] == bad_ctx
    assert violations[1][1] == 3  # line 3
    assert "Hardcoded Windows drive path" in violations[0][2]

    # Full scan should fail with machine-state leakage
    exit_code, messages = scan_spoke_cleanliness(tmp_path, max_scripts=15)
    assert exit_code == 1
    assert any("Vi phạm Machine-State Leakage" in m for m in messages)
