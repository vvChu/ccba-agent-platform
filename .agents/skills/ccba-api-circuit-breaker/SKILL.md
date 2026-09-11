---
name: ccba-api-circuit-breaker
description: Rate limiter + Circuit Breaker pattern cho LLM API calls trong batch
  pipelines. Tránh quota exhaustion, cascade failures, và infinite retry loops khi
  gọi AI Gateway hàng loạt.
version: 1.2.0
applies_to:
- Phần mềm
- Kiểm định
bundle: _core
dependencies:
- ccba-ai-gateway-sdk
gpi:
  s: 3.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- circuit breaker
- rate limit
- rpm
- throttle
- batch api
- api protection
- quota
- retry
---
# API Circuit Breaker

Rate limiter + Circuit Breaker 3-trạng-thái cho LLM API calls. Thiết kế cho các pipeline gọi AI Gateway **hàng loạt** (batch QC, wiki healing, domain enrichment).

> **Nguồn**: VvC Wiki Health v7.4 (2026) — giải quyết lỗi quota exhaustion khi wiki healer gọi LLM cho 300+ concept stubs liên tiếp không throttle.

---

## Kiến trúc & Triển khai

Mã nguồn triển khai chi tiết của lớp `CircuitBreaker` được tách biệt hoàn toàn ra tệp tin mô-đun:
👉 **Mã nguồn:** [circuit_breaker.py](resources/circuit_breaker.py)

Kỹ sư hoặc Agent tại dự án Spoke có thể dễ dàng import và sử dụng trực tiếp:
```python
from resources.circuit_breaker import CircuitBreaker, CircuitState
```

---

## Cách sử dụng trong CCBA Batch Pipeline

```python
from ccba_ai import ai
from resources.circuit_breaker import CircuitBreaker

# Khởi tạo 1 lần duy nhất dùng chung cho toàn bộ luồng lặp
breaker = CircuitBreaker(
    rpm_limit=20,           # Giới hạn 20 Requests Per Minute
    backoff_seconds=3.0,    # Chờ 3s sau mỗi lỗi
    failure_threshold=3,    # 3 lỗi liên tiếp -> OPEN circuit
    recovery_timeout=30.0   # Chuyển HALF_OPEN sau 30s
)

def audit_drawing(drawing_text: str) -> dict | None:
    """Audit 1 bản vẽ — có circuit breaker bảo vệ."""
    return breaker.call(
        lambda: ai.chat(
            f"Audit bản vẽ sau: {drawing_text}",
            model="qwen-local-primary"
        )
    )

# Batch processing loop
results = []
skipped = 0
for drawing in drawings:
    result = audit_drawing(drawing.text)
    if result is None:
        skipped += 1
        # Trạng thái lỗi JSON được tự động in ra stderr để LLM Agent tự phục hồi
    else:
        results.append(result)
```

---

## Tự động kiểm soát và sửa lỗi (Self-Healing)

Khi Circuit Breaker ngăn chặn các API requests hoặc gặp lỗi API, nó không im lặng bỏ qua mà tự động xuất ra luồng `stderr` cấu trúc phản hồi lỗi JSON chuẩn hóa:
```json
{
  "status": "error",
  "error_code": "CIRCUIT_BREAKER_OPEN",
  "message": "Circuit Breaker is OPEN due to 3 consecutive failures. Request blocked.",
  "recovery_suggestion": "Wait for recovery timeout (30.0s) before trying again or check backend service status."
}
```
LLM Agents hoặc debugger tự động (`mock-debugger`) có thể parse trực tiếp JSON này để:
1. Đọc trường `recovery_suggestion` để biết cách xử lý tiếp theo.
2. Tự động chuyển đổi model LLM dự phòng hoặc trì hoãn/tắt luồng an toàn.

---

## Rejected Items Caching (Infinite Retry Prevention)

Tránh việc retry vô tận ở các lượt chạy sau bằng cơ chế cache lại các item bị lỗi:
```python
from resources.circuit_breaker import CircuitBreaker, load_rejected_cache, cache_rejected

breaker = CircuitBreaker()
rejected_cache = load_rejected_cache()

for item in items:
    if item.id in rejected_cache:
        continue  # Skip không gọi API nữa
        
    result = breaker.call(lambda: process(item))
    if result is None:
        cache_rejected(item.id) # Ghi nhận vào file cache tạm
```

---

## Sơ đồ Trạng thái (3-State Diagram)

```
          success (HALF_OPEN)
    ┌────────────────────────────────┐
    │                                ▼
[CLOSED] ──fail×N──► [OPEN] ──30s──► [HALF_OPEN]
    ▲                                    │
    └────────── success ─────────────────┘
                         fail → back to OPEN
```
