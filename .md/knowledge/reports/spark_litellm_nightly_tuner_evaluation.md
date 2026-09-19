# 📋 Báo Cáo Khảo Sát & Đánh Giá Cấu Hình Real LLM Trên Server Spark (:8090) Cho Nightly Auto-Tuner

- **Tác giả:** Antigravity AI Agent & Research Subagent
- **Ngày lập:** 2026-09-19
- **Căn cứ tài liệu:** `.agents/skills/ccba-ai-gateway-sdk/SKILL.md`, `packages/ccba-ai/src/ccba_ai/`, `packages/ccba-harness/src/ccba_harness/evals/tuner.py`, `.md/knowledge/reports/qwen_evaluation_report.md`
- **Trạng thái:** Hoàn thành (Nghiệm thu Wayfinder Ticket 07)

---

## 1. Danh Mục Mô Hình Khả Dụng & Phân Phối Tải Trên Spark Gateway (:8090)

Hệ thống AI Gateway LiteLLM trên Server Spark (`100.83.192.30:8090/v1`) phân loại theo các Archetypes chuyên biệt:

### 1.1. Nhóm Mô hình Local GPU (vLLM trên Server Spark DGX) — ⭐ KHUYẾN NGHỊ MẶC ĐỊNH
- **`qwen-local-primary`** (backend `Qwen/Qwen2.5-35B-Instruct-FP8` trên vLLM):
  - **Latency / TTFT:** TTFT `~0.114s` `[đo thực tế]`, tổng thời gian phản hồi 2–4s.
  - **Throughput:** `~45.24 tokens/s` `[đo thực tế]` (khi có cache Redis trả lời lặp lại: `~0.01s`).
  - **Chi phí & Quota:** **Zero-Cost ($0)**, không giới hạn request/token (Unlimited), không lo bị 429 hay ngắt quota đám mây khi chạy batch thâu đêm.
  - **Năng lực Tiếng Việt & System Prompt:** Natively Chain-of-Thought (`<think>`), tuân thủ nghiêm ngặt các ràng buộc formatting và ngữ cảnh chuyên ngành xây dựng Việt Nam.

### 1.2. Nhóm Mô hình Cloud Tốc Độ Cao & Tiết Kiệm (Speed Tier)
- **`gemini-3.7-flash`** (hoặc `gemini-3.7-flash-medium`):
  - **Latency:** `~0.96s – 1.35s` `[đo thực tế]`.
  - **Throughput:** Rất cao (~80–120 tokens/s qua Google Cloud API).
  - **Chi phí & Quota:** Cực rẻ, pool 10 API keys. Phù hợp làm baseline đối chiếu hoặc chạy A/B testing nhanh.

### 1.3. Nhóm Mô hình Cloud Deep Reasoning
- **`gemini-3.7-flash-high`** (hoặc `claude-sonnet-4-6-thinking`):
  - **Latency:** `7s – 13s/call` `[đo thực tế]`.
  - **Throughput:** Sinh CoT lớn, tự động cấp phát `max_tokens=16,384`.
  - **Đánh giá cho Nightly Tuner:** Chỉ nên dùng khi tinh chỉnh các kỹ năng audit pháp lý cực khó (Hard Floor / Red Team). Không nên dùng đại trà cho 73 skills vì thời gian chạy sẽ vượt quá 6 tiếng.

---

## 2. Thiết Lập Biến Môi Trường & Cơ Chế Vận Hành `AIClient`

### 2.1. Thiết lập Biến Môi Trường Chuẩn trong `.env`
```env
# Endpoint LiteLLM trên Server Spark qua Tailscale VPN
AI_GATEWAY_URL=http://100.83.192.30:8090/v1

# Key xác thực AI Gateway (Khai báo cả 2 để tương thích SDK và môi trường)
AI_GATEWAY_KEY=sk-spark-secure-key-2026
AI_GATEWAY_API_KEY=sk-spark-secure-key-2026

# Model dùng cho Nightly Auto-Tuner
CCBA_TUNER_MODEL=qwen-local-primary

# Trần ngân sách token bảo vệ phiên và timeout kết nối
CCBA_TUNER_TOKEN_BUDGET=5000000
AI_GATEWAY_TIMEOUT=60.0
CCBA_TUNER_ENGINE=REAL_LLM
```

> **Lưu ý Mã Nguồn (`client.py:154-157`):**  
> `AIClient` ưu tiên đọc `AI_GATEWAY_KEY`. Bắt buộc phải khai báo biến này để tránh client fallback về `"mock-key-for-ci"`.

### 2.2. Cơ Chế Vi Đo Lường & Ngắt An Toàn (Telemetry & Circuit Breaker)
1. **Vi đo lường Token Usage (`client.py:239-346`, `models.py:6-23`):**
   - `ai.chat_with_metadata()` trích xuất chính xác `prompt_tokens`, `completion_tokens`, `total_tokens` từ `response.usage`.
   - `LLMTaskAdapter` trong `tuner.py` truyền dữ liệu sang `TokenUsageTracker`. Nếu tổng token vượt trần 5,000,000, hệ thống dừng an toàn với `TokenBudgetExceededError`.
2. **Circuit Breaker Fast-Fail (`circuit_breaker.py:16-134`):**
   - Khi gặp 3 lỗi liên tiếp (timeout, 500, lỗi mạng VPN), Circuit Breaker chuyển sang trạng thái `OPEN` và ném `CircuitBreakerOpenError`.
   - `nightly_tuner_daemon.py` bắt biệt lệ này, ngắt tiến trình kịp thời (`halt_reason = "CIRCUIT_BREAKER_OPEN"`), tự động dọn dẹp worktree và gửi thông báo Telegram, không làm treo máy chủ.

---

## 3. Khuyến Nghị Cấu Hình Mặc Định Cho Cron Job Nightly Tuner

| Tham số | Giá trị Khuyến nghị | Cơ sở & Lý do |
| :--- | :--- | :--- |
| **Model chính (`--model`)** | `qwen-local-primary` | Local GPU DGX, $0 chi phí, không giới hạn rate-limit, tốc độ ~45 t/s. |
| **Model fallback (A/B Test)** | `gemini-3.7-flash` | Cloud tốc độ cao (<1s), chi phí tối thiểu (~$1.5/đêm), dùng đối soát. |
| **Trần Token (`--token-budget`)**| `5,000,000` tokens | Hard floor an toàn trong `TokenUsageTracker`. Cảnh báo tại 90% (4.5M) và dừng sạch tại 5M. |
| **Số vòng lặp (`--max-iter`)** | `10` (mặc định) | 73 skills x 10 iter = tối đa 730 trials. Đủ tìm ra prompt đột biến mà không vượt ngưỡng 6 tiếng. |
| **Early Stopping (`patience`)**| `3` | Nếu sau 3 lần đột biến liên tiếp không tăng điểm, dừng chuyển sang skill tiếp theo. |
| **Timeout per request** | `60.0s` | Đảm bảo đủ thời gian cho LiteLLM fallback nội bộ mà không bị client timeout sớm. |
| **Circuit Breaker** | `threshold=3`, `cooldown=30s` | Fast-fail bảo vệ batch daemon không bị treo vĩnh viễn khi mạng VPN gặp sự cố. |

### Lệnh thực thi trong cron runner (`scripts/cron/run_nightly_tuner.sh`):
```bash
python3 scripts/eval/nightly_tuner_daemon.py \
  --use-real-llm \
  --model qwen-local-primary \
  --max-iter 10 \
  --token-budget 5000000
```
