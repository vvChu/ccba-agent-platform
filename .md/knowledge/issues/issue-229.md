---
id: 229
title: "feat(ccba-ai): multi-model failover matrix, local ollama & offline mock provider"
state: "closed"
labels:
  - "enhancement"
  - "completed"
assignee: "vvChu"
created_at: "2026-09-02T06:27:35Z"
updated_at: "2026-09-02T11:03:37Z"
closed_at: "2026-09-02T11:03:37Z"
merged_pr: 234
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
- `ccba-ai` hiện chỉ trỏ duy nhất vào LiteLLM Proxy trên Server Spark (`100.83.192.30:8090`).
- Khi lập trình viên làm việc offline, mạng Tailscale VPN bị ngắt, hoặc khi Server Spark bảo trì/khởi động lại, các lệnh gọi `ai.chat()` rơi vào vòng lặp retry và gây crash timeout (`APIConnectionError`).
- Chưa có cơ chế chuyển vùng dự phòng tự động (Automated Failover) sang Local Ollama (`localhost:11434`) hoặc Deterministic Mock Provider phục vụ Unit Test và Offline CI.

---

### 2. Đề xuất giải pháp (RFC Proposal):
Xây dựng `TieredFallbackRouter` trong `packages/ccba-ai/src/ccba_ai/routing.py`:
- **Tier 1 (Default):** LiteLLM Server Spark (`gpt-4o`, `gemini-2.5-flash`, `deepseek-r1`).
- **Tier 2 (Cloud Direct Fallback):** Trực tiếp gọi API provider nếu có env key (`GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`).
- **Tier 3 (Local Offline):** Tự động phát hiện Ollama daemon cục bộ (`http://127.0.0.1:11434/v1`) với các model nhẹ (`qwen2.5-coder:7b`, `phi-4-mini`).
- **Tier 4 (Test / Mock):** Mock LLM fixture mode khi biến môi trường `CCBA_AI_MOCK=1` được bật.
- Cấu hình Circuit Breaker chuyển vùng mượt mà (Graceful Degradation) và ghi log cảnh báo rõ ràng.

---

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Bổ sung `TieredFallbackRouter` và `MockProvider` trong `packages/ccba-ai`.
- [ ] Khi ngắt kết nối Server Spark, `ai.chat()` tự động fallback sang Tier 2 hoặc Tier 3 mà không làm sập pipeline.
- [ ] 100% các unit tests của `ccba-ai` có thể chạy offline độc lập qua Mock Provider.
- [ ] Bổ sung tài liệu cấu hình trong `packages/ccba-ai/README.md` và `docs/adr/`.

---
*Được đề xuất tự động từ Spoke `ccba-legal-knowledge` qua workflow `/ccba-issue-to-hub`.*

---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-09-02T06:40:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage).
> Xác nhận nhu cầu phân tầng dự phòng và Mock Provider cho `ccba-ai` là rất cấp thiết để phục vụ cả môi trường làm việc Offline, CI tự động và tăng độ ổn định của toàn bộ Agent Platform.
> Đã gán nhãn `enhancement` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief chi tiết bên dưới.

> **@Antigravity AI Agent (Release)** (2026-09-02T11:03:37Z):
> 🎉 Đã hoàn thành 100% việc triển khai **Ma Trận Chuyển Vùng Dự Phòng 5 Tầng (5-Tier Failover Matrix)** và **Deterministic In-Memory Mock Provider**.
> - Đã ban hành kiến trúc chính thức: [`docs/adr/0055-ccba-ai-multi-tier-failover-and-mock-provider.md`](../../../docs/adr/0055-ccba-ai-multi-tier-failover-and-mock-provider.md).
> - Đã vượt qua toàn bộ 111/111 unit tests và CI eval gates.
> - Đã merge vào `main` qua Pull Request [#234](https://github.com/vvChu/ccba-agent-platform/pull/234).
> - Đóng issue #229 thành công.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Triển khai Tiered Fallback Router 4 tầng (Spark LiteLLM -> Direct Cloud API -> Local Ollama -> Deterministic Mock) trong `ccba-ai` để đảm bảo hoạt động liên tục khi offline.

### Hành vi hiện tại (Current behavior)
- `ccba-ai` phụ thuộc hoàn toàn vào kết nối tới Server Spark (`100.83.192.30:8090`).
- Khi offline hoặc mất kết nối Tailscale VPN, `ai.chat()` liên tục retry và ném ngoại lệ `APIConnectionError`, làm dừng pipeline.
- Chưa có mock provider tích hợp để chạy unit tests và CI độc lập mà không cần network/token.

### Hành vi mong muốn (Desired behavior)
- `TieredFallbackRouter` tự động phát hiện tình trạng khả dụng theo thứ tự ưu tiên:
  - Tier 1: Server Spark LiteLLM
  - Tier 2: Direct Cloud APIs (qua `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY` nếu có trong environment)
  - Tier 3: Local Ollama daemon (`http://127.0.0.1:11434/v1`)
  - Tier 4: `MockProvider` deterministic khi `CCBA_AI_MOCK=1` hoặc `CCBA_ENV=test`
- Tích hợp với `CircuitBreaker` để tự động hạ tầng (degrade) thay vì crash.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `packages/ccba-ai/src/ccba_ai/routing.py`: `TieredFallbackRouter`, `ProviderTier` enum
- `packages/ccba-ai/src/ccba_ai/mock_provider.py`: `MockProvider` trả về phản hồi giả định định dạng JSON/text
- `packages/ccba-ai/src/ccba_ai/client.py`: Tích hợp fallback trong `ai.chat()` và `ai.chat_async()`

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] `TieredFallbackRouter` chuyển vùng chính xác giữa các tầng khi có sự cố kết nối.
- [ ] `CCBA_AI_MOCK=1` cho phép gọi `ai.chat()` offline thành công mà không cần network.
- [ ] Bộ unit test `test_tiered_routing.py` và `test_mock_provider.py` đạt 100% pass.
- [ ] Cập nhật tài liệu `packages/ccba-ai/README.md`.

### Phạm vi loại trừ (Out of scope)
- Không thay đổi interface public `ai.chat(prompt, model=..., **kwargs)`.

### Đề xuất chế độ thực thi (Recommended Execution Strategy)
- **Mức độ phức tạp**: Trung bình (trong phạm vi `packages/ccba-ai`)
- **Khuyến nghị thực thi**:
  - `[x]` 🟢 **Standard** (`/ccba-implement`): Triển khai tuần tự, scoped tests.
  - `[ ]` 🟣 **Deep Reasoning** (`/boost`): Điều tra chuyên sâu root-cause / phản biện đa vòng.
  - `[ ]` 🔵 **Multi-Agent Orchestration** (`/ccba-teamwork` hoặc `/teamwork-preview`): Phân rã Seams và chạy đa tác nhân song song.
