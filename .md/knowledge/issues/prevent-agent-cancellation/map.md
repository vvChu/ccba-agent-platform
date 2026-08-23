# Bản đồ Định hướng Wayfinder: Bảo vệ Tuyệt đối Agent khỏi Lỗi Cancelled Execution [COMPLETED]

> **Mã Bản đồ:** `WAYFINDER-002`  
> **Trạng thái:** Completed  
> **Ngày khởi tạo:** 2026-08-12  
> **Ngày hoàn thành:** 2026-08-12  

---

## 🎯 1. Điểm đích (Destination)

Xây dựng cơ chế rào chắn sinh tồn tuyệt đối cho CCBA Agent Platform, đảm bảo 100% các lệnh runner, pytest suite, background tasks và long-running scripts **không bao giờ vượt quá ngưỡng timeout** hoặc **bị hiểu nhầm là đơ/treo**, triệt hạ vĩnh viễn nguy cơ gây ra lỗi `User cancelled agent execution` trên AI Client Host.

---

## 📝 2. Ghi chú (Notes)

- **Tuân thủ Hiến pháp `AGENTS.md` §4:**
  - Nghiêm cấm unscoped `pytest` toàn repository.
  - Bắt buộc Single-Instance Lock via `process_safety.py`.
  - Luôn duy trì unbuffered logging (`line_buffering=True`).
- **Triết lý:** Không ép hệ thống chạy nhanh hơn khả năng thực tế của phần cứng, mà **quản lý thời gian và tiến trình thông minh** để luôn duy trì tương tác sinh tồn với Agent Host.

---

## ✅ 3. Quyết định đã chốt (Decisions so far)

1. **[Tối ưu Mutex Timeout lên 0.3s](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/tests/test_crawler_upgrades.py#L24)**
   - *Tóm tắt:* Đã hạ timeout trong unit test từ 1.0s xuống 0.3s, cắt giảm thời gian chạy test suite từ > 80s xuống **9.41s** (Fast suite 4.09s), loại bỏ Flaky Test trên CI.
2. **[Bật Unbuffered Logging tập trung](file:///d:/GitHubProjects/ccba-agent-platform/scripts/eval/process_safety.py#L22)**
   - *Tóm tắt:* Đã đưa `sys.stdout.reconfigure(line_buffering=True)` vào `process_safety.py` để mọi background script tự động đẩy log trực tiếp xuống đĩa ngay lập tức.
3. **[Phân tầng `@pytest.mark.slow`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/tests/test_crawler_upgrades.py#L270)**
   - *Tóm tắt:* Đã gắn tag `slow` cho các test cào mạng nặng, giúp cờ `-m "not slow"` tự động lọc bỏ 19 bài test nặng khỏi lượt chạy nhanh hàng ngày.
4. **[Ticket 1: Live Heartbeat Logging](file:///d:/GitHubProjects/ccba-agent-platform/scripts/eval/run_safe_eval_wrapper.py#L77)**
   - *Tóm tắt:* Đã nâng cấp `run_safe_eval_wrapper.py` tự động ghi log dòng theo dòng và phát heartbeat `⏱️ [HEARTBEAT]` mỗi 10 giây.
5. **[Ticket 2: Tập trung Unbuffered I/O vào `process_safety.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/eval/process_safety.py#L22)**
   - *Tóm tắt:* Đã đưa cấu hình `line_buffering=True` vào hàm `ensure_single_instance()` dùng chung cho toàn bộ scripts.
6. **[Ticket 3: Tự động cờ an toàn trong `safe_pytest.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/safe_pytest.py#L80)**
   - *Tóm tắt:* Đã tự động chèn cờ `--maxfail=1` và `-m "not slow"` vào CLI bridge `safe_pytest.py` (chạy test 2.46s).
7. **[Ticket 4: Linter `test_speed_guard.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/hooks/test_speed_guard.py)**
   - *Tóm tắt:* Đã giải mã mục Sương mù chiến trận thành công, tạo script `scripts/hooks/test_speed_guard.py` tự động phát hiện và cảnh báo các file test chạy > 2.0s mà thiếu tag `@pytest.mark.slow`.

---

## 🚧 4. Ticket ở Biên giới (Frontier - Unblocked Tickets)

*(Tất cả 4 ticket đã hoàn thành 100%)*

---

## 🌫️ 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

*(Mục sương mù chiến trận duy nhất đã được giải mã và chuyển thành Ticket 4 hoàn tất)*

---

## 🚫 6. Ngoài phạm vi (Out of scope)

- **Tăng cứng phần cứng hoặc thay đổi Agent Server Host:** Không sửa đổi timeout cấu hình trên Agent Server Host; chỉ giải quyết triệt me từ phía codebase và runner infrastructure.
