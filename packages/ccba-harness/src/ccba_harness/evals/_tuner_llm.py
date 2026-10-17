"""_tuner_llm.py - Token budget tracking, adaptive rate limiting, and LLM task adapter."""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast

from ._tuner_models import (
    _UNSET,
    RateLimiter,
    TokenBudgetExceededError,
    load_tuner_config,
)
from .models import EvalItem

try:
    from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
    from ccba_ai.client import AIClient, AsyncAIClient
except ImportError:
    AIClient = None  # type: ignore[assignment, misc]
    AsyncAIClient = None  # type: ignore[assignment, misc]
    CircuitBreaker = None  # type: ignore[assignment, misc]

    class CircuitBreakerOpenError(Exception):  # type: ignore[no-redef]
        """Fallback CircuitBreakerOpenError when ccba-ai is not installed."""

        pass


logger = logging.getLogger("ccba.eval.ratchet")


@dataclass
class TokenUsageTracker:
    """Session-wide token consumption tracker and circuit breaker observer."""

    budget_ceiling: int = cast(Any, _UNSET)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_calls: int = 0
    total_latency_s: float = 0.0
    warning_triggered: bool = False
    halt_triggered: bool = False
    reserved_tokens: int = 0

    def __post_init__(self) -> None:
        if self.budget_ceiling is _UNSET:
            cfg = load_tuner_config()
            self.budget_ceiling = int(cfg.get("tokens", {}).get("budget_ceiling", 5_000_000))

    def reserve(self, estimated_tokens: int = 2000) -> bool:
        """Attempts to reserve an estimated number of tokens before dispatching concurrent requests."""
        if (
            self.halt_triggered
            or (self.total_tokens + self.reserved_tokens + estimated_tokens) > self.budget_ceiling
        ):
            return False
        self.reserved_tokens += estimated_tokens
        return True

    def release_reservation(self, estimated_tokens: int = 2000) -> None:
        """Releases a previously reserved token amount."""
        self.reserved_tokens = max(0, self.reserved_tokens - estimated_tokens)

    def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        latency_s: float = 0.0,
        reserved_tokens: int = 0,
    ) -> None:
        """Records token usage and latency from a model inference call, releasing reservation if held."""
        if reserved_tokens > 0:
            self.reserved_tokens = max(0, self.reserved_tokens - reserved_tokens)
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.total_calls += 1
        self.total_latency_s += latency_s

        if not self.warning_triggered and self.total_tokens >= 0.9 * self.budget_ceiling:
            self.warning_triggered = True
            logger.warning(
                f"⚠️ [Token Budget Warning] Tổng token ({self.total_tokens:,}) đã chạm ngưỡng 90% ngân sách ({self.budget_ceiling:,})!"
            )

        if self.total_tokens >= self.budget_ceiling:
            self.halt_triggered = True
            logger.error(
                f"🛑 [Token Budget Halt] Tổng token ({self.total_tokens:,}) đã vượt trần ngân sách ({self.budget_ceiling:,})! Kích hoạt dừng khẩn cấp."
            )

    @property
    def available_tokens(self) -> int:
        """Returns remaining unreserved and unconsumed tokens under budget ceiling."""
        return max(0, self.budget_ceiling - (self.total_tokens + self.reserved_tokens))

    @property
    def is_exhausted(self) -> bool:
        """Checks whether token budget ceiling has been exhausted or fully reserved."""
        return (
            self.total_tokens + self.reserved_tokens
        ) >= self.budget_ceiling or self.halt_triggered

    @property
    def avg_latency_s(self) -> float:
        """Returns average latency per call in seconds."""
        return self.total_latency_s / self.total_calls if self.total_calls > 0 else 0.0


class AdaptiveRateLimiter:
    """Token-Bucket / Leaky-Bucket Rate Limiter with adaptive latency backoff."""

    def __init__(
        self,
        requests_per_minute: float = 60.0,
        min_delay_s: float = 0.01,
        max_delay_s: float = 10.0,
        latency_threshold_s: float | None = None,
        backoff_multiplier: float = 1.5,
        sleeper: Callable[[float], None] = time.sleep,
        time_fn: Callable[[], float] = time.monotonic,
        async_sleeper: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.requests_per_minute = max(1.0, requests_per_minute)
        self.min_interval = 60.0 / self.requests_per_minute
        self.min_delay_s = min_delay_s
        self.max_delay_s = max_delay_s
        if latency_threshold_s is None:
            cfg = load_tuner_config()
            self.latency_threshold_s = float(
                cfg.get("execution", {}).get("latency_threshold_s", 4.0)
            )
        else:
            self.latency_threshold_s = latency_threshold_s
        self.backoff_multiplier = backoff_multiplier
        self.sleeper = sleeper
        self.time_fn = time_fn
        self.async_sleeper = async_sleeper
        self.last_request_time: float = 0.0

    def wait(self, last_latency_s: float = 0.0) -> float:
        """Enforces rate limit interval and applies adaptive backoff if latency is high."""
        now = self.time_fn()
        elapsed = (
            now - self.last_request_time if self.last_request_time > 0.0 else self.min_interval
        )
        base_delay = max(0.0, self.min_interval - elapsed)

        backoff_delay = 0.0
        if last_latency_s > self.latency_threshold_s:
            excess = last_latency_s - self.latency_threshold_s
            backoff_delay = min(excess * (self.backoff_multiplier - 1.0), self.max_delay_s)

        total_delay = min(base_delay + backoff_delay, self.max_delay_s)
        if total_delay >= self.min_delay_s:
            self.sleeper(total_delay)

        self.last_request_time = self.time_fn()
        return total_delay

    async def wait_async(self, last_latency_s: float = 0.0) -> float:
        """Non-blocking rate limiter for async continuous batching."""
        backoff_delay = 0.0
        if last_latency_s > self.latency_threshold_s:
            excess = last_latency_s - self.latency_threshold_s
            backoff_delay = min(excess * (self.backoff_multiplier - 1.0), self.max_delay_s)

        if backoff_delay >= self.min_delay_s:
            if self.async_sleeper is not None:
                await self.async_sleeper(backoff_delay)
            else:
                await asyncio.sleep(backoff_delay)

        self.last_request_time = self.time_fn()
        return backoff_delay


class LLMTaskAdapter:
    """Connects GitRatchetOptimizer with ccba_ai client for Real LLM evaluations."""

    def __init__(
        self,
        model: str | None = None,
        client: Any | None = None,
        token_tracker: TokenUsageTracker | None = None,
        circuit_breaker: Any | None = None,
        rate_limiter: RateLimiter | None = None,
        async_client: Any | None = None,
        estimated_task_tokens: int = 2000,
    ) -> None:
        cfg = load_tuner_config()
        try:
            from ccba_ai.routing import choose_model

            fallback_model = choose_model("local")
        except (ImportError, Exception):
            fallback_model = "qwen-local-primary"
        default_model = str(cfg.get("execution", {}).get("default_model", fallback_model))
        self.model = model or os.getenv("CCBA_TUNER_MODEL", default_model)
        self.token_tracker = token_tracker or TokenUsageTracker()
        self.rate_limiter = rate_limiter
        self.estimated_task_tokens = estimated_task_tokens
        self._last_latency_s = 0.0
        self.circuit_breaker = (
            circuit_breaker
            if circuit_breaker is not None
            else (CircuitBreaker() if CircuitBreaker is not None else None)
        )
        self._init_clients(client, async_client)

    def _init_clients(self, client: Any | None, async_client: Any | None) -> None:
        """Initializes synchronous and asynchronous AI clients with fallback validation."""
        if client is not None or async_client is not None:
            self.client = client if client is not None else async_client
        elif AIClient is not None:
            self.client = AIClient(default_model=self.model, circuit_breaker=self.circuit_breaker)
        else:
            raise ImportError(
                "ccba-ai package is required for real LLM evaluation. Install via: pip install -e packages/ccba-ai"
            )

        if async_client is not None or client is not None:
            self.async_client = async_client if async_client is not None else client
        elif AsyncAIClient is not None:
            self.async_client = AsyncAIClient(
                default_model=self.model, circuit_breaker=self.circuit_breaker
            )
        else:
            self.async_client = None

    def _reserve_tokens(self) -> int:
        """Reserves estimated task tokens from the tracker or raises TokenBudgetExceededError."""
        tokens_to_reserve = min(
            self.estimated_task_tokens, max(1, self.token_tracker.budget_ceiling // 5)
        )
        if not self.token_tracker.reserve(tokens_to_reserve):
            raise TokenBudgetExceededError(
                f"Token budget ceiling ({self.token_tracker.budget_ceiling:,} tokens) exceeded."
            )
        return tokens_to_reserve

    def _finalize_response(self, res: Any, t0: float, tokens_to_reserve: int) -> str:
        """Records token usage and latency from LLM response and returns response text."""
        latency = time.perf_counter() - t0
        self._last_latency_s = latency
        usage = getattr(res, "usage", None)
        p_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
        c_tok = getattr(usage, "completion_tokens", 0) if usage else 0
        self.token_tracker.record_usage(
            p_tok, c_tok, latency_s=latency, reserved_tokens=tokens_to_reserve
        )
        return str(res.content)

    def _record_failure(self, exc: Exception) -> None:
        """Records exception into the circuit breaker if configured."""
        if self.circuit_breaker is not None and hasattr(self.circuit_breaker, "record_failure"):
            self.circuit_breaker.record_failure(exc)

    async def _invoke_async_chat(self, prompt: str, skill_content: str) -> Any:
        """Invokes chat_with_metadata on the active async/sync client."""
        active_client = self.async_client if self.async_client is not None else self.client
        call_fn = active_client.chat_with_metadata
        if inspect.iscoroutinefunction(call_fn):
            return await call_fn(
                message=prompt, system=skill_content, model=self.model, temperature=0.0
            )
        call_res = call_fn(message=prompt, system=skill_content, model=self.model, temperature=0.0)
        return await call_res if inspect.isawaitable(call_res) else call_res

    def create_eval_task(self, skill_content: str) -> Callable[[EvalItem], str]:
        """Creates a callable task for EvalRunner that evaluates candidate skill content via Real LLM."""

        def llm_eval_task(item: EvalItem) -> str:
            tokens_to_reserve = self._reserve_tokens()
            reserved = True
            try:
                if self.rate_limiter is not None:
                    self.rate_limiter.wait(last_latency_s=self._last_latency_s)
                t0 = time.perf_counter()
                res = self.client.chat_with_metadata(
                    message=str(item.input_prompt),
                    system=skill_content,
                    model=self.model,
                    temperature=0.0,
                )
                reserved = False
                return self._finalize_response(res, t0, tokens_to_reserve)
            except CircuitBreakerOpenError:
                raise
            except Exception as e:
                self._record_failure(e)
                raise
            finally:
                if reserved:
                    self.token_tracker.release_reservation(tokens_to_reserve)

        return llm_eval_task

    def create_async_eval_task(self, skill_content: str) -> Callable[[EvalItem], Awaitable[str]]:
        """Creates an async callable task for EvalRunner that evaluates candidate skill content via Real LLM."""

        async def async_llm_eval_task(item: EvalItem) -> str:
            tokens_to_reserve = self._reserve_tokens()
            reserved = True
            try:
                if self.rate_limiter is not None:
                    if hasattr(self.rate_limiter, "wait_async"):
                        await self.rate_limiter.wait_async(last_latency_s=self._last_latency_s)
                    else:
                        self.rate_limiter.wait(last_latency_s=self._last_latency_s)
                t0 = time.perf_counter()
                res = await self._invoke_async_chat(str(item.input_prompt), skill_content)
                reserved = False
                return self._finalize_response(res, t0, tokens_to_reserve)
            except CircuitBreakerOpenError:
                raise
            except Exception as e:
                self._record_failure(e)
                raise
            finally:
                if reserved:
                    self.token_tracker.release_reservation(tokens_to_reserve)

        return async_llm_eval_task
