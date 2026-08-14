# Ticket 04: Rà Soát & Điều Chỉnh Model Routing trong Specialized Packages & Skills

> **Parent Map**: [map.md](map.md)  
> **Loại**: `Task [AFK]`  
> **Assignee**: AI Agent  
> **Trạng thái**: Closed (Resolved)  
> **Thời gian hoàn thành**: 2026-08-14

---

## 🎯 Mục tiêu
Cập nhật model mặc định trong các packages và skills chuyên sâu:
1. `packages/mdconverter/src/mdconverter/config.py`: Đổi danh sách fallback models sang `["qwen-local-primary", "gemini-3.7-flash", "ocr-primary", "gemini-3.7-flash-high", "claude-sonnet-4-6"]`.
2. `packages/ccba-legal-intel/src/ccba_legal/parser.py`: Default `LegalAnalysisEngine` sang `gemini-3.7-flash-high`.
3. `packages/ccba-pdf-prep/src/ccba_pdf_prep/core.py`: Default model sang `gemini-3.7-flash`.
4. `.agents/skills/ccba-ai-qc-discovery/scripts/discovery_engine.py`: Default `ai_model` sang `gemini-3.7-flash`.
5. `.agents/skills/ccba-ai-qc-batch-orchestrator/scripts/orchestrator.py`: Default `ai_model` sang `gemini-3.7-flash-high`.
6. `.agents/skills/design/scripts/llm_adapter.py`: Default model sang `gemini-3.7-flash`.

---

## 🔍 Kết Quả Triển Khai
- Tất cả các điểm hardcoded model cũ đã được chuyển dịch hoàn tất.
