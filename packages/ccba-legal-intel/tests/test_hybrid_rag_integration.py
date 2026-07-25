"""Unit tests for LegalHybridRAG integration in ccba_legal."""

from ccba_legal.hybrid_rag import LegalHybridRAG


def test_legal_hybrid_rag_indexing_and_query() -> None:
    """Test indexing legal document content and querying via BM25 / keyword scoring."""
    doc1 = """# Luật Phòng cháy và chữa cháy 2024
Điều 12. Phương tiện PCCC cho hộ gia đình
Hộ gia đình phải trang bị ít nhất 01 bình chữa cháy xách tay và dụng cụ phá dỡ thô sơ.
"""
    doc2 = """# Luật Đất đai 2024
Điều 15. Quy hoạch sử dụng đất
Quy hoạch sử dụng đất cấp tỉnh phải được phê duyệt trước ngày 31 tháng 12.
"""

    rag = LegalHybridRAG()
    rag.index_document("Luat-55-2024", doc1)
    rag.index_document("Luat-31-2024", doc2)

    # Query 1: PCCC query should match doc1
    results = rag.query("bình chữa cháy hộ gia đình PCCC", top_k=2)
    assert len(results) > 0
    assert results[0]["doc_id"] == "Luat-55-2024"
    assert "bình chữa cháy" in results[0]["snippet"]

    # Query 2: Land query should match doc2
    results_land = rag.query("quy hoạch sử dụng đất cấp tỉnh", top_k=2)
    assert len(results_land) > 0
    assert results_land[0]["doc_id"] == "Luat-31-2024"
