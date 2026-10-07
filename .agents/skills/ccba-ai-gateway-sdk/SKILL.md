---
name: ccba-ai-gateway-sdk
description: Kết nối AI Gateway trên Server Spark — Đa mô hình (local GPU + cloud),
  1 endpoint. Bao gồm Python package ccba-ai.
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
tier: kernel
command: /ccba-ai-gateway-sdk
metadata:
  version: "1.4.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- ai
- llm
- model
- gateway
- chat
- inference
- DGX
- vLLM
- Qwen
- Claude
- Gemini
package_path: packages/ccba-ai
---
# AI Gateway SDK

Kết nối **AI Gateway** (LiteLLM) trên **Server Spark** (DGX). Một endpoint duy nhất cung cấp đa dạng mô hình thời gian thực qua `ai.models()` — từ Qwen 35B chạy local GPU đến Claude, Gemini trên cloud.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`package-bound`**, bám trực tiếp vào gói monorepo `packages/ccba-ai` cung cấp 4 Capability Seams nền tảng:
- **`ai_chat.v1`**: Đàm thoại và sinh văn bản (`from ccba_ai import ai`).
- **`ai_embedding.v1`**: Trích xuất vector ngữ nghĩa (`from ccba_ai import embed`).
- **`ai_transcribe.v1`**: Chuyển giọng nói thành văn bản (`from ccba_ai import transcribe`).
- **`model_routing.v1`**: Định tuyến mô hình theo tác vụ chuẩn (`from ccba_ai import choose_model, ModelArchetype`).

Mọi tương tác LLM từ client (Hub/Spoke/CLI) BẮT BUỘC định tuyến qua Seam `model_routing.v1` bằng các khóa tác vụ chuẩn (`general`, `reasoning`, `coding`, `ocr`, `rag`, `private`). Tuyệt đối không hardcode API key, không nhúng chuỗi model thô của nhà cung cấp vào mã nguồn.

---

## Kiến trúc

```
┌──────────────────────────────────────────────────────────────┐
│  MÁY CLIENT (PC/Laptop/Server khác)                         │
│                                                              │
│  from ccba_ai import ai                                      │
│  ai.chat("...")  ──► http://${CCBA_AI_GATEWAY_HOST}:8090/v1   │
│                         ▲                                    │
│                    .env (API_KEY)                             │
└────────────────────┬─────────────────────────────────────────┘
                     │ Tailscale VPN / LAN / SSH Tunnel
┌────────────────────▼─────────────────────────────────────────┐
│  SERVER DGX SPARK                                            │
│                                                              │
│  :8090 ─► AI Gateway (LiteLLM)                               │
│              ├── qwen-local-primary    ← vLLM, local GPU    │
│              ├── reasoning-gemma       ← Google API, fallback│
│              ├── Claude Reasoning      ← Anthropic API      │
│              ├── Gemini Standard/Flash ← Google API         │
│              ├── ocr-primary / tier3   ← Vision APIs        │
│              └── Auto-fallback + Redis cache                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Kết nối

| Phương thức | Server Host | Ghi chú |
|---|---|---|
| **Tailscale VPN** ⭐ | `${CCBA_AI_GATEWAY_HOST}` | Khuyến nghị — an toàn, xuyên NAT |
| LAN (cùng mạng) | `<LAN_IP>` | Hỏi admin |
| SSH Tunnel | `localhost` | `ssh -N -L 8090:localhost:8090 vvc@<IP>` |

- **Gateway URL**: `http://${CCBA_AI_GATEWAY_HOST}:8090/v1`
- **API Key**: `<YOUR_AI_GATEWAY_KEY>`

---

## 🏛️ 4 Model Archetypes (Vai trò Nghiệp vụ Chuẩn)

Khi tích hợp từ phía client (Hub/Spoke/Web/CLI), luôn định tuyến model theo đúng 4 Archetypes chuẩn qua Seam `model_routing.v1`:

| Archetype | Task Key (`choose_model`) | Enum Archetype | Khi nào sử dụng? |
| :--- | :--- | :--- | :--- |
| **1. OCR & Vision** | `"ocr"` | `ModelArchetype.OCR` | Xử lý OCR tài liệu PDF, bản vẽ, hình ảnh, trích xuất text bảng biểu. |
| **2. Standard / Coding** | `"general"`, `"coding"` | `ModelArchetype.STANDARD` | Chat tổng quát, code sinh tự động, tóm tắt bài viết, đàm thoại agent. |
| **3. Deep Reasoning** | `"reasoning"`, `"audit"` | `ModelArchetype.REASONING` | Phân tích điều khoản hợp đồng phức tạp, đối soát pháp lý, suy luận đa bước. |
| **4. Local Private** | `"private"`, `"rag"` | `ModelArchetype.LOCAL`, `ModelArchetype.RAG` | Chạy offline, dữ liệu tuyệt mật nội bộ, fallback chốt chặn khi mất Internet. |

---

## ⚙️ Quy tắc Hợp đồng Tích hợp (Client Contract Rules)

### 1. Quy tắc HTTP Timeout (Bắt buộc: 30s – 90s, Mặc định: 90s)
- **Lý do**: AI Gateway triển khai cơ chế **Fallback Cascade** đa tầng (tự động xoay vòng 10 API keys và giáng cấp model khi upstream gặp lỗi 503/429).
- **Quy chuẩn**: Phía client **PHẢI** cấu hình `timeout >= 30.0s` (mặc định trong SDK: `90.0s`). Tuyệt đối không cấu hình timeout quá ngắn (<15s) tránh cắt đứt luồng failover ngầm.

### 2. Zero-Config Thinking Parameters
- Phía client **KHÔNG CẦN** tự tạo cấu trúc Google-specific như `generationConfig.thinking_config` hay `thinking_budget`.
- AI Gateway tích hợp sẵn middleware `custom_callbacks.gemini_corrector` tự động chuẩn hóa, chèn và lọc tham số suy luận theo từng model (`-low`, `-medium`, `-high`).

---

## 🛡️ Sơ đồ Chuyển vùng Dự phòng (Fallback Cascade)

```mermaid
graph TD
    User([Client Request]) --> ModelChoice{Task Routing}

    ModelChoice -->|reasoning| R1[Reasoning Tier 1]
    R1 -->|503/429/Timeout| R2[Reasoning Tier 2]
    R2 -->|503/429/Timeout| R3[Standard Fallback]
    R3 -->|503/429/Timeout| R4[Local MoE GPU]

    ModelChoice -->|ocr| O1[Vision OCR Primary]
    O1 -->|503/429/Timeout| O2[Vision OCR Fallback]
    O2 -->|503/429/Timeout| R4
```

### 🛡️ Cơ chế Kháng Lỗi Ngân sách LiteLLM & 5-Tier Failover Router (RULE-2.12)
`ccba-ai` tích hợp sẵn bộ định tuyến chuyển vùng dự phòng tự động 5 tầng:
- **Tier 1 (Gateway)**: LiteLLM trên Server Spark (:8090).
- **Tier 2 (Cloud Direct)**: Gọi trực tiếp Google AI Studio / Groq / OpenAI qua API keys cục bộ.
- **Tier 3 (Dual-CLI)**: Trực tiếp qua Antigravity CLI / GitHub Copilot CLI.
- **Tier 4 (Local Offline)**: Ollama hoặc local vLLM Qwen 35B trên DGX Spark.
- **Tier 5 (Mock)**: Giả lập kết quả cho testing không tốn token.

**Kháng lỗi Ngân sách (`BudgetExceededError`)**:
Khi LiteLLM Gateway hết quota hoặc vượt ngưỡng chi phí, lỗi trả về đa dạng (JSON structured hoặc plain text). Router tự động nhận diện mẫu lỗi:
```python
is_budget_exceeded = "budget" in str(exc).lower() and "exceeded" in str(exc).lower()
```
Khi kích hoạt, hệ thống lập tức chuyển thẳng sang Tier 2 hoặc Tier 4 (Local Ollama/Qwen), ngăn chặn triệt để vòng lặp thử lại vô hạn (infinite retry loop) và bảo đảm tác vụ không bị đình trệ.

---

## Cách dùng

### Option A — `ccba-ai` Package (Khuyến nghị cho Hub/Spoke)

```bash
pip install -e "$CCBA_HUB_PATH/packages/ccba-ai"
# Tùy chọn: cài đặt thêm ccba-harness nếu cần FileMutexLock cấp cao cho Plan/Team:
# pip install -e "$CCBA_HUB_PATH/packages/ccba-harness"
```

```python
from ccba_ai import ai, async_ai, ModelArchetype, choose_model, chat_with_metadata

# 1. Chat cơ bản (mặc định timeout=90.0s, strip_thinking=True)
response = ai.chat(
    "Tóm tắt các điểm chính trong tài liệu đính kèm...",
    model=ModelArchetype.STANDARD  # Khóa tác vụ general
)
print(response)

# 2. Deep reasoning (Tự động cấp phát max_tokens=16384 và tự làm sạch thẻ <think>)
deep_res = ai.chat(
    "Phân tích xung đột giữa Điều 12 và Điều 18 của dự thảo...",
    model=ModelArchetype.REASONING  # Khóa tác vụ reasoning
)
print(deep_res)

# 3. Đo lường Telemetry, Token Usage & Độ trễ (ChatResult)
res = ai.chat_with_metadata("Kiểm tra pháp lý hợp đồng...", model=ModelArchetype.REASONING)
print(f"Content: {res.content}")
print(f"Model used: {res.model}")
print(f"Tokens: prompt={res.usage.prompt_tokens}, completion={res.usage.completion_tokens}, total={res.usage.total_tokens}")
print(f"Latency: {res.latency_ms} ms")

# 4. Định tuyến tự động theo task
model_name = choose_model("ocr")  # Seam model_routing.v1
```

---

## 📦 Prompt Engineering & Evaluator-Optimizer Loop

SDK `ccba-ai` cung cấp sẵn các module hỗ trợ kỹ thuật Prompting nâng cao (Technique 15 & Anthropic Best Practices):

### 1. XML Prompt Envelopes (`xml_envelope`, `parse_xml_tags`)
Đóng gói tài liệu, chỉ thị và ngữ cảnh vào các thẻ XML để phân định ranh giới ngữ cảnh rõ ràng và triệt tiêu prompt injection:

```python
from ccba_ai import ai, choose_model, parse_xml_tags, xml_envelope

# Bọc có cấu trúc
envelope_prompt = xml_envelope({
    "instructions": "Soạn thảo văn bản thẩm tra PCCC theo chuẩn Nghị định 105/2025",
    "context": {"decree": "105/2025/NĐ-CP", "standard": "QCVN 06:2022/BXD"},
    "documents": ["Nội dung thuyết minh thiết kế công trình..."],
})

response = ai.chat(envelope_prompt, model=choose_model("reasoning"))
tags = parse_xml_tags(response)
print(tags.get("answer", response))
```

### 2. Evaluator-Optimizer Feedback Loop (`evaluator_optimizer_loop`)
Vòng lặp tự động sửa lỗi giữa Generator $\leftrightarrow$ Evaluator:

```python
from ccba_ai import ai, evaluator_optimizer_loop

result = evaluator_optimizer_loop(
    generator_fn=lambda fb: ai.chat(f"Soạn thảo tài liệu. Phản hồi vòng trước: {fb}"),
    evaluator_fn=lambda draft: (95.0, "Đạt") if "105/2025" in draft else (60.0, "Bổ sung viện dẫn NĐ 105/2025"),
    max_iterations=3,
    pass_score=85.0,
)
print(f"Hoàn tất: {result.passed} trong {result.iterations} vòng. Điểm: {result.score}")
```

---

## ⚡ Local Fast-Fail Circuit Breaker (Chống Treo Khi Mất Mạng)

Để bảo vệ các batch processing pipelines không bị treo 60s timeout khi mạng Tailscale VPN rớt, `ccba-ai` tích hợp sẵn **`CircuitBreaker`**:

- **3 Trạng thái**: `CLOSED` (bình thường), `OPEN` (ngắt nhanh fast-fail), `HALF_OPEN` (thử thăm dò phục hồi sau 30s cooldown).
- **Ngưỡng kích hoạt**: Mặc định 3 lần lỗi kết nối liên tiếp sẽ ngắt kết nối (`CircuitBreakerOpenError`) tức thì ở các request sau.

```python
from ccba_ai import ai, CircuitBreaker

# Tùy chỉnh Circuit Breaker cho batch pipeline
custom_cb = CircuitBreaker(failure_threshold=2, recovery_timeout=15.0)
ai.circuit_breaker = custom_cb
```

---

## 🧠 Đặc tính & Cách Xử lý Reasoning Models (Thinking Models)

Một số model trên Gateway (như `gemini-3.7-flash-high`, `claude-sonnet-4-6-thinking`, `reasoning-gemma`, `qwen-local-primary`) sở hữu cơ chế tư duy nội suy. 

**Bản chất:** Model sinh ra quá trình suy luận bên trong thẻ `<think>...</think>` trước khi đưa ra kết quả cuối cùng.

### Cơ chế Tự động hóa trong `ccba-ai` SDK:

1. **Auto Max-Tokens (16,384 tokens)**: 
   Khi gọi reasoning model với `max_tokens` mặc định (`1024` hoặc `2048`), SDK tự động nâng ngân sách lên **`16,384` tokens** để chứa trọn vẹn cả thinking budget và câu trả lời mà không bị cắt cụt (truncated).
2. **Auto Strip Thinking (`strip_thinking=True`)**:
   Mặc định, `ai.chat()` và `ai.chat_multi()` tự động lọc sạch các thẻ `<think>` khỏi output trả về. Nếu muốn lấy toàn bộ nội dung suy luận thô, truyền `strip_thinking=False`.
3. **Nhiệt độ khuyến nghị**: 
   Đặt `temperature=0.1` hoặc `0.0` khi yêu cầu trích xuất JSON cấu trúc để giữ tính ổn định.

### Khi nào nên dùng Reasoning Models?
- **NÊN DÙNG:** Các bài toán phức tạp, đòi hỏi phân tích chéo, toán học, đối chiếu luật (như Semantic PCCC Audit), hoặc xử lý code quy mô lớn.
- **KHÔNG NÊN DÙNG:** Các bài toán trích xuất NER cơ bản (đọc Name, Phone từ CV), định dạng lại chuỗi, hoặc các task cần phản hồi tốc độ cực cao (< 2s) vì quá trình `<think>` rất tốn thời gian.

---

## Cấu hình (.env)

Copy file `.env.ai-gateway` (cùng folder) vào project, đổi tên `.env`:

```env
AI_GATEWAY_URL=http://${CCBA_AI_GATEWAY_HOST}:8090/v1
AI_GATEWAY_KEY=<YOUR_AI_GATEWAY_KEY>
AI_MODEL=general
```

---

## Model Routing Logic per ADR-0061

```python
from ccba_ai.routing import choose_model, ModelArchetype

# Định tuyến chuẩn theo tác vụ qua Seam model_routing.v1
# SSOT mapping được quản trị tập trung tại packages/ccba-ai/src/ccba_ai/routing.py
model_alias = choose_model("reasoning")
```

---

## Quick Test

```bash
# Verify gateway reachable
curl http://${CCBA_AI_GATEWAY_HOST}:8090/v1/models \
  -H "Authorization: Bearer <YOUR_AI_GATEWAY_KEY>"

# Health check
curl http://${CCBA_AI_GATEWAY_HOST}:8090/health
```

---

## Xử lý sự cố

| Vấn đề | Giải pháp |
|--------|-----------|
| `Connection refused` | Kiểm tra Tailscale/VPN, hoặc dùng SSH tunnel |
| `401 Unauthorized` | Sai API key — kiểm tra `AI_GATEWAY_KEY` |
| `Model not found` | Kiểm tra tên model bằng `/v1/models` |
| `504 Gateway Timeout` | Model đang load, chờ 2-3 phút rồi thử lại |
| Qwen 35B chậm | Giảm `max_tokens`, hoặc dùng `rag-light` (9B AWQ, on-demand profile `vllm-light`) |

## 🧹 Output Processing — Làm Sạch LLM Output

> Áp dụng **TRƯỚC** khi parse, lưu hoặc hiển thị bất kỳ output LLM nào.  
> Kinh nghiệm từ VvC Pipeline (v7.4+): 100% output phải đi qua các bước này.

### 1. Think-Tag Stripping (Bắt buộc với Reasoning Models)

LLM reasoning models (Qwen, DeepSeek-R1, Claude -thinking) có thể rò rỉ `<think>` tags vào output. **Phải strip unconditionally** — không phụ thuộc vào prompt hay model config.

```python
import re

# 3 patterns xử lý toàn bộ edge cases
_THINK_PATTERN  = re.compile(r"<think>.*?</think>\n*", re.DOTALL | re.IGNORECASE)
_THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)   # tag chưa đóng
_ORPHAN_END     = re.compile(r"^.*?</think>\n*", re.DOTALL | re.IGNORECASE)  # chỉ có </think>

def strip_think_tags(text: str) -> str:
    """Strip toàn bộ <think>...</think> blocks khỏi LLM output."""
    text = _THINK_PATTERN.sub("", text)
    text = _THINK_UNCLOSED.sub("", text)
    text = _ORPHAN_END.sub("", text)
    return text.strip()
```

> [!CAUTION]
> Nếu bỏ qua bước này, toàn bộ chain-of-thought của LLM (có thể 200+ dòng) sẽ rò rỉ vào output thực tế — đã xảy ra trong thực tế (`deliberate_practice.md` chứa 210 dòng think-tag).

### 2. JSON Extraction từ Markdown Code Fence

LLM thường bọc JSON trong ` ```json ... ``` `. Phải extract trước khi `json.loads()`.

```python
def extract_json(raw: str) -> dict | None:
    """Extract JSON từ LLM output, xử lý cả raw JSON và markdown-wrapped."""
    clean = strip_think_tags(raw)
    # Thử markdown fence trước
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, flags=re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Fallback: tìm raw JSON object
    match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return None
```

### 3. Timeout / Garbage Guard

Luôn validate output trước khi dùng. Không có bước này → pipeline sẽ lưu error messages vào database.

```python
def is_valid_output(text: str, min_chars: int = 10) -> bool:
    """Kiểm tra output LLM không phải timeout error hay rỗng."""
    if not text or len(text.strip()) < min_chars:
        return False
    if text.strip().startswith("Error connecting"):
        return False
    return True
```

### 4. Web Fetch Garbage Detection

Khi fetch URL để làm context, sites JS-heavy (Twitter, SPA) trả về error pages.

```python
_GARBAGE_PATTERNS = [
    r"javascript is (?:disabled|not available)",
    r"enable javascript",
    r"something went wrong.*(?:try again|let.s give it another shot)",
    r"we.ve detected that javascript",
    r"please enable cookies",
    r"access denied.*cloudflare",
    r"noscript",
    r"this browser is no longer supported",
]

def is_garbage_fetch(text: str, min_chars: int = 100) -> bool:
    """True nếu fetched content là error page, không phải real content."""
    if len(text.strip()) < min_chars:
        return True
    text_lower = text.lower()
    return sum(1 for p in _GARBAGE_PATTERNS if re.search(p, text_lower)) >= 2
```

### 5. ALL-CAPS OCR Artifact Removal

Khi OCR capture page headers/footers (thường in HOA), loại bỏ trước khi synthesis.

```python
def remove_ocr_artifacts(text: str) -> str:
    """Loại bỏ các dòng ALL-CAPS dài (>15 chars) — thường là header/footer trang."""
    return re.sub(r'^[A-ZÀ-Ỹ][A-ZÀ-Ỹ\s_]{14,}\.?\s*$', '', text,
                  flags=re.MULTILINE).strip()
```

---

## Bảo mật

1. **KHÔNG commit API key** vào git — thêm `.env` vào `.gitignore`
2. **Dùng Tailscale** thay vì expose port ra public internet
3. **Mỗi project** có `.env` riêng, không hardcode IP/key trong code

## Files liên quan

- **Package**: `packages/ccba-ai/` — pip install để dùng `from ccba_ai import ai`
- **Env template**: `.agents/skills/ccba-ai-gateway-sdk/.env.ai-gateway`
- **Server docs**: Xem thêm tại `AI_Gateway/playbooks/` (archived)

---

## Tiêu chí hoàn thành

- [ ] **Completion Criterion:** Đã kết nối và xác thực thành công các Capability Seams (`ai_chat.v1`, `ai_embedding.v1`, `ai_transcribe.v1`, `model_routing.v1`) qua package `ccba_ai`, tuân thủ định tuyến mô hình chuẩn qua `choose_model()`.

