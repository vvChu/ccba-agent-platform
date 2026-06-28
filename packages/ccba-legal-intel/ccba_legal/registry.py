from pathlib import Path

import yaml


class LegalRegistryManager:
    """Manages loading, updating, and saving of the CCBA Legal Document Registry (legal_registry.yaml)."""

    def __init__(self, registry_path: Path | None = None) -> None:
        if registry_path:
            self.registry_path = registry_path
        else:
            # Fallback path inside ccba-agent-platform project structure
            self.registry_path = Path("d:/GitHubProjects/ccba-agent-platform/.agent/skills/_consulting/legal-document-tracker/registry/legal_registry.yaml")

    def load(self) -> dict:
        """Load the legal document registry from YAML."""
        if not self.registry_path.exists():
            print(f"[Registry] Warning: Registry file {self.registry_path} not found. Starting with empty registry.")
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
