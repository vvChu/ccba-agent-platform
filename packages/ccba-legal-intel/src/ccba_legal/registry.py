"""Registry manager for legal documents in CCBA.

Manages loading, updating, and saving information in the YAML registry
by dynamically resolving file paths relative to the project root.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def resolve_project_root() -> Path:
    """Traverse upwards from the current file to find the project root directory.

    Looks for common project indicators such as a .git directory or a pyproject.toml file.
    If none is found, falls back to Path.cwd().
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


class LegalRegistryManager:
    """Manages loading, updating, and saving of the CCBA Legal Document Registry (legal_registry.yaml)."""

    def __init__(self, registry_path: Path | None = None) -> None:
        """Initialize the manager, resolving default registry paths relative to the project root."""
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            project_root = resolve_project_root()
            self.registry_path = project_root / ".md" / "data" / "legal_registry.yaml"

    def load(self) -> dict:
        """Load the legal document registry from YAML."""
        if not self.registry_path.exists():
            print(
                f"[Registry] Warning: Registry file {self.registry_path} not found. Starting with empty registry."
            )
            return {"metadata": {}, "laws": [], "decrees": [], "circulars": []}

        with open(self.registry_path, encoding="utf-8") as f:
            try:
                return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[Registry] Error loading YAML: {e}")
                return {"metadata": {}, "laws": [], "decrees": [], "circulars": []}

    def save(self, data: dict) -> None:
        """Save the updated registry to YAML."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"[Registry] Successfully saved registry to {self.registry_path}")

    def register_document(self, doc_id: str, doc_data: dict) -> None:
        """Register or update a document in the registry."""
        doc_type = doc_data.get("type", "").lower()
        category = "laws"
        if "nghị định" in doc_type or "decree" in doc_type:
            category = "decrees"
        elif "thông tư" in doc_type or "circular" in doc_type:
            category = "circulars"
        self.add_or_update_doc(category, doc_id, doc_data)

    def add_or_update_doc(self, category: str, doc_id: str, doc_data: dict) -> None:
        """Add a new document entry or update an existing one under the specified category (laws / decrees)."""
        data = self.load()
        if category not in data:
            data[category] = []

        # Find existing document
        existing_idx = -1
        for idx, doc in enumerate(data[category]):
            if doc.get("id") == doc_id:
                existing_idx = idx
                break

        if existing_idx >= 0:
            # Update existing
            data[category][existing_idx].update(doc_data)
            print(f"[Registry] Updated doc ID {doc_id} in {category}")
        else:
            # Add new
            new_doc = {"id": doc_id}
            new_doc.update(doc_data)
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
        """Update the status of a specific clause in a registered document.

        Args:
            target_doc_id: The ID of the target document (e.g. 'ND-06-2021').
            clause_anchor: The anchor representing the clause (e.g. 'd15k2').
            status: The status (e.g., 'amended').
            amended_by: The source making the amendment (e.g., 'Điều 1 Thông tư B').
            source_doc_path: Path of the source document making the amendment.
        """
        data = self.load()
        norm_target = target_doc_id.lower().replace("-", "_")

        found = False
        # Iterate over lists in YAML (laws, decrees, circulars, etc.)
        for _category, docs in data.items():
            if isinstance(docs, list):
                for doc in docs:
                    if (
                        isinstance(doc, dict)
                        and doc.get("id")
                        and doc["id"].lower().replace("-", "_") == norm_target
                    ):
                        # Initialize clauses section under document metadata if not exists
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
                        found = True
                        break
            if found:
                break

        if not found:
            print(
                f"[Registry] Warning: Target doc {target_doc_id} not found in registry. Clause status not updated."
            )
        else:
            self.save(data)

    def find_doc_by_id(self, doc_id: str) -> dict | None:
        """Find a document in the registry by its ID (case-insensitive)."""
        data = self.load()
        norm_id = doc_id.lower().replace("-", "_")
        for _category, docs in data.items():
            if isinstance(docs, list):
                for doc in docs:
                    if (
                        isinstance(doc, dict)
                        and doc.get("id")
                        and doc["id"].lower().replace("-", "_") == norm_id
                    ):
                        return doc
        return None

    def get_markdown_path_for_doc(self, doc_metadata: dict) -> Path | None:
        """Resolve the path to the main markdown file (full_text.md or doc_slug.md) for a document."""
        project_root = resolve_project_root()

        # 1. Check 'markdown_path' in metadata
        markdown_path_str = doc_metadata.get("markdown_path")
        if markdown_path_str:
            p = project_root / markdown_path_str
            if p.exists():
                return p

        # 2. Check 'file_path' in metadata
        file_path_str = doc_metadata.get("file_path")
        if file_path_str:
            p = project_root / file_path_str
            # Check for full_text.md in the folder of that file
            full_text_p = p.parent / "full_text.md"
            if full_text_p.exists():
                return full_text_p
            # Check if there is a .md file next to the .docx file
            md_p = p.with_suffix(".md")
            if md_p.exists():
                return md_p

        # 3. Fallback: search for files matching the title or short_name slug in legal_docs
        doc_id = doc_metadata.get("id", "")
        slug = doc_id.lower().replace("-", "_")
        legal_docs_dir = project_root / ".md" / "legal_docs"
        if legal_docs_dir.exists():
            for p in legal_docs_dir.rglob("*.md"):
                if p.name == "full_text.md" and slug in p.parent.name.lower():
                    return p
                if p.stem.lower() == slug:
                    return p
        return None

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search legal registry documents matching query terms across titles, topics, and notes.

        Args:
            query: Space-separated search query terms.
            top_k: Maximum number of top matching documents to return.

        Returns:
            List of matching document dictionaries sorted descending by relevance score.
        """
        data = self.load()
        query_terms = [t.lower() for t in query.split() if len(t) > 1]
        if not query_terms:
            return []

        matched_docs: list[tuple[int, dict[str, Any]]] = []
        categories = ["decrees", "laws", "circulars", "standards", "seminars"]

        for category in categories:
            docs = data.get(category, [])
            for doc in docs:
                if not isinstance(doc, dict):
                    continue

                score = 0
                title = str(doc.get("title", "")).lower()
                short_name = str(doc.get("short_name", "")).lower()
                topics = [str(t).lower() for t in doc.get("topics", [])]
                notes = str(doc.get("notes", "")).lower()
                doc_num = str(doc.get("document_number", "")).lower()

                combined_text = f"{title} {short_name} {doc_num} {' '.join(topics)} {notes}"

                for term in query_terms:
                    if term in combined_text:
                        score += 1
                    if term in title or term in short_name:
                        score += 2
                    if any(term in t for t in topics):
                        score += 3

                if score > 0:
                    matched_docs.append((score, doc))

        matched_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in matched_docs[:top_k]]


DEFAULT_RELATION_SYNONYMS = {
    "Văn bản bị sửa đổi bổ sung": "amends_docs",
    "Văn bản bị sửa đổi, bổ sung": "amends_docs",
    "Văn bản bị thay thế": "replaced_docs",
    "Văn bản được dẫn chiếu": "referenced_docs",
    "Văn bản được căn cứ": "basis_docs",
    "Văn bản được hướng dẫn": "guided_docs",
    "Văn bản được hợp nhất": "consolidated_docs",
    "Văn bản hướng dẫn": "guiding_docs",
    "Văn bản hợp nhất": "consolidations",
    "Văn bản sửa đổi bổ sung": "amended_by_docs",
    "Văn bản sửa đổi, bổ sung": "amended_by_docs",
    "Văn bản thay thế": "replaced_by_docs",
    "Văn bản liên quan cùng nội dung": "related_docs",
}


def load_relation_synonyms(project_root: Path | None = None) -> dict[str, str]:
    """Load relation synonyms configuration from YAML and return a synonym-to-key mapping.

    If the configuration file is missing or invalid, falls back to a default mapping.

    Returns:
        dict[str, str]: A dictionary mapping Vietnamese synonym phrases to CCBA relation keys.
    """
    if project_root is None:
        project_root = resolve_project_root()

    synonyms_path = (
        project_root
        / ".agents"
        / "skills"
        / "ccba-legal-intel"
        / "resources"
        / "relation_synonyms.yaml"
    )

    if not synonyms_path.exists():
        print(f"[Registry] Synonyms config not found at {synonyms_path}. Using default synonyms.")
        return DEFAULT_RELATION_SYNONYMS.copy()

    try:
        with open(synonyms_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        synonyms_dict = config.get("relation_synonyms", {})
        mapping = {}
        for key, synonyms in synonyms_dict.items():
            if isinstance(synonyms, list):
                for syn in synonyms:
                    mapping[syn] = key
                    norm_syn = re.sub(r"\s+", " ", syn.replace(",", "")).strip()
                    mapping[norm_syn] = key
            elif isinstance(synonyms, str):
                mapping[synonyms] = key
                norm_syn = re.sub(r"\s+", " ", synonyms.replace(",", "")).strip()
                mapping[norm_syn] = key
        return mapping
    except Exception as e:
        print(
            f"[Registry] Error reading relation synonyms from {synonyms_path}: {e}. Using default synonyms."
        )
        return DEFAULT_RELATION_SYNONYMS.copy()


def format_citation(doc: dict[str, Any]) -> str:
    """Format a legal document citation strictly [Short Name - Doc Number].

    Args:
        doc: Dictionary containing document metadata fields (short_name, document_number, id).

    Returns:
        Formatted citation string, e.g. '[Luật XD 2025 - 135/2025/QH15]'.
    """
    short_name = doc.get("short_name") or doc.get("id", "VBPL")
    doc_num = doc.get("document_number")
    if doc_num:
        return f"[{short_name} - {doc_num}]"
    return f"[{short_name}]"


def load_legal_registry(registry_path: Path | str | None = None) -> dict[str, Any]:
    """Safely load and parse legal_registry.yaml into a dictionary.

    Args:
        registry_path: Optional path to the legal_registry.yaml file.

    Returns:
        Loaded registry dictionary or empty structure if not found.
    """
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.load()


def search_legal_registry(
    query: str, registry_path: Path | str | None = None, top_k: int = 5
) -> list[dict[str, Any]]:
    """Search legal registry documents matching query terms across titles, topics, and notes.

    Args:
        query: Space-separated search query terms.
        registry_path: Optional path to legal_registry.yaml.
        top_k: Maximum number of top matching documents to return.

    Returns:
        List of matching document dictionaries sorted descending by relevance score.
    """
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.search(query=query, top_k=top_k)

