"""Unit tests for Legal Registry Loader & RAG Indexer (Seam tests)."""

from pathlib import Path

from scripts.legal.legal_rag_indexer import (
    format_citation,
    load_legal_registry,
    search_legal_registry,
)

REGISTRY_PATH = Path(".agents/skills/legal-document-tracker/resources/legal_registry.yaml")


def test_load_legal_registry_valid_yaml():
    """Test that legal_registry.yaml can be parsed cleanly and contains essential categories."""
    data = load_legal_registry(REGISTRY_PATH)
    assert isinstance(data, dict)
    assert "decrees" in data or "laws" in data or "standards" in data

    # Verify metadata
    metadata = data.get("metadata", {})
    assert "focus_area" in metadata


def test_format_citation_structure():
    """Test citation formatting follows strict legal reference standards [Short Name - Document Number]."""
    doc = {
        "short_name": "Luật XD 2025",
        "document_number": "135/2025/QH15",
        "title": "Luật Xây dựng 2025",
        "status": "enacted",
    }
    citation = format_citation(doc)
    assert "[Luật XD 2025 - 135/2025/QH15]" in citation or "[Luật XD 2025]" in citation


def test_search_legal_registry_query_pccc():
    """Test search functionality matching keywords for PCCC and Quality Management."""
    results = search_legal_registry("an toàn cháy PCCC", registry_path=REGISTRY_PATH, top_k=3)
    assert len(results) > 0
    # Check that QCVN-06 or fire_safety topic is present in top results
    titles_and_topics = [
        str(doc.get("title", "")) + " " + " ".join(doc.get("topics", [])) for doc in results
    ]
    assert any(
        "cháy" in item.lower() or "fire_safety" in item.lower() for item in titles_and_topics
    )
