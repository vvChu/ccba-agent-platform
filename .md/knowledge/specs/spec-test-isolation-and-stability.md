# Spec: Cô lập & Ổn định hóa Hệ thống Kiểm thử (Test Isolation and Stability)

## Problem Statement

Hiện tại khi Kỹ sư AI Agent hoặc Lập trình viên chạy lệnh kiểm thử (`pytest` hoặc `scripts/run_harness_evals.py`) trên repository `ccba-agent-platform`, tiến trình kiểm thử thường xuyên bị treo vô thời hạn, tiêu tốn quá mức tài nguyên CPU/RAM, gây ra lỗi ngắt phiên ("User Canceled") hoặc làm sập/tái khởi động server AI. 

Nguyên nhân chính do:
1. Thiếu rào chắn thời gian toàn cục (`timeout = 10`s per test) tại cấu hình Pytest root (`pyproject.toml`).
2. Không phân loại và tách biệt bài test đơn vị nhanh (Fast Unit Tests) với các bài test tải nặng (`*stress.py`, `*adversarial*.py`).
3. Thiếu cơ chế kiểm soát timeout ở mức subprocess trong các script điều phối test runner.

---

## Solution

Thiết lập hệ thống kiểm thử cô lập đa lớp (Multi-layer Isolated Test Architecture):
1. **Pytest Level Isolation**: Khai báo cấu hình `[tool.pytest.ini_options]` tại `pyproject.toml` root project với timeout mặc định 10 giây/testcase, gán cờ mặc định bỏ qua các bài test nặng (`-m "not stress and not slow"`).
2. **Suite Classification**: Phân loại và gán nhãn Pytest Markers cho 100% các tệp test (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.stress`, `@pytest.mark.adversarial`).
3. **Runner Level Isolation**: Cập nhật `scripts/run_harness_evals.py` chỉ chạy Fast Unit Tests trong luồng mặc định, bổ sung cờ `--stress` khi muốn chạy toàn diện, và thiết lập subprocess timeout tối đa cho các lệnh thực thi con.
4. **Isolated CLI Helper**: Cung cấp công cụ `scripts/run_isolated_tests.py` hỗ trợ chạy test cô lập theo 1 package hoặc 1 file test duy nhất.

---

## User Stories

1. As an AI Agent developer, I want all pytest runs to have a strict 10-second timeout per testcase, so that hanging tests are automatically terminated before causing server cancellation.
2. As a software engineer, I want heavy stress and adversarial tests excluded by default during routine development, so that my local test feedback loop completes within 10-15 seconds.
3. As a CI/CD automation runner, I want a explicit `--stress` CLI flag in `run_harness_evals.py`, so that comprehensive stress testing is only triggered on dedicated evaluation gates.
4. As an AI subagent working on a specific package (e.g. `ccba-ai`), I want to execute isolated tests for only that package, so that I don't waste token context or execution budget scanning unrelated test files.
5. As a developer debugging a failing seam, I want clear test failure summaries without log floods, so that I can quickly pinpoint root causes.

---

## Implementation Decisions

- **Configuration File Centralization**: Mọi quy tắc timeout và default markers cho Pytest được tập trung tại file `pyproject.toml` ở root repository thay vì cài đặt rải rác.
- **Default Marker Expression**: Mặc định Pytest sẽ chạy với biểu thức `-m "not stress and not slow"`. Người dùng hoặc CI có thể mở rộng bằng cách truyền cờ `-m stress` hoặc `--stress`.
- **Subprocess Execution Safety**: Tất cả các script điều phối (`run_harness_evals.py`, `run_isolated_tests.py`) phải bọc lệnh `subprocess.run` bằng tham số `timeout` tối đa (ví dụ `timeout=60`s cho toàn bộ suite), đảm bảo ngắt tiến trình con nếu tiến trình đó bị treo.
- **Seam Alignment**: Khớp nối (seam) được sử dụng để kiểm thử là giao diện `run_command` trong `run_harness_evals.py` và cờ CLI của Pytest.
- **Zero Heavy Network Dependency**: Mọi bài test trong môi trường isolation đều sử dụng Synthetic Data hoặc Mocks, không thực hiện HTTP call trực tiếp tới Server Spark hay Cloud APIs.

---

## Testing Decisions

- **Test Seam**: Seam chính để kiểm thử giải pháp này là việc gọi lệnh CLI `pytest` và `scripts/run_harness_evals.py` trên các gói package độc lập.
- **External Behavior Testing**: Kiểm thử xem lệnh `pytest` có tự ngắt sau đúng 10 giây khi chạy bài test giả lập `time.sleep(15)` hay không.
- **Regression Suite**: Chạy toàn bộ fast unit tests trên 7 packages (`ccba-ai`, `ccba-harness`, `ccba-legal-intel`, `ccba-notebooklm`, `ccba-ooxml`, `ccba-pdf-prep`, `mdconverter`) và xác nhận thời gian hoàn thành dưới 15 giây.

---

## Out of Scope

- Sửa đổi logic nghiệp vụ của các gói tính năng bên trong `packages/` trừ khi phát hiện bug lặp vô tận trong code test.
- Thay đổi cấu trúc thư mục của các package.
- Tích hợp các thư viện kiểm thử song song phức tạp như `pytest-xdist` trong giai đoạn 1.

---

## Further Notes

- Kế hoạch triển khai kỹ thuật chi tiết đã được đăng ký tại [implementation_plan.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/853f878b-db1e-4e7b-9274-0218dfc84c9a/implementation_plan.md).
- Bản đồ Wayfinder tương ứng được lưu tại [.md/knowledge/issues/test_stability/map.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/test_stability/map.md).
