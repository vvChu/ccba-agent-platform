"""Registry manager for legal documents in CCBA.

Manages loading, updating, saving information in the YAML registry
by dynamically resolving file paths relative to the project root.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ccba_legal._registry_discovery import (
    _collect_hub_candidates,
    _discover_tier3_to_6_for_root,
    _find_registry_under,
    _resolve_registry_from_hub,
    _resolve_registry_from_local_candidates,
    _resolve_registry_in_context,
    _resolve_registry_tier12,
)
from ccba_legal._registry_lifecycle import (
    DEFAULT_RELATION_SYNONYMS,
    KNOWN_STATUTORY_REPLACEMENTS,
    build_inverted_replacements,
    find_active_delegation_document,
    load_relation_synonyms_from_root,
    resolve_document_lifecycle,
)
from ccba_legal._registry_query import (
    find_doc_by_id_in_data,
    find_doc_in_data,
    format_citation,
    load_registry_yaml,
    merge_master_into_local_data,
    resolve_markdown_path_for_doc,
    save_registry_yaml,
    search_registry_docs,
    update_clause_status_in_data,
)


def resolve_project_root() -> Path:
    """Resolve the workspace or Hub root directory via the unified workspace_roots seam."""
    from ccba_harness import resolve_workspace_and_hub_roots

    return resolve_workspace_and_hub_roots(Path(__file__).resolve()).workspace_root


def discover_master_registry_path(custom_path: Path | str | None = None) -> Path:
    """Discover the canonical Master Legal Registry path across Hub and Spoke environments (ADR 0050)."""
    if tier12 := _resolve_registry_tier12(custom_path):
        return tier12
    # Call resolve_project_root() on the facade at runtime so mock patches on ccba_legal.registry take effect.
    project_root = resolve_project_root()
    return _discover_tier3_to_6_for_root(project_root)


class LegalRegistryManager:
    """Manages loading, updating, saving and lifecycle resolution of the CCBA Legal Document Registry."""

    def __init__(self, registry_path: Path | str | None = None) -> None:
        """Initialize manager, resolving default registry paths relative to workspace or master registry."""
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            cwd_cand = Path.cwd() / ".md" / "data" / "legal_registry.yaml"
            self.registry_path = (
                cwd_cand.resolve() if cwd_cand.is_file() else discover_master_registry_path()
            )
        self._inverted_replacements: dict[str, dict[str, Any]] = {}

    def load(self) -> dict[str, Any]:
        """Load the legal document registry from YAML."""
        loaded = load_registry_yaml(self.registry_path)
        self._inverted_replacements.clear()
        self._inverted_replacements.update(build_inverted_replacements(loaded))
        return loaded

    def save(self, data: dict[str, Any], max_retries: int = 3, retry_delay: float = 0.1) -> None:
        """Save the updated registry to YAML with Windows Read-Only clearance and lock retry."""
        save_registry_yaml(
            self.registry_path, data, max_retries=max_retries, retry_delay=retry_delay
        )

    def register_document(self, doc_id: str, doc_data: dict[str, Any]) -> None:
        """Register or update a document in the registry."""
        doc_type = str(doc_data.get("type", "")).lower()
        category = "laws"
        for kw, cat in (
            ("nghị định", "decrees"),
            ("decree", "decrees"),
            ("thông tư", "circulars"),
            ("circular", "circulars"),
            ("quyết định", "decisions"),
            ("decision", "decisions"),
            ("nghị quyết", "resolutions"),
            ("resolution", "resolutions"),
        ):
            if kw in doc_type:
                category = cat
                break
        self.add_or_update_doc(category, doc_id, doc_data)

    def add_or_update_doc(self, category: str, doc_id: str, doc_data: dict[str, Any]) -> None:
        """Add a new document entry or update an existing one under the specified category."""
        data = self.load()
        if category not in data:
            data[category] = []
        existing_idx = next(
            (idx for idx, doc in enumerate(data[category]) if doc.get("id") == doc_id), -1
        )
        if existing_idx >= 0:
            data[category][existing_idx].update(doc_data)
            print(f"[Registry] Updated doc ID {doc_id} in {category}")
        else:
            new_doc = {"id": doc_id, **doc_data}
            data[category].append(new_doc)
            print(f"[Registry] Added new doc ID {doc_id} to {category}")
        self.save(data)

    def update_clause_status(
        self,
        target_doc_id: str,
        clause_anchor: str,
        status: str,
        amended_by: str,
        source_doc_path: str,
    ) -> None:
        """Update the status of a specific clause in a registered document."""
        data = self.load()
        if update_clause_status_in_data(
            data, target_doc_id, clause_anchor, status, amended_by, source_doc_path
        ):
            self.save(data)

    def find_doc_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Find a document in the registry by its ID (case-insensitive)."""
        return find_doc_by_id_in_data(self.load(), doc_id)

    def find_doc(self, identifier: str) -> dict[str, Any] | None:
        """Find a document by ID, document_number, or short_name (case/punctuation insensitive)."""
        return find_doc_in_data(self.load(), identifier)

    def get_lifecycle(self, identifier: str) -> dict[str, Any]:
        """Resolve full lifecycle information, validity status, and replacement warnings (ADR 0050)."""
        if not self._inverted_replacements:
            self.load()
        return resolve_document_lifecycle(self.find_doc, self._inverted_replacements, identifier)

    def get_markdown_path_for_doc(self, doc_metadata: dict[str, Any]) -> Path | None:
        """Resolve the path to the main markdown file (`full_text.md` or `<slug>.md`)."""
        project_root = resolve_project_root()
        return resolve_markdown_path_for_doc(doc_metadata, project_root)

    def search(
        self,
        query: str,
        top_k: int = 5,
        territory: str | None = None,
        include_expired: bool = False,
    ) -> list[dict[str, Any]]:
        """Search legal registry documents matching query terms (ADR 0050)."""
        return search_registry_docs(
            self.load(), query, top_k, territory, include_expired, self.get_lifecycle
        )

    def merge_with_master_registry(
        self, master_registry_data: dict[str, Any], backup: bool = True
    ) -> dict[str, int]:
        """Perform Non-Destructive Additive Merge from master registry data (ADR 0050)."""
        local_data = self.load()
        counts = merge_master_into_local_data(
            self.registry_path, local_data, master_registry_data, backup=backup
        )
        self.save(local_data)
        return counts


def load_relation_synonyms(project_root: Path | None = None) -> dict[str, str]:
    """Load relation synonyms configuration from YAML and return a synonym-to-key mapping."""
    resolved_root = resolve_project_root() if project_root is None else project_root
    return load_relation_synonyms_from_root(resolved_root)


def load_legal_registry(registry_path: Path | str | None = None) -> dict[str, Any]:
    """Safely load and parse legal_registry.yaml into a dictionary."""
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.load()


def search_legal_registry(
    query: str,
    registry_path: Path | str | None = None,
    top_k: int = 5,
    territory: str | None = None,
) -> list[dict[str, Any]]:
    """Search legal registry documents matching query terms across titles, topics, and notes."""
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.search(query=query, top_k=top_k, territory=territory)


def get_lifecycle(identifier: str, registry_path: Path | str | None = None) -> dict[str, Any]:
    """Resolve full lifecycle information, validity status, and replacement warnings (ADR 0050)."""
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.get_lifecycle(identifier)


def query(
    search_query: str,
    registry_path: Path | str | None = None,
    top_k: int = 5,
    include_expired: bool = False,
) -> list[dict[str, Any]]:
    """High-level query API searching legal registry with automatic lifecycle warnings (ADR 0050)."""
    from ccba_legal.engine import LegalKnowledgeEngine

    engine = LegalKnowledgeEngine(registry_path=registry_path)
    return engine.search(query=search_query, top_k=top_k, include_expired=include_expired)


def get_active_delegation_document(
    territory: str,
    domain: str = "construction",
    as_of_date: str | None = None,
    registry_path: Path | str | None = None,
) -> dict[str, Any] | None:
    """Discover the active delegation document for a given territory and domain from the registry."""
    from ccba_legal.jurisdiction import normalize_jurisdiction

    norm_jur = normalize_jurisdiction(territory)
    if norm_jur == "VN":
        return None
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    target_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
    return find_active_delegation_document(mgr.load(), norm_jur, domain, target_date)


__all__ = [
    "DEFAULT_RELATION_SYNONYMS",
    "KNOWN_STATUTORY_REPLACEMENTS",
    "LegalRegistryManager",
    "_collect_hub_candidates",
    "_find_registry_under",
    "_resolve_registry_from_hub",
    "_resolve_registry_from_local_candidates",
    "_resolve_registry_in_context",
    "_resolve_registry_tier12",
    "discover_master_registry_path",
    "format_citation",
    "get_active_delegation_document",
    "get_lifecycle",
    "load_legal_registry",
    "load_relation_synonyms",
    "query",
    "resolve_project_root",
    "search_legal_registry",
]
