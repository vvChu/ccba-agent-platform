# Configuration

Configure mdconvert using environment variables or `.env` file.

## Environment Variables

### AI Gateway (Primary)

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_GATEWAY_URL` | AI Gateway URL (Server Spark) | `http://100.83.192.30:8090/v1` |
| `AI_GATEWAY_KEY` | AI Gateway API key | — |

### mdconverter Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MDCONVERT_MAX_OUTPUT_TOKENS` | Max tokens for LLM output | 65536 |
| `MDCONVERT_TIMEOUT_SECONDS` | Request timeout | 600 |
| `MDCONVERT_TEMPERATURE` | LLM temperature | 0.1 |
| `MDCONVERT_MIN_CONTENT_LENGTH` | Min output length | 100 |
| `MDCONVERT_HIGH_QUALITY_THRESHOLD` | Quality score threshold | 95 |
| `MDCONVERT_LLAMA_CLOUD_API_KEY` | LlamaCloud API key (optional) | None |

## .env File

Create a `.env` file in your project root:

```bash
# AI Gateway
AI_GATEWAY_URL=http://100.83.192.30:8090/v1
AI_GATEWAY_KEY=your-key-here

# Conversion Settings
MDCONVERT_MAX_OUTPUT_TOKENS=65536
MDCONVERT_TIMEOUT_SECONDS=600
```

## View Current Config

```bash
mdconvert config show
```

## Model Fallback Chain

The converter tries models in this order via AI Gateway:

1. `qwen3.5-35b` — Local GPU (private, fast)
2. `gemini-3-flash` — Cloud (multimodal)
3. `claude-sonnet-4-6` — Cloud (best coding)
4. `gemini-3.1-pro` — Cloud (1M context)

If one fails, it automatically falls back to the next.
