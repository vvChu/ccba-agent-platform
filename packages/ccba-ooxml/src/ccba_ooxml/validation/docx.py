"""Validator for Word document XML files against XSD schemas."""

from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import lxml.etree

from ._parsed_package import ValidationDiagnostic, extract_error_line, make_diagnostic
from .base import BaseSchemaValidator, make_secure_xml_parser


def _truncate_repr(text: str, limit: int = 50) -> str:
    """Return a bounded repr preview of XML text content."""
    rendered = repr(text)
    return f"{rendered[:limit]}..." if len(rendered) > limit else rendered


def _parse_exception_diag(rel_path: str, exc: BaseException) -> ValidationDiagnostic:
    """Build a structured diagnostic from an XML parse or traversal exception."""
    return make_diagnostic(
        f"Error: {exc}",
        rel_path,
        extract_error_line(exc),
        f"  {rel_path}: Error: {exc}",
    )


class DOCXSchemaValidator(BaseSchemaValidator):
    """Validator for Word document XML files against XSD schemas."""

    WORD_2006_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    ELEMENT_RELATIONSHIP_TYPES: dict[str, str] = {}

    def validate(self) -> bool:
        """Run all validation checks and return True if all pass."""
        self.reset_diagnostics()
        if not self.validate_xml():
            return False

        checks = (
            self.validate_namespaces,
            self.validate_unique_ids,
            self.validate_file_references,
            self.validate_content_types,
            self.validate_against_xsd,
            self.validate_whitespace_preservation,
            self.validate_deletions,
            self.validate_insertions,
            self.validate_all_relationship_ids,
        )
        all_valid = True
        for check in checks:
            if not check():
                all_valid = False

        if self.verbose:
            self.compare_paragraph_counts()
        return all_valid

    def validate_whitespace_preservation(self) -> bool:
        """Validate that w:t elements with leading/trailing whitespace declare xml:space='preserve'."""
        diagnostics: list[ValidationDiagnostic] = []
        xml_space_attr = f"{{{self.XML_NAMESPACE}}}space"
        t_tag = f"{{{self.WORD_2006_NAMESPACE}}}t"

        for xml_file in self.xml_files:
            if xml_file.name != "document.xml":
                continue
            rel_path = self.parsed_package.rel_path_str(xml_file)
            try:
                root = self.parsed_package.get_root(xml_file)
                for elem in root.iter(t_tag):
                    text = elem.text
                    if not text or not (re.match(r"^\s.*", text) or re.match(r".*\s$", text)):
                        continue
                    if elem.attrib.get(xml_space_attr) != "preserve":
                        msg = f"w:t element with whitespace missing xml:space='preserve': {_truncate_repr(text)}"
                        diagnostics.append(make_diagnostic(msg, rel_path, elem.sourceline))
            except (lxml.etree.XMLSyntaxError, Exception) as exc:
                diagnostics.append(_parse_exception_diag(rel_path, exc))

        return self._emit_result(
            diagnostics,
            f"FAILED - Found {len(diagnostics)} whitespace preservation violations:",
            "PASSED - All whitespace is properly preserved",
        )

    def validate_deletions(self) -> bool:
        """Validate that w:t elements are not within w:del elements."""
        diagnostics: list[ValidationDiagnostic] = []
        namespaces = {"w": self.WORD_2006_NAMESPACE}

        for xml_file in self.xml_files:
            if xml_file.name != "document.xml":
                continue
            rel_path = self.parsed_package.rel_path_str(xml_file)
            try:
                root = self.parsed_package.get_root(xml_file)
                nodes: Any = root.xpath(".//w:del//w:t", namespaces=namespaces)
                if isinstance(nodes, list):
                    for t_elem in nodes:
                        if t_elem.text:
                            msg = f"<w:t> found within <w:del>: {_truncate_repr(t_elem.text)}"
                            diagnostics.append(make_diagnostic(msg, rel_path, t_elem.sourceline))
            except (lxml.etree.XMLSyntaxError, Exception) as exc:
                diagnostics.append(_parse_exception_diag(rel_path, exc))

        return self._emit_result(
            diagnostics,
            f"FAILED - Found {len(diagnostics)} deletion validation violations:",
            "PASSED - No w:t elements found within w:del elements",
        )

    def count_paragraphs_in_unpacked(self) -> int:
        """Count the number of paragraphs in the unpacked document."""
        count = 0
        p_tag = f".//{{{self.WORD_2006_NAMESPACE}}}p"
        for xml_file in self.xml_files:
            if xml_file.name != "document.xml":
                continue
            try:
                root = self.parsed_package.get_root(xml_file)
                count = len(root.findall(p_tag))
            except Exception as exc:
                if self.verbose:
                    print(f"Error counting paragraphs in unpacked document: {exc}")
        return count

    def count_paragraphs_in_original(self) -> int:
        """Count the number of paragraphs in the original docx file."""
        count = 0
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(self.original_file, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
                doc_xml_path = Path(temp_dir) / "word" / "document.xml"
                root = lxml.etree.parse(
                    str(doc_xml_path), parser=make_secure_xml_parser()
                ).getroot()
                count = len(root.findall(f".//{{{self.WORD_2006_NAMESPACE}}}p"))
        except Exception as exc:
            if self.verbose:
                print(f"Error counting paragraphs in original document: {exc}")
        return count

    def validate_insertions(self) -> bool:
        """Validate that w:delText elements are not within w:ins elements."""
        diagnostics: list[ValidationDiagnostic] = []
        namespaces = {"w": self.WORD_2006_NAMESPACE}

        for xml_file in self.xml_files:
            if xml_file.name != "document.xml":
                continue
            rel_path = self.parsed_package.rel_path_str(xml_file)
            try:
                root = self.parsed_package.get_root(xml_file)
                nodes: Any = root.xpath(
                    ".//w:ins//w:delText[not(ancestor::w:del)]", namespaces=namespaces
                )
                if isinstance(nodes, list):
                    for elem in nodes:
                        msg = f"<w:delText> within <w:ins>: {_truncate_repr(elem.text or '')}"
                        diagnostics.append(make_diagnostic(msg, rel_path, elem.sourceline))
            except (lxml.etree.XMLSyntaxError, Exception) as exc:
                diagnostics.append(_parse_exception_diag(rel_path, exc))

        return self._emit_result(
            diagnostics,
            f"FAILED - Found {len(diagnostics)} insertion validation violations:",
            "PASSED - No w:delText elements within w:ins elements",
        )

    def compare_paragraph_counts(self) -> None:
        """Compare paragraph counts between original and new document when verbose."""
        original_count = self.count_paragraphs_in_original()
        new_count = self.count_paragraphs_in_unpacked()
        diff = new_count - original_count
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        if self.verbose:
            print(f"\nParagraphs: {original_count} → {new_count} ({diff_str})")


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly.")
