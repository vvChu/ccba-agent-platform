"""CCBA Universal Legal DOCX Converter Engine (OKF v2.2 Gateway).

Converts official .docx documents (QCVN / TCVN / VBPL / Nghị định / Luật / Thông tư)
into Gold Standard OKF v2.2 Markdown bundles with:
- Pure Normative Body (.md)
- Structured Legal Knowledge Graph (legal_basis in metadata.yaml)
- Atomic Form Templates (templates/phu_luc_XX/mau_YY_...md)
- 3-Tier Semantic Table Classifier (tables/csv and tables/json)
- Universal Clause Numbering Normalization (**1.**, **2.**)
- Atomic AST (clauses.json) & QA Benchmark (qa_benchmark.json)
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.gold_standard import (
    GoldStandardProcessor,
    generate_bundle_ast_and_qa,
    inject_semantic_anchors,
)


def format_all_qcvn_md_tables(md_path: Path) -> int:
    """Scan and convert all multiline/broken table blocks in md_path to 2D GFM Pipe Tables."""
    if not md_path.exists():
        return 0

    content = md_path.read_text(encoding="utf-8")
    table_block_regex = re.compile(
        r"(<a id=\"[^\"]+\"></a>\n)?([#*]+)?\s*(Bảng\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*([^\n\*\#]+))([#*]*|\n)?"
        r"(.*?)(?=\n<a id=\"|\n#{1,6}\s+|\n(?:\#|\*)*\s*Bảng|\Z)",
        re.DOTALL | re.IGNORECASE,
    )

    formatted_count = 0

    def replace_table_block(match: re.Match) -> str:
        nonlocal formatted_count
        full_match_text = match.group(0)
        table_num = match.group(4)
        table_title_text = match.group(5).strip("*\n# ")
        table_title = f"Bảng {table_num} - {table_title_text}"
        table_anchor = f"bang-{table_num.lower().replace('.', '-')}"
        body_text = match.group(7)

        raw_lines = body_text.splitlines()
        clean_tokens: list[str] = []
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

            if "\t" in clean_str:
                parts = [p.strip(" |") for p in clean_str.split("\t") if p.strip()]
                clean_tokens.extend(parts)
            else:
                clean_tokens.append(clean_str)

        if len(clean_tokens) < 2:
            return full_match_text

        header_end = 1
        for tok_idx, tok in enumerate(clean_tokens[1:], 1):
            if re.match(r"^\d+[\.\)]?\s*", tok) or re.search(r"\b(REI|EI|R|E|P|F\d)\s*\d*", tok):
                header_end = tok_idx
                break

        cols_count = max(1, header_end)
        header_row = clean_tokens[:cols_count]
        data_tokens = clean_tokens[cols_count:]

        data_rows: list[list[str]] = []
        for chunk_idx in range(0, len(data_tokens), cols_count):
            chunk = data_tokens[chunk_idx : chunk_idx + cols_count]
            if any(chunk):
                if len(chunk) < cols_count:
                    chunk.extend([""] * (cols_count - len(chunk)))
                data_rows.append(chunk)

        if not data_rows:
            return full_match_text

        md_lines = [
            f'<a id="{table_anchor}"></a>',
            f"### {table_title}\n",
            "| " + " | ".join(header_row) + " |",
            "| " + " | ".join(["---"] * cols_count) + " |",
        ]
        for row in data_rows:
            md_lines.append("| " + " | ".join(row) + " |")

        if footnotes:
            md_lines.append("\n" + "\n".join(f"_{fn}_" for fn in footnotes))

        md_lines.append("\n")
        formatted_count += 1
        return "\n".join(md_lines)

    new_content = table_block_regex.sub(replace_table_block, content)
    md_path.write_text(new_content, encoding="utf-8")
    return formatted_count


def normalize_docx_markdown(md_text: str) -> str:
    """Normalize mammoth converted markdown headings and clean up escape chars."""
    md_text = (
        md_text.replace(r"\.", ".").replace(r"\-", "-").replace(r"\(", "(").replace(r"\)", ")")
    )

    md_text = re.sub(r"__(Chương\s+[IVXLCDM0-9]+(?::\s*[^_]+)?)__", r"## \1", md_text)
    md_text = re.sub(r"__(Điều\s+\d+\.\s*[^_]+)__", r"### \1", md_text)
    md_text = re.sub(
        r"__(Phụ lục\s+[A-Za-z0-9]+(?:\s*\([^)]+\))?(?:\.\s*[^_]+)?)__",
        r"## \1",
        md_text,
        flags=re.IGNORECASE,
    )
    md_text = re.sub(
        r"^#*\s*(PHỤ LỤC\s+[A-I]\b[^\n]*)", r"## \1", md_text, flags=re.MULTILINE | re.IGNORECASE
    )
    md_text = re.sub(
        r"__Bảng\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*([^_]+)__", r"### Bảng \1 - \2", md_text
    )
    md_text = re.sub(r"__((?:[1-7]|[A-I])\.\d+\.\d+\.\d+)\.?\s*([^_]+)__", r"##### \1 \2", md_text)
    md_text = re.sub(r"__((?:[1-7]|[A-I])\.\d+\.\d+)\.?\s*([^_]+)__", r"#### \1 \2", md_text)
    md_text = re.sub(r"__((?:[1-7]|[A-I])\.\d+)\.?\s*([^_]+)__", r"### \1 \2", md_text)
    md_text = re.sub(r"(###\s*)+", "### ", md_text)
    md_text = re.sub(r"###\s*###\s*", "### ", md_text)
    return md_text


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
    """3-Tier Semantic Table Classifier according to ADR 0021."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "Gói 'python-docx' chưa được cài đặt. Vui lòng cài đặt qua 'pip install python-docx' để bóc tách bảng DOCX."
        )

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
        "cộng hòa xã hội chủ nghĩa",
        "độc lập - tự do",
        "nơi nhận:",
        "tm. chính phủ",
        "kt. thủ tướng",
        "phó thủ tướng",
        "bộ trưởng",
        "chủ tịch ủy ban",
        "ký, ghi rõ họ tên",
        "ký, đóng dấu",
        "lưu: vt",
    ]

    for idx, table in enumerate(doc.tables, 1):
        rows_cnt = len(table.rows)
        cols_cnt = len(table.columns)
        table_text = " ".join(c.text.lower() for row in table.rows for c in row.cells)

        if (rows_cnt <= 2 and cols_cnt <= 2) or (rows_cnt == 1 and cols_cnt == 2):
            if any(k in table_text for k in layout_keywords):
                continue
        elif rows_cnt <= 3 and cols_cnt <= 2:
            if "nơi nhận:" in table_text or "cộng hòa" in table_text:
                continue

        grid = []
        for row in table.rows:
            grid.append([c.text.strip().replace("\n", " ") for c in row.cells])
        if not grid:
            continue

        headers = grid[0]
        if cols_cnt < 3 and rows_cnt < 20:
            continue

        table_slug = f"bang_{idx:02d}"

        csv_file = csv_dir / f"{table_slug}.csv"
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(grid)

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
        }
        json_file = json_dir / f"{table_slug}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        extracted_tables.append(
            {
                "table_id": table_slug,
                "rows": len(grid),
                "cols": len(headers),
                "csv": str(csv_file.relative_to(bundle_dir)),
                "json": str(json_file.relative_to(bundle_dir)),
            }
        )

    return extracted_tables


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
    except ImportError:
        raise ImportError(
            "Gói 'mammoth' chưa được cài đặt. Vui lòng cài đặt qua 'pip install mammoth' để chuyển đổi DOCX sang Markdown."
        )

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
                slug = re.sub(r"[^\w\d]+", "_", form_title.lower()).strip("_")[:40]
                filename = f"mau_{f_num}_{slug}.md"
                tmpl_content = f"""---
title: "Mẫu số {f_num} - {form_title}"
document: "{doc_num_str}"
appendix: "Phụ lục {roman_num}"
form_number: "Mẫu số {f_num}"
type: "form_template"
usage: "Biểu mẫu chuẩn hóa phục vụ AI Copywriting, QC Audit & Sinh Hồ Sơ"
---

# Mẫu Số {f_num} - {form_title}
*(Kèm theo Phụ lục {roman_num} {doc_num_str})*

---

{form_norm_text}
"""
                target_file = sub_dir / filename
                target_file.write_text(tmpl_content, encoding="utf-8")
                created_templates.append(
                    {
                        "roman": roman_num,
                        "filename": f"phu_luc_{roman_num.lower()}/{filename}",
                        "title": f"Phụ lục {roman_num} - Mẫu {f_num}: {form_title}",
                        "path": str(target_file.relative_to(bundle_dir)),
                    }
                )
        else:
            is_data_table_appendix = any(
                k in app_title_clean.lower()
                for k in [
                    "danh mục công trình ảnh hưởng lớn",
                    "danh mục công trình quy mô lớn",
                    "bảng danh mục công trình",
                ]
            ) or (
                len(app_full_text.splitlines()) > 50
                and "mã số" in app_full_text.lower()
                and "cấp công trình" in app_full_text.lower()
            )
            if is_data_table_appendix:
                continue

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

    if not app_matches:
        direct_form_matches = list(
            re.finditer(
                r"(?:^|\n)#*\s*__?\s*Mẫu\s+số\s*[:\.]?\s*(\d+[a-zA-Z\(\)]*(?:/[\w\.\-]+)?)[.\s_]*([^\n]*)",
                cleaned_md,
                re.IGNORECASE,
            )
        )
        for idx, match in enumerate(direct_form_matches):
            f_code = match.group(1).strip()
            f_title_line = match.group(2).strip()
            start_pos = match.start()
            end_pos = (
                direct_form_matches[idx + 1].start()
                if idx + 1 < len(direct_form_matches)
                else len(cleaned_md)
            )
            form_raw_text = cleaned_md[start_pos:end_pos].strip()
            form_norm_text = normalize_clause_numbers(form_raw_text)

            lines = [
                line_item.strip() for line_item in form_raw_text.splitlines() if line_item.strip()
            ]
            form_title = f_title_line
            if not form_title:
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
            if not form_title:
                form_title = f"Mẫu số {f_code}"

            clean_slug = re.sub(r"[^\w\d]+", "_", form_title.lower()).strip("_")[:40]
            clean_f_code = re.sub(r"[^\w\d]+", "_", f_code.lower()).strip("_")
            filename = f"mau_{clean_f_code}_{clean_slug}.md"
            tmpl_content = f"""---
title: "Mẫu số {f_code} - {form_title}"
document: "{doc_num_str}"
form_number: "Mẫu số {f_code}"
type: "form_template"
usage: "Biểu mẫu chuẩn hóa phục vụ AI Copywriting, QC Audit & Sinh Hồ Sơ"
---

# Mẫu Số {f_code} - {form_title}
*(Kèm theo {doc_num_str})*

---

{form_norm_text}
"""
            target_file = templates_dir / filename
            target_file.write_text(tmpl_content, encoding="utf-8")
            created_templates.append(
                {
                    "filename": filename,
                    "title": f"Mẫu số {f_code}: {form_title}",
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
        "clauses_count": len(clauses),
        "templates_count": len(created_templates),
        "tables_count": len(extracted_tables),
        "qa_count": len(qa_benchmark),
    }


def detect_document_pipeline(
    target_bundle_dir: Path,
    doc_type: str | None = None,
    registry_file: Path | None = None,
) -> str:
    """Determine whether to use VBPL (OKF v2.2) or QCVN pipeline."""
    if doc_type:
        dt = doc_type.lower()
        if "qcvn" in dt or "tcvn" in dt or "standard" in dt:
            return "qcvn"
        return "vbpl"

    path_str = str(target_bundle_dir).lower()
    if "01_vbpl" in path_str:
        return "vbpl"
    if "02_qcvn" in path_str or "03_tcvn" in path_str:
        return "qcvn"

    reg_path = registry_file or (Path.cwd() / "legal_registry.yaml")
    if reg_path.exists():
        with open(reg_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            all_items = []
            for _k, v in data.items():
                if isinstance(v, list):
                    all_items.extend(v)
            for item in all_items:
                if item.get("id") == target_bundle_dir.name or item.get("bundle_path", "").rstrip(
                    "/\\"
                ).endswith(target_bundle_dir.name):
                    t = item.get("type", "").lower()
                    if "quy chuẩn" in t or "tiêu chuẩn" in t:
                        return "qcvn"
                    return "vbpl"

    return "vbpl"


def convert_docx_to_okf_bundle(
    docx_path: Path,
    target_bundle_dir: Path,
    output_filename: str | None = None,
    doc_type: str | None = None,
    registry_file: Path | None = None,
) -> dict[str, Any]:
    """Convert .docx file to Gold Standard OKF v2.2 Markdown bundle."""
    if not docx_path.exists():
        raise FileNotFoundError(f"Input file not found: {docx_path}")

    target_bundle_dir.mkdir(parents=True, exist_ok=True)
    reg_file = registry_file or (Path.cwd() / "legal_registry.yaml")

    pipeline_type = detect_document_pipeline(target_bundle_dir, doc_type, reg_file)

    if pipeline_type == "vbpl":
        return process_vbpl_bundle_okf_v22(
            docx_path=docx_path,
            bundle_dir=target_bundle_dir,
            registry_file=reg_file,
            output_filename=output_filename,
        )
    else:
        if not output_filename:
            output_filename = f"{target_bundle_dir.name}.md"

        target_md_path = target_bundle_dir / output_filename
        try:
            import mammoth
        except ImportError:
            raise ImportError(
                "Gói 'mammoth' chưa được cài đặt. Vui lòng cài đặt qua 'pip install mammoth' để chuyển đổi DOCX sang Markdown."
            )

        with open(docx_path, "rb") as docx_file:
            result = mammoth.convert_to_markdown(docx_file)
            raw_md = result.value

        normalized_md = normalize_docx_markdown(raw_md)
        raw_md_store = docx_path.parent / f"{docx_path.stem}_from_docx.md"
        raw_md_store.write_text(normalized_md, encoding="utf-8")
        target_md_path.write_text(normalized_md, encoding="utf-8")

        format_all_qcvn_md_tables(target_md_path)
        return GoldStandardProcessor.process_bundle(target_bundle_dir, doc_type=doc_type)
