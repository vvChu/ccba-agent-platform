---
name: ccba-llm-pipeline-patterns
description: Anti-patterns và best practices thiết kế LLM processing pipelines (VvC LLM OS). Không dùng để chạy tìm kiếm ngữ nghĩa BM25/Embedding.
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Kiểm định
bundle: _software
scope: universal
posture: seam-exempt
tier: kernel
command: /ccba-llm-pipeline-patterns
metadata:
  version: "1.5.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 2.0
  a: 4.0
  p: 1.0
triggers:
- llm pipeline
- pipeline patterns
- 2-pass
- synthesis pipeline
- self-correction
- multi turn memory
---

# LLM Pipeline Patterns

Pattern library cho các pipeline LLM multi-stage — đúc rút từ thực tế vận hành **VvC LLM OS** (v5.1 → v8.15, 2026). Mỗi pattern đều có ít nhất 1 incident thực tế chứng minh sự cần thiết.

> [!IMPORTANT]
> Đây là **documentation skill** — không có code cần install. Load file này khi thiết kế bất kỳ pipeline LLM nào trong CCBA.

## Danh Mục 17 Pipeline Patterns (VvC LLM OS v5.1 → v8.15)

| Pattern | Tên Pattern | Cơ Chế & Ngưỡng Quyết Định Cốt Lõi | Tài Liệu Chi Tiết |
| :---: | :--- | :--- | :--- |
| `P1` | **2-Pass Architecture** | Pass 1 fast draft; Pass 2 reasoning chỉ sửa **1 section cụ thể** + ground truth | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P2` | **Ground Truth Scoping** | Lọc theo chapter + ~500 chars opening text (`BM25` score tăng `60 -> 1193`) | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P3` | **Min Content Threshold** | `< 50 chars` skip early; `50-200` `confidence: low`; `> 200` chạy chuẩn | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P4` | **Idempotent Stages** | Kiểm tra tồn tại + upsert YAML (`safe_load -> merge -> safe_dump`) | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P5` | **Error String Detection** | Chặn string lỗi (`"Error connecting"`, `"Rate limit..."`, `"I cannot"`) | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P6` | **Semantic Dedup Gate** | Hook `>= 4` hoặc size `> P95*1.3` -> `SEPARATE`; sim `>= 0.88` -> LLM arbitrator | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P7` | **Context File Hierarchy** | Layer 1 (`AGENTS.md`) SSOT; Layer 2/3 pointer-only, không duplicate schema | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P8` | **PowerShell Exit Code** | `sys.stdout.reconfigure(encoding="utf-8")` + `logging(..., stream=sys.stdout)` | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P9` | **Async Poller Drainage** | Vòng lặp vét cạn (`max_queries=10`) + `extract_sections()` test assertion | [core](references/core_pipeline_patterns_1_to_9.md) |
| `P10` | **Dual-Scope Visual Ctx** | Ngữ cảnh 2 lớp (`TARGET SECTION` + `FULL ARTICLE` tối đa 12,000 chars) | [adv](references/advanced_pipeline_patterns_10_to_17.md) |
| `P11` | **Conditional Artifacts** | Chỉ nhúng Mermaid/Excalidraw/D2/DOCX khi yêu cầu hoặc có quy trình đa bước | [adv](references/advanced_pipeline_patterns_10_to_17.md) |
| `P12` | **Zero-Broken-Link Diagrams** | Sinh warning placeholder hợp lệ + vệ sinh ký tự cấm Windows `[<>:"/\\|?*]` | [adv](references/advanced_pipeline_patterns_10_to_17.md) |
| `P13` | **2-Phase Map-Reduce** | Tài liệu `> 200k chars`: chia chunk heading-aware `40k` overlap `1k` -> reduce | [adv](references/advanced_pipeline_patterns_10_to_17.md) |
| `P14` | **Conditional Memory** | Chỉ inject `N=1` lượt gần nhất (`<= 4k chars`) khi khớp continuity regex | [adv](references/advanced_pipeline_patterns_10_to_17.md) |
| `P15` | **2-Tier Noise Defense** | Tầng 1 `is_live` + DOM + `pHash < 2`; Tầng 2 Vision judge (`KEY_FRAMES: []`) | [adv](references/advanced_pipeline_patterns_10_to_17.md) |
| `P16` | **Thinking Starvation** | Ép `enable_thinking: False` / alias `local-instruct` khi `max_tokens <= 512` | [adv](references/advanced_pipeline_patterns_10_to_17.md) |
| `P17` | **Tier Fallback Matrix** | Ánh xạ `TIER_FALLBACK_MATRIX` + chuẩn hóa hậu tố (`-high`/`-medium`/`-low`) | [adv](references/advanced_pipeline_patterns_10_to_17.md) |

---

## Quick Reference — Model Routing & Decision Rules

| Task trong pipeline | Model / Alias khuyến nghị | Lý do & Ràng buộc |
|---|---|---|
| Deep reasoning & Topic Essay | `claude-opus-4-6-thinking` / `gemini-4-argon-high` | Tier 1 CLI (`agy`), suy luận sâu |
| Concept Synthesis | `gemini-4-argon-medium` → `gemini-3.8-flash-high` | Tiết kiệm ~80% output tokens, đạt chuẩn Schema |
| Self-Correction / Ground Truth | `gemini-4-argon-low` (`0` thinking tokens) | Đối soát trích dẫn tất định |
| Fast JIT Map / Interactive | `gemini-3.8-flash-high` | Port 8090, ~2s, hỗ trợ auto-downgrade |
| Extraction / JSON / HyDE | `local-instruct` / `claude-haiku-4-5` | `enable_thinking: False`, chống thinking starvation |
| Draft Synthesis / Offline Audit | `qwen-local-primary` | Local GPU, bảo mật offline |
| Quality Verify / Large Corpus | `reasoning-gemma` / `gemini-3.1-pro-high` | Verify chính xác hoặc ngữ cảnh `1M` |

---

## Tiêu chí hoàn thành & Progressive Disclosure (Level 3)

- **Tiêu chí hoàn thành:** Pipeline LLM thiết kế/cập nhật phải vượt qua `python -m ccba_harness verify-patch` với exit code 0, áp dụng đúng pattern chống starvation/lỗi string/broken link và bảo toàn toàn bộ test hiện có.

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/core_pipeline_patterns_1_to_9.md` | Chi tiết Patterns 1–9: 2-Pass Architecture, BM25 Chapter Scoping, Idempotency, Error Strings, Dedup Gate, Poller Drainage Loop |
| `references/advanced_pipeline_patterns_10_to_17.md` | Chi tiết Patterns 10–17: Dual-Scope Context, Conditional Diagrams, Map-Reduce >200k, Conditional Memory, pHash Multimodal Filter, Thinking Starvation & Tier Fallback Matrix |
