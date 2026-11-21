# Hybrid RAG Search — Scoping, Graceful Degradation & Caching Recipes

Tài liệu tham chiếu Level 3 cho `ccba-hybrid-rag-search`, chứa các helper mẫu về giới hạn phạm vi ngữ cảnh (scoping), giáng cấp về BM25-only và lưu đệm chỉ mục vector.

## 1. Corpus Scoping (Chapter, Domain & 5-Ring Legal Graph Pruning)

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

# Lọc corpus theo Vành đai Quan hệ Pháp lý (5-Ring Legal Graph Pruning)
def scope_corpus_by_legal_ring(
    full_corpus: list[dict],
    allowed_doc_ids: set[str]
) -> list[str]:
    """Lọc các đoạn trích chỉ thuộc các văn bản nằm trong vành đai quan hệ mục tiêu.
    Danh sách allowed_doc_ids được truy xuất từ:
    python scripts/spoke_cli.py graph --doc <doc_id> --json
    """
    return [
        doc["text"] for doc in full_corpus
        if doc.get("doc_id") in allowed_doc_ids
    ]
```

## 2. Graceful Degradation (Fallback về BM25-only)

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

## 3. Caching Strategy (`.rag_cache` Embeddings Cache)

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
