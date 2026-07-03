"""Registry manager for legal documents in CCBA.

Manages loading, updating, and saving information in the YAML registry
by dynamically resolving file paths relative to the project root.
"""

from pathlib import Path

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
            self.registry_path = (
                project_root
                / ".agents"
                / "skills"
                / "legal-document-tracker"
                / "resources"
                / "legal_registry.yaml"
            )

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
