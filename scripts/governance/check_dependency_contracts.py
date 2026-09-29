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
import re
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

# Raw third-party library bypass mapping (default fallback if seam-contracts.yaml is absent)
RAW_BYPASS_RESTRICTIONS: dict[str, tuple[set[str], str]] = {
    "docx": ({"ccba_ooxml", "ccba_legal", "mdconverter"}, "ccba_ooxml"),
    "fitz": ({"ccba_pdf_prep"}, "ccba_pdf_prep"),
    "pymupdf": ({"ccba_pdf_prep"}, "ccba_pdf_prep"),
    "openpyxl": ({"ccba_ooxml"}, "ccba_ooxml"),
}

VALID_QUARANTINE_REASONS = {
    "hardware_mismatch",
    "seam_regression",
    "health_timeout",
    "version_conflict",
}
ISSUE_URL_PATTERN = re.compile(r"^https://github\.com/vvChu/ccba-agent-platform/issues/\d+$")
QUARANTINE_KV_PATTERN = re.compile(r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s#]+))')


@dataclass
class SeamCardRestriction:
    seam_id: str
    allowed_packages: set[str]
    seam_replacement: str
    forbidden_imports: list[str]


def load_seam_bypass_restrictions(
    project_root: Path,
) -> tuple[dict[str, SeamCardRestriction], dict[str, dict[str, Any]]]:
    """Dynamically build bypass restrictions from seam-contracts.yaml."""
    contracts_file = project_root / "seam-contracts.yaml"
    restrictions: dict[str, SeamCardRestriction] = {}
    card_map: dict[str, dict[str, Any]] = {}

    if contracts_file.is_file():
        try:
            import yaml

            data = yaml.safe_load(contracts_file.read_text(encoding="utf-8")) or {}
            cards = data.get("cards", [])
            for card in cards:
                seam_id = card.get("seam_id")
                if not seam_id:
                    continue
                card_map[seam_id] = card
                imp_pkgs = set(card.get("implementation_packages", []))
                seam_repl = card.get("import_path", "")
                if not seam_repl and card.get("command"):
                    seam_repl = card.get("command")

                for forbidden in card.get("forbidden_substitute_imports", []):
                    restrictions[forbidden] = SeamCardRestriction(
                        seam_id=seam_id,
                        allowed_packages=imp_pkgs,
                        seam_replacement=seam_repl,
                        forbidden_imports=card.get("forbidden_substitute_imports", []),
                    )
        except Exception:
            pass

    # Fallback to static RAW_BYPASS_RESTRICTIONS if empty
    if not restrictions:
        for mod, (allowed, repl) in RAW_BYPASS_RESTRICTIONS.items():
            restrictions[mod] = SeamCardRestriction(
                seam_id=f"{mod}_legacy",
                allowed_packages=allowed,
                seam_replacement=repl,
                forbidden_imports=[mod],
            )

    return restrictions, card_map


def parse_quarantine_marker(line_text: str) -> dict[str, str] | None:
    """Extract key-value parameters from # ccba:quarantine marker."""
    if "ccba:quarantine" not in line_text:
        return None
    part = line_text.split("ccba:quarantine", 1)[1]
    matches = QUARANTINE_KV_PATTERN.findall(part)
    params: dict[str, str] = {}
    for key, v1, v2, v3 in matches:
        val = v1 or v2 or v3 or ""
        params[key.strip()] = val.strip()
    return params


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
        bypass_restrictions: dict[str, SeamCardRestriction] | None = None,
        card_map: dict[str, dict[str, Any]] | None = None,
        strict_quarantine: bool = False,
        enforce_quarantine_path: bool = False,
    ) -> None:
        self.current_package = current_package
        self.current_file = current_file
        self.raw_lines = raw_lines
        if bypass_restrictions is None:
            self.restrictions = {
                mod: SeamCardRestriction(
                    seam_id=f"{mod}_legacy",
                    allowed_packages=allowed,
                    seam_replacement=repl,
                    forbidden_imports=[mod],
                )
                for mod, (allowed, repl) in RAW_BYPASS_RESTRICTIONS.items()
            }
        else:
            self.restrictions = bypass_restrictions
        self.card_map = card_map or {}
        self.strict_quarantine = strict_quarantine
        self.enforce_quarantine_path = enforce_quarantine_path
        self.violations: list[ImportViolation] = []
        self.legacy_bypasses: list[tuple[Path, int, str]] = []
        self.active_quarantines: list[tuple[Path, int, str, str, str]] = []

    def visit_Import(self, node: ast.Import) -> None:
        end_lineno = getattr(node, "end_lineno", node.lineno)
        for alias in node.names:
            self._check_module_import(alias.name, node.lineno, end_lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            end_lineno = getattr(node, "end_lineno", node.lineno)
            self._check_module_import(node.module, node.lineno, end_lineno)
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

    def _check_module_import(
        self, module_name: str, line_number: int, end_line_number: int | None = None
    ) -> None:
        parts = module_name.split(".")
        root_mod = parts[0]

        # Check 0: Raw Third-Party Bypass (Platform-Aware KISS Guard & Quarantine Governance)
        if root_mod in self.restrictions:
            restriction = self.restrictions[root_mod]
            allowed_pkgs = restriction.allowed_packages
            seam_pkg = restriction.seam_replacement

            if self.current_package not in allowed_pkgs:
                # Inspect line span for quarantine or legacy exemption comments
                start_idx = max(0, line_number - 1)
                end_line = end_line_number if end_line_number is not None else line_number
                end_idx = min(len(self.raw_lines), end_line) if self.raw_lines else 0

                quarantine_line: str | None = None
                legacy_line: str | None = None
                if self.raw_lines:
                    for idx in range(start_idx, end_idx):
                        lt = self.raw_lines[idx]
                        if "ccba:quarantine" in lt:
                            quarantine_line = lt
                            break
                        if "ccba:allow-raw-bypass" in lt or "noqa: raw-bypass" in lt:
                            legacy_line = lt

                if quarantine_line is not None:
                    # Validate quarantine marker
                    params = parse_quarantine_marker(quarantine_line) or {}
                    seam_id = params.get("seam_id", "")
                    reason = params.get("reason", "")
                    until_str = params.get("until", "")
                    issue = params.get("issue", "")

                    missing_fields = []
                    for f in ["seam_id", "reason", "until", "issue"]:
                        if not params.get(f):
                            missing_fields.append(f)

                    if missing_fields:
                        self.violations.append(
                            ImportViolation(
                                file_path=self.current_file,
                                line_number=line_number,
                                imported_module=module_name,
                                rule_name="QuarantineMarkerViolation",
                                message=(
                                    f"Quarantine marker missing required field(s): {', '.join(missing_fields)}. "
                                    f"Required: seam_id=<id> reason=<reason> until=YYYY-MM-DD issue=<url>"
                                ),
                            )
                        )
                    else:
                        # 1. Validate seam_id
                        if ".." in seam_id or "/" in seam_id or "\\" in seam_id:
                            self.violations.append(
                                ImportViolation(
                                    file_path=self.current_file,
                                    line_number=line_number,
                                    imported_module=module_name,
                                    rule_name="QuarantineMarkerViolation",
                                    message=f"Quarantine seam_id '{seam_id}' contains invalid path characters.",
                                )
                            )
                        elif self.card_map and seam_id not in self.card_map:
                            self.violations.append(
                                ImportViolation(
                                    file_path=self.current_file,
                                    line_number=line_number,
                                    imported_module=module_name,
                                    rule_name="QuarantineMarkerViolation",
                                    message=f"Quarantine seam_id '{seam_id}' not found in seam-contracts.yaml.",
                                )
                            )
                        else:
                            # 2. Validate forbidden import match
                            card = self.card_map.get(seam_id, {})
                            forbidden_list = card.get("forbidden_substitute_imports", [])
                            if forbidden_list and root_mod not in forbidden_list:
                                self.violations.append(
                                    ImportViolation(
                                        file_path=self.current_file,
                                        line_number=line_number,
                                        imported_module=module_name,
                                        rule_name="QuarantineMarkerViolation",
                                        message=(
                                            f"Quarantine marker for seam '{seam_id}' does not govern forbidden module '{root_mod}'. "
                                            f"Card governs: {forbidden_list}."
                                        ),
                                    )
                                )

                        # 3. Validate reason
                        if reason not in VALID_QUARANTINE_REASONS:
                            self.violations.append(
                                ImportViolation(
                                    file_path=self.current_file,
                                    line_number=line_number,
                                    imported_module=module_name,
                                    rule_name="QuarantineMarkerViolation",
                                    message=(
                                        f"Invalid quarantine reason '{reason}'. "
                                        f"Must be one of: {sorted(VALID_QUARANTINE_REASONS)}."
                                    ),
                                )
                            )

                        # 4. Validate issue URL
                        if not ISSUE_URL_PATTERN.match(issue):
                            self.violations.append(
                                ImportViolation(
                                    file_path=self.current_file,
                                    line_number=line_number,
                                    imported_module=module_name,
                                    rule_name="QuarantineMarkerViolation",
                                    message=(
                                        f"Invalid issue URL '{issue}'. "
                                        f"Must match format 'https://github.com/vvChu/ccba-agent-platform/issues/<number>'."
                                    ),
                                )
                            )

                        # 5. Validate until date
                        try:
                            until_date = datetime.strptime(until_str, "%Y-%m-%d").date()
                            current_utc_date = datetime.now(timezone.utc).date()
                            if until_date < current_utc_date:
                                self.violations.append(
                                    ImportViolation(
                                        file_path=self.current_file,
                                        line_number=line_number,
                                        imported_module=module_name,
                                        rule_name="QuarantineExpiredViolation",
                                        message=(
                                            f"Quarantine for seam '{seam_id}' expired on {until_str} "
                                            f"(current UTC date: {current_utc_date}). Issue: {issue}."
                                        ),
                                    )
                                )
                        except ValueError:
                            self.violations.append(
                                ImportViolation(
                                    file_path=self.current_file,
                                    line_number=line_number,
                                    imported_module=module_name,
                                    rule_name="QuarantineMarkerViolation",
                                    message=f"Invalid date format in until='{until_str}'. Expected YYYY-MM-DD.",
                                )
                            )

                        # 6. Validate quarantine path if enforced
                        if self.enforce_quarantine_path:
                            is_quarantine_path = (
                                "adapters/quarantine" in self.current_file.as_posix()
                                or "quarantine" in self.current_file.parts
                            )
                            if not is_quarantine_path:
                                self.violations.append(
                                    ImportViolation(
                                        file_path=self.current_file,
                                        line_number=line_number,
                                        imported_module=module_name,
                                        rule_name="QuarantinePathViolation",
                                        message=(
                                            f"Quarantined import must reside in 'adapters/quarantine/<seam_id>.py'. "
                                            f"Found in '{self.current_file}'."
                                        ),
                                    )
                                )

                    # If no violations were added for this import, record active quarantine
                    if not any(
                        v.line_number == line_number and v.file_path == self.current_file
                        for v in self.violations
                    ):
                        self.active_quarantines.append(
                            (self.current_file, line_number, root_mod, seam_id, until_str)
                        )

                elif legacy_line is not None:
                    if self.strict_quarantine:
                        self.violations.append(
                            ImportViolation(
                                file_path=self.current_file,
                                line_number=line_number,
                                imported_module=module_name,
                                rule_name="LegacyBypassDeprecatedViolation",
                                message=(
                                    f"File '{self.current_file.name}' uses legacy bypass '# ccba:allow-raw-bypass'. "
                                    f"Under strict quarantine, must migrate to '# ccba:quarantine seam_id=... reason=... until=... issue=...' or use Seam."
                                ),
                            )
                        )
                    else:
                        self.legacy_bypasses.append((self.current_file, line_number, root_mod))

                else:
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


def scan_file_for_violations(
    file_path: Path,
    packages_dir: Path,
    bypass_restrictions: dict[str, SeamCardRestriction] | None = None,
    card_map: dict[str, dict[str, Any]] | None = None,
    strict_quarantine: bool = False,
    enforce_quarantine_path: bool = False,
    visitor_collector: list[DependencyASTVisitor] | None = None,
) -> list[ImportViolation]:
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

    visitor = DependencyASTVisitor(
        current_package=pkg,
        current_file=file_path,
        raw_lines=raw_lines,
        bypass_restrictions=bypass_restrictions,
        card_map=card_map,
        strict_quarantine=strict_quarantine,
        enforce_quarantine_path=enforce_quarantine_path,
    )
    visitor.visit(tree)
    if visitor_collector is not None:
        visitor_collector.append(visitor)
    return visitor.violations


def check_all_contracts(
    project_root: Path,
    include_scripts: bool = True,
    strict_quarantine: bool = False,
    enforce_quarantine_path: bool = False,
    audit_report: dict[str, Any] | None = None,
) -> tuple[bool, list[ImportViolation], int]:
    """Scan all Python source files in packages/ and scripts/ for dependency violations."""
    packages_dir = project_root / "packages"
    violations: list[ImportViolation] = []
    files_scanned = 0

    bypass_restrictions, card_map = load_seam_bypass_restrictions(project_root)
    all_visitors: list[DependencyASTVisitor] = []

    # 1. Scan packages/*/src
    if packages_dir.is_dir():
        for py_file in sorted(packages_dir.glob("*/src/**/*.py"), key=lambda p: p.as_posix()):
            if "__pycache__" in py_file.parts:
                continue
            files_scanned += 1
            file_violations = scan_file_for_violations(
                py_file,
                packages_dir,
                bypass_restrictions=bypass_restrictions,
                card_map=card_map,
                strict_quarantine=strict_quarantine,
                enforce_quarantine_path=enforce_quarantine_path,
                visitor_collector=all_visitors,
            )
            violations.extend(file_violations)

    # 2. Optionally scan scripts/
    if include_scripts:
        scripts_dir = project_root / "scripts"
        if scripts_dir.is_dir():
            for py_file in sorted(scripts_dir.glob("**/*.py"), key=lambda p: p.as_posix()):
                if (
                    "__pycache__" in py_file.parts
                    or "tests" in py_file.parts
                    or "archive" in py_file.parts
                ):
                    continue
                files_scanned += 1
                file_violations = scan_file_for_violations(
                    py_file,
                    packages_dir,
                    bypass_restrictions=bypass_restrictions,
                    card_map=card_map,
                    strict_quarantine=strict_quarantine,
                    enforce_quarantine_path=enforce_quarantine_path,
                    visitor_collector=all_visitors,
                )
                violations.extend(file_violations)

    if audit_report is not None:
        legacy_list: list[tuple[Path, int, str]] = []
        quarantine_list: list[tuple[Path, int, str, str, str]] = []
        for v in all_visitors:
            legacy_list.extend(v.legacy_bypasses)
            quarantine_list.extend(v.active_quarantines)
        audit_report["legacy_bypasses"] = legacy_list
        audit_report["active_quarantines"] = quarantine_list

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
        "--strict-quarantine",
        action="store_true",
        help="Reject legacy '# ccba:allow-raw-bypass' and enforce strict quarantine markers.",
    )
    parser.add_argument(
        "--enforce-quarantine-path",
        action="store_true",
        help="Require all quarantined imports to reside in 'adapters/quarantine/'.",
    )
    parser.add_argument(
        "--dry-run-quarantine",
        action="store_true",
        help="Audit and display all legacy bypasses and active quarantine markers.",
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

    audit_report: dict[str, Any] = {}
    passed, violations, files_scanned = check_all_contracts(
        args.root,
        strict_quarantine=args.strict_quarantine,
        enforce_quarantine_path=args.enforce_quarantine_path,
        audit_report=audit_report,
    )
    elapsed = time.time() - start_time

    print(f"📁 Scanned {files_scanned} Python source files in {elapsed:.3f}s.")

    if args.dry_run_quarantine:
        legacy = audit_report.get("legacy_bypasses", [])
        active_q = audit_report.get("active_quarantines", [])
        print("\n" + "=" * 60)
        print("📋 QUARANTINE DRY-RUN AUDIT REPORT")
        print("=" * 60)
        print(f"• Active Valid Quarantines: {len(active_q)}")
        for path, line_no, mod, s_id, until in active_q:
            try:
                rel = path.relative_to(args.root)
            except ValueError:
                rel = path
            print(f"  - [QUARANTINE] {rel}:{line_no} -> module='{mod}' seam='{s_id}' until={until}")

        print(f"\n• Legacy Raw Bypasses ('# ccba:allow-raw-bypass'): {len(legacy)}")
        for path, line_no, mod in legacy:
            try:
                rel = path.relative_to(args.root)
            except ValueError:
                rel = path
            print(f"  - [LEGACY] {rel}:{line_no} -> module='{mod}' (pending migration)")
        print("=" * 60)

    if passed:
        print(
            "✅ Tất cả các gói Monorepo đều tuân thủ 100% ranh giới phụ thuộc và Seam invariants!"
        )
    else:
        print(f"❌ Phát hiện {len(violations)} lỗi vi phạm hợp đồng kiến trúc:")
        for v in violations:
            try:
                rel_path = v.file_path.relative_to(args.root)
            except ValueError:
                rel_path = v.file_path
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
