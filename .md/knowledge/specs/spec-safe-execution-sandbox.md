# 📋 Technical Spec: Safe Execution Sandbox & Self-Healing Loop

> **Trạng thái:** READY FOR AGENT  
> **Mã tính năng:** `safe-execution-sandbox`  
> **Vị trí file:** `.md/knowledge/specs/spec-safe-execution-sandbox.md`  

---

## Problem Statement

Khi AI Agent thực thi các lệnh kiểm thử toàn diện, CI Eval Gates hoặc script Python chạy dài hạn trong Antigravity IDE, hai sự cố chính thường xảy ra:
1. **Lỗi ngắt kết nối `User cancelled agent execution`**: Do gọi lệnh với tham số chờ đồng bộ quá lâu (`WaitMsBeforeAsync: 10000`), hệ thống IDE Client bị treo giao diện trong 10 giây và đứt kết nối khi server restart hoặc khi tiến trình chưa hoàn tất.
2. **Thiếu cơ chế chẩn đoán sự cố tự động (Self-Healing)**: Khi lệnh kiểm thử thất bại hoặc bị văng exception, terminal output bị tràn ngập hàng ngàn dòng log rác, làm trôi context budget của Agent và khiến Agent không thể phân tích chính xác nguyên nhân gốc để tự vá mã nguồn.

---

## Solution

Xây dựng bộ bọc thực thi an toàn **Safe Execution Sandbox Wrapper** (`scripts/run_safe_eval_wrapper.py`) cùng quy trình tự động xuất báo cáo chẩn đoán cấu trúc (`diagnostics.json`):
1. **Cô lập tiến trình & Quản lý thời gian ngầm**: Mọi lệnh runner/eval được thực thi trong một `subprocess` cô lập với Timeout Watchdog cứng (60s/90s) và Singleton Process Lock (`ensure_single_instance()`), đồng thời ép buộc `WaitMsBeforeAsync` $\le 2000$ms để đẩy lệnh xuống Background Task ngay lập tức.
2. **Nhật ký cô lập (Isolated Logging)**: Toàn bộ `stdout` và `stderr` được ghi vào file log riêng tại `.md/scratch/eval_runs/<run_id>.log` để giữ terminal sạch sẽ.
3. **Báo cáo Chẩn đoán Cấu trúc (`diagnostics.json`)**: Khi có sự cố (fail assertion, timeout, exception crash), Wrapper tự động lọc vết lỗi (traceback) và xuất tệp JSON cấu trúc chứa `status`, `error_type`, `failed_gate`, `culprit_file`, và `summary_traceback`.
4. **Vòng lặp Tự sửa lỗi (Self-Healing Loop)**: Cập nhật kỹ năng `/ccba-eval-gate` để Agent tự động đọc `diagnostics.json` khi nhận được thông báo Background Task hoàn tất và tiến hành vá mã nguồn tự động.

---

## User Stories

1. As an AI Agent, I want long-running eval commands to execute asynchronously in a background task, so that my execution turn is never cancelled by IDE client timeouts or network resets.
2. As a Software Engineer, I want long test logs to be saved into isolated `.log` files, so that my terminal output remains clean and readable.
3. As an AI Agent, I want failed test runs to automatically generate a structured `diagnostics.json` report, so that I can immediately pinpoint the exact failing file, line number, and traceback without parsing thousands of un-truncated log lines.
4. As a System Operator, I want repeated runner invocations to automatically terminate obsolete/zombie processes via a Singleton Process Lock, so that CPU and memory resources are not exhausted by duplicate background tasks.
5. As a Project Maintainer, I want the execution wrapper to be implemented using Python standard libraries without adding external third-party dependencies, so that it remains lightweight, fast, and KISS-compliant.

---

## Implementation Decisions

- **Tách biệt Tầng Thực thi (Execution Harness Seam):**
  - Mọi thao tác kiểm thử nâng cao sẽ gọi qua giao diện `scripts/run_safe_eval_wrapper.py`.
  - Wrapper chấp nhận các tham số CLI: `--cmd` (lệnh cần bọc), `--timeout` (thời gian tối đa tính bằng giây), và `--output-dir` (thư mục lưu kết quả).

- **Khóa đơn Tiến trình (Singleton Process Lock):**
  - Tái sử dụng cơ chế `ensure_single_instance()` để thu hồi các PID cũ đang chạy script trùng lặp trước khi khởi tạo tiến trình mới.

- **Cấu trúc Báo cáo Chẩn đoán (`diagnostics.json`):**
  ```json
  {
    "status": "FAILED",
    "error_type": "TIMEOUT" | "ASSERTION_FAILURE" | "SYNTAX_ERROR" | "IMPORT_ERROR" | "UNKNOWN",
    "command": "python scripts/run_harness_evals.py",
    "elapsed_seconds": 90.0,
    "failed_gate": "Gate 3: Pytest Unit Tests",
    "culprit_file": "packages/ccba-harness/tests/test_harness_stress.py",
    "summary_traceback": [
      "AssertionError: Expected 200, got 500",
      "File packages/ccba-harness/tests/test_harness_stress.py, line 42"
    ],
    "log_file": ".md/scratch/eval_runs/run_20260723_092000.log"
  }
  ```

- **Rào chắn Async Context (`AGENTS.md` Alignment):**
  - Quy định trong `eval-gate/SKILL.md` yêu cầu Agent khởi chạy wrapper với `WaitMsBeforeAsync` $\le 2000$ms, lắng nghe sự kiện phản hồi qua Reactive Async Notification của nền tảng.

---

## Testing Decisions

- **Điểm khớp nối kiểm thử (Testing Seams):**
  - Tạo tệp kiểm thử đơn vị `scripts/tests/test_run_safe_eval_wrapper.py`.
  - Không mock các hàm OS cơ bản; sử dụng lệnh python dummy (ví dụ: `python -c "import time; time.sleep(0.1)"` cho PASS và `python -c "import sys; sys.exit(1)"` cho FAILED) để test trực tiếp hành vi thực tế của `subprocess`.

- **Các kịch bản kiểm thử bắt buộc (Mandatory Test Cases):**
  1. `test_wrapper_successful_execution()`: Kiểm tra lệnh chạy thành công, mã thoát 0, xuất `diagnostics.json` với `status = PASS`.
  2. `test_wrapper_timeout_expired()`: Kiểm tra lệnh chạy vượt quá timeout (ví dụ sleep 5s với timeout 1s), bẫy `TIMEOUT` và xuất `diagnostics.json` với `status = TIMEOUT`.
  3. `test_wrapper_failed_command_traceback()`: Kiểm tra lệnh trả về exit code khác 0, bẫy `FAILED` và trích xuất đúng 20-30 dòng traceback cuối cùng vào JSON.

---

## Out of Scope

- Không sửa đổi mã nguồn core binary hoặc GUI Client của Antigravity IDE.
- Không thay đổi các quy tắc viết unit test của pytest trong các package nghiệp vụ.
- Không tích hợp thông báo qua Webhook bên ngoài (Slack, Discord, Telegram) trong phạm vi phiên này.

---

## Further Notes

- Kế thừa trực tiếp cấu trúc từ Wayfinder Map tại [map.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/safe-execution-sandbox/map.md).
- Tuân thủ nghiêm ngặt Hiến pháp CCBA tại [AGENTS.md](file:///d:/GitHubProjects/ccba-agent-platform/.agents/AGENTS.md).
