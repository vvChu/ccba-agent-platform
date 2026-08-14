# Ticket 03: Local Fast-Fail Circuit Breaker cho Mạng VPN

> **Parent Map**: [map.md](map.md)  
> **Loại**: `Task [AFK]`  
> **Assignee**: AI Agent  
> **Trạng thái**: Closed (Resolved)  
> **Thời gian hoàn thành**: 2026-08-14

---

## 🎯 Mục tiêu Đã Đạt Được
1. **Module `circuit_breaker.py`**:
   - Xây dựng lớp `CircuitBreaker` với 3 trạng thái chuẩn (`CLOSED`, `OPEN`, `HALF_OPEN`).
   - Tham số cấu hình: `failure_threshold: int = 3` (lỗi liên tiếp), `recovery_timeout: float = 30.0` (thời gian cooldown).
   - Cơ chế tự động thử thăm dò (probe) khi hết cooldown và chuyển sang `HALF_OPEN`, tự đóng lại `CLOSED` khi thành công, hoặc ngắt lại `OPEN` ngay lập tức nếu probe thất bại.
   - Định dạng ngoại lệ `CircuitBreakerOpenError` theo chuẩn JSON có cấu trúc (`CCBAErrorCode.CIRCUIT_BREAKER_OPEN`).
2. **Client `client.py` (`AIClient` & `AsyncAIClient`)**:
   - Tích hợp `circuit_breaker` trực tiếp vào vòng retry sync và async (`_retry_sync`, `_retry_async`).
   - Tự động ngắt nhanh (Fast-Fail) ngay lập tức khi mất kết nối mạng Tailscale liên tiếp mà không bị treo 60s timeout hay thử retry vô ích.
   - Hỗ trợ truyền custom `circuit_breaker` từ bên ngoài hoặc dùng mặc định theo từng client instance.
3. **Module `__init__.py`**:
   - Export `CircuitBreaker`, `CircuitState`, `CircuitBreakerOpenError`.
4. **Kiểm thử Unit Tests**:
   - Viết trọn bộ 7 bài test trong `packages/ccba-ai/tests/test_circuit_breaker.py` bao phủ toàn bộ chuyển đổi trạng thái (State Transition Matrix).
   - Viết 2 bài integration test trong `test_client.py` và `test_async_client.py` khẳng định `AIClient` & `AsyncAIClient` ngắt ngay lập tức khi breaker mở mà không gọi sang upstream API.
   - **79/79 unit tests pass 100%**, `ruff check` sạch sẽ không cảnh báo.
