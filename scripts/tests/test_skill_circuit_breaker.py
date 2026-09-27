"""Unit tests for ccba-api-circuit-breaker skill resource (resources/circuit_breaker.py)."""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path
from unittest.mock import patch

# Load CircuitBreaker directly from skill resources
SKILL_ROOT = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "ccba-api-circuit-breaker"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from resources.circuit_breaker import (  # type: ignore[import-not-found]
    CircuitBreaker,
    CircuitState,
    cache_rejected,
    load_rejected_cache,
)


def test_circuit_breaker_success() -> None:
    """Verify normal successful execution resets failure counter and stays CLOSED."""
    cb = CircuitBreaker(rpm_limit=600, failure_threshold=3)
    result = cb.call(lambda: "ok")
    assert result == "ok"
    assert cb._state == CircuitState.CLOSED
    assert cb._consecutive_fails == 0


def test_circuit_breaker_consecutive_failures() -> None:
    """Verify standard failures trip circuit to OPEN after threshold."""
    cb = CircuitBreaker(rpm_limit=600, failure_threshold=2, backoff_seconds=0.01)

    def failing_fn() -> None:
        raise RuntimeError("Transient connection reset")

    # Fail 1
    assert cb.call(failing_fn) is None
    assert cb._state == CircuitState.CLOSED
    assert cb._consecutive_fails == 1

    # Fail 2 -> Trips to OPEN
    assert cb.call(failing_fn) is None
    assert cb._state == CircuitState.OPEN
    assert cb._consecutive_fails == 2

    # Blocked while OPEN
    assert cb.call(lambda: "wont run") is None


def test_circuit_breaker_budget_exceeded_fast_fail() -> None:
    """Verify LiteLLM budget exceeded errors trip circuit OPEN immediately (Fast-Fail)."""
    cb = CircuitBreaker(rpm_limit=600, failure_threshold=5, backoff_seconds=0.01)

    budget_err_msg = "Budget has been exceeded! Current cost: 5.01, Max budget: 5.0"

    def budget_failing_fn() -> None:
        raise Exception(budget_err_msg)

    stderr_capture = io.StringIO()
    with patch("sys.stderr", stderr_capture):
        res = cb.call(budget_failing_fn)

    assert res is None
    # Fast-fail: Immediately OPEN on first failure
    assert cb._state == CircuitState.OPEN
    output = stderr_capture.getvalue()
    assert "CIRCUIT_BREAKER_OPEN" in output or "RATE_LIMIT_HIT" in output
    assert "budget" in output.lower() and "exceeded" in output.lower()


def test_circuit_breaker_recovery_half_open() -> None:
    """Verify recovery timeout moves state to HALF_OPEN and then CLOSED on success."""
    cb = CircuitBreaker(
        rpm_limit=600,
        failure_threshold=1,
        backoff_seconds=0.01,
        recovery_timeout=0.05,
    )

    # Trip to OPEN
    cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
    assert cb._state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.06)

    # Next call should attempt (HALF_OPEN) and recover on success
    res = cb.call(lambda: "recovered")
    assert res == "recovered"
    assert cb._state == CircuitState.CLOSED
    assert cb._consecutive_fails == 0


def test_rejected_items_cache(tmp_path: Path) -> None:
    """Verify caching rejected items persists to disk."""
    cache_file = tmp_path / "test_rejected.json"
    with patch("resources.circuit_breaker.REJECTED_CACHE", cache_file):
        assert load_rejected_cache() == set()
        cache_rejected("item_001")
        cache_rejected("item_002")
        cached = load_rejected_cache()
        assert "item_001" in cached
        assert "item_002" in cached
