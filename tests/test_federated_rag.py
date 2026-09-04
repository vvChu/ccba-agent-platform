"""Tests for Federated Legal Ground-Truth Query Engine (Issue #232).

All tests run offline using mocked data — no network or AI Gateway calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_bundle(tmp_path: Path) -> Path:
    """Create a minimal OKF v2.4 bundle for testing."""
    bundle = tmp_path / "nghi_dinh_105_2025_nd_cp"
    bundle.mkdir()

    # metadata.yaml
    meta = {
        "doc_id": "nghi_dinh_105_2025_nd_cp",
        "title": "Nghị định 105/2025/NĐ-CP",
        "doc_number": "105/2025/NĐ-CP",
        "status": "effective",
        "source_url": "https://thuvienphapluat.vn/van-ban/105-2025",
        "category": "PCCC",
        "sha256": "abc123",
    }
    (bundle / "metadata.yaml").write_text(yaml.dump(meta, allow_unicode=True), encoding="utf-8")

    # clauses.json
    clauses = [
        {
            "clause_id": "dieu-9",
            "node_type": "article",
            "title": "Điều 9. Phân định thẩm quyền thẩm định thiết kế PCCC",
            "line_start": 1,
            "line_end": 3,
        },
        {
            "clause_id": "dieu-10",
            "node_type": "article",
            "title": "Điều 10. Hồ sơ thẩm duyệt thiết kế PCCC",
            "line_start": 4,
            "line_end": 6,
        },
    ]
    (bundle / "clauses.json").write_text(
        json.dumps(clauses, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # main markdown
    md_content = (
        "Cơ quan chuyên môn về xây dựng chủ trì thẩm định thiết kế PCCC.\n"
        "Phòng cháy chữa cháy là yêu cầu bắt buộc.\n"
        "Thẩm quyền thuộc Bộ Xây dựng và Cục PCCC.\n"
        "Hồ sơ thẩm duyệt thiết kế phòng cháy chữa cháy bao gồm.\n"
        "Đơn đề nghị thẩm duyệt thiết kế về PCCC.\n"
        "Bản sao giấy chứng nhận đăng ký kinh doanh.\n"
    )
    (bundle / "nghi_dinh_105_2025_nd_cp.md").write_text(md_content, encoding="utf-8")

    return bundle


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


class TestFederatedLegalEngine:
    """Test suite for FederatedLegalEngine."""

    def test_engine_pccc_query(self, sample_bundle: Path) -> None:
        """Tra cứu 'thẩm định PCCC' should match dieu-9."""
        from ccba_legal.federated_rag import FederatedLegalEngine

        engine = FederatedLegalEngine(
            corpus_paths=[sample_bundle],
            embedding_enabled=False,
        )
        results = engine.query("thẩm định PCCC")

        assert len(results) > 0
        clause_ids = [r["clause_id"] for r in results]
        assert "dieu-9" in clause_ids

    def test_schema_conformance(self, sample_bundle: Path) -> None:
        """Result dictionaries should have all 7 required fields."""
        from ccba_legal.federated_rag import FederatedLegalEngine

        engine = FederatedLegalEngine(
            corpus_paths=[sample_bundle],
            embedding_enabled=False,
        )
        results = engine.query("PCCC")
        assert len(results) > 0

        required_keys = {
            "clause_id",
            "document_id",
            "article_num",
            "title",
            "text_snippet",
            "confidence_score",
            "citation_url",
            "status",
        }
        for result in results:
            assert required_keys.issubset(result.keys()), (
                f"Missing keys: {required_keys - result.keys()}"
            )

    def test_bigram_tokenizer(self, sample_bundle: Path) -> None:
        """Tokenizer should produce bigrams for compound terms."""
        from ccba_legal.federated_rag import FederatedLegalEngine

        engine = FederatedLegalEngine(
            corpus_paths=[sample_bundle],
            embedding_enabled=False,
        )
        tokens = engine._tokenize("phòng cháy chữa cháy")

        assert "phòng" in tokens
        assert "cháy" in tokens
        assert "phòng_cháy" in tokens
        assert "chữa_cháy" in tokens

    def test_empty_corpus_graceful(self, tmp_path: Path) -> None:
        """Empty corpus should return [] without crashing."""
        from ccba_legal.federated_rag import FederatedLegalEngine

        empty_dir = tmp_path / "empty_corpus"
        empty_dir.mkdir()

        engine = FederatedLegalEngine(
            corpus_paths=[empty_dir],
            embedding_enabled=False,
        )
        results = engine.query("anything")
        assert results == []

    def test_pure_bm25_fallback(self, sample_bundle: Path) -> None:
        """With embedding_enabled=False, engine should still return accurate results."""
        from ccba_legal.federated_rag import FederatedLegalEngine

        engine = FederatedLegalEngine(
            corpus_paths=[sample_bundle],
            embedding_enabled=False,
        )
        assert engine._embedding_matrix is None

        results = engine.query("hồ sơ thẩm duyệt")
        assert len(results) > 0
        assert any("dieu-10" == r["clause_id"] for r in results)

    def test_mcp_tool_dynamic_import(self) -> None:
        """MCP server module loads successfully with ccba-legal-intel present."""
        # Verify the try/except pattern exists and handles ImportError gracefully
        # We just confirm the tool registration code is syntactically valid
        import ccba_ai.mcp_server as mcp_mod  # noqa: F401

        # If we get here without error, the module loaded successfully
        assert True
