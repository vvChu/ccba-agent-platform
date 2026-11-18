"""Base validator facade delegating parsing, relationship checks, and XSD engines."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Any

import lxml.etree

from ._parsed_package import (
    ParsedOOXMLPackage,
    ValidationDiagnostic,
    _make_secure_xml_parser,
    check_content_types,
    check_namespaces,
    check_xml_wellformed,
    make_secure_xml_parser,
)
from ._relationship_checks import (
    CONTENT_TYPES_NAMESPACE,
    MC_NAMESPACE,
    OFFICE_RELATIONSHIPS_NAMESPACE,
    PACKAGE_RELATIONSHIPS_NAMESPACE,
    UNIQUE_ID_REQUIREMENTS,
    XML_NAMESPACE,
    check_all_relationship_ids,
    check_file_references,
    check_unique_ids,
    expected_relationship_type,
)
from ._xsd_engine import (
    COMPILED_SCHEMA_CACHE,
    MAIN_CONTENT_FOLDERS,
    OOXML_NAMESPACES,
    SCHEMA_MAPPINGS,
    OfflineSchemaResolver,
    clean_ignorable_namespaces,
    get_compiled_schema,
    preprocess_mc_ignorable,
    remove_ignorable_elements,
    remove_template_tags_from_text_nodes,
    resolve_schema_path,
    validate_single_file_xsd,
)


class BaseSchemaValidator:
    """Base validator facade with common OOXML structural and XSD checks."""

    _COMPILED_SCHEMA_CACHE = COMPILED_SCHEMA_CACHE
    UNIQUE_ID_REQUIREMENTS = UNIQUE_ID_REQUIREMENTS
    ELEMENT_RELATIONSHIP_TYPES: dict[str, str] = {}
    SCHEMA_MAPPINGS = SCHEMA_MAPPINGS
    MC_NAMESPACE = MC_NAMESPACE
    XML_NAMESPACE = XML_NAMESPACE
    PACKAGE_RELATIONSHIPS_NAMESPACE = PACKAGE_RELATIONSHIPS_NAMESPACE
    OFFICE_RELATIONSHIPS_NAMESPACE = OFFICE_RELATIONSHIPS_NAMESPACE
    CONTENT_TYPES_NAMESPACE = CONTENT_TYPES_NAMESPACE
    MAIN_CONTENT_FOLDERS = MAIN_CONTENT_FOLDERS
    OOXML_NAMESPACES = OOXML_NAMESPACES

    @classmethod
    def get_compiled_schema(cls, schema_path: Path, schemas_dir: Path) -> lxml.etree.XMLSchema:
        """Load and compile an XMLSchema with offline resolution and caching."""
        return get_compiled_schema(schema_path, schemas_dir, cache=cls._COMPILED_SCHEMA_CACHE)

    def __init__(
        self,
        unpacked_dir: str | Path,
        original_file: str | Path,
        verbose: bool = False,
        parsed_package: ParsedOOXMLPackage | None = None,
    ) -> None:
        """Initialize schema validator with shared or newly created ``ParsedOOXMLPackage``."""
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file)
        self.verbose = verbose

        pkg_schemas = Path(__file__).parent.parent / "schemas"
        self.schemas_dir = (
            pkg_schemas if pkg_schemas.exists() else Path(__file__).parent.parent.parent / "schemas"
        )
        self.parsed_package = parsed_package or ParsedOOXMLPackage(self.unpacked_dir)
        self.xml_files = list(self.parsed_package.xml_files)
        self.last_diagnostics: list[ValidationDiagnostic] = []

        if not self.xml_files:
            print(f"Warning: No XML files found in {self.unpacked_dir}")

    def validate(self) -> bool:
        """Run all validation checks and return True if all pass."""
        raise NotImplementedError("Subclasses must implement the validate method")

    def _emit_result(
        self,
        diagnostics: list[ValidationDiagnostic],
        fail_header: str,
        pass_msg: str,
        extra_footer: str | None = None,
    ) -> bool:
        """Store diagnostics, emit console output per legacy behavior, and return bool."""
        self.last_diagnostics = list(diagnostics)
        if diagnostics:
            print(fail_header)
            for diag in diagnostics:
                print(diag.legacy_line or f"  {diag.message}")
            if extra_footer:
                print(extra_footer)
            return False
        if self.verbose:
            print(pass_msg)
        return True

    def validate_xml(self) -> bool:
        """Validate that all XML files are well-formed."""
        diags = check_xml_wellformed(self.parsed_package)
        return self._emit_result(
            diags,
            f"FAILED - Found {len(diags)} XML violations:",
            "PASSED - All XML files are well-formed",
        )

    def validate_namespaces(self) -> bool:
        """Validate that namespace prefixes in Ignorable attributes are declared."""
        diags = check_namespaces(self.parsed_package)
        return self._emit_result(
            diags,
            f"FAILED - {len(diags)} namespace issues:",
            "PASSED - All namespace prefixes properly declared",
        )

    def validate_unique_ids(self) -> bool:
        """Validate that specific IDs are unique according to OOXML requirements."""
        diags = check_unique_ids(
            self.parsed_package, self.MC_NAMESPACE, self.UNIQUE_ID_REQUIREMENTS
        )
        return self._emit_result(
            diags,
            f"FAILED - Found {len(diags)} ID uniqueness violations:",
            "PASSED - All required IDs are unique",
        )

    def validate_file_references(self) -> bool:
        """Validate that all .rels files reference existing files and no files are orphaned."""
        has_rels, diags = check_file_references(
            self.parsed_package, self.PACKAGE_RELATIONSHIPS_NAMESPACE
        )
        if not has_rels:
            self.last_diagnostics = []
            if self.verbose:
                print("PASSED - No .rels files found")
            return True
        if self.verbose:
            target_count = len(
                [
                    f
                    for f in self.parsed_package.all_files
                    if f.name != "[Content_Types].xml" and not f.name.endswith(".rels")
                ]
            )
            print(
                f"Found {len(self.parsed_package.rels_files)} .rels files and {target_count} target files"
            )
        footer = (
            "CRITICAL: These errors will cause the document to appear corrupt. "
            "Broken references MUST be fixed, and unreferenced files MUST be referenced or removed."
        )
        return self._emit_result(
            diags,
            f"FAILED - Found {len(diags)} relationship validation errors:",
            "PASSED - All references are valid and all files are properly referenced",
            extra_footer=footer,
        )

    def validate_all_relationship_ids(self) -> bool:
        """Validate that all ``r:id`` attributes reference existing IDs in ``.rels``."""
        diags = check_all_relationship_ids(
            self.parsed_package,
            self.PACKAGE_RELATIONSHIPS_NAMESPACE,
            self.OFFICE_RELATIONSHIPS_NAMESPACE,
            self.ELEMENT_RELATIONSHIP_TYPES,
        )
        return self._emit_result(
            diags,
            f"FAILED - Found {len(diags)} relationship ID reference errors:",
            "PASSED - All relationship ID references are valid",
            extra_footer="\nThese ID mismatches will cause the document to appear corrupt!",
        )

    def _get_expected_relationship_type(self, element_name: str) -> str | None:
        """Return expected relationship type for ``element_name``."""
        return expected_relationship_type(element_name, self.ELEMENT_RELATIONSHIP_TYPES)

    def validate_content_types(self) -> bool:
        """Validate that all content files are declared in [Content_Types].xml."""
        exists, diags = check_content_types(self.parsed_package, self.CONTENT_TYPES_NAMESPACE)
        if not exists:
            self.last_diagnostics = [
                ValidationDiagnostic(
                    message="[Content_Types].xml file not found",
                    file_path="[Content_Types].xml",
                )
            ]
            print("FAILED - [Content_Types].xml file not found")
            return False
        return self._emit_result(
            diags,
            f"FAILED - Found {len(diags)} content type declaration errors:",
            "PASSED - All content files are properly declared in [Content_Types].xml",
        )

    def validate_file_against_xsd(
        self, xml_file: str | Path, verbose: bool = False
    ) -> tuple[bool | None, set[str]]:
        """Validate a single XML file against XSD schema, comparing with original."""
        resolved_xml = Path(xml_file).resolve()
        is_valid, current_errors = self._validate_single_file_xsd(resolved_xml, self.unpacked_dir)
        if is_valid is None:
            return None, set()
        if is_valid:
            return True, set()

        original_errors = self._get_original_file_errors(resolved_xml)
        assert current_errors is not None
        new_errors = current_errors - original_errors
        if new_errors:
            if verbose:
                rel_path = resolved_xml.relative_to(self.unpacked_dir)
                print(f"FAILED - {rel_path}: {len(new_errors)} new error(s)")
                for error in list(new_errors)[:3]:
                    print(f"  - {error[:250] + '...' if len(error) > 250 else error}")
            return False, new_errors
        if verbose:
            print(f"PASSED - No new errors (original had {len(current_errors)} errors)")
        return True, set()

    def validate_against_xsd(self) -> bool:
        """Validate all unpacked XML files against XSD schemas."""
        error_lines: list[str] = []
        diags: list[ValidationDiagnostic] = []
        counts = {"valid": 0, "skipped": 0, "original": 0}
        for xml_file in self.xml_files:
            rel_path = self.parsed_package.rel_path_str(xml_file)
            is_valid, new_errs = self.validate_file_against_xsd(xml_file, verbose=False)
            if is_valid is None:
                counts["skipped"] += 1
            elif is_valid:
                counts["valid"] += 1
                counts["original"] += 1 if new_errs else 0
            else:
                error_lines.append(f"  {rel_path}: {len(new_errs)} new error(s)")
                for err in sorted(new_errs)[:3]:
                    trunc = f"{err[:250]}..." if len(err) > 250 else err
                    error_lines.append(f"    - {trunc}")
                    diags.append(
                        ValidationDiagnostic(
                            message=err, file_path=rel_path, legacy_line=f"    - {trunc}"
                        )
                    )
        if self.verbose:
            self._print_xsd_summary(counts, error_lines)
        self.last_diagnostics = diags
        if error_lines:
            print("\nFAILED - Found NEW validation errors:")
            for line in error_lines:
                print(line)
            return False
        if self.verbose:
            print("\nPASSED - No new XSD validation errors introduced")
        return True

    def _print_xsd_summary(self, counts: dict[str, int], error_lines: list[str]) -> None:
        """Print verbose XSD validation counts."""
        print(f"Validated {len(self.xml_files)} files:")
        print(f"  - Valid: {counts['valid']}")
        print(f"  - Skipped (no schema): {counts['skipped']}")
        if counts["original"]:
            print(f"  - With original errors (ignored): {counts['original']}")
        new_count = len([ln for ln in error_lines if not ln.startswith("    ")])
        print(f"  - With NEW errors: {new_count}")

    def _get_schema_path(self, xml_file: Path) -> Path | None:
        """Determine the appropriate schema path for an XML file."""
        return resolve_schema_path(
            xml_file, self.schemas_dir, self.SCHEMA_MAPPINGS, self.MAIN_CONTENT_FOLDERS
        )

    def _clean_ignorable_namespaces(self, xml_doc: Any) -> Any:
        """Remove attributes and elements not in allowed namespaces on a cloned tree."""
        return clean_ignorable_namespaces(xml_doc, self.OOXML_NAMESPACES)

    def _remove_ignorable_elements(self, root: Any) -> None:
        """Recursively remove all elements not in allowed namespaces."""
        remove_ignorable_elements(root, self.OOXML_NAMESPACES)

    def _preprocess_for_mc_ignorable(self, xml_doc: Any) -> Any:
        """Preprocess XML to remove ``mc:Ignorable`` attribute before validation."""
        return preprocess_mc_ignorable(xml_doc, mc_ns=self.MC_NAMESPACE)

    def _validate_single_file_xsd(
        self, xml_file: Path, base_path: Path
    ) -> tuple[bool | None, set[str] | None]:
        """Validate a single XML file against XSD schema."""
        schema_path = self._get_schema_path(Path(xml_file))
        if not schema_path:
            return None, None
        schema = self.get_compiled_schema(schema_path, self.schemas_dir)
        return validate_single_file_xsd(
            Path(xml_file),
            Path(base_path),
            schema,
            self.parsed_package,
            self.OOXML_NAMESPACES,
            self.MAIN_CONTENT_FOLDERS,
            mc_ns=self.MC_NAMESPACE,
        )

    def _get_original_file_errors(self, xml_file: Path) -> set[str]:
        """Get XSD validation errors from a single file inside ``self.original_file``."""
        resolved_xml = Path(xml_file).resolve()
        relative_path = resolved_xml.relative_to(self.unpacked_dir)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(self.original_file, "r") as zip_ref:
                zip_ref.extractall(temp_path)
            original_xml_file = temp_path / relative_path
            if not original_xml_file.exists():
                return set()
            _, errors = self._validate_single_file_xsd(original_xml_file, temp_path)
            return errors if errors else set()

    def _remove_template_tags_from_text_nodes(self, xml_doc: Any) -> tuple[Any, list[str]]:
        """Remove template tags from XML text nodes on a clone and collect warnings."""
        return remove_template_tags_from_text_nodes(xml_doc)


__all__ = [
    "BaseSchemaValidator",
    "OfflineSchemaResolver",
    "ParsedOOXMLPackage",
    "ValidationDiagnostic",
    "_make_secure_xml_parser",
    "make_secure_xml_parser",
]
