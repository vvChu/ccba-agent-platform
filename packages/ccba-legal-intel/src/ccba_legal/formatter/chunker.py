"""Semantic and structural chunker for RAG."""

from __future__ import annotations

import json
import math
from pathlib import Path

from ccba_legal.monitor import TokenMonitor


def generate_chunks(content: str, bundle_dir: Path) -> None:
    """Segment content into 200-400 word chunks and write to chunks.json."""
    monitor = TokenMonitor()
    paragraphs = []
    curr_para: list[str] = []
    for line in content.splitlines():
        if not line.strip():
            if curr_para:
                paragraphs.append("\n".join(curr_para))
                curr_para = []
        else:
            curr_para.append(line)
    if curr_para:
        paragraphs.append("\n".join(curr_para))
    total_words = sum(len(p.split()) for p in paragraphs)
    if total_words == 0:
        (bundle_dir / "chunks.json").write_text("[]", encoding="utf-8")
        return
    num_chunks = max(1, math.ceil(total_words / 300))
    target_size = total_words / num_chunks
    chunks = []
    curr_chunk: list[str] = []
    curr_words = 0
    idx = 1
    for p in paragraphs:
        p_words = len(p.split())
        if (
            curr_chunk
            and (curr_words >= 200)
            and (curr_words + p_words / 2 > target_size or curr_words + p_words > 400)
        ):
            c_text = "\n\n".join(curr_chunk)
            chunks.append(
                {
                    "chunk_id": idx,
                    "content": c_text,
                    "word_count": curr_words,
                    "token_count": monitor.get_context_token_count([c_text]),
                }
            )
            idx += 1
            curr_chunk, curr_words = [p], p_words
        else:
            curr_chunk.append(p)
            curr_words += p_words
    if curr_chunk:
        c_text = "\n\n".join(curr_chunk)
        if curr_words < 200 and chunks:
            chunks[-1]["content"] += "\n\n" + c_text
            chunks[-1]["word_count"] += curr_words
            chunks[-1]["token_count"] = monitor.get_context_token_count([chunks[-1]["content"]])
        else:
            chunks.append(
                {
                    "chunk_id": idx,
                    "content": c_text,
                    "word_count": curr_words,
                    "token_count": monitor.get_context_token_count([c_text]),
                }
            )
    (bundle_dir / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
