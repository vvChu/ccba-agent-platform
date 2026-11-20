"""test_dependency_contracts.py - Automated Governance Tests for Monorepo Dependency Contracts & Seams.

Verifies:
1. All monorepo packages adhere to dependency contracts (0 violations).
2. AST visitor correctly catches and flags:
   - Private submodule leakage across packages
   - Foundation leaf purity violations
   - Leaf independence violations
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from scripts.governance.check_dependency_contracts import (
    DependencyASTVisitor,
    check_all_contracts,
    check_init_lazy_exports_parity,
    scan_file_for_violations,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_real_codebase_dependency_contracts() -> None:
    """Verify that all monorepo source files satisfy 100% of dependency contracts."""
    passed, violations, files_scanned = check_all_contracts(PROJECT_ROOT)

    violation_details = [
        f"[{v.rule_name}] {v.file_path}:{v.line_number} -> {v.message}" for v in violations
    ]
    assert passed is True, f"Found {len(violations)} architectural violations:\n" + "\n".join(
        violation_details
    )
    assert files_scanned > 50, f"Expected >50 files scanned, but got {files_scanned}"


def test_ast_visitor_catches_private_submodule_violation() -> None:
    """Verify that importing private submodules from external package is flagged."""
    code = """
import os
from ccba_maskara._locator import AGENT_SPECS
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_ai",
        current_file=Path("packages/ccba-ai/src/ccba_ai/client.py"),
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "PrivateSubmoduleSeamViolation"
    assert "cannot import private submodule" in visitor.violations[0].message


def test_ast_visitor_allows_internal_private_submodule() -> None:
    """Verify that importing internal private submodules within the SAME package is allowed."""
    code = """
from ccba_maskara._locator import AGENT_SPECS
from ._rules import REGEX_PATTERNS
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_maskara",
        current_file=Path("packages/ccba-maskara/src/ccba_maskara/scanner.py"),
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 0


def test_ast_visitor_catches_foundation_purity_violation() -> None:
    """Verify that foundation leaf package cannot import domain/orchestrator package."""
    code = """
from ccba_legal import ASTParser
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_pdf_prep",
        current_file=Path("packages/ccba-pdf-prep/src/ccba_pdf_prep/core.py"),
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "FoundationLeafPurityViolation"


def test_ast_visitor_catches_leaf_independence_violation() -> None:
    """Verify that sibling leaf packages cannot cross-import each other."""
    code = """
import ccba_ooxml
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_pdf_prep",
        current_file=Path("packages/ccba-pdf-prep/src/ccba_pdf_prep/core.py"),
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "LeafIndependenceViolation"


def test_scripts_maskara_strict_seam_compliance() -> None:
    """Verify that scripts/maskara.py satisfies 100% of dependency seam contracts with 0 violations."""
    maskara_script = PROJECT_ROOT / "scripts" / "maskara.py"
    packages_dir = PROJECT_ROOT / "packages"
    violations = scan_file_for_violations(maskara_script, packages_dir)

    violation_details = [
        f"[{v.rule_name}] {v.file_path}:{v.line_number} -> {v.message}" for v in violations
    ]
    assert len(violations) == 0, (
        f"Expected 0 violations in scripts/maskara.py, but found {len(violations)}:\n"
        + "\n".join(violation_details)
    )


def test_ast_visitor_catches_raw_bypass_violation() -> None:
    """Verify that ad-hoc scripts cannot directly import raw bypass libraries without platform seam."""
    code = """
import docx
"""
    tree = ast.parse(code)
    raw_lines = code.splitlines()
    visitor = DependencyASTVisitor(
        current_package=None,
        current_file=Path("scripts/adhoc_script.py"),
        raw_lines=raw_lines,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "RawThirdPartyBypassViolation"
    assert (
        "Platform-Aware KISS requires using 'ccba_ooxml' seam instead"
        in visitor.violations[0].message
    )


def test_ast_visitor_allows_raw_bypass_with_comment() -> None:
    """Verify that inline comment # ccba:allow-raw-bypass allows exemption."""
    code = """
import docx  # ccba:allow-raw-bypass (synthetic mock generator)
"""
    tree = ast.parse(code)
    raw_lines = code.splitlines()
    visitor = DependencyASTVisitor(
        current_package=None,
        current_file=Path("scripts/adhoc_script.py"),
        raw_lines=raw_lines,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 0


def test_ast_visitor_catches_fitz_and_pymupdf_bypass() -> None:
    """Verify that direct imports of fitz or pymupdf outside ccba_pdf_prep raise violations."""
    code = """
import fitz
import pymupdf
"""
    tree = ast.parse(code)
    raw_lines = code.splitlines()
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=raw_lines,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 2
    assert all(v.rule_name == "RawThirdPartyBypassViolation" for v in visitor.violations)
    assert (
        "Platform-Aware KISS requires using 'ccba_pdf_prep' seam instead"
        in visitor.violations[0].message
    )
    assert (
        "Platform-Aware KISS requires using 'ccba_pdf_prep' seam instead"
        in visitor.violations[1].message
    )


def test_ast_visitor_catches_openpyxl_bypass() -> None:
    """Verify that direct imports of openpyxl outside ccba_ooxml raise violations."""
    code = """
from openpyxl import load_workbook
"""
    tree = ast.parse(code)
    raw_lines = code.splitlines()
    visitor = DependencyASTVisitor(
        current_package="ccba_legal",
        current_file=Path("packages/ccba-legal-intel/src/ccba_legal/parser.py"),
        raw_lines=raw_lines,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "RawThirdPartyBypassViolation"
    assert (
        "Platform-Aware KISS requires using 'ccba_ooxml' seam instead"
        in visitor.violations[0].message
    )


def test_ast_visitor_allows_fitz_with_comment() -> None:
    """Verify that fitz import with ccba:allow-raw-bypass is exempted."""
    code = """
import fitz  # ccba:allow-raw-bypass (low-level PDF image xref extraction)
"""
    tree = ast.parse(code)
    raw_lines = code.splitlines()
    visitor = DependencyASTVisitor(
        current_package="ccba_legal",
        current_file=Path("packages/ccba-legal-intel/src/ccba_legal/formula_harvester.py"),
        raw_lines=raw_lines,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 0


def test_ast_visitor_allows_multiline_import_with_comment() -> None:
    """Verify that multiline from import with trailing ccba:allow-raw-bypass is exempted."""
    code = """from openpyxl import (
    Workbook,
    load_workbook,
)  # ccba:allow-raw-bypass (isolated benchmark tool)
"""
    tree = ast.parse(code)
    raw_lines = code.splitlines()
    visitor = DependencyASTVisitor(
        current_package="ccba_ai",
        current_file=Path("packages/ccba-ai/scripts/bench.py"),
        raw_lines=raw_lines,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 0


def test_check_init_lazy_exports_parity_catches_orphan_symbol(tmp_path: Path) -> None:
    """Verify check_init_lazy_exports_parity flags symbols in _*_EXPORTS missing from __all__."""
    init_py = tmp_path / "__init__.py"
    init_py.write_text(
        '__all__ = ["upload_immutable_signed_pdf"]\n'
        '_FOLDER_EXPORTS = frozenset({"upload_immutable_signed_pdf", "forgotten_helper"})\n',
        encoding="utf-8",
    )
    violations = check_init_lazy_exports_parity(init_py, "tools.storage")
    assert len(violations) == 1
    assert violations[0].rule_name == "OrphanLazyExportViolation"
    assert "forgotten_helper" in violations[0].message


def test_probe_lazy_export_symbol_distinguishes_external_vs_internal_missing_dep(
    tmp_path: Path,
) -> None:
    """Verify uninstalled external deps skip while missing internal monorepo modules fail closed."""
    from scripts.governance.check_dependency_contracts import _probe_lazy_export_symbol

    init_py = tmp_path / "__init__.py"

    class _ExternalMissingMod:
        def __getattr__(self, name: str) -> object:
            raise ModuleNotFoundError("No module named 'pptx'", name="pptx")

    class _InternalMissingMod:
        def __getattr__(self, name: str) -> object:
            raise ModuleNotFoundError(
                "No module named 'ccba_ooxml.nonexistent_submod'",
                name="ccba_ooxml.nonexistent_submod",
            )

    assert (
        _probe_lazy_export_symbol(_ExternalMissingMod(), "Presentation", "ccba_ooxml", init_py)
        is None
    )
    internal_violation = _probe_lazy_export_symbol(
        _InternalMissingMod(), "MissingSym", "ccba_ooxml", init_py
    )
    assert internal_violation is not None
    assert internal_violation.rule_name == "UnboundAllExportViolation"
    assert "ccba_ooxml.nonexistent_submod" in internal_violation.message


def _load_pyproject_toml(pyproject_path: Path) -> dict[str, object]:
    """Load pyproject.toml across Python 3.10 (tomli) and 3.11+ (tomllib)."""
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 CI path
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]

    return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))


def test_pyproject_tid251_parity_with_seam_contracts() -> None:
    """Verify Ruff TID251 banned-api and per-file-ignores match seam-contracts.yaml 100%."""
    import yaml

    pyproject_data = _load_pyproject_toml(PROJECT_ROOT / "pyproject.toml")
    ruff_lint = pyproject_data["tool"]["ruff"]["lint"]  # type: ignore[index]
    assert "TID251" in ruff_lint["select"]  # type: ignore[operator]

    banned_api = ruff_lint["flake8-tidy-imports"]["banned-api"]  # type: ignore[index]
    contracts_data = yaml.safe_load(
        (PROJECT_ROOT / "seam-contracts.yaml").read_text(encoding="utf-8")
    )
    expected_forbidden = {
        mod
        for card in contracts_data.get("cards", [])
        for mod in card.get("forbidden_substitute_imports", [])
    }
    expected_modules = {"fitz", "pymupdf", "openpyxl", "docx", "fpdf", "graphviz"}
    assert expected_forbidden == expected_modules
    assert set(banned_api.keys()) == expected_forbidden  # type: ignore[arg-type]
    for mod, cfg in banned_api.items():  # type: ignore[union-attr]
        assert isinstance(cfg, dict) and str(cfg.get("msg", "")).strip(), (
            f"Missing TID251 remediation message for '{mod}'"
        )

    per_file = ruff_lint["per-file-ignores"]  # type: ignore[index]
    tid251_globs = {glob for glob, rules in per_file.items() if "TID251" in rules}  # type: ignore[union-attr]
    assert tid251_globs == {
        "packages/ccba-ooxml/**",
        "packages/ccba-pdf-prep/**",
        "packages/ccba-legal-intel/**",
        "packages/mdconverter/**",
        "packages/ccba-diagram/**",
    }


def test_raw_bypass_violation_appends_fix_hints_from_seam_contracts() -> None:
    """Verify RawThirdPartyBypassViolation keeps legacy prefix and appends 2 Seam Fix-Hint lines."""
    from scripts.governance.check_dependency_contracts import load_seam_bypass_restrictions

    restrictions, card_map = load_seam_bypass_restrictions(PROJECT_ROOT)
    tree = ast.parse("import fitz\n")
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/sample.py"),
        raw_lines=["import fitz"],
        bypass_restrictions=restrictions,
        card_map=card_map,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    msg = visitor.violations[0].message
    assert (
        "Platform-Aware KISS requires using 'ccba_pdf_prep:PDFProcessingPipeline' seam instead."
        in msg
    )
    assert "Gợi ý thay thế: from ccba_pdf_prep import PDFProcessingPipeline" in msg
    assert (
        "Tra cứu Seam: ccba-platform find-seam --in pdf --out tiles,segments,text,png --json" in msg
    )


def test_raw_bypass_violation_fallback_without_card_map_or_colon() -> None:
    """Verify fallback visitor with bypass_restrictions=None emits clean legacy prefix only."""
    tree = ast.parse("import docx\n")
    visitor = DependencyASTVisitor(
        current_package=None,
        current_file=Path("scripts/adhoc_sample.py"),
        raw_lines=["import docx"],
        bypass_restrictions=None,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    msg = visitor.violations[0].message
    assert "Platform-Aware KISS requires using 'ccba_ooxml' seam instead." in msg
    assert "Gợi ý thay thế:" not in msg
    assert "Tra cứu Seam:" not in msg

    malformed_visitor = DependencyASTVisitor(
        current_package=None,
        current_file=Path("scripts/adhoc_sample.py"),
        raw_lines=["import docx"],
        bypass_restrictions=None,
        card_map={"docx_legacy": {"capability": "invalid-non-dict"}},
    )
    malformed_visitor.visit(tree)
    assert len(malformed_visitor.violations) == 1
    assert "Tra cứu Seam:" not in malformed_visitor.violations[0].message
