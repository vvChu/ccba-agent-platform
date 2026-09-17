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
        """Resolve corpus paths from environment, master discovery, or auto-discovery."""
        env_paths = os.environ.get("CCBA_LEGAL_CORPUS_PATH")
        if env_paths:
            separator = ";" if os.name == "nt" else ":"
            raw = [Path(p) for p in env_paths.split(separator) if p.strip()]
            return self._expand_bundle_dirs(raw)

        if self._corpus_paths:
            return self._expand_bundle_dirs(self._corpus_paths)

        # 1. Master registry discovery
        try:
            from ccba_legal.registry import discover_master_registry_path

            master_reg = discover_master_registry_path()
            if master_reg and master_reg.exists():
                candidates: list[Path] = []
                reg_parent = master_reg.parent
                candidates.append(reg_parent / "legal_docs")
                candidates.append(reg_parent / ".md" / "legal_docs")
                if reg_parent.name == "data" and reg_parent.parent.name == ".md":
                    project_root = reg_parent.parent.parent
                    candidates.append(project_root / "legal_docs")
                    candidates.append(project_root / ".md" / "legal_docs")

                for cand in candidates:
                    if cand.is_dir():
                        bundles = self._expand_bundle_dirs([cand])
                        if bundles:
                            return bundles
        except Exception:
            pass

        # 2. Auto-discovery: scan upward for .md/legal_docs/ or legal_docs/
        current = Path(__file__).resolve()
        for parent in current.parents:
            for cand_rel in [".md/legal_docs", "legal_docs"]:
                candidate = parent / cand_rel
                if candidate.is_dir():
                    bundles = self._expand_bundle_dirs([candidate])
                    if bundles:
                        return bundles
        return []

    @staticmethod
    def _expand_bundle_dirs(paths: list[Path]) -> list[Path]:
        """Expand parent directories into individual bundle subdirectories."""
        bundles: list[Path] = []
        for p in paths:
            if not p.is_dir():
                continue
            if (p / "metadata.yaml").exists():
                bundles.append(p)
                continue
            # Recursive scan for any bundle folder containing metadata.yaml
            for meta_file in sorted(p.rglob("metadata.yaml")):
                bundles.append(meta_file.parent)

        # Remove duplicates while preserving order
        seen: set[Path] = set()
        unique_bundles: list[Path] = []
        for b in bundles:
            resolved = b.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique_bundles.append(b)
        return unique_bundles

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
                    p
                    for p in bundle_dir.glob("*.md")
                    if not p.name.startswith("dead_ends")
                    and p.name != "index.md"
                    and p.name != "log.md"
                ]
                if not md_files:
                    continue

                with md_files[0].open("r", encoding="utf-8") as f:
                    md_lines = f.readlines()

                doc_id = meta.get("doc_id", bundle_dir.name)
                citation_url = meta.get("source_url", "")
                doc_status = meta.get("status", "unknown")
                raw_territory = meta.get("territory") or meta.get("territorial_jurisdiction")
                if not raw_territory:
                    raw_territory = "VN-HN" if str(doc_id).startswith("vn_hn_") else "VN"
                territory = str(raw_territory)
                hierarchy_level = str(
                    meta.get("hierarchy_level", "provincial" if territory != "VN" else "national")
                )

                for clause in clauses:
                    line_start = clause.get("line_start", 1) - 1
                    line_end = clause.get("line_end", line_start + 1)
                    text = "".join(md_lines[line_start:line_end]).strip()
                    if not text:
                        text = clause.get("title", "")

                    self._chunks.append(
                        {
                            "clause_id": clause.get("clause_id", ""),
                            "document_id": doc_id,
                            "article_num": clause.get("title", ""),
                            "title": clause.get("title", ""),
                            "text": text,
                            "citation_url": citation_url,
                            "status": doc_status,
                            "domain": meta.get("category", ""),
                            "territory": territory,
                            "hierarchy_level": hierarchy_level,
                        }
                    )
                    all_text += text
            except Exception as e:
                logger.error("Error loading bundle %s: %s", bundle_dir, e)

        self._corpus_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into unigrams and bigrams."""
        tokens = text.lower().split()
        bigrams = [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def _build_bm25_index(self) -> None:
        """Build the BM25 index."""
        try:
            from rank_bm25 import BM25Okapi

            tokenized_corpus = [self._tokenize(c["text"]) for c in self._chunks]
            self._bm25_index = BM25Okapi(tokenized_corpus)
        except ImportError:
            self._bm25_index = None

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
                hash_path = cache_path.with_suffix(".sha256")
                cached_hash = hash_path.read_text().strip() if hash_path.exists() else ""
                if len(matrix) == len(self._chunks) and cached_hash == self._corpus_hash:
                    self._embedding_matrix = matrix
                    return

            client = AIClient()
            embeddings = client.embed(texts)
            self._embedding_matrix = np.array(embeddings)

            if cache_path:
                np.save(str(cache_path), self._embedding_matrix)
                cache_path.with_suffix(".sha256").write_text(self._corpus_hash)
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

    def _rrf_fusion(
        self, *ranked_lists: list[tuple[int, float]], k: int = 60
    ) -> list[tuple[int, float]]:
        """Reciprocal Rank Fusion."""
        from collections import defaultdict

        rrf_scores: dict[int, float] = defaultdict(float)

        for ranked_list in ranked_lists:
            for rank, (doc_id, _) in enumerate(ranked_list):
                rrf_scores[doc_id] += 1.0 / (rank + k)

        fused = list(rrf_scores.items())
        return sorted(fused, key=lambda x: x[1], reverse=True)

    def _format_chunk_result(self, chunk: dict[str, Any], score: float) -> dict[str, Any]:
        raw_level = str(chunk.get("hierarchy_level", "national")).upper()
        return {
            "clause_id": chunk.get("clause_id", ""),
            "document_id": chunk.get("document_id", ""),
            "article_num": chunk.get("title", ""),
            "title": chunk.get("title", ""),
            "text": chunk.get("text", ""),
            "text_snippet": chunk.get("text", "")[:500],
            "confidence_score": round(score, 4),
            "citation_url": chunk.get("citation_url", ""),
            "status": chunk.get("status", "unknown"),
            "territory": chunk.get("territory", "VN"),
            "hierarchy_level": raw_level,
        }

    def query(
        self,
        query_text: str,
        domain: str | None = None,
        jurisdiction: str | None = None,
        as_of_date: str | None = None,
        top_k: int = 5,
        k_local_min: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Query the ground-truth engine with Dual-Pool Partitioned Retrieval and Geofencing (ADR 0050)."""
        if not self._chunks:
            return []

        if "k" in kwargs and kwargs["k"] is not None:
            top_k = int(kwargs["k"])

        from ccba_legal.jurisdiction import expand_jurisdiction_queries, normalize_jurisdiction

        is_wildcard = jurisdiction in ("*", "ALL", "all")
        target_territories: set[str] = set()
        if not is_wildcard and jurisdiction:
            if isinstance(jurisdiction, list):
                target_territories = {normalize_jurisdiction(j) for j in jurisdiction}
            else:
                target_territories = {normalize_jurisdiction(jurisdiction)}

        primary_jur = next(iter(target_territories)) if target_territories else None
        expanded_queries = expand_jurisdiction_queries(
            query_text, jurisdiction=primary_jur, as_of_date=as_of_date
        )
        effective_query = " ".join(expanded_queries[:2])

        candidate_multiplier = max(top_k * 4, 20)
        bm25_results = self._search_bm25(effective_query, candidate_multiplier)
        emb_results = self._search_embedding(effective_query, candidate_multiplier)

        fused = self._rrf_fusion(bm25_results, emb_results)

        if is_wildcard:
            # Unconstrained search across all territories
            results: list[dict[str, Any]] = []
            for doc_id, score in fused:
                chunk = self._chunks[doc_id]
                if domain and chunk.get("domain") != domain:
                    continue
                results.append(self._format_chunk_result(chunk, score))
                if len(results) >= top_k:
                    break
            return results

        local_targets = {t for t in target_territories if t != "VN"}
        if not local_targets:
            # Strict National Isolation: Only return national documents
            results = []
            for doc_id, score in fused:
                chunk = self._chunks[doc_id]
                if domain and chunk.get("domain") != domain:
                    continue
                c_territory = str(chunk.get("territory", "VN"))
                if c_territory in {"VN", "national", ""}:
                    results.append(self._format_chunk_result(chunk, score))
                    if len(results) >= top_k:
                        break
            return results

        # 2. Dual-Pool Partitioned Retrieval (Local Pool vs National Pool)
        local_pool: list[dict[str, Any]] = []
        national_pool: list[dict[str, Any]] = []

        for doc_id, score in fused:
            chunk = self._chunks[doc_id]
            if domain and chunk.get("domain") != domain:
                continue

            c_territory = str(chunk.get("territory", "VN"))
            if c_territory in local_targets:
                local_pool.append(self._format_chunk_result(chunk, score))
            elif c_territory in {"VN", "national", ""}:
                national_pool.append(self._format_chunk_result(chunk, score))

        # Partition allocation: prioritize local results if available
        local_min = k_local_min if k_local_min is not None else max(1, top_k // 2)
        target_local_k = min(len(local_pool), local_min)
        final_results: list[dict[str, Any]] = local_pool[:target_local_k]
        needed_national = top_k - len(final_results)
        final_results.extend(national_pool[:needed_national])

        # If still short of top_k, fill with remaining local results
        if len(final_results) < top_k and len(local_pool) > target_local_k:
            remaining_slots = top_k - len(final_results)
            final_results.extend(local_pool[target_local_k : target_local_k + remaining_slots])

        return final_results


_cached_engine: FederatedLegalEngine | None = None


def query_ground_truth(
    query: str,
    domain: str | None = None,
    jurisdiction: str | None = None,
    as_of_date: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """High-level API for federated legal ground-truth search.

    Uses a module-level cached engine to avoid rebuilding BM25 index
    on every call (Copilot review: latency optimization).

    Args:
        query: Query text.
        domain: Optional domain filter.
        jurisdiction: Optional territory code for Geofencing.
        as_of_date: Optional historical evaluation date.
        top_k: Max number of results.

    Returns:
        List of result dictionaries.
    """
    global _cached_engine  # noqa: PLW0603
    if _cached_engine is None:
        _cached_engine = FederatedLegalEngine(embedding_enabled=False)
    return _cached_engine.query(
        query, domain=domain, jurisdiction=jurisdiction, as_of_date=as_of_date, top_k=top_k
    )


__all__ = ["FederatedLegalEngine", "query_ground_truth"]
