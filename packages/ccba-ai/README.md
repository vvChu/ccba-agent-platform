# ccba-ai — CCBA AI Gateway Client & Resilience Engine

Kết nối AI Gateway trên Server Spark — **Đa mô hình (local GPU + cloud), 1 endpoint**, tích hợp **Multi-Tier Failover Matrix** và **Deterministic Mock Provider**.

---

## Cài đặt

```bash
# 1. Cài đặt cơ bản cho Spoke (AI Gateway Client, chat, stream — không phụ thuộc ccba-harness)
pip install -e "D:\GitHubProjects\ccba-agent-platform\packages\ccba-ai"

# 2. Cài đặt đầy đủ tính năng quản lý Plan/Team với FileMutexLock cấp cao
pip install -e "D:\GitHubProjects\ccba-agent-platform\packages\ccba-harness"
pip install -e "D:\GitHubProjects\ccba-agent-platform\packages\ccba-ai"

# Hoặc thiết lập tự động hóa toàn bộ packages qua Spoke Bootstrap:
python scripts/spoke/spoke_bootstrap.py
```

---

## 5 Tầng Chuyển vùng Dự phòng (Multi-Tier Failover Matrix)

`ccba-ai` được trang bị sẵn cơ chế chuyển vùng dự phòng tự động (Automated Failover Cascade) khi gặp lỗi kết nối hoặc Circuit Breaker mở:

```
Tier 1 (Server Spark :8090) ──► Tier 2 (Cloud Direct API) ──► Tier 3 (Dual-CLI: Copilot & Antigravity) ──► Tier 4 (Local Ollama :11434) ──► Tier 5 (Deterministic Mock)
```

1. **Tier 1 (Default):** LiteLLM Server Spark (`http://100.83.192.30:8090/v1`).
2. **Tier 2 (Cloud Direct Fallback):** Tự động phát hiện các biến môi trường `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY` để gọi trực tiếp tới Cloud Provider khi Server Spark bảo trì.
3. **Tier 3 (Dual-CLI Provider Matrix & Persistent Daemon Bridge):** Zero-config fallback qua GitHub Copilot CLI (`copilot.exe` — GPT-5.4 / GPT-5.4-mini / Claude) và Antigravity CLI (`agy.exe` — Gemini 3.7 Flash). Tự động điều phối theo Model-Family Affinity, hỗ trợ Cross-CLI Failover, và tích hợp Persistent Stdio Daemon Bridge giúp giảm độ trễ từ ~41s xuống ~2.6s/call [đo thực tế].
4. **Tier 4 (Local Offline LLM):** Tự động kết nối tới Ollama cục bộ (`http://127.0.0.1:11434/v1`) với model nhẹ (`qwen2.5-coder:7b`, `phi-4-mini`) khi làm việc ngoại tuyến (Air-gapped).
5. **Tier 5 (Deterministic Mock Provider):** Giả lập in-memory hoàn toàn không qua mạng, phục vụ Unit Test và No-Network CI khi đặt `CCBA_AI_MOCK=1`.

---

## Cách dùng Cơ bản

```python
from ccba_ai import ai

# 1. Chat đơn giản (tự động chuyển vùng nếu mất mạng Spark)
reply = ai.chat("Xin chào!")

# 2. Chọn model archetype hoặc tên cụ thể
reply = ai.chat("Review code này", model="claude-sonnet-4-6")

# 3. Chat kèm metadata (đo latency và token usage)
result = ai.chat_with_metadata("Thẩm tra hồ sơ", model="gemini-3.7-flash")
print(f"Content: {result.content}, Latency: {result.latency_ms}ms, Usage: {result.usage}")

# 4. Streaming
for chunk in ai.stream("Viết hàm quicksort bằng Python"):
    print(chunk, end="")

# 5. Multi-turn conversation
reply = ai.chat_multi([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What's 2+2?"},
])

# 6. Xem danh sách models khả dụng
models = ai.models()
```

---

## Sử dụng Mock Provider trong Unit Test & CI

Để chạy toàn bộ ứng dụng hoặc test suite offline độc lập:

```python
from ccba_ai import AIClient, MockProvider

# Khởi tạo client ở chế độ Mock
client = AIClient(mock_mode=True)

# Đăng ký pattern phản hồi tùy chỉnh cho test cases
client.mock_provider.register_pattern("kiểm tra pccc", "Đạt chuẩn QCVN 06:2022")
assert client.chat("Yêu cầu kiểm tra PCCC") == "Đạt chuẩn QCVN 06:2022"
```

Hoặc kích hoạt toàn cục qua biến môi trường:
```bash
export CCBA_AI_MOCK=1
pytest packages/ccba-ai/tests
```

---

## Cấu hình Biến Môi trường

```env
# Tier 1 (Server Spark)
AI_GATEWAY_URL=http://100.83.192.30:8090/v1
AI_GATEWAY_KEY=sk-spark-secure-key-2026
AI_MODEL=qwen-local-primary
AI_GATEWAY_TIMEOUT=60.0

# Tier 2 (Cloud Direct Fallback - tùy chọn)
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key

# Tier 3 (Local Ollama - tùy chọn)
OLLAMA_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=qwen2.5-coder:7b

# Tier 4 (Mock Engine)
CCBA_AI_MOCK=0
```

---

## Prompting Helpers & Evaluator-Optimizer Loop

```python
from ccba_ai import xml_envelope, parse_xml_tags, evaluator_optimizer_loop

# 1. Đóng gói XML Envelopes
prompt = xml_envelope({
    "instructions": "Soạn thảo văn bản thẩm tra thiết kế PCCC",
    "context": {"decree": "105/2025/NĐ-CP", "standard": "QCVN 06:2022/BXD"},
})

# 2. Vòng lặp Generator <-> Evaluator tự sửa lỗi
result = evaluator_optimizer_loop(
    generator_fn=lambda fb: ai.chat(f"Draft document with feedback: {fb}"),
    evaluator_fn=lambda draft: (90.0, "Đạt yêu cầu") if "105/2025" in draft else (60.0, "Thiếu viện dẫn NĐ 105/2025"),
    max_iterations=3,
    pass_score=85.0,
)
print(f"Passed: {result.passed} in {result.iterations} iterations")
```
