# API Circuit Breaker — Implementation Recipes

Tài liệu tham chiếu Level 3 cho `ccba-api-circuit-breaker`, chứa đầy đủ mẫu code Python cho batch loop, Soft Cooldown Auto-Downgrade (`:8090`) và Rejected Items Caching.

## 1. Batch Pipeline với `CircuitBreaker`

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

## 2. Soft Cooldown Auto-Downgrade Seam (`:8090`)

```python
import time
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

    cooldown_until = _model_cooldown_until.get(task_or_model, 0.0)
    if time.time() < cooldown_until:
        remaining = int(cooldown_until - time.time())
        logger.warning(f"Task/Model {task_or_model} in cooldown ({remaining}s left). Auto-downgrading to fallback model...")
        return _call_fallback_gateway(prompt, timeout=timeout), True

    try:
        resolved_model = choose_model(task_or_model)
        content = _call_gateway_endpoint(prompt, model=resolved_model, timeout=timeout)
        return content, False
    except (GatewayHttp503Error, GatewayHttp429Error) as exc:
        _model_cooldown_until[task_or_model] = time.time() + 30.0
        logger.warning(f"Task/Model {task_or_model} limited: {exc}. Cooldown 30s set. Downgrading to fallback...")
        return _call_fallback_gateway(prompt, timeout=timeout), True
```

### Transparency UI Callout Format

Khi `was_downgraded == True`:

```markdown
> [!info] ℹ️ Mô hình chính đang trong thời gian hồi phục tài khoản (cooldown), hệ thống đã tự động phản hồi bằng mô hình dự phòng (General/Fast) để bạn không phải chờ đợi.
```

## 3. Rejected Items Caching (Infinite Retry Prevention)

```python
import json
import sys
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
        cache_rejected(item.id)
```
