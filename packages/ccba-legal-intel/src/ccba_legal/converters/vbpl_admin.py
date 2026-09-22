"""Complete OKF v2.4 Universal Transformation Pipeline for Decrees, Circulars and Laws (ADR 0021, ADR 0034, ADR 0036)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

import mammoth
import yaml

from ccba_legal.constants import (
    CURRENT_CONVERTER_VERSION,
    CURRENT_OKF_SCHEMA_URI,
    CURRENT_OKF_SPEC,
    DIR_TABLES,
    TABLES_CATALOG_SCHEMA_VERSION,
)
from ccba_legal.converters.table_extractor import classify_and_extract_tables
from ccba_legal.converters.unit_normalizer import (
    normalize_clause_numbers,
    normalize_docx_markdown,
)
from ccba_legal.gold_standard import generate_bundle_ast_and_qa, inject_semantic_anchors
from ccba_legal.table_cleaner import clean_markdown_tables_and_notes


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
        title_clean = re.sub(
            r"^căn\s+cứ\s+", "", match.group(0).strip(" ;.\r\n*"), flags=re.IGNORECASE
        ).strip()
        title_clean = (
            re.sub(r"<[^>]+>", "", title_clean)
            .replace("*", "")
            .replace("\\", "")
            .replace("_", "")
            .strip()
        )
        if not any(
            k in title_clean.lower()
            for k in ["luật", "nghị định", "pháp lệnh", "nghị quyết", "thông tư"]
        ):
            continue
        doc_num = match.group(2) if match.group(2) else ""
        if not doc_num:
            m_num = re.search(r"số\s+([\d\w\-/]+)", title_clean, re.IGNORECASE)
            if m_num:
                doc_num = m_num.group(1)
        doc_id = registry_lookup.get(
            doc_num, re.sub(r"[^\w\d]+", "_", title_clean.lower()).strip("_")[:50]
        )
        basis_list.append({"doc_id": doc_id, "title": title_clean})
    return basis_list


def _load_registry_metadata(
    registry_file: Path, bundle_name: str
) -> tuple[dict[str, str], dict[str, Any]]:
    """Load lookup map and specific metadata for target document from legal_registry.yaml."""
    reg_lookup: dict[str, str] = {}
    doc_registry_meta: dict[str, Any] = {}
    if registry_file.exists():
        with open(registry_file, encoding="utf-8") as f:
            reg_data = yaml.safe_load(f)
            all_items: list[dict[str, Any]] = []
            for _k, v in reg_data.items():
                if isinstance(v, list):
                    all_items.extend(v)
            for item in all_items:
                doc_num = item.get("document_number")
                if doc_num:
                    reg_lookup[doc_num] = item.get("id")
                if item.get("id") == bundle_name or item.get("document_number") == bundle_name:
                    doc_registry_meta = item
    return (reg_lookup, doc_registry_meta)


def _convert_docx_to_clean_markdown(docx_input: Path | BinaryIO) -> str:
    """Convert docx to raw markdown via Mammoth and clean escaping artifacts."""
    if hasattr(docx_input, "read"):
        docx_input.seek(0)
        raw_md = mammoth.convert_to_markdown(docx_input).value
    else:
        with open(docx_input, "rb") as f:
            raw_md = mammoth.convert_to_markdown(f).value
    cleaned = re.sub(r'<a id="[^"]+"></a>', "", raw_md)
    return normalize_docx_markdown(cleaned)


def _export_single_template(
    form_text: str, roman_num: str, f_num: str, doc_num_str: str, sub_dir: Path
) -> Path:
    """Export an individual atomic form template markdown file."""
    first_few_lines = form_text.splitlines()[:5]
    f_title = f"Biểu mẫu số {f_num}"
    for line in first_few_lines:
        cleaned_line = re.sub(r"^#+\s*|__|\*", "", line).strip()
        if cleaned_line and not cleaned_line.lower().startswith("mẫu số") and len(cleaned_line) > 5:
            f_title = cleaned_line
            break
    slug_title = re.sub(r"[^\w\d]+", "_", f_title.lower()).strip("_")[:40]
    form_file = sub_dir / f"mau_{f_num}_{slug_title}.md"
    tpl_header = f"# Phụ lục {roman_num} — Mẫu số {f_num}: {f_title}\n\n> [!NOTE]\n> **Văn bản ban hành:** {doc_num_str}\n> **Biểu mẫu:** Mẫu số {f_num} thuộc Phụ lục {roman_num}\n\n---\n\n"
    form_file.write_text(tpl_header + form_text + "\n", encoding="utf-8")
    return form_file


def _extract_and_export_templates(
    cleaned_md: str, templates_dir: Path, doc_num_str: str
) -> tuple[str, list[Path]]:
    """Split administrative appendices into atomic templates in templates/ directory."""
    app_matches = list(
        re.finditer(
            r"(?:^|\n)#*\s*__?\s*PHỤ LỤC\s+([IVXLCDM0-9]+)__?\s*([^\n]*)", cleaned_md, re.IGNORECASE
        )
    )
    created_templates: list[Path] = []

    for idx, match in enumerate(app_matches):
        roman_num = match.group(1).upper()
        app_title = re.sub(r"^__+|__+$", "", match.group(2).strip()).strip()
        start_pos = match.start()
        end_pos = app_matches[idx + 1].start() if idx + 1 < len(app_matches) else len(cleaned_md)
        app_full_text = cleaned_md[start_pos:end_pos].strip()

        pattern = re.compile(r"(?:^|\n)#*\s*__?\s*Mẫu\s+số\s+(\d+[a-zA-Z]?)[.\s_]*", re.IGNORECASE)
        form_positions = {m.group(1).zfill(2): m.start() for m in pattern.finditer(app_full_text)}

        def _form_sort_key(item: tuple[str, int]) -> tuple[int, str]:
            tag = item[0]
            m_digits = re.match(r"^(\d+)(.*)$", tag)
            if m_digits:
                return (int(m_digits.group(1)), m_digits.group(2))
            return (999, tag)

        sorted_forms = sorted(form_positions.items(), key=_form_sort_key)

        if len(sorted_forms) >= 2:
            sub_dir = templates_dir / f"phu_luc_{roman_num.lower()}"
            sub_dir.mkdir(parents=True, exist_ok=True)
            for f_idx, (f_num, f_start) in enumerate(sorted_forms):
                f_end = (
                    sorted_forms[f_idx + 1][1]
                    if f_idx + 1 < len(sorted_forms)
                    else len(app_full_text)
                )
                form_file = _export_single_template(
                    app_full_text[f_start:f_end].strip(), roman_num, f_num, doc_num_str, sub_dir
                )
                created_templates.append(form_file)
        else:
            app_file = templates_dir / f"phu_luc_{roman_num.lower()}.md"
            tpl_header = f"# Phụ lục {roman_num}: {app_title}\n\n> [!NOTE]\n> **Văn bản ban hành:** {doc_num_str}\n> **Phụ lục:** Phụ lục số {roman_num}\n\n---\n\n"
            app_file.write_text(tpl_header + app_full_text + "\n", encoding="utf-8")
            created_templates.append(app_file)

    first_app_pos = app_matches[0].start() if app_matches else len(cleaned_md)
    return (cleaned_md[:first_app_pos].strip(), created_templates)


def _build_pure_normative_body(pure_body_raw: str) -> str:
    """Strip administrative preamble headers, trailing footer signatures, and apply strict bullet indentation formatting."""
    pure_body = re.sub(
        r"^(?:[\s\S]*?)(#+\s*__?\s*Chương\s+[IVXLCDM0-9]+|#+\s*__?\s*Điều\s+1\b)",
        r"\1",
        pure_body_raw,
        flags=re.IGNORECASE,
    )
    # Strip trailing administrative signature blocks / distribution footers
    sig_split = re.split(
        r"(?:\n\s*__\*?\s*Nơi nhận\s*:|\n\s*\*+Nơi nhận\s*:|\n\s*Nơi nhận\s*:|\n\s*__KT\.\s+BỘ\s+TRƯỞNG|\n\s*KT\.\s+BỘ\s+TRƯỞNG\s*\n|\n\s*__BỘ\s+TRƯỞNG__|\n\s*__THỨ\s+TRƯỞNG__|\n\s*__CHỦ\s+TỊCH\s+QUỐC\s+HỘI|\n\s*CHỦ\s+TỊCH\s+QUỐC\s+HỘI\s*\n|\n\s*__TM\.\s+QUỐC\s+HỘI|\n\s*__TM\.\s+CHÍNH\s+PHỦ|\n\s*__THỦ\s+TƯỚNG__|\n\s*\*+Luật\s+này\s+được\s+Quốc\s+hội|\n\s*Luật\s+này\s+được\s+Quốc\s+hội)",
        pure_body,
        flags=re.IGNORECASE,
    )
    pure_body = sig_split[0].strip()

    pure_body = normalize_clause_numbers(pure_body)
    pure_body = re.sub(r"(\n\s*\+\s+[^\n]+)", r"&nbsp;&nbsp;\1", pure_body)
    pure_body = re.sub(r"&nbsp;&nbsp;\n\s*\+\s+", r"\n&nbsp;&nbsp;\\+ ", pure_body)
    pure_body = re.sub(r"\n\s*-\s+", r"\n\\- ", pure_body)
    return inject_semantic_anchors(pure_body, archetype="VBPL_ADMIN")


def _write_bundle_metadata_and_index(
    bundle_dir: Path,
    target_md_name: str,
    doc_meta: dict[str, Any],
    legal_basis: list[dict[str, str]],
    clauses_cnt: int,
    qa_cnt: int,
    templates_cnt: int,
    tables_cnt: int,
    spec_version: str = CURRENT_OKF_SPEC,
) -> None:
    """Write metadata.yaml and human-readable index.md for the OKF bundle."""
    doc_num = doc_meta.get("document_number", bundle_dir.name.upper())
    doc_title = doc_meta.get("title", f"Văn bản quy phạm pháp luật {doc_num}")
    effective_date = doc_meta.get("effective_date", "2021-03-03")
    signer = doc_meta.get("signer", "Thủ tướng Chính phủ")
    pdf_path = doc_meta.get("pdf_path", f"{bundle_dir.name}.pdf")
    pdf_sha256 = doc_meta.get("pdf_sha256", "UNVERIFIED")

    metadata_obj = {
        "id": doc_meta.get("id", bundle_dir.name),
        "document_number": doc_num,
        "type": doc_meta.get("type", "Nghị định"),
        "title": doc_title,
        "status": doc_meta.get("status", "effective"),
        "effective_date": effective_date,
        "signer": signer,
        "pdf_path": pdf_path,
        "pdf_sha256": pdf_sha256,
        "pdf_status": doc_meta.get("pdf_status", "verified"),
        "legal_basis": legal_basis,
        "replaces": doc_meta.get("relations", {}).get("replaces", [])
        if isinstance(doc_meta.get("relations"), dict)
        else doc_meta.get("replaces", []),
        "okf_spec": spec_version,
        "converter_version": CURRENT_CONVERTER_VERSION,
        "schema_uri": CURRENT_OKF_SCHEMA_URI,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(bundle_dir / "metadata.yaml", "w", encoding="utf-8") as f:
        yaml.dump(metadata_obj, f, allow_unicode=True, sort_keys=False, indent=2)

    index_md = f"""# Gói Tri Thức Pháp Lý OKF {CURRENT_OKF_SPEC}: {doc_num}

> [!NOTE]
> **Văn bản:** {doc_title}
> **Cơ quan ban hành:** Chính phủ (Người ký: {signer}).
> **Hiệu lực:** {effective_date}.
> **Mỏ neo PDF Công báo:** [{Path(pdf_path).name}](./{Path(pdf_path).name}) *(SHA-256: `{pdf_sha256}`)*.

---

## 📑 Danh Mục Thành Phần Gói Tri Thức (OKF {CURRENT_OKF_SPEC} Bundle)

- [Toàn văn Quy phạm (Markdown OKF {CURRENT_OKF_SPEC})](./{target_md_name}) — Thân văn bản quy phạm thuần khiết có gắn thẻ neo `#dieu-X`.
- [Metadata Pháp lý & Đồ thị (YAML)](./metadata.yaml) — Đặc tả thuộc tính và cây đồ thị `legal_basis`.
- [Cây Cú Pháp Điều Khoản (AST Clauses JSON)](./clauses.json) — {clauses_cnt} nodes điều khoản phục vụ AI QC & RAG.
- [Bộ Đánh Giá Độ Chính Xác (QA Benchmark)](./qa_benchmark.json) — {qa_cnt} cặp câu hỏi - câu trả lời đối soát.
- [Kho Biểu Mẫu Chuẩn Hóa (Templates Directory)](./templates/) — {templates_cnt} Biểu mẫu Markdown phục vụ Agent Copywriting & Sinh Hồ Sơ.
- [Bảng Tra Cứu Kỹ Thuật (Tables Directory)](./tables/) — {tables_cnt} Bảng tra cứu số học (CSV + JSON).
"""
    (bundle_dir / "index.md").write_text(index_md, encoding="utf-8")


def _generate_vbpl_frontmatter(
    doc_meta: dict[str, Any], bundle_dir: Path, target_md_name: str
) -> str:
    """Generate canonical OKF v2.4 YAML frontmatter for VBPL normative document."""
    doc_id = doc_meta.get("id", bundle_dir.name)
    doc_num = doc_meta.get("document_number", bundle_dir.name.upper())
    title = doc_meta.get("title", f"Văn bản quy phạm pháp luật {doc_num}")
    doc_type = doc_meta.get("type", "Nghị định")
    issued_by = doc_meta.get("issued_by", "Chính phủ")
    signer = doc_meta.get("signer", "Thủ tướng Chính phủ")
    issued_date = doc_meta.get("issued_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    effective_date = doc_meta.get("effective_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    status = doc_meta.get("status", "active")
    pdf_path = doc_meta.get("pdf_path", f"./sources/{bundle_dir.name}.pdf")
    pdf_name = Path(pdf_path).name
    pdf_sha = doc_meta.get("pdf_sha256", "UNVERIFIED")
    cong_bao = doc_meta.get("cong_bao_number", "Đang cập nhật")

    raw_pdf_anchor = doc_meta.get("pdf_anchor")
    if isinstance(raw_pdf_anchor, dict):
        if raw_pdf_anchor.get("path"):
            pdf_path = raw_pdf_anchor["path"]
            pdf_name = Path(pdf_path).name
        if raw_pdf_anchor.get("sha256"):
            pdf_sha = raw_pdf_anchor["sha256"]
        if raw_pdf_anchor.get("cong_bao_number"):
            cong_bao = raw_pdf_anchor["cong_bao_number"]

    replaces = (
        doc_meta.get("relations", {}).get("replaces", [])
        if isinstance(doc_meta.get("relations"), dict)
        else doc_meta.get("replaces", [])
    )
    category = "01_vbpl"
    for part in bundle_dir.parts:
        if part in ("01_vbpl", "02_qcvn", "03_tcvn", "04_appendices"):
            category = part
            break

    fm_dict: dict[str, Any] = {
        "okf_version": "2.4",
        "type": "legal_normative_body",
        "title": title,
        "description": title,
        "tags": ["vbpl", re.sub(r"[^\w]+", "_", str(doc_type).lower()).strip("_")],
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z"),
        "resource": f"legal_docs/{category}/{bundle_dir.name}/{target_md_name}",
        "id": doc_id,
        "doc_id": doc_id,
        "document_number": doc_num,
        "document_type": doc_type,
        "issued_by": issued_by,
        "signer": signer,
        "issued_date": str(issued_date),
        "effective_date": str(effective_date),
        "status": status,
        "pdf_anchor": {
            "path": f"./sources/{pdf_name}",
            "sha256": pdf_sha,
            "cong_bao_number": cong_bao,
        },
    }
    if replaces:
        fm_dict["relations"] = (
            [{"target_id": r, "relation_type": "replaces"} for r in replaces]
            if isinstance(replaces, list)
            else replaces
        )
    return (
        "---\n"
        + yaml.dump(fm_dict, allow_unicode=True, sort_keys=False, indent=2).strip()
        + "\n---\n\n"
    )


def process_vbpl_bundle(
    docx_path: Path,
    bundle_dir: Path,
    registry_file: Path,
    output_filename: str | None = None,
    spec_version: str = CURRENT_OKF_SPEC,
    sanitized_stream: BinaryIO | None = None,
    doc_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Complete OKF Transformation Pipeline for Decrees, Circulars and Laws."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = bundle_dir / "templates"
    if templates_dir.exists():
        shutil.rmtree(templates_dir)
    templates_dir.mkdir(parents=True, exist_ok=True)

    reg_lookup, loaded_meta = _load_registry_metadata(registry_file, bundle_dir.name)
    effective_meta = dict(loaded_meta)
    if doc_meta:
        effective_meta.update(doc_meta)
    if effective_meta.get("document_number") and effective_meta.get("id"):
        reg_lookup[effective_meta["document_number"]] = effective_meta["id"]

    input_src: Path | BinaryIO = sanitized_stream if sanitized_stream is not None else docx_path
    cleaned_md = _convert_docx_to_clean_markdown(input_src)
    extracted_tables = classify_and_extract_tables(input_src, bundle_dir)
    if extracted_tables:
        tables_dir = bundle_dir / DIR_TABLES
        with open(tables_dir / "tables_catalog.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "schema_version": TABLES_CATALOG_SCHEMA_VERSION,
                    "okf_spec": CURRENT_OKF_SPEC,
                    "total_tables": len(extracted_tables),
                    "tables": extracted_tables,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    pure_body_raw, created_templates = _extract_and_export_templates(
        cleaned_md, templates_dir, effective_meta.get("document_number", bundle_dir.name)
    )
    if not created_templates and templates_dir.exists():
        shutil.rmtree(templates_dir, ignore_errors=True)

    body_anchored = _build_pure_normative_body(pure_body_raw)
    body_anchored = clean_markdown_tables_and_notes(body_anchored)

    target_md_filename = output_filename or f"{bundle_dir.name}.md"
    frontmatter = _generate_vbpl_frontmatter(effective_meta, bundle_dir, target_md_filename)
    (bundle_dir / target_md_filename).write_text(frontmatter + body_anchored, encoding="utf-8")

    clauses, qa_benchmark = generate_bundle_ast_and_qa(bundle_dir / target_md_filename, bundle_dir)
    legal_basis_graph = extract_legal_basis_graph(cleaned_md, reg_lookup)

    _write_bundle_metadata_and_index(
        bundle_dir=bundle_dir,
        target_md_name=target_md_filename,
        doc_meta=effective_meta,
        legal_basis=legal_basis_graph,
        clauses_cnt=len(clauses),
        qa_cnt=len(qa_benchmark),
        templates_cnt=len(created_templates),
        tables_cnt=len(extracted_tables),
        spec_version=spec_version,
    )

    return {
        "status": "success",
        "bundle": bundle_dir.name,
        "archetype": "VBPL_ADMIN",
        "spec_version": spec_version,
        "clauses_count": len(clauses),
        "templates_count": len(created_templates),
        "tables_count": len(extracted_tables),
        "qa_count": len(qa_benchmark),
    }


# Backward compatibility aliases for versioned function callers (ADR 0021, ADR 0036)
process_vbpl_bundle_okf_v24 = process_vbpl_bundle
process_vbpl_bundle_okf_v22 = process_vbpl_bundle
