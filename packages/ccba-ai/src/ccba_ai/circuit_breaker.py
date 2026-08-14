"""Local Fast-Fail Circuit Breaker for CCBA AI Gateway.

Provides in-memory circuit breaker protection to fail fast when AI Gateway
or Tailscale VPN connectivity is broken, preventing batch pipeline hangs.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from ccba_ai.exceptions import CCBAErrorCode, format_error_json


class CircuitState(str, Enum):
    """Circuit Breaker States."""

    CLOSED = "CLOSED"  # Normal operation: all requests allowed
    OPEN = "OPEN"  # Fast-fail: connection failed repeatedly, reject calls immediately
    HALF_OPEN = "HALF_OPEN"  # Probe mode: test if gateway recovered with a single trial request


class CircuitBreakerOpenError(Exception):
    """Raised when request is rejected because Circuit Breaker is OPEN."""

    def __init__(
        self,
        message: str = "AI Gateway is currently unreachable. Circuit breaker is OPEN (fast-fail mode).",
        suggestion: str = "Check Tailscale VPN status (100.83.192.30:8090) or wait for cooldown period.",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.code = CCBAErrorCode.CIRCUIT_BREAKER_OPEN
        self.message = message
        self.suggestion = suggestion
        self.extra = extra or {}
        self.json_output = format_error_json(self.code, self.message, self.suggestion, self.extra)
        super().__init__(self.json_output)

    def to_json(self) -> str:
        """Return JSON formatted error string."""
        return self.json_output


class CircuitBreaker:
    """In-memory Fast-Fail Circuit Breaker with Recovery Cooldown."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ) -> None:
        """Initialize Circuit Breaker.

        Args:
            failure_threshold: Number of consecutive connection failures before opening circuit.
            recovery_timeout: Cooldown time in seconds before attempting probe in HALF_OPEN.
        """
        self.failure_threshold = max(1, failure_threshold)
        self.recovery_timeout = max(0.001, recovery_timeout)
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.last_state_change: float = time.time()
        self.last_failure_time: float = 0.0

    def allow_request(self) -> bool:
        """Check whether a request is allowed through the circuit breaker.

        Returns:
            True if request should proceed, False if circuit is OPEN and within cooldown.
        """
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if now - self.last_state_change >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                return True
            return False

        # HALF_OPEN state allows probe request
        return True

    def check_allowed(self) -> None:
        """Ensure requests are allowed, or raise CircuitBreakerOpenError immediately."""
        if not self.allow_request():
            remaining = max(
                0.0, round(self.recovery_timeout - (time.time() - self.last_state_change), 1)
            )
            raise CircuitBreakerOpenError(
                message=f"AI Gateway connection failure threshold reached ({self.failure_count} consecutive errors). Circuit is OPEN.",
                suggestion=f"Wait {remaining}s for cooldown or check Tailscale connection to Server Spark.",
                extra={
                    "state": self.state.value,
                    "consecutive_failures": self.failure_count,
                    "cooldown_remaining_sec": remaining,
                },
            )

    def record_success(self) -> None:
        """Record a successful API response and close circuit."""
        self.failure_count = 0
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()

    def record_failure(self, exc: Exception | None = None) -> None:
        """Record a connection or timeout failure.

        Args:
            exc: The exception caught during the API call.
        """
        now = time.time()
        self.last_failure_time = now
        self.failure_count += 1

        if self.state == CircuitState.HALF_OPEN:
            # Probe request failed -> trip back to OPEN immediately
            self.state = CircuitState.OPEN
            self.last_state_change = now
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = now

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()
        self.last_failure_time = 0.0
