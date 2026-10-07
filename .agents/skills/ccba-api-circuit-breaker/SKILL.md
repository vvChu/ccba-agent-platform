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
  version: "1.4.0"
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

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`package-bound`**, bám trực tiếp vào lớp `CircuitBreaker` đã được triển khai, kiểm thử và tích hợp sẵn trong package monorepo `packages/ccba-ai` (`from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState`).

Mọi quy trình xử lý theo lô (batch processing pipelines) bắt buộc tái sử dụng trực tiếp lớp `CircuitBreaker` từ package `ccba_ai`, không duy trì script ad-hoc cục bộ tại Spoke hay thư mục `resources/`. Mọi tương tác gọi LLM bên trong hàm lambda được bảo vệ bắt buộc định tuyến qua `choose_model()` hoặc `ModelArchetype`.

---

## Cách sử dụng trong CCBA Batch Pipeline

```python
from ccba_ai import ai, choose_model
from ccba_ai.circuit_breaker import CircuitBreaker

# Khởi tạo 1 lần duy nhất dùng chung cho toàn bộ luồng lặp
breaker = CircuitBreaker(
    failure_threshold=3,    # 3 lỗi liên tiếp -> OPEN circuit
    recovery_timeout=30.0   # Chuyển HALF_OPEN sau 30s
)

def audit_drawing(drawing_text: str) -> dict | None:
    """Audit 1 bản vẽ — có circuit breaker bảo vệ."""
    if not breaker.allow_request():
        return None
    try:
        result = ai.chat(
            f"Audit bản vẽ sau: {drawing_text}",
            model=choose_model("general")
        )
        breaker.record_success()
        return result
    except Exception as exc:
        breaker.record_failure(exc)
        return None

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

### Cơ chế Kháng lỗi Ngân sách LiteLLM & Local Fallback (RULE-2.12)
LiteLLM Gateway v1.83+ trên Server Spark trả về ngoại lệ ngân sách đa định dạng (cả JSON structured `{"type": "budget_exceeded"}` lẫn chuỗi thô `Budget has been exceeded! ...`). Circuit Breaker nhận diện chuẩn xác thông qua kiểm tra đồng thời:
```python
is_budget_error = "budget" in str(e).lower() and "exceeded" in str(e).lower()
```
Khi phát hiện lỗi ngân sách:
- **Fast-Fail tức thì:** Circuit lập tức ngắt sang `CircuitState.OPEN` mà không chờ số lần lỗi đạt `failure_threshold`.
- **Cảnh báo chuẩn:** Xuất JSON mã lỗi `CCBAErrorCode.CIRCUIT_BREAKER_OPEN` ra `stderr` khuyến nghị chuyển đổi sang mô hình cục bộ không tốn phí (local fallback model / `choose_model("local")`).
- **Chống Retry vô hạn:** Kết hợp `cache_rejected()` để bỏ qua item gây cạn quota ở các vòng lặp tiếp theo.

---

## Centralized Gateway (:8090) & Soft Cooldown Auto-Downgrade Pattern

### Kiến trúc Tập Trung tại Gateway Cổng :8090
Toàn bộ danh mục mô hình (kể cả các archetypes reasoning, coding, general và local Qwen) được cung cấp **tập trung tại Gateway duy nhất cổng `:8090`** trên Server Spark (`http://${CCBA_AI_GATEWAY_HOST}:8090/v1`). Không còn phân tách endpoint hay proxy phụ trợ trên cổng `:8045`.

### Bối cảnh & Vấn đề
Khi một pipeline LLM gọi các mô hình reasoning chuyên biệt (như các mô hình thuộc task `reasoning` hoặc `ModelArchetype.REASONING`) qua AI Gateway:
- Khi upstream provider tạm thời cạn kiệt quota hoặc bị giới hạn tần suất, gateway có thể trả về lỗi HTTP `503 Service Unavailable` hoặc HTTP `429 Too Many Requests`.
- Nếu áp dụng Circuit Breaker cứng truyền thống (ngắt toàn bộ pipeline) $\rightarrow$ Tác vụ của người dùng bị dừng khựng (Hard Crash/Abort), gây ức chế và đình trệ quy trình.

### Giải pháp: Model-Level Soft Cooldown & Auto-Downgrade
Kết hợp cơ chế **Soft Cooldown** tạm thời cho từng mô hình với **Tự động giáng cấp xuống mô hình dự phòng** tương đương (như task `general` hoặc `ModelArchetype.STANDARD` ngay trên Gateway `:8090`):

```
                       Request (task="reasoning")
                                       │
                         [Is model in Cooldown (30s)?]
                                 ├── Yes ──► [Auto-Downgrade to Fallback General (:8090)]
                                 │           (was_downgraded = True)
                                 └── No
                                     │
                             Gửi tới Gateway :8090
                                     ├── HTTP 200 ──► Trả về kết quả (was_downgraded = False)
                                     └── HTTP 503/429
                                             │
                                             ├── Kích hoạt Cooldown: _model_cooldown_until[task] = now + 30s
                                             └── [Auto-Downgrade to Fallback General (:8090)]
                                                 (was_downgraded = True)
```

### Triển khai Mẫu (Architecture Seam)
```python
from ccba_ai import choose_model

_model_cooldown_until: dict[str, float] = {}

def call_gateway_with_meta(
    prompt: str,
    *,
    task_or_model: str = "reasoning",
    timeout: int = 90,
) -> tuple[str, bool]:
    """Gọi LLM Gateway (:8090) có theo dõi metadata giáng cấp (was_downgraded)."""
    global _model_cooldown_until

    # 1. Nếu model/task đang trong thời gian Cooldown -> Tự động giáng cấp ngay lập tức
    cooldown_until = _model_cooldown_until.get(task_or_model, 0.0)
    if time.time() < cooldown_until:
        remaining = int(cooldown_until - time.time())
        logger.warning(f"Task/Model {task_or_model} in cooldown ({remaining}s left). Auto-downgrading to fallback model...")
        return _call_fallback_gateway(prompt, timeout=timeout), True

    # 2. Thử gọi mô hình chính trên Gateway :8090
    try:
        resolved_model = choose_model(task_or_model)
        content = _call_gateway_endpoint(prompt, model=resolved_model, timeout=timeout)
        return content, False
    except (GatewayHttp503Error, GatewayHttp429Error) as exc:
        # 3. Kích hoạt 30s Soft Cooldown và giáng cấp tức thì sang model dự phòng trên :8090
        _model_cooldown_until[task_or_model] = time.time() + 30.0
        logger.warning(f"Task/Model {task_or_model} limited: {exc}. Cooldown 30s set. Downgrading to fallback...")
        return _call_fallback_gateway(prompt, timeout=timeout), True
```

### Transparency UI Callout Invariant
Khi cờ `was_downgraded == True`, lớp điều phối (Coordinator/UI) BẮT BUỘC chèn một Callout thông báo minh bạch ở đầu bài viết để người dùng nắm rõ lý do mô hình bị thay thế mà không gây gián đoạn luồng làm việc:

```markdown
> [!info] ℹ️ Mô hình chính đang trong thời gian hồi phục tài khoản (cooldown), hệ thống đã tự động phản hồi bằng mô hình dự phòng (General/Fast) để bạn không phải chờ đợi.
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
import json
from pathlib import Path
from ccba_ai.circuit_breaker import CircuitBreaker

REJECTED_CACHE = Path(".rejected_items.json")

def load_rejected_cache() -> set[str]:
    """Tải danh sách các item bị reject."""
    if REJECTED_CACHE.exists():
        try:
            return set(json.loads(REJECTED_CACHE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def cache_rejected(item_id: str) -> None:
    """Cache lại item_id bị reject để phòng tránh infinite retry loop."""
    rejected = load_rejected_cache()
    rejected.add(item_id)
    try:
        REJECTED_CACHE.write_text(json.dumps(list(rejected)), encoding="utf-8")
    except Exception as e:
        print(f"[Warning] Failed to write rejected cache: {e}", file=sys.stderr)

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
rejected_cache = load_rejected_cache()

for item in items:
    if item.id in rejected_cache:
        continue  # Skip không gọi API nữa
        
    if not breaker.allow_request():
        continue

    try:
        result = process(item)
        breaker.record_success()
    except Exception as exc:
        breaker.record_failure(exc)
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

## Chuẩn Mực Thiết Kế Mã Nguồn: KISS, Idempotency & Error Handling
* **KISS (Keep It Simple, Stupid):** Ưu tiên giải pháp đơn giản nhất; không tạo abstraction/seam giả định khi chưa có ít nhất 2 adapter thực tế.
* **Idempotency:** Mọi script thao tác tệp, database hay git worktree phải đảm bảo tính lũy kế an toàn (chạy nhiều lần cho ra cùng một kết quả vững chắc).
* **Explicit Error Handling:** Xử lý ngoại lệ cụ thể (Specific Exceptions); nghiêm cấm sử dụng bare `except:` hoặc nuốt lỗi âm thầm.
* **Type Hints & Docstrings:** Mọi hàm/phương thức public bắt buộc có type annotations đầy đủ và docstrings chuẩn mực.
