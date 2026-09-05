---
name: ccba-llm-pipeline-patterns
description: Anti-patterns và best practices cho việc xây dựng LLM processing pipelines.
  Đúc rút từ VvC LLM OS (v5.1→v8.7, 2026).
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Kiểm định
bundle: _core
triggers:
- llm pipeline
- pipeline patterns
- 2-pass
- ground truth
- rag pipeline
- synthesis pipeline
- self-correction
---
# LLM Pipeline Patterns

Pattern library cho các pipeline LLM multi-stage — đúc rút từ thực tế vận hành **VvC LLM OS** (v5.1 → v8.7, 2026). Mỗi pattern đều có ít nhất 1 incident thực tế chứng minh sự cần thiết.

> [!IMPORTANT]
> Đây là **documentation skill** — không có code cần install. Load file này khi thiết kế bất kỳ pipeline LLM nào trong CCBA.

---

## Pattern 1: 2-Pass Architecture (Quality vs Speed)

### Vấn đề
Single-pass synthesis (dù với Ground Truth) vẫn sinh ra lỗi OCR, hallucination, hay sai format trong một số trường hợp.

### Giải pháp
```
Pass 1: Fast model (local GPU / claude-haiku)
        → Generate toàn bộ draft
        → ~30-90 giây

Pass 2: Reasoning model (claude-sonnet-thinking / gemma-reasoning)
        → Verify/correct MỘT SECTION CỤ THỂ duy nhất
        → KHÔNG audit toàn bộ output (quá chậm, overkill)
        → ~15-30 giây
```

### Anti-pattern cần tránh
❌ **SAI**: Pass 2 re-generates toàn bộ output → tốn 3-5x thời gian, mất context.  
✅ **ĐÚNG**: Pass 2 chỉ nhận vào đoạn cần verify + ground truth, trả ra patch duy nhất.

### Safety Fallback (2-layer)
1. **Abort on Error**: Nếu Pass 1 trả `"Error connecting"` → abort ngay, không tạo file.
2. **Graceful Degradation**: Nếu Pass 2 timeout → giữ nguyên Pass 1 draft, vẫn lưu.

---

## Pattern 2: Ground Truth Scoping (BM25 + Chapter Filter)

### Vấn đề
BM25 trên toàn bộ corpus (400+ đoạn văn) thường match sai chapter. VD: query về "strategic agility" match text từ "Chapter 8 - Idea Generation" thay vì "Chapter 3 - Strategic Agility".

**Score trước khi scope**: ~60  
**Score sau khi scope theo chapter**: ~1193 (20x chính xác hơn)

### Giải pháp: Chapter-Scoped Search
```
1. Detect page number từ input (OCR / metadata)
2. Resolve chapter từ page number via TOC map
3. Load ONLY paragraphs từ 1-2 chapters liên quan
4. BM25 search trên corpus đã filter (44-97 đoạn thay vì 400+)
```

### Key Insight
Dùng **chapter opening text** (~500 chars đầu mỗi chapter) để routing — thay vì chỉ dùng title ngắn. BM25 score tăng từ ~60 → ~188 khi matching title + description + opening text.

---

## Pattern 3: Minimum Content Threshold

### Vấn đề
Input quá ngắn (< 50 chars) vẫn được đưa qua pipeline đắt tiền → tạo ra Concept Notes rỗng như `"tái tạo là một Hệ sinh thái."`.

### Giải pháp
```python
# Stage đầu tiên của pipeline — gate tất cả stages đắt tiền
if len(extracted_text.strip()) < 50:
    mark_as_low_confidence()
    skip_expensive_llm_stages()
    return  # early exit
```

### Ngưỡng tham chiếu từ thực tế
| Ngưỡng | Ý nghĩa |
|---|---|
| < 50 chars | Bỏ qua — có thể chỉ là header trang / caption |
| 50-200 chars | `confidence: low` — synthesize nhưng flag review |
| > 200 chars | Xử lý bình thường |

---

## Pattern 4: Idempotent Pipeline Stages

### Vấn đề
Khi daemon restart hoặc xử lý lại file, các stage không idempotent sẽ tạo duplicate output, corrupt state, hoặc fail với "file already exists".

### Giải pháp — Checklist Idempotency
```python
# ✅ ĐÚNG — kiểm tra trước khi tạo
output_path = concepts_dir / f"{stem}.md"
if output_path.exists():
    logger.info(f"Skip — đã tồn tại: {stem}")
    return existing_path

# ✅ ĐÚNG — upsert thay vì insert
yaml.safe_dump(new_data, stream, allow_unicode=True)  # overwrite toàn bộ

# ❌ SAIÔ — append không kiểm tra
with open(output_path, "a") as f:
    f.write(new_content)  # → duplicate content mỗi lần chạy
```

### Rule cho Metadata Sync
Khi sync ngược metadata (VD: TOC → Source Note), luôn dùng `safe_load → merge → safe_dump` thay vì string append. Đảm bảo không overwrite các field user đã customize.

---

## Pattern 5: LLM Error String Detection

### Vấn đề
Nhiều LLM client trả về error message dưới dạng string (không phải exception). Pipeline xử lý "bình thường" → lưu error message vào database.

### Danh sách error patterns cần detect
```python
ERROR_SIGNATURES = [
    "Error connecting",
    "Connection timeout",
    "Rate limit exceeded",
    "context_length_exceeded",
    "maximum context length",
    "I cannot",            # Model refusal
    "I'm unable to",       # Model refusal
]

def is_llm_error(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return True
    return any(text.strip().startswith(sig) for sig in ERROR_SIGNATURES)
```

### Behavior khi detect error
- **Stage đầu (critical)**: Abort toàn bộ pipeline, không tạo file output.
- **Stage cuối (optional enrichment)**: Log warning, keep partial output, continue.

---

## Pattern 6: Semantic Duplicate Detection (Pre-Save Gate)

### Vấn đề
Khi xử lý nhiều trang của cùng một khái niệm, pipeline tạo ra nhiều Concept Notes khác nhau với nội dung chồng chéo lớn (90%+). Zettelkasten bị phân mảnh.

### Giải pháp: 3-Tier Merge Control
```
Tier 1 — Hook Count Gate:
    Nếu existing note đã có ≥4 Evidence Hooks → force SEPARATE + cross-link
    (tránh "God Notes" chứa quá nhiều quotes)

Tier 2 — Dynamic Size Limit:
    Nếu existing note > P95 size × 1.3 (≈ 7,700 bytes) → force SEPARATE
    Threshold = vault-wide P95 size của tất cả concept notes

Tier 3 — LLM Arbitrator:
    Nếu cosine similarity ≥ 0.88 → hỏi LLM: MERGE / SEPARATE / SUBSUME
    Bias toward SEPARATE để tránh information loss
```

### 3 Outcomes
| Decision | Hành động |
|---|---|
| `MERGE` | Academic Merge — xếp chồng Evidence Hooks, viết lại Core Idea |
| `SEPARATE` | Lưu note mới + tạo two-way cross-link tự động |
| `SUBSUME` | Drop note mới hoàn toàn — existing note đã cover 100% |

---

## Pattern 7: Context File Hierarchy

### Vấn đề
Dự án phức tạp có nhiều context files cho AI agents (instructions, rules, pipeline config). AI không biết file nào có authority cao nhất, dẫn đến conflict rules.

### Giải pháp: 3-Layer Self-Describing Headers
```
Layer 1 — Constitution (AGENTS.md):
    [!IMPORTANT] "Đây là nguồn quy tắc duy nhất — highest authority"
    Chứa: Full schema, architecture rules, behavior specs

Layer 2 — Quick Reference (GEMINI.md / README.md):
    [!NOTE] "Quick reference — defer to AGENTS.md for full schema"
    Chứa: Pointer đến Layer 1, DRY principle — KHÔNG duplicate schema

Layer 3 — Scope Override (scripts/GEMINI.md):
    [!NOTE] "Scoped override — chỉ override BEHAVIOR, KHÔNG override schema"
    Chứa: Mode-specific behavior (VD: Pipeline Mode = text-only, no explanations)
```

### DRY Violation Rule
Nếu Layer 2 hoặc 3 duplicate nội dung từ Layer 1 → replace bằng pointer: `📖 Full schema defined in AGENTS.md §3`. Không cho phép 2 nguồn truth cho cùng 1 rule.

---

## Pattern 8: PowerShell Exit Code Fix

### Vấn đề
Python scripts chạy từ PowerShell terminal trả về **exit code 1** dù không có lỗi. Confuses CI/CD pipelines.

### Root Cause
Python `logging` mặc định ghi vào `stderr`. PowerShell coi bất kỳ output trên `stderr` là error → exit code 1.

### Fix (1 dòng)
```python
# ❌ SAIÔ — ghi vào stderr, PowerShell báo lỗi
logging.basicConfig(level=logging.INFO)

# ✅ ĐÚNG — ghi vào stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
```

### Rule bổ sung cho Windows scripts
```python
# Nếu script in ký tự Unicode (tiếng Việt) ra terminal Windows
sys.stdout.reconfigure(encoding='utf-8')  # phải gọi TRƯỚC logging.basicConfig
```

**Áp dụng cho**: Mọi script có `if __name__ == "__main__"` block chạy từ PowerShell terminal.  
**Không áp dụng**: Daemon dùng `pythonw.exe` (headless, không có terminal).

---

## Quick Reference — Model Routing cho Pipeline Tasks

| Task trong pipeline | Model khuyến nghị | Lý do |
|---|---|---|
| OCR / Vision extract | `ocr-primary` (Gemini Flash) | Fast, cheap, multimodal |
| Draft synthesis (Pass 1) | `qwen-local-primary` | Fast local GPU, Vietnamese |
| Quality check (Pass 2) | `reasoning-gemma` / `claude-sonnet-thinking` | Precision verify |
| Metadata extract | `claude-haiku-4-5` | Clean JSON, no reasoning overhead |
| Large corpus (> 50k tokens) | `gemini-3.1-pro-high` | 1M context window |
| Cross-reference audit | `qwen-local-primary` | Private data, offline |

---

## Files Tham Khảo (VvC Implementation)

| Pattern | Reference file |
|---|---|
| 2-Pass Architecture | `D:\VvC_Notes\scripts\pipeline\synthesize.py` + `self_correct.py` |
| Ground Truth Scoping | `D:\VvC_Notes\scripts\pipeline\ground_truth.py` |
| Think-Tag Stripping | `D:\VvC_Notes\scripts\core\llm\utils.py` |
| Semantic Duplicate Detection | `D:\VvC_Notes\scripts\pipeline\post_process.py` |
| Output Sanitization | xem `ai-gateway-sdk` SKILL.md §Output Processing |
