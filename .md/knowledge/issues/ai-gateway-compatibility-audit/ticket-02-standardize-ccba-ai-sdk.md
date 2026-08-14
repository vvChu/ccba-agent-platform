# Ticket 02: Chuẩn Hóa Timeout & Archetypes trong ccba-ai SDK

> **Parent Map**: [map.md](map.md)  
> **Loại**: `Task [AFK]`  
> **Assignee**: AI Agent  
> **Trạng thái**: Closed (Resolved)  
> **Thời gian hoàn thành**: 2026-08-14

---

## 🎯 Mục tiêu
Cập nhật `packages/ccba-ai` tuân thủ AI Gateway Client Integration Contract:
1. Thêm tham số `timeout: float | None = None` vào `AIClient` và `AsyncAIClient` với giá trị mặc định 60.0s (nạp từ `AI_GATEWAY_TIMEOUT`).
2. Tách module `ccba_ai/routing.py` chứa `ModelArchetype` và `choose_model`.
3. Export `ModelArchetype` và `choose_model` tại `ccba_ai/__init__.py`.
4. Bổ sung unit tests cho timeout và routing.

---

## 🔍 Kết Quả Triển Khai
- `packages/ccba-ai/src/ccba_ai/client.py`: Đã hỗ trợ `timeout=60.0` cho `OpenAI` và `AsyncOpenAI`.
- `packages/ccba-ai/src/ccba_ai/routing.py`: Đã tạo mới với 4 Archetypes chuẩn.
- `packages/ccba-ai/tests/test_routing.py`: 3 unit tests pass 100%.
- `packages/ccba-ai/tests/test_client.py`: 3 unit tests timeout pass 100%.
- `packages/ccba-ai/tests/test_async_client.py`: 1 unit test timeout pass 100%.
