"""Tests for PEP 562 lazy package exports in ccba_qc_core."""

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


def test_ccba_qc_core_all_and_lazy_exports_ast_parity() -> None:
    """Verify exact 2-way AST parity between __all__ (14) and _LAZY_EXPORTS."""
    init_path = Path(__file__).resolve().parents[1] / "src" / "ccba_qc_core" / "__init__.py"
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
    assert len(all_symbols) == 14
    assert len(set(all_symbols)) == 14

    lazy_keys = {
        k.value for k in lazy_node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    assert len(lazy_keys) == len(lazy_node.keys)
    assert set(all_symbols) == lazy_keys


def test_ccba_qc_core_jurisdiction_isolation_no_heavy_deps() -> None:
    """Verify importing ccba_qc_core.jurisdiction skips pipeline, openai, httpx, fitz, and pymupdf."""
    code = (
        "import json, sys\n"
        "import ccba_qc_core.jurisdiction as jur\n"
        "loaded = {\n"
        "  'openai': 'openai' in sys.modules,\n"
        "  'httpx': 'httpx' in sys.modules,\n"
        "  'fitz': 'fitz' in sys.modules,\n"
        "  'pymupdf': 'pymupdf' in sys.modules,\n"
        "  'pipeline': 'ccba_qc_core.pipeline' in sys.modules,\n"
        "  'has_router': hasattr(jur, 'PcccJurisdictionRouter'),\n"
        "}\n"
        "print(json.dumps(loaded))\n"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert json.loads(res.stdout.strip()) == {
        "openai": False,
        "httpx": False,
        "fitz": False,
        "pymupdf": False,
        "pipeline": False,
        "has_router": True,
    }


def test_ccba_qc_core_dir_and_unknown_attr() -> None:
    """Verify __dir__ exposes __all__ and unknown attribute raises AttributeError."""
    import ccba_qc_core

    assert "QCAuditPipeline" in dir(ccba_qc_core)
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent_qc_sym'"):
        _ = ccba_qc_core.nonexistent_qc_sym
