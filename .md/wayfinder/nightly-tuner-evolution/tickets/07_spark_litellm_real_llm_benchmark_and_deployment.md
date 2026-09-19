# Ticket 07: Khảo Sát & Đánh Giá Cấu Hình Real LLM trên Máy Chủ Spark (:8090) Cho Nightly Tuner

- **Type:** Research (AFK / Architectural Investigation)
- **Status:** in_progress
- **Assignee:** Antigravity AI Agent (delegated to subagent `research`)
- **Target Seam:** `packages/ccba-ai/src/ccba_ai/`, `.agents/skills/ccba-ai-gateway-sdk/SKILL.md`
- **Reference:** ADR-0023, Ticket 03 Nightly Tuner Evolution

---

## 🎯 Mục Tiêu
Khảo sát và xác định mô hình tối ưu trên LiteLLM Server Spark (:8090, qua Tailscale VPN `100.83.192.30`) để chạy đợt tuning ban đêm với Real LLM (`--use-real-llm`), bao gồm:
1. Danh mục 22 mô hình khả dụng trên Spark (:8090) và phân loại theo tier (Local GPU vs Cloud fallback).
2. Đo lường tốc độ suy luận (latency), chi phí token, và giới hạn quota/concurrency khi chạy batch 73 kỹ năng.
3. Xác lập bộ tham số mặc định cho `scripts/cron/run_nightly_tuner.sh`: `--model`, `--token-budget`, timeout per call, circuit breaker threshold.

---

## 📋 Câu Hỏi Cốt Lõi Cần Trả Lời
1. Mô hình nào đạt điểm cân bằng tốt nhất giữa năng lực phân tích prompt ngữ nghĩa tiếng Việt kỹ thuật và tốc độ (tokens/s)?
2. LiteLLM gateway có hỗ trợ streaming token usage metadata trong response không?
3. Khi LiteLLM gặp rate-limit 429 hoặc 503, `CircuitBreakerOpenError` trong `ccba-ai` và `tuner.py` hoạt động thế nào để dừng an toàn mà không làm hỏng dữ liệu worktree?

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [ ] 1. Báo cáo nghiên cứu hoàn chỉnh lưu tại `.md/knowledge/reports/spark_litellm_nightly_tuner_evaluation.md`.
- [ ] 2. Đề xuất cấu hình biến môi trường chuẩn trong `.env` của server Spark.
