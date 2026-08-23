# Danh sách Tickets: Safe Execution Sandbox & Self-Healing Loop

Tài liệu này phân rã Đặc tả Kỹ thuật [spec-safe-execution-sandbox.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/specs/spec-safe-execution-sandbox.md) thành các ticket công việc độc lập theo mô hình lát cắt dọc (vertical slice).

👉 **Nguyên tắc:** Chỉ thực hiện các ticket thuộc **Biên giới (Frontier)** — những ticket không bị chặn bởi bất kỳ ticket mở nào khác.

---

## Ticket 1: Triển khai Safe Execution Sandbox Wrapper Core (`scripts/run_safe_eval_wrapper.py`)

**Nghiệp vụ cần làm:**  
Tạo công cụ CLI `scripts/run_safe_eval_wrapper.py` bọc thực thi các lệnh terminal kiểm thử/eval ngầm. Công cụ này phải khởi chạy tiến trình cô lập, tự động gọi Singleton Lock (`ensure_single_instance()`), áp dụng Timeout Watchdog cứng (60s/90s), tách biệt file nhật ký tại `.md/scratch/eval_runs/run_<timestamp>.log` và tự động trích xuất file `diagnostics.json` chứa kết quả chẩn đoán chi tiết.

**Bị chặn bởi:** Không có — có thể bắt đầu ngay.

- [x] Hỗ trợ các tham số CLI: `--cmd` (lệnh cần bọc), `--timeout` (thời gian tối đa), `--output-dir` (thư mục lưu log và report).
- [x] Tích hợp `ensure_single_instance()` dọn dẹp các tiến trình runner trùng lặp bị treo từ trước.
- [x] Ghi nhận toàn bộ stdout/stderr vào file nhật ký cô lập `.md/scratch/eval_runs/run_<timestamp>.log`.
- [x] Tự động trích xuất tệp chẩn đoán cấu trúc `diagnostics.json` chứa: `status` (`PASS` | `TIMEOUT` | `FAILED`), `error_type`, `failed_gate`, `culprit_file`, `summary_traceback`, và `log_file`.

---

## Ticket 2: Viết Unit Test Suite cho Safe Execution Sandbox Wrapper (`scripts/tests/test_run_safe_eval_wrapper.py`)

**Nghiệp vụ cần làm:**  
Xây dựng bộ kiểm thử tự động độc lập cho wrapper tại `scripts/tests/test_run_safe_eval_wrapper.py` nhằm xác minh tính ổn định của cơ chế bẫy lỗi mà không phụ thuộc vào toàn bộ codebase.

**Bị chặn bởi:** Ticket 1 (Triển khai Safe Execution Sandbox Wrapper Core).

- [x] Viết test `test_wrapper_successful_execution()`: Kiểm chứng lệnh thành công (exit code 0), `diagnostics.json` có `status = PASS`.
- [x] Viết test `test_wrapper_timeout_expired()`: Kiểm chứng lệnh chạy quá giờ bị kill, `diagnostics.json` có `status = TIMEOUT`.
- [x] Viết test `test_wrapper_failed_command_traceback()`: Kiểm chứng lệnh bị lỗi, `diagnostics.json` có `status = FAILED` và trích xuất đúng 20-30 dòng traceback cuối cùng.
- [x] Đảm bảo lệnh `.venv\Scripts\python.exe -m pytest scripts/tests/test_run_safe_eval_wrapper.py` chạy qua 100%.

---

## Ticket 3: Cập nhật Skill & Workflow Quy chế Async Execution & Self-Healing Protocol

**Nghiệp vụ cần làm:**  
Cập nhật tệp kỹ năng [.agents/skills/eval-gate/SKILL.md](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/SKILL.md) và workflow [/ccba-eval-gate](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-eval-gate.md) để quy định Agent luôn kích hoạt runner ngầm thông qua `run_safe_eval_wrapper.py` với `WaitMsBeforeAsync` $\le 2000$ms và tự động đọc `diagnostics.json` để sửa lỗi mã nguồn khi nhận tin nhắn notification.

**Bị chặn bởi:** Ticket 1 & Ticket 2.

- [x] Cập nhật quy tắc `WaitMsBeforeAsync` $\le 2000$ms trong `eval-gate/SKILL.md`.
- [x] Thêm quy trình Self-Healing Feedback Protocol (đọc `diagnostics.json` và vá code tự động) vào [/ccba-eval-gate](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-eval-gate.md).
