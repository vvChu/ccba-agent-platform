"""Hybrid RAG Search Engine for Legal Documents."""

import math
import re
from typing import Any


class LegalHybridRAG:
    """Hybrid RAG Engine indexing and querying legal document collections."""

    def __init__(self) -> None:
        self.corpus: dict[str, str] = {}  # doc_id -> raw content
        self.tokenized_corpus: dict[str, list[str]] = {}

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenizer splitting text into lowercase words."""
        words = re.findall(r"\w+", text.lower(), re.UNICODE)
        return [w for w in words if len(w) > 1]

    def index_document(self, doc_id: str, content: str) -> None:
        """Add a legal document or VBHN markdown to the RAG index."""
        self.corpus[doc_id] = content
        self.tokenized_corpus[doc_id] = self._tokenize(content)

    def query(self, query_text: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Query indexed documents using BM25 / token overlap scoring."""
        query_tokens = self._tokenize(query_text)
        if not query_tokens or not self.corpus:
            return []

        scores: list[tuple[str, float]] = []
        doc_count = len(self.corpus)

        for doc_id, doc_tokens in self.tokenized_corpus.items():
            if not doc_tokens:
                continue

            score = 0.0
            doc_len = len(doc_tokens)
            doc_token_set = set(doc_tokens)

            for token in query_tokens:
                if token in doc_token_set:
                    # Term frequency
                    tf = doc_tokens.count(token) / doc_len
                    # IDF approximation
                    docs_containing = sum(
                        1 for tokens in self.tokenized_corpus.values() if token in tokens
                    )
                    idf = math.log((doc_count + 1) / (docs_containing + 1)) + 1.0
                    score += tf * idf

            if score > 0:
                scores.append((doc_id, score))

        # Sort descending by score
        scores.sort(key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for doc_id, score in scores[:top_k]:
            content = self.corpus[doc_id]
            # Extract snippet containing query words
            snippet = content[:300].strip()
            results.append(
                {
                    "doc_id": doc_id,
                    "score": round(score, 4),
                    "snippet": snippet,
                }
            )

        return results
