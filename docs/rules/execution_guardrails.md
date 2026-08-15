# CCBA Execution Guardrails & Async Task Policy

> **Tài liệu Tham chiếu Quy chuẩn Thực thi (Layer 2)**  
> Áp dụng cho toàn bộ các tác vụ lập trình, chạy kiểm thử, và điều phối quy trình ngầm trên CCBA Platform.

---

## 1. Scoped Test Execution (Kiểm thử Cô lập)
- Nghiêm cấm kích hoạt các lệnh kiểm thử toàn diện (unscoped `pytest`) trên toàn bộ repository mà không chỉ định rõ phạm vi.
- Luôn chỉ định rõ file test hoặc module mục tiêu: ví dụ `pytest packages/{pkg}/tests/test_file.py` hoặc cờ loại trừ `-m "not slow and not stress"`.

---

## 2. Bounded Async Task & Anti-Polling Circuit Breaker
- Khi một lệnh chạy dưới dạng tác vụ ngầm (Background Task):
  - Agent chỉ được dùng `manage_task status` tối đa **2 lần** để kiểm tra tiến độ tác vụ ngắn.
  - Nếu tác vụ vẫn ở trạng thái **RUNNING** sau 2 lần kiểm tra, Agent **NGHIÊM CẤM** lặp polling `manage_task status` dồn dập trong cùng một lượt. Agent phải xuất ra thông báo súc tích cho người dùng rồi **kết thúc lượt (End Turn)** để chờ thông báo Reactive Wakeup từ hệ thống.

---

## 3. TDD Retry Cap (Giới hạn Vòng lặp Sửa lỗi)
- Trong vòng lặp Red→Green→Refactor (TDD) hoặc edit→test, Agent chỉ được lặp lại tối đa **5 vòng** cho cùng một seam hoặc test file.
- Nếu sau 5 vòng test vẫn fail, Agent phải dừng lại, commit Work-In-Progress (WIP), ghi nhận các blockers chưa giải quyết được, và xin chỉ thị từ người dùng — tuyệt đối không tiếp tục lặp cho đến khi cạn context budget.

---

## 4. Anti-Duplicate Background Runner
- Nghiêm cấm Agent kích hoạt nhiều lệnh chạy ngầm (`run_command` async) cho cùng một script test runner hoặc harness evaluation.
- Mọi script test runner ngầm bắt buộc phải tích hợp Singleton Process Lock (`ensure_single_instance()`) và kiểm tra tiến trình cũ trước khi khởi động.

---

## 5. Safe Process Termination Invariant
- Khi viết hoặc thực thi bất kỳ logic nào có chức năng dọn dẹp hoặc duy trì đơn tiến trình (`ensure_single_instance()`), Agent **bắt buộc phải loại trừ** cả tiến trình hiện tại (`os.getpid()`) và tiến trình cha (`os.getppid()`).
- Nghiêm cấm kích hoạt `taskkill` hoặc `proc.terminate()` lên `os.getppid()` để tránh làm sập Agent Server Host.

---

## 6. Task Log Readiness Check
- Nghiêm cấm gọi `view_file` tới tệp `task-XXX.log` lập tức ngay sau lượt `run_command` async mà không kiểm tra xem tệp tin log đã thực sự được hệ thống tạo và ghi dữ liệu lên ổ đĩa hay chưa.
- Phải dùng `manage_task status` hoặc chờ thông báo hoàn tất từ hệ thống trước khi đọc log.

---

## 7. Invalid Args Circuit Breaker
- Khi gặp lỗi `model output error: invalid tool call error (invalid_args)` từ **2 lần liên tiếp trở lên**, đây là tín hiệu context budget sắp cạn kiệt.
- Agent phải **dừng ngay lập tức**, commit WIP nếu có thay đổi chưa lưu, tóm tắt trạng thái công việc hiện tại, và thông báo cho người dùng mở phiên mới để tiếp tục — không được cố gắng chạy thêm bất kỳ tool call nào.

---

## 8. 2-Tier Test Speed Compliance
- Mọi tệp kiểm thử đơn vị (Unit Test) mới viết bắt buộc phải chạy dưới 2.0 giây.
- Các tệp test tích hợp mạng, Chromium CDP, hoặc LLM latency nặng bắt buộc phải được dán decorator `@pytest.mark.slow` hoặc `@pytest.mark.stress` để tự động loại trừ khỏi vòng lặp kiểm thử nhanh hàng ngày (`-m "not slow"`).
