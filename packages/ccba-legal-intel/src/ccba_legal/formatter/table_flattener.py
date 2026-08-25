"""HTML Table processing and 2D grid flattening utilities."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup


def flatten_html_table(table_soup: Any) -> tuple[list[list[str]], bool, int]:
    """Flatten an HTML table with rowspan or colspan using a virtual 2D grid."""
    is_complex = False
    rows = table_soup.find_all("tr")
    if not rows:
        return [], False, 0
    grid = {}
    max_c = 0
    max_r = len(rows)
    for r_idx, row in enumerate(rows):
        c_idx = 0
        cells = row.find_all(["td", "th"])
        for cell in cells:
            while (r_idx, c_idx) in grid:
                c_idx += 1
            try:
                rowspan = int(cell.get("rowspan", 1))
            except (ValueError, TypeError):
                rowspan = 1
            try:
                colspan = int(cell.get("colspan", 1))
            except (ValueError, TypeError):
                colspan = 1
            if rowspan > 1 or colspan > 1:
                is_complex = True
            text = cell.get_text().strip().replace("\n", " ").replace("\r", "")
            for r_offset in range(rowspan):
                for c_offset in range(colspan):
                    grid[(r_idx + r_offset, c_idx + c_offset)] = text
            c_idx += colspan
            if c_idx > max_c:
                max_c = c_idx
    final_grid = [[grid.get((r, c), "") for c in range(max_c)] for r in range(max_r)]
    return final_grid, is_complex, max_r


def grid_to_markdown(grid: list[list[str]]) -> str:
    """Convert a 2D grid into a markdown table representation."""
    if not grid or all(not row for row in grid):
        return ""
    headers = [val.replace("|", "\\|") for val in grid[0]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in grid[1:]:
        cells = [val.replace("|", "\\|") for val in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def grid_to_csv(grid: list[list[str]]) -> str:
    """Convert a 2D grid into CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(grid)
    return output.getvalue()


def grid_to_json(grid: list[list[str]]) -> str:
    """Convert a 2D grid into a list of row-object dicts formatted as JSON."""
    if len(grid) < 2:
        return "[]"
    headers = grid[0]
    rows = []
    for row_vals in grid[1:]:
        row_dict = {}
        for h, val in zip(headers, row_vals):
            if h:
                row_dict[h] = val
        rows.append(row_dict)
    return json.dumps(rows, ensure_ascii=False, indent=2)


def find_top_level_tables(soup: BeautifulSoup) -> list[Any]:
    """Extract only top-level <table> elements, ignoring nested ones."""
    all_tables = soup.find_all("table")
    top_tables = []
    for tbl in all_tables:
        parent = tbl.find_parent("table")
        if not parent:
            top_tables.append(tbl)
    return top_tables


def process_tables(content: str, bundle_dir: Path) -> str:
    """Extract, flatten, and save tables from HTML content."""
    if "<table" not in content.lower():
        return content
    soup = BeautifulSoup(content, "html.parser")
    tables = find_top_level_tables(soup)
    if not tables:
        return content
    tables_dir = bundle_dir / "tables"
    for idx, tbl in enumerate(tables, 1):
        grid, is_complex, num_rows = flatten_html_table(tbl)
        if not grid:
            tbl.decompose()
            continue
        if is_complex or num_rows > 10:
            tables_dir.mkdir(parents=True, exist_ok=True)
            table_id = f"table_{idx:02d}"
            (tables_dir / f"{table_id}.csv").write_text(grid_to_csv(grid), encoding="utf-8")
            (tables_dir / f"{table_id}.json").write_text(grid_to_json(grid), encoding="utf-8")
            link_tag = soup.new_tag("p")
            link_tag.string = f"[Bảng {idx} (Xem chi tiết bảng đầy đủ tệp CSV)](tables/{table_id}.csv) | [Xem tệp JSON](tables/{table_id}.json)"
            tbl.replace_with(link_tag)
        else:
            md_table = grid_to_markdown(grid)
            md_p = soup.new_tag("p")
            md_p.string = f"\n\n{md_table}\n\n"
            tbl.replace_with(md_p)
    return str(soup)
