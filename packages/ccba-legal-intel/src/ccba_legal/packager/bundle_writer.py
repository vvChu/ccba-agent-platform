"""Bundle and Concept File Writer."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import yaml

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
    """Write a concept file with valid OKF YAML frontmatter."""
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
    """Create and update index.md, log.md, and dead_ends.md in the root of the OKF Bundle."""
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
    """Write lightweight OKF v2.0 index and logs."""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    title = metadata.get("title", bundle_slug)
    doc_type = metadata.get("type", "Document")

    log_content = f"# OKF v2.0 Processing Log\n\n- [{timestamp}] Bundle initialized for {bundle_slug}\n"
    (bundle_dir / "log.md").write_text(log_content, encoding="utf-8")

    index_content = f"# OKF Bundle: {title}\n\n## Metadata\n- **Type**: {doc_type}\n- **ID**: {bundle_slug}\n- **Generated**: {timestamp}\n\n## Contents\n- [{bundle_slug}.md](./{bundle_slug}.md) — Canonical Document Body\n- [metadata.yaml](./metadata.yaml) — Standalone Machine Metadata\n- [clauses.json](./clauses.json) — Structured AST Nodes\n- [qa_benchmark.json](./qa_benchmark.json) — QA Benchmark Ground Truth\n"
    (bundle_dir / "index.md").write_text(index_content, encoding="utf-8")


def package_bundle(root_dir: Path, doc_id: str, content: str, metadata: dict[str, Any]) -> Path:
    """Create and structure an OKF bundle for a document."""
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
    meta_yaml_path.write_text(yaml.safe_dump(meta_dict, allow_unicode=True, sort_keys=False), encoding="utf-8")

    write_concept(root_dir=root_dir, relative_path=f"{bundle_slug}/{bundle_slug}.md", concept_type=doc_type, title=title, description=f"Raw text for {doc_id}", content=content, resource_uri=metadata.get("source_url", ""))
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
    """Create a strictly flat, zero-redundancy OKF v2.0 bundle."""
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
    }
    (bundle_dir / "metadata.yaml").write_text(yaml.safe_dump(meta_dict, allow_unicode=True, sort_keys=False), encoding="utf-8")
    primary_file = bundle_dir / f"{bundle_slug}.md"
    primary_file.write_text(content, encoding="utf-8")

    # Generate AST clauses.json
    generate_clauses_json(content, bundle_dir)

    # Save QA Benchmark if provided
    if qa_items:
        (bundle_dir / "qa_benchmark.json").write_text(json.dumps(qa_items, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        (bundle_dir / "qa_benchmark.json").write_text("[]", encoding="utf-8")

    write_logs_and_index_v2(bundle_dir, bundle_slug, metadata)
    return bundle_dir
