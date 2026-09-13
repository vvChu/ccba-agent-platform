---
name: ccba-api-circuit-breaker
description: Rate limiter + Circuit Breaker pattern cho LLM API calls trong batch
  pipelines. Tránh quota exhaustion, cascade failures, và infinite retry loops khi
  gọi AI Gateway hàng loạt.
applies_to:
- Phần mềm
- Kiểm định
bundle: _core
tier: kernel
command: /ccba-api-circuit-breaker
metadata:
  version: "1.3.0"
  author: "CCBA Hub"
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
- auto downgrade
- soft cooldown
---
# API Circuit Breaker

Rate limiter + Circuit Breaker 3-trạng-thái cho LLM API calls. Thiết kế cho các pipeline gọi AI Gateway **hàng loạt** (batch QC, wiki healing, domain enrichment) và các kiến trúc Multi-Endpoint tự phục hồi (Self-Healing).

> **Nguồn**: VvC Wiki Health v7.4 → LLM OS v8.15 (2026) — giải quyết lỗi quota exhaustion khi wiki healer gọi LLM cho 300+ concept stubs liên tiếp không throttle, và cơ chế Soft Cooldown tự động giáng cấp (Auto-Downgrade) khi Cổng Proxy chuyên biệt đạt giới hạn tài khoản.

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

## Multi-Endpoint Soft Cooldown & Tier 1 Auto-Downgrade Pattern

### Bối cảnh & Vấn đề
Khi một pipeline LLM tích hợp các dịch vụ reasoning chuyên biệt thông qua một Proxy trung gian hoặc Endpoint tài khoản dùng chung (ví dụ: Antigravity Tools Proxy trên Cổng 8045 cung cấp Claude Opus 4.6 Thinking / Sonnet 4.6):
- Khi pool tài khoản tạm thời cạn kiệt hoặc bị giới hạn tần suất, endpoint trả về lỗi HTTP `503 Service Unavailable` (`All accounts limited. Wait Xs.`) hoặc HTTP `429 Too Many Requests`.
- Nếu áp dụng Circuit Breaker cứng truyền thống (Hard Trip ngắt toàn bộ pipeline) $\rightarrow$ Tác vụ của người dùng bị dừng khựng (Hard Crash/Abort), gây ức chế và đình trệ quy trình.

### Giải pháp: Soft Cooldown Timer & Tier 1 Auto-Downgrade
Kết hợp cơ chế **Soft Cooldown** tạm thời với **Tự động giáng cấp xuống mô hình Tier 1** tương đương (như `gemini-3.8-flash-high` hoặc `gemini-3.1-pro` trên Cổng chính 8090):

```
                       Request (model="claude-opus-4-6-thinking")
                                       │
                         [Is in Soft Cooldown (30s)?]
                                 ├── Yes ──► [Auto-Downgrade to Gemini 3.8 Flash High (8090)]
                                 │           (was_downgraded = True)
                                 └── No
                                     │
                             Gửi tới Port 8045
                                     ├── HTTP 200 ──► Trả về kết quả (was_downgraded = False)
                                     └── HTTP 503/429
                                             │
                                             ├── Kích hoạt Cooldown: _proxy_cooldown_until = now + 30s
                                             └── [Auto-Downgrade to Gemini 3.8 Flash High (8090)]
                                                 (was_downgraded = True)
```

### Triển khai Mẫu (Architecture Seam)
```python
_proxy_cooldown_until: float = 0.0

def call_gateway_with_meta(
    prompt: str,
    *,
    model: str = "",
    timeout: int = 60,
) -> tuple[str, bool]:
    """Gọi LLM Gateway có theo dõi metadata giáng cấp (was_downgraded)."""
    global _proxy_cooldown_until

    is_proxy = _is_proxy_model(model)

    # 1. Nếu proxy đang trong thời gian Cooldown -> Tự động giáng cấp ngay lập tức
    if is_proxy and time.time() < _proxy_cooldown_until:
        remaining = int(_proxy_cooldown_until - time.time())
        logger.warning(f"Proxy port 8045 in cooldown ({remaining}s left). Auto-downgrading to fallback model...")
        return _call_fallback_gateway(prompt, timeout=timeout), True

    # 2. Thử gọi Proxy chính
    if is_proxy:
        try:
            content = _call_proxy_endpoint(prompt, model=model, timeout=timeout)
            return content, False
        except (GatewayHttp503Error, GatewayHttp429Error) as exc:
            # 3. Kích hoạt 30s Soft Cooldown và giáng cấp tức thì
            _proxy_cooldown_until = time.time() + 30.0
            logger.warning(f"Proxy 8045 limited: {exc}. Cooldown 30s set. Downgrading to Tier 1 fallback...")
            return _call_fallback_gateway(prompt, timeout=timeout), True

    # 4. Các model thông thường gọi trực tiếp endpoint chuẩn
    return _call_standard_gateway(prompt, model=model, timeout=timeout), False
```

### Transparency UI Callout Invariant
Khi cờ `was_downgraded == True`, lớp điều phối (Coordinator/UI) BẮT BUỘC chèn một Callout thông báo minh bạch ở đầu bài viết để người dùng nắm rõ lý do mô hình bị thay thế mà không gây gián đoạn luồng làm việc:

```markdown
> [!info] ℹ️ Mô hình chính đang trong thời gian hồi phục tài khoản (cooldown), hệ thống đã tự động phản hồi bằng Gemini 3.8 Flash High để bạn không phải chờ đợi.
```

### Ưu điểm Cốt Lõi
1. **Zero User Interruption**: Người dùng không bao giờ nhận lỗi 503/429 hay màn hình trắng; luôn có phản hồi trong 2-4 giây.
2. **Self-Healing Loop**: Ngay khi hết 30 giây cooldown, request tiếp theo sẽ tự động thăm dò lại Cổng 8045 mà không cần người dùng khởi động lại daemon.
3. **Auditability**: Mọi sự kiện giáng cấp đều được ghi log rõ ràng kèm lý do mã lỗi HTTP.

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
