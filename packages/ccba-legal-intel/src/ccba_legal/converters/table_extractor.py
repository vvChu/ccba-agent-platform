"""3-Tier Semantic Table Classifier and Extractor (ADR 0021, ADR 0028, ADR 0030)."""

from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

LAYOUT_KEYWORDS = [
    "cộng hòa xã hội chủ nghĩa", "độc lập - tự do", "nơi nhận:",
    "tm. chính phủ", "kt. thủ tướng", "phó thủ tướng", "bộ trưởng",
    "chủ tịch ủy ban", "ký, ghi rõ họ tên", "ký, đóng dấu", "lưu: vt",
]

NORMATIVE_KEYWORDS = [
    "nguy cơ", "phân loại", "phụ lục", "quy định", "mã hiệu", "định mức",
    "công năng", "tải trọng", "chi phí", "áp lực", "lưu lượng", "khoảng cách",
    "nhiệt độ", "cường độ", "đơn vị", "đường kính", "loại ống", "bội số",
]


def _is_admin_layout_table(text: str, rows: int, cols: int) -> bool:
    """Detect whether a small table is administrative header or signature block."""
    if rows <= 3 and cols <= 2:
        if any(k in text for k in LAYOUT_KEYWORDS) and not any(k in text for k in NORMATIVE_KEYWORDS):
            return True
    return False


def _is_formula_frame_table(table: Any, rows: int, cols: int) -> bool:
    """Detect 2-column formula frames with formula tags (e.g. '(1)', '(B.1)')."""
    if rows <= 2 and cols == 2:
        cell_texts = [c.text.strip() for row in table.rows for c in row.cells]
        has_tag = any(re.match(r"^\(\d+[a-z]?\)$", t) for t in cell_texts)
        has_empty = any(t == "" for t in cell_texts)
        if has_tag and (has_empty or len(cell_texts) <= 2):
            return True
    return False


def _find_preceding_caption(blocks: list[tuple[str, Any]], block_idx: int) -> tuple[str | None, str | None]:
    """Look backwards 1-4 paragraphs to find a table caption ('Bảng X - ...')."""
    for prev_idx in range(block_idx - 1, max(-1, block_idx - 4), -1):
        if blocks[prev_idx][0] == "p":
            p_txt = blocks[prev_idx][1].text.strip()
            if not p_txt:
                continue
            m_cap = re.match(r"^(?:Bảng|Table)\s+([0-9A-Za-z\.\-]+)(?:\s*[-–—:]\s*(.+))?", p_txt, re.IGNORECASE)
            if m_cap:
                return (m_cap.group(1), p_txt)
            break
    return (None, None)


def _is_glossary_table(blocks: list[tuple[str, Any]], block_idx: int, cols: int, caption_num: str | None) -> bool:
    """Detect 2-column symbol and abbreviation tables."""
    if cols == 2 and not caption_num:
        prev_context = " ".join(blocks[p_i][1].text.lower() for p_i in range(max(0, block_idx - 3), block_idx) if blocks[p_i][0] == "p")
        if any(k in prev_context for k in ["ký hiệu", "chữ viết tắt", "từ viết tắt", "symbols", "abbreviations"]):
            return True
    return False


def _harvest_table_footnotes(blocks: list[tuple[str, Any]], block_idx: int) -> list[str]:
    """Harvest footnote lines immediately following the table block."""
    footnotes: list[str] = []
    next_idx = block_idx + 1
    while next_idx < len(blocks):
        next_type, next_obj = blocks[next_idx]
        if next_type == "tbl":
            break
        p_text = next_obj.text.strip()
        if not p_text:
            next_idx += 1
            continue
        if p_text.startswith(("CHÚ THÍCH", "GHI CHÚ", "Chú dẫn")) or (footnotes and p_text.startswith("-")):
            footnotes.append(p_text)
            next_idx += 1
        else:
            break
    return footnotes


def _export_table_files(
    grid: list[list[str]],
    headers: list[str],
    footnotes: list[str],
    table_slug: str,
    csv_dir: Path,
    json_dir: Path,
    bundle_dir: Path,
) -> dict[str, Any]:
    """Export 2D table grid to CSV and JSON files."""
    csv_file = csv_dir / f"{table_slug}.csv"
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(grid)
        if footnotes:
            writer.writerow([])
            writer.writerow(["--- GHI CHÚ / CHÚ THÍCH ---"])
            for fn in footnotes:
                writer.writerow([fn])

    records: list[dict[str, Any]] = []
    if len(grid) > 1:
        for r in grid[1:]:
            records.append({headers[c_idx] or f"col_{c_idx + 1}": r[c_idx] if c_idx < len(r) else "" for c_idx in range(len(headers))})

    json_file = json_dir / f"{table_slug}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({"table_id": table_slug, "rows_count": len(grid), "columns_count": len(headers), "headers": headers, "records": records, "footnotes": footnotes}, f, ensure_ascii=False, indent=2)

    return {
        "table_id": table_slug,
        "rows": len(grid),
        "cols": len(headers),
        "footnotes_count": len(footnotes),
        "csv": str(csv_file.relative_to(bundle_dir)),
        "json": str(json_file.relative_to(bundle_dir)),
    }


def classify_and_extract_tables(docx_path: Path, bundle_dir: Path) -> list[dict[str, Any]]:
    """3-Tier Semantic Table Classifier according to ADR 0021 & ADR 0028."""
    import docx.oxml
    import docx.oxml.table
    import docx.oxml.text.paragraph
    from docx import Document

    doc = Document(str(docx_path))
    tables_dir = bundle_dir / "tables"
    csv_dir = tables_dir / "csv"
    json_dir = tables_dir / "json"

    if tables_dir.exists():
        shutil.rmtree(tables_dir)
    csv_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    blocks: list[tuple[str, Any]] = []
    for child in doc.element.body.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            blocks.append(("p", docx.text.paragraph.Paragraph(child, doc)))
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            blocks.append(("tbl", docx.table.Table(child, doc)))

    extracted_tables: list[dict[str, Any]] = []
    table_counter = 0

    for block_idx, (b_type, obj) in enumerate(blocks):
        if b_type != "tbl":
            continue
        table = obj
        table_counter += 1
        rows_cnt, cols_cnt = len(table.rows), len(table.columns)
        table_text = " ".join(c.text.lower() for row in table.rows for c in row.cells)

        if _is_admin_layout_table(table_text, rows_cnt, cols_cnt) or _is_formula_frame_table(table, rows_cnt, cols_cnt):
            continue

        caption_num, caption_title = _find_preceding_caption(blocks, block_idx)
        if _is_glossary_table(blocks, block_idx, cols_cnt, caption_num):
            continue

        grid: list[list[str]] = []
        for row in table.rows:
            clean_cells: list[str] = []
            row_seen_tc: set[Any] = set()
            for c in row.cells:
                tc_elem = getattr(c, "_tc", id(c))
                if tc_elem not in row_seen_tc:
                    row_seen_tc.add(tc_elem)
                    clean_cells.append(c.text.strip().replace("\n", " "))
            if clean_cells:
                grid.append(clean_cells)


        if not grid:
            continue

        table_slug = f"bang_{int(caption_num):02d}" if caption_num and caption_num.isdigit() else (f"bang_{caption_num.replace('.', '_')}" if caption_num else f"bang_{table_counter:02d}")
        footnotes = _harvest_table_footnotes(blocks, block_idx)
        extracted_tables.append(_export_table_files(grid, grid[0], footnotes, table_slug, csv_dir, json_dir, bundle_dir))

    return extracted_tables
