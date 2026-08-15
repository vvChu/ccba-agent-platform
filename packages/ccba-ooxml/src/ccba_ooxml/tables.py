"""Deep Seam for extracting and reconstructing OpenXML DOCX tables into GFM Markdown, JSON, and CSV.

Provides high-precision cell unmerging, footnote separation, descriptive slug generation,
and idempotent markdown table replacement.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    Document = None  # type: ignore[assignment,misc]
    DOCX_AVAILABLE = False


def vietnamese_to_ascii(text: str) -> str:
    """Convert Vietnamese accented text to unaccented ASCII."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return text


def make_descriptive_table_slug(table_num: str, title: str = "") -> str:
    """Generate clean descriptive slug for table filenames."""
    num_str = table_num.lower().replace(".", "_")
    if re.match(r"^\d+$", num_str):
        num_str = f"{int(num_str):02d}"

    base_prefix = f"bang_{num_str}"
    if not title:
        return base_prefix

    title_clean = re.sub(
        r"^(?:Bảng|Table)\s+[A-Z0-9]+(?:\.[0-9]+)?\s*[-–:]\s*",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    ascii_title = vietnamese_to_ascii(title_clean).lower()
    words = re.findall(r"\b[a-z0-9]+\b", ascii_title)

    stopwords = {
        "va", "cua", "cho", "cac", "thuc", "hien", "tuong",
        "ung", "voi", "chung", "nhung", "theo", "đoi", "doi",
    }
    filtered = [w for w in words if w not in stopwords][:5]

    if filtered:
        return f"{base_prefix}_{'_'.join(filtered)}"
    return base_prefix


@dataclass
class StructuredTable:
    """Immutable data transfer object representing a structured 2D table."""

    table_id: str
    num: str
    title: str
    headers: list[str]
    rows: list[list[str]]
    footnotes: list[str] = field(default_factory=list)
    cols_count: int = 0

    def __post_init__(self) -> None:
        """Calculate column count if not provided."""
        if not self.cols_count:
            self.cols_count = len(self.headers) if self.headers else (len(self.rows[0]) if self.rows else 0)

    def to_markdown(self, anchor: bool = True) -> str:
        """Convert table to clean 2D GFM Markdown Pipe Table."""
        lines: list[str] = []
        clean_num = self.num.lower().replace(".", "-")
        if anchor:
            lines.append(f'<a id="bang-{clean_num}"></a>')
        lines.append(f"### {self.title}\n")

        cols = max(self.cols_count, len(self.headers), 1)
        headers = self.headers + [""] * (cols - len(self.headers))
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * cols) + " |")

        for r in self.rows:
            r_padded = r + [""] * (cols - len(r))
            lines.append("| " + " | ".join(r_padded[:cols]) + " |")

        if self.footnotes:
            lines.append("")
            for fn in self.footnotes:
                lines.append(f"_{fn}_")

        lines.append("")
        return "\n".join(lines)

    def to_json(self) -> dict[str, Any]:
        """Convert table to dictionary structure suitable for JSON export."""
        return {
            "table_id": self.table_id,
            "num": self.num,
            "title": self.title,
            "headers": self.headers,
            "rows": self.rows,
            "total_rows": len(self.rows),
            "footnotes": self.footnotes,
            "cols_count": self.cols_count,
        }

    def to_csv(self) -> str:
        """Convert table to CSV formatted string."""
        output = io.StringIO()
        writer = csv.writer(output)
        if self.headers:
            writer.writerow(self.headers)
        for r in self.rows:
            writer.writerow(r)
        return output.getvalue()


class TableReconstructor:
    """Deep Seam for extracting and reconstructing OpenXML DOCX tables."""

    @classmethod
    def extract_docx_tables(cls, docx_path: str | Path) -> list[StructuredTable]:
        """Extract all tables from a .docx file with clean 2D grid matrix and footnotes.

        Args:
            docx_path: Path to the input .docx file.

        Returns:
            list[StructuredTable]: List of extracted structured tables.
        """
        path = Path(docx_path)
        if not DOCX_AVAILABLE or Document is None or not path.exists():
            return []

        doc = Document(str(path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        title_pattern = re.compile(
            r"^(?:Bảng|Table)\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*(.+)$",
            re.IGNORECASE,
        )

        table_titles: list[dict[str, Any]] = []
        for p_idx, text in enumerate(paragraphs):
            match = title_pattern.match(text)
            if match:
                table_titles.append({
                    "num": match.group(1),
                    "title": f"Bảng {match.group(1)} - {match.group(2).strip()}",
                    "p_idx": p_idx,
                })

        extracted_tables: list[StructuredTable] = []

        for idx, table in enumerate(doc.tables):
            table_info = table_titles[idx] if idx < len(table_titles) else {
                "num": str(idx + 1),
                "title": f"Bảng {idx + 1}",
            }

            num_str = str(table_info["num"])
            title_str = str(table_info["title"])
            slug = make_descriptive_table_slug(num_str, title_str)

            grid: list[list[str]] = []
            footnotes: list[str] = []

            for row in table.rows:
                row_cells = [c.text.replace("\n", " ").strip() for c in row.cells]

                # Footnote detection: all cells identical and starts with keyword or length > 80
                is_footnote = len(set(row_cells)) == 1 and (
                    row_cells[0].startswith("CHÚ THÍCH")
                    or bool(re.match(r"^\d+\)\s+", row_cells[0]))
                    or len(row_cells[0]) > 80
                )
                if is_footnote:
                    fn_text = row_cells[0]
                    if fn_text and fn_text not in footnotes:
                        footnotes.append(fn_text)
                    continue

                grid.append(row_cells)

            if not grid:
                continue

            headers = grid[0]
            raw_rows = grid[1:]

            clean_rows: list[list[str]] = []
            for r in raw_rows:
                clean_r = [re.sub(r"\s+", " ", cell).strip() for cell in r]
                if any(clean_r):
                    clean_rows.append(clean_r)

            structured_table = StructuredTable(
                table_id=slug,
                num=num_str,
                title=title_str,
                headers=headers,
                rows=clean_rows,
                footnotes=footnotes,
                cols_count=len(headers),
            )
            extracted_tables.append(structured_table)

        return extracted_tables

    @classmethod
    def replace_markdown_tables(cls, md_content: str, tables: list[StructuredTable]) -> str:
        """Replace unformatted or broken table blocks in markdown with precision GFM pipe tables.

        Args:
            md_content: Original markdown string.
            tables: List of StructuredTable objects to inject.

        Returns:
            str: Updated markdown content.
        """
        content = md_content
        for table in tables:
            table_num = table.num
            new_table_str = table.to_markdown(anchor=True)

            pattern = re.compile(
                rf"(?:<a id=\"[^\"]+\"></a>\n)?(?:###|\*\*|#)*\s*Bảng\s+{re.escape(table_num)}\s*[-–:].*?(?=\n<a id=\"muc-|\n### |\n# |\n(?:#|\*)*\s*Bảng|\Z)",
                re.DOTALL | re.IGNORECASE,
            )

            if pattern.search(content):
                content = pattern.sub(new_table_str, content, count=1)

        return content

    @classmethod
    def save_table_exports(
        cls,
        table: StructuredTable,
        tables_dir: str | Path,
    ) -> tuple[Path, Path]:
        """Save structured table into tables/json/ and tables/csv/ directories.

        Args:
            table: The StructuredTable instance to save.
            tables_dir: Directory where tables are stored.

        Returns:
            tuple[Path, Path]: Paths to the created (json_file, csv_file).
        """
        base_dir = Path(tables_dir)
        json_dir = base_dir / "json"
        csv_dir = base_dir / "csv"
        json_dir.mkdir(parents=True, exist_ok=True)
        csv_dir.mkdir(parents=True, exist_ok=True)

        slug = table.table_id
        json_path = json_dir / f"{slug}.json"
        csv_path = csv_dir / f"{slug}.csv"

        json_path.write_text(
            json.dumps(table.to_json(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            f.write(table.to_csv())

        return json_path, csv_path
