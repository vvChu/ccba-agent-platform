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

