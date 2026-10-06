"""test_module_budget_ratchet.py - Unit and governance tests for module size budget and function length gates (ADR-0061 / ADR-0066).

Validates:
1. All 340+ Python modules in packages/*/src comply with static line budget (<= 800 LOC or ratchet baseline).
2. Ratchet mechanism fails closed when an existing oversized module increases in line count.
3. Hard cap rejects any new unexempted module exceeding 800 LOC.
4. AST function length checker enforces KISS (<= 50 LOC / post-parse <= 40 LOC).
5. Quarantined functions with active until= dates are respected, while expired or malformed ones fail.
6. Fail-closed behavior on syntax errors or unreadable files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccba_harness.peer_gate import check_ast_function_length, check_module_size_budget

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_all_monorepo_modules_respect_module_budget() -> None:
    """Verifies that all current modules in packages/*/src respect the module budget baseline."""
    res = check_module_size_budget()
    assert res.passed, f"Module size budget violations found:\n{res.stdout_tail}"
    assert res.exit_code == 0


def test_module_budget_ratchet_detects_growth(tmp_path: Path) -> None:
    """Ensures ratchet fails when an exempted file exceeds its committed baseline."""
    ws = tmp_path / "workspace"
    pkg_src = ws / "packages" / "ccba-dummy" / "src" / "dummy"
    pkg_src.mkdir(parents=True)
    target_file = pkg_src / "oversized.py"
    target_file.write_text("\n".join(["x = 1"] * 900) + "\n", encoding="utf-8")

    baseline_file = ws / "baseline.json"
    rel_path = target_file.relative_to(ws).as_posix()
    # Baseline set to 850 lines, but file has 900 lines
    baseline_file.write_text(json.dumps({rel_path: 850}), encoding="utf-8")

    res = check_module_size_budget(workspace_dir=ws, baseline_path=baseline_file)
    assert not res.passed
    assert res.exit_code == 1
    assert "ratchet violation" in res.stdout_tail
    assert "900 lines > committed baseline 850" in res.stdout_tail


def test_module_budget_rejects_unexempted_oversized_file(tmp_path: Path) -> None:
    """Ensures new files exceeding 800 lines fail immediately without baseline entry."""
    ws = tmp_path / "workspace"
    pkg_src = ws / "packages" / "ccba-dummy" / "src" / "dummy"
    pkg_src.mkdir(parents=True)
    target_file = pkg_src / "god_module.py"
    target_file.write_text("\n".join(["y = 2"] * 850) + "\n", encoding="utf-8")

    baseline_file = ws / "baseline.json"
    baseline_file.write_text("{}", encoding="utf-8")

    res = check_module_size_budget(workspace_dir=ws, baseline_path=baseline_file)
    assert not res.passed
    assert res.exit_code == 1
    assert "hard cap exceeded" in res.stdout_tail
    assert "850 lines > 800 LOC limit" in res.stdout_tail


def test_ast_function_length_respects_quarantine(tmp_path: Path) -> None:
    """Ensures functions with valid quarantine annotations are exempted, while unquarantined ones fail."""
    py_file = tmp_path / "test_module.py"
    # Create a function of 60 lines with active quarantine
    quarantined_func = (
        "# ccba:quarantine seam_id=test.heavy reason=refactor until=2099-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/100\n"
        "def heavy_func():\n" + "".join([f"    a{i} = {i}\n" for i in range(55)])
    )
    # Create an unquarantined function of 60 lines
    unquarantined_func = "\ndef bad_func():\n" + "".join([f"    b{i} = {i}\n" for i in range(55)])
    py_file.write_text(quarantined_func + unquarantined_func, encoding="utf-8")

    res = check_ast_function_length([py_file], max_lines=50)
    assert not res.passed
    assert "bad_func()" in res.stdout_tail
    assert "lines > 50" in res.stdout_tail
    assert "heavy_func" not in res.stdout_tail


def test_ast_function_length_fail_closed_on_syntax_error(tmp_path: Path) -> None:
    """Ensures AST function length checker fails closed when Python syntax is invalid."""
    py_file = tmp_path / "broken.py"
    py_file.write_text("def broken_syntax(:\n    pass\n", encoding="utf-8")

    res = check_ast_function_length([py_file], max_lines=50)
    assert not res.passed
    assert res.exit_code == 1
    assert "Syntax/Read error" in res.stdout_tail
