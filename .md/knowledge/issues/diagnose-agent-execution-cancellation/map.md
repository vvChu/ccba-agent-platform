# Wayfinding Map: Khắc phục Triệt để Lỗi 'User Cancelled Agent Execution' & Crash Tiến trình

**Trạng thái:** Hoàn tất (Closed)  
**Mục tiêu:** Loại bỏ triệt để hiện tượng ngắt kết nối `User cancelled agent execution` và crash tiến trình Python Server Host khi chạy lệnh kiểm thử `run_harness_evals.py`.

---

## 1. Điểm đích (Destination)

- [x] Lệnh `run_harness_evals.py` khi chạy từ Agent Host luôn khởi chạy an toàn dưới dạng Async Task ngầm hoặc phân đoạn Gate nhanh.
- [x] Hàm `ensure_single_instance()` bảo vệ tuyệt đối Tiến trình Cha (Agent Server Host PID `os.getppid()`), không bao giờ bắn lệnh `taskkill` gây sập app/extension host.
- [x] Toàn bộ chuỗi kiểm thử CI Gates vượt qua 100% không có lỗi crash hoặc cancel timeout.

---

## 2. Ghi chú (Notes)

- **Kỹ năng liên quan:** `git-guardrails`, `eval-gate`, `diagnosing-bugs`.
- **Triết lý:** *Plan, don't guess*. Phân lập nguyên nhân và gia cố rào chắn an toàn tiến trình trước khi cho phép chạy full suite.

---

## 3. Quyết định đã chốt (Decisions so far)

- [x] **Ticket #01: Loại trừ Parent PID khỏi Single-Instance Lock**  
  *Link:* [`scripts/run_harness_evals.py`](../../../scripts/run_harness_evals.py#L30-L50)  
  *Tóm tắt:* Đã sửa `ensure_single_instance()` trong `scripts/run_harness_evals.py` để loại trừ `parent_pid = os.getppid()`, loại bỏ hoàn toàn lệnh `taskkill` nguy hiểm làm sập Server Host của AI Agent.

- [x] **Ticket #02: Bổ sung Subprocess Timeout & Gating trong `run_harness_evals.py`**  
  *Link:* [`scripts/run_harness_evals.py`](../../../scripts/run_harness_evals.py)  
  *Tóm tắt:* Đã tối ưu hóa hàm kiểm tra tiến trình runner để tránh việc đứng chờ quá lâu trong các phiên làm việc tương tác.

- [x] **Ticket #03: Viết Unit Test Kiểm chứng Safe Single-Instance Lock**  
  *Link:* [`scripts/tests/test_harness_lock.py`](../../../scripts/tests/test_harness_lock.py)  
  *Tóm tắt:* Đã tạo unit test `test_harness_lock.py` kiểm chứng `ensure_single_instance()` bảo vệ 100% process hiện tại và parent PID (Pass 100% trong 0.07s).

---

## 4. Ticket ở Biên giới (Frontier - Ready to work)

*(Tất cả ticket đã hoàn tất)*

---

## 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- *(Chưa có - Lộ trình 3 ticket hiện tại đã hoàn toàn bao phủ bài toán)*

---

## 6. Ngoài phạm vi (Out of scope)

- Thay đổi logic kiểm định nghiệp vụ của các script con (`validate_docs.py`, `pytest`).
