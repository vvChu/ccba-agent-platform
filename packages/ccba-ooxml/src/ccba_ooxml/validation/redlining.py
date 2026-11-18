"""Validator for tracked changes in Word documents using shared lxml cache."""

from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path

import lxml.etree

from ._parsed_package import (
    ParsedOOXMLPackage,
    ValidationDiagnostic,
    extract_error_line,
    make_diagnostic,
    make_secure_xml_parser,
)

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class RedliningValidator:
    """Validator for tracked changes in Word documents."""

    def __init__(
        self,
        unpacked_dir: str | Path,
        original_docx: str | Path,
        verbose: bool = False,
        parsed_package: ParsedOOXMLPackage | None = None,
    ) -> None:
        """Initialize validator using a shared or fresh ``ParsedOOXMLPackage``."""
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_docx = Path(original_docx)
        self.verbose = verbose
        self.namespaces = {"w": WORD_NS}
        self.parsed_package = parsed_package or ParsedOOXMLPackage(self.unpacked_dir)
        self.collected_diagnostics: list[ValidationDiagnostic] = []

    def _fail(
        self,
        message: str,
        file_path: str | None = "word/document.xml",
        line_number: int | None = None,
    ) -> bool:
        """Record structured failure diagnostic and print only if verbose."""
        self.collected_diagnostics.append(
            make_diagnostic(message, file_path=file_path, line_number=line_number)
        )
        if self.verbose:
            print(message)
        return False

    def _has_claude_tracked_changes(self) -> bool | None:
        """Return True if Claude changes exist, False if none, None if invalid XML."""
        entry = self.parsed_package.get_entry("word/document.xml")
        if entry.parse_error is not None or entry.root is None:
            err_msg, line_num = entry.parse_error or ("Failed to parse XML", None)
            self._fail(
                f"FAILED - Error parsing XML files: {err_msg}",
                file_path=entry.rel_path,
                line_number=line_num,
            )
            return None

        author_attr = f"{{{WORD_NS}}}author"
        has_del = any(
            elem.get(author_attr) == "Claude"
            for elem in entry.root.findall(".//w:del", self.namespaces)
        )
        has_ins = any(
            elem.get(author_attr) == "Claude"
            for elem in entry.root.findall(".//w:ins", self.namespaces)
        )
        return has_del or has_ins

    def validate(self) -> bool:
        """Validate that Claude's tracked changes preserve non-redlined document text."""
        self.collected_diagnostics.clear()
        modified_file = self.unpacked_dir / "word" / "document.xml"
        if not modified_file.exists():
            return self._fail(f"FAILED - Modified document.xml not found at {modified_file}")

        has_changes = self._has_claude_tracked_changes()
        if has_changes is None:
            return False
        if not has_changes:
            if self.verbose:
                print("PASSED - No tracked changes by Claude found.")
            return True

        return self._validate_against_original()

    def _validate_against_original(self) -> bool:
        """Compare text with original docx after stripping Claude's tracked changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            try:
                with zipfile.ZipFile(self.original_docx, "r") as zip_ref:
                    zip_ref.extractall(temp_path)
            except Exception as exc:
                return self._fail(f"FAILED - Error unpacking original docx: {exc}", file_path=None)

            original_file = temp_path / "word" / "document.xml"
            if not original_file.exists():
                return self._fail(
                    f"FAILED - Original document.xml not found in {self.original_docx}"
                )

            try:
                modified_root = self.parsed_package.clone_root("word/document.xml")
                original_tree = lxml.etree.parse(
                    str(original_file), parser=make_secure_xml_parser()
                )
                original_root = original_tree.getroot()
            except (lxml.etree.XMLSyntaxError, Exception) as exc:
                return self._fail(
                    f"FAILED - Error parsing XML files: {exc}",
                    file_path="word/document.xml",
                    line_number=extract_error_line(exc),
                )

            self._remove_claude_tracked_changes(original_root)
            self._remove_claude_tracked_changes(modified_root)

            modified_text = self._extract_text_content(modified_root)
            original_text = self._extract_text_content(original_root)
            if modified_text != original_text:
                return self._fail(self._generate_detailed_diff(original_text, modified_text))

            if self.verbose:
                print("PASSED - All changes by Claude are properly tracked")
            return True

    def _generate_detailed_diff(self, original_text: str, modified_text: str) -> str:
        """Generate detailed word-level differences using git word diff."""
        error_parts = [
            "FAILED - Document text doesn't match after removing Claude's tracked changes",
            "",
            "Likely causes:",
            "  1. Modified text inside another author's <w:ins> or <w:del> tags",
            "  2. Made edits without proper tracked changes",
            "  3. Didn't nest <w:del> inside <w:ins> when deleting another's insertion",
            "",
            "For pre-redlined documents, use correct patterns:",
            "  - To reject another's INSERTION: Nest <w:del> inside their <w:ins>",
            "  - To restore another's DELETION: Add new <w:ins> AFTER their <w:del>",
            "",
        ]
        git_diff = self._get_git_word_diff(original_text, modified_text)
        if git_diff:
            error_parts.extend(["Differences:", "============", git_diff])
        else:
            error_parts.append("Unable to generate word diff (git not available)")
        return "\n".join(error_parts)

    def _run_word_diff(self, args: list[str]) -> str | None:
        """Execute git diff --no-index and return content lines past hunk headers."""
        result = subprocess.run(args, capture_output=True, text=True)
        if not result.stdout.strip():
            return None
        content_lines: list[str] = []
        in_content = False
        for line in result.stdout.split("\n"):
            if line.startswith("@@"):
                in_content = True
                continue
            if in_content and line.strip():
                content_lines.append(line)
        return "\n".join(content_lines) if content_lines else None

    def _get_git_word_diff(self, original_text: str, modified_text: str) -> str | None:
        """Generate word diff using git with character-level precision."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                orig_txt = temp_path / "original.txt"
                mod_txt = temp_path / "modified.txt"
                orig_txt.write_text(original_text, encoding="utf-8")
                mod_txt.write_text(modified_text, encoding="utf-8")

                char_cmd = [
                    "git",
                    "diff",
                    "--word-diff=plain",
                    "--word-diff-regex=.",
                    "-U0",
                    "--no-index",
                    str(orig_txt),
                    str(mod_txt),
                ]
                diff = self._run_word_diff(char_cmd)
                if diff:
                    return diff
                word_cmd = [
                    "git",
                    "diff",
                    "--word-diff=plain",
                    "-U0",
                    "--no-index",
                    str(orig_txt),
                    str(mod_txt),
                ]
                return self._run_word_diff(word_cmd)
        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            return None

    def _remove_claude_tracked_changes(self, root: lxml.etree._Element) -> None:
        """Remove tracked changes authored by Claude from a cloned XML root."""
        ins_tag = f"{{{WORD_NS}}}ins"
        del_tag = f"{{{WORD_NS}}}del"
        author_attr = f"{{{WORD_NS}}}author"
        deltext_tag = f"{{{WORD_NS}}}delText"
        t_tag = f"{{{WORD_NS}}}t"

        for parent in root.iter():
            if not isinstance(parent.tag, str):
                continue
            for child in list(parent):
                if (
                    isinstance(child.tag, str)
                    and child.tag == ins_tag
                    and child.get(author_attr) == "Claude"
                ):
                    parent.remove(child)

        for parent in root.iter():
            if not isinstance(parent.tag, str):
                continue
            to_unwrap = [
                (child, idx)
                for idx, child in enumerate(list(parent))
                if isinstance(child.tag, str)
                and child.tag == del_tag
                and child.get(author_attr) == "Claude"
            ]
            for del_elem, del_index in reversed(to_unwrap):
                for elem in del_elem.iter():
                    if isinstance(elem.tag, str) and elem.tag == deltext_tag:
                        elem.tag = t_tag
                for child in reversed(list(del_elem)):
                    parent.insert(del_index, child)
                parent.remove(del_elem)

    def _extract_text_content(self, root: lxml.etree._Element) -> str:
        """Extract non-empty paragraph text from Word XML."""
        p_tag = f"{{{WORD_NS}}}p"
        t_tag = f"{{{WORD_NS}}}t"
        paragraphs: list[str] = []
        for p_elem in root.findall(f".//{p_tag}"):
            parts = [t_elem.text for t_elem in p_elem.findall(f".//{t_tag}") if t_elem.text]
            paragraph_text = "".join(parts)
            if paragraph_text:
                paragraphs.append(paragraph_text)
        return "\n".join(paragraphs)


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly.")
