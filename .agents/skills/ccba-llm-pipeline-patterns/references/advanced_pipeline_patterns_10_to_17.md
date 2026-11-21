# LLM Pipeline Patterns (Part 2: Multimodal, Memory, Map-Reduce & Routing, Patterns 10–17)

Tài liệu tham chiếu Level 3 cho `ccba-llm-pipeline-patterns`, lưu trữ đầy đủ kiến trúc, invariants và code mẫu Python cho Patterns 10–17 cùng bảng định tuyến mô hình.

## Pattern 10: Dual-Scope Context for Visual Workers

Cung cấp ngữ cảnh 2 lớp cho worker sinh sơ đồ (tối đa 12,000 ký tự / ~3,000 tokens):

```python
target_section = source_text[sec_start:sec_end].strip()
full_context = source_text[:12000].strip()

prompt = (
    f"=== [TARGET SECTION (Trọng tâm sơ đồ)] ===\n{target_section}\n\n"
    f"=== [FULL ARTICLE CONTEXT (Toàn bộ bài viết tham chiếu)] ===\n{full_context}"
)
```

---

## Pattern 11: Prompt Conditional Artifact Anchors

Chỉ chèn sơ đồ khi (1) người dùng yêu cầu trực tiếp, hoặc (2) phân tích có quy trình nhiều bước / kiến trúc đa tầng; **cấm chèn mặc định** khi chỉ giải thích khái niệm:
- **Excalidraw:** mindmap, mô hình khái niệm, ma trận 2x2.
- **Mermaid:** Flowchart TD, Sequence, cây phân cấp.
- **D2:** topology mạng, hạ tầng phân tán.
- **DOCX, CSV, XLSX:** chỉ xuất khi người dùng yêu cầu cụ thể.

---

## Pattern 12: Zero-Broken-Link Diagram Fallbacks & Windows Path Hygiene

```python
# Tạo placeholder hợp lệ thay vì return im lặng (gây broken link trên Obsidian)
mermaid_code = (
    "flowchart TD\n"
    f'    err["⚠️ Không thể khởi tạo sơ đồ: {safe_title}<br/><i>{safe_error}</i>"]\n'
    "    style err fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#991b1b;\n"
)

# Vệ sinh ký tự cấm trên Windows trước khi ghi đĩa
safe_name = re.sub(r'[<>:"/\\|?*]', "_", raw_filename)
```

---

## Pattern 13: Heading-Aware 2-Phase Map-Reduce (>200,000 chars)

```python
def map_reduce_summarize(text: str, target_model: str = "gemini-3.8-flash-high", max_chars: int = 200_000) -> str:
    """Tóm tắt Map-Reduce cho tài liệu vượt ngưỡng an toàn."""
    if len(text) <= max_chars:
        return text

    chunks = split_into_chunks(text, chunk_size=40_000, overlap=1_000)
    summaries = []
    for idx, chunk in enumerate(chunks):
        chunk_sum = call_fast_llm(
            f"Trích xuất luận điểm cốt lõi, số liệu, thực thể phần {idx+1}/{len(chunks)}:\n\n{chunk}",
            model=target_model,
        )
        summaries.append(f"### Phân đoạn {idx+1}/{len(chunks)}\n{chunk_sum}")

    combined = "\n\n".join(summaries)
    final_summary = call_reasoning_llm(f"Tổng hợp bản tóm tắt học thuật toàn diện:\n\n{combined}")
    return (
        f'<large_document_map_reduce_summary original_chars="{len(text)}" chunks="{len(chunks)}">\n'
        f"{final_summary}\n</large_document_map_reduce_summary>"
    )
```

- **Key Invariants:** Cắt theo `# > ## > ### > \n\n`, overlap `1,000` ký tự, bọc metadata tag `original_chars` + `chunks`.

---

## Pattern 14: Conditional Short-term Multi-turn Memory

Chỉ inject lịch sử khi khớp tín hiệu liên kết ngữ nghĩa và giới hạn cứng `N=1`, tối đa `4,000` ký tự trong thẻ `<previous_conversation_context>` tách biệt khỏi `<rag_context>`:

```python
CONTINUITY_PATTERN = re.compile(
    r"(ở trên|vừa rồi|trước đó|vừa nêu|bảng trên|phần \d+|mục \d+|ý thứ \d+|luận điểm \d+|"
    r"nói rõ hơn|giải thích thêm|làm rõ|chi tiết hơn|tiếp tục|tiếp theo|bổ sung|so sánh với cái trước)",
    re.IGNORECASE,
)

def detect_continuity_signal(query: str) -> bool:
    return bool(CONTINUITY_PATTERN.search(query))

def extract_last_exchange(file_content: str, max_chars: int = 4_000) -> dict[str, str] | None:
    ...
    return {"query": clean_q[:1000], "response": clean_r[:max_chars]}
```

---

## Pattern 15: Two-Tier Multimodal Noise Defense

1. **Tầng 1 — Bộ lọc tất định (Zero-Token):** Kiểm tra `is_live` hủy livestream vô tận; lọc `live_chat` / `live_chat_replay` & DOM rác (`<div`, `yt-formatted-string`); chạy Perceptual Hashing (pHash, khoảng cách Hamming `< 2`) để loại `>= 90%` ảnh tĩnh trùng lặp trước khi gửi lên Vision API (`<= 5-10` frames).
2. **Tầng 2 — Cổng nhận thức (Vision SLM):** Prompt kèm negative constraint bắt buộc xuất `KEY_FRAMES: []` nếu là ảnh trang trí / chân dung người nói; chỉ phê duyệt slide/sơ đồ/bảng biểu để trích xuất HD `1280x720` + Alt-Text.

---

## Pattern 16: Thinking Token Starvation Defense (RULE-5.8)

Với prompt ngắn có cấu trúc (`max_tokens <= 512`, `extract_json()`, HyDE), tắt thinking từ chat template hoặc dùng alias `local-instruct` / `rag-core` để tránh đốt hết budget vào `<think>` dẫn tới `content: None` (`finish_reason: length`):

```python
response = await client.chat.completions.create(
    model="local-instruct",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=300,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

# Auto-Recovery fallback khi cạn token
if response.choices[0].finish_reason == "length" and not response.choices[0].message.content:
    return await call_llm(prompt, enable_thinking=False, max_tokens=max_tokens * 2)
```

---

## Pattern 17: Tier-Aware Fallback Translation & CLI Suffix Guard

Khi mô hình thế hệ mới chỉ có trên Tier 1 CLI (`agy`), luôn ánh xạ qua `resolve_tier_fallback(model, tier, default)` thay vì truyền nguyên `explicit_model` xuống các tier thấp (gây `404` dây chuyền), và chuẩn hóa hậu tố (`-high`, `-medium`, `-low`) trước khi chạy `subprocess.run` (tránh treo binary `agy` 15s):

```python
_BARE_GEMINI_CLI_PATTERN = re.compile(r"^gemini-\d+(?:\.\d+)*-(?:flash|argon)$", re.IGNORECASE)

TIER_FALLBACK_MATRIX: dict[str, dict[str, str]] = {
    "gemini-4-argon-high": {"gateway": "gemini-3.8-flash-high", "copilot": "claude-sonnet-4.6", "gemini": "gemini-3.1-flash-lite-preview"},
    "gemini-4-argon-medium": {"gateway": "gemini-3.8-flash-high", "copilot": "gpt-5-mini", "gemini": "gemini-3.1-flash-lite-preview"},
    "gemini-4-argon-low": {"gateway": "gemini-3.1-flash-lite", "copilot": "gpt-5-mini", "gemini": "gemini-3.1-flash-lite-preview"},
}
```
