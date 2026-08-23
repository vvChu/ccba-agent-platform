# Wayfinder Map: Cô lập & Ổn định hóa Hệ thống Kiểm thử (Test Suite Isolation & Stability)

## Điểm đích (Destination)
Cô lập và chuẩn hóa toàn bộ hệ thống kiểm thử (`tests/`, `packages/*/tests`, `scripts/tests`) trên CCBA Agent Platform. Đảm bảo 100% các lượt chạy test (`pytest`, `run_harness_evals.py`, CLI commands) đều diễn ra nhanh chóng (< 15 giây tổng cộng cho suite nhanh), có timeout bảo vệ (tối đa 10 giây/testcase), phân tách rõ ràng giữa Unit Test (fast) và Stress/Adversarial Test (heavy), tuyệt đối không gây treo CPU/memory deadlock khiến server bị ngắt (user canceled / server restart).

---

## Ghi chú (Notes)
- Tuân thủ quy tắc **Scoped Test Execution** trong `AGENTS.md`: Nghiêm cấm chạy unscoped `pytest -q` trên toàn bộ repo mà không chỉ định rõ scope hoặc markers.
- Tuân thủ **Anti-Duplicate Background Runner**: Luôn đảm bảo Singleton process lock trước khi kích hoạt test runners.
- Áp dụng nguyên tắc **KISS**: Sử dụng cấu hình `pyproject.toml` tiêu chuẩn và pytest markers thay vì viết thêm các framework phức tạp.

---

## Quyết định đã chốt (Decisions so far)
- **[Nghiên cứu nguyên nhân gốc lỗi treo test](../../../../pyproject.toml)**: Đã xác định root `pyproject.toml` thiếu cấu hình `[tool.pytest.ini_options]`, chưa có `pytest-timeout`, chưa đăng ký `markers` phân loại (unit/integration/stress), dẫn đến việc `pytest` unscoped vô tình quét và chạy đồng thời các file `test_*stress.py` và `test_*adversarial.py` nặng mà không có rào chắn thời gian.

---

## Biên giới & Ticket Unblocked (Frontier Tickets)

- **[T1: Cấu hình Root Pytest Timeout & Markers Standard](../../../../pyproject.toml) [AFK]**
  - **Mục tiêu**: Bổ sung `[tool.pytest.ini_options]` vào `pyproject.toml` tại root project với `timeout = 10`, đăng ký các markers: `unit`, `integration`, `slow`, `stress`, `adversarial`.
  - **Trạng thái**: Unblocked. Assignee: `@agent`.

- **[T2: Phân loại & Đánh nhãn Pytest Markers cho tệp test nặng](../../../../packages) [AFK]**
  - **Mục tiêu**: Gắn cờ `@pytest.mark.stress` / `@pytest.mark.slow` cho các testsuite nặng (`test_harness_stress.py`, `test_*adversarial*.py`) để mặc định `pytest` bỏ qua các bài test nặng này ngoại trừ khi truyền `-m stress` hoặc `--all-tests`.
  - **Trạng thái**: Unblocked (phụ thuộc T1). Assignee: `@agent`.

- **[T3: Cập nhật run_harness_evals.py với Isolation Mode & Scoped Filtering](../../../../scripts/run_harness_evals.py) [AFK]**
  - **Mục tiêu**: Nâng cấp `run_harness_evals.py` chỉ chạy fast unit tests mặc định (`pytest -m "not stress and not slow"`), đặt timeout tổng thể cho mỗi subprocess, ngăn ngừa treo process.
  - **Trạng thái**: Unblocked (phụ thuộc T1, T2). Assignee: `@agent`.

- **[T4: Tạo Script Helper Kiểm thử Cô lập theo Package (scripts/run_isolated_tests.py)](../../../../scripts/run_isolated_tests.py) [AFK]**
  - **Mục tiêu**: Xây dựng công cụ CLI nhỏ hỗ trợ Agent và Developer chạy kiểm thử cô lập chính xác 1 package hoặc 1 file test với timeout rào chắn, hiển thị summary gọn gàng.
  - **Trạng thái**: Unblocked. Assignee: `@agent`.

---

## Chưa xác định rõ (Not yet specified)
- Tự động hóa đo lường độ phủ coverage chỉ trên fast unit tests trong CI.
- Kiểm tra tính tương thích của `pytest-xdist` nếu cần chạy song song trong tương lai.

---

## Ngoài phạm vi (Out of scope)
- Sửa đổi logic nghiệp vụ bên trong các hàm sản phẩm (trừ khi phát hiện bug lặp vô tận trong code test/mock).
- Thay đổi cấu trúc các package trong `packages/`.
