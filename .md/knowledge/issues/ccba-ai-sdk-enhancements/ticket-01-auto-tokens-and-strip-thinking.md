# Ticket 01: Auto Max-Tokens Allocation & Auto Strip Think Tags

> **Parent Map**: [map.md](map.md)  
> **Loại**: `Task [AFK]`  
> **Assignee**: AI Agent  
> **Trạng thái**: Closed (Resolved)  
> **Thời gian hoàn thành**: 2026-08-14

---

## 🎯 Mục tiêu Đã Đạt Được
1. **Module `routing.py`**:
   - Thêm `is_reasoning_model(model_name: str) -> bool`: Nhận diện các mô hình suy luận sâu (`-high`, `-thinking`, `reasoning`, `o1`, `o3`, `gemini-3.7-flash-high`, `claude-sonnet-4-6-thinking`).
   - Thêm `resolve_max_tokens(model_name, requested_max_tokens, baseline_default, reasoning_allocation=16384) -> int`: Tự động nâng trần lên **16,384 tokens** khi gọi reasoning model nếu `max_tokens` giữ mặc định (1024 hoặc 2048). Bảo toàn giá trị tùy biến nếu người dùng truyền tường minh.
2. **Client `AIClient` & `AsyncAIClient` trong `client.py`**:
   - Tích hợp `resolve_max_tokens` cho cả `chat()`, `chat_multi()`, `async chat()`, `async chat_multi()`.
   - Bổ sung tham số `strip_thinking: bool = True` (mặc định) tự động làm sạch thẻ `<think>...</think>` trước khi trả về chuỗi text cho ứng dụng.
3. **Kiểm thử Unit Tests**:
   - 65/65 unit tests toàn bộ `packages/ccba-ai` pass 100%.
