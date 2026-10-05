"""tests/test_pstack_disciplines.py - Unit tests for Upstream Pstack Disciplines (ADR-0009 / Issue #461)."""

import tempfile
from pathlib import Path

from ccba_harness.architecture import (
    explain_architecture_why,
)
from ccba_harness.blast_radius import (
    analyze_blast_radius,
    extract_ast_references,
)
from ccba_harness.cli import (
    run_blast_radius_cli,
    run_explain_why_cli,
)
from ccba_harness.peer_gate import (
    GateCheck,
    GateResult,
    check_ast_function_length,
    check_hub_import_depth,
    check_redundant_comments,
    check_secret_ip_cleanliness,
    run_full_gate,
    run_implementation_gate,
    write_verdict_file,
)


def test_ast_function_length_passes_and_flags():
    """Verify AST function length check properly identifies long functions."""
    short_code = "def short_func():\n    return 42\n"
    long_code = (
        "def long_func():\n"
        + "\n".join([f"    x_{i} = {i}" for i in range(55)])
        + "\n    return x_0\n"
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf1:
        tf1.write(short_code)
        short_file = Path(tf1.name)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf2:
        tf2.write(long_code)
        long_file = Path(tf2.name)

    try:
        check_pass = check_ast_function_length([short_file], max_lines=50)
        assert check_pass.passed is True
        assert check_pass.exit_code == 0

        check_fail = check_ast_function_length([long_file], max_lines=50)
        assert check_fail.passed is False
        assert check_fail.exit_code == 1
        assert "long_func()" in check_fail.stdout_tail
    finally:
        short_file.unlink(missing_ok=True)
        long_file.unlink(missing_ok=True)


def test_hub_import_depth_enforcement():
    """Verify deep imports into Hub packages are flagged."""
    clean_code = "from ccba_ai import client\n"
    deep_code = "from ccba_legal.crawler.chrome_cdp import internal_helper\n"

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf1:
        tf1.write(clean_code)
        clean_file = Path(tf1.name)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf2:
        tf2.write(deep_code)
        deep_file = Path(tf2.name)

    try:
        assert check_hub_import_depth([clean_file]).passed is True
        fail_res = check_hub_import_depth([deep_file])
        assert fail_res.passed is False
        assert "forbidden deep import" in fail_res.stdout_tail
    finally:
        clean_file.unlink(missing_ok=True)
        deep_file.unlink(missing_ok=True)


def test_secret_ip_cleanliness():
    """Verify Tailscale IPs without allowlist comment are blocked."""
    clean_code = (
        "ip = os.getenv('NODE_IP', '127.0.0.1')\nallow_ip = '100.83.192.30' # ccba:allow-raw-ip\n"
    )
    leak_code = "ip = '100.83.192.30'\n"

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf1:
        tf1.write(clean_code)
        clean_file = Path(tf1.name)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf2:
        tf2.write(leak_code)
        leak_file = Path(tf2.name)

    try:
        assert check_secret_ip_cleanliness([clean_file]).passed is True
        fail_res = check_secret_ip_cleanliness([leak_file])
        assert fail_res.passed is False
        assert "raw Tailscale IP detected" in fail_res.stdout_tail
    finally:
        clean_file.unlink(missing_ok=True)
        leak_file.unlink(missing_ok=True)


def test_write_verdict_file():
    """Verify gate verdict file writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        peer_dir = Path(tmpdir)
        check = GateCheck(
            name="test_check", passed=True, exit_code=0, stdout_tail="ok", duration_ms=10
        )
        res = GateResult(
            gate="PASS", timestamp="2026-10-04T12:00:00", branch="main", checks=[check]
        )

        v_file = write_verdict_file(res, peer_dir)
        assert v_file.exists()
        content = v_file.read_text(encoding="utf-8")
        assert "GATE_PASS" in content
        assert "Automated Gate Execution Report" in content


def test_blast_radius_analyzer():
    """Verify AST reference extraction and risk scoring in blast radius analyzer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        pkg_dir = root_dir / "services" / "retrieval"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        py_file = pkg_dir / "service.py"
        py_file.write_text(
            "import ccba_ai\nfrom ccba_harness import HarnessGuard\nx = HarnessGuard()\n",
            encoding="utf-8",
        )

        hits = extract_ast_references(py_file, {"ccba_ai", "HarnessGuard"})
        assert len(hits) >= 2

        report = analyze_blast_radius({"ccba_ai"}, root_dir)
        assert report.affected_file_count == 1
        assert report.risk_level == "CRITICAL"  # retrieval is core keyword
        assert "service.py" in report.affected_files[0]


def test_architecture_why_lookup():
    """Verify ADR parsing and architecture why explanation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        adr_dir = root_dir / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)

        sample_adr = adr_dir / "0001-sample-decision.md"
        sample_adr.write_text(
            "# 1. Sample Decision\n\n**Trạng thái**: Accepted\n\n## Quyết định\nSử dụng Redis DB 0-5 để tách biệt ngữ cảnh cache.\n",
            encoding="utf-8",
        )

        explanation = explain_architecture_why(
            "Redis DB 0-5 cache", root_dir=root_dir, adr_dirs=[adr_dir]
        )
        assert len(explanation.adr_matches) >= 1
        assert explanation.adr_matches[0].adr_id == "0001"
        assert "Redis DB 0-5" in explanation.synthesis


def test_cli_dispatch_pstack():
    """Verify CLI commands run without crashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Test explain-why
        rc_why = run_explain_why_cli(["Redis", "--root", str(root), "--json"])
        assert rc_why == 0

        # Test blast-radius
        rc_blast = run_blast_radius_cli(["ccba_ai", "--root", str(root), "--json"])
        assert rc_blast == 0


def test_redundant_comments_passes_clean_code():
    """Verify clean code, allowlisted comments, and valid prose pass the gate."""
    clean_code = (
        "# ccba:allow-machine-path\n"
        "# noqa: E501\n"
        "# type: ignore[attr-defined]\n"
        "# pragma: no cover\n"
        "# Theo Điều 15 NĐ 175/2024: Quy định về điều kiện khởi công\n"
        "# ------------------------------------------------------------\n"
        "# Return cached model if available to minimize network latency\n"
        "# return early if cache hit\n"
        "def fetch_model():\n"
        "    return 'model_v1'\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(clean_code)
        clean_file = Path(tf.name)

    try:
        res = check_redundant_comments([clean_file])
        assert res.passed is True
        assert res.exit_code == 0
        assert "clean" in res.stdout_tail.lower()
    finally:
        clean_file.unlink(missing_ok=True)


def test_redundant_comments_flags_dead_code():
    """Verify commented-out dead code (def, class, import, return) is flagged."""
    dead_code_samples = [
        "# def old_calculate_sum(a, b): return a + b\n",
        "# class LegacyParser:\n#     pass\n",
        "# import legacy_service\n",
        "# from math import sin, cos\n",
        "# return False\n",
    ]
    for sample in dead_code_samples:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(sample)
            fpath = Path(tf.name)
        try:
            res = check_redundant_comments([fpath])
            assert res.passed is False, f"Failed to flag dead code in: {sample}"
            assert res.exit_code == 1
            assert "commented-out dead code" in res.stdout_tail
        finally:
            fpath.unlink(missing_ok=True)


def test_redundant_comments_flags_duplicate_name_restatement():
    """Verify redundant comments merely restating function/class name are flagged."""
    dup_samples = [
        "# get project by id\ndef get_project_by_id():\n    pass\n",
        "# run full gate\n@some_decorator\ndef run_full_gate():\n    pass\n",
        "# Base Handler\nclass BaseHandler:\n    pass\n",
    ]
    for sample in dup_samples:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(sample)
            fpath = Path(tf.name)
        try:
            res = check_redundant_comments([fpath])
            assert res.passed is False, f"Failed to flag duplicate restatement in: {sample}"
            assert res.exit_code == 1
            assert "duplicate comment restating" in res.stdout_tail
        finally:
            fpath.unlink(missing_ok=True)


def test_run_implementation_gate_alias():
    """Verify run_implementation_gate is canonical alias of run_full_gate."""
    assert run_implementation_gate is run_full_gate
