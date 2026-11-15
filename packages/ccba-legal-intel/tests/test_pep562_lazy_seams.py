"""Tests for PEP 562 lazy package exports in ccba_legal."""

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


def test_ccba_legal_all_and_lazy_exports_ast_parity() -> None:
    """Verify exact 2-way AST parity between __all__ (148) and _LAZY_EXPORTS."""
    init_path = Path(__file__).resolve().parents[1] / "src" / "ccba_legal" / "__init__.py"
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
    assert len(all_symbols) == 148
    assert len(set(all_symbols)) == 148

    lazy_keys = {
        k.value for k in lazy_node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    lazy_vals = [
        v.value
        for v in lazy_node.values
        if isinstance(v, ast.Constant) and isinstance(v.value, str)
    ]
    assert len(lazy_keys) == len(lazy_node.keys)
    assert all(val.startswith("ccba_legal.") for val in lazy_vals)
    assert set(all_symbols) == lazy_keys


def test_ccba_legal_models_isolation_no_heavy_deps() -> None:
    """Verify importing ccba_legal.models does not pull openai, httpx, fitz, pymupdf, or docx."""
    code = (
        "import json, sys\n"
        "import ccba_legal.models as models\n"
        "loaded = {\n"
        "  'openai': 'openai' in sys.modules,\n"
        "  'httpx': 'httpx' in sys.modules,\n"
        "  'fitz': 'fitz' in sys.modules,\n"
        "  'pymupdf': 'pymupdf' in sys.modules,\n"
        "  'docx': 'docx' in sys.modules,\n"
        "  'has_status': hasattr(models, 'LegalDocStatus'),\n"
        "}\n"
        "print(json.dumps(loaded))\n"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert json.loads(res.stdout.strip()) == {
        "openai": False,
        "httpx": False,
        "fitz": False,
        "pymupdf": False,
        "docx": False,
        "has_status": True,
    }


def test_ccba_legal_dir_and_unknown_attr() -> None:
    """Verify __dir__ exposes __all__ and unknown attribute raises AttributeError."""
    import ccba_legal

    assert "LegalKnowledgeEngine" in dir(ccba_legal)
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent_legal_sym'"):
        _ = ccba_legal.nonexistent_legal_sym
