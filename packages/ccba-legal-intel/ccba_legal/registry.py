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

    def process_amendments_from_document(
        self, source_doc_id: str, source_doc_content: str, source_doc_path: str
    ) -> list[dict]:
        """Parse clause-level changes from the source document, update registry, and inject warnings in target documents."""
        from ccba_legal.parser import LegalAnalysisEngine

        engine = LegalAnalysisEngine()

        modifications = engine.extract_amendments(source_doc_content, source_doc_path)

        for mod in modifications:
            target_doc_id = mod.get("target_doc_id")
            target_anchor = mod.get("target_anchor")
            amendment_source = mod.get("amendment_source")
            mod_source_doc_path = mod.get("source_doc_path", source_doc_path)

            if not target_doc_id or not target_anchor:
                continue

            self.update_clause_status(
                target_doc_id=target_doc_id,
                clause_anchor=target_anchor,
                status="amended",
                amended_by=amendment_source,
                source_doc_path=mod_source_doc_path,
            )

            target_meta = self.find_doc_by_id(target_doc_id)
            if target_meta:
                markdown_path = self.get_markdown_path_for_doc(target_meta)
                if markdown_path and markdown_path.exists():
                    try:
                        content = markdown_path.read_text(encoding="utf-8")
                        from ccba_legal.packager import inject_warning_block

                        updated_content = inject_warning_block(
                            markdown_content=content,
                            target_anchor=target_anchor,
                            amendment_source=amendment_source,
                            source_doc_path=mod_source_doc_path,
                        )
                        markdown_path.write_text(updated_content, encoding="utf-8")
                        print(
                            f"[Registry] Injected warning in target {target_doc_id} at {target_anchor}"
                        )
                    except Exception as e:
                        print(f"[Registry] Error injecting warning into {markdown_path}: {e}")

        return modifications
