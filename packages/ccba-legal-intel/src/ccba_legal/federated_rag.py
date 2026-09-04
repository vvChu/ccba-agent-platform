"""Federated Legal Ground-Truth Query Engine.

Hybrid Search combining BM25 (keyword) + Embedding (semantic, optional)
+ Reciprocal Rank Fusion over OKF v2.4 legal knowledge bundles.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FederatedLegalEngine:
    """Federated Legal Ground-Truth Query Engine (ADR 0049, ADR 0010).

    Hybrid Search combining BM25 + Embedding (optional) + RRF Fusion
    on OKF v2.4 legal knowledge corpus with configurable paths.
    """

    def __init__(
        self,
        corpus_paths: list[Path] | None = None,
        registry_path: Path | None = None,
        embedding_enabled: bool = True,
    ) -> None:
        """Initialize the engine."""
        self._corpus_paths: list[Path] = corpus_paths or []
        self._registry_path: Path | None = registry_path
        self._embedding_enabled: bool = embedding_enabled
        self._chunks: list[dict[str, Any]] = []
        self._bm25_index: Any | None = None
        self._embedding_matrix: Any | None = None
        self._corpus_hash: str = ""

        resolved_paths = self._resolve_corpus_paths()
        if not resolved_paths:
            logger.warning("No corpus paths resolved. Corpus will be empty.")
            return

        self._corpus_paths = resolved_paths
        self._load_corpus()

        if self._chunks:
            self._build_bm25_index()
            if self._embedding_enabled:
                self._build_embedding_index()

    def _resolve_corpus_paths(self) -> list[Path]:
        """Resolve corpus paths from environment or auto-discovery."""
        env_paths = os.environ.get("CCBA_LEGAL_CORPUS_PATH")
        if env_paths:
            separator = ";" if os.name == "nt" else ":"
            return [Path(p) for p in env_paths.split(separator) if p.strip()]

        if self._corpus_paths:
            return self._expand_bundle_dirs(self._corpus_paths)

        # Auto-discovery: scan upward for .md/legal_docs/
        current = Path(__file__).resolve()
        for parent in current.parents:
            candidate = parent / ".md" / "legal_docs"
            if candidate.is_dir():
                return self._expand_bundle_dirs([candidate])
        return []

    @staticmethod
    def _expand_bundle_dirs(paths: list[Path]) -> list[Path]:
        """Expand parent directories into individual bundle subdirectories."""
        bundles: list[Path] = []
        for p in paths:
            if (p / "metadata.yaml").exists():
                bundles.append(p)
            elif p.is_dir():
                for child in sorted(p.iterdir()):
                    if child.is_dir() and (child / "metadata.yaml").exists():
                        bundles.append(child)
        return bundles

    def _load_corpus(self) -> None:
        """Load corpus chunks from bundles."""
        import yaml

        all_text = ""
        for bundle_dir in self._corpus_paths:
            meta_path = bundle_dir / "metadata.yaml"
            clauses_path = bundle_dir / "clauses.json"

            if not meta_path.exists() or not clauses_path.exists():
                continue

            try:
                with meta_path.open("r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f) or {}
                with clauses_path.open("r", encoding="utf-8") as f:
                    clauses = json.load(f)

                md_files = [
                    p for p in bundle_dir.glob("*.md")
                    if not p.name.startswith("dead_ends") and p.name != "index.md" and p.name != "log.md"
                ]
                if not md_files:
                    continue

                with md_files[0].open("r", encoding="utf-8") as f:
                    md_lines = f.readlines()

                doc_id = meta.get("doc_id", bundle_dir.name)
                citation_url = meta.get("source_url", "")
                doc_status = meta.get("status", "unknown")

                for clause in clauses:
                    line_start = clause.get("line_start", 1) - 1
                    line_end = clause.get("line_end", line_start + 1)
                    text = "".join(md_lines[line_start:line_end]).strip()
                    if not text:
                        text = clause.get("title", "")

                    self._chunks.append({
                        "clause_id": clause.get("clause_id", ""),
                        "document_id": doc_id,
                        "article_num": clause.get("title", ""),
                        "title": clause.get("title", ""),
                        "text": text,
                        "citation_url": citation_url,
                        "status": doc_status,
                        "domain": meta.get("category", ""),
                    })
                    all_text += text
            except Exception as e:
                logger.error("Error loading bundle %s: %s", bundle_dir, e)

        self._corpus_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into unigrams and bigrams."""
        tokens = text.lower().split()
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)]
        return tokens + bigrams

    def _build_bm25_index(self) -> None:
        """Build the BM25 index."""
        from rank_bm25 import BM25Okapi

        tokenized_corpus = [self._tokenize(c["text"]) for c in self._chunks]
        self._bm25_index = BM25Okapi(tokenized_corpus)

    def _build_embedding_index(self) -> None:
        """Build or load the embedding index."""
        try:
            import numpy as np

            from ccba_ai import AIClient
        except ImportError:
            self._embedding_matrix = None
            return

        try:
            texts = [c["text"] for c in self._chunks]
            cache_path = self._corpus_paths[0] / "embeddings.npy" if self._corpus_paths else None

            if cache_path and cache_path.exists():
                matrix = np.load(str(cache_path))
                if len(matrix) == len(self._chunks):
                    self._embedding_matrix = matrix
                    return

            client = AIClient()
            embeddings = client.embed(texts)
            self._embedding_matrix = np.array(embeddings)

            if cache_path:
                np.save(str(cache_path), self._embedding_matrix)
        except Exception as e:
            logger.error("Error building embeddings: %s", e)
            self._embedding_matrix = None

    def _search_bm25(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Search using BM25."""
        if not self._bm25_index:
            return []

        tokenized = self._tokenize(query)
        scores = self._bm25_index.get_scores(tokenized)

        indexed_scores = [(i, float(s)) for i, s in enumerate(scores)]
        return sorted(indexed_scores, key=lambda x: x[1], reverse=True)[:top_k]

    def _search_embedding(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Search using embeddings."""
        if self._embedding_matrix is None:
            return []

        try:
            import numpy as np

            from ccba_ai import AIClient

            query_emb = np.array(AIClient().embed([query])[0])
            norms = np.linalg.norm(self._embedding_matrix, axis=1) * np.linalg.norm(query_emb)
            norms[norms == 0] = 1e-10
            scores = np.dot(self._embedding_matrix, query_emb) / norms

            indexed_scores = [(i, float(s)) for i, s in enumerate(scores)]
            return sorted(indexed_scores, key=lambda x: x[1], reverse=True)[:top_k]
        except Exception:
            return []

    def _rrf_fusion(self, *ranked_lists: list[tuple[int, float]], k: int = 60) -> list[tuple[int, float]]:
        """Reciprocal Rank Fusion."""
        from collections import defaultdict

        rrf_scores: dict[int, float] = defaultdict(float)

        for ranked_list in ranked_lists:
            for rank, (doc_id, _) in enumerate(ranked_list):
                rrf_scores[doc_id] += 1.0 / (rank + k)

        fused = list(rrf_scores.items())
        return sorted(fused, key=lambda x: x[1], reverse=True)

    def query(self, query_text: str, domain: str | None = None, top_k: int = 5) -> list[dict[str, Any]]:
        """Query the ground-truth engine."""
        if not self._chunks:
            return []

        bm25_results = self._search_bm25(query_text, top_k * 2)
        emb_results = self._search_embedding(query_text, top_k * 2)

        fused = self._rrf_fusion(bm25_results, emb_results)

        results = []
        for doc_id, score in fused:
            chunk = self._chunks[doc_id]
            if domain and chunk.get("domain") != domain:
                continue

            results.append({
                "clause_id": chunk.get("clause_id", ""),
                "document_id": chunk.get("document_id", ""),
                "article_num": chunk.get("title", ""),
                "title": chunk.get("title", ""),
                "text_snippet": chunk.get("text", "")[:500],
                "confidence_score": round(score, 4),
                "citation_url": chunk.get("citation_url", ""),
                "status": chunk.get("status", "unknown"),
            })

            if len(results) >= top_k:
                break

        return results


def query_ground_truth(
    query: str,
    domain: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """High-level API for federated legal ground-truth search.

    Args:
        query: Query text.
        domain: Optional domain filter.
        top_k: Max number of results.

    Returns:
        List of result dictionaries.
    """
    engine = FederatedLegalEngine(embedding_enabled=False)
    return engine.query(query, domain=domain, top_k=top_k)


__all__ = ["FederatedLegalEngine", "query_ground_truth"]
