"""Smart Resolution Gateway module for CCBA Legal Knowledge Access."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

SPOKE_LOCAL_PATH = Path("D:/GitHubProjects/ccba-legal-knowledge/legal_docs")
SPOKE_REGISTRY_PATH = Path("D:/GitHubProjects/ccba-legal-knowledge/legal_registry.yaml")
HUB_FALLBACK_PATH = Path(__file__).parents[4] / ".md" / "legal_docs"

class LegalKnowledgeGateway:
    """Smart Resolution Gateway 3-Layer Fallback for CCBA Legal Knowledge."""

    def __init__(self, custom_spoke_path: Optional[str] = None):
        if custom_spoke_path:
            self.spoke_path = Path(custom_spoke_path)
        else:
            env_path = os.getenv("CCBA_KNOWLEDGE_SPOKE_PATH")
            self.spoke_path = Path(env_path) if env_path else SPOKE_LOCAL_PATH

    def get_registry(self) -> Dict[str, Any]:
        """Layer 1: Local Spoke Registry -> Layer 2: Hub Registry Fallback."""
        if SPOKE_REGISTRY_PATH.exists():
            try:
                return yaml.safe_load(SPOKE_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
            except Exception:
                pass
        
        hub_reg = HUB_FALLBACK_PATH / "legal_registry.yaml"
        if hub_reg.exists():
            try:
                return yaml.safe_load(hub_reg.read_text(encoding="utf-8")) or {}
            except Exception:
                pass
        
        return {"version": "2.0.0", "documents": []}

    def search_documents(self, query: str) -> List[Dict[str, Any]]:
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

    def get_document_content(self, doc_slug: str) -> Optional[str]:
        """Fetch document content prioritizing Local Spoke -> Hub Fallback."""
        # Layer 1: Check Local Spoke
        if self.spoke_path.exists():
            matches = list(self.spoke_path.glob(f"**/{doc_slug}*.md"))
            if matches:
                # Prefer consolidated text if available
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
