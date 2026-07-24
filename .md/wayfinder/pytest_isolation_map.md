# Bản đồ Định hướng Wayfinder: Cô lập & Tối ưu Bộ test `ccba-legal-intel`

## 1. Điểm đích (Destination)
Bộ test suite gồm 17 tệp tại `packages/ccba-legal-intel/tests` được chạy hoàn toàn ổn định, phân lập theo từng tầng/file, thời gian phản hồi từng file test < 3 giây, tự động dọn dẹp tài nguyên tạm (Mutex Lock files), và KHÔNG BAO GIỜ bị treo/đơ dẫn đến lỗi "User cancelled agent execution".

---

## 2. Ghi chú (Notes)
- **Tái sử dụng & Tuân thủ Hiến pháp AGENTS.md**: Nghiêm cấm chạy unscoped `pytest -q` trên toàn thư mục dạng đồng bộ block luồng.
- **Môi trường**: Windows OS, Python virtualenv tại `.venv\Scripts\pytest`.
- **Kỹ năng áp dụng**: `wayfinder`, `eval-gate`, `tdd`.

---

## 3. Quyết định đã chốt (Decisions so far)
- **[Đã chốt - 2026-07-23] Lập Kế hoạch cô lập (Implementation Plan)**: Đã xác định 17 test file thuộc 3 phân nhóm (Fast Pure Logic, Mock Integration, và Adversarial/Mutex Lock).

---

## 4. Ticket ở Biên giới (Frontier Unblocked Tickets)

### Ticket 1: [Investigation/AFK] Đo benchmark thời gian chạy thực tế từng test file
- **Mục tiêu**: Chạy đơn lẻ từng file trong 17 files test để ghi nhận exact duration và phát hiện file nào gây trễ (> 2s).
- **Trạng thái**: Open (Unblocked)
- **Assignee**: AI Agent

### Ticket 2: [Task/AFK] Bổ sung Lock Auto-Cleanup Fixture tại `conftest.py`
- **Mục tiêu**: Đảm bảo tệp `tvpl_vip_session.lock` được dọn dẹp sạch sau mỗi test case để tránh treo dây chuyền.
- **Trạng thái**: Open (Unblocked)
- **Assignee**: AI Agent

### Ticket 3: [Task/AFK] Cấu hình Pytest Timeout & Isolation Guardrail
- **Mục tiêu**: Cấu hình rào chắn timeout (max 5 giây/test) và ngắt sớm `--maxfail=1` khi phát hiện lặp vô hạn.
- **Trạng thái**: Open (Unblocked)
- **Assignee**: AI Agent

### Ticket 4: [Task/AFK] Xây dựng Isolated Test Runner Script (`.md/scripts/run_isolated_tests.py`)
- **Mục tiêu**: Tạo Python script điều phối chạy theo lô cô lập, bắt lỗi và xuất báo cáo hiệu năng từng tệp test.
- **Trạng thái**: Open (Unblocked)
- **Assignee**: AI Agent

---

## 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- **Cấu hình Async Background Monitoring cho AI Agent**: Cách thức AI Agent gọi runner qua Background Task sao cho nhận thông tin tức thì khi có 1 file fail mà không cần chờ toàn bộ suite.

---

## 6. Ngoài phạm vi (Out of Scope)
- Sửa lại logic nghiệp vụ chính của cào dữ liệu `ccba_legal` (chỉ tập trung cô lập và tối ưu môi trường test & runner).
