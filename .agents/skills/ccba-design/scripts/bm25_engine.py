#!/usr/bin/env python3
"""Shared Deterministic BM25 Search Engine for ccba-design (UI/UX, Logo, and CIP domains)."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from math import log
from pathlib import Path


class BM25:
    """Deterministic BM25 ranking engine with multi-key tie-breaking (Rule 5 compliant)."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize BM25 parameters and empty index."""
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_lengths: list[int] = []
        self.avgdl: float = 0.0
        self.idf: dict[str, float] = {}
        self.doc_freqs: dict[str, int] = defaultdict(int)
        self.num_docs: int = 0

    def tokenize(self, text: str) -> list[str]:
        """Lowercase, strip punctuation, and keep tokens with length >= 2."""
        cleaned = re.sub(r"[^\w\s-]", " ", str(text).lower())
        return [w for w in cleaned.split() if len(w) >= 2]

    def fit(self, documents: list[str]) -> None:
        """Build BM25 inverse document frequency index from documents."""
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.num_docs = len(self.corpus)
        if self.num_docs == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / self.num_docs
        for doc in self.corpus:
            for word in set(doc):
                self.doc_freqs[word] += 1
        for word, freq in self.doc_freqs.items():
            self.idf[word] = log((self.num_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def score(self, query: str) -> list[tuple[int, float]]:
        """Score all indexed documents against query using deterministic multi-key sort."""
        query_tokens = self.tokenize(query)
        scores: list[tuple[int, float]] = []
        for idx, doc in enumerate(self.corpus):
            doc_score = 0.0
            doc_len = self.doc_lengths[idx]
            term_freqs: dict[str, int] = defaultdict(int)
            for word in doc:
                term_freqs[word] += 1
            for token in query_tokens:
                if token in self.idf and term_freqs[token] > 0:
                    tf = term_freqs[token]
                    idf = self.idf[token]
                    denom = tf + self.k1 * (1.0 - self.b + self.b * doc_len / self.avgdl)
                    doc_score += idf * (tf * (self.k1 + 1.0)) / denom
            scores.append((idx, doc_score))
        return sorted(scores, key=lambda x: (-round(x[1], 4), x[0]))


def load_csv(filepath: Path) -> list[dict[str, str]]:
    """Load UTF-8 CSV file into a list of row dictionaries."""
    with open(filepath, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def search_csv(
    filepath: Path,
    search_cols: list[str],
    output_cols: list[str],
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    """Execute deterministic BM25 search over specified CSV columns."""
    if not filepath.exists():
        return []
    data = load_csv(filepath)
    documents = [" ".join(str(row.get(col, "")) for col in search_cols) for row in data]
    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(query)
    results: list[dict[str, str]] = []
    for idx, doc_score in ranked[:max_results]:
        if doc_score > 0:
            row = data[idx]
            results.append({col: row.get(col, "") for col in output_cols if col in row})
    return results
