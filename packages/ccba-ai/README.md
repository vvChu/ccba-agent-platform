# ccba-ai — CCBA AI Gateway Client

Kết nối AI Gateway trên Server Spark — **22 models, 1 endpoint**.

## Cài đặt

```bash
# Editable install (recommended — thay đổi code tự update)
pip install -e "D:\GitHubProjects\ccba-agent-platform\packages\ccba-ai"

# Hoặc chỉ cần PYTHONPATH
set PYTHONPATH=D:\GitHubProjects\ccba-agent-platform\packages\ccba-ai\src;%PYTHONPATH%
```

## Cách dùng

```python
from ccba_ai import ai

# Chat đơn giản (Qwen local — mặc định)
reply = ai.chat("Xin chào!")

# Chọn model
reply = ai.chat("Review code này", model="claude-sonnet-4-6")

# System prompt
reply = ai.chat(
    "Tóm tắt văn bản này...",
    system="Bạn là chuyên gia pháp luật xây dựng Việt Nam",
    model="gemini-3.1-pro"
)

# Streaming
for chunk in ai.stream("Viết hàm quicksort bằng Python"):
    print(chunk, end="")

# Multi-turn conversation
reply = ai.chat_multi([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What's 2+2?"},
])

# Xem danh sách models
models = ai.models()
```

## Cấu hình

Qua biến môi trường hoặc file `.env`:

```env
AI_GATEWAY_URL=http://100.83.192.30:8090/v1
AI_GATEWAY_KEY=sk-spark-secure-key-2026
AI_MODEL=qwen-local-primary
```

## Models

| Tier | Model | Mô tả |
|------|-------|-------|
| 🖥️ Local | `qwen-local-primary` | Private, offline, default |
| ☁️ Smart | `claude-sonnet-4-6` ⭐ | Best coding/agentic |
| ☁️ Fast | `gemini-3.1-pro-low` | Nhanh, speed optimized |
| ☁️ Deep | `gemini-3.1-pro` | 1M context, research |

Xem đầy đủ 22 models trong SKILL.md.
