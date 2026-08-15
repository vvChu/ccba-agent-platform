"""Constitution-Driven Cross-Reference Validator Engine.

Validates bi-directional links in cross_references.yaml against actual spec files
and governance constitution documents. Supports fuzzy match suggestions and auto-fix.
"""

import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CrossRefIssue:
    """Represents a validation issue found in cross_references.yaml."""

    severity: str  # "ERROR" or "WARNING"
    module_id: str
    message: str
    target_file: str = ""
    current_value: str = ""
    suggestion: str | None = None
    ref_index: int = -1
    ref_type: str = ""  # "governance" or "blueprint"
    field_name: str = ""


@dataclass
class CrossRefValidationReport:
    """Aggregated validation report for cross_references.yaml."""

    yaml_path: Path
    total_modules: int = 0
    total_references: int = 0
    errors: list[CrossRefIssue] = field(default_factory=list)
    warnings: list[CrossRefIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Returns True if there are zero errors."""
        return len(self.errors) == 0

    def print_summary(self) -> None:
        """Prints a human-readable summary of the validation report."""
        print("\n" + "=" * 60)
        print("🔍 CROSS-REFERENCE VALIDATION REPORT")
        print("=" * 60)
        print(f"Target File      : {self.yaml_path}")
        print(f"Modules Checked  : {self.total_modules}")
        print(f"References Total : {self.total_references}")
        print(f"Status           : {'✅ PASSED' if self.is_valid else '❌ FAILED'}")
        print(f"Errors           : {len(self.errors)}")
        print(f"Warnings         : {len(self.warnings)}")
        print("=" * 60)

        if self.errors:
            print("\n❌ ERRORS (Hard Blockers):")
            for idx, err in enumerate(self.errors, 1):
                print(f"  {idx}. [{err.module_id}] {err.message}")
                if err.target_file:
                    print(f"     File: {err.target_file}")

        if self.warnings:
            print("\n⚠️ WARNINGS & SUGGESTIONS:")
            for idx, warn in enumerate(self.warnings, 1):
                print(f"  {idx}. [{warn.module_id}] {warn.message}")
                if warn.suggestion:
                    print(
                        f"     💡 Gợi ý sửa: '{warn.suggestion}' (thay vì '{warn.current_value}')"
                    )
        print("=" * 60 + "\n")


def extract_markdown_headings(content_or_path: str | Path) -> list[str]:
    """Extracts raw markdown headings from markdown content or file path."""
    if isinstance(content_or_path, Path):
        if not content_or_path.exists():
            return []
        content = content_or_path.read_text(encoding="utf-8", errors="replace")
    else:
        content = content_or_path

    headings: list[str] = []
    # Match markdown headings: # Heading, ## Heading, ### Heading
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    for match in heading_pattern.finditer(content):
        heading_text = match.group(2).strip()
        # Remove any trailing anchor syntax or formatting tags
        heading_text = re.sub(r"\{#.*?\}", "", heading_text).strip()
        headings.append(heading_text)

    return headings


def find_closest_heading(
    target: str, available_headings: list[str], cutoff: float = 0.4
) -> str | None:
    """Finds the most similar heading using fuzzy matching (Levenshtein-based)."""
    if not available_headings or not target:
        return None
    matches = difflib.get_close_matches(target, available_headings, n=1, cutoff=cutoff)
    return matches[0] if matches else None


class CrossRefValidator:
    """Core validator for Constitution-Driven Cross-Reference Matrices."""

    def __init__(self, project_root: Path | str = ".") -> None:
        self.project_root = Path(project_root).resolve()

    def _resolve_constitution_file(self, doc_name: str) -> Path | None:
        """Finds the constitution document in standard directories."""
        candidates = [
            self.project_root / ".md" / "governance_constitution" / doc_name,
            self.project_root / ".md" / "system_blueprint" / doc_name,
            self.project_root / ".md" / doc_name,
            self.project_root / "docs" / doc_name,
        ]
        for path in candidates:
            if path.exists():
                return path
        return None

    def validate(self, yaml_path: Path | str) -> CrossRefValidationReport:
        """Validates cross_references.yaml structure, files, and headings."""
        yaml_file = Path(yaml_path)
        if not yaml_file.is_absolute():
            yaml_file = (self.project_root / yaml_file).resolve()

        report = CrossRefValidationReport(yaml_path=yaml_file)

        if not yaml_file.exists():
            report.errors.append(
                CrossRefIssue(
                    severity="ERROR",
                    module_id="ROOT",
                    message=f"Tệp tin không tồn tại: {yaml_file}",
                    target_file=str(yaml_file),
                )
            )
            return report

        try:
            data: dict[str, Any] = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        except Exception as e:
            report.errors.append(
                CrossRefIssue(
                    severity="ERROR",
                    module_id="ROOT",
                    message=f"Lỗi cú pháp YAML: {e}",
                    target_file=str(yaml_file),
                )
            )
            return report

        modules = data.get("modules", [])
        report.total_modules = len(modules)

        for mod in modules:
            mod_id = mod.get("module_id", "unknown_module")
            spec_rel_path = mod.get("spec_file", "")
            spec_file_path = self.project_root / spec_rel_path

            # 1. Check spec file existence
            if not spec_rel_path or not spec_file_path.exists():
                report.errors.append(
                    CrossRefIssue(
                        severity="ERROR",
                        module_id=mod_id,
                        message=f"Không tìm thấy tệp spec: '{spec_rel_path}'",
                        target_file=str(spec_file_path),
                    )
                )
                spec_headings: list[str] = []
            else:
                spec_headings = extract_markdown_headings(spec_file_path)

            # 2. Check governance constitution references
            gov_refs = mod.get("governance_constitution_references", [])
            report.total_references += len(gov_refs)

            for idx, ref in enumerate(gov_refs):
                doc_name = ref.get("document", "")
                section_ctx = ref.get("section_context", "")

                doc_path = self._resolve_constitution_file(doc_name)
                if not doc_path:
                    report.errors.append(
                        CrossRefIssue(
                            severity="ERROR",
                            module_id=mod_id,
                            message=f"Không tìm thấy tệp quy chế thể chế: '{doc_name}'",
                            target_file=doc_name,
                            ref_index=idx,
                            ref_type="governance",
                        )
                    )
                else:
                    # Check section_context in spec headings if applicable
                    if section_ctx and spec_headings and section_ctx not in spec_headings:
                        closest = find_closest_heading(section_ctx, spec_headings)
                        report.warnings.append(
                            CrossRefIssue(
                                severity="WARNING",
                                module_id=mod_id,
                                message=f"Tiêu đề mục '{section_ctx}' không khớp chính xác trong spec.md",
                                target_file=str(spec_file_path),
                                current_value=section_ctx,
                                suggestion=closest,
                                ref_index=idx,
                                ref_type="governance",
                                field_name="section_context",
                            )
                        )

            # 3. Check system blueprint references
            bp_refs = mod.get("system_blueprint_references", [])
            report.total_references += len(bp_refs)

            for idx, ref in enumerate(bp_refs):
                doc_name = ref.get("document", "")
                doc_path = self._resolve_constitution_file(doc_name)
                if not doc_path:
                    report.errors.append(
                        CrossRefIssue(
                            severity="ERROR",
                            module_id=mod_id,
                            message=f"Không tìm thấy tệp system blueprint: '{doc_name}'",
                            target_file=doc_name,
                            ref_index=idx,
                            ref_type="blueprint",
                        )
                    )

        return report

    def apply_fixes(self, yaml_path: Path | str, report: CrossRefValidationReport) -> bool:
        """Applies auto-suggestions to cross_references.yaml."""
        yaml_file = Path(yaml_path)
        if not yaml_file.is_absolute():
            yaml_file = (self.project_root / yaml_file).resolve()

        if not yaml_file.exists():
            return False

        data: dict[str, Any] = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        modules = data.get("modules", [])

        applied_fixes = 0
        for warn in report.warnings:
            if warn.suggestion and warn.ref_index >= 0:
                # Find matching module
                for mod in modules:
                    if mod.get("module_id") == warn.module_id:
                        ref_list_key = (
                            "governance_constitution_references"
                            if warn.ref_type == "governance"
                            else "system_blueprint_references"
                        )
                        ref_list = mod.get(ref_list_key, [])
                        if 0 <= warn.ref_index < len(ref_list):
                            ref_item = ref_list[warn.ref_index]
                            if ref_item.get(warn.field_name) == warn.current_value:
                                ref_item[warn.field_name] = warn.suggestion
                                applied_fixes += 1

        if applied_fixes > 0:
            yaml_file.write_text(
                yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            print(f"✨ Đã tự động vá {applied_fixes} liên kết trong {yaml_file.name}!")
            return True
        return False


def validate_cross_references(
    yaml_path: Path | str,
    project_root: Path | str = ".",
    warn_only: bool = False,
    auto_fix: bool = False,
) -> int:
    """Procedural seam to validate cross references with exit code."""
    validator = CrossRefValidator(project_root)
    report = validator.validate(yaml_path)
    report.print_summary()

    if auto_fix and report.warnings:
        validator.apply_fixes(yaml_path, report)
        # Re-validate after fixing
        report = validator.validate(yaml_path)

    if not report.is_valid:
        if warn_only:
            print(
                "⚠️ [WARN-ONLY] Phát hiện lỗi nhưng không chặn tiến trình do cờ --warn-only được bật."
            )
            return 0
        print("❌ [HARD-GATE] Chặn tiến trình do phát hiện lỗi liên kết gãy!")
        return 1

    return 0
