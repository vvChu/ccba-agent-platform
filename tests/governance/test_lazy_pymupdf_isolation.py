"""Tests enforcing lazy PyMuPDF (pymupdf) isolation and warning-free loading."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _is_type_checking_guard(test_node: ast.expr) -> bool:
    """Return True if an `if` condition checks `TYPE_CHECKING`."""
    if isinstance(test_node, ast.Name) and test_node.id == "TYPE_CHECKING":
        return True
    if isinstance(test_node, ast.Attribute) and test_node.attr == "TYPE_CHECKING":
        return True
    return False


def _collect_eager_or_deprecated_fitz_imports(root: Path) -> list[str]:
    """Return violations for top-level or deprecated `import fitz` outside tests."""
    findings: list[str] = []
    for search_dir in (root / "packages", root / "tools"):
        if not search_dir.is_dir():
            continue
        for py_file in sorted(search_dir.rglob("*.py")):
            if "tests" in py_file.parts:
                continue
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            if "fitz" not in source and "pymupdf" not in source:
                continue
            tree = ast.parse(source, filename=str(py_file))
            # Check top-level body (skipping `if TYPE_CHECKING:` and lazy def/class bodies)
            for stmt in tree.body:
                if isinstance(stmt, ast.If) and _is_type_checking_guard(stmt.test):
                    continue
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    nodes_to_scan = [
                        n for n in ast.walk(stmt) if isinstance(n, (ast.Import, ast.ImportFrom))
                    ]
                    eager_module_level = False
                else:
                    nodes_to_scan = [
                        n for n in ast.walk(stmt) if isinstance(n, (ast.Import, ast.ImportFrom))
                    ]
                    eager_module_level = True
                for node in nodes_to_scan:
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == "fitz" or alias.name.startswith("fitz."):
                                findings.append(
                                    f"{py_file.relative_to(root)}:{node.lineno}: deprecated `import {alias.name}`"
                                )
                            elif eager_module_level and (
                                alias.name == "pymupdf" or alias.name.startswith("pymupdf.")
                            ):
                                findings.append(
                                    f"{py_file.relative_to(root)}:{node.lineno}: eager top-level `import {alias.name}`"
                                )
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        if node.module == "fitz" or node.module.startswith("fitz."):
                            findings.append(
                                f"{py_file.relative_to(root)}:{node.lineno}: deprecated `from {node.module} import ...`"
                            )
                        elif eager_module_level and (
                            node.module == "pymupdf" or node.module.startswith("pymupdf.")
                        ):
                            findings.append(
                                f"{py_file.relative_to(root)}:{node.lineno}: eager top-level `from {node.module} import ...`"
                            )
    return findings


def test_no_top_level_or_deprecated_fitz_imports_in_production_code() -> None:
    """Production modules must not import fitz/pymupdf eagerly or use deprecated `import fitz`."""
    findings = _collect_eager_or_deprecated_fitz_imports(REPO_ROOT)
    assert findings == []


@pytest.mark.parametrize(
    "module_name",
    [
        "ccba_pdf_prep",
        "ccba_pdf_prep.core",
        "ccba_qc_core.pipeline",
        "ccba_legal.provenance",
    ],
)
def test_module_import_keeps_pymupdf_lazy_and_quiet(module_name: str) -> None:
    """Importing PDF-related modules must not eagerly load fitz/pymupdf or emit warnings."""
    code = (
        "import json, sys\n"
        f"import {module_name}\n"
        "print(json.dumps({'fitz': 'fitz' in sys.modules, 'pymupdf': 'pymupdf' in sys.modules}))\n"
    )
    res = subprocess.run(
        [sys.executable, "-W", "default", "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(res.stdout.strip()) == {"fitz": False, "pymupdf": False}
    assert "fitz" not in res.stderr.lower()


def test_get_fitz_sets_pymupdf_message_and_suppresses_fitz_warning() -> None:
    """Calling ccba_pdf_prep._pymupdf._get_fitz sets PYMUPDF_MESSAGE=fd:2 cleanly."""
    code = (
        "import json, os, sys\n"
        "from ccba_pdf_prep._pymupdf import _get_fitz\n"
        "mod = _get_fitz()\n"
        "print(json.dumps({\n"
        "  'env': os.environ.get('PYMUPDF_MESSAGE'),\n"
        "  'mod_name': mod.__name__,\n"
        "  'pymupdf_loaded': 'pymupdf' in sys.modules,\n"
        "}))\n"
    )
    env = dict(os.environ)
    env.pop("PYMUPDF_MESSAGE", None)
    res = subprocess.run(
        [sys.executable, "-W", "default", "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert json.loads(res.stdout.strip()) == {
        "env": "fd:2",
        "mod_name": "pymupdf",
        "pymupdf_loaded": True,
    }
    assert "The `fitz` API is deprecated" not in res.stderr
