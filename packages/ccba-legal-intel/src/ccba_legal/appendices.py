"""Appendix Slicer & Markdown Standardizer for Vietnamese Legal Documents.

Extracts and standardizes embedded appendices (Phụ lục) from Decrees, Circulars,
and Standards into standalone Open Knowledge Format (OKF) appendix files with
proper frontmatter, relative linking, and table of contents synchronization.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

APPENDIX_HEADER_PATTERN = re.compile(
    r"^(?:#*|\**)\s*(PHỤ LỤC(?:\s+([IVXLCDM]+|\d+))?)\s*(?:\**)\s*$", re.IGNORECASE
)


def roman_to_decimal(r: str) -> int:
    """Convert Roman numeral string to decimal integer.

    Args:
        r: Roman numeral string (e.g. 'I', 'IV', 'XII').

    Returns:
        Integer representation (or parsed integer if r was digits).
    """
    r = r.strip().upper()
    if r.isdigit():
        return int(r)
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    val = 0
    for i in range(len(r)):
        if r[i] not in roman_map:
            continue
        if i + 1 < len(r) and r[i + 1] in roman_map and roman_map[r[i]] < roman_map[r[i + 1]]:
            val -= roman_map[r[i]]
        else:
            val += roman_map[r[i]]
    return val if val > 0 else 1


class AppendixSplitter:
    """Deep Seam class for parsing and splitting legal document appendices."""

    def __init__(self, uniclass_code: str = "Fi_10_20") -> None:
        self.uniclass_code = uniclass_code

    def split_document_content(
        self, content: str, parent_slug: str, parent_filename: str = ""
    ) -> tuple[str, list[dict[str, Any]]]:
        """Slice a legal markdown document into main body and separate appendix records.

        Args:
            content: Raw markdown text of the parent legal document.
            parent_slug: Document identifier slug (e.g. 'nd_105_2025_nd_cp').
            parent_filename: Optional filename of the parent document (e.g. 'nd_105.md').

        Returns:
            Tuple of (updated_main_body_content, list_of_appendix_dicts).
        """
        lines = content.splitlines()
        matches: list[tuple[int, str, str]] = []

        for idx, line in enumerate(lines):
            m = APPENDIX_HEADER_PATTERN.match(line.strip())
            if m:
                label = m.group(1)
                num_part = m.group(2) or ""
                matches.append((idx, label, num_part))

        if not matches:
            return content, []

        main_body_lines = lines[: matches[0][0]]
        while main_body_lines and not main_body_lines[-1].strip():
            main_body_lines.pop()

        appendices: list[dict[str, Any]] = []
        appendix_links_in_parent: list[str] = []

        for i, (start_idx, full_label, num_part) in enumerate(matches):
            end_idx = matches[i + 1][0] if i + 1 < len(matches) else len(lines)
            app_lines = lines[start_idx:end_idx]

            # Remove header line from content body
            if app_lines:
                app_lines.pop(0)

            # Find title
            title = ""
            for line in app_lines:
                cleaned = line.strip()
                if cleaned and not cleaned.startswith("(") and not cleaned.endswith(")"):
                    title = cleaned.replace("#", "").strip()
                    break

            if not title:
                title = full_label

            # Format decimal string
            if num_part:
                dec_num = roman_to_decimal(num_part)
                dec_str = f"{dec_num:02d}"
            else:
                dec_str = f"{i + 1:02d}"

            app_filename = f"{parent_slug}-phu_luc_{dec_str}.md"
            parent_ref = f"../{parent_filename}" if parent_filename else f"../{parent_slug}.md"

            frontmatter = f"""---
type: Appendix
title: "{full_label} - {title}"
description: "Chi tiết {full_label} ban hành kèm theo {parent_slug.replace("_", " ").title()}"
parent_document: "{parent_ref}"
uniclass: "{self.uniclass_code}"
---

# {full_label}

"""
            app_content = frontmatter + "\n".join(app_lines).strip() + "\n"
            rel_link_parent = f"- [{full_label}: {title}](appendices/{app_filename})"
            rel_link_index = f"- [{full_label}: {title}](guiding_docs/appendices/{app_filename})"

            appendix_links_in_parent.append(rel_link_parent)
            appendices.append(
                {
                    "label": full_label,
                    "title": title,
                    "filename": app_filename,
                    "content": app_content,
                    "parent_link": rel_link_parent,
                    "index_link": rel_link_index,
                }
            )

        updated_parent = "\n".join(main_body_lines).strip() + "\n\n"
        updated_parent += "## DANH SÁCH PHỤ LỤC ĐÍNH KÈM\n\n"
        updated_parent += "\n".join(appendix_links_in_parent) + "\n"

        return updated_parent, appendices

    def process_directory(
        self, guiding_dir: Path | str, base_dir: Path | str | None = None
    ) -> dict[str, Any]:
        """Scan a directory of guiding docs, extract appendices, write files and sync index.

        Args:
            guiding_dir: Directory containing input markdown documents.
            base_dir: Optional root directory containing index.md.

        Returns:
            Dictionary summary with total_files_processed and total_appendices_created.
        """
        g_dir = Path(guiding_dir)
        if not g_dir.exists():
            return {"error": f"Directory not found: {guiding_dir}", "files_processed": 0}

        app_dir = g_dir / "appendices"
        app_dir.mkdir(parents=True, exist_ok=True)

        md_files = [p for p in g_dir.glob("*.md") if p.is_file()]
        all_index_links: list[str] = []
        files_processed = 0
        total_appendices = 0

        for md_path in md_files:
            content = md_path.read_text(encoding="utf-8")
            updated_parent, app_list = self.split_document_content(
                content=content,
                parent_slug=md_path.stem,
                parent_filename=md_path.name,
            )

            if app_list:
                md_path.write_text(updated_parent, encoding="utf-8")
                for app in app_list:
                    out_path = app_dir / app["filename"]
                    out_path.write_text(app["content"], encoding="utf-8")
                    all_index_links.append(app["index_link"])
                    total_appendices += 1
                files_processed += 1

        # Update index.md if base_dir is provided or parent of guiding_dir
        b_dir = Path(base_dir) if base_dir else g_dir.parent
        index_path = b_dir / "index.md"
        if index_path.exists() and all_index_links:
            index_content = index_path.read_text(encoding="utf-8")
            if "### Phụ lục đính kèm" not in index_content:
                appendix_section = "\n### Phụ lục đính kèm (Decree Appendices)\n\n"
                appendix_section += "\n".join(all_index_links) + "\n"
                index_path.write_text(
                    index_content.strip() + "\n" + appendix_section, encoding="utf-8"
                )

        return {
            "files_processed": files_processed,
            "total_appendices_created": total_appendices,
            "appendices_directory": str(app_dir),
        }
