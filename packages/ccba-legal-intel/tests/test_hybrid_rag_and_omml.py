"""Unit tests for LegalHybridRAG and OMML Delimiters."""

from ccba_legal.converters.omml import _format_delimiter, omml_to_latex
from ccba_legal.hybrid_rag import LegalHybridRAG


def test_hybrid_rag_query() -> None:
    rag = LegalHybridRAG()
    rag.index_document("doc1", "Quy chuẩn kỹ thuật quốc gia về an toàn cháy cho nhà và công trình")
    rag.index_document("doc2", "Tiêu chuẩn thiết kế kết cấu bê tông cốt thép tải trọng gió")
    rag.index_document("doc3", "Nghị định quy định chi tiết một số điều của Luật Xây dựng")

    # Query matching doc1
    res1 = rag.query("an toàn cháy công trình", top_k=2)
    assert len(res1) > 0
    assert res1[0]["doc_id"] == "doc1"
    assert res1[0]["score"] > 0

    # Query matching doc2
    res2 = rag.query("tải trọng gió bê tông", top_k=2)
    assert len(res2) > 0
    assert res2[0]["doc_id"] == "doc2"

    # Empty query
    assert rag.query("") == []


def test_omml_delimiter_mapping() -> None:
    # Open / Close parentheses
    assert _format_delimiter("(", is_left=True) == r"\left("
    assert _format_delimiter(")", is_left=False) == r"\right)"

    # Open / Close brackets
    assert _format_delimiter("[", is_left=True) == r"\left["
    assert _format_delimiter("]", is_left=False) == r"\right]"

    # Reverse delimiters (e.g. interval ]a, b[)
    assert _format_delimiter("]", is_left=True) == r"\left]"
    assert _format_delimiter("[", is_left=False) == r"\right["
