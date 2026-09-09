"""Table extraction, QCVN technical formatting, and DOCX normalization engine.

Provides precision table extraction from DOCX documents and standardized
conversion to GFM Markdown Pipe Tables according to Vietnamese legal & QCVN standards.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document
from pydantic import BaseModel, Field


class ExtractedTable(BaseModel):
    """Structured representation of an extracted document table."""

    table_id: str
    caption: str = ""
    rows: int
    cols: int
    markdown_representation: str
    headers: list[str] = Field(default_factory=list)
    data: list[list[str]] = Field(default_factory=list)
    footnotes: list[str] = Field(default_factory=list)


def extract_docx_tables(docx_path: Path | str) -> list[ExtractedTable]:
    """Extract all tables from a Word document, resolving merged cells cleanly.

    Args:
        docx_path: Path to DOCX file.

    Returns:
        List of ExtractedTable models with GFM markdown pipe tables.
    """
    path_obj = Path(docx_path)
    if not path_obj.exists():
        return []

    doc = Document(str(path_obj))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    title_pattern = re.compile(
        r"^(?:Bảng|Table)\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*(.+)$",
        re.IGNORECASE,
    )

    table_titles: list[dict[str, Any]] = []
    for p_idx, text in enumerate(paragraphs):
        match = title_pattern.match(text)
        if match:
            table_titles.append(
                {
                    "num": match.group(1),
                    "title": f"Bảng {match.group(1)} - {match.group(2).strip()}",
                    "p_idx": p_idx,
                }
            )

    results: list[ExtractedTable] = []

    for idx, table in enumerate(doc.tables):
        table_info = (
            table_titles[idx]
            if idx < len(table_titles)
            else {
                "num": str(idx + 1),
                "title": f"Bảng {idx + 1}",
            }
        )

        num_str = str(table_info["num"])
        slug = f"bang_{num_str.lower().replace('.', '_')}"
        if re.match(r"^\d+$", num_str):
            slug = f"bang_{int(num_str):02d}"

        grid: list[list[str]] = []
        footnotes: list[str] = []

        for row in table.rows:
            row_cells = [c.text.replace("\n", " ").strip() for c in row.cells]
            if len(set(row_cells)) == 1 and (
                row_cells[0].startswith("CHÚ THÍCH")
                or re.match(r"^\d+\)\s+", row_cells[0])
                or len(row_cells[0]) > 80
            ):
                if row_cells[0] and row_cells[0] not in footnotes:
                    footnotes.append(row_cells[0])
                continue
            grid.append(row_cells)

        if not grid:
            continue

        headers = grid[0]
        data_rows = grid[1:]
        clean_rows = []
        for r in data_rows:
            clean_r = [re.sub(r"\s+", " ", cell).strip() for cell in r]
            if any(clean_r):
                clean_rows.append(clean_r)

        cols_count = len(headers)
        table_anchor = f"bang-{num_str.lower().replace('.', '-')}"

        md_lines = [
            f'<a id="{table_anchor}"></a>',
            f"### {table_info['title']}\n",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * cols_count) + " |",
        ]
        for r in clean_rows:
            if len(r) < cols_count:
                r = r + [""] * (cols_count - len(r))
            md_lines.append("| " + " | ".join(r[:cols_count]) + " |")

        if footnotes:
            md_lines.append("\n" + "\n".join(f"_{fn}_" for fn in footnotes))

        md_rep = "\n".join(md_lines)

        results.append(
            ExtractedTable(
                table_id=slug,
                caption=table_info["title"],
                rows=len(clean_rows) + 1,
                cols=cols_count,
                markdown_representation=md_rep,
                headers=headers,
                data=clean_rows,
                footnotes=footnotes,
            )
        )

    return results


def format_qcvn_md_table(table_raw_md: str) -> str:
    """Format and normalize technical compliance tables according to Vietnam QCVN standards.

    Args:
        table_raw_md: Raw multiline or broken markdown table string.

    Returns:
        Clean, aligned 2D GFM Markdown pipe table.
    """
    lines = [line.strip() for line in table_raw_md.splitlines() if line.strip()]
    if not lines:
        return ""

    # Parse pipe lines or tab-separated lines
    rows: list[list[str]] = []
    for line in lines:
        if line.startswith("|") and line.endswith("|"):
            parts = [p.strip() for p in line.strip("|").split("|")]
        elif "\t" in line:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
        else:
            parts = [p.strip() for p in re.split(r"\s{2,}", line) if p.strip()]

        # Skip delimiter rows
        if parts and all(re.match(r"^:?-+:?$", p) for p in parts if p):
            continue
        if parts:
            rows.append(parts)

    if not rows:
        return table_raw_md

    max_cols = max(len(r) for r in rows)
    if max_cols == 0:
        return table_raw_md

    # Pad rows to max_cols
    normalized_rows = [r + [""] * (max_cols - len(r)) for r in rows]

    headers = normalized_rows[0]
    data_rows = normalized_rows[1:]

    out_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * max_cols) + " |",
    ]
    for r in data_rows:
        out_lines.append("| " + " | ".join(r) + " |")

    return "\n".join(out_lines)


def format_all_qcvn_md_tables(md_path: Path | str) -> int:
    """Scan and convert all multiline/broken table blocks in md_path to 2D GFM Pipe Tables.

    Args:
        md_path: Path to Markdown file.

    Returns:
        Number of tables reformatted.
    """
    path_obj = Path(md_path)
    if not path_obj.exists():
        return 0

    content = path_obj.read_text(encoding="utf-8")
    table_block_regex = re.compile(
        r"(<a id=\"[^\"]+\"></a>\n)?([#*]+)?\s*(Bảng\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*([^\n\*\#]+))([#*]*|\n)?"
        r"(.*?)(?=\n<a id=\"muc-|\n### |\n# |\n(?:\#|\*)*\s*Bảng|\Z)",
        re.DOTALL | re.IGNORECASE,
    )

    formatted_count = 0

    def replace_table_block(match: re.Match[str]) -> str:
        nonlocal formatted_count
        table_num = match.group(4)
        table_title_text = match.group(5).strip("*\n# ")
        table_title = f"Bảng {table_num} - {table_title_text}"
        table_anchor = f"bang-{table_num.lower().replace('.', '-')}"
        body_text = match.group(7)

        raw_lines = body_text.splitlines()
        row_lines: list[str] = []
        footnotes: list[str] = []

        for line in raw_lines:
            line_str = line.strip()
            clean_str = re.sub(r"<a id=\"[^\"]+\"></a>", "", line_str)
            clean_str = re.sub(r"^[#*\s|]+", "", clean_str).strip(" |")

            if not clean_str or clean_str == "---":
                continue

            if re.match(r"^\d+\)\s+", clean_str) or clean_str.startswith("CHÚ THÍCH"):
                footnotes.append(clean_str)
                continue

            row_lines.append(clean_str)

        if len(row_lines) < 2:
            return str(match.group(0))

        formatted_count += 1
        pipe_table = format_qcvn_md_table("\n".join(row_lines))
        result = f'<a id="{table_anchor}"></a>\n### {table_title}\n\n{pipe_table}\n'
        if footnotes:
            result += "\n" + "\n".join(f"_{fn}_" for fn in footnotes) + "\n"
        return result

    updated_content = table_block_regex.sub(replace_table_block, content)
    path_obj.write_text(updated_content, encoding="utf-8")
    return formatted_count


def normalize_docx_markdown(md_text: str) -> str:
    """Normalize mammoth converted markdown headings and clean up escape chars.

    Args:
        md_text: Raw markdown text from mammoth converter.

    Returns:
        Normalized markdown string with clean headings and anchors.
    """
    # Remove escaped dots, hyphens, and brackets
    text = md_text.replace(r"\.", ".").replace(r"\-", "-").replace(r"\(", "(").replace(r"\)", ")")

    # Clean double ### headers if any exist
    text = re.sub(r"(###\s*)+", "### ", text)

    # Replace bold section headings __1.1 Title__ with ### 1.1 Title
    text = re.sub(r'<a id="[^"]+"></a>\s*__(\d+(?:\.\d+)*)\.?\s*([^_]+)__', r"### \1 \2", text)
    text = re.sub(r"__(\d+(?:\.\d+)*)\.?\s*([^_]+)__", r"### \1 \2", text)

    # Replace bold table headings __Bảng X - Title__ with ### Bảng X - Title
    text = re.sub(
        r"__Bảng\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*([^_]+)__", r"### Bảng \1 - \2", text
    )

    # Clean duplicate ### prefixes
    text = re.sub(r"###\s*###\s*", "### ", text)

    return text


def convert_docx_to_okf_bundle(
    docx_path: Path | str, target_bundle_dir: Path | str
) -> dict[str, Any]:
    """Convert a Word document into an Open Knowledge Format (OKF v2.4) Markdown bundle.

    Args:
        docx_path: Path to input DOCX file.
        target_bundle_dir: Destination directory for bundle output.

    Returns:
        Dictionary summary of the conversion result.
    """
    in_file = Path(docx_path)
    bundle_dir = Path(target_bundle_dir)
    if not in_file.exists():
        raise FileNotFoundError(f"Input file not found: {in_file}")

    bundle_dir.mkdir(parents=True, exist_ok=True)
    target_md = bundle_dir / f"{in_file.stem}.md"

    try:
        import mammoth

        with open(in_file, "rb") as f:
            result = mammoth.convert_to_markdown(f)
            raw_md = result.value
    except ImportError:
        # Fallback to python-docx text extraction
        doc = Document(str(in_file))
        raw_md = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    normalized_md = normalize_docx_markdown(raw_md)
    target_md.write_text(normalized_md, encoding="utf-8")

    # Extract tables and format
    tables = extract_docx_tables(in_file)
    reformatted_tables = format_all_qcvn_md_tables(target_md)

    return {
        "status": "success",
        "output_file": str(target_md),
        "tables_extracted": len(tables),
        "tables_reformatted": reformatted_tables,
        "bytes_written": len(normalized_md),
    }


__all__ = [
    "ExtractedTable",
    "extract_docx_tables",
    "format_qcvn_md_table",
    "format_all_qcvn_md_tables",
    "normalize_docx_markdown",
    "convert_docx_to_okf_bundle",
]
