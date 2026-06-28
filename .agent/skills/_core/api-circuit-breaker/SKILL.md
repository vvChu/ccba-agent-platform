---
name: API Circuit Breaker
description: Rate limiter + Circuit Breaker pattern cho LLM API calls trong batch pipelines. Tránh quota exhaustion, cascade failures, và infinite retry loops khi gọi AI Gateway hàng loạt.
applies_to:
  - "Phần mềm"
  - "Kiểm định"
bundle: "_core"
---

# API Circuit Breaker

Rate limiter + Circuit Breaker 3-trạng-thái cho LLM API calls. Thiết kế cho các pipeline gọi AI Gateway **hàng loạt** (batch QC, wiki healing, domain enrichment).

> **Nguồn**: VvC Wiki Health v7.4 (2026) — giải quyết lỗi quota exhaustion khi wiki healer gọi LLM cho 300+ concept stubs liên tiếp không throttle.

---

## Vấn đề: Batch API Cascade Failure

```
Batch pipeline gọi LLM cho 300 items
         ↓
Items 1-50: OK
         ↓
Items 51-55: Rate limit hit (429 Too Many Requests)
         ↓ Pipeline tiếp tục retry ngay lập tức
Items 56-300: Tất cả fail với 429
         ↓
Pipeline kết thúc: 245/300 items bị drop silently
         ↓
❌ Không có error log rõ ràng, không có recovery mechanism
```

---

## Implementation: 3-State Circuit Breaker

```python
import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, TypeVar

T = TypeVar("T")

class CircuitState(Enum):
    CLOSED   = "closed"    # Hoạt động bình thường
    OPEN     = "open"      # Đang block — đợi recovery timeout
    HALF_OPEN = "half_open" # Thử lại 1 request để kiểm tra

@dataclass
class CircuitBreaker:
    """3-state circuit breaker cho LLM API calls.

    Args:
        rpm_limit:          Số request tối đa mỗi phút (requests per minute).
        backoff_seconds:    Thời gian chờ sau mỗi lần lỗi (giây).
        failure_threshold:  Số lỗi liên tiếp để trip circuit (OPEN).
        recovery_timeout:   Thời gian OPEN trước khi chuyển sang HALF_OPEN (giây).
    """
    rpm_limit:         int   = 20
    backoff_seconds:   float = 3.0
    failure_threshold: int   = 3
    recovery_timeout:  float = 30.0

    _state:             CircuitState = field(default=CircuitState.CLOSED, init=False)
    _consecutive_fails: int          = field(default=0, init=False)
    _last_failure_time: float        = field(default=0.0, init=False)
    _request_times:     list         = field(default_factory=list, init=False)
    _lock:              threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def min_interval(self) -> float:
        """Khoảng cách tối thiểu giữa 2 requests (giây)."""
        return 60.0 / self.rpm_limit  # VD: 20 RPM → 3.0s/request

    def _enforce_rate_limit(self) -> None:
        """Block cho đến khi đủ khoảng cách với request trước."""
        now = time.time()
        if self._request_times:
            elapsed = now - self._request_times[-1]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self._request_times.append(time.time())
        # Giữ window 60s để tính RPM thực tế
        cutoff = time.time() - 60
        self._request_times = [t for t in self._request_times if t > cutoff]

    def call(self, func: Callable[[], T]) -> T | None:
        """Gọi func() với rate limiting + circuit breaker protection.

        Returns:
            Kết quả của func() nếu thành công.
            None nếu circuit OPEN hoặc gặp lỗi.
        """
        with self._lock:
            # Kiểm tra circuit state
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                else:
                    return None  # Circuit vẫn OPEN — skip request

            # Enforce rate limit
            self._enforce_rate_limit()

        try:
            result = func()
            # Success → reset failure count
            with self._lock:
                self._consecutive_fails = 0
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.CLOSED
            return result

        except Exception as e:
            with self._lock:
                self._consecutive_fails += 1
                self._last_failure_time = time.time()

                if self._consecutive_fails >= self.failure_threshold:
                    self._state = CircuitState.OPEN

            # Backoff trước khi tiếp tục
            time.sleep(self.backoff_seconds)
            return None
```

---

## Usage trong CCBA Batch Pipeline

```python
from ccba_ai import ai

# Khởi tạo 1 lần, dùng chung toàn pipeline
breaker = CircuitBreaker(
    rpm_limit=20,           # 20 RPM — giới hạn an toàn cho AI Gateway
    backoff_seconds=3.0,    # Chờ 3s sau mỗi lỗi
    failure_threshold=3,    # 3 lỗi liên tiếp → OPEN
    recovery_timeout=30.0   # 30s OPEN → thử HALF_OPEN
)

def audit_drawing(drawing_text: str) -> dict | None:
    """Audit 1 bản vẽ — có circuit breaker protection."""
    return breaker.call(
        lambda: ai.chat(
            f"Audit bản vẽ sau: {drawing_text}",
            model="qwen-local-primary"
        )
    )

# Batch processing
results = []
skipped = 0
for drawing in drawings:
    result = audit_drawing(drawing.text)
    if result is None:
        skipped += 1
        update_log("skip", f"Circuit OPEN — skipped: {drawing.name}")
    else:
        results.append(result)

update_log("lifecycle", f"Batch complete: {len(results)} OK, {skipped} skipped")
```

---

## Cấu hình Tham Khảo theo Model

| Model | RPM khuyến nghị | `backoff_seconds` | `failure_threshold` |
|---|---|---|---|
| `qwen-local-primary` (local GPU) | 60 | 1.0 | 5 |
| `ocr-primary` (Gemini Flash) | 30 | 2.0 | 3 |
| `text-gemma` (free tier) | 20 | 3.0 | 3 |
| `claude-haiku-4-5` | 40 | 1.5 | 4 |
| `gemini-3.1-pro-high` | 10 | 6.0 | 2 |

> [!TIP]
> Với `_core` AI Gateway của CCBA (local DGX Spark), `qwen-local-primary` không bị cloud rate limit — có thể dùng RPM cao hơn (60+). Chỉ cần circuit breaker để xử lý trường hợp GPU overload.

---

## Rejected Items Caching (Infinite Retry Prevention)

Khi Circuit OPEN skip một item, cache lại để tránh retry vô tận ở run sau.

```python
import json
from pathlib import Path

REJECTED_CACHE = Path(".rejected_items.json")

def load_rejected_cache() -> set[str]:
    if REJECTED_CACHE.exists():
        return set(json.loads(REJECTED_CACHE.read_text()))
    return set()

def cache_rejected(item_id: str) -> None:
    rejected = load_rejected_cache()
    rejected.add(item_id)
    REJECTED_CACHE.write_text(json.dumps(list(rejected)))

# Trong batch loop
rejected_cache = load_rejected_cache()
for item in items:
    if item.id in rejected_cache:
        continue  # Skip — đã bị reject trước đó
    result = breaker.call(lambda: process(item))
    if result is None:
        cache_rejected(item.id)
```

---

## 3-State Diagram

```
          success (HALF_OPEN)
    ┌────────────────────────────────┐
    │                                ▼
[CLOSED] ──fail×N──► [OPEN] ──30s──► [HALF_OPEN]
    ▲                                    │
    └────────── success ─────────────────┘
                         fail → back to OPEN
```

---

## Ứng dụng trong CCBA Hub

| Service | Vấn đề cần giải quyết |
|---|---|
| `ccba-ai-qc-batch-orchestrator` | Gọi LLM cho 100+ bản vẽ — cần throttle + circuit breaker |
| `legal-document-tracker` | Batch embed VBPL mới — cần RPM control |
| `ccba-ai-qc-reporter` | Nhiều LLM calls song song để build report sections |

---

## Reference Implementation

```
D:\VvC_Notes\scripts\services\wiki_health.py  →  _call_with_throttle() + circuit breaker logic
```
