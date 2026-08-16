"""Unit tests for CircuitBreaker in ccba_ai.circuit_breaker."""

import json
import time

import pytest

from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_circuit_breaker_initial_state() -> None:
    """Verify initial state is CLOSED and allows requests."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.allow_request() is True
    # check_allowed should not raise
    cb.check_allowed()


def test_circuit_breaker_trips_to_open_after_threshold() -> None:
    """Verify circuit trips to OPEN after consecutive failures reach threshold."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)

    cb.record_failure(Exception("err1"))
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    cb.record_failure(Exception("err2"))
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 2

    cb.record_failure(Exception("err3"))
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3
    assert cb.allow_request() is False

    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        cb.check_allowed()
    assert "Circuit is OPEN" in str(exc_info.value)


def test_circuit_breaker_success_resets_failure_count() -> None:
    """Verify success resets consecutive failure count in CLOSED state."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)

    cb.record_failure()
    cb.record_failure()
    assert cb.failure_count == 2

    cb.record_success()
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_half_open_recovery() -> None:
    """Verify circuit transitions to HALF_OPEN after cooldown, then CLOSED on success."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Within cooldown: rejected
    assert cb.allow_request() is False

    # Sleep past cooldown
    time.sleep(0.06)

    # First request after cooldown probes gateway
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Probe succeeds -> CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_half_open_failure_reopens() -> None:
    """Verify failure during HALF_OPEN immediately re-opens the circuit."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    time.sleep(0.06)
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Probe fails -> immediately OPEN again
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False


def test_circuit_breaker_manual_reset() -> None:
    """Verify manual reset restores circuit to CLOSED state."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.allow_request() is True


def test_circuit_breaker_open_error_json_structure() -> None:
    """Verify CircuitBreakerOpenError formats structured JSON output."""
    err = CircuitBreakerOpenError(
        message="Gateway unreachable",
        suggestion="Check VPN",
        extra={"failures": 3},
    )
    payload = json.loads(err.to_json())
    assert payload["status"] == "error"
    assert payload["error_code"] == "CIRCUIT_BREAKER_OPEN"
    assert payload["message"] == "Gateway unreachable"
    assert payload["recovery_suggestion"] == "Check VPN"
    assert payload["extra"]["failures"] == 3
