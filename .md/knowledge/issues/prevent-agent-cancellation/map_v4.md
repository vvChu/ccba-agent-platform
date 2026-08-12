# Bản đồ Định hướng Wayfinder: Quy trình Vận hành Chuẩn (SOP) Thực thi Slow Test Suite [COMPLETED]

> **Mã Bản đồ:** `WAYFINDER-004`  
> **Trạng thái:** Completed  
> **Ngày khởi tạo:** 2026-08-12  
> **Ngày hoàn thành:** 2026-08-12  

---

## 🎯 1. Điểm đích (Destination)

Chuẩn hóa **Quy trình Vận hành Chuẩn (Standard Operating Procedure - SOP)** và tích hợp rào chắn an toàn tự động cho việc thực thi các bài kiểm thử nặng (`@pytest.mark.slow`), đảm bảo 100% không rò rỉ tiến trình, không gây gián đoạn phiên làm việc và không bị hỏng ngầm (test decay).

---

## 📝 2. Ghi chú & Rào chắn Hạ tầng (Notes & Guardrails)

- **Tuân thủ Hiến pháp `AGENTS.md` §4:**
  - Fast Suite hàng ngày luôn lọc qua cờ `-m "not slow"` (chạy hoàn tất trong **4.09s**).
  - Mọi tệp test chạy > 2.0s phải được gắn decorator `@pytest.mark.slow` (giám sát tự động bởi `scripts/hooks/test_speed_guard.py`).
  - Mọi lệnh chạy slow test đều phải dùng runner bọc cô lập (`safe_pytest.py` hoặc `run_safe_eval_wrapper.py`).

---

## ✅ 3. Quyết định đã chốt (Decisions so far)

### 📌 Kịch bản 1: Chạy 1 tệp Slow Test đơn lẻ
- **Lệnh thực thi:**
  ```powershell
  python scripts/safe_pytest.py -f packages/ccba-legal-intel/tests/test_crawler_adversarial.py
  ```
- **Cơ chế an toàn:** `safe_pytest.py` tự động kích hoạt [`safe_runner.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/safe_runner.py#L90) chứa cờ `DETACHED_PROCESS`, tách 100% tiến trình con khỏi Agent Host.

### 📌 Kịch bản 2: Chạy Toàn bộ Slow Test Suite của 1 Package
- **Lệnh thực thi:**
  ```powershell
  python scripts/eval/run_safe_eval_wrapper.py --cmd "python scripts/eval/run_isolated_tests.py -p ccba-legal-intel --stress" --timeout 180
  ```
- **Cơ chế an toàn:** [`run_safe_eval_wrapper.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/eval/run_safe_eval_wrapper.py#L46) kích hoạt **Non-blocking Thread + Queue I/O** và **Live Heartbeat `⏱️ [HEARTBEAT]` mỗi 10 giây**, ghi log trực tiếp theo từng dòng.

### 📌 Kịch bản 3: Tự động hóa Tối đa trên CI / Workflow
- **Nightly CI Build:** Tệp [`.github/workflows/nightly-slow-tests.yml`](file:///d:/GitHubProjects/ccba-agent-platform/.github/workflows/nightly-slow-tests.yml) tự động kích hoạt `--stress` vào 2:00 AM UTC (9:00 AM ICT) hàng ngày.
- **Pre-release Gate:** Workflow [`/ccba-release-feature`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-release-feature.md#L12) cưỡng chế chạy full slow tests tại Bước 0 trước khi cho phép merge PR.

---

## 🚧 4. Ticket ở Biên giới (Frontier - Unblocked Tickets)

*(Tất cả các ticket thuộc SOP Slow Test Execution đã được hoàn thành và đóng băng 100%)*

---

## 🚫 5. Ngoài phạm vi (Out of scope)

- **Over-mocking vô ích:** Không biến các bài test tích hợp cào mạng thực tế thành purely fake in-memory mocks.
