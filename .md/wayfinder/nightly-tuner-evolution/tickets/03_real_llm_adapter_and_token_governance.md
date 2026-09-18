# Ticket 03: Cầu Nối Adapter Real LLM, Token Budget Ceiling & Circuit Breaker

- **Type:** Research / Task (AFK)
- **Status:** closed
- **Assignee:** Antigravity
- **Target Seam:** `packages/ccba-harness/src/ccba_harness/evals/tuner.py`, `packages/ccba-ai/src/ccba_ai/client.py`, `scripts/eval/nightly_tuner_daemon.py`, `scripts/cron/run_nightly_tuner.sh`
- **Reference:** Báo cáo nghiên cứu `/boost` ngày 18/09/2026 (REC-08), ADR 0025, ADR 0055

---

## 🎯 Mục Tiêu
Xây dựng lớp Adapter thống nhất kết nối `GitRatchetOptimizer` với `ccba_ai.client.AIClient`, cho phép Nightly Tuner chuyển dịch từ cơ chế regex mock sang chạy suy luận thực tế (Real LLM Inference) trên Server Spark (:8090) với trần ngân sách token (Token Budget Ceiling) và Circuit Breaker bảo vệ.

---

## 📋 Đặc Tả Kỹ Thuật Chi Tiết
- [x] **Khảo sát & Tích hợp Telemetry:** Xây dựng `TokenUsageTracker` đo lường và tích hợp đo `prompt_tokens`, `completion_tokens`, `total_tokens`, `total_calls`, `avg_latency_s` vào `RatchetTrialResult` và `RatchetReport`.
- [x] **Xây dựng `LLMTaskAdapter` trong `tuner.py`:**
  - Hỗ trợ tham số `use_real_llm: bool`, `llm_model: str` và cờ CLI `--use-real-llm`, `--model`.
  - Kết nối trực tiếp qua `AIClient.chat_with_metadata()` với đầy đủ error handling.
- [x] **Thiết lập Trần Ngân Sách Token (Token Budget Ceiling):**
  - Giới hạn cứng ngân sách toàn phiên (mặc định: 5,000,000 tokens/đêm qua `--token-budget`).
  - Cảnh báo log ngưỡng 90%, tự động ngắt vòng lặp an toàn (Fail-safe Halt: `TokenBudgetExceededError`), hoàn tác rollback về baseline và gắn `halt_reason="TOKEN_BUDGET_EXCEEDED"`.
- [x] **Tích hợp Circuit Breaker Fast-Fail:**
  - Phát hiện và xử lý `CircuitBreakerOpenError`, ngắt optimizer an toàn, hoàn tác candidate mutation, gán `halt_reason="CIRCUIT_BREAKER_OPEN"`.
- [x] **Tích hợp Nightly Tuner Daemon & Cron Runner:**
  - Cập nhật `nightly_tuner_daemon.py` với các tham số CLI `--use-real-llm`, `--token-budget`, `--model`.
  - Cập nhật báo cáo Markdown và cảnh báo Telegram hiển thị tổng lượng token tiêu thụ và engine (`REAL_LLM` vs `MOCK`).
  - Cập nhật `run_nightly_tuner.sh` chuyển tiếp các cờ CLI xuống daemon.

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
1. [x] Thử nghiệm chạy 1 kỹ năng đơn lẻ với `--use-real-llm`: ghi nhận telemetry đo lường token và latency thành công, tổng hợp đúng vào `RatchetReport`.
2. [x] Kiểm tra khi lỗi quota 429 hoặc circuit breaker mở: Circuit breaker kích hoạt dừng tiến trình an toàn, rollback sạch về baseline, không tạo vòng lặp vô tận.
3. [x] Kiểm tra vượt trần ngân sách token: Vòng lặp ngắt ngay lập tức với `TokenBudgetExceededError`, rollback sạch về baseline và ghi nhận `halt_reason`.
4. [x] 100% test suite vượt qua (492 passed), pass `verify-patch --preset code` và `verify-patch --preset eval`.
