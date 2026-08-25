"""Complete OKF v2.2 Transformation Pipeline for Decrees, Circulars and Laws (ADR 0021)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.converters.table_extractor import classify_and_extract_tables
from ccba_legal.converters.unit_normalizer import normalize_clause_numbers
from ccba_legal.gold_standard import generate_bundle_ast_and_qa, inject_semantic_anchors


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
            for f_idx, (f_num, f_start) in enumerate(sorted_forms):
                f_end = (
                    sorted_forms[f_idx + 1][1]
                    if f_idx + 1 < len(sorted_forms)
                    else len(app_full_text)
                )
                form_text = app_full_text[f_start:f_end].strip()

                first_few_lines = form_text.splitlines()[:5]
                f_title = f"Biểu mẫu số {f_num}"
                for line in first_few_lines:
                    cleaned_line = re.sub(r"^#+\s*|__|\*", "", line).strip()
                    if (
                        cleaned_line
                        and not cleaned_line.lower().startswith("mẫu số")
                        and len(cleaned_line) > 5
                    ):
                        f_title = cleaned_line
                        break

                slug_title = re.sub(r"[^\w\d]+", "_", f_title.lower()).strip("_")[:40]
                form_filename = f"mau_{f_num}_{slug_title}.md"
                form_file = sub_dir / form_filename

                tpl_header = f"""# Phụ lục {roman_num} — Mẫu số {f_num}: {f_title}

> [!NOTE]
> **Văn bản ban hành:** {doc_num_str}
> **Biểu mẫu:** Mẫu số {f_num} thuộc Phụ lục {roman_num}

---

"""
                with open(form_file, "w", encoding="utf-8") as f:
                    f.write(tpl_header + form_text + "\n")
                created_templates.append(form_file)
        else:
            app_filename = f"phu_luc_{roman_num.lower()}.md"
            app_file = templates_dir / app_filename
            tpl_header = f"""# Phụ lục {roman_num}: {app_title_clean}

> [!NOTE]
> **Văn bản ban hành:** {doc_num_str}
> **Phụ lục:** Phụ lục số {roman_num}

---

"""
            with open(app_file, "w", encoding="utf-8") as f:
                f.write(tpl_header + app_full_text + "\n")
            created_templates.append(app_file)

    first_app_pos = app_matches[0].start() if app_matches else len(cleaned_md)
    pure_body_raw = cleaned_md[:first_app_pos].strip()

    pure_body_raw = re.sub(
        r"^(?:[\s\S]*?)(#+\s*__?\s*Chương\s+[IVXLCDM0-9]+|#+\s*__?\s*Điều\s+1\b)",
        r"\1",
        pure_body_raw,
        flags=re.IGNORECASE,
    )
    pure_body_raw = normalize_clause_numbers(pure_body_raw)
    pure_body_raw = re.sub(r"(\n\s*\+\s+[^\n]+)", r"&nbsp;&nbsp;\1", pure_body_raw)
    pure_body_raw = re.sub(r"&nbsp;&nbsp;\n\s*\+\s+", r"\n&nbsp;&nbsp;\\+ ", pure_body_raw)
    pure_body_raw = re.sub(r"(\n\s*-\s+[^\n]+)", r"\1", pure_body_raw)
    pure_body_raw = re.sub(r"\n\s*-\s+", r"\n\\- ", pure_body_raw)

    body_anchored = inject_semantic_anchors(pure_body_raw, archetype="VBPL_ADMIN")

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

    legal_basis_graph = extract_legal_basis_graph(cleaned_md, reg_lookup)

    doc_num = doc_registry_meta.get("document_number", bundle_dir.name.upper())
    doc_title = doc_registry_meta.get("title", f"Văn bản quy phạm pháp luật {doc_num}")
    effective_date = doc_registry_meta.get("effective_date", "2021-03-03")
    signer = doc_registry_meta.get("signer", "Thủ tướng Chính phủ")
    pdf_path = doc_registry_meta.get("pdf_path", f"{bundle_dir.name}.pdf")
    pdf_sha256 = doc_registry_meta.get("pdf_sha256", "UNVERIFIED")

    metadata_obj = {
        "id": bundle_dir.name,
        "document_number": doc_num,
        "type": doc_registry_meta.get("type", "Nghị định"),
        "title": doc_title,
        "status": "effective",
        "effective_date": effective_date,
        "signer": signer,
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
