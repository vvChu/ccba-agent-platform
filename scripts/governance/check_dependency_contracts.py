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

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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
    project_root: Path | None = None,
    hub_root: Path | None = None,
) -> tuple[dict[str, SeamCardRestriction], dict[str, dict[str, Any]]]:
    """Dynamically build bypass restrictions from Hub seam contracts or Spoke snapshot.

    Raises:
        CatalogSnapshotMissing: When neither physical Hub nor valid snapshot exists.
        CorruptSnapshotError: When snapshot bytes or provenance are corrupted.
    """
    from scripts.spoke.catalog_snapshot_client import (
        CatalogSnapshotMissing,
        CorruptSnapshotError,
        resolve_catalog_context,
    )

    restrictions: dict[str, SeamCardRestriction] = {}
    card_map: dict[str, dict[str, Any]] = {}
    target_root = hub_root or project_root or ROOT_DIR

    try:
        data, _, _, _ = resolve_catalog_context(project_root=target_root)
    except (CatalogSnapshotMissing, CorruptSnapshotError):
        # Strict Fail-Closed: Never silently fall back to RAW_BYPASS_RESTRICTIONS
        raise
    except Exception as e:
        raise RuntimeError(f"Lỗi khi nạp seam contracts cho linter: {e}") from e

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

    def _add_violation(
        self, line_number: int, module_name: str, rule_name: str, message: str
    ) -> None:
        self.violations.append(
            ImportViolation(
                file_path=self.current_file,
                line_number=line_number,
                imported_module=module_name,
                rule_name=rule_name,
                message=message,
            )
        )

    def _find_exemption_markers(
        self, line_number: int, end_line_number: int | None
    ) -> tuple[str | None, str | None]:
        if not self.raw_lines:
            return None, None
        start_idx = max(0, line_number - 1)
        end_line = end_line_number if end_line_number is not None else line_number
        end_idx = min(len(self.raw_lines), end_line)
        quarantine_line: str | None = None
        legacy_line: str | None = None
        for idx in range(start_idx, end_idx):
            lt = self.raw_lines[idx]
            if "ccba:quarantine" in lt:
                return lt, legacy_line
            if "ccba:allow-raw-bypass" in lt or "noqa: raw-bypass" in lt:
                legacy_line = lt
        return quarantine_line, legacy_line

    def _validate_quarantine_seam_and_reason(
        self,
        seam_id: str,
        reason: str,
        issue: str,
        root_mod: str,
        module_name: str,
        line_number: int,
    ) -> None:
        if ".." in seam_id or "/" in seam_id or "\\" in seam_id:
            self._add_violation(
                line_number,
                module_name,
                "QuarantineMarkerViolation",
                f"Quarantine seam_id '{seam_id}' contains invalid path characters.",
            )
        elif self.card_map and seam_id not in self.card_map:
            self._add_violation(
                line_number,
                module_name,
                "QuarantineMarkerViolation",
                f"Quarantine seam_id '{seam_id}' not found in seam-contracts.yaml.",
            )
        else:
            forbidden_list = self.card_map.get(seam_id, {}).get("forbidden_substitute_imports", [])
            if forbidden_list and root_mod not in forbidden_list:
                self._add_violation(
                    line_number,
                    module_name,
                    "QuarantineMarkerViolation",
                    f"Quarantine marker for seam '{seam_id}' does not govern forbidden module '{root_mod}'. Card governs: {forbidden_list}.",
                )
        if reason not in VALID_QUARANTINE_REASONS:
            self._add_violation(
                line_number,
                module_name,
                "QuarantineMarkerViolation",
                f"Invalid quarantine reason '{reason}'. Must be one of: {sorted(VALID_QUARANTINE_REASONS)}.",
            )
        if not ISSUE_URL_PATTERN.match(issue):
            self._add_violation(
                line_number,
                module_name,
                "QuarantineMarkerViolation",
                f"Invalid issue URL '{issue}'. Must match format 'https://github.com/vvChu/ccba-agent-platform/issues/<number>'.",
            )

    def _validate_quarantine_expiry_and_path(
        self, seam_id: str, until_str: str, issue: str, module_name: str, line_number: int
    ) -> None:
        try:
            until_date = datetime.strptime(until_str, "%Y-%m-%d").date()
            current_utc_date = datetime.now(timezone.utc).date()
            if until_date < current_utc_date:
                self._add_violation(
                    line_number,
                    module_name,
                    "QuarantineExpiredViolation",
                    f"Quarantine for seam '{seam_id}' expired on {until_str} (current UTC date: {current_utc_date}). Issue: {issue}.",
                )
        except ValueError:
            self._add_violation(
                line_number,
                module_name,
                "QuarantineMarkerViolation",
                f"Invalid date format in until='{until_str}'. Expected YYYY-MM-DD.",
            )
        if self.enforce_quarantine_path:
            is_q_path = (
                "adapters/quarantine" in self.current_file.as_posix()
                or "quarantine" in self.current_file.parts
            )
            if not is_q_path:
                self._add_violation(
                    line_number,
                    module_name,
                    "QuarantinePathViolation",
                    f"Quarantined import must reside in 'adapters/quarantine/<seam_id>.py'. Found in '{self.current_file}'.",
                )

    def _handle_quarantine_marker(
        self, quarantine_line: str, root_mod: str, module_name: str, line_number: int
    ) -> None:
        params = parse_quarantine_marker(quarantine_line) or {}
        missing = [f for f in ("seam_id", "reason", "until", "issue") if not params.get(f)]
        if missing:
            self._add_violation(
                line_number,
                module_name,
                "QuarantineMarkerViolation",
                f"Quarantine marker missing required field(s): {', '.join(missing)}. Required: seam_id=<id> reason=<reason> until=YYYY-MM-DD issue=<url>",
            )
            return
        seam_id, reason = params.get("seam_id", ""), params.get("reason", "")
        until_str, issue = params.get("until", ""), params.get("issue", "")
        self._validate_quarantine_seam_and_reason(
            seam_id, reason, issue, root_mod, module_name, line_number
        )
        self._validate_quarantine_expiry_and_path(
            seam_id, until_str, issue, module_name, line_number
        )
        if not any(
            v.line_number == line_number and v.file_path == self.current_file
            for v in self.violations
        ):
            self.active_quarantines.append(
                (self.current_file, line_number, root_mod, seam_id, until_str)
            )

    def _check_raw_bypass(
        self, root_mod: str, module_name: str, line_number: int, end_line_number: int | None
    ) -> None:
        restriction = self.restrictions[root_mod]
        if self.current_package in restriction.allowed_packages:
            return
        quarantine_line, legacy_line = self._find_exemption_markers(line_number, end_line_number)
        if quarantine_line is not None:
            self._handle_quarantine_marker(quarantine_line, root_mod, module_name, line_number)
        elif legacy_line is not None:
            if self.strict_quarantine:
                self._add_violation(
                    line_number,
                    module_name,
                    "LegacyBypassDeprecatedViolation",
                    f"File '{self.current_file.name}' uses legacy bypass '# ccba:allow-raw-bypass'. Under strict quarantine, must migrate to '# ccba:quarantine seam_id=... reason=... until=... issue=...' or use Seam.",
                )
            else:
                self.legacy_bypasses.append((self.current_file, line_number, root_mod))
        else:
            self._add_violation(
                line_number,
                module_name,
                "RawThirdPartyBypassViolation",
                f"File '{self.current_file.name}' cannot directly import raw '{root_mod}'. Platform-Aware KISS requires using '{restriction.seam_replacement}' seam instead.",
            )

    def _check_monorepo_boundaries(
        self, parts: list[str], root_mod: str, module_name: str, line_number: int
    ) -> None:
        if root_mod != self.current_package:
            for sub_part in parts[1:]:
                if sub_part.startswith("_") and not sub_part.startswith("__"):
                    self._add_violation(
                        line_number,
                        module_name,
                        "PrivateSubmoduleSeamViolation",
                        f"Package '{self.current_package or 'external'}' cannot import private submodule '{module_name}'. Must import from '{root_mod}' public seam.",
                    )
                    break
        if self.current_package in LEAF_FOUNDATION_PACKAGES:
            if root_mod in HIGHER_DOMAIN_PACKAGES:
                self._add_violation(
                    line_number,
                    module_name,
                    "FoundationLeafPurityViolation",
                    f"Foundation leaf package '{self.current_package}' is not allowed to import domain package '{root_mod}'.",
                )
            if root_mod in LEAF_FOUNDATION_PACKAGES and root_mod != self.current_package:
                self._add_violation(
                    line_number,
                    module_name,
                    "LeafIndependenceViolation",
                    f"Leaf package '{self.current_package}' cannot depend on sibling leaf '{root_mod}'.",
                )

    def _check_module_import(
        self, module_name: str, line_number: int, end_line_number: int | None = None
    ) -> None:
        parts = module_name.split(".")
        root_mod = parts[0]
        if root_mod in self.restrictions:
            self._check_raw_bypass(root_mod, module_name, line_number, end_line_number)
        if root_mod in MONOREPO_ROOT_MODULES:
            self._check_monorepo_boundaries(parts, root_mod, module_name, line_number)


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


def check_init_lazy_exports_parity(
    init_file: Path,
    mod_name: str = "",
) -> list[ImportViolation]:
    """Verify AST parity between __all__ and module-level _*_EXPORTS sets in __init__.py."""
    violations: list[ImportViolation] = []
    if not init_file.is_file():
        return violations
    label = mod_name or init_file.parent.name
    try:
        tree = ast.parse(init_file.read_text(encoding="utf-8"), filename=str(init_file))
    except Exception:
        return violations

    all_list: list[str] | None = None
    export_sets: list[tuple[str, int, list[str]]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                all_list = [
                    elt.value
                    for elt in node.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
            elif target.id.endswith("_EXPORTS"):
                vals = [
                    elt.value
                    for elt in ast.walk(node.value)
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
                export_sets.append((target.id, node.lineno, vals))

    if all_list is None:
        return violations
    all_set = set(all_list)
    for set_name, lineno, vals in export_sets:
        for sym in vals:
            if "." not in sym and sym not in all_set:
                violations.append(
                    ImportViolation(
                        init_file,
                        lineno,
                        label,
                        "OrphanLazyExportViolation",
                        f"Symbol '{sym}' in {set_name} is missing from {label}.__all__.",
                    )
                )
    return violations


def check_package_all_exports(
    packages_dir: Path,
    project_root: Path | None = None,
) -> list[ImportViolation]:
    """Verify every symbol declared in package __all__ is bound, non-duplicated, and synced with _*_EXPORTS."""
    import importlib

    violations: list[ImportViolation] = []
    if packages_dir.is_dir():
        for pkg_folder, mod_name in sorted(PACKAGE_MAP.items()):
            init_file = packages_dir / pkg_folder / "src" / mod_name / "__init__.py"
            if not init_file.is_file():
                continue
            violations.extend(check_init_lazy_exports_parity(init_file, mod_name))
            src_dir = str(packages_dir / pkg_folder / "src")
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            try:
                mod = importlib.import_module(mod_name)
            except Exception:
                continue
            exports = getattr(mod, "__all__", None)
            if not isinstance(exports, (list, tuple)):
                continue
            seen: set[str] = set()
            for sym in exports:
                if sym in seen:
                    violations.append(
                        ImportViolation(
                            init_file,
                            1,
                            mod_name,
                            "DuplicateAllExportViolation",
                            f"Duplicate symbol '{sym}' in {mod_name}.__all__.",
                        )
                    )
                seen.add(sym)
                if not hasattr(mod, sym):
                    violations.append(
                        ImportViolation(
                            init_file,
                            1,
                            mod_name,
                            "UnboundAllExportViolation",
                            f"Symbol '{sym}' in {mod_name}.__all__ is not bound at runtime.",
                        )
                    )

    root = project_root or packages_dir.parent
    tools_dir = root / "tools"
    if tools_dir.is_dir():
        for init_file in sorted(tools_dir.glob("*/__init__.py"), key=lambda p: p.as_posix()):
            violations.extend(
                check_init_lazy_exports_parity(init_file, f"tools.{init_file.parent.name}")
            )
    return violations


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

    candidates: list[Path] = []
    if packages_dir.is_dir():
        candidates.extend(
            p
            for p in sorted(packages_dir.glob("*/src/**/*.py"), key=lambda p: p.as_posix())
            if "__pycache__" not in p.parts
        )
    if include_scripts and (project_root / "scripts").is_dir():
        candidates.extend(
            p
            for p in sorted((project_root / "scripts").glob("**/*.py"), key=lambda p: p.as_posix())
            if not any(part in p.parts for part in ("__pycache__", "tests", "archive"))
        )

    for py_file in candidates:
        files_scanned += 1
        violations.extend(
            scan_file_for_violations(
                py_file,
                packages_dir,
                bypass_restrictions=bypass_restrictions,
                card_map=card_map,
                strict_quarantine=strict_quarantine,
                enforce_quarantine_path=enforce_quarantine_path,
                visitor_collector=all_visitors,
            )
        )
    violations.extend(check_package_all_exports(packages_dir, project_root=project_root))

    if audit_report is not None:
        audit_report["legacy_bypasses"] = [item for v in all_visitors for item in v.legacy_bypasses]
        audit_report["active_quarantines"] = [
            item for v in all_visitors for item in v.active_quarantines
        ]

    return len(violations) == 0, violations, files_scanned


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


def _print_quarantine_report(root: Path, audit_report: dict[str, Any]) -> None:
    """Display dry-run quarantine and legacy bypass report."""
    legacy = audit_report.get("legacy_bypasses", [])
    active_q = audit_report.get("active_quarantines", [])
    print("\n" + "=" * 60 + "\n📋 QUARANTINE DRY-RUN AUDIT REPORT\n" + "=" * 60)
    print(f"• Active Valid Quarantines: {len(active_q)}")
    for path, line_no, mod, s_id, until in active_q:
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        print(f"  - [QUARANTINE] {rel}:{line_no} -> module='{mod}' seam='{s_id}' until={until}")
    print(f"\n• Legacy Raw Bypasses ('# ccba:allow-raw-bypass'): {len(legacy)}")
    for path, line_no, mod in legacy:
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        print(f"  - [LEGACY] {rel}:{line_no} -> module='{mod}' (pending migration)")
    print("=" * 60)


def _print_violations_summary(root: Path, passed: bool, violations: list[ImportViolation]) -> None:
    """Print overall pass/fail status and list of violations."""
    if passed:
        print(
            "✅ Tất cả các gói Monorepo đều tuân thủ 100% ranh giới phụ thuộc và Seam invariants!"
        )
        return
    print(f"❌ Phát hiện {len(violations)} lỗi vi phạm hợp đồng kiến trúc:")
    for v in violations:
        rel_path = (
            v.file_path.relative_to(root) if v.file_path.is_relative_to(root) else v.file_path
        )
        print(f"  - [{v.rule_name}] {rel_path}:{v.line_number} -> {v.message}")


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
    print("=" * 60 + "\n🛡️  CCBA DEPENDENCY & SEAM CONTRACT LINTER\n" + "=" * 60)
    audit_report: dict[str, Any] = {}
    passed, violations, files_scanned = check_all_contracts(
        args.root,
        strict_quarantine=args.strict_quarantine,
        enforce_quarantine_path=args.enforce_quarantine_path,
        audit_report=audit_report,
    )
    print(f"📁 Scanned {files_scanned} Python source files in {time.time() - start_time:.3f}s.")
    if args.dry_run_quarantine:
        _print_quarantine_report(args.root, audit_report)
    _print_violations_summary(args.root, passed, violations)

    if args.with_import_linter:
        print("\n" + "-" * 60 + "\n🔍 Executing Industry-Standard import-linter:")
        il_code = run_import_linter_tool(args.root)
        if il_code != 0:
            return il_code

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
