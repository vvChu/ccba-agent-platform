# LLM Pipeline Patterns (Part 1: Core Architecture & Anti-Starvation, Patterns 1–9)

Tài liệu tham chiếu Level 3 cho `ccba-llm-pipeline-patterns`, lưu trữ đầy đủ mô tả incident, kiến trúc, bảng ngưỡng và code mẫu Python cho Patterns 1–9.

## Pattern 1: 2-Pass Architecture (Quality vs Speed)

### Vấn đề
Single-pass synthesis (dù với Ground Truth) vẫn sinh ra lỗi OCR, hallucination, hay sai format trong một số trường hợp.

### Giải pháp
```
Pass 1: Fast model (local GPU / claude-haiku)
        -> Generate toàn bộ draft (~30-90 giây)

Pass 2: Reasoning model (claude-sonnet-thinking / gemma-reasoning)
        -> Verify/correct MỘT SECTION CỤ THỂ duy nhất (~15-30 giây)
        -> KHÔNG audit toàn bộ output (quá chậm, overkill)
```

### Anti-pattern & Safety Fallback
- **SAI:** Pass 2 re-generates toàn bộ output -> tốn 3-5x thời gian, mất context.
- **ĐÚNG:** Pass 2 chỉ nhận vào đoạn cần verify + ground truth, trả ra patch duy nhất.
- **Safety Fallback:** (1) Pass 1 trả `"Error connecting"` -> abort ngay, không tạo file; (2) Pass 2 timeout -> giữ Pass 1 draft.

---

## Pattern 2: Ground Truth Scoping (BM25 + Chapter Filter)

### Vấn đề
BM25 trên toàn bộ corpus (400+ đoạn văn) thường match sai chapter. Score trước khi scope: ~60; sau khi scope theo chapter: ~1193 (20x chính xác hơn).

### Giải pháp: Chapter-Scoped Search
1. Detect page number từ input (OCR / metadata) -> resolve chapter via TOC map -> load ONLY paragraphs từ 1-2 chapters liên quan (44-97 đoạn thay vì 400+).
2. Dùng **chapter opening text** (~500 chars đầu mỗi chapter) để routing — thay vì chỉ dùng title ngắn (~60 -> ~188).

---

## Pattern 3: Minimum Content Threshold

```python
# Stage đầu tiên của pipeline — gate tất cả stages đắt tiền
if len(extracted_text.strip()) < 50:
    mark_as_low_confidence()
    skip_expensive_llm_stages()
    return  # early exit
```

| Ngưỡng | Ý nghĩa |
|---|---|
| `< 50 chars` | Bỏ qua — có thể chỉ là header trang / caption |
| `50-200 chars` | `confidence: low` — synthesize nhưng flag review |
| `> 200 chars` | Xử lý bình thường |

---

## Pattern 4: Idempotent Pipeline Stages

```python
# Kiểm tra trước khi tạo & upsert thay vì append
output_path = concepts_dir / f"{stem}.md"
if output_path.exists():
    logger.info(f"Skip — đã tồn tại: {stem}")
    return existing_path

yaml.safe_dump(new_data, stream, allow_unicode=True)
```

- Khi sync ngược metadata (TOC -> Source Note), luôn dùng `safe_load -> merge -> safe_dump` thay vì string append để không overwrite các field user đã customize.

---

## Pattern 5: LLM Error String Detection

```python
ERROR_SIGNATURES = [
    "Error connecting",
    "Connection timeout",
    "Rate limit exceeded",
    "context_length_exceeded",
    "maximum context length",
    "I cannot",
    "I'm unable to",
]

def is_llm_error(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return True
    return any(text.strip().startswith(sig) for sig in ERROR_SIGNATURES)
```

- **Stage đầu (critical):** Abort toàn bộ pipeline, không tạo file output.
- **Stage cuối (optional enrichment):** Log warning, keep partial output, continue.

---

## Pattern 6: Semantic Duplicate Detection (Pre-Save Gate)

```
Tier 1 — Hook Count Gate: existing note >= 4 Evidence Hooks -> force SEPARATE + cross-link
Tier 2 — Dynamic Size Limit: existing note > P95 size * 1.3 (~7,700 bytes) -> force SEPARATE
Tier 3 — LLM Arbitrator: cosine similarity >= 0.88 -> MERGE / SEPARATE / SUBSUME (bias SEPARATE)
```

| Decision | Hành động |
|---|---|
| `MERGE` | Academic Merge — xếp chồng Evidence Hooks, viết lại Core Idea |
| `SEPARATE` | Lưu note mới + tạo two-way cross-link tự động |
| `SUBSUME` | Drop note mới hoàn toàn — existing note đã cover 100% |

---

## Pattern 7: Context File Hierarchy

- **Layer 1 — Constitution (`AGENTS.md`):** Nguồn quy tắc duy nhất (`Full schema`).
- **Layer 2 — Quick Reference (`GEMINI.md` / `README.md`):** Pointer đến Layer 1, KHÔNG duplicate schema.
- **Layer 3 — Scope Override (`scripts/GEMINI.md`):** Chỉ override BEHAVIOR theo chế độ, KHÔNG override schema.

---

## Pattern 8: PowerShell Exit Code Fix

Python `logging` mặc định ghi vào `stderr` -> PowerShell coi bất kỳ output trên `stderr` là error (exit code 1).

```python
import logging
import sys

sys.stdout.reconfigure(encoding="utf-8")  # gọi TRƯỚC logging.basicConfig
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
```

---

## Pattern 9: Asynchronous Poller Drainage Loop (Anti-Starvation Seam)

Khi background daemon cập nhật `Command.md`, nếu worker chỉ xử lý 1 truy vấn rồi cập nhật `mtime`, các truy vấn nhập thêm trong lúc chạy sẽ bị starvation. Worker bắt buộc vét cạn nội bộ (`max_queries = 10`):

```python
def handle_command(command_file: Path | None = None, max_queries: int = 10) -> int:
    processed = 0
    while processed < max_queries:
        content = cmd_file.read_text(encoding="utf-8")
        query = find_pending_query(content)
        if not query:
            break
        response = process_query(query)
        write_response(content, query, response)
        processed += 1
    return processed
```

- **Dual-Section Assertion Invariant:** Phân rã tệp Inbox + History bằng `extract_sections()` rồi assert tách biệt `query not in inbox` và `query in after`.
