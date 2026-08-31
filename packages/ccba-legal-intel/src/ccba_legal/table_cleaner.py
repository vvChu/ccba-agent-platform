"""Table and Footnote Formatting Resilience Module (ADR 0030 & ADR 0035).

Provides deterministic cleaners to prevent squashed table rows, broken header rows,
and non-monotonic footnote sequencing in OKF Markdown conversions.
"""

from __future__ import annotations

import re


def flatten_table_headers(markdown_text: str) -> str:
    """Flatten multiline cells within table headers and ensure each table row is intact.
    
    Removes interior newlines (\\r, \\n) from table header lines before the separator row.
    """
    lines = markdown_text.splitlines()
    output_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if the next line is a markdown table separator: | :--- | :--- | ... |
        if i + 1 < len(lines) and re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", lines[i + 1].strip()):
            # The current line `line` is the table header.
            # If the header itself was broken across previous lines or contains unclosed row, merge it.
            header_parts = [stripped]
            # Check backwards if previous lines were broken header fragments
            # Usually in docx conversions, header is on 1 line or immediately broken into 2 lines
            # Check if current line starts with | but doesn't end with |
            if stripped.startswith("|") and not stripped.endswith("|") and i + 1 < len(lines):
                pass
            output_lines.append(line)
            i += 1
            continue

        # If a line starts with | but doesn't end with |, it's an unclosed table row that was wrapped
        if stripped.startswith("|") and not stripped.endswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # If next line ends with |, merge them into a single valid table row
            if next_line.endswith("|") and not next_line.startswith("| :---"):
                merged = f"{stripped} {next_line}"
                output_lines.append(merged)
                i += 2
                continue

        output_lines.append(line)
        i += 1

    return "\n".join(output_lines)


def enforce_monotonic_footnotes(markdown_text: str) -> str:
    """Ensure that all multi-part footnotes strictly follow monotonic numbering (CHÚ THÍCH 1, 2...).
    
    If a section or table note has 'CHÚ THÍCH 2:' but the preceding note is unnumbered,
    this automatically prefixes it with '**CHÚ THÍCH 1:**'.
    """
    # 1. Pattern matching: _CHÚ THÍCH:_\n\n<content_1>\n\n**CHÚ THÍCH 2:**
    pattern = re.compile(
        r"(_CHÚ THÍCH:_\s*\n+)(?!\s*\*\*CHÚ THÍCH 1:\*\*)([^\n]+)(\s*\n+\s*\*\*CHÚ THÍCH 2:\*\*)",
        re.MULTILINE
    )

    def replacer(m: re.Match[str]) -> str:
        content_1 = m.group(2).strip()
        rest = m.group(3)
        return f"_CHÚ THÍCH:_\n\n**CHÚ THÍCH 1:** {content_1}{rest}"

    new_text = pattern.sub(replacer, markdown_text)

    # 2. Chunk-based verification across section headers
    chunks = re.split(r"(?=\n#{1,4}\s+|\n<a id=)", new_text)
    fixed_chunks: list[str] = []
    for chunk in chunks:
        labels = [
            re.sub(r"[_*]", "", m.group(1)).strip().upper()
            for m in re.finditer(r"(?:^|[^a-zA-Z0-9])([_*]*(?:CHÚ THÍCH|Chú thích)(?:\s+\d+)?[_*]*):", chunk, re.IGNORECASE)
        ]
        if "CHÚ THÍCH 2" in labels and "CHÚ THÍCH 1" not in labels:
            chunk = re.sub(
                r"(_CHÚ THÍCH:_\s*\n+)(?!\s*\*\*CHÚ THÍCH 1:\*\*)([^\n]+)",
                r"_CHÚ THÍCH:_\n\n**CHÚ THÍCH 1:** \2",
                chunk,
                count=1
            )
            chunk = re.sub(
                r"(?:\*\*)?(?:CHÚ THÍCH|Chú thích)(?:\*\*)?:\s*([^\n]+)",
                r"_CHÚ THÍCH:_\n\n**CHÚ THÍCH 1:** \1",
                chunk,
                count=1
            )
        fixed_chunks.append(chunk)

    final_text = "".join(fixed_chunks)
    # Clean duplicate consecutive _CHÚ THÍCH:_ headers
    final_text = re.sub(r"(_CHÚ THÍCH:_\s*\n+)+_CHÚ THÍCH:_\s*\n+", r"_CHÚ THÍCH:_\n\n", final_text)
    return final_text


def clean_markdown_tables_and_notes(markdown_text: str) -> str:
    """Unified master cleaner for Markdown tables and footnotes."""
    text = flatten_table_headers(markdown_text)
    text = enforce_monotonic_footnotes(text)
    return text
