# Báo cáo Nghiên cứu: Toàn Cảnh Kiến Trúc, Năng Lực & Rủi Ro Module `ccba-ai`

> **Quy trình thực hiện:** `/ccba-research` — Chế độ Phản biện Kép (Dual-Agent Adversarial Pattern)  
> **Thời gian nghiên cứu:** 16/09/2026  
> **Thực thể khảo sát:** `packages/ccba-ai` (`src/ccba_ai/`)  
> **Tiêu chuẩn đối soát:** ADR-0025, ADR-0029, ADR-0035 (Deep Modules), ADR-0055 (Multi-Tier Failover), ADR-0058 (Hard Completion Lock)

---

## 1. Tóm Tắt Thực Thi (Executive Summary)

Module `ccba-ai` ([`packages/ccba-ai`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai)) là xương sống cung cấp dịch vụ trí tuệ nhân tạo (AI Gateway & Client Library) dùng chung cho toàn bộ hệ sinh thái CCBA Agent Services Platform (Hub và các Spoke). Được xây dựng dựa trên giao thức bọc OpenAI SDK, package giải quyết bài toán trừu tượng hóa đa mô hình: kết nối LiteLLM Gateway trên Server Spark (`:8090`), các API đám mây trực tiếp (Google Gemini, Groq, OpenAI), Antigravity CLI subprocess (`agy -p`), và máy chủ Ollama cục bộ (`127.0.0.1:11434`).

Khảo sát đối kháng chéo (Dual-Pass Adversarial Review) ghi nhận các điểm mạnh vượt trội:
1. **Thiết kế Thin Seam chuẩn mực (ADR-0035):** Tất cả các consumer trong monorepo đều nhập qua public entry point `from ccba_ai import ai, AIClient...`, hoàn toàn không có hiện tượng xâm nhập private submodules (`ccba_ai._*`).
2. **Khả năng chịu lỗi đa tầng (ADR-0055):** Ma trận 5 tầng failover đảm bảo hệ thống không bao giờ bị đứt gãy luồng xử lý do sự cố của một nhà cung cấp.
3. **Cơ chế kiểm thử độc lập (Zero-Network CI):** `MockProvider` cho phép chạy 100% test suite nội bộ mà không phát sinh chi phí hoặc phụ thuộc mạng ngoài.

Tuy nhiên, cuộc rà soát đối kháng đã chỉ ra **3 rủi ro kỹ thuật cần đặc biệt lưu ý**:
- **Vách đá độ trễ (Latency Cliff):** Khi đứt kết nối VPN Tailscale vào Server Spark, thời gian chờ timeout tích lũy qua 3 lần retry có thể lên tới ~247 giây (~4.1 phút) trước khi kích hoạt tầng failover tiếp theo.
- **Rủi ro lộ sơ đồ mạng nội bộ:** IP CGNAT Tailscale `100.83.192.30:8090` và Ollama `127.0.0.1:11434` đang được gán cứng làm giá trị mặc định trong code.
- **Độ phình của `client.py`:** Tệp tin hiện dài 964 dòng, gánh quá nhiều trách nhiệm (tải env, retry, streaming, sync/async client, routing).

---

## 2. Kết Quả Nghiên Cứu Chi Tiết (Key Findings)

### 2.1. Tổng quan Cấu trúc & Public Seams
Module được tổ chức theo cấu trúc chuẩn PEP 621 (`pyproject.toml`) với các Deep Seams được bộc lộ tại [`src/ccba_ai/__init__.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/__init__.py):
- **Singleton Cấp Module:** `ai = AIClient()` và `async_ai = AsyncAIClient()`. Tối ưu tài nguyên, không gây ô nhiễm `builtins`.
- **Hàm Tiện Ích Trực Tiếp (Convenience Shorthands):** `chat`, `chat_with_metadata`, `stream`, `chat_multi`, `models`, `transcribe`, `encode_image`.
- **Lazy Loading (PEP 562):** Áp dụng `__getattr__` cho namespace `services`, giúp package khởi động tức thì mà không bị kéo theo các dependencies nặng khi chỉ cần chat cơ bản.

### 2.2. Ma Trận Điều Hướng & Chuyển Vùng Đa Tầng (Multi-Tier Failover Matrix - ADR 0055)
Hệ thống vận hành theo chuỗi chuyển tiếp một chiều (không có nguy cơ Infinite Loop):
```
[Tier 1: LiteLLM Spark :8090]
       │ (Gặp lỗi mạng / 5xx)
       ▼
[Tier 2: Cloud Direct API (Gemini / Groq / OpenAI)]
       │ (Thiếu API Keys)
       ▼
[Tier 3: Antigravity CLI (agy -p)] ──► Độ trễ cao (~30-40s/call [đo thực tế])
       │ (Không có CLI binary)
       ▼
[Tier 4: Local Ollama daemon (127.0.0.1:11434)]
       │ (Ollama không bật)
       ▼
[Tier 5: Deterministic In-Memory MockProvider]
```

- **Cơ chế Reasoning Auto-Allocation:** Hàm `is_reasoning_model()` tự động phát hiện các mô hình tư duy sâu (o1, o3, DeepSeek-R1, Gemini Thinking) và tự động mở rộng `max_tokens` từ mức mặc định lên **16,384 tokens**, ngăn chặn triệt để hiện tượng đứt chuỗi suy luận.
- **Lọc thẻ tư duy (`strip_think_tags`):** Tự động bóc tách các tag `<think>...</think>` trước khi chuyển giao kết quả cho người dùng hoặc parser JSON.

### 2.3. Đánh Giá Đối Kháng & Rủi Ro Kỹ Thuật (Adversarial Analysis)

| Trục Đánh Giá | Hiện Trạng Thực Tế | Rủi Ro / Điểm Nghẽn | Mức Độ |
| :--- | :--- | :--- | :---: |
| **Bảo Mật & Secrets** | Có `PrivacyGuardHook` quét prompt & response theo chuẩn Maskara. | Hardcode IP Tailscale `100.83.192.30` trong `client.py:153`. Fallback về `"mock-key-for-ci"` gây chậm phát hiện lỗi thiếu key. Tự ý duyệt ngược 5 cấp thư mục tìm `.env`. | 🟡 Medium |
| **Độ Trễ Khi Đứt VPN (Latency Cliff)** | Retry exponential backoff (3 lần) phối hợp `timeout=60s`. | Khi đứt mạng Spark, thời gian chờ Tier 1 lên tới **247 giây** trước khi sang Tier 2. Thiếu `connect_timeout` ngắn (fail-fast LAN). | 🔴 High |
| **Circuit Breaker Coupling** | Ngưỡng `failure_threshold = 3`. | Mỗi lần retry trong cùng 1 request đều tính là 1 failure $\rightarrow$ 1 request duy nhất bị timeout là CircuitBreaker chuyển sang `OPEN`. | 🟡 Medium |
| **Độ Phức Tạp Mã Nguồn** | `client.py` dài 964 dòng chứa toàn bộ logic. | Vi phạm nguyên tắc Single Responsibility Principle (SRP) và KISS. | 🟡 Medium |
| **Độ Cách Ly Kiểm Thử** | 18 test files bao phủ hầu hết các thành phần. | `AIClient.__init__` khởi tạo socket thật nếu không bật `CCBA_AI_MOCK=1`. Thiếu rào chắn cấm socket cấp CI (`pytest-socket`). | 🟢 Low |

---

## 3. Khuyến Nghị Triển Khai (Implementation Recommendations)

### 3.1. Khuyến Nghị Ngay (Short-Term Refinements)
1. **Thiết lập `connect_timeout` Ngắn Cho Mạng LAN/VPN:**
   - Thay vì để một timeout duy nhất `60.0s` cho cả vòng đời request, cấu hình `httpx.Timeout(timeout=60.0, connect=3.0)` cho kết nối tới Spark Gateway. Nếu sau 3 giây không bắt tay được socket với Spark, lập tức kích hoạt Failover sang Tier 2 thay vì chờ hết 60 giây.
2. **Loại Bỏ Hardcode IP & Fallback Mock Key:**
   - Đọc `AI_GATEWAY_URL` bắt buộc từ biến môi trường hoặc file cấu hình, có fallback an toàn về `localhost` thay vì phơi bày dải IP mạng VPN nội bộ.
   - Khi thiếu API Key, ném ngoại lệ `AuthenticationError` rõ ràng (Fail-Fast) thay vì âm thầm gửi key giả `"mock-key-for-ci"`.

### 3.2. Khuyến Nghị Tái Cấu Trúc (Architectural Evolution)
1. **Chia Nhỏ `client.py` Thành Deep Seams Nội Bộ:**
   - Tách `client.py` thành các mô-đun chuyên biệt: `_retry.py` (logic retry & backoff), `_sync_client.py` (`AIClient`), `_async_client.py` (`AsyncAIClient`), và `_transport.py`. Giữ `client.py` chỉ làm facade mỏng (Thin Seam).
2. **Schema-Aware Mock Generator Trong `MockProvider`:**
   - Bổ sung cơ chế sinh JSON giả lập tương thích với Pydantic schema hoặc cấu trúc `parse_llm_json()` khi chạy ở Tier 5 để các caller cấp cao không bị `JSONDecodeError`.

---

## 4. Ma Trận Đánh Giá Giải Pháp (Value Matrix)

$$\text{Tổng Điểm} = \text{Giá Trị} \times 3.0 - \text{Độ Phức Tạp} \times 1.5 - \text{Rủi Ro} \times 2.0 + \text{KISS} \times 2.5$$

| Tiêu Chí | Đánh Giá | Nhận Xét Cụ Thể |
| :--- | :---: | :--- |
| **Giá Trị (Value)** | `9.0/10` | Cung cấp cổng AI trung tâm ổn định, đa mô hình, tự thích ứng suy luận sâu cho toàn nền tảng. |
| **Độ Phức Tạp (Complexity)** | `6.5/10` | 5 tầng fallback và CircuitBreaker hoạt động tốt nhưng đan xen nhiều tầng cấu hình. |
| **Rủi Ro (Risk)** | `4.0/10` | Rủi ro chính nằm ở Latency Cliff khi đứt VPN Spark; rủi ro rò rỉ mã/secret ở mức thấp nhờ Maskara Hook. |
| **Tính Đơn Giản (KISS)** | `7.0/10` | Singleton `ai.chat()` cực kỳ thân thiện với người dùng; tuy nhiên file `client.py` cần được tinh gọn. |

---

## 5. Tài Liệu Tham Chiếu & Citations

1. **Monorepo Package Core:**
   - Cấu hình Package: [`packages/ccba-ai/pyproject.toml`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/pyproject.toml)
   - Cửa ngõ Deep Seam: [`packages/ccba-ai/src/ccba_ai/__init__.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/__init__.py)
   - Core Transport Client: [`packages/ccba-ai/src/ccba_ai/client.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/client.py)
   - Fallback Matrix: [`packages/ccba-ai/src/ccba_ai/fallback.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/fallback.py)
   - Circuit Breaker: [`packages/ccba-ai/src/ccba_ai/circuit_breaker.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/circuit_breaker.py)
   - Testing Mock: [`packages/ccba-ai/src/ccba_ai/mock_provider.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/mock_provider.py)
2. **Quy Định Kiến Trúc & Hiến Pháp:**
   - [`docs/adr/0035-polyglot-deep-modules-and-subagent-guardrails.md`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0035-polyglot-deep-modules-and-subagent-guardrails.md): Nguyên tắc Thin Seams & Deep Modules.
   - [`docs/adr/0055-ccba-ai-multi-tier-failover-and-mock-provider.md`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0055-ccba-ai-multi-tier-failover-and-mock-provider.md): Chuẩn mực ma trận chuyển vùng đa tầng.
   - [Global User Rules & AI Gateway Integration](file:///C:/Users/chuvu/.gemini/GEMINI.md#2-ai-gateway-integration): Quy tắc triệu hồi `from ccba_ai import ai`.

---

## 6. Câu Hỏi Chưa Làm Rõ (Unresolved Questions)

1. **Chính sách phân bổ tài nguyên Spark GPU khi chạy đồng thời nhiều Spoke:** Khi có 5-10 Spoke thực hiện batch RAG hoặc thẩm tra QC cùng lúc, LiteLLM trên Spark có cơ chế rate limit theo từng Spoke token hay chỉ dùng chung một pool kết nối?
2. **Cập nhật danh sách reasoning models:** Hàm `is_reasoning_model()` hiện đang dùng danh sách tiền tố tĩnh (`o1`, `o3`, `deepseek-r1`, `gemini-2.5-flash-thinking`). Cần xem xét cơ chế cập nhật tự động từ registry mô hình của Gateway để tránh phải patch code mỗi khi có model mới xuất hiện.

---
*Báo cáo được biên soạn và kiểm chứng theo quy chuẩn nghiên cứu kỹ thuật CCBA Platform.*
