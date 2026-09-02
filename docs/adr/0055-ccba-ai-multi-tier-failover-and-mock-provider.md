# 0055. CCBA AI Multi-Tier Failover Matrix, Antigravity CLI Bridge, Local Ollama & Offline Mock Provider

* **Status:** Accepted
* **Date:** 2026-09-02
* **Updated:** 2026-09-02 (v2 — Added Tier 3 Antigravity CLI Bridge)
* **Deciders:** CCBA Platform Core Team
* **Consulted:** ADR 0029 (AI Gateway Contract), ADR 0044 (Shared SDKs), Issue #229

---

## Context & Problem Statement

Thư viện cốt lõi `ccba-ai` (`packages/ccba-ai`) đóng vai trò là client thống nhất kết nối toàn bộ hệ thống Hub-Spoke với LiteLLM AI Gateway trên Server Spark (`100.83.192.30:8090/v1`).
Tuy nhiên, môi trường vận hành bộc lộ các thách thức sau:
1. **Rớt mạng Tailscale VPN / Bảo trì Server Spark:** Khi Server Spark khởi động lại hoặc mạng VPN bị gián đoạn, các lệnh gọi `ai.chat()` rơi vào vòng lặp retry và gây crash timeout (`APIConnectionError`), làm tê liệt các pipeline tự động (TVPL crawler, PCCC audit, OKF parser).
2. **Nhu cầu làm việc Ngoại tuyến (Air-gapped / Offline):** Kỹ sư làm việc tại công trường hoặc trên máy bay không có kết nối internet/VPN nhưng vẫn cần khả năng xử lý LLM cơ bản qua mô hình cục bộ (Local LLM).
3. **Kiểm thử tự động & CI độc lập (No-Network CI):** Quá trình chạy Unit Tests trong môi trường CI cách ly cần một Deterministic Mock Provider in-memory với độ trễ <1ms mà không phụ thuộc vào kết nối mạng bên ngoài.
4. **Zero-Config Fallback (v2):** Developer workstation thường cài sẵn Antigravity CLI (`agy`) — cần tận dụng binary này làm fallback không cần cấu hình thêm, dù chấp nhận latency cao (~30-40s/call).

---

## Decision Outcome

Quyết định triển khai **Multi-Tier Failover Matrix** (5 tầng) trực tiếp trong `packages/ccba-ai`:

### 1. Ma trận 5 Tầng Chuyển vùng Dự phòng (Tiered Fallback Router)
- **Tier 1 (Default - Central Gateway):** LiteLLM Proxy trên Server Spark (`http://100.83.192.30:8090/v1`) theo chuẩn 4 Model Archetypes (ADR 0029).
- **Tier 2 (Cloud Direct Fallback):** Tự động phát hiện các API keys độc lập trong môi trường:
  - Google Gemini API (`GEMINI_API_KEY`) → endpoint Google AI Studio / Vertex AI.
  - Groq API (`GROQ_API_KEY`) → endpoint `api.groq.com/openai/v1`.
  - OpenAI API (`OPENAI_API_KEY`) → endpoint `api.openai.com/v1`.
- **Tier 3 (Antigravity CLI Bridge):** Zero-config fallback qua `agy -p` subprocess. Tự phát hiện binary `agy` trên PATH via `shutil.which`. Sử dụng `--output-format stream-json` + NDJSON parsing. Hỗ trợ multi-model (Gemini 3.7 Flash, Claude Sonnet 4.6, GPT-OSS). **Trade-off: ~30-40s latency/call** [đo thực tế] do agent context loading (~26K input tokens). Chỉ dùng cho interactive fallback trên developer workstation.
- **Tier 4 (Local Offline LLM):** Tự động phát hiện Ollama daemon cục bộ (`http://127.0.0.1:11434/v1`) ánh xạ sang các mô hình nhẹ (`qwen2.5-coder:7b`, `phi-4-mini`).
- **Tier 5 (Deterministic Mock Provider):** Giả lập in-memory không qua mạng, kích hoạt khi bật biến môi trường `CCBA_AI_MOCK=1` hoặc cấu hình `mock_mode=True`.

### 2. Tích hợp Circuit Breaker & Graceful Degradation
- Khi Tier 1 văng lỗi mạng hoặc Circuit Breaker chuyển sang trạng thái `OPEN`, router tự động chuyển vùng tuần tự Tier 2 → Tier 3 → Tier 4 → Tier 5 kèm log cảnh báo có cấu trúc.
- Khi chuyển vùng thành công, Circuit Breaker tự động ghi nhận phục hồi và không làm gián đoạn luồng xử lý của ứng dụng.

### 3. Khả năng Mock Deterministic & Quản lý Pattern
- `MockProvider` hỗ trợ cả Sync (`OpenAI`) và Async (`AsyncOpenAI`), tự động sinh phản hồi JSON hợp lệ khi prompt yêu cầu format JSON, và cho phép đăng ký bảng mẫu phản hồi (`register_pattern`).

---

## Consequences

### Positive
- **99.99% Uptime Resilience:** Loại bỏ hoàn toàn điểm nghẽn đơn lẻ (Single Point of Failure) của Server Spark.
- **Zero-Config Tier 3:** Antigravity CLI tự động phát hiện — không cần cấu hình API key hay endpoint thêm.
- **100% Offline Capable:** Chạy mượt mà offline với Local Ollama hoặc Mock Provider.
- **Zero-Network CI Tests:** 100% test suites có thể chạy độc lập trong môi trường cô lập không có Internet.
- **Zero-Extra Dependencies:** Tận dụng 100% chuẩn OpenAI-compatible interface, không phát sinh thêm thư viện bên ngoài.

### Negative / Trade-offs
- Cần tải sẵn model trong Ollama (`ollama pull qwen2.5-coder:7b`) nếu muốn sử dụng Tier 4 khi mất mạng hoàn toàn.
- Tier 3 (Antigravity CLI) có latency ~30-40s/call [đo thực tế] — KHÔNG phù hợp cho batch pipeline (>10 calls). Chỉ dùng cho interactive fallback.
- `max_tokens` và `temperature` parameters bị lossy khi đi qua Tier 3 (agy -p không hỗ trợ).
