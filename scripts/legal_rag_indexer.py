"""Utility script and module for loading, indexing, and searching legal_registry.yaml."""

from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


def load_legal_registry(registry_path: Path) -> Dict[str, Any]:
    """Load and parse legal_registry.yaml safely."""
    path = Path(registry_path)
    if not path.is_file():
        raise FileNotFoundError(f"Registry file not found at: {registry_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def format_citation(doc: Dict[str, Any]) -> str:
    """Format a legal document citation strictly [Short Name - Doc Number]."""
    short_name = doc.get("short_name") or doc.get("id", "VBPL")
    doc_num = doc.get("document_number")
    if doc_num:
        return f"[{short_name} - {doc_num}]"
    return f"[{short_name}]"


def search_legal_registry(
    query: str,
    registry_path: Path,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Search legal registry documents matching query terms across titles, topics, and notes."""
    registry = load_legal_registry(registry_path)
    query_terms = [t.lower() for t in query.split() if len(t) > 1]
    
    matched_docs: List[tuple[int, Dict[str, Any]]] = []
    
    # Categories in registry (decrees, laws, circulars, standards, etc.)
    categories = ["decrees", "laws", "circulars", "standards", "seminars"]
    
    for category in categories:
        docs = registry.get(category, [])
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            
            score = 0
            title = doc.get("title", "").lower()
            short_name = doc.get("short_name", "").lower()
            topics = [str(t).lower() for t in doc.get("topics", [])]
            notes = str(doc.get("notes", "")).lower()
            
            combined_text = f"{title} {short_name} {' '.join(topics)} {notes}"
            
            for term in query_terms:
                if term in combined_text:
                    score += 1
                if term in title:
                    score += 2
                if any(term in t for t in topics):
                    score += 3
            
            if score > 0:
                matched_docs.append((score, doc))
                
    # Sort by relevance score descending
    matched_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in matched_docs[:top_k]]


if __name__ == "__main__":
    default_path = Path(".agents/skills/legal-document-tracker/resources/legal_registry.yaml")
    data = load_legal_registry(default_path)
    print(f"✅ Loaded legal registry with metadata: {data.get('metadata')}")
