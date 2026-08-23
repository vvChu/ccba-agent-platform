# Danh sách Tickets: Cô lập & Ổn định hóa Hệ thống Kiểm thử (Test Isolation & Stability)

Tài liệu spec tham chiếu: [Spec: Cô lập & Ổn định hóa Hệ thống Kiểm thử](../../specs/spec-test-isolation-and-stability.md)  
Bản đồ Wayfinder: [Wayfinder Map](map.md)

👉 **Nguyên tắc**: Chỉ thực hiện các ticket nằm ở **Biên giới (Frontier)** — là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái `[x]` hoàn thành.

---

## Ticket 1: Cấu hình Pytest Timeout & Fast Marker Selection tại pyproject.toml

**Nghiệp vụ cần làm:**  
Khai báo cấu hình `[tool.pytest.ini_options]` tại file `pyproject.toml` ở root project. Thiết lập cờ `timeout = 10` (tối đa 10 giây/testcase), đăng ký các nhãn (`unit`, `integration`, `slow`, `stress`, `adversarial`), và cấu hình default filter `-m "not stress and not slow"`. Đảm bảo mọi lượt gọi `pytest` trực tiếp hay gián tiếp đều lập tự động ngắt nếu có testcase bị treo.

**Bị chặn bởi:** Không có — có thể bắt đầu ngay. (Frontier)

**Tiêu chí nghiệm thu:**
- [ ] Pytest ở root nhận diện được cấu hình `[tool.pytest.ini_options]`.
- [ ] Chạy bài test quá 10 giây bị pytest ngắt và báo lỗi timeout thay vì treo vô thời hạn.
- [ ] Mặc định `pytest` bỏ qua các testcase có gắn nhãn `@pytest.mark.stress` hoặc `@pytest.mark.slow`.

---

## Ticket 2: Đánh nhãn Pytest Markers cho các tệp test nặng (Stress & Adversarial Suites)

**Nghiệp vụ cần làm:**  
Phân loại và bổ sung decorator `@pytest.mark.stress` / `@pytest.mark.slow` / `@pytest.mark.adversarial` cho các tệp test nặng trong codebase (đặc biệt là các tệp `test_harness_stress.py`, `test_*adversarial*.py` tại `packages/ccba-harness/tests`, `packages/ccba-legal-intel/tests`, và `scripts/tests`).

**Bị chặn bởi:** Ticket 1 (`Cấu hình Pytest Timeout & Fast Marker Selection tại pyproject.toml`).

**Tiêu chí nghiệm thu:**
- [ ] 100% các file test tải nặng hoặc test đối kháng (adversarial) được gắn nhãn tương ứng.
- [ ] Chạy `pytest` bình thường chỉ thực thi Fast Unit Tests (tổng thời gian < 15 giây).
- [ ] Chạy `pytest -m stress` thực thi đúng các test suite tải nặng.

---

## Ticket 3: Tối ưu hóa script run_harness_evals.py với Isolation Controls & Subprocess Timeout

**Nghiệp vụ cần làm:**  
Cập nhật `scripts/run_harness_evals.py` để mặc định chỉ kích hoạt Fast Unit Tests. Bổ sung tham số CLI `--stress` cho phép chạy toàn bộ stress tests khi cần thiết. Bọc tất cả các lệnh gọi subprocess bằng cờ `timeout` ở cấp runner để đảm bảo không một cổng CI Gate nào có thể làm đơ/treo hệ thống.

**Bị chặn bởi:** Ticket 1 và Ticket 2.

**Tiêu chí nghiệm thu:**
- [ ] Lệnh `python scripts/run_harness_evals.py` chạy mặc định chỉ thực thi Fast Unit Tests và hoàn thành trong thời gian ngắn.
- [ ] Lệnh `python scripts/run_harness_evals.py --stress` chạy đầy đủ các bài stress test khi được yêu cầu.
- [ ] Subprocess runner tự ngắt an toàn nếu một cổng kiểm tra bị đơ/treo.

---

## Ticket 4: Xây dựng CLI Helper kiểm thử cô lập theo Package (scripts/run_isolated_tests.py)

**Nghiệp vụ cần làm:**  
Tạo script CLI nhỏ `scripts/run_isolated_tests.py` hỗ trợ Kỹ sư và AI Subagent chạy kiểm thử cô lập chính xác 1 package (ví dụ `python scripts/run_isolated_tests.py --package ccba-ai`) hoặc 1 file test cụ thể, tự động áp dụng timeout rào chắn và in báo cáo kết quả súc tích.

**Bị chặn bởi:** Ticket 1. (Frontier)

**Tiêu chí nghiệm thu:**
- [ ] Chạy `python scripts/run_isolated_tests.py --package <name>` thực thi cô lập bài test của đúng package đó.
- [ ] Báo cáo kết quả gọn gàng, hiển thị rõ thời gian chạy và số testcase pass/fail.
