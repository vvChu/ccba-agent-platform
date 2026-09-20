"""ccba_legal.compiler — Sharded Legal Registry Compiler.

Recursively discovers and compiles sharded `metadata.yaml` files within legal document
bundles (e.g. `legal_docs/**/metadata.yaml`) into a single, deterministically sorted
`legal_registry.yaml`.

This eliminates git merge conflicts on monolithic registry files when multiple engineers
or autonomous agents collaborate on adding new legal documents.
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("ccba_legal.compiler")

# Standard legal document category keys
LEGAL_CATEGORIES: set[str] = {
    "laws",
    "decrees",
    "circulars",
    "decisions",
    "resolutions",
    "standards",
}

# Canonical key order for individual document dictionaries
CANONICAL_DOC_KEYS: list[str] = [
    "id",
    "document_number",
    "title",
    "type",
    "category",
    "issued_by",
    "signer",
    "issued_date",
    "effective_date",
    "published_date",
    "status",
    "relations",
    "topics",
    "source_url",
    "download_url",
    "file_path",
    "markdown_path",
    "sha256",
]


def infer_category(
    doc_type: str, raw_category: str | None = None, relative_path: Path | None = None
) -> str:
    """Infer standard registry category from type, category field, or directory path.

    Args:
        doc_type: Raw document type string (e.g., 'Luật', 'Nghị định', 'Decision').
        raw_category: Explicit category string in metadata if present.
        relative_path: Relative Path to the document bundle directory.

    Returns:
        Standard category string in LEGAL_CATEGORIES.
    """
    if raw_category:
        norm_cat = raw_category.strip().lower()
        if norm_cat in LEGAL_CATEGORIES:
            return norm_cat
        # Handle singular forms
        singular_map = {
            "law": "laws",
            "decree": "decrees",
            "circular": "circulars",
            "decision": "decisions",
            "resolution": "resolutions",
            "standard": "standards",
        }
        if norm_cat in singular_map:
            return singular_map[norm_cat]

    dt = (doc_type or "").strip().lower()
    if any(k in dt for k in ("nghị định", "decree")):
        return "decrees"
    if any(k in dt for k in ("luật", "bộ luật", "law", "act")):
        return "laws"
    if any(k in dt for k in ("thông tư", "circular")):
        return "circulars"
    if any(k in dt for k in ("quyết định", "decision")):
        return "decisions"
    if any(k in dt for k in ("nghị quyết", "resolution")):
        return "resolutions"
    if any(k in dt for k in ("tiêu chuẩn", "quy chuẩn", "tcvn", "qcvn", "standard")):
        return "standards"

    # Fallback to directory structure inspection
    if relative_path:
        parts_lower = [p.lower() for p in relative_path.parts]
        for p in parts_lower:
            if "01_vbpl" in p or "laws" in p:
                return "laws"
            if "02_qcvn" in p or "standards" in p:
                return "standards"
            if "decrees" in p:
                return "decrees"
            if "circulars" in p:
                return "circulars"

    return "decrees"


def normalize_metadata_to_doc_entry(
    metadata: dict[str, Any],
    bundle_dir: Path,
    project_root: Path | None = None,
) -> tuple[str, dict[str, Any]]:
    """Normalize a sharded metadata.yaml dictionary into a canonical registry document entry.

    Args:
        metadata: Raw dictionary loaded from metadata.yaml.
        bundle_dir: Path to directory containing this metadata.yaml.
        project_root: Project root to compute relative file paths from.

    Returns:
        tuple (category, doc_entry_dict)
    """
    doc_id = str(metadata.get("id") or metadata.get("doc_id") or bundle_dir.name).strip()
    doc_number = str(metadata.get("document_number") or metadata.get("doc_number") or "").strip()
    title = str(metadata.get("title") or "").strip()
    raw_type = str(metadata.get("type") or "").strip()
    raw_cat = str(metadata.get("category") or "") if metadata.get("category") else None

    rel_bundle = bundle_dir
    if project_root:
        try:
            rel_bundle = bundle_dir.relative_to(project_root)
        except ValueError:
            pass

    category = infer_category(raw_type, raw_category=raw_cat, relative_path=rel_bundle)

    # Issued by / Issuer
    issued_by = str(metadata.get("issued_by") or metadata.get("issuer") or "").strip()
    signer = str(metadata.get("signer") or "").strip()

    # Dates
    issued_date = str(metadata.get("issued_date") or "").strip()
    effective_date = str(metadata.get("effective_date") or "").strip()
    published_date = str(metadata.get("published_date") or "").strip()

    # Status
    raw_status = str(metadata.get("status") or "active").strip()
    status = raw_status.lower()

    # Relations
    relations: dict[str, Any] = {}
    if isinstance(metadata.get("relations"), dict):
        relations = copy.deepcopy(metadata["relations"])

    # Replaces / Supersedes alias resolution
    for key in ("replaces", "supersedes", "guided_by", "replaces_docs"):
        val = metadata.get(key)
        if val:
            norm_key = "replaces" if key == "replaces_docs" else key
            if norm_key not in relations:
                relations[norm_key] = val

    # Assets & Relative Paths
    file_path = str(metadata.get("file_path") or "")
    markdown_path = str(metadata.get("markdown_path") or "")

    # Auto-detect primary .md or .docx in bundle directory if missing
    if not markdown_path and bundle_dir.exists():
        # Look for <bundle_dir.name>.md or index.md or full_text.md
        cand_md = bundle_dir / f"{bundle_dir.name}.md"
        if not cand_md.exists():
            cand_md = bundle_dir / "full_text.md"
        if not cand_md.exists():
            cand_md = bundle_dir / "index.md"
        if cand_md.exists():
            if project_root:
                try:
                    markdown_path = str(cand_md.relative_to(project_root)).replace("\\", "/")
                except ValueError:
                    markdown_path = str(cand_md).replace("\\", "/")
            else:
                markdown_path = str(cand_md).replace("\\", "/")

    if not file_path and bundle_dir.exists():
        for docx_file in bundle_dir.glob("*.docx"):
            if not docx_file.name.startswith("~$"):
                if project_root:
                    try:
                        file_path = str(docx_file.relative_to(project_root)).replace("\\", "/")
                    except ValueError:
                        file_path = str(docx_file).replace("\\", "/")
                else:
                    file_path = str(docx_file).replace("\\", "/")
                break

    # SHA256 checksum
    sha256 = str(metadata.get("sha256") or "")
    if not sha256 and isinstance(metadata.get("source_assets"), dict):
        sa = metadata["source_assets"]
        sha256 = str(sa.get("pdf_sha256") or sa.get("docx_sha256") or "")

    # Source URL
    source_url = str(metadata.get("source_url") or metadata.get("url") or "")
    download_url = str(metadata.get("download_url") or "")

    # Topics
    topics = metadata.get("topics") or []
    if isinstance(topics, str):
        topics = [topics]

    doc_entry: dict[str, Any] = {
        "id": doc_id,
        "document_number": doc_number,
        "title": title,
        "type": raw_type,
        "issued_by": issued_by,
        "signer": signer,
        "issued_date": issued_date,
        "effective_date": effective_date,
        "published_date": published_date,
        "status": status,
        "relations": relations,
        "topics": list(topics),
        "source_url": source_url,
        "file_path": file_path,
        "markdown_path": markdown_path,
        "sha256": sha256,
    }
    if download_url:
        doc_entry["download_url"] = download_url

    # Preserve any other non-standard fields from sharded metadata
    for k, v in metadata.items():
        if k not in doc_entry and k not in (
            "doc_id",
            "doc_number",
            "issuer",
            "replaces_docs",
            "source_assets",
        ):
            doc_entry[k] = v

    # Clean empty string attributes if desired, but keep canonical fields intact
    return category, doc_entry


def sort_document_dict(doc: dict[str, Any]) -> dict[str, Any]:
    """Sort keys of a document dictionary according to canonical ordering for determinism."""
    sorted_dict: dict[str, Any] = {}
    # First canonical keys
    for k in CANONICAL_DOC_KEYS:
        if k in doc:
            sorted_dict[k] = doc[k]
    # Then remaining arbitrary keys in alphabetical order
    for k in sorted(doc.keys()):
        if k not in sorted_dict:
            sorted_dict[k] = doc[k]
    return sorted_dict


def compile_sharded_registry(
    docs_dir: Path | str,
    output_file: Path | str | None = None,
    base_registry_path: Path | str | None = None,
    check_only: bool = False,
    project_root: Path | str | None = None,
) -> tuple[dict[str, Any], bool, list[str]]:
    """Compile sharded metadata.yaml files into a consolidated legal_registry.yaml.

    Args:
        docs_dir: Directory containing legal document bundles with metadata.yaml.
        output_file: Target path to write compiled legal_registry.yaml.
        base_registry_path: Optional existing registry path to preserve non-document sections.
        check_only: If True, do not write to disk; verify synchronization and return diffs.
        project_root: Root directory for relative path resolution.

    Returns:
        tuple (compiled_data, is_in_sync, issues_or_diffs)
    """
    p_docs = Path(docs_dir).resolve()
    p_root = Path(project_root).resolve() if project_root else p_docs.parent
    p_out = Path(output_file).resolve() if output_file else None

    # Resolve base registry to preserve non-category sections (metadata, monitoring, seminars)
    base_path = Path(base_registry_path).resolve() if base_registry_path else p_out
    preserved_sections: dict[str, Any] = {
        "metadata": {
            "focus_area": "Quản lý chất lượng và quy chuẩn xây dựng",
            "maintained_by": "CCBA Platform — Autonomous Legal Compiler",
        },
        "monitoring": [],
        "seminars": [],
    }

    if base_path and base_path.is_file():
        try:
            with open(base_path, encoding="utf-8") as f:
                loaded_base = yaml.safe_load(f)
            if isinstance(loaded_base, dict):
                for k, v in loaded_base.items():
                    if k not in LEGAL_CATEGORIES:
                        preserved_sections[k] = v
        except Exception as e:
            logger.warning(f"Could not read base registry {base_path}: {e}")

    # Discover all metadata.yaml files deterministically
    sharded_files: list[Path] = []
    if p_docs.exists() and p_docs.is_dir():
        for meta_file in sorted(p_docs.rglob("metadata.yaml")):
            # Ignore hidden directories (.git, .venv, etc.)
            if not any(part.startswith(".") for part in meta_file.parts):
                sharded_files.append(meta_file)

    # Initialize categorized document buckets
    categorized: dict[str, list[dict[str, Any]]] = {cat: [] for cat in LEGAL_CATEGORIES}

    for meta_path in sharded_files:
        try:
            with open(meta_path, encoding="utf-8") as f:
                raw_meta = yaml.safe_load(f)
            if not isinstance(raw_meta, dict):
                continue
            cat, doc_entry = normalize_metadata_to_doc_entry(
                metadata=raw_meta,
                bundle_dir=meta_path.parent,
                project_root=p_root,
            )
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(sort_document_dict(doc_entry))
        except Exception as e:
            logger.error(f"Error parsing sharded metadata {meta_path}: {e}")

    # Deterministic sorting within each category
    for cat in categorized:
        categorized[cat].sort(key=lambda d: str(d.get("id", "")).lower())

    # Build final compiled registry dictionary
    compiled: dict[str, Any] = {}
    # First: metadata section
    if "metadata" in preserved_sections:
        compiled["metadata"] = preserved_sections["metadata"]

    # Next: canonical legal categories
    for cat in [
        "laws",
        "decrees",
        "circulars",
        "decisions",
        "resolutions",
        "standards",
    ]:
        compiled[cat] = categorized.get(cat, [])

    # Next: other preserved sections (monitoring, seminars, etc.)
    for k, v in preserved_sections.items():
        if k != "metadata" and k not in compiled:
            compiled[k] = v

    issues: list[str] = []
    is_in_sync = True

    # Compare with existing output file if check_only or checking parity
    if p_out and p_out.is_file():
        try:
            with open(p_out, encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}

            # Check for missing or differing documents across categories
            for cat in LEGAL_CATEGORIES:
                existing_docs: dict[str, Any] = {
                    str(d.get("id")): d
                    for d in existing.get(cat, [])
                    if isinstance(d, dict) and d.get("id")
                }
                compiled_docs: dict[str, Any] = {
                    str(d.get("id")): d
                    for d in compiled.get(cat, [])
                    if isinstance(d, dict) and d.get("id")
                }

                missing_in_existing: set[str] = set(compiled_docs.keys()) - set(
                    existing_docs.keys()
                )
                extra_in_existing: set[str] = set(existing_docs.keys()) - set(compiled_docs.keys())

                if missing_in_existing:
                    is_in_sync = False
                    issues.append(
                        f"Category '{cat}': {len(missing_in_existing)} sharded document(s) missing in {p_out.name}: "
                        + ", ".join(sorted(missing_in_existing))
                    )
                if extra_in_existing:
                    is_in_sync = False
                    issues.append(
                        f"Category '{cat}': {len(extra_in_existing)} document(s) in {p_out.name} not found in sharded docs: "
                        + ", ".join(sorted(extra_in_existing))
                    )
        except Exception as e:
            is_in_sync = False
            issues.append(f"Error comparing existing registry {p_out}: {e}")
    elif p_out and not p_out.exists():
        is_in_sync = False
        issues.append(f"Target registry file does not exist: {p_out}")

    # Write to disk if not check_only
    if not check_only and p_out:
        p_out.parent.mkdir(parents=True, exist_ok=True)
        with open(p_out, "w", encoding="utf-8") as f:
            yaml.safe_dump(compiled, f, allow_unicode=True, sort_keys=False)
        logger.info(f"Successfully compiled sharded registry to {p_out}")

    return compiled, is_in_sync, issues
