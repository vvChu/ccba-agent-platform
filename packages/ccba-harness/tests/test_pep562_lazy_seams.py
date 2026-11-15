"""Tests for PEP 562 lazy package exports in ccba_harness."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _extract_assign(tree: ast.Module, name: str) -> ast.expr | None:
    """Return AST value for an unannotated top-level assignment."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
    return None


def test_ccba_harness_all_and_lazy_exports_ast_parity() -> None:
    """Verify exact 2-way AST parity between __all__ (240) and _LAZY_EXPORTS."""
    init_path = Path(__file__).resolve().parents[1] / "src" / "ccba_harness" / "__init__.py"
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))

    all_node = _extract_assign(tree, "__all__")
    lazy_node = _extract_assign(tree, "_LAZY_EXPORTS")
    assert isinstance(all_node, ast.List)
    assert isinstance(lazy_node, ast.Dict)

    all_symbols = [
        elt.value
        for elt in all_node.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    ]
    assert len(all_symbols) == 240
    assert len(set(all_symbols)) == 240

    lazy_keys = {
        k.value for k in lazy_node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    lazy_vals = [
        v.value
        for v in lazy_node.values
        if isinstance(v, ast.Constant) and isinstance(v.value, str)
    ]
    assert len(lazy_keys) == len(lazy_node.keys)
    assert all(val.startswith("ccba_harness.") for val in lazy_vals)
    assert set(all_symbols) == lazy_keys


def test_ccba_harness_keeps_eager_subprocess_and_isolates_gpi() -> None:
    """Verify eager subprocess attr and clean ccba_harness.gpi import isolation."""
    code = (
        "import json, sys\n"
        "import ccba_harness\n"
        "has_sub = hasattr(ccba_harness, 'subprocess')\n"
        "import ccba_harness.gpi as gpi\n"
        "loaded = {\n"
        "  'has_subprocess': has_sub,\n"
        "  'skill_validator': 'ccba_harness.skill_validator' in sys.modules,\n"
        "  'verifier': 'ccba_harness.verifier' in sys.modules,\n"
        "  'peer_gate': 'ccba_harness.peer_gate' in sys.modules,\n"
        "  'dashboard': 'ccba_harness.dashboard' in sys.modules,\n"
        "  'has_calc_gpi': hasattr(gpi, 'calculate_gpi'),\n"
        "}\n"
        "print(json.dumps(loaded))\n"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert json.loads(res.stdout.strip()) == {
        "has_subprocess": True,
        "skill_validator": False,
        "verifier": False,
        "peer_gate": False,
        "dashboard": False,
        "has_calc_gpi": True,
    }


def test_ccba_harness_dir_and_unknown_attr() -> None:
    """Verify __dir__ exposes __all__ and unknown attribute raises AttributeError."""
    import ccba_harness

    assert "HarnessGuard" in dir(ccba_harness)
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent_harness_sym'"):
        _ = ccba_harness.nonexistent_harness_sym
