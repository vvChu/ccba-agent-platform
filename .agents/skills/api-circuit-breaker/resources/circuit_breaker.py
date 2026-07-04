import json
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TypeVar

from ccba_ai import CCBAErrorCode, format_error_json

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"  # Hoạt động bình thường
    OPEN = "open"  # Đang block — đợi recovery timeout
    HALF_OPEN = "half_open"  # Thử lại 1 request để kiểm tra


@dataclass
class CircuitBreaker:
    """3-state circuit breaker cho LLM API calls.
    Tích hợp tự động in log lỗi JSON chuẩn hóa cho LLM Agents.

    Args:
        rpm_limit:          Số request tối đa mỗi phút (requests per minute).
        backoff_seconds:    Thời gian chờ sau mỗi lần lỗi (giây).
        failure_threshold:  Số lỗi liên tiếp để trip circuit (OPEN).
        recovery_timeout:   Thời gian OPEN trước khi chuyển sang HALF_OPEN (giây).
    """

    rpm_limit: int = 20
    backoff_seconds: float = 3.0
    failure_threshold: int = 3
    recovery_timeout: float = 30.0

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _consecutive_fails: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _request_times: list = field(default_factory=list, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

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
            None nếu circuit OPEN hoặc gặp lỗi (in JSON lỗi ra stderr).
        """
        with self._lock:
            # Kiểm tra circuit state và chuyển HALF_OPEN nếu hết timeout
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                else:
                    # In log lỗi JSON chuẩn hóa khi Circuit OPEN block request
                    error_json = format_error_json(
                        CCBAErrorCode.CIRCUIT_BREAKER_OPEN,
                        f"Circuit Breaker is OPEN due to {self._consecutive_fails} consecutive failures. Request blocked.",
                        f"Wait for recovery timeout ({self.recovery_timeout}s) before trying again or check backend service status.",
                    )
                    print(error_json, file=sys.stderr)
                    return None

            # Enforce rate limit
            self._enforce_rate_limit()

        try:
            result = func()
            # Thành công -> reset trạng thái
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

            # In log lỗi JSON chuẩn hóa khi gặp exception
            error_json = format_error_json(
                CCBAErrorCode.RATE_LIMIT_HIT,
                f"LLM API call failed: {str(e)}",
                f"Check if you hit API Rate Limit. Circuit state: {self._state.value.upper()}. Retrying in {self.backoff_seconds}s.",
            )
            print(error_json, file=sys.stderr)

            # Backoff trước khi trả về
            time.sleep(self.backoff_seconds)
            return None


# Helper functions cho Rejected Items Caching
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
