# Wayfinder Map: CCBA-AI SDK Enhancements & Resilience Pipeline

> **Issue Path**: `.md/knowledge/issues/ccba-ai-sdk-enhancements/map.md`  
> **Trạng thái**: Hoàn thành 100% (Completed)  
> **Chủ đề**: Lộ trình Nâng cấp SDK `ccba-ai` — Quản trị Tự động Ngân sách Token Reasoning, Làm Sạch Dữ liệu Suy Luận, Thu Thập Metadata & Phòng Vệ Rớt Mạng

---

## 🎯 Điểm đích (Destination) — [ĐÃ HOÀN THÀNH 100%]

Gói thư viện cốt lõi **`ccba-ai`** đạt độ tin cậy và tự chủ cao trong mọi môi trường vận hành:
1. **Zero-Friction Reasoning**: Tự động cấp phát `max_tokens` (16384) khi gọi Reasoning Models (Archetype 3) và tự động làm sạch thẻ `<think>` (`strip_thinking=True` mặc định) để chống ô nhiễm Markdown.
2. **Observability & Telemetry**: Hỗ trợ `chat_with_metadata()` / `async_ai.chat_with_metadata()` trích xuất chi tiết token usage, latency_ms và model resolution cho các batch pipeline lớn.
3. **Network Resilience**: Tích hợp Local In-Memory Circuit Breaker tự động ngắt nhanh (Fast-Fail) khi Tailscale VPN rớt mạng, tránh nghẽn luồng xử lý hàng loạt.
4. **100% Test Coverage & Documentation**: Toàn bộ tính năng mới đều có unit test độc lập (79 tests) và tài liệu cập nhật trong `SKILL.md`, `client-setup-guide.md`, và `session_learnings.md`.

---

## 📝 Ghi chú (Notes)

- **Nguyên lý KISS**: Triển khai trực tiếp và súc tích trong `ccba-ai`, không thêm external dependencies nặng nề.
- **Deep Modules**: Tách các mối quan tâm riêng biệt (`routing.py`, `models.py`, `circuit_breaker.py`) để giữ `client.py` gọn gàng.
- **Tương thích ngược 100%**: Mọi hàm `ai.chat()`, `ai.stream()` hiện tại giữ nguyên chữ ký (signature) và giá trị trả về mặc định.

---

## 📍 Quyết định đã chốt (Decisions so far)

- [x] `[Quyết định Mặc định Làm sạch Think Tags]` Thống nhất kích hoạt `strip_thinking: bool = True` mặc định trong `ai.chat()` để bảo vệ output khỏi rò rỉ Chain-of-Thought, đồng thời cho phép người dùng truyền `strip_thinking=False` nếu muốn xem nội dung tư duy.
- [x] `[Quyết định Tự Động Nâng Max Tokens]` Nếu `max_tokens` đang ở mức mặc định (1024/2048) và model đích là Reasoning Model (`gemini-3.7-flash-high`, `claude-sonnet-4-6-thinking`, `reasoning-gemma`, hoặc có hậu tố `-high`/`-thinking`), tự động nâng ngân sách lên **`16,384` tokens**.
- [x] `[TICKET-01: Auto Max-Tokens & Strip Thinking]` Hoàn thành và vượt qua 100% unit tests.
- [x] `[TICKET-02: Telemetry & chat_with_metadata]` Hoàn thành, bổ sung `ChatResult`, `ChatUsage`, và `chat_with_metadata()` (sync/async).
- [x] `[TICKET-03: Local Fast-Fail Circuit Breaker]` Hoàn thành, bổ sung module `circuit_breaker.py`, tích hợp vào `AIClient` & `AsyncAIClient`, kiểm thử vượt qua 100%.
- [x] `[TICKET-04: Documentation & Skill Sync]` Hoàn thành đồng bộ `SKILL.md`, `client-setup-guide.md`, và `session_learnings.md`.

---

## 🚀 Danh sách Ticket Biên giới (Frontier Tickets)

### 1. ✅ `[TICKET-01]` [Auto Max-Tokens Allocation & Auto Strip Think Tags](ticket-01-auto-tokens-and-strip-thinking.md) — Closed
- **Mục tiêu**: Tự động phát hiện reasoning model để nâng `max_tokens` lên 16384 và làm sạch thẻ `<think>` (`strip_thinking=True`).
- **Trạng thái**: Closed (Resolved)

### 2. ✅ `[TICKET-02]` [Chat Telemetry & Metadata Extraction Engine](ticket-02-chat-metadata-telemetry.md) — Closed
- **Mục tiêu**: Bổ sung data model `ChatResult`, `ChatUsage` và phương thức `chat_with_metadata()` đo đạc latency và token usage.
- **Trạng thái**: Closed (Resolved)

### 3. ✅ `[TICKET-03]` [Local Fast-Fail Circuit Breaker cho Mạng VPN](ticket-03-local-circuit-breaker.md) — Closed
- **Mục tiêu**: Xây dựng module `circuit_breaker.py` gọn nhẹ, tích hợp vào `AIClient` & `AsyncAIClient` để Fast-Fail khi mất kết nối mạng.
- **Trạng thái**: Closed (Resolved)

### 4. ✅ `[TICKET-04]` [Tài Liệu Hóa & Đồng Bộ Skill ai-gateway-sdk](ticket-04-docs-and-skill-sync.md) — Closed
- **Mục tiêu**: Cập nhật `.agents/skills/ai-gateway-sdk/SKILL.md`, `.md/knowledge/client-setup-guide.md`, và `.md/knowledge/session_learnings.md`. Chạy full test suite và linter toàn diện.
- **Trạng thái**: Closed (Resolved)
