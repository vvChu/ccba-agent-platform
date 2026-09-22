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

## Centralized Gateway (:8090) & Soft Cooldown Auto-Downgrade Pattern

### Kiến trúc Tập Trung tại Gateway Cổng :8090
Toàn bộ danh mục mô hình (kể cả Gemini Flash High, Claude Sonnet 4.6 Thinking, Claude Opus 4.6 Thinking và local Qwen) được cung cấp **tập trung tại Gateway duy nhất cổng `:8090`** trên Server Spark (`http://100.83.192.30:8090/v1`). Không còn phân tách endpoint hay proxy phụ trợ trên cổng `:8045`.

### Bối cảnh & Vấn đề
Khi một pipeline LLM gọi các mô hình reasoning chuyên biệt (như `claude-opus-4-6`, `claude-sonnet-4-6-thinking`) qua AI Gateway:
- Khi upstream provider tạm thời cạn kiệt quota hoặc bị giới hạn tần suất, gateway có thể trả về lỗi HTTP `503 Service Unavailable` hoặc HTTP `429 Too Many Requests`.
- Nếu áp dụng Circuit Breaker cứng truyền thống (ngắt toàn bộ pipeline) $\rightarrow$ Tác vụ của người dùng bị dừng khựng (Hard Crash/Abort), gây ức chế và đình trệ quy trình.

### Giải pháp: Model-Level Soft Cooldown & Auto-Downgrade
Kết hợp cơ chế **Soft Cooldown** tạm thời cho từng mô hình với **Tự động giáng cấp xuống mô hình dự phòng** tương đương (như `gemini-3.7-flash-high` hoặc `gemini-3.8-flash` ngay trên Gateway `:8090`):

```
                       Request (model="claude-opus-4-6")
                                       │
                         [Is model in Cooldown (30s)?]
                                 ├── Yes ──► [Auto-Downgrade to Gemini Flash High (:8090)]
                                 │           (was_downgraded = True)
                                 └── No
                                     │
                             Gửi tới Gateway :8090
                                     ├── HTTP 200 ──► Trả về kết quả (was_downgraded = False)
                                     └── HTTP 503/429
                                             │
                                             ├── Kích hoạt Cooldown: _model_cooldown_until[model] = now + 30s
                                             └── [Auto-Downgrade to Gemini Flash High (:8090)]
                                                 (was_downgraded = True)
```

### Triển khai Mẫu (Architecture Seam)
```python
_model_cooldown_until: dict[str, float] = {}

def call_gateway_with_meta(
    prompt: str,
    *,
    model: str = "claude-opus-4-6",
    timeout: int = 90,
) -> tuple[str, bool]:
    """Gọi LLM Gateway (:8090) có theo dõi metadata giáng cấp (was_downgraded)."""
    global _model_cooldown_until

    # 1. Nếu model đang trong thời gian Cooldown -> Tự động giáng cấp ngay lập tức
    cooldown_until = _model_cooldown_until.get(model, 0.0)
    if time.time() < cooldown_until:
        remaining = int(cooldown_until - time.time())
        logger.warning(f"Model {model} in cooldown ({remaining}s left). Auto-downgrading to fallback model...")
        return _call_fallback_gateway(prompt, timeout=timeout), True

    # 2. Thử gọi mô hình chính trên Gateway :8090
    try:
        content = _call_gateway_endpoint(prompt, model=model, timeout=timeout)
        return content, False
    except (GatewayHttp503Error, GatewayHttp429Error) as exc:
        # 3. Kích hoạt 30s Soft Cooldown và giáng cấp tức thì sang model dự phòng trên :8090
        _model_cooldown_until[model] = time.time() + 30.0
        logger.warning(f"Model {model} limited: {exc}. Cooldown 30s set. Downgrading to Tier 1 fallback...")
        return _call_fallback_gateway(prompt, timeout=timeout), True
```

### Transparency UI Callout Invariant
Khi cờ `was_downgraded == True`, lớp điều phối (Coordinator/UI) BẮT BUỘC chèn một Callout thông báo minh bạch ở đầu bài viết để người dùng nắm rõ lý do mô hình bị thay thế mà không gây gián đoạn luồng làm việc:

```markdown
> [!info] ℹ️ Mô hình chính đang trong thời gian hồi phục tài khoản (cooldown), hệ thống đã tự động phản hồi bằng Gemini Flash High để bạn không phải chờ đợi.
```

### Ưu điểm Cốt Lõi
1. **Zero User Interruption**: Người dùng không bao giờ nhận lỗi 503/429 hay màn hình trắng; luôn có phản hồi trong 2-4 giây.
2. **Self-Healing Loop**: Ngay khi hết 30 giây cooldown, request tiếp theo sẽ tự động thăm dò lại mô hình chính trên Cổng `:8090` mà không cần người dùng can thiệp thủ công.
3. **Unified Single Gateway**: Toàn bộ lưu lượng đi qua cổng duy nhất `:8090`, loại bỏ hoàn toàn việc phân mảnh proxy hoặc phụ thuộc vào port 8045.
4. **Auditability**: Mọi sự kiện giáng cấp đều được ghi log rõ ràng kèm lý do mã lỗi HTTP.

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

## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)
* **Tiêu chí hoàn thành tất định:** Mọi thay đổi mã nguồn, kỹ năng hoặc tài liệu bắt buộc phải vượt qua bộ kiểm thử tự động.
* **Hard Completion Lock:** Nghiêm cấm tuyên bố hoàn thành task hoặc yêu cầu nghiệm thu nếu lệnh xác minh chưa vượt qua:
  ```bash
  python -m ccba_harness verify-patch
  ```
* **Zero Tolerance Exit Code:** Lệnh kiểm thử phải thoát với mã exit code 0; tuyệt đối không bỏ qua các lỗi linter hay hồi quy.

## Kỷ Luật Rà Soát Hai Vòng (Double-Pass Adversarial Review)
* **Vòng 1 (Code-First Research):** Luôn đọc implementation thực tế và kiểm tra data flow end-to-end trước khi sửa đổi. Không suy đoán hành vi từ tên hàm hay docstring.
* **Vòng 2 (Self-Adversarial Review):** Tự đặt câu hỏi: *Đề xuất này có thể SAI ở đâu?* Kiểm chứng tối thiểu 3 giả định cốt lõi bằng dữ liệu và kiểm thử thực tế trước khi bàn giao.
* **Bảo tồn Invariants:** Không bao giờ xóa hoặc nới lỏng (weaken) các bài test hiện có để làm cho bài test vượt qua.
