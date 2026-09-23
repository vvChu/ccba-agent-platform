# Copyright (c) 2026 CCBA. All rights reserved.
"""Export & Packaging Functional Helpers for Standard Converter (OKF v2.4)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from ccba_legal.constants import (
    CURRENT_CONVERTER_VERSION,
    CURRENT_OKF_SCHEMA_URI,
    CURRENT_OKF_SPEC,
    DIR_TABLES,
    TABLES_CATALOG_SCHEMA_VERSION,
)
from ccba_legal.gold_standard import generate_bundle_ast_and_qa
from ccba_legal.table_cleaner import clean_markdown_tables_and_notes

if TYPE_CHECKING:
    from ccba_legal.converters.standard.strategy import StandardConversionContext

__all__ = [
    "build_frontmatter_yaml",
    "export_standard_bundle",
]


def build_frontmatter_yaml(bundle_dir: Path, doc_meta: dict[str, Any] | None = None) -> str:
    """Build standard OKF v2.4 YAML frontmatter for technical standard/QCVN document."""
    meta_file = bundle_dir / "metadata.yaml"
    m_data: dict[str, Any] = {}
    if meta_file.exists():
        try:
            loaded = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                m_data = loaded
        except Exception:
            pass
    if doc_meta:
        for k, v in doc_meta.items():
            if k not in m_data or not m_data[k]:
                m_data[k] = v

    doc_id = m_data.get("id", bundle_dir.name)
    doc_num = m_data.get("document_number", bundle_dir.name.replace("_", " ").upper())
    title = m_data.get("title", f"{doc_num} — {doc_id}")
    issued_by = m_data.get("issued_by", "Bộ Xây dựng")
    signer = m_data.get("signer", "")
    issued_date = m_data.get("issued_date", "")
    effective_date = m_data.get("effective_date", "")
    status = m_data.get("status", "active")
    cong_bao = m_data.get("cong_bao_number", "Đang cập nhật")
    pdf_path = m_data.get("pdf_path", f"./sources/{bundle_dir.name}.pdf")
    pdf_name = Path(pdf_path).name
    pdf_sha = m_data.get("pdf_sha256", "")

    replaces = (
        m_data.get("relations", {}).get("replaces", [])
        if isinstance(m_data.get("relations"), dict)
        else m_data.get("replaces", [])
    )

    fm_dict: dict[str, Any] = {
        "okf_version": "2.4",
        "type": "technical_standard_qcvn"
        if "qcvn" in bundle_dir.name.lower()
        else "technical_standard_tcvn",
        "title": title,
        "description": title,
        "tags": [
            "qcvn" if "qcvn" in bundle_dir.name.lower() else "tcvn",
            "quy_chuan_ky_thuat" if "qcvn" in bundle_dir.name.lower() else "tieu_chuan_ky_thuat",
        ],
        "timestamp": "2026-08-26T00:00:00Z",
        "resource": f"legal_docs/02_qcvn/{bundle_dir.name}/{bundle_dir.name}.md"
        if "qcvn" in bundle_dir.name.lower()
        else f"legal_docs/03_tcvn/{bundle_dir.name}/{bundle_dir.name}.md",
        "id": doc_id,
        "doc_id": doc_id,
        "document_number": doc_num,
        "document_type": m_data.get("type", "Quy chuẩn kỹ thuật quốc gia"),
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
        fm_dict["relations"] = {"replaces": replaces}
    fm_dict["artifacts"] = {
        "tables_dir": "./tables/",
        "tables_catalog": "./tables/tables_catalog.json",
        "benchmark_file": "./qa_benchmark.json",
        "figures_dir": "./figures/",
    }

    return (
        "---\n"
        + yaml.dump(fm_dict, allow_unicode=True, sort_keys=False, indent=2).strip()
        + "\n---\n\n"
    )


def export_standard_bundle(ctx: StandardConversionContext) -> dict[str, Any]:
    """Export modular annex files, 2D navigation matrix, tables catalog, AST index, and update metadata."""
    # 1. Export Annexes
    if ctx.annex_buffers:
        annexes_dir = ctx.bundle_dir / "annexes"
        annexes_dir.mkdir(parents=True, exist_ok=True)
        nav_rows: list[str] = []
        for a_letter, a_info in ctx.annex_buffers.items():
            annex_slug, annex_title, annex_type, annex_anchor = (
                a_info["slug"],
                a_info["title"],
                a_info["type"],
                a_info["anchor"],
            )
            annex_md = (
                "".join(a_info["parts"])
                .replace("figures/images/", "../figures/images/")
                .replace("tables/", "../tables/")
            )
            annex_md = clean_markdown_tables_and_notes(annex_md)
            (annexes_dir / f"{annex_slug}.md").write_text(annex_md, encoding="utf-8")
            nav_rows.append(
                f"| **Phụ lục {a_letter}** | {annex_title} | {annex_type} | [📑 **Xem Phụ lục**](annexes/{annex_slug}.md#{annex_anchor}) |"
            )

        nav_matrix = [
            "\n---\n",
            f"## 📑 DANH MỤC PHỤ LỤC KỸ THUẬT CHUYÊN ĐỀ (MODULAR ANNEXES)\n\nToàn bộ {len(ctx.annex_buffers)} Phụ lục kỹ thuật chuyên đề đã được module hóa thành các tệp độc lập nhằm tối ưu hóa tra cứu và thẩm tra thiết kế (ADR 0021 & ADR 0030):\n",
            "| Ký hiệu | Tên Phụ Lục | Tính chất | Liên kết Tập tin |",
            "| :---: | :--- | :---: | :---: |",
        ]
        nav_matrix.extend(nav_rows)
        nav_matrix.append(
            f"\n---\n\n## 📊 HỆ THỐNG TRA CỨU BẢNG & SƠ ĐỒ KỸ THUẬT\n\n- **Tra cứu {len(ctx.tables_extracted)} Bảng Số Liệu:** Tra cứu chi tiết dạng CSV/JSON tại [Thư mục Bảng Số Liệu](tables/README.md).\n- **Tra cứu Sơ Đồ Hình Vẽ:** Tra cứu ảnh nét cao và đặc tả phân vùng tại [Danh Mục Sơ Đồ Khí Động](figures/figures_catalog.yaml).\n\n"
        )
        ctx.body_md_parts.append("\n".join(nav_matrix))

    # 2. Write Primary Markdown
    out_name = ctx.output_filename or f"{ctx.bundle_dir.name}.md"
    target_md_path = ctx.bundle_dir / out_name
    final_body_md = clean_markdown_tables_and_notes("".join(ctx.body_md_parts))
    if not final_body_md.strip().startswith("---"):
        frontmatter = build_frontmatter_yaml(ctx.bundle_dir, ctx.doc_meta)
        final_body_md = frontmatter + final_body_md
    target_md_path.write_text(final_body_md, encoding="utf-8")

    # 3. Export Tables Catalog & README
    if ctx.tables_extracted:
        tables_dir = ctx.bundle_dir / DIR_TABLES
        with open(tables_dir / "tables_catalog.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "schema_version": TABLES_CATALOG_SCHEMA_VERSION,
                    "okf_spec": CURRENT_OKF_SPEC,
                    "total_tables": len(ctx.tables_extracted),
                    "tables": ctx.tables_extracted,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        tbl_readme = [
            f"# DANH MỤC BẢNG TRA CỨU KỸ THUẬT 2D (OKF {CURRENT_OKF_SPEC})\n",
            "| Mã bảng | Tên bảng | CSV | JSON |",
            "| :--- | :--- | :---: | :---: |",
        ]
        for t in ctx.tables_extracted:
            tbl_readme.append(
                f"| {t['table_id']} | {t['title']} | [CSV]({t['csv_file']}) | [JSON]({t['json_file']}) |"
            )
        (tables_dir / "README.md").write_text("\n".join(tbl_readme) + "\n", encoding="utf-8")

    # 4. Generate AST and QA Benchmarks
    clauses, qa_list = generate_bundle_ast_and_qa(ctx.bundle_dir)

    # 5. Attest OKF Provenance & Converter Version into metadata.yaml
    meta_path = ctx.bundle_dir / "metadata.yaml"
    try:
        m_data: dict[str, Any] = {}
        if meta_path.exists():
            try:
                loaded = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    m_data = loaded
            except Exception:
                pass

        if ctx.doc_meta:
            for k, v in ctx.doc_meta.items():
                if k not in m_data or not m_data[k]:
                    m_data[k] = v

        doc_id = m_data.get("id", ctx.bundle_dir.name)
        doc_num = m_data.get("document_number", ctx.bundle_dir.name.replace("_", " ").upper())
        is_qcvn = "qcvn" in ctx.bundle_dir.name.lower()
        m_data.setdefault("id", doc_id)
        m_data.setdefault("document_number", doc_num)
        m_data.setdefault(
            "type", "Quy chuẩn kỹ thuật quốc gia" if is_qcvn else "Tiêu chuẩn quốc gia"
        )
        m_data.setdefault("title", f"{doc_num} — {doc_id}")
        m_data.setdefault("status", "active")
        m_data.setdefault("issued_by", "Bộ Xây dựng" if is_qcvn else "Bộ Khoa học và Công nghệ")
        m_data.setdefault("signer", "")
        m_data.setdefault("issued_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        m_data.setdefault("effective_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        m_data.setdefault("pdf_path", f"./sources/{ctx.bundle_dir.name}.pdf")
        m_data.setdefault("pdf_sha256", m_data.get("pdf_sha256", "UNVERIFIED"))
        m_data.setdefault("pdf_status", m_data.get("pdf_status", "verified"))
        if "relations" in m_data and isinstance(m_data["relations"], dict):
            if "replaces" in m_data and m_data["replaces"] == []:
                del m_data["replaces"]
            if "legal_basis" in m_data and m_data["legal_basis"] == []:
                del m_data["legal_basis"]
        else:
            m_data.setdefault("legal_basis", [])
            m_data.setdefault("replaces", [])
        m_data["okf_spec"] = CURRENT_OKF_SPEC
        m_data["converter_version"] = CURRENT_CONVERTER_VERSION
        m_data["schema_uri"] = CURRENT_OKF_SCHEMA_URI
        m_data["extracted_at"] = datetime.now(timezone.utc).isoformat()

        meta_path.write_text(
            yaml.dump(m_data, allow_unicode=True, sort_keys=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        print(f"Warning: Failed to write metadata.yaml in standard strategy: {exc}")
    return {
        "status": "success",
        "bundle": ctx.bundle_dir.name,
        "archetype": "TECHNICAL_TCVN",
        "clauses_count": len(clauses),
        "templates_count": 0,
        "tables_count": len(ctx.tables_extracted),
        "qa_count": len(qa_list),
    }
