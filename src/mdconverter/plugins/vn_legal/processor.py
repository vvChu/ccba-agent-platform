"""
Vietnamese Legal Document Processor.

Post-processing rules specifically for Vietnamese legal documents.
"""

import re


class VNLegalProcessor:
    """Post-processor for Vietnamese legal documents."""

    def __init__(self) -> None:
        """Initialize processor with rule counters."""
        self.fixes: dict[str, int] = {}

    def process(self, content: str) -> str:
        """
        Apply all Vietnamese legal document processing rules.

        Args:
            content: Raw Markdown content.

        Returns:
            Processed Markdown content.
        """
        self.fixes = {}

        # Apply rules in order
        content = self._remove_page_numbers(content)
        content = self._remove_bullet_from_intro(content)
        content = self._fix_definition_lists(content)
        content = self._fix_bold_header_spacing(content)
        content = self._normalize_list_markers(content)
        content = self._fix_emphasis_style(content)
        content = self._fix_multiple_blanks(content)
        content = self._ensure_trailing_newline(content)

        return content

    def _remove_page_numbers(self, content: str) -> str:
        """Remove standalone page numbers from PDF conversion artifacts."""
        # Match lines that contain only a number (1-999) possibly with whitespace
        pattern = r"^\s*(\d{1,3})\s*$"

        lines = content.split("\n")
        cleaned_lines = []
        removed_count = 0

        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                page_num = int(match.group(1))
                # Only remove if it's a reasonable page number (1-200)
                # and is surrounded by content (not part of a numbered list)
                if 1 <= page_num <= 200:
                    # Check context: previous and next lines should have content
                    prev_line = lines[i-1].strip() if i > 0 else ""
                    _next_line = lines[i+1].strip() if i < len(lines)-1 else ""  # noqa: F841

                    # If previous line ends with punctuation or is blank, likely page number
                    if not prev_line or prev_line.endswith(('.', ':', ';', '…', ',')):
                        removed_count += 1
                        continue  # Skip this line

            cleaned_lines.append(line)

        if removed_count > 0:
            self.fixes["page_numbers"] = removed_count

        return "\n".join(cleaned_lines)

    def _remove_bullet_from_intro(self, content: str) -> str:
        """Remove bullets from introductory phrases (Đối với..., Trường hợp...)."""
        patterns = [
            (r"^- (Đối với[^:]+:)", r"\1"),
            (r"^- (Trường hợp[^:]+:)", r"\1"),
            (r"^- (Riêng với[^:]+:)", r"\1"),
        ]

        for pattern, replacement in patterns:
            matches = len(re.findall(pattern, content, re.MULTILINE))
            if matches > 0:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                self.fixes["bullet_intro"] = self.fixes.get("bullet_intro", 0) + matches

        return content

    def _fix_definition_lists(self, content: str) -> str:
        """Convert inline definitions to proper list format."""
        # Pattern: KEY: value on same line without bullet
        pattern = r"^([A-ZĐÀÁẢÃẠ][A-ZĐÀÁẢÃẠA-Z0-9\s]{2,20}):\s*([^\n]+)$"

        def replace_def(match: re.Match[str]) -> str:
            key = match.group(1).strip()
            value = match.group(2).strip()
            return f"- **{key}:** {value}"

        matches = len(re.findall(pattern, content, re.MULTILINE))
        if matches > 0:
            content = re.sub(pattern, replace_def, content, flags=re.MULTILINE)
            self.fixes["definition_lists"] = matches

        return content

    def _fix_bold_header_spacing(self, content: str) -> str:
        """Ensure blank line after bold headers (**N. Header**)."""
        pattern = r"(\*\*\d+\..*\*\*)(\n)([^\n])"

        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, r"\1\n\n\3", content)
            self.fixes["bold_header_spacing"] = matches

        return content

    def _normalize_list_markers(self, content: str) -> str:
        """Normalize list markers to use - consistently."""
        # Convert + or * to -
        pattern = r"^(\s*)[\+\*](?=\s)"
        matches = len(re.findall(pattern, content, re.MULTILINE))
        if matches > 0:
            content = re.sub(pattern, r"\1-", content, flags=re.MULTILINE)
            self.fixes["list_markers"] = matches

        return content

    def _ensure_trailing_newline(self, content: str) -> str:
        """Ensure file ends with exactly one newline."""
        if not content.endswith("\n") or content.endswith("\n\n"):
            content = content.rstrip() + "\n"
            self.fixes["trailing_newline"] = 1

        return content

    def _fix_emphasis_style(self, content: str) -> str:
        """Convert underscore emphasis to asterisk emphasis (MD049)."""
        # Pattern: _text_ -> *text*
        # Avoid matching across lines or matching __bold__
        pattern = r"(?<!_)(?<!\w)_(?!\s|_)((?:[^_]|\\_)+)(?<!\s|_)_(?!\w)(?!_)"

        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, r"*\1*", content)
            self.fixes["emphasis_style"] = matches

        return content

    def _fix_multiple_blanks(self, content: str) -> str:
        """Collapse multiple consecutive blank lines to max one blank line (MD012)."""
        # Replace 3 or more newlines with 2 newlines (paragraph break)
        pattern = r"\n{3,}"

        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, "\n\n", content)
            self.fixes["multiple_blanks"] = matches

        return content

    def get_fix_summary(self) -> dict[str, int]:
        """Get summary of fixes applied."""
        return self.fixes.copy()
