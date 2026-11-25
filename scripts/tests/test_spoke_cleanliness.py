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


def test_ast_docstring_vs_triple_quote_literals_and_sorted_scan(tmp_path: Path) -> None:
    """Verifies AST docstring parsing does not get tricked by triple-quote string literals in code, fallback docstring closing lines are skipped, and file/model scans sort deterministically (RULE-5.9)."""
    from scripts.spoke.check_spoke_cleanliness import (
        _collect_py_files_to_scan,
        check_machine_state_leakage,
        check_raw_ip_leakage,
        check_raw_model_leakage,
        check_script_count,
    )

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    ip_a = "100.83." + "192.30"
    win_path = "D:\\GitHubProjects\\ccba-agent-platform"

    tricky_py = scripts_dir / "z_tricky.py"
    tricky_py.write_text(
        '"""Module docstring."""\n'
        'DELIM = \'"""\'\n'
        f'LEAK_PATH = r"{win_path}"\n'
        f'LEAK_IP = "http://{ip_a}:8090"\n'
        "def nested():\n"
        '    return "gpt-4o"\n'  # ccba:allow-raw-model
        'TOP_MODEL = "gemini-3-flash"\n'  # ccba:allow-raw-model
        "EXEMPT_MULTILINE = (\n"
        '    "claude-"\n'  # ccba:allow-raw-model
        '    "haiku-4"  # ccba:allow-raw-model\n'
        ")\n",
        encoding="utf-8",
    )

    broken_py = scripts_dir / "a_broken.py"
    broken_py.write_text(
        "def broken(:\n"
        f'    """Single-line fallback docstring with {win_path}"""\n'
        '    """Multi-line fallback docstring\n'
        f'    closing with {win_path}"""\n'
        f'    LEAK_PATH = r"{win_path}"\n',
        encoding="utf-8",
    )

    path_violations = check_machine_state_leakage([tricky_py, broken_py])
    assert len(path_violations) == 2
    assert path_violations[0][0] == tricky_py and path_violations[0][1] == 3
    assert path_violations[1][0] == broken_py and path_violations[1][1] == 5

    ip_violations = check_raw_ip_leakage([tricky_py])
    assert len(ip_violations) == 1
    assert ip_violations[0][0] == tricky_py and ip_violations[0][1] == 4

    model_violations = check_raw_model_leakage([tricky_py])
    assert [v[1] for v in model_violations] == [6, 7]

    counted, _ = check_script_count(scripts_dir)
    assert counted == sorted(counted)

    collected = _collect_py_files_to_scan(tmp_path, scripts_dir)
    assert collected == sorted(collected)


def test_services_walk_prunes_volumes_and_checks_import_depth(tmp_path: Path, monkeypatch) -> None:
    """Verifies cleanliness and import-depth guardrails scan services/ safely while pruning restricted dirs."""
    import os
    import sys

    from scripts.spoke import check_hub_import_depth
    from scripts.spoke.check_spoke_cleanliness import _collect_py_files_to_scan

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    svc_dir = tmp_path / "services" / "rag-service"
    svc_tests = svc_dir / "tests"
    svc_volumes = svc_dir / "volumes" / "etcd" / "member"
    svc_node = svc_dir / "node_modules" / "pkg"
    for d in (svc_tests, svc_volumes, svc_node):
        d.mkdir(parents=True)

    app_py = svc_dir / "app.py"
    app_py.write_text("from ccba_ai.internal.submod import helper\n", encoding="utf-8")
    (svc_tests / "test_x.py").write_text("from ccba_ai import ai\n", encoding="utf-8")
    (svc_volumes / "state.py").write_text(
        "from ccba_ai.internal.submod import helper\n", encoding="utf-8"
    )
    (svc_node / "ignored.py").write_text(
        "from ccba_ai.internal.submod import helper\n", encoding="utf-8"
    )

    os.chmod(svc_volumes, 0o000)
    try:
        collected = _collect_py_files_to_scan(tmp_path, scripts_dir)
        assert collected == [app_py]

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "check_hub_import_depth.py",
                "--path",
                str(tmp_path),
                "--hub-path",
                str(Path(__file__).resolve().parents[2]),
            ],
        )
        assert check_hub_import_depth.main() == 1
    finally:
        os.chmod(svc_volumes, 0o755)


def test_session_debris_md_scripts_and_systemd_service_scanning(tmp_path: Path) -> None:
    """Verifies .agents session debris, .md/scripts/ scanning, and systemd unit leak detection."""
    from scripts.spoke.check_spoke_cleanliness import (
        _collect_py_files_to_scan,
        check_agents_session_debris,
        scan_spoke_cleanliness,
    )

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    agents_dir = tmp_path / ".agents"
    for canonical in ("rules", "skills", "proposals", "workflows"):
        (agents_dir / canonical).mkdir(parents=True)
    (agents_dir / "AGENTS.md").write_text("# canonical\n", encoding="utf-8")
    debris_dir = agents_dir / "auditor_99"
    debris_dir.mkdir()
    debris_req = agents_dir / "ORIGINAL_REQUEST.md"
    debris_req.write_text("ephemeral\n", encoding="utf-8")
    assert check_agents_session_debris(tmp_path) == [debris_req, debris_dir]
    rc_debris, msgs_debris = scan_spoke_cleanliness(tmp_path)
    assert rc_debris == 1
    assert any("Session Debris Isolation" in m for m in msgs_debris)
    debris_req.unlink()
    debris_dir.rmdir()
    assert check_agents_session_debris(tmp_path) == []

    md_helper = tmp_path / ".md" / "scripts" / "helper.py"
    md_helper.parent.mkdir(parents=True)
    md_helper.write_text("X = 1\n", encoding="utf-8")
    archived_py = tmp_path / ".md" / "scripts" / "archive" / "old.py"
    archived_py.parent.mkdir(parents=True)
    archived_py.write_text("Y = 2\n", encoding="utf-8")
    assert _collect_py_files_to_scan(tmp_path, scripts_dir) == [md_helper]

    systemd_unit = tmp_path / "tools" / "systemd" / "demo.service"
    systemd_unit.parent.mkdir(parents=True)
    raw_home = "/home/" + "user/project"
    raw_ip = ".".join(("100", "83", "192", "30"))
    systemd_unit.write_text(
        f"[Service]\nWorkingDirectory={raw_home}\nEnvironment=GATEWAY=http://{raw_ip}:8090\n",
        encoding="utf-8",
    )
    rc_dirty, msgs_dirty = scan_spoke_cleanliness(tmp_path)
    assert rc_dirty == 1
    assert any("Raw IP Leakage" in m for m in msgs_dirty)
    assert any("Machine-State Leakage" in m for m in msgs_dirty)

    systemd_unit.write_text("[Service]\nWorkingDirectory=@PROJECT_ROOT@\n", encoding="utf-8")
    rc_clean, _ = scan_spoke_cleanliness(tmp_path)
    assert rc_clean == 0


def test_peer_exchange_git_hygiene_spoke_vs_hub_and_strict(tmp_path: Path) -> None:
    """Warns on git-tracked .md/peer_exchange drafts on Spokes, silent on Hub and allowlist."""
    import subprocess

    from scripts.spoke.check_spoke_cleanliness import scan_spoke_cleanliness

    def _git(repo: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    # 1. Non-git tmp_path stays clean
    (tmp_path / "non_git" / ".md" / "peer_exchange").mkdir(parents=True)
    (tmp_path / "non_git" / ".md" / "peer_exchange" / "prompt_grok_x.md").write_text("hi")
    rc_nongit, msgs_nongit = scan_spoke_cleanliness(tmp_path / "non_git", strict=True)
    assert rc_nongit == 0
    assert not any("Peer Exchange Git Hygiene" in m for m in msgs_nongit)

    # 2. Spoke git repo with allowlisted files only -> clean even under strict=True
    spoke = tmp_path / "spoke_repo"
    (spoke / ".md" / "peer_exchange").mkdir(parents=True)
    _git(spoke, "init")
    _git(spoke, "config", "user.email", "test@ccba.local")
    _git(spoke, "config", "user.name", "Test")
    for fname in ("PEER_HANDSHAKE.md", "README.md", ".gitkeep"):
        (spoke / ".md" / "peer_exchange" / fname).write_text("ok\n", encoding="utf-8")
    _git(spoke, "add", ".md/peer_exchange/")
    _git(spoke, "commit", "-m", "init allowlist")

    rc_allow, msgs_allow = scan_spoke_cleanliness(spoke, strict=True)
    assert rc_allow == 0
    assert not any("Peer Exchange Git Hygiene" in m for m in msgs_allow)

    # 3. Spoke tracking a draft file -> warn (exit 0 default, exit 1 --strict)
    (spoke / ".md" / "peer_exchange" / "prompt_grok_secret.md").write_text("secret\n")
    _git(spoke, "add", ".md/peer_exchange/prompt_grok_secret.md")
    _git(spoke, "commit", "-m", "track draft")

    rc_warn, msgs_warn = scan_spoke_cleanliness(spoke, strict=False)
    assert rc_warn == 0
    assert any("Peer Exchange Git Hygiene" in m for m in msgs_warn)

    rc_strict, _ = scan_spoke_cleanliness(spoke, strict=True)
    assert rc_strict == 1

    # 4. Hub repo (origin contains ccba-agent-platform) stays silent
    _git(spoke, "remote", "add", "origin", "https://github.com/vvChu/ccba-agent-platform.git")
    rc_hub, msgs_hub = scan_spoke_cleanliness(spoke, strict=True)
    assert rc_hub == 0
    assert not any("Peer Exchange Git Hygiene" in m for m in msgs_hub)
