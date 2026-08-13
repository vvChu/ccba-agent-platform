from dataclasses import dataclass, field
from pathlib import Path

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
    """Unified deep validation interface for Office Open XML files.

    This class wraps individual format-specific validators and exposes
    a single, clean entry point for client code.
    """

    def __init__(self, unpacked_dir, original_file, verbose=False):
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file).resolve()
        self.verbose = verbose

    def validate_report(self) -> ValidationReport:
        """Run all applicable validators and return a structured report.

        Returns:
            ValidationReport containing is_valid status and detailed issues.
        """
        file_extension = self.original_file.suffix.lower()

        match file_extension:
            case ".docx":
                validator_classes = [DOCXSchemaValidator, RedliningValidator]
            case ".pptx":
                validator_classes = [PPTXSchemaValidator]
            case _:
                issue = ValidationIssue(
                    message=f"Validation not supported for file type {file_extension}",
                    severity="ERROR",
                )
                return ValidationReport(is_valid=False, issues=[issue], validators_run=[])

        is_valid = True
        issues: list[ValidationIssue] = []
        validators_run: list[str] = []

        for V in validator_classes:
            validator_name = V.__name__
            validators_run.append(validator_name)
            validator = V(self.unpacked_dir, self.original_file, verbose=self.verbose)
            passed = validator.validate()

            if not passed:
                is_valid = False
                issues.append(
                    ValidationIssue(
                        message=f"{validator_name} failed validation",
                        severity="ERROR",
                        file_path=str(self.original_file),
                    )
                )

        return ValidationReport(is_valid=is_valid, issues=issues, validators_run=validators_run)

    def validate(self) -> bool:
        """Run all applicable validators based on file extension.

        Returns:
            bool: True if all validations passed, False otherwise.
        """
        report = self.validate_report()
        return report.is_valid
