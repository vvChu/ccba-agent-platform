# Hướng Dẫn Cài Đặt Client — Kết Nối AI Gateway từ Máy Khác

> **Server**: DGX Spark (`spark-CCBA`)
> **Gateway**: LiteLLM AI Gateway — 22 models (Claude, Gemini, GPT, Qwen local)
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
│              ├── Qwen 3.6 35B (:8004) (local GPU)            │
│              ├── Qwen 3.5 9B  (:8003) (local GPU, fallback)  │
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
# Chạy trên máy client — mở tunnel:
ssh -N -L 8090:localhost:8090 -L 8004:localhost:8004 vvc@<SERVER_IP>

# Sau đó dùng localhost:
curl http://localhost:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026"
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

AI_GATEWAY_URL=http://100.83.192.30:8090/v1
AI_GATEWAY_KEY=sk-spark-secure-key-2026

# Nếu project dùng OpenAI SDK convention:
OPENAI_API_BASE=http://100.83.192.30:8090/v1
OPENAI_API_KEY=sk-spark-secure-key-2026

# Model mặc định (tùy chọn)
AI_MODEL=qwen3.5-35b
```

### 2.2 — Danh Sách Models Có Sẵn

| Tier | Model Name | Mô Tả |
|------|-----------|--------|
| 🖥️ **Local GPU** | `qwen3.5-35b` | Qwen 35B — private, offline, nhanh |
| 🖥️ **Local GPU** | `rag-core` | Alias của qwen3.5-35b (dùng trong RAG) |
| 🖥️ **Local GPU** | `rag-light` | Qwen 4B — nhẹ, nhanh hơn |
| ☁️ **Cloud** | `claude-sonnet-4-6` | ⭐ Best coding/agentic |
| ☁️ **Cloud** | `claude-sonnet-4-6-thinking` | Claude + Chain-of-Thought |
| ☁️ **Cloud** | `claude-opus-4-6` | Claude mạnh nhất |
| ☁️ **Cloud** | `claude-opus-4-5-thinking` | Deep reasoning |
| ☁️ **Cloud** | `gemini-3-flash` | Nhanh, multimodal |
| ☁️ **Cloud** | `gemini-3.1-pro` | 1M context, research |
| ☁️ **Cloud** | `gemini-3.1-pro-high` | Scientific reasoning |
| ☁️ **Cloud** | `gemini-3.1-flash-lite` | Rẻ nhất, nhanh nhất |
| ☁️ **Cloud** | `gemma-3-27b` | Free tier, metadata |
| ☁️ **Cloud** | `gpt-oss-120b-medium` | OpenAI OSS model |

> 💡 **Tất cả models dùng chung 1 endpoint.** Chỉ cần thay `model` name.

---

## Bước 3: Tích Hợp Vào Code

### Python (OpenAI SDK)

```bash
pip install openai python-dotenv
```

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["AI_GATEWAY_URL"],
    api_key=os.environ["AI_GATEWAY_KEY"],
)

# --- Chat đơn giản ---
response = client.chat.completions.create(
    model="qwen3.5-35b",
    messages=[{"role": "user", "content": "Giải thích REST API trong 3 câu"}],
    max_tokens=512,
    temperature=0.7,
)
print(response.choices[0].message.content)

# --- Streaming ---
stream = client.chat.completions.create(
    model="gemini-3-flash",
    messages=[{"role": "user", "content": "Viết hàm quicksort bằng Python"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# --- Dùng Claude cho coding ---
response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[
        {"role": "system", "content": "You are an expert Python developer."},
        {"role": "user", "content": "Review this code and suggest improvements: ..."},
    ],
    max_tokens=2048,
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
});

// Chat
async function chat(message, model = 'qwen3.5-35b') {
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
    model: "qwen3.5-35b",
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
    "model": "qwen3.5-35b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 256
  }'

# Streaming
curl http://100.83.192.30:8090/v1/chat/completions \
  -H "Authorization: Bearer sk-spark-secure-key-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5-35b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

---

## Bước 4: Verify Kết Nối

Chạy script test (đã cung cấp sẵn):

```bash
# Download script test
curl -O http://100.83.192.30:8005/static/test-gateway.sh
# hoặc copy từ server:
# scp vvc@<SERVER_IP>:/home/vvc/Codebase/dgx-spark-toolkit/examples/client-setup/test-connection.sh .

bash test-connection.sh
```

Hoặc tự test:

```bash
# 1. Test connectivity
curl -s http://100.83.192.30:8090/health | python3 -m json.tool

# 2. List models
curl -s http://100.83.192.30:8090/v1/models \
  -H "Authorization: Bearer sk-spark-secure-key-2026" | python3 -m json.tool

# 3. Test Qwen 35B local
curl -s http://100.83.192.30:8090/v1/chat/completions \
  -H "Authorization: Bearer sk-spark-secure-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.5-35b","messages":[{"role":"user","content":"Say hello in Vietnamese"}],"max_tokens":50}' \
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
| Qwen 35B chậm | Giảm `max_tokens`, hoặc dùng `rag-light` (4B) cho task nhẹ |

---

## Lưu Ý Bảo Mật

1. **KHÔNG commit API key** vào git — thêm `.env` vào `.gitignore`
2. **Dùng Tailscale** thay vì expose port ra public internet
3. **Mỗi project** nên có `.env` riêng, không hardcode IP/key trong code
4. Nếu cần revoke key, thay đổi `LITELLM_MASTER_KEY` trên server và restart gateway
