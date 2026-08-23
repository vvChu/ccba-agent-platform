# Danh Sách Tickets: System Stability & Auto-Guardrails for Async Tasks

Tài liệu này phân rã kế hoạch và đặc tả [spec-system-stability-auto-guardrails.md](../../specs/spec-system-stability-auto-guardrails.md) thành các ticket phát triển độc lập theo dạng lát cắt dọc (tracer bullets).

👉 **Nguyên tắc**: Chỉ thực hiện các ticket nằm ở **Biên giới (Frontier)** - là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái `[x]` hoàn thành.

---

## Ticket 1: Tích hợp Singleton Process Lock vào run_harness_evals.py

**Nghiệp vụ cần làm**: Khi người dùng hoặc Agent kích hoạt kiểm thử CI Gates, `run_harness_evals.py` sẽ tự động kiểm tra tiến trình hệ thống và triệt hạ bất kỳ tiến trình `run_harness_evals.py` cũ nào đang treo ngầm. Điều này đảm bảo chỉ duy nhất 1 bộ runner chạy tại một thời điểm, loại bỏ tình trạng ngốn 100% CPU.

**Bị chặn bởi**: Không có — có thể bắt đầu ngay.

- [x] Tích hợp hàm `ensure_single_instance()` sử dụng `psutil` / `wmic`.
- [x] Tự động dừng tiến trình cũ trùng PID trước khi chạy linter/mypy/pytest.
- [x] Kiểm thử độc lập bằng cách chạy `.venv\Scripts\python scripts/run_harness_evals.py --no-test`.

---

## Ticket 2: Thu hồi Tiến trình Mồ côi trong session_cleanup.py

**Nghiệp vụ cần làm**: Khi thực hiện dọn dẹp phiên làm việc (`session_cleanup.py`), hệ thống tự động quét các tiến trình `pytest` hoặc `safe_runner` bị treo quá 15 phút do phiên làm việc trước bị ngắt kết nối/crash và tự động triệt hạ để giải phóng RAM.

**Bị chặn bởi**: Không có — có thể bắt đầu ngay.

- [x] Bổ sung import `time` và hoàn thiện logic tính toán thời gian `age_seconds`.
- [x] Thêm thông báo chi tiết khi thu hồi zombie process (`[TERMINATE] Killing orphan process PID ...`).
- [x] Kiểm thử chạy `.venv\Scripts\python scripts/session_cleanup.py --execute`.

---

## Ticket 3: Cưỡng chế Mặc định Scoped Evaluation (Git Diff Check)

**Nghiệp vụ cần làm**: Khi `run_harness_evals.py` chạy mà không có cờ `--all`, nó sẽ tự động trích xuất các file Python/Markdown bị sửa đổi từ `git status` và `git diff` để chạy linter/formatter/pytest tương ứng. Tránh quét toàn bộ codebase ngoại trừ khi được yêu cầu.

**Bị chặn bởi**: Ticket 1

- [x] Cấu hình logic lọc `py_modified` và `md_modified` trong `run_harness_evals.py`.
- [x] Báo cáo chi tiết số lượng file bị ảnh hưởng trước khi chạy từng Gate.

---

## Ticket 4: Tự động hóa Pre-Eval Health Check & Disk Space Guardrail

**Nghiệp vụ cần làm**: Trước khi khởi chạy các bộ test ngầm quy mô lớn, hệ thống sẽ thực hiện kiểm tra nhanh dung lượng đĩa trống (< 2GB sẽ đưa ra cảnh báo) và kiểm tra khả năng truy cập virtualenv để phát hiện sớm các nguy cơ đứt gãy.

**Bị chặn bởi**: Ticket 1, Ticket 2

- [x] Tích hợp kiểm tra dung lượng đĩa trống trong `run_harness_evals.py`.
- [x] Trả về cảnh báo thân thiện và khuyến nghị chạy `session_cleanup.py` nếu dung lượng đĩa khả dụng dưới ngưỡng an toàn.

---

## Ticket 5: Cập nhật Hiến pháp AGENTS.md & Quy Trình Eval Gate Workflow

**Nghiệp vụ cần làm**: Cập nhật chính thức các quy tắc **Bounded Async Task Policy** và rào chắn chống trùng lặp tác vụ ngầm vào [AGENTS.md](../../../../.agents/AGENTS.md) và tài liệu workflow `/ccba-eval-gate`.

**Bị chặn bởi**: Ticket 3, Ticket 4

- [x] Bổ sung mục Bounded Async Task Policy trong `AGENTS.md`.
- [x] Cập nhật hướng dẫn trong workflow `ccba-eval-gate.md`.
