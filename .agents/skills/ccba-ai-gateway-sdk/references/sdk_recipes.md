# CCBA AI Gateway SDK — Code Recipes & Output Sanitization Reference

Tài liệu tham chiếu Level 3 cho `ccba-ai-gateway-sdk`, chứa các đoạn code mẫu về Telemetry (`chat_with_metadata`), XML Prompt Envelopes, `evaluator_optimizer_loop`, Reasoning Models và 5 bước làm sạch output LLM.

## 1. Python SDK Recipes (`ccba_ai`)

```python
from ccba_ai import ai, async_ai, ModelArchetype, choose_model, chat_with_metadata

# 1. Chat cơ bản (mặc định timeout=90.0s, strip_thinking=True)
response = ai.chat(
    "Tóm tắt các điểm chính trong tài liệu đính kèm...",
    model=ModelArchetype.STANDARD
)

# 2. Deep reasoning (Tự động cấp phát max_tokens=16384 và tự làm sạch thẻ <think>)
deep_res = ai.chat(
    "Phân tích xung đột giữa Điều 12 và Điều 18 của dự thảo...",
    model=ModelArchetype.REASONING
)

# 3. Đo lường Telemetry, Token Usage & Độ trễ (ChatResult)
res = ai.chat_with_metadata("Kiểm tra pháp lý hợp đồng...", model=ModelArchetype.REASONING)
print(res.content, res.model, res.usage.total_tokens, res.latency_ms)

# 4. Định tuyến tự động theo task (Seam model_routing.v1)
model_name = choose_model("ocr")
```

## 2. Prompt Engineering & Evaluator-Optimizer Loop

```python
from ccba_ai import ai, choose_model, evaluator_optimizer_loop, parse_xml_tags, xml_envelope

envelope_prompt = xml_envelope({
    "instructions": "Soạn thảo văn bản thẩm tra PCCC theo chuẩn Nghị định 105/2025",
    "context": {"decree": "105/2025/NĐ-CP", "standard": "QCVN 06:2022/BXD"},
    "documents": ["Nội dung thuyết minh thiết kế công trình..."],
})
response = ai.chat(envelope_prompt, model=choose_model("reasoning"))
tags = parse_xml_tags(response)

result = evaluator_optimizer_loop(
    generator_fn=lambda fb: ai.chat(f"Soạn thảo tài liệu. Phản hồi vòng trước: {fb}"),
    evaluator_fn=lambda draft: (95.0, "Đạt") if "105/2025" in draft else (60.0, "Bổ sung viện dẫn NĐ 105/2025"),
    max_iterations=3,
    pass_score=85.0,
)
```

### Custom Local Fast-Fail `CircuitBreaker`

```python
from ccba_ai import ai, CircuitBreaker

ai.circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=15.0)
```

## 3. Reasoning Models (`<think>...</think>`) & Output Cleaning (5 Bước)

- **Auto Max-Tokens:** Tự động nâng lên `16,384` tokens khi gọi reasoning model (`gemini-3.8-flash-high`, `claude-sonnet-4-6-thinking`, `reasoning-gemma`, `qwen-local-primary`).
- **Auto Strip Thinking (`strip_thinking=True`):** Mặc định tự động lọc `<think>...</think>`; dùng `strip_thinking=False` nếu cần chuỗi suy luận thô. Đặt `temperature=0.0` hoặc `0.1` khi xuất JSON.
- **Nên dùng Reasoning** cho đối chiếu pháp lý/PCCC/code quy mô lớn; **không dùng** cho NER đơn giản hoặc task cần phản hồi < 2s.

### Output Sanitization Pipeline (VvC v7.4+)

```python
import json
import re

_THINK_PATTERN  = re.compile(r"<think>.*?</think>\n*", re.DOTALL | re.IGNORECASE)
_THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
_ORPHAN_END     = re.compile(r"^.*?</think>\n*", re.DOTALL | re.IGNORECASE)

def strip_think_tags(text: str) -> str:
    """Strip toàn bộ <think>...</think> blocks khỏi LLM output."""
    text = _THINK_PATTERN.sub("", text)
    text = _THINK_UNCLOSED.sub("", text)
    return _ORPHAN_END.sub("", text).strip()

def extract_json(raw: str) -> dict | None:
    """Extract JSON từ LLM output, xử lý cả raw JSON và markdown fence."""
    clean = strip_think_tags(raw)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, flags=re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
    return json.loads(match.group(0)) if match else None

def is_valid_output(text: str, min_chars: int = 10) -> bool:
    """Kiểm tra output LLM không phải timeout error hay rỗng."""
    stripped = text.strip() if text else ""
    return len(stripped) >= min_chars and not stripped.startswith("Error connecting")

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
    """True nếu fetched content là JS/Cloudflare error page."""
    if len(text.strip()) < min_chars:
        return True
    text_lower = text.lower()
    return sum(1 for p in _GARBAGE_PATTERNS if re.search(p, text_lower)) >= 2

def remove_ocr_artifacts(text: str) -> str:
    """Loại bỏ dòng ALL-CAPS dài (>15 chars) từ header/footer OCR."""
    return re.sub(r'^[A-ZÀ-Ỹ][A-ZÀ-Ỹ\s_]{14,}\.?\s*$', '', text, flags=re.MULTILINE).strip()
```

## 4. Quick Test (`curl`)

```bash
curl http://${CCBA_AI_GATEWAY_HOST}:8090/v1/models -H "Authorization: Bearer <YOUR_AI_GATEWAY_KEY>"
curl http://${CCBA_AI_GATEWAY_HOST}:8090/health
```
