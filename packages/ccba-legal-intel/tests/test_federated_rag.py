"""Unit tests for FederatedLegalEngine vectorized embedding and cache functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ccba_legal.federated_rag import FederatedLegalEngine


def test_federated_rag_embedding_cache_and_vectorized_search(tmp_path: Path) -> None:
    """Test embedding pre-normalization, .rag_cache path, and argpartition Top-K search."""
    cache_dir = tmp_path / ".rag_cache"
    cache_file = cache_dir / "legal_corpus_bge_m3_v1.npy"

    # Mock chunks
    mock_chunks = [
        {"clause_id": "c1", "text": "Quy định về phòng cháy và chữa cháy", "territory": "VN"},
        {"clause_id": "c2", "text": "Tiêu chuẩn thiết kế kết cấu thép xây dựng", "territory": "VN"},
        {"clause_id": "c3", "text": "Quy chuẩn an toàn lao động trong thi công", "territory": "VN"},
    ]

    # Mock embeddings (unnormalized random vectors, 3 items x 8 dims)
    rng = np.random.default_rng(42)
    fake_matrix = rng.standard_normal((3, 8), dtype=np.float32) * 5.0

    mock_client = MagicMock()
    mock_client.embed.side_effect = lambda texts: (
        fake_matrix.tolist() if len(texts) == 3 else [fake_matrix[0].tolist()]
    )

    with patch.dict("os.environ", {"CCBA_RAG_CACHE_DIR": str(cache_dir)}):
        with patch("ccba_ai.AIClient", return_value=mock_client):
            engine = FederatedLegalEngine.__new__(FederatedLegalEngine)
            engine._chunks = mock_chunks
            engine._corpus_paths = [tmp_path]
            engine._corpus_hash = "mock_hash_123"
            engine._embedding_matrix = None
            engine._bm25_index = None
            engine._embed_timeout = 5.0
            engine._embedding_enabled = True

            # 1. Build index from scratch
            engine._build_embedding_index()

            # Verify cache was written to specified .rag_cache location
            assert cache_file.exists()
            assert cache_file.with_suffix(".sha256").exists()
            assert cache_file.with_suffix(".sha256").read_text() == "mock_hash_123"

            # Verify matrix in memory is pre-normalized (L2 norm should be ~1.0)
            assert engine._embedding_matrix is not None
            norms = np.linalg.norm(engine._embedding_matrix, axis=1)
            np.testing.assert_allclose(norms, np.ones(3), rtol=1e-5)

            # 2. Re-load from cache and verify allow_pickle=False and pre-normalization
            engine._embedding_matrix = None
            with patch("numpy.load", wraps=np.load) as spy_load:
                engine._build_embedding_index()
                spy_load.assert_called_once_with(str(cache_file), allow_pickle=False)
                assert engine._embedding_matrix is not None
                norms_cached = np.linalg.norm(engine._embedding_matrix, axis=1)
                np.testing.assert_allclose(norms_cached, np.ones(3), rtol=1e-5)

            # 3. Test _search_embedding Top-K retrieval via argpartition
            mock_query_emb = fake_matrix[0].tolist()
            mock_client.embed.return_value = [mock_query_emb]

            results = engine._search_embedding("phòng cháy", top_k=2)
            assert len(results) == 2
            # First item should be index 0 with highest score (~1.0 cosine similarity)
            assert results[0][0] == 0
            assert results[0][1] >= results[1][1]
            assert pytest.approx(results[0][1], abs=1e-4) == 1.0


def test_federated_rag_search_alias(tmp_path: Path) -> None:
    """Test search() alias method forwards to query()."""
    engine = FederatedLegalEngine.__new__(FederatedLegalEngine)
    engine.query = MagicMock(return_value=[{"clause_id": "c1"}])

    res = engine.search("pccc", top_k=3, jurisdiction="VN")
    engine.query.assert_called_once_with(
        query_text="pccc",
        domain=None,
        jurisdiction="VN",
        as_of_date=None,
        top_k=3,
        k_local_min=None,
        include_expired=False,
    )
    assert res == [{"clause_id": "c1"}]
