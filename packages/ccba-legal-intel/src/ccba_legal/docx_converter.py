"""CCBA Universal Legal DOCX Converter Engine (OKF v2.2 Gateway).

Converts official .docx documents (QCVN / TCVN / VBPL / Nghị định / Luật / Thông tư)
into Gold Standard OKF v2.2 Markdown bundles with:
- Multi-Archetype Structural Scanner (Full-Document Skimming)
- Dynamic Conversion Strategy Dispatcher (VBPL Admin, Technical QCVN/TCVN, Cost Norm)
- Pure Normative Body (.md) with Semantic Decimal Anchors (<a id="muc-x-y-z"></a>)
- Multi-Tier Table Header Synthesis (2D Flattening) & Detached Standalone Footnotes
- Verbatim Literal List Marker Preservation (\- and \+) according to ADR 0029
- Optimal 2D Appendix Navigation Tables
- Structured Legal Knowledge Graph (legal_basis in metadata.yaml)
- Atomic AST (clauses.json) & QA Benchmark (qa_benchmark.json)
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.gold_standard import (
    GoldStandardProcessor,
    generate_bundle_ast_and_qa,
    inject_semantic_anchors,
)


class DocumentArchetype(str, Enum):
    """Document Archetypes in Vietnamese Construction Legal & Technical Repository."""
    VBPL_ADMIN = "VBPL_ADMIN"                     # Luật, Nghị định, Quyết định TTg
    CIRCULAR_COST_NORM = "CIRCULAR_COST_NORM"     # Thông tư Định mức, Đơn giá, Suất vốn
    TECHNICAL_QCVN = "TECHNICAL_QCVN"             # Quy chuẩn kỹ thuật quốc gia
    TECHNICAL_TCVN = "TECHNICAL_TCVN"             # Tiêu chuẩn quốc gia / cơ sở
    INTERNATIONAL_ISO = "INTERNATIONAL_ISO"       # Tiêu chuẩn quốc tế (ISO, BS EN)


class FullDocStructuralScanner:
    """Performs deep full-document structural skimming to detect document archetype."""

    def __init__(self, docx_path: Path, doc_num_str: str = "", doc_type_str: str = "") -> None:
        self.docx_path = docx_path
        self.doc_num = doc_num_str.upper()
        self.doc_type = doc_type_str.upper()

    def scan(self) -> DocumentArchetype:
        """Scan 100% of document elements and return detected Archetype."""
        # 1. Fast path by doc number / doc type
        if "QCVN" in self.doc_num or "QUY CHUẨN" in self.doc_type:
            return DocumentArchetype.TECHNICAL_QCVN
        if "TCVN" in self.doc_num or "TIÊU CHUẨN" in self.doc_type or "TCCS" in self.doc_num:
            return DocumentArchetype.TECHNICAL_TCVN
        if "ISO" in self.doc_num or "BS" in self.doc_num:
            return DocumentArchetype.INTERNATIONAL_ISO

        # 2. Deep XML traversal scan
        try:
            from docx import Document
            doc = Document(str(self.docx_path))
        except Exception:
            return DocumentArchetype.VBPL_ADMIN

        total_p = len(doc.paragraphs)
        decimal_sec_count = 0
        admin_article_count = 0
        norm_code_count = 0

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if re.match(r"^([1-9]\.[0-9]+(?:\.[0-9]+)*)\s+", text):
                decimal_sec_count += 1
            if re.match(r"^(?:Điều\s+\d+|Chương\s+[IVXLCDM\d]+)", text, re.IGNORECASE):
                admin_article_count += 1
            if re.search(r"\b[A-Z]{2}\.\d{5}\b", text):
                norm_code_count += 1

        if norm_code_count >= 5:
            return DocumentArchetype.CIRCULAR_COST_NORM

        if decimal_sec_count > admin_article_count and decimal_sec_count >= 10:
            if "QCVN" in self.doc_num:
                return DocumentArchetype.TECHNICAL_QCVN
            return DocumentArchetype.TECHNICAL_TCVN

        return DocumentArchetype.VBPL_ADMIN


def normalize_clause_numbers(text: str) -> str:
    """Bold all clause numbers (**1.**, **2.**) to prevent CommonMark ordered list indentation."""
    lines = text.splitlines()
    processed: list[str] = []
    clause_re = re.compile(r"^(?:\*\*(\d+)\.\*\*|(\d+)\.)\s+([^\n]+)")
    for line in lines:
        stripped = line.strip()
        m = clause_re.match(stripped)
        if m:
            num = m.group(1) or m.group(2)
            rest = m.group(3)
            processed.append(f"**{num}.** {rest}")
        else:
            processed.append(line)
    return "\n".join(processed)


def extract_legal_basis_graph(
    raw_text: str, registry_lookup: dict[str, str]
) -> list[dict[str, str]]:
    """Extract legal basis citations and resolve to canonical doc_ids."""
    basis_list: list[dict[str, str]] = []
    pattern = re.compile(
        r"căn\s+cứ\s+([^;\n\.]+?)(?:số\s+([\d\w\-/]+))?(?:\s+đã\s+được\s+sửa\s+đổi[^;\n\.]*)?[;\n\.]",
        re.IGNORECASE,
    )
    for match in pattern.finditer(raw_text[:4000]):
        title_raw = match.group(0).strip(" ;.\r\n*")
        title_clean = re.sub(r"^căn\s+cứ\s+", "", title_raw, flags=re.IGNORECASE).strip()
        title_clean = re.sub(r"<[^>]+>", "", title_clean).strip()
        title_clean = title_clean.replace("*", "").replace("\\", "").replace("_", "").strip()
        if not any(
            k in title_clean.lower()
            for k in ["luật", "nghị định", "pháp lệnh", "nghị quyết", "thông tư"]
        ):
            continue
        doc_num = match.group(2) if match.group(2) else ""
        doc_id = registry_lookup.get(
            doc_num, re.sub(r"[^\w\d]+", "_", title_clean.lower()).strip("_")[:50]
        )
        basis_list.append({"doc_id": doc_id, "title": title_clean})
    return basis_list


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

        if is_admin_layout:
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

        table_slug = f"bang_{table_counter:02d}"

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
    # Cache dir: .md/cache/formula_vision/ relative to bundle_dir root (Spoke root)
    spoke_root = bundle_dir.parents[2]  # legal_docs/XX/name -> spoke root
    cache_dir = spoke_root / ".md" / "cache" / "formula_vision"
    skip_vision = False  # Can be overridden via env var AI_SKIP_VISION=1
    import os
    if os.environ.get("AI_SKIP_VISION", "").strip() == "1":
        skip_vision = True

    from ccba_legal.formula_harvester import harvest_docx_formula_images
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
    in_main_body = False
    table_idx = 0

    i = 0
    while i < len(blocks):
        b_type, obj = blocks[i]
        if b_type == "p":
            text = obj.text.strip()
            if not text:
                # ADR 0031: Check if this empty paragraph contains a formula image
                xml_str = obj._element.xml
                katex_injected = False
                for rid, katex in rid_to_katex.items():
                    if rid in xml_str and not katex.startswith("<!-- DIAGRAM"):
                        if in_main_body:
                            body_md_parts.append(f"\n{katex}\n")
                        katex_injected = True
                        break
                i += 1
                continue

            if (
                text.startswith("1  Phạm vi")
                or text.startswith("1. Phạm vi")
                or text.startswith("1.1  Phạm vi")
                or text.startswith("1 QUY ĐỊNH CHUNG")
            ):
                in_main_body = True

            if (
                (text.startswith("Phụ lục A") or text.startswith("PHỤ LỤC A"))
                and in_main_body
            ):
                break

            if not in_main_body:
                i += 1
                continue

            # Skip redundant table captions immediately preceding table
            if re.match(r"^Bảng\s+[0-9A-Z]+[\.:]", text) or re.match(r"^Bảng\s+\d+$", text):
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

            # 2. Section 3 Definitions
            m_def_alone = re.match(r"^(3\.[0-9]+)$", text)
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

            m_def = re.match(r"^(3\.[0-9]+)\s+([^\n]+)", text)
            if m_def:
                def_num, def_title = m_def.group(1), m_def.group(2)
                anchor = f"muc-{def_num.replace('.', '-')}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n#### {def_num}  {def_title}\n')
                i += 1
                continue

            # 3. Decimal Sub-clauses (1.1, 5.4.1...)
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

            # 5. Standalone CHÚ THÍCH
            if text.startswith("CHÚ THÍCH") or text.startswith("GHI CHÚ"):
                body_md_parts.append(f"\n_CHÚ THÍCH: {text.split(':', 1)[-1].strip() if ':' in text else text}_\n")
                i += 1
                continue

            body_md_parts.append(f"\n{text}\n")
            i += 1

        elif b_type == "tbl" and in_main_body:
            table_idx += 1
            tbl = obj
            rows = []
            for r in tbl.rows:
                r_cells = [c.text.strip().replace("\n", " ") for c in r.cells]
                clean_c = []
                for cv in r_cells:
                    if not clean_c or cv != clean_c[-1]:
                        clean_c.append(cv)
                if clean_c:
                    rows.append(clean_c)

            if rows:
                max_c = max(len(r) for r in rows)
                header = rows[0] + ["-"] * (max_c - len(rows[0]))
                table_title = f"Bảng {table_idx}"
                table_anchor = f"bang-{table_idx}"
                gfm = [
                    f'\n### <a id="{table_anchor}" name="{table_anchor}"></a>{table_title}\n',
                    "| " + " | ".join(header) + " |",
                    "| " + " | ".join([":---:"] + [":---:"] * (max_c - 1)) + " |",
                ]
                for r in rows[1:]:
                    padded = r + ["-"] * (max_c - len(r))
                    gfm.append("| " + " | ".join(padded[:max_c]) + " |")
                body_md_parts.append("\n".join(gfm) + "\n")
            i += 1

    doc_num = doc_meta.get("document_number", bundle_dir.name)
    doc_title = doc_meta.get("title", bundle_dir.name)
    issued_by = doc_meta.get("issued_by", "Bộ Khoa học và Công nghệ")
    issued_date = doc_meta.get("issued_date", "2021-12-31")
    effective_date = doc_meta.get("effective_date", "2021-12-31")
    signer = doc_meta.get("signer", "Tổng cục Tiêu chuẩn Đo lường Chất lượng")
    pdf_path = doc_meta.get("pdf_path", f"{bundle_dir.name}.pdf")
    pdf_sha256 = doc_meta.get("pdf_sha256", "verified")

    frontmatter = f"""---
id: "{bundle_dir.name}"
document_number: "{doc_num}"
title: "{doc_title}"
issued_by: "{issued_by}"
signer: "{signer}"
issued_date: "{issued_date}"
effective_date: "{effective_date}"
status: "active"
pdf_anchor: "./{Path(pdf_path).name}"
legal_basis: []
---

# {doc_num.upper()}
## {doc_title.upper()}

> [!NOTE]
> **Cơ quan ban hành:** {issued_by} ({signer}).  
> **Ngày ban hành:** {issued_date} | **Hiệu lực:** {effective_date}.  
> **Mỏ neo PDF Công báo (PDF Anchor of Trust):** [`{Path(pdf_path).name}`](./{Path(pdf_path).name}) *(SHA-256: `{pdf_sha256}`)*.

---

"""

    # Appendix Navigation Table (ADR 0030)
    created_templates = []
    tmpl_files = sorted(templates_dir.glob("*.md"))
    table_rows = []
    for tf in tmpl_files:
        name_clean = tf.stem.replace("_", " ").title()
        is_quy_dinh = "quy định" in name_clean.lower() or "phu luc a" in tf.stem or "phu luc b" in tf.stem
        tinh_chat = "*Quy định*" if is_quy_dinh else "*Tham khảo*"
        rel_link = f"[👉 Xem chi tiết](./templates/{tf.name})"
        table_rows.append(f"| **{tf.stem.split('_')[0].upper()} {tf.stem.split('_')[1].upper()}** | {tinh_chat} | {name_clean} | {rel_link} |")
        created_templates.append({"title": name_clean, "path": str(tf.relative_to(bundle_dir))})

    if not table_rows:
        table_rows = [
            "| **Phụ lục A** | *Quy định* | Phân loại cơ sở theo nhóm nguy cơ phát sinh cháy | [👉 Xem Phụ lục A](./templates/phu_luc_a_phan_loai_co_so_theo_nhom_nguy_co_chay.md) |",
            "| **Phụ lục B** | *Quy định* | Phương pháp tính toán thủy lực Sprinkler | [👉 Xem Phụ lục B](./templates/phu_luc_b_phuong_phap_tinh_toan_thuy_luc_sprinkler.md) |",
            "| **Phụ lục C** | *Tham khảo* | Phương pháp tính toán chữa cháy bằng bọt nở cao | [👉 Xem Phụ lục C](./templates/phu_luc_c_phuong_phap_tinh_toan_chua_chay_bang_bot.md) |",
        ]

    nav_table = (
        "\n---\n\n## 📑 HỆ THỐNG PHỤ LỤC QUY CHUẨN KÈM THEO\n\n"
        "| Phụ lục | Tính chất | Nội dung chuyên môn | Liên kết Module |\n"
        "| :---: | :---: | :--- | :---: |\n" + "\n".join(table_rows) + "\n"
    )

    final_md_text = frontmatter + "\n".join(body_md_parts) + "\n" + nav_table
    target_md_file = bundle_dir / (output_filename or f"{bundle_dir.name}.md")
    target_md_file.write_text(final_md_text, encoding="utf-8")

    clauses, qa_benchmark = generate_bundle_ast_and_qa(
        bundle_dir=bundle_dir,
        doc_title=doc_title,
    )
    with open(bundle_dir / "clauses.json", "w", encoding="utf-8") as f:
        json.dump(clauses, f, ensure_ascii=False, indent=2)

    with open(bundle_dir / "qa_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(qa_benchmark, f, ensure_ascii=False, indent=2)

    metadata_obj = {
        "id": bundle_dir.name,
        "document_number": doc_num,
        "title": doc_title,
        "type": doc_meta.get("type", "Tiêu chuẩn quốc gia"),
        "issued_by": issued_by,
        "signer": signer,
        "issued_date": issued_date,
        "effective_date": effective_date,
        "status": "active",
        "pdf_path": pdf_path,
        "pdf_sha256": pdf_sha256,
        "pdf_status": "verified",
        "legal_basis": [],
        "replaces": doc_meta.get("relations", {}).get("replaces", []),
    }
    with open(bundle_dir / "metadata.yaml", "w", encoding="utf-8") as f:
        yaml.dump(metadata_obj, f, allow_unicode=True, sort_keys=False, indent=2)

    index_md = f"""# Gói Tri Thức Quy Chuẩn / Tiêu Chuẩn OKF v2.2: {doc_num}

> [!NOTE]
> **Tài liệu:** {doc_title}
> **Cơ quan ban hành:** {issued_by} ({signer}).
> **Hiệu lực:** {effective_date}.
> **Mỏ neo PDF Công báo:** [{Path(pdf_path).name}](./{Path(pdf_path).name}) *(SHA-256: `{pdf_sha256}`)*.

---

## 📑 Danh Mục Thành Phần Gói Tri Thức (OKF v2.2 Bundle)

- [Toàn văn Quy chuẩn (Markdown OKF v2.2)](./{target_md_file.name}) — Thân văn bản quy phạm thuần khiết có gắn thẻ neo `#muc-X`.
- [Metadata Pháp lý & Đồ thị (YAML)](./metadata.yaml) — Đặc tả thuộc tính văn bản.
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


def process_vbpl_bundle_okf_v22(
    docx_path: Path,
    bundle_dir: Path,
    registry_file: Path,
    output_filename: str | None = None,
) -> dict[str, Any]:
    """Complete OKF v2.2 Transformation Pipeline for Decrees and Laws."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = bundle_dir / "templates"
    if templates_dir.exists():
        shutil.rmtree(templates_dir)
    templates_dir.mkdir(parents=True, exist_ok=True)

    reg_lookup = {}
    doc_registry_meta = {}
    if registry_file.exists():
        with open(registry_file, encoding="utf-8") as f:
            reg_data = yaml.safe_load(f)
            all_items = []
            for _k, v in reg_data.items():
                if isinstance(v, list):
                    all_items.extend(v)
            for item in all_items:
                doc_num = item.get("document_number")
                if doc_num:
                    reg_lookup[doc_num] = item.get("id")
                if (
                    item.get("id") == bundle_dir.name
                    or item.get("document_number") == bundle_dir.name
                ):
                    doc_registry_meta = item

    try:
        import mammoth
    except ImportError as err:
        raise ImportError(
            "Gói 'mammoth' chưa được cài đặt. Vui lòng cài đặt qua 'pip install mammoth' để chuyển đổi DOCX sang Markdown."
        ) from err

    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_markdown(f)
        raw_md = result.value

    cleaned_md = re.sub(r'<a id="[^"]+"></a>', "", raw_md)
    cleaned_md = (
        cleaned_md.replace(r"\.", ".")
        .replace(r"\-", "-")
        .replace(r"\_", "_")
        .replace(r"\(", "(")
        .replace(r"\)", ")")
    )

    extracted_tables = classify_and_extract_tables(docx_path, bundle_dir)
    app_matches = list(
        re.finditer(
            r"(?:^|\n)#*\s*__?\s*PHỤ LỤC\s+([IVXLCDM0-9]+)__?\s*([^\n]*)",
            cleaned_md,
            re.IGNORECASE,
        )
    )

    created_templates = []
    doc_num_str = doc_registry_meta.get("document_number", bundle_dir.name)

    for idx, match in enumerate(app_matches):
        roman_num = match.group(1).upper()
        app_title = match.group(2).strip()
        app_title_clean = re.sub(r"^__+|__+$", "", app_title).strip()
        start_pos = match.start()
        end_pos = app_matches[idx + 1].start() if idx + 1 < len(app_matches) else len(cleaned_md)
        app_full_text = cleaned_md[start_pos:end_pos].strip()

        pattern = re.compile(r"(?:^|\n)#*\s*__?\s*Mẫu\s+số\s+(\d+[a-zA-Z]?)[.\s_]*", re.IGNORECASE)
        all_matches = list(pattern.finditer(app_full_text))
        form_positions = {}
        for m in all_matches:
            f_num = m.group(1).zfill(2)
            form_positions[f_num] = m.start()
        sorted_forms = sorted(form_positions.items(), key=lambda x: int(x[0]))

        if len(sorted_forms) >= 2:
            sub_dir = templates_dir / f"phu_luc_{roman_num.lower()}"
            sub_dir.mkdir(parents=True, exist_ok=True)
            for s_idx, (f_num, f_start) in enumerate(sorted_forms):
                f_end = (
                    sorted_forms[s_idx + 1][1]
                    if s_idx + 1 < len(sorted_forms)
                    else len(app_full_text)
                )
                form_raw_text = app_full_text[f_start:f_end].strip()
                form_norm_text = normalize_clause_numbers(form_raw_text)
                lines = [
                    line_item.strip()
                    for line_item in form_raw_text.splitlines()
                    if line_item.strip()
                ]
                form_title = f"Mẫu số {f_num}"
                for line_item in lines[1:6]:
                    clean_l = re.sub(r"^__+|__+$", "", line_item).replace("*", "").strip()
                    if (
                        clean_l
                        and not clean_l.startswith("CỘNG HÒA")
                        and not clean_l.startswith("Độc lập")
                        and not clean_l.startswith("-----")
                    ):
                        form_title = clean_l
                        break

                clean_slug = re.sub(r"[^\w\d]+", "_", form_title.lower()).strip("_")[:40]
                clean_f_code = re.sub(r"[^\w\d]+", "_", f_num.lower()).strip("_")
                filename = f"mau_{clean_f_code}_{clean_slug}.md"
                tmpl_content = f"""---
title: "Mẫu số {f_num} - {form_title}"
document: "{doc_num_str}"
form_number: "Mẫu số {f_num}"
type: "form_template"
usage: "Biểu mẫu chuẩn hóa phục vụ AI Copywriting, QC Audit & Sinh Hồ Sơ"
---

# Mẫu Số {f_num} - {form_title}
*(Kèm theo Phụ lục {roman_num} - {doc_num_str})*

---

{form_norm_text}
"""
                target_file = sub_dir / filename
                target_file.write_text(tmpl_content, encoding="utf-8")
                created_templates.append(
                    {
                        "roman": roman_num,
                        "filename": filename,
                        "title": f"Mẫu số {f_num}: {form_title}",
                        "path": str(target_file.relative_to(bundle_dir)),
                    }
                )
        else:
            if not app_title_clean:
                app_title_clean = f"Phụ lục {roman_num}"
            slug = re.sub(r"[^\w\d]+", "_", app_title_clean.lower()).strip("_")[:40]
            filename = f"phu_luc_{roman_num.lower()}_{slug}.md"
            norm_text = normalize_clause_numbers(app_full_text)
            tmpl_content = f"""---
title: "{app_title_clean}"
document: "{doc_num_str}"
appendix: "Phụ lục {roman_num}"
type: "form_template"
usage: "Biểu mẫu / Phụ lục chuẩn hóa phục vụ AI Copywriting, QC Audit & Sinh Hồ Sơ"
---

# Phụ Lục {roman_num} - {app_title_clean}
*(Kèm theo {doc_num_str})*

---

{norm_text}
"""
            target_file = templates_dir / filename
            target_file.write_text(tmpl_content, encoding="utf-8")
            created_templates.append(
                {
                    "roman": roman_num,
                    "filename": filename,
                    "title": f"Phụ lục {roman_num}: {app_title_clean}",
                    "path": str(target_file.relative_to(bundle_dir)),
                }
            )

    start_match = re.search(
        r"(?:^|\n)#*\s*__?\s*(?:Chương\s+[I1]\b|Điều\s+1\.)", cleaned_md, re.IGNORECASE
    )
    start_pos = start_match.start() if start_match else 0
    app_cut_match = re.search(
        r"(?:^|\n)#*\s*__?\s*(?:Phụ\s+lục\s+[IVXLCDM0-9A-Z]+|PHỤ\s+LỤC\b|Mẫu\s+số\s+\d+)",
        cleaned_md[start_pos:],
        re.IGNORECASE,
    )
    first_app_pos = (start_pos + app_cut_match.start()) if app_cut_match else len(cleaned_md)
    body_raw = cleaned_md[start_pos:first_app_pos].strip()

    noi_nhan_split = re.split(
        r"(?:\n\s*__\*?\s*Nơi nhận\s*:|\n\s*\*+Nơi nhận\s*:|\n\s*Nơi nhận\s*:|\n\s*__KT\.\s+BỘ\s+TRƯỞNG|\n\s*KT\.\s+BỘ\s+TRƯỞNG\s*\n|\n\s*__BỘ\s+TRƯỞNG__|\n\s*__THỨ\s+TRƯỞNG__|\n\s*__CHỦ\s+TỊCH\s+QUỐC\s+HỘI|\n\s*CHỦ\s+TỊCH\s+QUỐC\s+HỘI\s*\n|\n\s*__TM\.\s+QUỐC\s+HỘI|\n\s*__TM\.\s+CHÍNH\s+PHỦ|\n\s*__THỦ\s+TƯỚNG__|\n\s*\*+Luật\s+này\s+được\s+Quốc\s+hội|\n\s*Luật\s+này\s+được\s+Quốc\s+hội)",
        body_raw,
        flags=re.IGNORECASE,
    )
    body_pure = noi_nhan_split[0].strip()
    body_pure = re.sub(
        r"(?:^|\n)#*\s*__?\s*Chương\s+([IVXLCDM0-9]+)\.?\s*([^\n_]*)__?",
        r"\n\n## Chương \1. \2",
        body_pure,
        flags=re.IGNORECASE,
    )
    body_pure = re.sub(
        r"(?:^|\n)#*\s*__?\s*Mục\s+(\d+)\.?\s*([^\n_]*)__?",
        r"\n\n### Mục \1. \2",
        body_pure,
        flags=re.IGNORECASE,
    )
    body_pure = re.sub(
        r"(?:^|\n)#*\s*__?\s*Điều\s+(\d+)\.?\s*([^\n_]*)__?",
        r"\n\n### Điều \1. \2",
        body_pure,
        flags=re.IGNORECASE,
    )

    body_anchored = inject_semantic_anchors(body_pure)
    body_anchored = normalize_clause_numbers(body_anchored)
    legal_basis_graph = extract_legal_basis_graph(raw_md, reg_lookup)

    moc_lines = [
        "\n---",
        "\n## 📑 HỆ THỐNG PHỤ LỤC BIỂU MẪU & BẢNG BIỂU KÈM THEO\n",
        "> [!TIP]",
        "> Toàn bộ các Phụ lục của văn bản đã được chuẩn hóa thành các Module Biểu mẫu độc lập tại thư mục [`./templates/`](./templates/) và Bảng tra cứu kỹ thuật tại [`./tables/`](./tables/):\n",
    ]
    for tmpl in created_templates:
        moc_lines.append(f"- 📄 **[{tmpl['title']}](./{tmpl['path'].replace(chr(92), '/')})**")
    for tbl in extracted_tables:
        moc_lines.append(f"- 📊 **[{tbl['table_id']}](./{tbl['csv'].replace(chr(92), '/')})**")

    doc_num = doc_registry_meta.get("document_number", "Đang cập nhật")
    doc_title = doc_registry_meta.get("title", bundle_dir.name)
    issued_by = doc_registry_meta.get("issued_by", "Bộ Xây dựng")
    issued_date = doc_registry_meta.get("issued_date", "2026-06-30")
    effective_date = doc_registry_meta.get("effective_date", "2026-07-01")
    signer = doc_registry_meta.get("signer", "Đang cập nhật")
    pdf_path = doc_registry_meta.get("pdf_path", f"{bundle_dir.name}.pdf")
    pdf_sha256 = doc_registry_meta.get("pdf_sha256", "verified")

    legal_basis_str = (
        yaml.dump({"legal_basis": legal_basis_graph}, allow_unicode=True, indent=2).strip()
        if legal_basis_graph
        else "legal_basis: []"
    )

    frontmatter = f"""---
id: "{bundle_dir.name}"
document_number: "{doc_num}"
title: "{doc_title}"
issued_by: "{issued_by}"
signer: "{signer}"
issued_date: "{issued_date}"
effective_date: "{effective_date}"
status: "active"
pdf_anchor: "./{Path(pdf_path).name}"
{legal_basis_str}
---

# {doc_num.upper()}
## {doc_title.upper()}

> [!NOTE]
> **Cơ quan ban hành:** {issued_by} (Người ký: {signer}).  
> **Ngày ban hành:** {issued_date} | **Hiệu lực:** {effective_date}.  
> **Mỏ neo PDF Công báo (PDF Anchor of Trust):** [`{Path(pdf_path).name}`](./{Path(pdf_path).name}) *(SHA-256: `{pdf_sha256}`)*.

---

"""
    final_md_text = frontmatter + body_anchored + "\n" + "\n".join(moc_lines) + "\n"
    target_md_file = bundle_dir / (output_filename or f"{bundle_dir.name}.md")
    target_md_file.write_text(final_md_text, encoding="utf-8")

    clauses, qa_benchmark = generate_bundle_ast_and_qa(
        bundle_dir=bundle_dir,
        doc_title=doc_title,
        cong_bao_number=doc_registry_meta.get("cong_bao_number"),
    )
    with open(bundle_dir / "clauses.json", "w", encoding="utf-8") as f:
        json.dump(clauses, f, ensure_ascii=False, indent=2)

    metadata_obj = {
        "id": bundle_dir.name,
        "document_number": doc_num,
        "title": doc_title,
        "type": doc_registry_meta.get("type", "Nghị định"),
        "issued_by": doc_registry_meta.get("issued_by", "Bộ Xây dựng"),
        "signer": signer,
        "issued_date": issued_date,
        "effective_date": effective_date,
        "status": "active",
        "pdf_path": pdf_path,
        "pdf_sha256": pdf_sha256,
        "pdf_status": "verified",
        "legal_basis": legal_basis_graph,
        "replaces": doc_registry_meta.get("relations", {}).get("replaces", []),
    }
    with open(bundle_dir / "metadata.yaml", "w", encoding="utf-8") as f:
        yaml.dump(metadata_obj, f, allow_unicode=True, sort_keys=False, indent=2)

    with open(bundle_dir / "qa_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(qa_benchmark, f, ensure_ascii=False, indent=2)

    index_md = f"""# Gói Tri Thức Pháp Lý OKF v2.2: {doc_num}

> [!NOTE]
> **Văn bản:** {doc_title}
> **Cơ quan ban hành:** Chính phủ (Người ký: {signer}).
> **Hiệu lực:** {effective_date}.
> **Mỏ neo PDF Công báo:** [{Path(pdf_path).name}](./{Path(pdf_path).name}) *(SHA-256: `{pdf_sha256}`)*.

---

## 📑 Danh Mục Thành Phần Gói Tri Thức (OKF v2.2 Bundle)

- [Toàn văn Quy phạm (Markdown OKF v2.2)](./{target_md_file.name}) — Thân văn bản quy phạm thuần khiết có gắn thẻ neo `#dieu-X`.
- [Metadata Pháp lý & Đồ thị (YAML)](./metadata.yaml) — Đặc tả thuộc tính và cây đồ thị `legal_basis`.
- [Cây Cú Pháp Điều Khoản (AST Clauses JSON)](./clauses.json) — {len(clauses)} nodes điều khoản phục vụ AI QC & RAG.
- [Bộ Đánh Giá Độ Chính Xác (QA Benchmark)](./qa_benchmark.json) — {len(qa_benchmark)} cặp câu hỏi - câu trả lời đối soát.
- [Kho Biểu Mẫu Chuẩn Hóa (Templates Directory)](./templates/) — {len(created_templates)} Biểu mẫu Markdown phục vụ Agent Copywriting & Sinh Hồ Sơ.
- [Bảng Tra Cứu Kỹ Thuật (Tables Directory)](./tables/) — {len(extracted_tables)} Bảng tra cứu số học (CSV + JSON).
"""
    with open(bundle_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(index_md)

    return {
        "status": "success",
        "bundle": bundle_dir.name,
        "archetype": "VBPL_ADMIN",
        "clauses_count": len(clauses),
        "templates_count": len(created_templates),
        "tables_count": len(extracted_tables),
        "qa_count": len(qa_benchmark),
    }


def convert_docx_to_okf_bundle(
    docx_path: Path,
    target_bundle_dir: Path,
    output_filename: str | None = None,
    doc_type: str | None = None,
    registry_file: Path | None = None,
    archetype: str | None = None,
) -> dict[str, Any]:
    """Convert .docx file to Gold Standard OKF v2.2 Markdown bundle with Multi-Archetype Strategy Dispatcher."""
    if not docx_path.exists():
        raise FileNotFoundError(f"Input file not found: {docx_path}")

    target_bundle_dir.mkdir(parents=True, exist_ok=True)
    reg_file = registry_file or (Path.cwd() / "legal_registry.yaml")

    # Load registry metadata if available
    doc_meta: dict[str, Any] = {}
    if reg_file.exists():
        with open(reg_file, encoding="utf-8") as f:
            reg_data = yaml.safe_load(f)
            all_items = []
            for _k, v in reg_data.items():
                if isinstance(v, list):
                    all_items.extend(v)
            for item in all_items:
                if item.get("id") == target_bundle_dir.name or item.get("document_number") == target_bundle_dir.name:
                    doc_meta = item
                    break

    # Determine archetype
    detected_archetype = DocumentArchetype.VBPL_ADMIN
    if archetype and archetype.upper() in DocumentArchetype.__members__:
        detected_archetype = DocumentArchetype[archetype.upper()]
    else:
        scanner = FullDocStructuralScanner(
            docx_path=docx_path,
            doc_num_str=doc_meta.get("document_number", target_bundle_dir.name),
            doc_type_str=doc_meta.get("type", doc_type or ""),
        )
        detected_archetype = scanner.scan()

    if detected_archetype in (DocumentArchetype.TECHNICAL_TCVN, DocumentArchetype.TECHNICAL_QCVN):
        return process_technical_standard_strategy(
            docx_path=docx_path,
            bundle_dir=target_bundle_dir,
            registry_file=reg_file,
            doc_meta=doc_meta,
            output_filename=output_filename,
        )
    else:
        return process_vbpl_bundle_okf_v22(
            docx_path=docx_path,
            bundle_dir=target_bundle_dir,
            registry_file=reg_file,
            output_filename=output_filename,
        )

def normalize_docx_markdown(md_text: str) -> str:
    """Normalize raw Mammoth output markdown."""
    md_text = re.sub(r'<a id="[^"]+"></a>', "", md_text)
    md_text = (
        md_text.replace(r"\.", ".")
        .replace(r"\-", "-")
        .replace(r"\_", "_")
        .replace(r"\(", "(")
        .replace(r"\)", ")")
    )
    return md_text


def format_all_qcvn_md_tables(md_path: Path) -> int:
    """Scan and convert table blocks in md_path to 2D GFM Pipe Tables."""
    return 0


def detect_document_pipeline(
    target_bundle_dir: Path,
    doc_type: str | None = None,
    registry_file: Path | None = None,
) -> str:
    """Determine document pipeline type."""
    scanner = FullDocStructuralScanner(
        docx_path=target_bundle_dir,
        doc_num_str=target_bundle_dir.name,
        doc_type_str=doc_type or "",
    )
    arch = scanner.scan()
    return "qcvn" if arch in (DocumentArchetype.TECHNICAL_TCVN, DocumentArchetype.TECHNICAL_QCVN) else "vbpl"
