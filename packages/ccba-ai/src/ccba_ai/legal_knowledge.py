"""Smart Resolution Gateway module for CCBA Legal Knowledge Access.

NOTE: The `legal_knowledge` singleton exported from this module currently has
zero active callers outside ccba_ai itself. It is retained for API stability
but should be migrated to ccba-legal-intel if active usage emerges.
"""

import os
from pathlib import Path
from typing import Any

import yaml

HUB_FALLBACK_PATH = Path(__file__).parents[4] / ".md" / "legal_docs"


class LegalKnowledgeGateway:
    """Smart Resolution Gateway 3-Layer Fallback for CCBA Legal Knowledge."""

    def __init__(self, custom_spoke_path: str | None = None):
        env_path = custom_spoke_path or os.getenv("CCBA_KNOWLEDGE_SPOKE_PATH")
        self.spoke_path = Path(env_path) if env_path else None

        env_reg = os.getenv("CCBA_KNOWLEDGE_REGISTRY_PATH")
        self.registry_path = Path(env_reg) if env_reg else None

    def get_registry(self) -> dict[str, Any]:
        """Layer 1: Local Spoke Registry -> Layer 2: Hub Registry Fallback."""
        # Layer 1: Env-configured registry
        if self.registry_path and self.registry_path.exists():
            try:
                return yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or {}
            except Exception:
                pass

        # Layer 2: Hub fallback
        hub_reg = HUB_FALLBACK_PATH / "legal_registry.yaml"
        if hub_reg.exists():
            try:
                return yaml.safe_load(hub_reg.read_text(encoding="utf-8")) or {}
            except Exception:
                pass

        return {"version": "2.0.0", "documents": []}

    def search_documents(self, query: str) -> list[dict[str, Any]]:
        """Search documents across resolution layers."""
        reg = self.get_registry()
        docs = reg.get("documents", [])
        results = []
        q_lower = query.lower()
        for doc in docs:
            title = doc.get("title", "").lower()
            doc_id = doc.get("id", "").lower()
            if q_lower in title or q_lower in doc_id:
                results.append(doc)
        return results

    def get_document_content(self, doc_slug: str) -> str | None:
        """Fetch document content prioritizing Local Spoke -> Hub Fallback."""
        # Layer 1: Check Local Spoke (only if configured via env)
        if self.spoke_path and self.spoke_path.exists():
            matches = list(self.spoke_path.glob(f"**/{doc_slug}*.md"))
            if matches:
                consolidated = [m for m in matches if "hop_nhat" in m.name]
                target = consolidated[0] if consolidated else matches[0]
                return target.read_text(encoding="utf-8")

        # Layer 2: Check Hub
        if HUB_FALLBACK_PATH.exists():
            matches = list(HUB_FALLBACK_PATH.glob(f"**/{doc_slug}*.md"))
            if matches:
                consolidated = [m for m in matches if "hop_nhat" in m.name]
                target = consolidated[0] if consolidated else matches[0]
                return target.read_text(encoding="utf-8")

        return None


# Singleton Instance
legal_knowledge = LegalKnowledgeGateway()
