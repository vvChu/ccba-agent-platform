# Ticket 01: Audit Toàn Bộ Codebase & Skills về Tham Chiếu Model & Timeout

> **Parent Map**: [map.md](map.md)  
> **Loại**: `Research [AFK]`  
> **Assignee**: AI Agent  
> **Trạng thái**: Closed (Resolved)  
> **Thời gian hoàn thành**: 2026-08-14

---

## 🎯 Mục tiêu
Rà soát toàn diện:
1. Các file trong `packages/` (`ccba-ai`, `mdconverter`, `ccba-legal-intel`, `ccba-pdf-prep`).
2. Các scripts trong `.agents/skills/`.
3. Các file hướng dẫn `.env.example`, `.env.ai-gateway`, `SKILL.md`.

---

## 🔍 Kết Quả Audit Toàn Diện

### 1. Tầng Core SDK (`packages/ccba-ai`)
- **Timeout**: `AIClient` và `AsyncAIClient` khởi tạo `OpenAI(...)` và `AsyncOpenAI(...)` chưa truyền tham số `timeout` rõ ràng. Cần bổ sung `timeout: float = 60.0` (và nạp từ `AI_GATEWAY_TIMEOUT`).
- **Model Archetypes**: Thiếu bộ hằng số / Enum / Helper chuẩn hóa 4 Archetypes để các package khác import và sử dụng an toàn, tránh dùng string tùy tiện.

### 2. Tầng Packages Nghiệp Vụ
- **`packages/mdconverter`**:
  - `src/mdconverter/config.py`: Danh sách `models` mặc định chứa `gemini-3-flash`, `gemini-3.1-pro`. Cần cập nhật sang `gemini-3.7-flash`, `ocr-primary`, `gemini-3.7-flash-high`.
- **`packages/ccba-legal-intel`**:
  - `src/ccba_legal/parser.py`: Default model `LegalAnalysisEngine` là `gemini-3.1-pro-high`. Cần cập nhật sang `gemini-3.7-flash-high`.

### 3. Tầng Skills & Scripts Chuyên Sâu
- **`ccba-ai-qc-discovery`**:
  - `discovery_engine.py`: Default `ai_model` là `gemini-3.1-pro-low`. Cần đổi sang `ocr-primary` (Archetype 1) cho OCR TitleBlock.
- **`ccba-ai-qc-batch-orchestrator`**:
  - `orchestrator.py`: Default `ai_model` là `gemini-3.1-pro-low`. Cần đổi sang `gemini-3.7-flash-high` (Archetype 3).
- **`design`**:
  - `scripts/llm_adapter.py`: Default model là `gemini-3.1-pro-preview`. Cần đổi sang `gemini-3.7-flash` (Archetype 2).

### 4. Tầng Tài Liệu, Skill Định Hướng & ADR
- **`.agents/skills/ai-gateway-sdk/SKILL.md`**: Cần cập nhật 4 Archetypes, Timeout Rule 30-60s, Fallback Cascade Mermaid chart.
- **`.md/knowledge/client-setup-guide.md`**: Cần cập nhật bảng Archetypes và Fallback Cascade.
- **`docs/adr/`**: Cần ban hành ADR-0026 ghi nhận Hợp đồng Tích hợp Client AI Gateway mới.

---

## 📌 Kết luận & Chuyển giao
- Ticket 01 đã làm rõ 100% các điểm bất tương thích và hardcoded models cũ trên toàn hệ thống.
- Sẵn sàng unblock **TICKET-02**, **TICKET-03**, **TICKET-04**, **TICKET-05**.
