"""Bundle and Concept File Writer."""

from __future__ import annotations

import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.constants import (
    CURRENT_CONVERTER_VERSION,
    CURRENT_OKF_SCHEMA_URI,
    CURRENT_OKF_SPEC,
)
from ccba_legal.packager.slug_utils import sanitize_slug


def write_concept(
    root_dir: Path,
    relative_path: str,
    concept_type: str,
    title: str,
    description: str,
    content: str,
    resource_uri: str = "",
) -> None:
    """Write a concept file with valid OKF YAML frontmatter.

    .. deprecated:: OKF v2.0+
       Embedded frontmatter in Markdown violates Gate 6 (Pure Normative Body).
       Metadata must be stored in standalone metadata.yaml.
    """
    warnings.warn(
        "write_concept is deprecated in OKF v2.4 Universal. Frontmatter in .md violates Gate 6.",
        DeprecationWarning,
        stacklevel=2,
    )
    dest_path = root_dir / relative_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fm_lines = [
        "---",
        f"type: {concept_type}",
        f'title: "{title}"',
        f'description: "{description}"',
        f'resource: "{resource_uri}"',
        f'timestamp: "{timestamp}"',
        'uniclass: "Pr_65_70"',
        "---",
    ]
    frontmatter = "\n".join(fm_lines) + "\n\n"
    full_content = frontmatter + content.strip() + "\n"
    dest_path.write_text(full_content, encoding="utf-8")
    print(f"[OKF Packager] Wrote concept file to {dest_path}")


def write_logs_and_index(bundle_dir: Path, bundle_slug: str, guiding_files: list[str]) -> None:
    """Create and update index.md, log.md, and dead_ends.md in the root of the OKF Bundle.

    .. deprecated:: OKF v2.0+
       Use write_logs_and_index_v2 for OKF v2.4 Universal bundles.
    """
    warnings.warn(
        "write_logs_and_index is deprecated. Use write_logs_and_index_v2.",
        DeprecationWarning,
        stacklevel=2,
    )
    log_path = bundle_dir / "log.md"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    log_content = f"# Processing Log for {bundle_slug}\n\n- [{timestamp}] Bundle generated and organized into legal_docs/{bundle_slug}\n"
    log_path.write_text(log_content, encoding="utf-8")

    dead_ends_path = bundle_dir / "dead_ends.md"
    dead_ends_content = f"# Dead Ends & Fallbacks for {bundle_slug}\n\n- None recorded.\n"
    dead_ends_path.write_text(dead_ends_content, encoding="utf-8")

    index_path = bundle_dir / "index.md"
    index_md = f"# OKF Bundle Index: {bundle_slug}\n\n## Primary Document\n- [{bundle_slug}.md](./{bundle_slug}.md)\n\n## Sections\n"
    sections_dir = bundle_dir / "sections"
    if sections_dir.exists():
        for sec in sorted(sections_dir.glob("*.md")):
            index_md += f"- [{sec.name}](./sections/{sec.name})\n"

    index_md += "\n## Guiding Documents\n"
    guiding_dir = bundle_dir / "guiding_docs"
    if guiding_dir.exists():
        for g in sorted(guiding_dir.glob("*.md")):
            index_md += f"- [{g.name}](./guiding_docs/{g.name})\n"

    primary_path = bundle_dir / f"{bundle_slug}.md"
    if primary_path.exists():
        p_content = primary_path.read_text(encoding="utf-8")
        if "## DANH SÁCH PHỤ LỤC ĐÍNH KÈM" in p_content:
            appendix_part = p_content.split("## DANH SÁCH PHỤ LỤC ĐÍNH KÈM")[1]
            index_md += "\n### Phụ lục đính kèm" + appendix_part

    index_path.write_text(index_md, encoding="utf-8")
    print(f"[OKF Packager] Wrote bundle index to {index_path}")


def write_logs_and_index_v2(bundle_dir: Path, bundle_slug: str, metadata: dict[str, Any]) -> None:
    """Write lightweight OKF index conforming to ADR 0036."""
    now_utc = datetime.now(timezone.utc).isoformat()
    title = metadata.get("title", bundle_slug)
    doc_type = metadata.get("type", "Document")

    log_content = f"# OKF {CURRENT_OKF_SPEC} Processing Log\n\n- [{now_utc}] Bundle initialized for {bundle_slug}\n"
    (bundle_dir / "log.md").write_text(log_content, encoding="utf-8")

    lines = [
        f"# Gói Tri Thức OKF {CURRENT_OKF_SPEC}: {title}\n",
        "## Metadata",
        f"- **Type**: {doc_type}",
        f"- **ID**: {bundle_slug}",
        f"- **Generated**: {now_utc}\n",
        "## Contents",
        f"- [{bundle_slug}.md](./{bundle_slug}.md) — Thân văn bản quy phạm nguyên văn",
        "- [metadata.yaml](./metadata.yaml) — Standalone Machine Metadata",
        "- [clauses.json](./clauses.json) — Cây cú pháp điều khoản AST",
        "- [qa_benchmark.json](./qa_benchmark.json) — Bộ câu hỏi kiểm thử QA Ground Truth",
    ]

    # ADR 0036 Compartment awareness
    compartments = [
        ("tables", "tables/README.md", "Bảng tra cứu số liệu kỹ thuật 2D"),
        ("figures", "figures/figures_catalog.yaml", "Thẻ thị giác sơ đồ hình học / khí động"),
        ("annexes", "annexes", "Phụ lục quy chuẩn kỹ thuật"),
        ("templates", "templates", "Biểu mẫu hành chính nguyên tử"),
        ("sources", "sources", "Tài liệu nguồn PDF Công báo & DOCX"),
    ]
    detected_compartments = []
    for folder, entry, desc in compartments:
        target = bundle_dir / folder
        if target.exists() and any(target.iterdir()):
            if (bundle_dir / entry).exists():
                detected_compartments.append(f"- [{folder}/](./{entry}) — {desc}")
            else:
                detected_compartments.append(f"- [{folder}/](./{folder}/) — {desc}")

    if detected_compartments:
        lines.append("\n## Ngăn Kéo Chuyên Biệt (ADR 0036)")
        lines.extend(detected_compartments)

    index_content = "\n".join(lines) + "\n"
    (bundle_dir / "index.md").write_text(index_content, encoding="utf-8")


def package_bundle(root_dir: Path, doc_id: str, content: str, metadata: dict[str, Any]) -> Path:
    """Create and structure an OKF bundle for a document.

    .. deprecated:: OKF v2.0+
       Use package_bundle_v2 or ccba_legal.converters.convert_docx_to_okf_bundle.
    """
    warnings.warn(
        "package_bundle (v1) is deprecated. Use package_bundle_v2 or convert_docx_to_okf_bundle.",
        DeprecationWarning,
        stacklevel=2,
    )
    bundle_slug = sanitize_slug(doc_id)
    bundle_dir = root_dir / bundle_slug
    bundle_dir.mkdir(parents=True, exist_ok=True)

    title = metadata.get("title", f"Legal Document {doc_id}")
    doc_type = metadata.get("type", "Law")

    meta_dict = {
        "doc_id": doc_id,
        "title": title,
        "type": doc_type,
        "doc_number": metadata.get("document_number", metadata.get("doc_number", "")),
        "category": metadata.get("category", doc_type),
        "issuer": metadata.get("issued_by", metadata.get("issuer", "")),
        "issued_date": metadata.get("issued_date", ""),
        "effective_date": metadata.get("effective_date", ""),
        "status": metadata.get("status", "effective"),
        "source_url": metadata.get("source_url", ""),
        "sha256": metadata.get("sha256", ""),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    meta_yaml_path = bundle_dir / "metadata.yaml"
    meta_yaml_path.write_text(
        yaml.safe_dump(meta_dict, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    write_concept(
        root_dir=root_dir,
        relative_path=f"{bundle_slug}/{bundle_slug}.md",
        concept_type=doc_type,
        title=title,
        description=f"Raw text for {doc_id}",
        content=content,
        resource_uri=metadata.get("source_url", ""),
    )
    write_logs_and_index(bundle_dir, bundle_slug, [])
    return bundle_dir


def package_bundle_v2(
    root_dir: Path,
    doc_id: str,
    content: str,
    metadata: dict[str, Any],
    qa_items: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> Path:
    """Create a strictly flat, zero-redundancy OKF v2.4 Universal bundle with provenance stamping."""
    from ccba_legal.packager.clause_indexer import generate_clauses_json

    bundle_slug = sanitize_slug(doc_id)
    bundle_dir = root_dir / bundle_slug
    bundle_dir.mkdir(parents=True, exist_ok=True)

    title = metadata.get("title", f"Legal Document {doc_id}")
    doc_type = metadata.get("type", "Law")

    meta_dict = {
        "doc_id": doc_id,
        "title": title,
        "type": doc_type,
        "doc_number": metadata.get("document_number", metadata.get("doc_number", "")),
        "category": metadata.get("category", doc_type),
        "issuer": metadata.get("issued_by", metadata.get("issuer", "")),
        "issued_date": metadata.get("issued_date", ""),
        "effective_date": metadata.get("effective_date", ""),
        "status": metadata.get("status", "effective"),
        "source_url": metadata.get("source_url", ""),
        "sha256": metadata.get("sha256", ""),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "okf_spec": CURRENT_OKF_SPEC,
        "converter_version": CURRENT_CONVERTER_VERSION,
        "schema_uri": CURRENT_OKF_SCHEMA_URI,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    (bundle_dir / "metadata.yaml").write_text(
        yaml.safe_dump(meta_dict, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    primary_file = bundle_dir / f"{bundle_slug}.md"
    primary_file.write_text(content, encoding="utf-8")

    # Generate AST clauses.json
    generate_clauses_json(content, bundle_dir)

    # Save QA Benchmark if provided
    if qa_items:
        (bundle_dir / "qa_benchmark.json").write_text(
            json.dumps(qa_items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        (bundle_dir / "qa_benchmark.json").write_text("[]", encoding="utf-8")

    write_logs_and_index_v2(bundle_dir, bundle_slug, metadata)
    return bundle_dir
