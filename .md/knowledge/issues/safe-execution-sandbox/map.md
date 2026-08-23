# 🗺️ Wayfinding Map: Safe Execution Sandbox & Self-Healing Loop

> **Trạng thái:** COMPLETED  
> **Mã tính năng:** `safe-execution-sandbox`  
> **Ngày hoàn thành:** 2026-07-23  

---

## 🎯 1. Điểm đích (Destination)

Thiết lập bộ bọc thực thi an toàn **Safe Execution Sandbox Wrapper** (`scripts/run_safe_eval_wrapper.py`) cùng quy trình tự động bẫy lỗi và chẩn đoán cấu trúc (`diagnostics.json`). Đảm bảo mọi tác vụ kiểm thử (Pytest, Ruff, Mypy, Eval Gates) và tiến trình runner chạy dài hạn:
- **Không bao giờ làm treo/hủy lượt Agent** (Triệt tiêu 100% lỗi `User cancelled agent execution`).
- **Tự động cô lập & phân tích lỗi:** Mọi sự cố (crash, timeout, memory leak, fail assertion) được bẫy riêng và xuất báo cáo `diagnostics.json` hỗ trợ vòng lặp Self-Healing.
- **Tuân thủ rào chắn Hiến pháp CCBA (`AGENTS.md`):** Tích hợp Singleton Process Lock (`ensure_single_instance()`), Reactive Async Notification, và Timeout Guardrails.

---

## 📝 2. Ghi chú (Notes)

- Nạp các kỹ năng liên quan: [api-circuit-breaker](../../../../.agents/skills/api-circuit-breaker/SKILL.md), [append-only-logger](../../../../.agents/skills/append-only-logger/SKILL.md), [eval-gate](../../../../.agents/skills/eval-gate/SKILL.md), [code-review](../../../../.agents/skills/code-review/SKILL.md).
- Ưu tiên nguyên tắc **KISS (Keep It Simple, Stupid)**: Wrapper là một script Python độc lập, đơn giản (~150-200 dòng), không tạo ra các lớp trừu tượng phức tạp không cần thiết.

---

## 📌 3. Quyết định đã chốt (Decisions so far)

1. **[Rút ngắn Blocking Wait khi gọi `run_command`](file:///C:/Users/chuvu/.gemini/antigravity/brain/853f878b-db1e-4e7b-9274-0218dfc84c9a/.system_generated/logs/transcript.jsonl)**: Quy định `WaitMsBeforeAsync` luôn $\le 2000$ms đối với các lệnh runner/eval dài hạn để chuyển ngay thành Background Task, tránh block IDE Client.
2. **[Tách biệt Log Output khỏi Terminal Stream](../../../../scripts/run_isolated_tests.py)**: Toàn bộ log của bài test/eval ngầm được ghi vào file `.md/scratch/eval_runs/<run_id>.log` để giữ terminal sạch sẽ và tránh đứt kết nối stream.

---

## 🚀 4. Danh sách các Ticket Biên Giới (Frontier Tickets)

* **[Ticket 1: Thiết kế & Triển khai `scripts/run_safe_eval_wrapper.py`](../../../../scripts/run_safe_eval_wrapper.py)** `[AFK/Task]`
  - *Mục tiêu:* Viết script wrapper chính bọc các lệnh terminal với Singleton Lock (`ensure_single_instance()`), Timeout Watchdog (mặc định 60s/gate), và bẫy ngoại lệ `subprocess`.
  - *Đầu ra:* File `scripts/run_safe_eval_wrapper.py`.

* **[Ticket 2: Chuẩn hóa Định dạng Báo cáo Chẩn đoán Cấu trúc (`diagnostics.json`)](../../../scratch/eval_runs/diagnostics.json)** `[AFK/Task]`
  - *Mục tiêu:* Định nghĩa cấu trúc JSON báo cáo chẩn đoán lỗi cô đọng (`status`, `error_type`, `failed_gate`, `culprit_file`, `summary_traceback`).
  - *Đầu ra:* Module trích xuất vết lỗi tự động trong `run_safe_eval_wrapper.py`.

* **[Ticket 3: Tích hợp Self-Healing Feedback Protocol cho Agent](../../../../.agents/skills/eval-gate/SKILL.md)** `[HITL/Research]`
  - *Mục tiêu:* Thiết lập hướng dẫn/workflow để Agent khi nhận tin nhắn hoàn tất từ Background Task sẽ tự động đọc `diagnostics.json` và đưa ra bản vá mã nguồn tự động mà không cần chờ người dùng nhắc nhở.
  - *Đầu ra:* Cập nhật workflow `/ccba-eval-gate` và `eval-gate/SKILL.md`.

---

## 🌫️ 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- **Tùy biến Timeout linh hoạt theo từng Package:** Việc một số package quá lớn cần timeout riêng (ví dụ 120s thay vì 60s) sẽ được quyết định sau khi đo đạc thực tế tại Ticket 1.
- **Tích hợp Slack/Discord Notification:** Gửi cảnh báo sự cố nếu runner thất bại trên CI server.

---

## 🚫 6. Ngoài phạm vi (Out of scope)

- **Thay đổi Core Architecture của IDE/Antigravity Platform:** Chỉ can thiệp ở tầng Script/Sandbox Harness của dự án, không sửa đổi source code của Antigravity IDE.
- **Sửa tất cả các Unit Tests đang hỏng của dự án khác:** Việc sửa lỗi logic của từng unit test cụ thể nằm ở các ticket tính năng tương ứng.
