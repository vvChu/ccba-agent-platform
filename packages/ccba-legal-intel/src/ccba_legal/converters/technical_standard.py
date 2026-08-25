"""Native Technical Standard (TCVN / QCVN) Strategy Converter (ADR 0030, ADR 0031)."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.converters.table_extractor import classify_and_extract_tables
from ccba_legal.converters.unit_normalizer import normalize_units_and_math
from ccba_legal.formula_harvester import harvest_docx_formula_images
from ccba_legal.gold_standard import generate_bundle_ast_and_qa, inject_semantic_anchors


def process_technical_standard_strategy(
    docx_path: Path,
    bundle_dir: Path,
    registry_file: Path,
    doc_meta: dict[str, Any],
    output_filename: str | None = None,
) -> dict[str, Any]:
    """Native Technical Standard (TCVN / QCVN) Strategy Converter."""
    import docx
    import docx.oxml
    import docx.oxml.text.paragraph
    import docx.oxml.table

    doc = docx.Document(str(docx_path))
    templates_dir = bundle_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # ADR 0031: Pre-harvest formula images from DOCX before main loop
    spoke_root = bundle_dir.parents[2]  # legal_docs/XX/name -> spoke root
    cache_dir = spoke_root / ".md" / "cache" / "formula_vision"
    skip_vision = os.environ.get("AI_SKIP_VISION", "").strip() == "1"

    rid_to_katex: dict = harvest_docx_formula_images(
        docx_path, cache_dir=cache_dir, skip_vision=skip_vision
    )

    extracted_tables = classify_and_extract_tables(docx_path, bundle_dir)

    blocks = []
    for child in doc.element.body.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            blocks.append(("p", docx.text.paragraph.Paragraph(child, doc)))
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            blocks.append(("tbl", docx.table.Table(child, doc)))

    body_md_parts: list[str] = []
    table_idx = 0

    # ADR 0030: Find exact start of real normative body
    start_idx = 0
    for idx, (b_type, obj) in enumerate(blocks):
        if b_type == "p":
            txt = obj.text.strip()
            if (
                "1 QUY ĐỊNH CHUNG" in txt
                or "1  QUY ĐỊNH CHUNG" in txt
                or "1. QUY ĐỊNH CHUNG" in txt
                or "1  Phạm vi" in txt
                or "1. Phạm vi" in txt
                or "1  PHẠM VI" in txt
            ):
                for k in range(idx + 1, min(idx + 10, len(blocks))):
                    if blocks[k][0] == "p":
                        k_txt = blocks[k][1].text.strip()
                        if k_txt.startswith("1.1.1") or k_txt.startswith("1.1.2") or len(k_txt) > 100:
                            start_idx = idx
                            break
                if start_idx > 0:
                    break

    i = start_idx
    in_main_body = True
    last_table_caption = ""
    in_formula_explanation = False

    while i < len(blocks):
        b_type, obj = blocks[i]
        if b_type == "p":
            text = obj.text.strip()
            if not text:
                # ADR 0031: Check if this empty paragraph contains a formula image
                xml_str = obj._element.xml
                for rid, katex in rid_to_katex.items():
                    if rid in xml_str and not katex.startswith("<!-- DIAGRAM"):
                        body_md_parts.append(f"\n{katex}\n")
                        break
                i += 1
                continue

            text = normalize_units_and_math(text)

            if (
                (text.startswith("Phụ lục A") or text.startswith("PHỤ LỤC A") or text.startswith("Phụ lục B"))
                and i > start_idx + 15
            ):
                break

            # Check for table title immediately preceding table
            m_tbl_title = re.match(r"^(Bảng\s+[0-9A-Z]+(?:\.[0-9A-Z]+)*[\.:\s\-]+[^\n]*)", text)
            if m_tbl_title:
                last_table_caption = text
                i += 1
                continue

            # 1. Major Section Headings
            m_sec = re.match(r"^([1-9])\s+([^\n]+)", text)
            if m_sec:
                sec_num, sec_title = m_sec.group(1), m_sec.group(2)
                anchor = f"muc-{sec_num}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n## {sec_num}  {sec_title.upper()}\n')
                i += 1
                continue

            # 2. Section Definitions
            m_def_alone = re.match(r"^(1\.3\.[0-9]+|3\.[0-9]+)$", text)
            if m_def_alone:
                def_num = m_def_alone.group(1)
                if i + 1 < len(blocks) and blocks[i + 1][0] == "p":
                    next_text = blocks[i + 1][1].text.strip()
                    anchor = f"muc-{def_num.replace('.', '-')}"
                    body_md_parts.append(f'\n<a id="{anchor}"></a>\n#### {def_num}  {next_text}\n')
                    i += 2
                    continue
                else:
                    anchor = f"muc-{def_num.replace('.', '-')}"
                    body_md_parts.append(f'\n<a id="{anchor}"></a>\n#### {def_num}\n')
                    i += 1
                    continue

            m_def = re.match(r"^(1\.3\.[0-9]+|3\.[0-9]+)\s+([^\n]+)", text)
            if m_def:
                def_num, def_title = m_def.group(1), m_def.group(2)
                anchor = f"muc-{def_num.replace('.', '-')}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n#### {def_num}  {def_title}\n')
                i += 1
                continue

            # 3. Decimal Sub-clauses
            m_clause = re.match(r"^([1-9]\.[0-9]+(?:\.[0-9]+)*)\s+([^\n]+)", text)
            if m_clause:
                cl_num, cl_text = m_clause.group(1), m_clause.group(2)
                anchor = f"muc-{cl_num.replace('.', '-')}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n### {cl_num}  {cl_text}\n')
                i += 1
                continue

            # 4. List markers preservation (ADR 0029)
            if text.startswith("+ ") or text.startswith("+"):
                clean_item = text.lstrip("+ ").strip()
                body_md_parts.append(f"&nbsp;&nbsp;\\+ {clean_item}\n")
                i += 1
                continue

            if (
                text.startswith("- ")
                or text.startswith("• ")
                or text.startswith("– ")
                or text.startswith("— ")
                or text.startswith("-")
            ):
                clean_item = text.lstrip("-•–— ").strip()
                body_md_parts.append(f"\\- {clean_item}\n")
                i += 1
                continue

            if re.match(r"^[a-z]\)", text):
                body_md_parts.append(f"\n{text}\n")
                i += 1
                continue

            # 6. Table Caption check
            m_tbl_cap = re.match(r"^(?:Bảng|Table)\s+([0-9A-Za-z\.\-]+)(?:\s*[-–—:]\s*(.+))?$", text, re.IGNORECASE)
            if m_tbl_cap and i + 1 < len(blocks) and blocks[i + 1][0] == "tbl":
                last_table_caption = text
                in_formula_explanation = False
                body_md_parts.append(f"\n{text}\n")
                i += 1
                continue

            # 7. Formula Explanation Trigger & Scope (ADR 0030)
            if re.match(r"^(?:trong đó|với|ở đây|ký hiệu trong công thức)\s*:?$", text, re.IGNORECASE):
                in_formula_explanation = True
                body_md_parts.append(f"\n{text}\n")
                i += 1
                continue

            if in_formula_explanation:
                if (
                    text.startswith("CHÚ THÍCH")
                    or text.startswith("GHI CHÚ")
                    or re.match(r"^(?:Đối với|Khi |Các |Trong trường hợp|Tải trọng)\b", text)
                ):
                    in_formula_explanation = False
                else:
                    if text.startswith(("+ ", "+", "- ", "• ", "– ", "— ", "-")):
                        clean_item = text.lstrip("-•–—+ ").strip()
                        body_md_parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{clean_item}\n")
                    else:
                        body_md_parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{text}\n")
                    i += 1
                    continue

            body_md_parts.append(f"\n{text}\n")
            i += 1

        elif b_type == "tbl" and in_main_body:
            tbl = obj
            rows_cnt = len(tbl.rows)
            cols_cnt = len(tbl.columns)

            # Check formula layout frame (ADR 0030)
            is_formula_frame = False
            if rows_cnt <= 2 and cols_cnt == 2:
                cell_texts = [c.text.strip() for r in tbl.rows for c in r.cells]
                has_tag = any(re.match(r"^\(\d+[a-z]?\)$", t) for t in cell_texts)
                has_empty = any(t == "" for t in cell_texts)
                if has_tag and (has_empty or len(cell_texts) <= 2):
                    is_formula_frame = True

            if is_formula_frame:
                i += 1
                continue

            # Anonymous table / Glossary check (ADR 0030)
            table_slug = None
            if last_table_caption:
                m_cap = re.match(r"^(?:Bảng|Table)\s+([0-9A-Za-z\.\-]+)", last_table_caption, re.IGNORECASE)
                if m_cap:
                    cap_val = m_cap.group(1)
                    if cap_val.isdigit():
                        table_slug = f"bang_{int(cap_val):02d}"
                    else:
                        table_slug = f"bang_{cap_val.replace('.', '_')}"

            if not table_slug:
                prev_text_context = "".join(body_md_parts[-3:]).lower()
                is_glossary = cols_cnt == 2 and any(k in prev_text_context for k in ["ký hiệu", "chữ viết tắt", "từ viết tắt", "symbols", "abbreviations"])
                if is_glossary:
                    for row in tbl.rows:
                        row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                        if len(row_cells) >= 2 and row_cells[0] and row_cells[1]:
                            sym, desc = row_cells[0], row_cells[1]
                            body_md_parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{sym}  {desc}\n\n")
                    last_table_caption = ""
                    i += 1
                    continue

                table_idx += 1
                table_slug = f"bang_{table_idx:02d}"

            anchor = f"bang-{table_slug.replace('_', '-')}"
            body_md_parts.append(f'\n<a id="{anchor}"></a>\n')

            # Render 2D GFM Table
            grid = []
            for row in tbl.rows:
                row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                clean_cells = []
                for cell_val in row_cells:
                    if not clean_cells or cell_val != clean_cells[-1]:
                        clean_cells.append(cell_val)
                if clean_cells:
                    grid.append(clean_cells)

            if grid:
                max_cols = max(len(r) for r in grid)
                norm_grid = [r + [""] * (max_cols - len(r)) for r in grid]
                header = norm_grid[0]
                body_md_parts.append("| " + " | ".join(header) + " |\n")
                body_md_parts.append("| " + " | ".join([":---:"] * max_cols) + " |\n")
                for r in norm_grid[1:]:
                    body_md_parts.append("| " + " | ".join(r) + " |\n")
                body_md_parts.append("\n")

            last_table_caption = ""
            i += 1

    body_raw = "".join(body_md_parts)
    body_anchored = inject_semantic_anchors(body_raw, archetype="TECHNICAL_TCVN")

    target_md_filename = output_filename or f"{bundle_dir.name}.md"
    target_md_file = bundle_dir / target_md_filename
    with open(target_md_file, "w", encoding="utf-8") as f:
        f.write(body_anchored)

    generate_bundle_ast_and_qa(target_md_file, bundle_dir)

    clauses = []
    if (bundle_dir / "clauses.json").exists():
        with open(bundle_dir / "clauses.json", encoding="utf-8") as f:
            clauses = json.load(f)

    qa_benchmark = []
    if (bundle_dir / "qa_benchmark.json").exists():
        with open(bundle_dir / "qa_benchmark.json", encoding="utf-8") as f:
            qa_benchmark = json.load(f)

    doc_num = doc_meta.get("document_number", bundle_dir.name.upper())
    doc_title = doc_meta.get("title", f"Tiêu chuẩn / Quy chuẩn {doc_num}")
    pdf_path = doc_meta.get("pdf_path", f"{bundle_dir.name}.pdf")
    pdf_sha256 = doc_meta.get("pdf_sha256", "UNVERIFIED")

    metadata_obj = {
        "id": bundle_dir.name,
        "document_number": doc_num,
        "type": doc_meta.get("type", "TCVN"),
        "title": doc_title,
        "status": "effective",
        "effective_date": doc_meta.get("effective_date", "2023-12-31"),
        "pdf_path": pdf_path,
        "pdf_sha256": pdf_sha256,
        "pdf_status": "verified",
        "legal_basis": [],
        "replaces": doc_meta.get("relations", {}).get("replaces", []),
    }
    with open(bundle_dir / "metadata.yaml", "w", encoding="utf-8") as f:
        yaml.dump(metadata_obj, f, allow_unicode=True, sort_keys=False, indent=2)

    created_templates = list(templates_dir.glob("*.md"))
    index_md = f"""# Gói Tri Thức Quy Chuẩn / Tiêu Chuẩn Kỹ Thuật OKF v2.2: {doc_num}

> [!NOTE]
> **Văn bản:** {doc_title}
> **Loại văn bản:** Tiêu chuẩn / Quy chuẩn Kỹ thuật Quốc gia.
> **Mỏ neo PDF Công báo:** [{Path(pdf_path).name}](./{Path(pdf_path).name}) *(SHA-256: `{pdf_sha256}`)*.

---

## 📑 Danh Mục Thành Phần Gói Tri Thức (OKF v2.2 Bundle)

- [Toàn văn Thân Quy Chuẩn (Markdown OKF v2.2)](./{target_md_file.name}) — Thân văn bản quy phạm kỹ thuật thuần khiết.
- [Metadata Pháp lý & Thuộc tính (YAML)](./metadata.yaml) — Thông số hiệu lực, ban hành, mã băm PDF SHA-256.
- [Cây Cú Pháp Điều Khoản (AST Clauses JSON)](./clauses.json) — {len(clauses)} nodes điều khoản phục vụ AI QC & RAG.
- [Bộ Đánh Giá Độ Chính Xác (QA Benchmark)](./qa_benchmark.json) — {len(qa_benchmark)} cặp câu hỏi - câu trả lời đối soát.
- [Kho Module Phụ Lục Kỹ Thuật (Templates Directory)](./templates/) — {len(created_templates)} Module Phụ lục Markdown.
- [Bảng Tra Cứu Số Hóa (Tables Directory)](./tables/) — {len(extracted_tables)} Bảng tra cứu số học (CSV + JSON).
"""
    with open(bundle_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(index_md)

    return {
        "status": "success",
        "bundle": bundle_dir.name,
        "archetype": "TECHNICAL_TCVN",
        "clauses_count": len(clauses),
        "templates_count": len(created_templates),
        "tables_count": len(extracted_tables),
        "qa_count": len(qa_benchmark),
    }
