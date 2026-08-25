"""3-Tier Semantic Table Classifier and Extractor (ADR 0021, ADR 0028, ADR 0030)."""

from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any


def classify_and_extract_tables(docx_path: Path, bundle_dir: Path) -> list[dict[str, Any]]:
    """3-Tier Semantic Table Classifier according to ADR 0021 & ADR 0028."""
    try:
        from docx import Document
        import docx.oxml
        import docx.oxml.text.paragraph
        import docx.oxml.table
    except ImportError as err:
        raise ImportError(
            "Gói 'python-docx' chưa được cài đặt. Vui lòng cài đặt qua 'pip install python-docx' để bóc tách bảng DOCX."
        ) from err

    doc = Document(str(docx_path))
    tables_dir = bundle_dir / "tables"
    csv_dir = tables_dir / "csv"
    json_dir = tables_dir / "json"

    if tables_dir.exists():
        shutil.rmtree(tables_dir)
    csv_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    extracted_tables = []
    layout_keywords = [
        "cộng hòa xã hội chủ nghĩa", "độc lập - tự do", "nơi nhận:",
        "tm. chính phủ", "kt. thủ tướng", "phó thủ tướng", "bộ trưởng",
        "chủ tịch ủy ban", "ký, ghi rõ họ tên", "ký, đóng dấu", "lưu: vt",
    ]
    normative_keywords = [
        "nguy cơ", "phân loại", "phụ lục", "quy định", "mã hiệu", "định mức",
        "công năng", "tải trọng", "chi phí", "áp lực", "lưu lượng", "khoảng cách",
        "nhiệt độ", "cường độ", "đơn vị", "đường kính", "loại ống", "bội số",
    ]

    blocks = []
    for child in doc.element.body.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            blocks.append(("p", docx.text.paragraph.Paragraph(child, doc)))
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            blocks.append(("tbl", docx.table.Table(child, doc)))

    table_counter = 0
    for block_idx, (b_type, obj) in enumerate(blocks):
        if b_type != "tbl":
            continue

        table = obj
        table_counter += 1
        rows_cnt = len(table.rows)
        cols_cnt = len(table.columns)
        table_text = " ".join(c.text.lower() for row in table.rows for c in row.cells)

        is_admin_layout = False
        if rows_cnt <= 3 and cols_cnt <= 2:
            if any(k in table_text for k in layout_keywords):
                if not any(k in table_text for k in normative_keywords):
                    is_admin_layout = True

        # Formula layout frame detection (ADR 0030)
        is_formula_frame = False
        if rows_cnt <= 2 and cols_cnt == 2:
            cell_texts = [c.text.strip() for row in table.rows for c in row.cells]
            has_tag = any(re.match(r"^\(\d+[a-z]?\)$", t) for t in cell_texts)
            has_empty = any(t == "" for t in cell_texts)
            if has_tag and (has_empty or len(cell_texts) <= 2):
                is_formula_frame = True

        # Preceding table caption detection
        caption_num = None
        caption_title = None
        for prev_idx in range(block_idx - 1, max(-1, block_idx - 4), -1):
            if blocks[prev_idx][0] == "p":
                p_txt = blocks[prev_idx][1].text.strip()
                if not p_txt:
                    continue
                m_cap = re.match(r"^(?:Bảng|Table)\s+([0-9A-Za-z\.\-]+)(?:\s*[-–—:]\s*(.+))?", p_txt, re.IGNORECASE)
                if m_cap:
                    caption_num = m_cap.group(1)
                    caption_title = p_txt
                    break
                else:
                    break

        # Glossary / Symbol list detection (ADR 0030)
        is_glossary = False
        if cols_cnt == 2 and not caption_num:
            prev_context = ""
            for p_i in range(max(0, block_idx - 3), block_idx):
                if blocks[p_i][0] == "p":
                    prev_context += " " + blocks[p_i][1].text.lower()
            if any(k in prev_context for k in ["ký hiệu", "chữ viết tắt", "từ viết tắt", "symbols", "abbreviations"]):
                is_glossary = True

        if is_admin_layout or is_formula_frame or is_glossary:
            continue

        grid = []
        for row in table.rows:
            row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            clean_cells = []
            for cell_val in row_cells:
                if not clean_cells or cell_val != clean_cells[-1]:
                    clean_cells.append(cell_val)
            if clean_cells:
                grid.append(clean_cells)

        if not grid:
            continue

        headers = grid[0]

        # Harvest footnotes
        footnotes = []
        next_idx = block_idx + 1
        while next_idx < len(blocks):
            next_type, next_obj = blocks[next_idx]
            if next_type == "tbl":
                break
            p_text = next_obj.text.strip()
            if not p_text:
                next_idx += 1
                continue
            if (
                p_text.startswith("CHÚ THÍCH")
                or p_text.startswith("GHI CHÚ")
                or p_text.startswith("Chú dẫn")
                or (footnotes and p_text.startswith("-"))
            ):
                footnotes.append(p_text)
                next_idx += 1
            else:
                break

        if caption_num:
            if caption_num.isdigit():
                table_slug = f"bang_{int(caption_num):02d}"
            else:
                table_slug = f"bang_{caption_num.replace('.', '_')}"
            table_display_title = caption_title if caption_title else f"Bảng {caption_num}"
        else:
            table_slug = f"bang_{table_counter:02d}"
            table_display_title = f"Bảng {table_counter}"

        # Write CSV
        csv_file = csv_dir / f"{table_slug}.csv"
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(grid)
            if footnotes:
                writer.writerow([])
                writer.writerow(["--- GHI CHÚ / CHÚ THÍCH ---"])
                for fn in footnotes:
                    writer.writerow([fn])

        # Write JSON
        records = []
        if len(grid) > 1:
            for r in grid[1:]:
                rec = {}
                for c_idx, h in enumerate(headers):
                    col_key = h if h else f"col_{c_idx + 1}"
                    rec[col_key] = r[c_idx] if c_idx < len(r) else ""
                records.append(rec)

        json_data = {
            "table_id": table_slug,
            "rows_count": len(grid),
            "columns_count": len(headers),
            "headers": headers,
            "records": records,
            "footnotes": footnotes,
        }
        json_file = json_dir / f"{table_slug}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        extracted_tables.append(
            {
                "table_id": table_slug,
                "rows": len(grid),
                "cols": len(headers),
                "footnotes_count": len(footnotes),
                "csv": str(csv_file.relative_to(bundle_dir)),
                "json": str(json_file.relative_to(bundle_dir)),
            }
        )

    return extracted_tables
