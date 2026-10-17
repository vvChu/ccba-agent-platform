"""Unit tests for check_spoke_cleanliness.py (Issue #215 / ADR 0044)."""

from __future__ import annotations

from pathlib import Path

from scripts.spoke.check_spoke_cleanliness import (
    check_ephemeral_scripts,
    check_hub_duplications,
    check_raw_ip_leakage,
    check_raw_model_leakage,
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
        "# This comment with D:\\\\is\\\\ignored\n"
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


def test_detect_raw_model_strings(tmp_path: Path) -> None:
    """Verifies that raw provider model strings in code trigger violations."""
    code_file = tmp_path / "bad_models.py"
    code_file.write_text(
        "def run_llm():\n"
        '    m1 = "gemini-3-flash"\n'  # ccba:allow-raw-model
        '    m2 = "claude-haiku-4"\n'  # ccba:allow-raw-model
        '    m3 = "openai/gemma-4-26b-a4b-it"\n'  # ccba:allow-raw-model
        '    m4 = "gpt-4o"\n'  # ccba:allow-raw-model
        '    m5 = "deepseek-v3"\n'  # ccba:allow-raw-model
        "    return [m1, m2, m3, m4, m5]\n",
        encoding="utf-8",
    )

    violations = check_raw_model_leakage([code_file])
    assert len(violations) == 5
    violation_texts = [v[2] for v in violations]
    assert any("gemini-3-flash" in v for v in violation_texts)  # ccba:allow-raw-model
    assert any("claude-haiku-4" in v for v in violation_texts)  # ccba:allow-raw-model
    assert any("openai/gemma-4-26b-a4b-it" in v for v in violation_texts)  # ccba:allow-raw-model
    assert any("gpt-4o" in v for v in violation_texts)  # ccba:allow-raw-model
    assert any("deepseek-v3" in v for v in violation_texts)  # ccba:allow-raw-model


def test_allowed_capability_aliases(tmp_path: Path) -> None:
    """Verifies that approved capability aliases do NOT trigger violations."""
    code_file = tmp_path / "good_aliases.py"
    code_file.write_text(
        "def run_llm():\n"
        '    a1 = "ocr-primary"\n'
        '    a2 = "ocr-fallback"\n'
        '    a3 = "fast-realtime"\n'
        '    a4 = "text-auto"\n'
        '    a5 = "text-gemma"\n'
        '    a6 = "rag-core"\n'
        "    return [a1, a2, a3, a4, a5, a6]\n",
        encoding="utf-8",
    )

    violations = check_raw_model_leakage([code_file])
    assert len(violations) == 0


def test_raw_model_exemptions(tmp_path: Path) -> None:
    """Verifies inline, file-level, and docstring exemptions for raw model strings."""
    inline_file = tmp_path / "inline_exempt.py"
    inline_file.write_text(
        'def legacy():\n    return "gemini-3-flash"  # ccba:allow-raw-model\n',
        encoding="utf-8",
    )
    assert len(check_raw_model_leakage([inline_file])) == 0

    file_exempt = tmp_path / "file_exempt.py"
    file_exempt.write_text(
        "# ccba:allow-raw-model-file\n"
        'def benchmark():\n    return ["gemini-3.5-flash-lite", "claude-haiku-4"]\n',  # ccba:allow-raw-model
        encoding="utf-8",
    )
    assert len(check_raw_model_leakage([file_exempt])) == 0

    docstring_file = tmp_path / "docstring_only.py"
    docstring_file.write_text(
        '"""Module mentioning gemini-3-flash and claude-haiku-4."""\n'  # ccba:allow-raw-model
        'def foo():\n    """Inner docstring mentioning gpt-4o."""\n    pass\n',  # ccba:allow-raw-model
        encoding="utf-8",
    )
    assert len(check_raw_model_leakage([docstring_file])) == 0


def test_detect_raw_ip_leakage(tmp_path: Path) -> None:
    """Verifies detection of raw non-local IPv4 addresses in code, scripts, and configs."""
    ip_a = "100.83." + "192.30"
    ip_b = "100.79." + "241.120"
    ip_file = tmp_path / "config_with_ips.py"
    ip_file.write_text(
        f'PROXY_URL = "http://{ip_a}:8090/v1"\nDIRECT_IP = "{ip_b}"\n',
        encoding="utf-8",
    )

    violations = check_raw_ip_leakage([ip_file])
    assert len(violations) == 2
    assert any(ip_a in v[2] for v in violations)
    assert any(ip_b in v[2] for v in violations)


def test_allowed_ips_and_exemptions(tmp_path: Path) -> None:
    """Verifies that loopback, 0.0.0.0, public DNS, comments, docstrings, and annotations pass."""
    ip_a = "100.83." + "192.30"
    allowed_file = tmp_path / "safe_config.py"
    allowed_file.write_text(
        f'"""Single-line docstring with IP {ip_a} should be ignored."""\n'
        f"# Commented IP should be ignored: {ip_a}\n"
        'LOCAL_BASE = "http://127.0.0.1:8090/v1"\n'
        'BIND_ALL = "0.0.0.0"\n'
        'DNS_PRIMARY = "8.8.8.8"\n'
        'DNS_SECONDARY = "1.1.1.1"\n'
        f'ANALYTICS_TARGET = "{ip_a}"  # ccba:allow-raw-ip\n',
        encoding="utf-8",
    )

    violations = check_raw_ip_leakage([allowed_file])
    assert len(violations) == 0


def test_scan_spoke_cleanliness_catches_raw_model_and_ip(tmp_path: Path) -> None:
    """Verifies scan_spoke_cleanliness wires raw model and IP checks into full spoke scan."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    ip_a = "100.83." + "192.30"
    (scripts_dir / "worker.py").write_text(
        f'MODEL = "gemini-3-flash"\nHOST = "{ip_a}"\n',  # ccba:allow-raw-model
        encoding="utf-8",
    )

    exit_code, messages = scan_spoke_cleanliness(tmp_path, max_scripts=15)
    assert exit_code == 1
    assert any("Vi phạm Raw Model Leakage" in m for m in messages)
    assert any("Vi phạm Raw IP Leakage" in m for m in messages)
