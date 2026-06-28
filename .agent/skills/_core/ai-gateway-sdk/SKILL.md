---
name: AI Gateway SDK
description: Kết nối AI Gateway trên Server Spark — 22 models (local GPU + cloud), 1 endpoint. Bao gồm Python package ccba-ai.
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# AI Gateway SDK

Kết nối **AI Gateway** (LiteLLM) trên **Server Spark** (DGX). Một endpoint duy nhất cung cấp 22 models — từ Qwen 35B chạy local GPU đến Claude 4.6, Gemini 3.1 Pro trên cloud.

## Kiến trúc

```
┌──────────────────────────────────────────────────────────────┐
│  MÁY CLIENT (PC/Laptop/Server khác)                         │
│                                                              │
│  from ccba_ai import ai                                      │
│  ai.chat("...")  ──► http://<SERVER_IP>:8090/v1              │
│                         ▲                                    │
│                    .env (API_KEY)                             │
└────────────────────┬─────────────────────────────────────────┘
                     │ Tailscale VPN / LAN / SSH Tunnel
┌────────────────────▼─────────────────────────────────────────┐
│  SERVER DGX SPARK                                            │
│                                                              │
│  :8090 ─► AI Gateway (LiteLLM)                               │
│              ├── qwen-local-primary    ← vLLM, local GPU    │
│              ├── reasoning-gemma       ← vLLM, fallback     │
│              ├── Claude 4.5/4.6        ← Anthropic API      │
│              ├── Gemini 3.1 Pro/Flash  ← Google API         │
│              ├── ocr-primary / tier3   ← Vision APIs        │
│              └── Auto-fallback + Redis cache                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Kết nối

| Phương thức | Server IP | Ghi chú |
|---|---|---|
| **Tailscale VPN** ⭐ | `100.83.192.30` | Khuyến nghị — an toàn, xuyên NAT |
| LAN (cùng mạng) | `<LAN_IP>` | Hỏi admin |
| SSH Tunnel | `localhost` | `ssh -N -L 8090:localhost:8090 vvc@<IP>` |

- **Gateway URL**: `http://<SERVER_IP>:8090/v1`
- **API Key**: `sk-spark-secure-key-2026`

---

## Model Catalog (Trích xuất từ API)

### 🖥️ Local GPU (Private, Offline, RAG)
| Model | Mô tả |
|-------|-------------|
| `qwen-local-primary` | ⭐ **Default** — Qwen reasoning model, mạnh mẽ cho audit |
| `rag-core` | Alias của qwen-local-primary (RAG pipeline) |
| `rag-light` | Qwen 3.5 4B — lightweight fallback |

### 🛠️ RAG Virtual Aliases (Free Tier Farm)
Mô hình "ảo" (Alias) được Gateway tự động định tuyến để tận dụng Quota Free của Google.
| Alias / Bí Danh | Model Thật (Backend) | Công Dụng (Best For) |
|-------|----------|----------|
| `text-gemma` | Gemma 3 27B | High-volume NLP (Sinh câu hỏi, Summarize) |
| `text-light-gemma` | Gemma 3 12B | Bóc tách siêu dữ liệu (Metadata, Tagging) |
| `reasoning-gemma` | Gemma 4 31B | Logical Graph (Neo4j), Structured JSON |
| `ocr-primary` | Gemini 3.1 Flash Lite| Cloud OCR Vision (Trích xuất văn bản từ Ảnh) |

### 🏎️ Cloud — Speed Tier (< 1.5s)
| Model | Best For |
|-------|----------|
| `gemini-3-flash` / `gemini-3.1-flash-lite` | Nhanh, multimodal / rẻ nhất |
| `gemma-3-27b` | Free tier, high-volume tasks |
| `claude-haiku-4` / `claude-haiku-4-5` | Fast Claude, better quality |

### 🧠 Cloud — Balanced Tier (1–3s)
| Model | Best For |
|-------|----------|
| `claude-sonnet-4-6` ⭐ | Best coding, agentic pipelines |
| `claude-sonnet-4-6-thinking` | Reasoning with CoT |
| `claude-opus-4-6` / `claude-opus-4-6-thinking` | Deep analysis, legal/financial, Opus + CoT |
| `gpt-oss-120b-medium` | Large OSS model via proxy |

### 🔬 Cloud — Deep Reasoning (7–13s, 1M context)
| Model | Best For |
|-------|----------|
| `gemini-3.1-pro` / `gemini-3.1-pro-high` / `gemini-3.1-pro-low`| Full codebase analysis, research, novel problems |
| `gemini-3-pro-high` / `gemini-3-pro-low` | Scientific reasoning, budget deep reasoning |

---

## Cách dùng

### Option A — `ccba-ai` Package (Recommended)

```bash
pip install -e "D:\GitHubProjects\ccba-agent-platform\packages\ccba-ai"
```

```python
from ccba_ai import ai

# Chat đơn giản (Qwen 35B local — mặc định)
reply = ai.chat("Xin chào!")

# Chọn model
reply = ai.chat("Review code", model="claude-sonnet-4-6")

# System prompt
reply = ai.chat("Tóm tắt...", system="Bạn là chuyên gia pháp luật", model="qwen-local-primary")

# Streaming
for chunk in ai.stream("Viết quicksort"):
    print(chunk, end="")

# Multi-turn
reply = ai.chat_multi([
    {"role": "system", "content": "Expert Python dev"},
    {"role": "user", "content": "Review this code..."},
])

# List models
print(ai.models())
```

### Option B — OpenAI SDK trực tiếp

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://100.83.192.30:8090/v1",
    api_key="sk-spark-secure-key-2026"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Option C — TypeScript/Node.js

```typescript
import OpenAI from 'openai';
import 'dotenv/config';

const client = new OpenAI({
    baseURL: process.env.AI_GATEWAY_URL || 'http://100.83.192.30:8090/v1',
    apiKey: process.env.AI_GATEWAY_KEY,
});

const response = await client.chat.completions.create({
    model: 'qwen-local-primary',
    messages: [{ role: 'user', content: 'Hello!' }],
});
```

### Option D — cURL

```bash
curl http://100.83.192.30:8090/v1/chat/completions \
  -H "Authorization: Bearer sk-spark-secure-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-local-primary","messages":[{"role":"user","content":"Hello!"}]}'
```

---

## 🧠 Đặc tính & Cách Xử lý Reasoning Models (Thinking Models)

Một số model trên Gateway (như `qwen-local-primary`, họ DeepSeek-R1, hoặc các model có hậu tố `-thinking` như `claude-sonnet-4-6-thinking`) sở hữu cơ chế tư duy nội suy. 

**Bản chất:** Thay vì sinh ra ngay kết quả, model sẽ phân tích logic, lập kế hoạch và in ra quá trình này bên trong thẻ `<think>...</think>`, sau đó mới cung cấp đáp án thực sự.

### Cấu hình bắt buộc khi gọi Reasoning Models

Để Agent/Script làm việc hiệu quả với dòng model này (đặc biệt trong các Task trích xuất dữ liệu JSON), **bắt buộc tuân thủ 3 nguyên tắc sau:**

1. **Cắt bỏ thẻ `<think>` bằng Regex:** 
   Các API Client chuẩn sẽ trả về toàn bộ text (bao gồm cả tư duy). Nếu bạn yêu cầu model trả về JSON, bạn **không thể** gọi `json.loads(raw_text)` ngay, mà phải làm sạch văn bản trước.
   ```python
   import re
   # Xóa toàn bộ nội dung trong thẻ <think>, bao gồm cả newline (DOTALL)
   clean_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
   
   # Sau đó mới tìm kiếm JSON block
   match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, flags=re.DOTALL)
   # ...
   ```

2. **Tham số `max_tokens` cực lớn:**
   Quá trình `<think>` có thể tiêu tốn từ `1000` đến `4000` tokens. Nếu bạn để `max_tokens` mặc định hoặc quá thấp, model sẽ bị đứt gãy (truncated) giữa chừng khi đang "suy nghĩ", dẫn đến không bao giờ trả ra JSON. 
   👉 **Khuyến nghị:** Luôn set `max_tokens=8192` (hoặc tối đa) khi dùng reasoning model.

3. **Tham số `temperature` cực thấp:**
   Bản thân quá trình `<think>` đã tạo ra độ đa dạng và sáng tạo (Variance) trong cách giải quyết vấn đề.
   👉 **Khuyến nghị:** Set `temperature=0.1` hoặc `0.0` để đảm bảo output cuối cùng (đặc biệt là schema JSON) luôn ổn định và đáng tin cậy.

### Khi nào nên dùng Reasoning Models?
- **NÊN DÙNG:** Các bài toán phức tạp, đòi hỏi phân tích chéo, toán học, đối chiếu luật (như Semantic PCCC Audit), hoặc xử lý code quy mô lớn.
- **KHÔNG NÊN DÙNG:** Các bài toán trích xuất NER cơ bản (đọc Name, Phone từ CV), định dạng lại chuỗi, hoặc các task cần phản hồi tốc độ cực cao (< 2s) vì quá trình `<think>` rất tốn thời gian.

---

## Cấu hình (.env)

Copy file `.env.ai-gateway` (cùng folder) vào project, đổi tên `.env`:

```env
AI_GATEWAY_URL=http://100.83.192.30:8090/v1
AI_GATEWAY_KEY=sk-spark-secure-key-2026
AI_MODEL=qwen-local-primary
```

---

## Model Routing Logic

```python
def choose_model(task_type: str) -> str:
    routing = {
        "coding":     "claude-sonnet-4-6",          # Best coding
        "reasoning":  "claude-sonnet-4-6-thinking", # Cloud logic
        "research":   "gemini-3.1-pro-high",        # Large context
        "fast":       "claude-haiku-4-5",           # Speed
        "private":    "qwen-local-primary",         # Offline/private logic
        "ocr":        "ocr-primary",                # For parsing PDFs/Images
        "vietnamese": "qwen-local-primary",         # Vietnamese text
    }
    return routing.get(task_type, "qwen-local-primary")
```

---

## Quick Test

```bash
# Verify gateway reachable
curl http://100.83.192.30:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026"

# Health check
curl http://100.83.192.30:8090/health
```

---

## Xử lý sự cố

| Vấn đề | Giải pháp |
|--------|-----------|
| `Connection refused` | Kiểm tra Tailscale/VPN, hoặc dùng SSH tunnel |
| `401 Unauthorized` | Sai API key — kiểm tra `AI_GATEWAY_KEY` |
| `Model not found` | Kiểm tra tên model bằng `/v1/models` |
| `504 Gateway Timeout` | Model đang load, chờ 2-3 phút rồi thử lại |
| Qwen 35B chậm | Giảm `max_tokens`, hoặc dùng `rag-light` (4B) |

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
- **Env template**: `.agent/skills/ai-gateway-sdk/.env.ai-gateway`
- **Server docs**: Xem thêm tại `AI_Gateway/playbooks/` (archived)
