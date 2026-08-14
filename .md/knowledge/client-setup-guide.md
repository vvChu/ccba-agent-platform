# Hướng Dẫn Cài Đặt Client — Kết Nối AI Gateway từ Máy Khác

> **Server**: DGX Spark (`spark-CCBA`)
> **Gateway**: LiteLLM AI Gateway — 44 models (Claude, Gemini, GPT, Qwen local)
> **Cập nhật**: 2026-03-28

---

## Tổng Quan Kiến Trúc

```
┌──────────────────────────────────────────────────────────────┐
│  MÁY CLIENT (PC/Laptop/Server khác)                         │
│                                                              │
│  Project A ──┐                                               │
│  Project B ──┼── OpenAI SDK ──► http://<SERVER_IP>:8090/v1   │
│  Project C ──┘      ▲                                        │
│                     │                                        │
│              .env (API_KEY)                                  │
└──────────────────────┬───────────────────────────────────────┘
                       │ Tailscale VPN / LAN / SSH Tunnel
┌──────────────────────▼───────────────────────────────────────┐
│  SERVER DGX SPARK                                            │
│                                                              │
│  :8090 ─► AI Gateway (LiteLLM)                               │
│              │                                               │
│              ├── Claude, Gemini, GPT  (cloud proxy)          │
│              ├── qwen-local-primary (:8004 active direct)   │
│              ├── rag-light (:8003 inactive, fallback)        │
│              └── Auto-fallback + Redis cache                 │
└──────────────────────────────────────────────────────────────┘
```

**Tất cả project chỉ cần 1 endpoint duy nhất** → `http://<SERVER_IP>:8090/v1`
Dùng OpenAI SDK chuẩn, thay đổi model name là xong.

---

## Bước 1: Chọn Phương Thức Kết Nối

### Phương thức A: Tailscale VPN ⭐ (Khuyến nghị)

> An toàn, không cần mở port ra internet, hoạt động xuyên NAT/firewall.

**Trên máy client:**
1. Cài Tailscale: https://tailscale.com/download
2. Đăng nhập cùng tài khoản Tailscale với server
3. Server IP qua Tailscale: **`100.83.192.30`**

```bash
# Test kết nối
ping 100.83.192.30
curl http://100.83.192.30:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026"
```

**Ưu điểm**: Không cần cấu hình firewall, hoạt động từ mọi nơi có internet.

---

### Phương thức B: Cùng mạng LAN

> Khi client và server cùng mạng nội bộ công ty/văn phòng.

```bash
# Tìm IP LAN của server (chạy trên server):
ip -4 addr show | grep -v '127.0.0.1\|tailscale' | grep 'inet '

# Test từ client:
curl http://<LAN_IP>:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026"
```

---

### Phương thức C: SSH Tunnel

> Khi không có Tailscale và không cùng LAN. Tạo tunnel qua SSH.

```bash
# Chạy trên máy client — mở tunnel (Port 8090: Gateway, Port 8004: Direct vLLM primary):
ssh -N -L 8090:localhost:8090 -L 8004:localhost:8004 vvc@<SERVER_IP>

# Sau đó dùng localhost:
curl http://localhost:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026"

# Ghi chú: Port 8004 là direct vLLM primary (qwen-local-primary). Port 8003 (vLLM fallback) hiện đang inactive/offline.
```

> 💡 Thêm `-f` để chạy nền: `ssh -fN -L 8090:localhost:8090 vvc@<SERVER_IP>`

---

## Bước 2: Cấu Hình Project

### 2.1 — File `.env`

Copy file `.env.ai-gateway` (đã cung cấp sẵn) vào project, hoặc thêm các biến sau:

```env
# === AI Gateway Connection ===
# Chọn 1 trong các SERVER_IP phù hợp:
#   Tailscale:  100.83.192.30
#   LAN:        <LAN_IP>
#   SSH Tunnel: localhost
# Ghi chú: `sk-spark-secure-key-2026` là master key mặc định cho $LITELLM_MASTER_KEY / $AI_GATEWAY_KEY

AI_GATEWAY_URL=http://100.83.192.30:8090/v1
AI_GATEWAY_KEY=sk-spark-secure-key-2026
AI_GATEWAY_TIMEOUT=60.0

# Nếu project dùng OpenAI SDK convention:
OPENAI_API_BASE=http://100.83.192.30:8090/v1
OPENAI_API_KEY=sk-spark-secure-key-2026

# Model mặc định (4 Archetypes chuẩn)
AI_MODEL=gemini-3.7-flash
```

### 2.2 — 4 Model Archetypes Chuẩn

| Archetype | Model Aliases | Target Backend | Khi nào sử dụng? |
| :--- | :--- | :--- | :--- |
| **1. OCR & Vision Ingestion** | `ocr-primary`<br>`ocr-fallback`<br>`ocr-tier4` | Google AI Studio Direct (10 keys) | Xử lý OCR tài liệu PDF, bản vẽ, hình ảnh, trích xuất text bảng biểu. |
| **2. Standard General / Coding** | `gemini-3.7-flash`<br>`gemini-3.7-flash-medium`<br>`text-gemma` | Google API + Centralized Proxy | Chat tổng quát, code sinh tự động, tóm tắt bài viết, đàm thoại agent. |
| **3. Deep Reasoning / Complex Audit** | `gemini-3.7-flash-high`<br>`claude-sonnet-4-6-thinking`<br>`reasoning-gemma` | Google API + Centralized Proxy | Phân tích điều khoản hợp đồng phức tạp, đối soát pháp lý, suy luận đa bước. |
| **4. Local Private / Zero-Cost** | `rag-core`<br>`qwen-local-primary` | vLLM Qwen 35B Local (GPU DGX) | Chạy offline, dữ liệu tuyệt mật nội bộ, fallback chốt chặn khi mất Internet. |

> 💡 **Tất cả models dùng chung 1 endpoint.** Chỉ cần thay `model` name.

---

## Bước 3: Tích Hợp Vào Code

### Python (`ccba-ai` Package — Khuyến nghị)

```python
from ccba_ai import ai, ModelArchetype, chat_with_metadata, CircuitBreaker

# 1. Chat cơ bản (mặc định timeout=60s, strip_thinking=True)
response = ai.chat("Giải thích REST API trong 3 câu", model=ModelArchetype.STANDARD)
print(response)

# 2. Deep reasoning (Tự động cấp phát max_tokens=16384 và lọc sạch thẻ <think>)
response = ai.chat("Phân tích điều khoản hợp đồng", model=ModelArchetype.REASONING)
print(response)

# 3. Trích xuất Telemetry (Token Usage, Latency & Model Resolution)
result = ai.chat_with_metadata("Audit xung đột thiết kế", model=ModelArchetype.REASONING)
print(f"Latency: {result.latency_ms}ms | Tokens: {result.usage.total_tokens}")

# 4. Resilience: Fast-Fail Circuit Breaker khi rớt mạng Tailscale
ai.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
```

### Python (OpenAI SDK trực tiếp)

```bash
pip install openai python-dotenv
```

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1"),
    api_key=os.environ.get("AI_GATEWAY_KEY", "sk-spark-secure-key-2026"),
    timeout=60.0,  # Bắt buộc: >= 30s - 60s
)

# --- Chat đơn giản ---
response = client.chat.completions.create(
    model="gemini-3.7-flash",
    messages=[{"role": "user", "content": "Giải thích REST API trong 3 câu"}],
    max_tokens=512,
    temperature=0.7,
)
print(response.choices[0].message.content)

# --- Streaming ---
stream = client.chat.completions.create(
    model="gemini-3.7-flash",
    messages=[{"role": "user", "content": "Viết hàm quicksort bằng Python"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# --- Deep reasoning ---
response = client.chat.completions.create(
    model="gemini-3.7-flash-high",
    messages=[
        {"role": "system", "content": "You are an expert auditor."},
        {"role": "user", "content": "Review this contract clause: ..."},
    ],
    max_tokens=4096,
)
```

### Node.js / TypeScript

```bash
npm install openai dotenv
```

```javascript
// ai-client.js
import OpenAI from 'openai';
import 'dotenv/config';

const client = new OpenAI({
  baseURL: process.env.AI_GATEWAY_URL,
  apiKey: process.env.AI_GATEWAY_KEY,
  timeout: 120000, // Best practice: 120s timeout cho proxy
});

// Chat
async function chat(message, model = 'qwen-local-primary') {
  const response = await client.chat.completions.create({
    model,
    messages: [{ role: 'user', content: message }],
    max_tokens: 1024,
  });
  return response.choices[0].message.content;
}

// Streaming
async function chatStream(message, model = 'gemini-3-flash') {
  const stream = await client.chat.completions.create({
    model,
    messages: [{ role: 'user', content: message }],
    stream: true,
  });
  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

export { client, chat, chatStream };
```

### C# / .NET

```bash
dotnet add package Azure.AI.OpenAI --prerelease
# hoặc
dotnet add package OpenAI
```

```csharp
using OpenAI;
using OpenAI.Chat;

var client = new ChatClient(
    model: "qwen-local-primary",
    credential: new ApiKeyCredential("sk-spark-secure-key-2026"),
    options: new OpenAIClientOptions
    {
        Endpoint = new Uri("http://100.83.192.30:8090/v1")
    }
);

ChatCompletion completion = await client.CompleteChatAsync("Xin chào!");
Console.WriteLine(completion.Content[0].Text);
```

### cURL (Test nhanh)

```bash
# Kiểm tra gateway hoạt động
curl http://100.83.192.30:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026"

# Chat với Qwen 35B local
curl http://100.83.192.30:8090/v1/chat/completions \
  -H "Authorization: Bearer sk-spark-secure-key-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-local-primary",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 256
  }'

# Streaming
curl http://100.83.192.30:8090/v1/chat/completions \
  -H "Authorization: Bearer sk-spark-secure-key-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-local-primary",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

---

## Bước 4: Verify Kết Nối

Chạy script test (đã cung cấp sẵn trong repo):

```bash
# Chạy script test từ repository:
bash examples/client-setup/test-connection.sh

# Hoặc nếu ở máy remote khác, copy script qua SCP rồi chạy:
# scp vvc@<SERVER_IP>:/home/vvc/Codebase/dgx-spark-toolkit/examples/client-setup/test-connection.sh .
# bash test-connection.sh
```

Hoặc tự test:

```bash
# 1. Test connectivity & health (LiteLLM yêu cầu Bearer key khi master key active)
curl -s http://100.83.192.30:8090/health -H "Authorization: Bearer sk-spark-secure-key-2026" | python3 -m json.tool

# 2. List models
curl -s http://100.83.192.30:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026" | python3 -m json.tool

# 3. Test Qwen 35B local
curl -s http://100.83.192.30:8090/v1/chat/completions \
  -H "Authorization: Bearer sk-spark-secure-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-local-primary","messages":[{"role":"user","content":"Say hello in Vietnamese"}],"max_tokens":50}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## Xử Lý Sự Cố

| Vấn đề | Giải pháp |
|--------|-----------|
| `Connection refused` | Kiểm tra Tailscale/VPN, hoặc dùng SSH tunnel |
| `401 Unauthorized` | Sai API key — kiểm tra `AI_GATEWAY_KEY` |
| `Model not found` | Kiểm tra tên model chính xác bằng `/v1/models` |
| `504 Gateway Timeout` | Model đang load, chờ 2-3 phút rồi thử lại |
| `Rate limit` | Gateway tự retry + fallback, tăng `timeout` nếu cần |
| Qwen 35B chậm | Giảm `max_tokens`, hoặc dùng `rag-light` (Qwen 3.5 9B / fallback routing) cho task nhẹ |

---

## Lưu Ý Bảo Mật

1. **KHÔNG commit API key** vào git — thêm `.env` vào `.gitignore`
2. **Dùng Tailscale** thay vì expose port ra public internet
3. **Mỗi project** nên có `.env` riêng, không hardcode IP/key trong code
4. Nếu cần revoke key, thay đổi `LITELLM_MASTER_KEY` trên server và restart gateway
