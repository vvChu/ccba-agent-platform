# Ticket 03: Cầu Nối Adapter Real LLM, Token Budget Ceiling & Circuit Breaker

- **Type:** Research / Task (AFK)
- **Status:** open
- **Assignee:** Unassigned
- **Target Seam:** `packages/ccba-harness/src/ccba_harness/evals/tuner.py`, `packages/ccba-ai/src/ccba_ai/eval_runner.py`
- **Reference:** Báo cáo nghiên cứu `/boost` ngày 18/09/2026 (REC-08), ADR 0025, ADR 0055

---

## 🎯 Mục Tiêu
Xây dựng lớp Adapter thống nhất kết nối `GitRatchetOptimizer` với `ccba_ai.client.AIClient`, cho phép Nightly Tuner chuyển dịch từ cơ chế regex mock sang chạy suy luận thực tế (Real LLM Inference) trên Server Spark (:8090) với trần ngân sách token (Token Budget Ceiling) và Circuit Breaker bảo vệ.

---

## 📋 Đặc Tả Kỹ Thuật Chi Tiết
- [ ] **Khảo sát & Tích hợp `EvalRunner`:** Kế thừa bộ khung đo lường benchmark từ `packages/ccba-ai/src/ccba_ai/eval_runner.py` (đã có telemetry đo `prompt_tokens`, `completion_tokens`, `avg_latency_s`).
- [ ] **Xây dựng `LLMTaskAdapter` trong `tuner.py`:**
  - Hỗ trợ tham số `--use-real-llm` hoặc biến môi trường `CCBA_TUNER_ENGINE=REAL_LLM`.
  - Tự động gọi `ai.chat()` với model alias phù hợp (ví dụ `gemini-3.7-flash-high` hoặc `qwen-local-primary`).
- [ ] **Thiết lập Trần Ngân Sách Token (Token Budget Ceiling):**
  - Giới hạn cứng ngân sách toàn phiên (ví dụ: tối đa 5,000,000 tokens/đêm).
  - Tự động ngắt vòng lặp (Fail-safe Halt) và gửi cảnh báo Telegram khi chạm ngưỡng 90% budget.
- [ ] **Tích hợp Circuit Breaker:** Kế thừa từ `ccba-api-circuit-breaker` để dừng gọi API khi phát hiện 3 lần lỗi HTTP 429 / 503 liên tiếp.

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
1. Thử nghiệm chạy 1 kỹ năng đơn lẻ với `--use-real-llm --max-iter 1`: ghi nhận telemetry đo lường token và latency thành công.
2. Kiểm tra khi mock lỗi quota 429: Circuit breaker kích hoạt dừng tiến trình an toàn, không tạo vòng lặp vô tận.
