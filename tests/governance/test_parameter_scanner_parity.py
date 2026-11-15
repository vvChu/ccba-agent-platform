"""Parity, Tier-0 Spoke isolation, and performance SLA tests for parameter cleanliness scanners."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from scripts.governance.check_hardcoded_parameters import check_file_content, scan_directory
from scripts.spoke.check_spoke_cleanliness import (
    check_machine_state_leakage,
    check_raw_ip_leakage,
    check_raw_model_leakage,
)

from ccba_harness.peer_gate import check_secret_ip_cleanliness

REPO_ROOT = Path(__file__).resolve().parents[2]
_RAW_MODEL = "gpt" + "-4o"
_RAW_IP = ".".join(("100", "64", "1", "1"))
_WIN_PATH = "C:" + "\\Program Files\\App\\tool.exe"


def _write_sample(tmp_path: Path, body: str) -> Path:
    """Create a non-test Python sample file outside any 'tests' directory segment."""
    target = tmp_path / "pkg_src" / "sample.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def test_statutory_clause_and_approved_aliases_exempt_across_scanners(tmp_path: Path) -> None:
    """Statutory clause citations and qwen-local aliases produce zero false positives."""
    src = (
        'RULE = "Quy định tại 3.2.1.1 về khoảng cách"\n'
        'PRIMARY = "qwen-local"\n'
        'FALLBACK = "qwen-local-primary"\n'
    )
    target = _write_sample(tmp_path, src)

    assert check_file_content(target, src) == []
    assert check_raw_ip_leakage([target]) == []
    assert check_raw_model_leakage([target]) == []
    assert check_machine_state_leakage([target]) == []

    gate = check_secret_ip_cleanliness([target])
    assert gate.passed is True


def test_tailscale_ip_windows_spaces_and_raw_model_parity(tmp_path: Path) -> None:
    """All unified scanners flag Tailscale IPv4, Windows paths with spaces, and raw models."""
    src = f'MODEL = "{_RAW_MODEL}"\nHOST = "http://{_RAW_IP}:8090"\nBIN_PATH = r"{_WIN_PATH}"\n'
    target = _write_sample(tmp_path, src)

    gov_rules = {v.rule_name for v in check_file_content(target, src)}
    assert gov_rules == {
        "RawModelStringViolation",
        "HardcodedNetworkIPViolation",
        "HardcodedMachinePathViolation",
    }

    assert len(check_raw_model_leakage([target])) == 1
    assert len(check_raw_ip_leakage([target])) == 1
    assert len(check_machine_state_leakage([target])) == 1

    gate = check_secret_ip_cleanliness([target])
    assert gate.passed is False
    assert "raw Tailscale IP detected" in gate.stdout_tail


def test_spoke_tier0_isolation_without_harness_or_yaml(tmp_path: Path) -> None:
    """Spoke cleanliness runs purely on stdlib with sibling _guardrails/_parameter_cleanliness.py."""
    scripts_dir = tmp_path / "scripts"
    guardrails_dir = scripts_dir / "_guardrails"
    guardrails_dir.mkdir(parents=True)

    shutil.copy2(
        REPO_ROOT / "scripts" / "spoke" / "check_spoke_cleanliness.py",
        scripts_dir / "check_spoke_cleanliness.py",
    )
    shutil.copy2(
        REPO_ROOT
        / "packages"
        / "ccba-harness"
        / "src"
        / "ccba_harness"
        / "_parameter_cleanliness.py",
        guardrails_dir / "_parameter_cleanliness.py",
    )

    seeded = tmp_path / "src" / "worker.py"
    seeded.parent.mkdir(parents=True)
    seeded.write_text(
        f'M = "{_RAW_MODEL}"\nIP = "{_RAW_IP}"\nWIN = r"{_WIN_PATH}"\n',
        encoding="utf-8",
    )

    runner = "\n".join(
        [
            "import importlib.util, json, sys",
            "from pathlib import Path",
            "sys.modules['ccba_harness'] = None",
            "sys.modules['yaml'] = None",
            f"script = Path({str(scripts_dir / 'check_spoke_cleanliness.py')!r})",
            "spec = importlib.util.spec_from_file_location('tier0_spoke_checker', script)",
            "mod = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(mod)",
            f"code, msgs = mod.scan_spoke_cleanliness(Path({str(tmp_path)!r}))",
            "print(json.dumps({'code': code, 'msgs': msgs}))",
        ]
    )
    proc = subprocess.run(
        [sys.executable, "-c", runner],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    payload = json.loads(proc.stdout)
    combined = "\n".join(payload["msgs"])
    assert payload["code"] == 1
    assert "Raw Model Leakage" in combined
    assert "Raw IP Leakage" in combined
    assert "Machine-State Leakage" in combined


def test_multiline_triple_quoted_assignment_vs_docstring_parity(tmp_path: Path) -> None:
    """Assigned triple-quoted strings are scanned while module docstrings stay exempt."""
    doc_only = _write_sample(tmp_path / "doc", f'"""Endpoint http://{_RAW_IP}:8090."""\nX = 1\n')
    assert check_file_content(doc_only, doc_only.read_text(encoding="utf-8")) == []
    assert check_raw_ip_leakage([doc_only]) == []
    assert check_secret_ip_cleanliness([doc_only]).passed is True

    assigned = _write_sample(tmp_path / "assign", f'QUERY = """\nhttp://{_RAW_IP}:8090\n"""\n')
    assert len(check_file_content(assigned, assigned.read_text(encoding="utf-8"))) == 1
    assert len(check_raw_ip_leakage([assigned])) == 1
    assert check_secret_ip_cleanliness([assigned]).passed is False


def test_repo_scan_directory_clean_and_fast() -> None:
    """Default repository cleanliness scan completes in under 1.0s with zero violations."""
    timings: list[float] = []
    for _ in range(2):
        t0 = time.perf_counter()
        violations = scan_directory(REPO_ROOT)
        timings.append(time.perf_counter() - t0)
        assert violations == []
    best_elapsed = min(timings)
    assert best_elapsed < 1.0, f"scan_directory best run took {best_elapsed:.3f}s (SLA < 1.0s)"
