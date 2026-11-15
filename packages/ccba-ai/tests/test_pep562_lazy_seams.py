"""Tests for PEP 562 lazy exports and deferred client instantiation in ccba_ai."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

_AI_SHORTHAND_NAMES = {
    "chat",
    "complete",
    "chat_with_metadata",
    "stream",
    "chat_multi",
    "models",
    "transcribe",
    "encode_image",
    "embed",
}
_SPECIAL_EXPORTS = {"ai", "async_ai", "services", *_AI_SHORTHAND_NAMES}


def _extract_assign_value(tree: ast.Module, name: str) -> ast.expr | None:
    """Return the AST value node for a top-level unannotated assignment."""
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return node.value
    return None


def test_ccba_ai_all_and_lazy_exports_ast_parity() -> None:
    """Verify 2-way AST parity between __all__ and unannotated _LAZY_EXPORTS."""
    init_path = Path(__file__).resolve().parents[1] / "src" / "ccba_ai" / "__init__.py"
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))

    all_node = _extract_assign_value(tree, "__all__")
    lazy_node = _extract_assign_value(tree, "_LAZY_EXPORTS")
    assert isinstance(all_node, ast.List)
    assert isinstance(lazy_node, ast.Dict)

    all_symbols = [
        elt.value
        for elt in all_node.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    ]
    assert len(all_symbols) == 65
    assert len(set(all_symbols)) == 65

    lazy_keys = {
        k.value for k in lazy_node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    lazy_vals = [
        v.value
        for v in lazy_node.values
        if isinstance(v, ast.Constant) and isinstance(v.value, str)
    ]
    assert len(lazy_keys) == len(lazy_node.keys)
    assert all(val.startswith("ccba_ai.") for val in lazy_vals)
    assert lazy_keys.isdisjoint(_SPECIAL_EXPORTS)
    assert set(all_symbols) == lazy_keys | _SPECIAL_EXPORTS


def test_ccba_ai_routing_import_does_not_eager_load_heavy_deps() -> None:
    """Verify importing leaf ccba_ai.routing does not pull client, services, httpx, or openai."""
    code = (
        "import json, sys\n"
        "import ccba_ai.routing as routing\n"
        "loaded = {\n"
        "  'openai': 'openai' in sys.modules,\n"
        "  'httpx': 'httpx' in sys.modules,\n"
        "  'client': 'ccba_ai.client' in sys.modules,\n"
        "  'services': 'ccba_ai.services' in sys.modules,\n"
        "  'callable': callable(routing.choose_model),\n"
        "}\n"
        "print(json.dumps(loaded))\n"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    loaded = json.loads(res.stdout.strip())
    assert loaded == {
        "openai": False,
        "httpx": False,
        "client": False,
        "services": False,
        "callable": True,
    }


def test_ccba_ai_deferred_singletons_and_shorthands_contract() -> None:
    """Verify ai, async_ai, shorthands, and services lazy resolution preserve identity and dir()."""
    code = (
        "import sys\n"
        "import ccba_ai\n"
        "assert ccba_ai.__version__ == '1.2.0'\n"
        "assert 'ccba_ai.client' not in sys.modules\n"
        "assert 'services' in dir(ccba_ai) and 'ai' in dir(ccba_ai)\n"
        "from ccba_ai import ai, async_ai\n"
        "assert 'ccba_ai.services' not in sys.modules\n"
        "from ccba_ai.client import AIClient, AsyncAIClient\n"
        "assert isinstance(ai, AIClient)\n"
        "assert isinstance(async_ai, AsyncAIClient)\n"
        "assert ccba_ai.chat == ai.chat\n"
        "assert ccba_ai.embed == ai.embed\n"
        "assert ccba_ai.services is sys.modules['ccba_ai.services']\n"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr


def test_ccba_ai_unknown_attribute_raises_attribute_error() -> None:
    """Verify accessing an unknown attribute on ccba_ai raises standard AttributeError."""
    import ccba_ai

    with pytest.raises(AttributeError, match="has no attribute 'does_not_exist_xyz'"):
        _ = ccba_ai.does_not_exist_xyz
