"""Registry YAML I/O, clause mutation, document search, and additive merge helpers."""

from __future__ import annotations

import os
import re
import shutil
import stat
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.models import LegalDocStatus

_SEARCH_CATEGORIES: tuple[str, ...] = (
    "decrees",
    "laws",
    "circulars",
    "standards",
    "seminars",
    "decisions",
    "resolutions",
)

_MERGE_CATEGORIES: tuple[str, ...] = (
    "laws",
    "decrees",
    "circulars",
    "standards",
    "seminars",
    "decisions",
    "resolutions",
)


def empty_registry_dict() -> dict[str, Any]:
    """Return canonical empty CCBA registry skeleton."""
    return {
        "metadata": {},
        "laws": [],
        "decrees": [],
        "circulars": [],
        "decisions": [],
        "resolutions": [],
    }


def load_registry_yaml(registry_path: Path) -> dict[str, Any]:
    """Load YAML registry file or return canonical empty dictionary on missing/error."""
    if not registry_path.exists():
        print(
            f"[Registry] Warning: Registry file {registry_path} not found. Starting with empty registry."
        )
        return empty_registry_dict()
    with open(registry_path, encoding="utf-8") as f:
        try:
            res = yaml.safe_load(f)
            return res if isinstance(res, dict) else {}
        except Exception as e:
            print(f"[Registry] Error loading YAML: {e}")
            return empty_registry_dict()


def save_registry_yaml(
    registry_path: Path, data: dict[str, Any], max_retries: int = 3, retry_delay: float = 0.1
) -> None:
    """Persist registry YAML with read-only chmod clearance and file-lock retries."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(max_retries):
        try:
            if registry_path.exists():
                try:
                    os.chmod(registry_path, registry_path.stat().st_mode | stat.S_IWUSR)
                except Exception:
                    try:
                        os.chmod(registry_path, stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
            with open(registry_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
            print(f"[Registry] Successfully saved registry to {registry_path}")
            return
        except (PermissionError, OSError):
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)


def update_clause_status_in_data(
    data: dict[str, Any],
    target_doc_id: str,
    clause_anchor: str,
    status: str,
    amended_by: str,
    source_doc_path: str,
) -> bool:
    """Mutate one clause's lifecycle status in memory; return True if target document found."""
    norm_target = target_doc_id.lower().replace("-", "_")
    for docs in data.values():
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if (
                isinstance(doc, dict)
                and doc.get("id")
                and doc["id"].lower().replace("-", "_") == norm_target
            ):
                if "clauses" not in doc or not isinstance(doc["clauses"], dict):
                    doc["clauses"] = {}
                doc["clauses"][clause_anchor] = {
                    "status": status,
                    "amended_by": amended_by,
                    "source_doc_path": source_doc_path,
                }
                print(
                    f"[Registry] Set status of {target_doc_id} clause {clause_anchor} to '{status}'"
                )
                return True
    print(
        f"[Registry] Warning: Target doc {target_doc_id} not found in registry. Clause status not updated."
    )
    return False


def find_doc_by_id_in_data(data: dict[str, Any], doc_id: str) -> dict[str, Any] | None:
    """Find document dictionary in loaded registry by case-insensitive ID."""
    norm_id = doc_id.lower().replace("-", "_").replace("đ", "d")
    for docs in data.values():
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if (
                isinstance(doc, dict)
                and doc.get("id")
                and doc["id"].lower().replace("-", "_").replace("đ", "d") == norm_id
            ):
                return doc
    return None


def _norm_ident(val: Any) -> str:
    """Normalize ID, document number, or short name for fuzzy lookup."""
    return re.sub(r"[\s\-_/.,:]+", "", str(val or "").lower()).replace("đ", "d")


def find_doc_in_data(data: dict[str, Any], identifier: str) -> dict[str, Any] | None:
    """Find document by normalized ID, document_number, or short_name."""
    norm_target = _norm_ident(identifier)
    for docs in data.values():
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            doc_id = _norm_ident(doc.get("id"))
            doc_num = _norm_ident(doc.get("document_number"))
            short_name = _norm_ident(doc.get("short_name"))
            if norm_target in {doc_id, doc_num, short_name}:
                return doc
    return None


def resolve_markdown_path_for_doc(doc_metadata: dict[str, Any], project_root: Path) -> Path | None:
    """Resolve primary markdown path (`full_text.md` or `<slug>.md`) for a document."""
    if markdown_path_str := doc_metadata.get("markdown_path"):
        p = project_root / str(markdown_path_str)
        if p.exists():
            return p
    if file_path_str := doc_metadata.get("file_path"):
        p = project_root / str(file_path_str)
        if (full_text_p := p.parent / "full_text.md").exists():
            return full_text_p
        if (md_p := p.with_suffix(".md")).exists():
            return md_p

    slug = str(doc_metadata.get("id", "")).lower().replace("-", "_")
    legal_docs_dir = project_root / ".md" / "legal_docs"
    if legal_docs_dir.exists():
        for p in sorted(legal_docs_dir.rglob("*.md"), key=lambda path: path.as_posix()):
            if p.name == "full_text.md" and slug in p.parent.name.lower():
                return p
            if p.stem.lower() == slug:
                return p
    return None


def _score_doc_for_terms(doc: dict[str, Any], query_terms: list[str], is_empty_query: bool) -> int:
    """Compute keyword relevance score for a registry entry."""
    if is_empty_query:
        return 1
    title = str(doc.get("title", "")).lower()
    short_name = str(doc.get("short_name", "")).lower()
    topics = [str(t).lower() for t in doc.get("topics", [])]
    notes = str(doc.get("notes", "")).lower()
    doc_num = str(doc.get("document_number", "")).lower()
    doc_id = str(doc.get("id", "")).lower()
    combined = f"{title} {short_name} {doc_num} {doc_id} {' '.join(topics)} {notes}"

    score = 0
    for term in query_terms:
        if term in combined:
            score += 1
        if term in title or term in short_name:
            score += 2
        if any(term in t for t in topics):
            score += 3
        if term in doc_num or term in doc_id:
            score += 4
    return score


def _enrich_matched_doc(
    doc: dict[str, Any],
    doc_territory: str,
    include_expired: bool,
    get_lifecycle_fn: Callable[[str], dict[str, Any]],
) -> dict[str, Any] | None:
    """Annotate matched doc with lifecycle warning/replacement and apply expiration filter."""
    doc_copy = dict(doc)
    lifecycle = get_lifecycle_fn(str(doc.get("id", "")))
    doc_copy["status"] = lifecycle.get("status", LegalDocStatus.ACTIVE.value)
    doc_copy["is_superseded"] = lifecycle.get("status") == LegalDocStatus.SUPERSEDED.value
    doc_copy["territory"] = lifecycle.get("territory", doc_territory)
    doc_copy["hierarchy_level"] = lifecycle.get(
        "hierarchy_level", "national" if doc_territory == "VN" else "provincial"
    )
    if lifecycle.get("warning"):
        doc_copy["lifecycle_warning"] = lifecycle["warning"]
    if lifecycle.get("suggested_replacement"):
        doc_copy["suggested_replacement"] = lifecycle["suggested_replacement"]

    if not include_expired:
        stat_str = str(doc_copy.get("status", "")).strip().lower()
        if doc_copy.get("is_superseded") or stat_str in {
            "expired",
            "hết hiệu lực",
            "superseded",
            "bị thay thế",
        }:
            return None
    return doc_copy


def search_registry_docs(
    data: dict[str, Any],
    query_str: str,
    top_k: int,
    territory: str | None,
    include_expired: bool,
    get_lifecycle_fn: Callable[[str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Search and deterministically rank registry documents with geofence and lifecycle filter."""
    query_terms = [t.lower() for t in query_str.split() if len(t) > 1]
    is_empty = len(query_terms) == 0
    target_territory: str | None = None
    if territory:
        from ccba_legal.jurisdiction import normalize_jurisdiction

        target_territory = normalize_jurisdiction(territory)

    matched_docs: list[tuple[int, dict[str, Any]]] = []
    for category in _SEARCH_CATEGORIES:
        for doc in data.get(category, []):
            if not isinstance(doc, dict):
                continue
            doc_territory = str(doc.get("territory", "VN"))
            if target_territory and doc_territory not in {"VN", target_territory}:
                continue
            score = _score_doc_for_terms(doc, query_terms, is_empty)
            if score > 0 and (
                enriched := _enrich_matched_doc(
                    doc, doc_territory, include_expired, get_lifecycle_fn
                )
            ):
                matched_docs.append((score, enriched))

    matched_docs.sort(key=lambda x: (-x[0], str(x[1].get("id", ""))))
    return [doc for _score, doc in matched_docs[:top_k]]


def _merge_category_docs(
    local_docs: list[Any], master_docs: list[Any], counts: dict[str, int]
) -> None:
    """Merge master category entries into local_docs while preserving custom local notes."""
    for m_doc in master_docs:
        if not isinstance(m_doc, dict) or not m_doc.get("id"):
            continue
        m_id = str(m_doc["id"]).strip()
        m_num = str(m_doc.get("document_number", "")).strip()
        local_idx = -1
        for idx, l_doc in enumerate(local_docs):
            if not isinstance(l_doc, dict):
                continue
            l_id = str(l_doc.get("id", "")).strip()
            l_num = str(l_doc.get("document_number", "")).strip()
            if (l_id and l_id.lower() == m_id.lower()) or (
                m_num and l_num and l_num.lower() == m_num.lower()
            ):
                local_idx = idx
                break
        if local_idx >= 0:
            target = local_docs[local_idx]
            for k, v in m_doc.items():
                if not (k == "notes" and target.get("notes") and target["notes"] != v):
                    target[k] = v
            counts["updated"] += 1
        else:
            local_docs.append(dict(m_doc))
            counts["added"] += 1


def merge_master_into_local_data(
    registry_path: Path,
    local_data: dict[str, Any],
    master_registry_data: dict[str, Any],
    backup: bool,
) -> dict[str, int]:
    """Perform non-destructive additive merge of master registry into local_data."""
    if backup and registry_path.exists():
        backup_dir = registry_path.parent.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_path = backup_dir / f"{registry_path.name}.bak_{ts}"
        shutil.copy2(registry_path, bak_path)
        print(f"[Registry] Created local backup at: {bak_path}")

    counts = {"updated": 0, "added": 0, "preserved": 0}
    if "metadata" not in local_data:
        local_data["metadata"] = master_registry_data.get("metadata", {})
    elif "metadata" in master_registry_data:
        local_data["metadata"]["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for category in _MERGE_CATEGORIES:
        if category not in local_data or not isinstance(local_data[category], list):
            local_data[category] = []
        master_docs = master_registry_data.get(category, [])
        if isinstance(master_docs, list):
            _merge_category_docs(local_data[category], master_docs, counts)
    return counts


def format_citation(doc: dict[str, Any]) -> str:
    """Format a legal document citation strictly `[Short Name - Doc Number]`."""
    short_name = doc.get("short_name") or doc.get("id", "VBPL")
    doc_num = doc.get("document_number")
    return f"[{short_name} - {doc_num}]" if doc_num else f"[{short_name}]"
