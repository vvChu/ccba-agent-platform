#!/usr/bin/env python3
"""check_dependency_contracts.py - Native AST Dependency Governance & Seam Linter.

Validates architectural boundaries and seam invariants across monorepo packages:
1. Private Submodule Invariant: External callers cannot import private modules (`_*`) from other packages.
2. Foundation Leaf Purity Invariant: `ccba_pdf_prep` and `ccba_ooxml` cannot import higher-level domain packages.
3. Leaf Independence Invariant: Leaf packages cannot cross-import each other.
4. Import-Linter Integration: Can delegate to `lint-imports` when `.importlinter` is present.
"""

from __future__ import annotations

import argparse
import ast
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# Monorepo packages and their root package names
PACKAGE_MAP: dict[str, str] = {
    "ccba-ai": "ccba_ai",
    "ccba-diagram": "ccba_diagram",
    "ccba-harness": "ccba_harness",
    "ccba-legal-intel": "ccba_legal",
    "ccba-maskara": "ccba_maskara",
    "ccba-notebooklm": "ccba_notebooklm",
    "ccba-ooxml": "ccba_ooxml",
    "ccba-pdf-prep": "ccba_pdf_prep",
    "ccba-qc-core": "ccba_qc_core",
    "mdconverter": "mdconverter",
}

MONOREPO_ROOT_MODULES = set(PACKAGE_MAP.values())
LEAF_FOUNDATION_PACKAGES = {"ccba_pdf_prep", "ccba_ooxml", "ccba_diagram"}
HIGHER_DOMAIN_PACKAGES = {
    "ccba_legal",
    "ccba_notebooklm",
    "ccba_ai",
    "ccba_harness",
    "ccba_qc_core",
}

# Raw third-party library bypass mapping: module -> (allowed_packages, seam_replacement)
RAW_BYPASS_RESTRICTIONS: dict[str, tuple[set[str], str]] = {
    "docx": ({"ccba_ooxml", "ccba_legal", "mdconverter"}, "ccba_ooxml"),
}


@dataclass
class ImportViolation:
    file_path: Path
    line_number: int
    imported_module: str
    rule_name: str
    message: str


class DependencyASTVisitor(ast.NodeVisitor):
    """AST Visitor that inspects import statements for dependency violations."""

    def __init__(
        self,
        current_package: str | None,
        current_file: Path,
        raw_lines: list[str] | None = None,
    ) -> None:
        self.current_package = current_package
        self.current_file = current_file
        self.raw_lines = raw_lines
        self.violations: list[ImportViolation] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_module_import(alias.name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self._check_module_import(node.module, node.lineno)
            # Also check imported member names for private member/submodule access (e.g., from pkg import _private)
            root_mod = node.module.split(".")[0]
            if root_mod in MONOREPO_ROOT_MODULES and root_mod != self.current_package:
                for alias in node.names:
                    if alias.name.startswith("_") and not alias.name.startswith("__"):
                        self.violations.append(
                            ImportViolation(
                                file_path=self.current_file,
                                line_number=node.lineno,
                                imported_module=f"{node.module}.{alias.name}",
                                rule_name="PrivateSubmoduleSeamViolation",
                                message=(
                                    f"Package '{self.current_package or 'external'}' cannot import private "
                                    f"symbol '{alias.name}' from '{node.module}'. "
                                    f"Must import from '{root_mod}' public seam."
                                ),
                            )
                        )
        self.generic_visit(node)

    def _check_module_import(self, module_name: str, line_number: int) -> None:
        parts = module_name.split(".")
        root_mod = parts[0]

        # Check 0: Raw Third-Party Bypass (Platform-Aware KISS Guard)
        if root_mod in RAW_BYPASS_RESTRICTIONS:
            allowed_pkgs, seam_pkg = RAW_BYPASS_RESTRICTIONS[root_mod]
            if self.current_package not in allowed_pkgs:
                # Check for explicit inline exemption comment
                line_has_exemption = False
                if self.raw_lines and 1 <= line_number <= len(self.raw_lines):
                    line_text = self.raw_lines[line_number - 1]
                    line_has_exemption = (
                        "ccba:allow-raw-bypass" in line_text or "noqa: raw-bypass" in line_text
                    )

                if not line_has_exemption:
                    self.violations.append(
                        ImportViolation(
                            file_path=self.current_file,
                            line_number=line_number,
                            imported_module=module_name,
                            rule_name="RawThirdPartyBypassViolation",
                            message=(
                                f"File '{self.current_file.name}' cannot directly import raw '{root_mod}'. "
                                f"Platform-Aware KISS requires using '{seam_pkg}' seam instead."
                            ),
                        )
                    )

        if root_mod not in MONOREPO_ROOT_MODULES:
            return

        # Check 1: Private submodule import from another package
        if root_mod != self.current_package:
            for sub_part in parts[1:]:
                if sub_part.startswith("_") and not sub_part.startswith("__"):
                    self.violations.append(
                        ImportViolation(
                            file_path=self.current_file,
                            line_number=line_number,
                            imported_module=module_name,
                            rule_name="PrivateSubmoduleSeamViolation",
                            message=(
                                f"Package '{self.current_package or 'external'}' cannot import private "
                                f"submodule '{module_name}'. Must import from '{root_mod}' public seam."
                            ),
                        )
                    )
                    break

        # Check 2: Foundation leaf purity (ccba_pdf_prep / ccba_ooxml cannot import domain packages)
        if self.current_package in LEAF_FOUNDATION_PACKAGES:
            if root_mod in HIGHER_DOMAIN_PACKAGES:
                self.violations.append(
                    ImportViolation(
                        file_path=self.current_file,
                        line_number=line_number,
                        imported_module=module_name,
                        rule_name="FoundationLeafPurityViolation",
                        message=(
                            f"Foundation leaf package '{self.current_package}' is not allowed to import "
                            f"domain package '{root_mod}'."
                        ),
                    )
                )

        # Check 3: Leaf independence (ccba_ooxml and ccba_pdf_prep cannot import each other)
        if self.current_package in LEAF_FOUNDATION_PACKAGES:
            if root_mod in LEAF_FOUNDATION_PACKAGES and root_mod != self.current_package:
                self.violations.append(
                    ImportViolation(
                        file_path=self.current_file,
                        line_number=line_number,
                        imported_module=module_name,
                        rule_name="LeafIndependenceViolation",
                        message=(
                            f"Leaf package '{self.current_package}' cannot depend on sibling leaf '{root_mod}'."
                        ),
                    )
                )


def get_package_for_file(file_path: Path, packages_dir: Path) -> str | None:
    """Identify which monorepo package a file belongs to."""
    try:
        rel = file_path.relative_to(packages_dir)
        pkg_folder = rel.parts[0]
        return PACKAGE_MAP.get(pkg_folder)
    except ValueError:
        return None


def scan_file_for_violations(file_path: Path, packages_dir: Path) -> list[ImportViolation]:
    """Parse and check a single Python file for architectural dependency violations."""
    pkg = get_package_for_file(file_path, packages_dir)
    try:
        content = file_path.read_text(encoding="utf-8")
        raw_lines = content.splitlines()
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        return [
            ImportViolation(
                file_path=file_path,
                line_number=1,
                imported_module=str(file_path),
                rule_name="SyntaxOrEncodingError",
                message=f"Failed to read or parse Python file: {exc}",
            )
        ]

    visitor = DependencyASTVisitor(current_package=pkg, current_file=file_path, raw_lines=raw_lines)
    visitor.visit(tree)
    return visitor.violations


def check_all_contracts(
    project_root: Path,
    include_scripts: bool = True,
) -> tuple[bool, list[ImportViolation], int]:
    """Scan all Python source files in packages/ and scripts/ for dependency violations."""
    packages_dir = project_root / "packages"
    violations: list[ImportViolation] = []
    files_scanned = 0

    # 1. Scan packages/*/src
    if packages_dir.is_dir():
        for py_file in packages_dir.glob("*/src/**/*.py"):
            if "__pycache__" in py_file.parts:
                continue
            files_scanned += 1
            file_violations = scan_file_for_violations(py_file, packages_dir)
            violations.extend(file_violations)

    # 2. Optionally scan scripts/
    if include_scripts:
        scripts_dir = project_root / "scripts"
        if scripts_dir.is_dir():
            for py_file in scripts_dir.glob("**/*.py"):
                if (
                    "__pycache__" in py_file.parts
                    or "tests" in py_file.parts
                    or "archive" in py_file.parts
                ):
                    continue
                files_scanned += 1
                file_violations = scan_file_for_violations(py_file, packages_dir)
                violations.extend(file_violations)

    passed = len(violations) == 0
    return passed, violations, files_scanned


def run_import_linter_tool(project_root: Path) -> int:
    """Run import-linter if available with sys.path properly configured."""
    try:
        packages_dir = project_root / "packages"
        for p in packages_dir.glob("*"):
            src = p / "src"
            if src.is_dir() and str(src) not in sys.path:
                sys.path.insert(0, str(src))

        from importlinter.cli import lint_imports  # type: ignore[import-not-found]

        config_file = project_root / ".importlinter"
        if config_file.exists():
            return int(lint_imports(config_filename=str(config_file)))
        return int(lint_imports())
    except ImportError:
        print("[ImportLinter] 'import-linter' package not installed, skipping external runner.")
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for check_dependency_contracts."""
    parser = argparse.ArgumentParser(description="CCBA Monorepo Dependency Contract & Seam Linter")
    parser.add_argument(
        "--with-import-linter",
        action="store_true",
        help="Also execute external import-linter runner (.importlinter)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="Project root directory",
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    start_time = time.time()
    print("=" * 60)
    print("🛡️  CCBA DEPENDENCY & SEAM CONTRACT LINTER")
    print("=" * 60)

    passed, violations, files_scanned = check_all_contracts(args.root)
    elapsed = time.time() - start_time

    print(f"📁 Scanned {files_scanned} Python source files in {elapsed:.3f}s.")

    if passed:
        print(
            "✅ Tất cả các gói Monorepo đều tuân thủ 100% ranh giới phụ thuộc và Seam invariants!"
        )
    else:
        print(f"❌ Phát hiện {len(violations)} lỗi vi phạm hợp đồng kiến trúc:")
        for v in violations:
            rel_path = v.file_path.relative_to(args.root)
            print(f"  - [{v.rule_name}] {rel_path}:{v.line_number} -> {v.message}")

    if args.with_import_linter:
        print("\n" + "-" * 60)
        print("🔍 Executing Industry-Standard import-linter:")
        il_code = run_import_linter_tool(args.root)
        if il_code != 0:
            return il_code

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
