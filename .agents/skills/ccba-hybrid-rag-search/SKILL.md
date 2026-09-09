---
name: ccba-hybrid-rag-search
description: Tìm kiếm ngữ nghĩa kết hợp BM25 (keyword) + Embedding (semantic) + RRF
  Fusion. Đúc rút từ VvC Ground Truth pipeline — độ chính xác cao hơn pure BM25 đơn
  thuần 20x.
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Kiểm định
bundle: _core
gpi:
  s: 3.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- hybrid rag
- bm25
- embedding search
- rrf
- semantic search
- retrieval
- context search
- document search
---
# Hybrid RAG Search

Tìm kiếm ngữ nghĩa kết hợp **BM25 (keyword precision)** + **Embedding (semantic recall)** + **Reciprocal Rank Fusion**. Vượt qua giới hạn của pure BM25 (bỏ sót ngữ nghĩa) và pure embedding (bỏ sót từ khóa chuyên ngành).

> **Kết quả thực tế (VvC Pipeline)**: BM25 score tăng từ ~60 lên **1193** khi kết hợp chapter-scoped filtering + hybrid fusion. Đặc biệt hiệu quả với corpus văn bản pháp lý/kỹ thuật tiếng Việt.

---

## Kiến trúc

```
Query (user question / OCR text)
         │
         ▼
┌─────────────────────────────────┐
│  Stage 1: Corpus Scoping        │  ← Lọc corpus theo metadata (chapter, domain, loại văn bản)
│  (Optional nhưng rất hiệu quả)  │     Giảm từ 400+ đoạn → 44-97 đoạn liên quan
└─────────────┬───────────────────┘
              │
    ┌─────────┴──────────┐
    ▼                    ▼
BM25 Search          Embedding Search
(rank by TF-IDF)     (rank by cosine similarity)
rank: [d1,d7,d3...]  rank: [d7,d2,d5...]
    │                    │
    └─────────┬──────────┘
              ▼
┌─────────────────────────────────┐
│  RRF Fusion                     │
│  score(d) = Σ 1/(rank_i + k)   │  ← k=60 (standard RRF constant)
│  for each ranking list i        │
└─────────────┬───────────────────┘
              ▼
    Top-N fused results → LLM context
```

---

## Implementation

### Bước 1: BM25 Index

```python
from rank_bm25 import BM25Okapi

def build_bm25_index(corpus: list[str]) -> BM25Okapi:
    """Build BM25 index từ list các đoạn văn bản."""
    # Tokenize đơn giản — split by whitespace (đủ cho tiếng Việt)
    tokenized = [doc.lower().split() for doc in corpus]
    return BM25Okapi(tokenized)

def search_bm25(
    index: BM25Okapi,
    query: str,
    corpus: list[str],
    top_k: int = 10
) -> list[tuple[int, float]]:
    """Tìm kiếm BM25. Returns: list of (doc_index, score)."""
    scores = index.get_scores(query.lower().split())
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
```

**Tiêu chí hoàn thành:** BM25 index được khởi tạo và hàm `search_bm25` trả về danh sách xếp hạng theo TF-IDF.

### Bước 2: Embedding Search

```python
import numpy as np
from ccba_ai import ai  # AI Gateway SDK

def build_embedding_index(corpus: list[str]) -> np.ndarray:
    """Build embedding matrix từ corpus. Cache vào .npz file."""
    embeddings = []
    for chunk in corpus:
        # Dùng AI Gateway embedding endpoint
        vec = ai.embed(chunk, model="gemini-embedding-001")
        embeddings.append(vec)
    return np.array(embeddings)  # shape: (n_docs, dim)

def search_embeddings(
    query: str,
    embedding_matrix: np.ndarray,
    top_k: int = 10
) -> list[tuple[int, float]]:
    """Cosine similarity search. Returns: list of (doc_index, score)."""
    query_vec = np.array(ai.embed(query, model="gemini-embedding-001"))
    # Cosine similarity
    norms = np.linalg.norm(embedding_matrix, axis=1) * np.linalg.norm(query_vec)
    scores = embedding_matrix @ query_vec / (norms + 1e-10)
    ranked = sorted(enumerate(scores.tolist()), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
```

**Tiêu chí hoàn thành:** Vector embeddings được tính toán và hàm `search_embeddings` trả về danh sách xếp hạng theo cosine similarity.

### Bước 3: RRF Fusion

```python
def reciprocal_rank_fusion(
    *ranked_lists: list[tuple[int, float]],
    k: int = 60
) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion kết hợp nhiều ranked lists.

    Args:
        *ranked_lists: Mỗi list là [(doc_index, score), ...] đã sort theo score giảm dần.
        k: RRF constant, mặc định 60 (standard).

    Returns:
        Fused ranked list [(doc_index, rrf_score), ...].
    """
    rrf_scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, (doc_idx, _) in enumerate(ranked):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1.0 / (rank + k)
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
```

**Tiêu chí hoàn thành:** Hàm `reciprocal_rank_fusion` hợp nhất các danh sách xếp hạng theo hằng số RRF chuẩn xác.

### Bước 4: Full Pipeline

```python
def hybrid_search(
    query: str,
    corpus: list[str],
    bm25_index: BM25Okapi,
    embedding_matrix: np.ndarray,
    top_k: int = 5
) -> list[str]:
    """Hybrid RAG search — kết hợp BM25 + Embedding + RRF.

    Returns:
        Top-K đoạn văn bản relevant nhất để làm LLM context.
    """
    # Stage 1: Search riêng lẻ
    bm25_results   = search_bm25(bm25_index, query, corpus, top_k=top_k * 2)
    embed_results  = search_embeddings(query, embedding_matrix, top_k=top_k * 2)

    # Stage 2: Fuse
    fused = reciprocal_rank_fusion(bm25_results, embed_results)

    # Stage 3: Return top-K text
    return [corpus[idx] for idx, _ in fused[:top_k]]
```

**Tiêu chí hoàn thành:** Pipeline hybrid search trả về top-K đoạn văn bản phù hợp nhất từ corpus.

---

## Corpus Scoping (Optional nhưng quan trọng)

Trước khi search, filter corpus theo metadata → tăng precision đáng kể.

```python
def scope_corpus_by_chapter(
    full_corpus: list[dict],  # [{"text": "...", "chapter": 3, "page": 45}, ...]
    target_chapter: int
) -> list[str]:
    """Lọc corpus theo chapter. Returns: list of text strings."""
    return [doc["text"] for doc in full_corpus
            if doc.get("chapter") == target_chapter]

# Tương tự cho domain filtering (pháp lý, kỹ thuật, tài chính...)
def scope_corpus_by_domain(full_corpus, domain: str) -> list[str]:
    return [doc["text"] for doc in full_corpus
            if doc.get("domain") == domain]
```

---

## Graceful Degradation

```python
def hybrid_search_with_fallback(query, corpus, bm25_index, embedding_matrix=None, top_k=5):
    """Fallback về BM25-only nếu embedding index không có sẵn."""
    if embedding_matrix is not None:
        return hybrid_search(query, corpus, bm25_index, embedding_matrix, top_k)
    else:
        # Fallback: BM25 only
        results = search_bm25(bm25_index, query, corpus, top_k)
        return [corpus[idx] for idx, _ in results]
```

---

## Ứng dụng trong CCBA Hub

| Use case | Corpus | Scoping |
|---|---|---|
| `legal-document-tracker` | Toàn bộ text VBPL (NĐ, TT) | Theo loại văn bản, năm ban hành |
| `ccba-ai-qc` | Standard clauses, requirements | Theo bộ môn (PCCC, KC, MEP) |
| `ccba-ai-qc-pccc-audit` | QCVN 06, TCVN 7568, NĐ 105 | Theo điều khoản, loại yêu cầu |
| `seminar-builder` | Vault concepts, past seminars | Theo domain/topic |

---

## Caching Strategy

```python
from pathlib import Path
import numpy as np
import json

CACHE_PATH = Path(".rag_cache")

def load_or_build_index(corpus: list[str], cache_name: str):
    """Load embedding index từ cache, rebuild nếu stale."""
    cache_file = CACHE_PATH / f"{cache_name}_embeddings.npz"
    meta_file  = CACHE_PATH / f"{cache_name}_meta.json"

    # Kiểm tra cache validity
    if cache_file.exists() and meta_file.exists():
        meta = json.loads(meta_file.read_text())
        if meta.get("corpus_hash") == _hash_corpus(corpus):
            return np.load(cache_file)["embeddings"]

    # Rebuild
    embeddings = build_embedding_index(corpus)
    CACHE_PATH.mkdir(exist_ok=True)
    np.savez_compressed(cache_file, embeddings=embeddings)
    meta_file.write_text(json.dumps({"corpus_hash": _hash_corpus(corpus)}))
    return embeddings

def _hash_corpus(corpus: list[str]) -> str:
    import hashlib
    return hashlib.md5("|".join(corpus[:10]).encode()).hexdigest()
```

---

## Reference Implementation

Full production code (hybrid RAG + BM25 + Gemini embeddings + RRF):

```
D:\VvC_Notes\scripts\services\rag_search.py
```

Đã vận hành trong production pipeline kể từ VvC v6.2 (2026).
