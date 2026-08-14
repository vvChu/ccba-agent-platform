# Ticket 02: Chat Telemetry & Metadata Extraction Engine

> **Parent Map**: [map.md](map.md)  
> **Loại**: `Task [AFK]`  
> **Assignee**: AI Agent  
> **Trạng thái**: Closed (Resolved)  
> **Thời gian hoàn thành**: 2026-08-14

---

## 🎯 Mục tiêu Đã Đạt Được
1. **Module `models.py`**:
   - Định nghĩa `ChatUsage(prompt_tokens, completion_tokens, total_tokens)`.
   - Định nghĩa `ChatResult(content, model, usage, latency_ms, raw_response)`.
2. **Client `client.py`**:
   - Cung cấp `AIClient.chat_with_metadata()` và `AsyncAIClient.chat_with_metadata()`.
   - Tự động đo `latency_ms` bằng `time.perf_counter()`, trích xuất usage token từ upstream gateway, và làm sạch think tags.
3. **Module `__init__.py`**:
   - Export `ChatResult`, `ChatUsage`, và hàm shorthand `chat_with_metadata = ai.chat_with_metadata`.
4. **Kiểm thử Unit Tests**:
   - Thêm 3 test cases cho `AIClient` và `AsyncAIClient` kiểm tra việc đóng gói `ChatResult`, tính toán latency và an toàn khi `usage` là None.
   - **47/47 tests pass 100%**, `ruff check` sạch sẽ.
