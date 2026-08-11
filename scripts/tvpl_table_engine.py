"""Dual-Parser Table Engine for converting complex docx tables into Markdown tables."""

import sys
from pathlib import Path

# Force UTF-8 encoding
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    import docx
except ImportError:
    docx = None


def convert_docx_table_to_markdown(table) -> str:
    """Convert a python-docx Table object to clean Markdown format."""
    rows_data: list[list[str]] = []
    for row in table.rows:
        row_cells = [cell.text.strip().replace("\n", "<br>") for cell in row.cells]
        rows_data.append(row_cells)

    if not rows_data:
        return ""

    # Generate header
    header = "| " + " | ".join(rows_data[0]) + " |"
    separator = "| " + " | ".join(["---"] * len(rows_data[0])) + " |"

    body_rows = []
    for r in rows_data[1:]:
        # Handle cell row length mismatch
        if len(r) < len(rows_data[0]):
            r += [""] * (len(rows_data[0]) - len(r))
        elif len(r) > len(rows_data[0]):
            r = r[: len(rows_data[0])]
        body_rows.append("| " + " | ".join(r) + " |")

    return "\n".join([header, separator] + body_rows)


def extract_docx_with_tables(docx_path: Path) -> str:
    """Extract clean text and reconstructed Markdown tables from a .docx file."""
    if not docx or not docx_path.exists():
        return ""

    doc = docx.Document(docx_path)
    output_parts = []

    for elem in doc.element.body:
        if elem.tag.endswith("p"):
            para = docx.text.paragraph.Paragraph(elem, doc)
            txt = para.text.strip()
            if txt:
                output_parts.append(txt)
        elif elem.tag.endswith("table"):
            tbl = docx.table.Table(elem, doc)
            md_tbl = convert_docx_table_to_markdown(tbl)
            if md_tbl:
                output_parts.append("\n" + md_tbl + "\n")

    return "\n\n".join(output_parts)
