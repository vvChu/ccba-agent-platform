# LLM API Integration Guide

## AI Gateway (Recommended — 44 Models)

All AI access should go through the **AI Gateway** for unified routing, fallbacks, and cloud model support.

### Gateway Endpoint

```
http://localhost:8090/v1          (local)
http://100.83.192.30:8090/v1     (remote via Tailscale)
Authorization: Bearer $LITELLM_MASTER_KEY
```

### Quick Test

```bash
curl http://localhost:8090/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4-6-thinking", "messages": [{"role": "user", "content": "Hello!"}]}'
```

---

## Available Models

### 🖥️ Local GPU — Private / Offline
| Model | Description |
|-------|-------------|
| `qwen-local-primary` | Floating role alias for main local GPU model (Qwen 3.5 35B FP8) |
| `qwen-3.5-35b` | Version-specific alias for Qwen 3.5 35B |
| `rag-core` | Alias of `qwen-local-primary` (RAG pipeline) |
| `rag-light` | Qwen 3.5 9B / fallback routing — lightweight fallback |

> 💡 **Cấu hình Động & Kiểm định Tự động**:
> - Tên model và đường dẫn trọng số được quản lý động qua file `.env` (`LOCAL_PRIMARY_LLM_DIR`, `LOCAL_PRIMARY_SERVED_NAME`).
> - Chạy kiểm định tự động tính khớp giữa đĩa và AI Gateway: `python3 scripts/verify_local_model_integrity.py`
>
> ⚠️ **Warning**: Do NOT use legacy unmapped aliases like `qwen3.5-35b` or `Qwen-3.6-35B-NVFP4`. Use `qwen-local-primary` (or `qwen-3.5-35b`) instead.

### 🏎️ Speed Tier (< 1.5s)
| Model | Latency | Best For |
|-------|---------|----------|
| `gemini-3.5-flash-low` ⚡ | **0.66s** | Ultra-fast text completion & summarization |
| `gemini-3-flash` | **0.96s** | Fast multimodal + reasoning |
| `gemini-3.6-flash-low` | **1.11s** | High-speed structured extraction |
| `gemini-3.1-flash-lite` | **1.22s** | Cheapest & fastest Gemini (OCR primary) |
| `gemini-3.5-flash-lite` | **1.35s** | Backup lightweight Flash model |
| `claude-haiku-4` | **1.40s** | Fast Claude |
| `claude-haiku-4-5` | **1.45s** | Faster Claude, better quality |

### 🖼️ Image Generation Tier
| Model | Endpoint | Description |
|-------|----------|-------------|
| `gemini-3-pro-image` | `/v1/images/generations` | High-quality image generation via Imagen/Gemini |
| `gemini-3.1-flash-image` | `/v1/images/generations` | Fast image generation & editing |

### 🛠️ RAG Virtual Aliases (Free Tier Farm)
Mô hình "ảo" (Alias) được Gateway tự động định tuyến để tận dụng Quota Free của Google & Proxy Gateway.
| Alias / Bí Danh | Model Thật (Backend) | Công Dụng (Best For) | Quota & Routing Policy |
|-------|----------|----------|----------|
| `ocr-primary` | Gemini 3.1 Flash Lite | Cloud OCR Vision (Backup: `ocr-fallback` gemini-3.5-flash-lite) | **10 Keys x 500 RPD** |
| `ocr-fallback` | Gemini 3.5 Flash Lite | OCR Secondary Backup | **10 Keys x 500 RPD** |
| `text-gemma` | Gemma 3 27B | High-volume NLP (Sinh câu hỏi, Summarize) | **144,000 req/ngày** |
| `text-light-gemma` | Gemma 3 12B | Bóc tách siêu dữ liệu (Metadata, Tagging) | **144,000 req/ngày** |
| `reasoning-gemma` | Gemma 4 31B | Logical Graph (Neo4j), Structured JSON | **15,000 req/ngày** |

### 🧠 Balanced Tier (1–3s)
| Model | Best For |
|-------|----------|
| `claude-sonnet-4-6` ⭐ | Coding, agentic pipelines |
| `claude-sonnet-4-5` | Previous gen Sonnet |
| `claude-sonnet-4-6-thinking` | Reasoning with CoT |
| `claude-sonnet-4-5-thinking` | Reasoning (previous gen) |
| `claude-opus-4-6` | Deep analysis, legal/financial |
| `claude-opus-4-5` | Previous gen Opus |
| `claude-opus-4-6-thinking` | Opus + chain-of-thought |
| `claude-opus-4-5-thinking` | Previous gen Opus + CoT |
| `gpt-oss-120b-medium` | Large OSS model via proxy |

### 🔬 Deep Reasoning (7–13s, 1M context)
| Model | Best For |
|-------|----------|
| `gemini-3.6-flash-high` | High-reasoning Flash model |
| `gemini-3.1-pro` | Full codebase analysis, research |
| `gemini-3.1-pro-high` | ARC-AGI-2, novel problems |
| `gemini-3.1-pro-low` | Cost-efficient Gemini Pro |
| `gemini-3-pro-high` | Scientific reasoning |
| `gemini-3-pro-low` | Budget deep reasoning |

---

## Python Integration

```python
from openai import OpenAI

# Via Gateway (recommended — all models + fallbacks)
client = OpenAI(
    base_url="http://localhost:8090/v1",
    api_key=os.environ["LITELLM_MASTER_KEY"]
)

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=1024
)
print(response.choices[0].message.content)
```

---

## Direct vLLM (Local Models Only)

Use only when you need raw vLLM access without gateway routing:

- **Port 8004 (Active)**: Direct vLLM primary serving `qwen-local-primary` (and `rag-core`).
- **Port 8003 (Inactive)**: vLLM fallback instance (currently offline).

```bash
# Qwen 35B Direct vLLM Primary (port 8004)
curl http://localhost:8004/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-local-primary", "messages": [{"role": "user", "content": "Hello!"}]}'
```

> ⚠️ Direct vLLM access has no fallbacks and no cloud models. Prefer the gateway.

---

## Remote Access (Máy Khác)

Để sử dụng Gateway từ máy khác, xem:
- **Hướng dẫn chi tiết**: [`client-setup-guide.md`](./client-setup-guide.md)
- **Files cấu hình sẵn**: [`examples/client-setup/`](../examples/client-setup/)
- **Test kết nối**: `bash examples/client-setup/test-connection.sh`
