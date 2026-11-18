"""Unified deep validation facade for OOXML documents (.docx and .pptx)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._parsed_package import ParsedOOXMLPackage
from .docx import DOCXSchemaValidator
from .pptx import PPTXSchemaValidator
from .redlining import RedliningValidator


@dataclass
class ValidationIssue:
    """Represents a single validation issue found during OOXML schema check."""

    message: str
    severity: str = "ERROR"  # ERROR, WARNING, INFO
    file_path: str | None = None
    line_number: int | None = None


@dataclass
class ValidationReport:
    """Detailed report containing all issues discovered during validation."""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    validators_run: list[str] = field(default_factory=list)


class OOXMLValidator:
    """Unified deep validation interface for Office Open XML files."""

    def __init__(
        self, unpacked_dir: str | Path, original_file: str | Path, verbose: bool = False
    ) -> None:
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file).resolve()
        self.verbose = verbose

    def _instantiate_validators(
        self, file_extension: str
    ) -> tuple[list[Any], ParsedOOXMLPackage | None]:
        """Instantiate format-specific validators sharing one cache for DOCX."""
        match file_extension:
            case ".docx":
                shared_pkg = ParsedOOXMLPackage(self.unpacked_dir)
                return [
                    DOCXSchemaValidator(
                        self.unpacked_dir,
                        self.original_file,
                        verbose=self.verbose,
                        parsed_package=shared_pkg,
                    ),
                    RedliningValidator(
                        self.unpacked_dir,
                        self.original_file,
                        verbose=self.verbose,
                        parsed_package=shared_pkg,
                    ),
                ], shared_pkg
            case ".pptx":
                return [
                    PPTXSchemaValidator(self.unpacked_dir, self.original_file, verbose=self.verbose)
                ], None
            case _:
                return [], None

    def validate_report(self) -> ValidationReport:
        """Run all applicable validators and return a structured report."""
        file_extension = self.original_file.suffix.lower()
        validators, _ = self._instantiate_validators(file_extension)
        if not validators:
            issue = ValidationIssue(
                message=f"Validation not supported for file type {file_extension}",
                severity="ERROR",
            )
            return ValidationReport(is_valid=False, issues=[issue], validators_run=[])

        is_valid = True
        issues: list[ValidationIssue] = []
        seen_keys: set[tuple[str, str | None, int | None, str]] = set()
        validators_run: list[str] = []

        for validator in validators:
            validator_name = type(validator).__name__
            validators_run.append(validator_name)
            passed = validator.validate()
            if passed:
                continue
            is_valid = False
            diags = list(getattr(validator, "collected_diagnostics", []))
            if not diags:
                diags_issues = [
                    ValidationIssue(
                        message=f"{validator_name} failed validation",
                        severity="ERROR",
                        file_path=str(self.original_file),
                    )
                ]
            else:
                diags_issues = [
                    ValidationIssue(
                        message=d.message,
                        severity=d.severity,
                        file_path=d.file_path,
                        line_number=d.line_number,
                    )
                    for d in diags
                ]
            for issue in diags_issues:
                key = (issue.severity, issue.file_path, issue.line_number, issue.message)
                if key not in seen_keys:
                    seen_keys.add(key)
                    issues.append(issue)

        return ValidationReport(is_valid=is_valid, issues=issues, validators_run=validators_run)

    def validate(self) -> bool:
        """Run all applicable validators based on file extension."""
        return self.validate_report().is_valid
