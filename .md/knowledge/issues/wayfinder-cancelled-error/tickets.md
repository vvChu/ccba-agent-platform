# Danh sách Tickets: Khắc Phục Triệt Để Lỗi "User cancelled agent execution"

Chuỗi ticket này phân rã từ tài liệu Spec [spec-wayfinder-cancelled-error.md](../../specs/spec-wayfinder-cancelled-error.md) và Wayfinder Map [map.md](map.md).

👉 **Nguyên tắc**: Chỉ thực hiện các ticket nằm ở **Biên giới (Frontier)** - là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái `[x]` hoàn thành.

---

## Ticket 1: Safe Runner Cô lập (Detached Process Runner)
- **Mô tả nghiệp vụ:** Cho phép AI Agent kích hoạt các lệnh kiểm thử hoặc kịch bản dài qua tiến trình detached độc lập (`safe_runner.py`), ghi log JSON ra đĩa để kết quả test không bị ngắt ngầm khi Server Daemon gặp sự cố restart chớp nhoáng.
- **Bị chặn bởi:** Không có — có thể bắt đầu ngay.
- **Trạng thái:** [x] **Hoàn thành** *(Commit `8ae987b`)*

- [x] Tạo `scripts/safe_runner.py` hỗ trợ các cờ `--command`, `--status`, `--help`.
- [x] Đảm bảo log stdout/stderr và exit code được ghi nhận an toàn vào đĩa đệm.

---

## Ticket 2: Phân rã Test Suite & Scoped Execution
- **Mô tả nghiệp vụ:** Tách biệt và tối ưu hóa chuỗi test case, chuyển đổi thói quen chạy full test suite sang chạy scoped test theo từng file để tiết kiệm token ngữ cảnh.
- **Bị chặn bởi:** Ticket 1.
- **Trạng thái:** [x] **Hoàn thành** *(23/23 tests PASSED qua safe_runner)*

- [x] Kiểm thử độc lập từng file test trong `packages/ccba-legal-intel/tests`.
- [x] Xác nhận không xảy ra lỗi cancellation khi chạy qua `safe_runner.py`.

---

## Ticket 4: Policy & Workflow Guardrails (TDD Retry Cap)
- **Mô tả nghiệp vụ:** Cập nhật Hiến pháp `AGENTS.md` và skill `/ccba-implement` để áp đặt giới hạn số vòng lặp Edit-Test tối đa 5 lượt cho mỗi seam, bắt buộc lưu WIP commit và xin chỉ thị người dùng để chống bùng nổ token.
- **Bị chặn bởi:** Ticket 1.
- **Trạng thái:** [x] **Hoàn thành**

- [x] Bổ sung quy định "TDD Retry Cap" vào Layer 1 `AGENTS.md`.
- [x] Cập nhật hướng dẫn trong `implement/SKILL.md` và `tdd/SKILL.md`.

---

## Ticket 5: Invalid Args Circuit Breaker Guardrail
- **Mô tả nghiệp vụ:** Cấu hình rào chắn tự động ngắt phiên an toàn khi Agent gặp lỗi tool call `invalid_args` ≥ 2 lần liên tiếp, phòng tránh việc lặp vô tận khi cạn ngữ cảnh.
- **Bị chặn bởi:** Ticket 4.
- **Trạng thái:** [x] **Hoàn thành**

- [x] Bổ sung quy định "Invalid Args Circuit Breaker" vào Layer 1 `AGENTS.md`.
- [x] Cập nhật hướng dẫn ngắt phiên chủ động trong `implement/SKILL.md`.

---

## Ticket 3: Tích hợp Exponential Backoff Retry & Circuit Breaker vào `ccba-ai` SDK
- **Mô tả nghiệp vụ:** Nâng cấp package `ccba-ai` (`AIClient` và `AsyncAIClient`) tự động bắt lỗi gián đoạn mạng ngắt kết nối (502/503/504, Connection Reset, Timeout) và thử lại 3 lần với khoảng thời gian chờ tăng theo cấp số nhân (1s -> 2s -> 4s). Nếu quá 3 lần, kích hoạt Circuit Breaker trả về ngoại lệ có cấu trúc.
- **Bị chặn bởi:** Ticket 1.
- **Trạng thái:** [x] **Hoàn thành** *(38/38 tests PASSED qua safe_runner)*

- [x] Bổ sung cơ chế retry cho `chat()`, `chat_multi()`, `stream()`, `transcribe()` trong `AIClient`.
- [x] Bổ sung cơ chế retry tương ứng cho `AsyncAIClient`.
- [x] Bổ sung unit tests cho retry & circuit breaker trong `test_client.py` và `test_async_client.py`.
- [x] Chạy kiểm thử an toàn qua `safe_runner.py`.

---

## Ticket 6: Tự động Dọn Dẹp Zombie Process & Health Monitor
- **Mô tả nghiệp vụ:** Nâng cấp `scripts/session_cleanup.py` bổ sung `clean_zombies()` và `health_check()`, kiểm tra dung lượng ổ đĩa, bộ nhớ và dọn dẹp các tiến trình mồ côi (`pytest`/`safe_runner`) trước/sau mỗi phiên.
- **Bị chặn bởi:** Ticket 3.
- **Trạng thái:** [x] **Hoàn thành** *(Đã tích hợp vào session_cleanup.py)*

- [x] Viết hàm `clean_zombies()` quét và tiêu diệt orphan processes với fallback taskkill/wmic.
- [x] Viết hàm `health_check()` chẩn đoán sức khỏe bộ nhớ/ổ đĩa.
- [x] Tích hợp vào quy trình session cleanup tự động.
