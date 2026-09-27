"""tuner.py - Autonomous Git-Ratchet Prompt & Skill Optimizer (ADR-0023).

Adapted from Andrej Karpathy's autoresearch paradigm (Propose -> Evaluate -> Keep/Revert via Git).
Optimizes AI skill prompts (SKILL.md) and prompt templates iteratively, committing on score
improvements and instantly rolling back (git checkout / file restore) on regressions or critical failures.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

import yaml

from .models import EvalItem, EvalReport
from .runner import EvalRunner, load_eval_dataset
from .scorers import (
    BaseScorer,
)
from .simulation import build_mock_agent_task
from .slicing import (
    AdaptiveDataSlicer,
    SlicedDataset,
)

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

# SSOT Regex patterns for ADR matrix tag detection and preservation
ADR_HEADER_TAG_REGEX = re.compile(
    r"\s*\([^)\n\r]*(?:HUB[-_]ADR|ADR)[-_\s]*[0-9]+[^)\n\r]*\)",
    re.IGNORECASE,
)
ADR_REF_PATTERN = re.compile(
    r"\b(?:HUB[-_]ADR|ADR)[-_\s]*0*([0-9]+)\b",
    re.IGNORECASE,
)


class TokenBudgetExceededError(Exception):
    """Raised when session-wide token budget ceiling is reached."""

    pass


_UNSET: Any = object()

_CACHED_TUNER_CONFIG: dict[str, Any] | None = None
_TUNER_CONFIG_PATH = Path(__file__).parent / "tuner_config.yaml"


def load_tuner_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Loads tuner hyperparameters from declarative YAML with in-memory singleton caching.

    Latency guarantee: O(1) in-memory dict lookup (< 0.05 ms).
    """
    global _CACHED_TUNER_CONFIG
    if config_path is None and _CACHED_TUNER_CONFIG is not None:
        return _CACHED_TUNER_CONFIG

    path = Path(config_path) if config_path else _TUNER_CONFIG_PATH
    if not path.is_file():
        return {}

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    if config_path is None:
        _CACHED_TUNER_CONFIG = data
    return data


def reload_tuner_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Forces reloading of the tuner configuration, clearing singleton cache."""
    global _CACHED_TUNER_CONFIG
    _CACHED_TUNER_CONFIG = None
    return load_tuner_config(config_path)


DEFAULT_MUTATION_STRATEGIES_PATH = Path(__file__).resolve().parent / "mutation_strategies.yaml"
_CACHED_MUTATION_STRATEGIES: dict[str, list[tuple[str, str]]] | None = None


def load_mutation_strategies(
    path: Path | None = None,
) -> dict[str, list[tuple[str, str]]]:
    """Loads prompt mutation strategies from declarative YAML with in-memory singleton caching.

    Latency guarantee: O(1) in-memory dict lookup (< 0.05 ms).
    """
    global _CACHED_MUTATION_STRATEGIES
    if path is None and _CACHED_MUTATION_STRATEGIES is not None:
        return _CACHED_MUTATION_STRATEGIES

    target_path = Path(path) if path else DEFAULT_MUTATION_STRATEGIES_PATH
    if not target_path.is_file():
        return {}

    with open(target_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    loaded: dict[str, list[tuple[str, str]]] = {}
    for arch_name, items in data.get("strategies", {}).items():
        if isinstance(items, list):
            loaded[arch_name] = [
                (str(item.get("name", "")), str(item.get("content", "")).strip())
                for item in items
                if isinstance(item, dict) and "name" in item and "content" in item
            ]

    if path is None:
        _CACHED_MUTATION_STRATEGIES = loaded
    return loaded


def reload_mutation_strategies(
    path: Path | None = None,
) -> dict[str, list[tuple[str, str]]]:
    """Forces reloading of mutation strategies, clearing singleton cache."""
    global _CACHED_MUTATION_STRATEGIES
    _CACHED_MUTATION_STRATEGIES = None
    return load_mutation_strategies(path)


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
        """Attempts to reserve an estimated number of tokens before dispatching concurrent requests.

        Returns:
            True if reservation was successful, False if budget would be exceeded.
        """
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

        # 90% warning threshold (REC-08)
        if not self.warning_triggered and self.total_tokens >= 0.9 * self.budget_ceiling:
            self.warning_triggered = True
            logger.warning(
                f"⚠️ [Token Budget Warning] Tổng token ({self.total_tokens:,}) đã chạm ngưỡng 90% ngân sách ({self.budget_ceiling:,})!"
            )

        # 100% hard ceiling halt
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


@runtime_checkable
class RateLimiter(Protocol):
    """Protocol for request throughput rate limiting in batch LLM evaluations."""

    def wait(self, last_latency_s: float = 0.0) -> float: ...


class AdaptiveRateLimiter:
    """Token-Bucket / Leaky-Bucket Rate Limiter with adaptive latency backoff.

    Protects LLM gateways (such as LiteLLM on Server Spark) from queue congestion
    and rate limit exhaustion during bulk overnight evaluation sweeps.
    """

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
        """Enforces rate limit interval and applies adaptive backoff if latency is high.

        Returns:
            The total delay in seconds waited.
        """
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
        """Non-blocking rate limiter for async continuous batching.

        Avoids sequential bottlenecking between parallel tasks to unlock vLLM continuous
        batching on Server Spark (:8090). Only applies backoff cooldown when the backend
        server exhibits latency higher than latency_threshold_s.

        Returns:
            The backoff delay in seconds waited.
        """
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
        fallback_model = "gemini-3.7-flash-high"  # ccba:allow-raw-model
        default_model = str(cfg.get("execution", {}).get("default_model", fallback_model))
        self.model = model or os.getenv("CCBA_TUNER_MODEL", default_model)
        self.token_tracker = token_tracker or TokenUsageTracker()
        self.rate_limiter = rate_limiter
        self.estimated_task_tokens = estimated_task_tokens
        self._last_latency_s = 0.0
        if circuit_breaker is not None:
            self.circuit_breaker = circuit_breaker
        elif CircuitBreaker is not None:
            self.circuit_breaker = CircuitBreaker()
        else:
            self.circuit_breaker = None

        if client is not None:
            self.client = client
        elif async_client is not None:
            self.client = async_client
        elif AIClient is not None:
            self.client = AIClient(
                default_model=self.model,
                circuit_breaker=self.circuit_breaker,
            )
        else:
            raise ImportError(
                "ccba-ai package is required for real LLM evaluation. Install via: pip install -e packages/ccba-ai"
            )

        if async_client is not None:
            self.async_client = async_client
        elif client is not None:
            self.async_client = client
        elif AsyncAIClient is not None:
            self.async_client = AsyncAIClient(
                default_model=self.model,
                circuit_breaker=self.circuit_breaker,
            )
        else:
            self.async_client = None

    def create_eval_task(self, skill_content: str) -> Callable[[EvalItem], str]:
        """Creates a callable task for EvalRunner that evaluates candidate skill content via Real LLM."""

        def llm_eval_task(item: EvalItem) -> str:
            tokens_to_reserve = min(
                self.estimated_task_tokens,
                max(1, self.token_tracker.budget_ceiling // 5),
            )
            if not self.token_tracker.reserve(tokens_to_reserve):
                raise TokenBudgetExceededError(
                    f"Token budget ceiling ({self.token_tracker.budget_ceiling:,} tokens) exceeded."
                )

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
                latency = time.perf_counter() - t0
                self._last_latency_s = latency
                p_tok = res.usage.prompt_tokens if res.usage else 0
                c_tok = res.usage.completion_tokens if res.usage else 0
                self.token_tracker.record_usage(
                    p_tok, c_tok, latency_s=latency, reserved_tokens=tokens_to_reserve
                )
                reserved = False
                return str(res.content)
            except CircuitBreakerOpenError:
                # Re-raise circuit breaker fast-fail to trigger early stopping
                raise
            except Exception as e:
                if self.circuit_breaker is not None and hasattr(
                    self.circuit_breaker, "record_failure"
                ):
                    self.circuit_breaker.record_failure(e)
                raise
            finally:
                if reserved:
                    self.token_tracker.release_reservation(tokens_to_reserve)

        return llm_eval_task

    def create_async_eval_task(self, skill_content: str) -> Callable[[EvalItem], Awaitable[str]]:
        """Creates an async callable task for EvalRunner that evaluates candidate skill content via Real LLM."""

        async def async_llm_eval_task(item: EvalItem) -> str:
            tokens_to_reserve = min(
                self.estimated_task_tokens,
                max(1, self.token_tracker.budget_ceiling // 5),
            )
            if not self.token_tracker.reserve(tokens_to_reserve):
                raise TokenBudgetExceededError(
                    f"Token budget ceiling ({self.token_tracker.budget_ceiling:,} tokens) exceeded."
                )

            reserved = True
            try:
                if self.rate_limiter is not None:
                    if hasattr(self.rate_limiter, "wait_async"):
                        await self.rate_limiter.wait_async(last_latency_s=self._last_latency_s)
                    else:
                        self.rate_limiter.wait(last_latency_s=self._last_latency_s)

                t0 = time.perf_counter()
                active_client = self.async_client if self.async_client is not None else self.client
                call_fn = active_client.chat_with_metadata
                if inspect.iscoroutinefunction(call_fn):
                    res = await call_fn(
                        message=str(item.input_prompt),
                        system=skill_content,
                        model=self.model,
                        temperature=0.0,
                    )
                else:
                    call_res = call_fn(
                        message=str(item.input_prompt),
                        system=skill_content,
                        model=self.model,
                        temperature=0.0,
                    )
                    if inspect.isawaitable(call_res):
                        res = await call_res
                    else:
                        res = call_res

                latency = time.perf_counter() - t0
                self._last_latency_s = latency
                usage = getattr(res, "usage", None)
                p_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
                c_tok = getattr(usage, "completion_tokens", 0) if usage else 0
                self.token_tracker.record_usage(
                    p_tok, c_tok, latency_s=latency, reserved_tokens=tokens_to_reserve
                )
                reserved = False
                return str(res.content)
            except CircuitBreakerOpenError:
                # Re-raise circuit breaker fast-fail to trigger early stopping
                raise
            except Exception as e:
                if self.circuit_breaker is not None and hasattr(
                    self.circuit_breaker, "record_failure"
                ):
                    self.circuit_breaker.record_failure(e)
                raise
            finally:
                if reserved:
                    self.token_tracker.release_reservation(tokens_to_reserve)

        return async_llm_eval_task


@dataclass
class RatchetConfig:
    """Configuration parsed from program.md or CLI flags."""

    target_file: Path
    eval_dataset_file: Path | None = None
    target_score: float = cast(Any, _UNSET)
    max_iterations: int = cast(Any, _UNSET)
    allowed_files: list[str] = field(default_factory=list)
    prohibited_files: list[str] = field(default_factory=list)
    skill_name: str = ""
    full_sweep: bool = cast(Any, _UNSET)
    patience: int = cast(Any, _UNSET)
    use_real_llm: bool = False
    llm_model: str = ""
    token_budget: int | None = cast(Any, _UNSET)
    rate_limiter: RateLimiter | None = None
    enable_adaptive_slicing: bool = cast(Any, _UNSET)
    split_ratio: float = cast(Any, _UNSET)
    slicing_seed: int = cast(Any, _UNSET)
    enable_perturbation: bool = cast(Any, _UNSET)
    per_skill_mutation_budget: int | None = cast(Any, _UNSET)
    hard_max_tokens_per_skill: int | None = cast(Any, _UNSET)
    max_concurrency: int = cast(Any, _UNSET)

    def __post_init__(self) -> None:
        cfg = load_tuner_config()
        r_cfg = cfg.get("ratchet", {})
        tok_cfg = cfg.get("tokens", {})
        exec_cfg = cfg.get("execution", {})

        if isinstance(self.target_file, str):
            self.target_file = Path(self.target_file)
        if self.eval_dataset_file and isinstance(self.eval_dataset_file, str):
            self.eval_dataset_file = Path(self.eval_dataset_file)
        if not self.skill_name and self.target_file:
            tf = self.target_file
            if "skills" in tf.parts or "skills" in str(tf):
                self.skill_name = tf.parent.name if tf.name.lower() == "skill.md" else tf.name
        if not self.use_real_llm and os.getenv("CCBA_TUNER_ENGINE") == "REAL_LLM":
            self.use_real_llm = True
        if not self.llm_model:
            fallback_m = "gemini-3.7-flash-high"  # ccba:allow-raw-model
            def_m = str(exec_cfg.get("default_model", fallback_m))
            self.llm_model = os.getenv("CCBA_TUNER_MODEL", def_m)

        # 4-tier Precedence: Explicit User Param > Env Var > Declarative YAML > Code Fallback
        # target_score
        if self.target_score is _UNSET:
            env_ts = os.getenv("CCBA_TUNER_TARGET_SCORE")
            if env_ts:
                try:
                    self.target_score = float(env_ts)
                except ValueError:
                    self.target_score = float(r_cfg.get("target_score", 90.0))
            else:
                self.target_score = float(r_cfg.get("target_score", 90.0))
        elif isinstance(self.target_score, str):
            self.target_score = float(self.target_score)

        # max_iterations
        if self.max_iterations is _UNSET:
            env_mi = os.getenv("CCBA_TUNER_MAX_ITERATIONS")
            if env_mi:
                try:
                    self.max_iterations = int(env_mi)
                except ValueError:
                    self.max_iterations = int(r_cfg.get("max_iterations", 10))
            else:
                self.max_iterations = int(r_cfg.get("max_iterations", 10))
        elif isinstance(self.max_iterations, str):
            self.max_iterations = int(self.max_iterations)

        # patience
        if self.patience is _UNSET:
            env_pat = os.getenv("CCBA_TUNER_PATIENCE")
            if env_pat:
                try:
                    self.patience = int(env_pat)
                except ValueError:
                    self.patience = int(r_cfg.get("patience", 3))
            else:
                self.patience = int(r_cfg.get("patience", 3))
        elif isinstance(self.patience, str):
            self.patience = int(self.patience)

        # full_sweep
        if self.full_sweep is _UNSET:
            env_fs = os.getenv("CCBA_TUNER_FULL_SWEEP")
            if env_fs is not None:
                self.full_sweep = env_fs.lower() in ("1", "true", "yes")
            else:
                self.full_sweep = bool(r_cfg.get("full_sweep", False))

        # split_ratio
        if self.split_ratio is _UNSET:
            env_sr = os.getenv("CCBA_TUNER_SPLIT_RATIO")
            if env_sr:
                try:
                    self.split_ratio = float(env_sr)
                except ValueError:
                    self.split_ratio = float(r_cfg.get("split_ratio", 0.7))
            else:
                self.split_ratio = float(r_cfg.get("split_ratio", 0.7))
        elif isinstance(self.split_ratio, str):
            self.split_ratio = float(self.split_ratio)

        # slicing_seed
        if self.slicing_seed is _UNSET:
            env_seed = os.getenv("CCBA_TUNER_SLICING_SEED")
            if env_seed:
                try:
                    self.slicing_seed = int(env_seed)
                except ValueError:
                    self.slicing_seed = int(r_cfg.get("slicing_seed", 42))
            else:
                self.slicing_seed = int(r_cfg.get("slicing_seed", 42))
        elif isinstance(self.slicing_seed, str):
            self.slicing_seed = int(self.slicing_seed)

        # enable_adaptive_slicing
        if self.enable_adaptive_slicing is _UNSET:
            env_as = os.getenv("CCBA_TUNER_ADAPTIVE_SLICING")
            if env_as is not None:
                self.enable_adaptive_slicing = env_as.lower() in ("1", "true", "yes")
            else:
                self.enable_adaptive_slicing = bool(r_cfg.get("enable_adaptive_slicing", True))

        # enable_perturbation
        if self.enable_perturbation is _UNSET:
            env_pt = os.getenv("CCBA_TUNER_PERTURBATION")
            if env_pt is not None:
                self.enable_perturbation = env_pt.lower() in ("1", "true", "yes")
            else:
                self.enable_perturbation = bool(r_cfg.get("enable_perturbation", True))

        # token_budget
        if self.token_budget is not _UNSET and self.token_budget is not None:
            if isinstance(self.token_budget, str):
                try:
                    self.token_budget = int(self.token_budget.replace(",", "").replace("_", ""))
                except ValueError:
                    self.token_budget = int(tok_cfg.get("budget_ceiling", 5_000_000))
        else:
            env_budget = os.getenv("CCBA_TUNER_TOKEN_BUDGET")
            if env_budget:
                try:
                    self.token_budget = int(env_budget.replace(",", "").replace("_", ""))
                except ValueError:
                    self.token_budget = int(tok_cfg.get("budget_ceiling", 5_000_000))
            else:
                self.token_budget = int(tok_cfg.get("budget_ceiling", 5_000_000))

        # per_skill_mutation_budget
        if self.per_skill_mutation_budget is not _UNSET:
            if isinstance(self.per_skill_mutation_budget, str):
                try:
                    self.per_skill_mutation_budget = int(
                        self.per_skill_mutation_budget.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.per_skill_mutation_budget = int(
                        tok_cfg.get("per_skill_mutation_budget", 250_000)
                    )
        else:
            env_ps_budget = os.getenv("CCBA_TUNER_PER_SKILL_MUTATION_BUDGET")
            if env_ps_budget:
                try:
                    self.per_skill_mutation_budget = int(
                        env_ps_budget.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.per_skill_mutation_budget = int(
                        tok_cfg.get("per_skill_mutation_budget", 250_000)
                    )
            else:
                self.per_skill_mutation_budget = int(
                    tok_cfg.get("per_skill_mutation_budget", 250_000)
                )

        # hard_max_tokens_per_skill
        if self.hard_max_tokens_per_skill is not _UNSET:
            if isinstance(self.hard_max_tokens_per_skill, str):
                try:
                    self.hard_max_tokens_per_skill = int(
                        self.hard_max_tokens_per_skill.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.hard_max_tokens_per_skill = int(
                        tok_cfg.get("hard_max_tokens_per_skill", 500_000)
                    )
        else:
            env_hard_max = os.getenv("CCBA_TUNER_HARD_MAX_PER_SKILL")
            if env_hard_max:
                try:
                    self.hard_max_tokens_per_skill = int(
                        env_hard_max.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.hard_max_tokens_per_skill = int(
                        tok_cfg.get("hard_max_tokens_per_skill", 500_000)
                    )
            else:
                self.hard_max_tokens_per_skill = int(
                    tok_cfg.get("hard_max_tokens_per_skill", 500_000)
                )

        # max_concurrency
        if self.max_concurrency is not _UNSET:
            if isinstance(self.max_concurrency, str):
                try:
                    self.max_concurrency = int(self.max_concurrency)
                except ValueError:
                    self.max_concurrency = int(exec_cfg.get("max_concurrency", 5))
        else:
            env_concurrency = os.getenv("CCBA_TUNER_CONCURRENCY")
            if env_concurrency:
                try:
                    self.max_concurrency = int(env_concurrency)
                except ValueError:
                    self.max_concurrency = int(exec_cfg.get("max_concurrency", 5))
            else:
                self.max_concurrency = int(exec_cfg.get("max_concurrency", 5))

    @classmethod
    def from_markdown_program(cls, program_path: Path, root: Path | None = None) -> RatchetConfig:
        """Parses a program.md specification file.

        Args:
            program_path: Path to the markdown program specification file.
            root: Optional root directory for relative path resolution.

        Returns:
            RatchetConfig parsed from the markdown file.

        Raises:
            FileNotFoundError: If program_path does not exist.
            ValueError: If target file cannot be found in the specification.
        """
        if not program_path.exists():
            raise FileNotFoundError(f"Program spec file not found: {program_path}")

        if root is None:
            cur = program_path.resolve().parent
            for p in [cur, *cur.parents]:
                if (
                    (p / ".agents").exists()
                    or (p / "pyproject.toml").exists()
                    or (p / ".git").exists()
                ):
                    root = p
                    break
            if root is None:
                root = cur

        content = program_path.read_text(encoding="utf-8")

        # Parse target file
        target_match = re.search(
            r"-\s*\*\*Target(?:\s*File)?\*\*:\s*`?([^`\r\n]+)`?", content, re.IGNORECASE
        )
        if not target_match:
            target_match = re.search(r"-\s*Target:\s*`?([^`\r\n]+)`?", content, re.IGNORECASE)
        if not target_match:
            raise ValueError(
                f"Missing required 'Target File' specification in program file: {program_path}"
            )
        target_str = target_match.group(1).strip()
        target_path = (
            (root / target_str).resolve()
            if not Path(target_str).is_absolute()
            else Path(target_str).resolve()
        )

        # Parse target score
        score_match = re.search(
            r"-\s*\*\*Target\s*Score\*\*:\s*(\d+(?:\.\d+)?)%?", content, re.IGNORECASE
        )
        target_score = float(score_match.group(1)) if score_match else 90.0

        # Parse max iterations
        iter_match = re.search(r"-\s*\*\*Max\s*Iterations\*\*:\s*(\d+)", content, re.IGNORECASE)
        max_iterations = int(iter_match.group(1)) if iter_match else 10

        # Parse eval dataset
        dataset_match = re.search(
            r"-\s*\*\*Dataset(?:\s*File)?\*\*:\s*`?([^`\r\n]+)`?", content, re.IGNORECASE
        )
        dataset_path = None
        if dataset_match:
            ds_str = dataset_match.group(1).strip()
            dataset_path = (
                (root / ds_str).resolve()
                if not Path(ds_str).is_absolute()
                else Path(ds_str).resolve()
            )

        # Extract skill name from target file if possible
        skill_name = target_path.parent.name if "skills" in str(target_path) else "custom_skill"

        # Parse Engine (Real LLM or Mock)
        engine_match = re.search(r"-\s*\*\*Engine\*\*:\s*`?([^`\r\n]+)`?", content, re.IGNORECASE)
        use_real_llm = False
        if engine_match:
            use_real_llm = "real" in engine_match.group(1).lower()

        # Parse Model
        model_match = re.search(r"-\s*\*\*Model\*\*:\s*`?([^`\r\n]+)`?", content, re.IGNORECASE)
        llm_model = model_match.group(1).strip() if model_match else ""

        # Parse Token Budget
        budget_match = re.search(
            r"-\s*\*\*Token\s*Budget\*\*:\s*([0-9,_]+)", content, re.IGNORECASE
        )
        token_budget = (
            int(re.sub(r"[,_]", "", budget_match.group(1))) if budget_match else 5_000_000
        )

        # Parse Per Skill Mutation Budget
        per_skill_match = re.search(
            r"-\s*\*\*Per\s*Skill\s*(?:Mutation\s*)?Budget\*\*:\s*([0-9,_]+)",
            content,
            re.IGNORECASE,
        )
        per_skill_mutation_budget = (
            int(re.sub(r"[,_]", "", per_skill_match.group(1))) if per_skill_match else _UNSET
        )

        # Parse Hard Max Tokens Per Skill
        hard_max_match = re.search(
            r"-\s*\*\*Hard\s*Max\s*(?:Tokens\s*)?(?:Per\s*Skill)?\*\*:\s*([0-9,_]+)",
            content,
            re.IGNORECASE,
        )
        hard_max_tokens_per_skill = (
            int(re.sub(r"[,_]", "", hard_max_match.group(1))) if hard_max_match else _UNSET
        )

        return cls(
            target_file=target_path,
            eval_dataset_file=dataset_path,
            target_score=target_score,
            max_iterations=max_iterations,
            skill_name=skill_name,
            use_real_llm=use_real_llm,
            llm_model=llm_model,
            token_budget=token_budget,
            per_skill_mutation_budget=per_skill_mutation_budget,
            hard_max_tokens_per_skill=hard_max_tokens_per_skill,
        )


@dataclass
class RatchetTrialResult:
    """Record of a single ratchet experiment iteration."""

    iteration: int
    score: float
    passed: bool
    critical_fails: int
    decision: str  # 'KEEP' | 'REVERT'
    summary: str
    diff_snippet: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Converts result to JSON-serializable dictionary."""
        return asdict(self)


@dataclass
class RatchetReport:
    """Full execution summary of a Git-Ratchet optimization run."""

    target_file: str
    initial_score: float
    final_score: float
    total_iterations: int
    kept_commits: int
    reverted_trials: int
    history: list[RatchetTrialResult] = field(default_factory=list)
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    avg_latency_s: float = 0.0
    halt_reason: str | None = None
    slicing_tier: str | None = None
    tuning_size: int = 0
    holdout_size: int = 0
    holdout_score: float | None = None
    holdout_initial_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converts report to JSON-serializable dictionary."""
        return {
            "target_file": self.target_file,
            "initial_score": self.initial_score,
            "final_score": self.final_score,
            "total_iterations": self.total_iterations,
            "kept_commits": self.kept_commits,
            "reverted_trials": self.reverted_trials,
            "history": [t.to_dict() for t in self.history],
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "avg_latency_s": self.avg_latency_s,
            "halt_reason": self.halt_reason,
            "slicing_tier": self.slicing_tier,
            "tuning_size": self.tuning_size,
            "holdout_size": self.holdout_size,
            "holdout_score": self.holdout_score,
            "holdout_initial_score": self.holdout_initial_score,
        }


def preserve_yaml_frontmatter(original_content: str, edited_content: str) -> str:
    """Preserves YAML frontmatter metadata when mutating SKILL.md body.

    Ensures mutations only modify the instruction body in SKILL.md,
    strictly preserving frontmatter fields byte-for-byte.

    Args:
        original_content: The unmutated SKILL.md content with frontmatter.
        edited_content: The newly proposed body content or full text.

    Returns:
        The combined text containing original frontmatter and new body.
    """
    # Match YAML frontmatter at the beginning of original_content
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", original_content, re.DOTALL)
    if not fm_match:
        # Check if original_content has leading whitespace before frontmatter
        fm_match = re.match(r"^\s*---\r?\n(.*?)\r?\n---\r?\n?", original_content, re.DOTALL)
        if not fm_match:
            return edited_content

    frontmatter_block = fm_match.group(0).strip()

    # If edited_content also contains frontmatter, strip it to avoid duplication
    edited_fm_match = re.match(r"^\s*---\r?\n.*?\r?\n---\r?\n?(.*)$", edited_content, re.DOTALL)
    if edited_fm_match:
        body = edited_fm_match.group(1)
    else:
        body = edited_content

    clean_body = body.strip()
    nl = "\r\n" if "\r\n" in original_content else "\n"
    if clean_body:
        return f"{frontmatter_block}{nl}{nl}{clean_body}{nl}"
    return f"{frontmatter_block}{nl}"


# ---------------------------------------------------------------------------
# Domain Archetypes (Re-exported from SSOT archetypes.py)
# ---------------------------------------------------------------------------
from .archetypes import (  # noqa: F401
    ACADEMIC_ARCHETYPE_KEYWORDS,
    ADR_ARCHETYPE_KEYWORDS,
    BIM_ARCHETYPE_KEYWORDS,
    BIM_GOVERNANCE_ARCHETYPE_KEYWORDS,
    BIM_RASE_ARCHETYPE_KEYWORDS,
    CODING_ARCHETYPE_KEYWORDS,
    DOMAIN_ARCHETYPES,
    GRILLING_ARCHETYPE_KEYWORDS,
    LEGAL_ARCHETYPE_KEYWORDS,
    OFFICE_ARCHETYPE_KEYWORDS,
    ORCHESTRATION_ARCHETYPE_KEYWORDS,
    RISK_ARCHETYPE_KEYWORDS,
    TECH_QC_ARCHETYPE_KEYWORDS,
    VISUAL_ARCHETYPE_KEYWORDS,
    DomainArchetype,
    get_default_domain_scorers,
    resolve_domain_archetype,
    resolve_domain_dataset,
)


@dataclass
class _RatchetLoopState:
    """Encapsulates mutable loop state and trial history for GitRatchetOptimizer."""

    best_score: float
    best_content: str
    has_committed: bool = False
    kept_count: int = 0
    reverted_count: int = 0
    stagnant_trials: int = 0
    seen_hashes: set[str] = field(default_factory=set)
    history: list[RatchetTrialResult] = field(default_factory=list)


# Alias for backward compatibility
_RatchetSession = _RatchetLoopState


class GitRatchetOptimizer:
    """Autonomous Ratchet Optimization Engine using Git commits for state persistence."""

    def __init__(
        self,
        config: RatchetConfig,
        scorers: list[BaseScorer] | None = None,
        dry_run_git: bool = False,
        project_root: Path | None = None,
        root: Path | None = None,
        task: Callable[[EvalItem], Any] | None = None,
        dataset: list[EvalItem] | None = None,
        client: Any | None = None,
        circuit_breaker: Any | None = None,
        rate_limiter: RateLimiter | None = None,
        async_client: Any | None = None,
    ) -> None:
        self.config = config
        self.target_file = Path(config.target_file).resolve()
        self.dry_run_git = dry_run_git
        self.custom_task = task
        self.client = client
        self.async_client = async_client
        self.circuit_breaker = circuit_breaker
        self.rate_limiter = rate_limiter or config.rate_limiter

        effective_root = project_root if project_root is not None else root
        if effective_root is not None:
            self.project_root = Path(effective_root).resolve()
        else:
            cur = self.target_file.parent
            detected = None
            for p in [cur, *cur.parents]:
                if (
                    (p / ".git").exists()
                    or (p / ".agents").exists()
                    or (p / "pyproject.toml").exists()
                ):
                    detected = p
                    break
            self.project_root = detected if detected else Path.cwd().resolve()

        self.scorers = scorers or get_default_domain_scorers(config.skill_name)
        self.runner = EvalRunner(
            default_pass_threshold=config.target_score,
            max_concurrency=config.max_concurrency,
        )
        self.dataset: list[EvalItem] = dataset if dataset is not None else self._load_dataset()

        # Three-Tier Adaptive Slicing (TICKET-006 / ADR-0058)
        if config.enable_adaptive_slicing and self.dataset:
            self.slicer = AdaptiveDataSlicer()
            self.sliced_data: SlicedDataset | None = self.slicer.slice(
                self.dataset,
                split_ratio=config.split_ratio,
                seed=config.slicing_seed,
                enable_perturbation=config.enable_perturbation,
            )
            self.tuning_dataset: list[EvalItem] = self.sliced_data.tuning_items
            self.holdout_dataset: list[EvalItem] = self.sliced_data.holdout_items
        else:
            self.sliced_data = None
            self.tuning_dataset = list(self.dataset)
            self.holdout_dataset = []

        # Token budget governance & Real LLM adapter (REC-08 / Ticket 03)
        budget = config.token_budget if config.token_budget is not None else 5_000_000
        self.token_tracker = TokenUsageTracker(budget_ceiling=budget)
        self.llm_adapter: LLMTaskAdapter | None = None
        if config.use_real_llm:
            self.llm_adapter = LLMTaskAdapter(
                model=config.llm_model,
                client=client,
                async_client=async_client,
                token_tracker=self.token_tracker,
                circuit_breaker=circuit_breaker,
                rate_limiter=self.rate_limiter,
            )

    def _load_dataset(self) -> list[EvalItem]:
        """Loads evaluation dataset from JSON or creates synthetic items."""
        items: list[EvalItem] = []
        if self.config.eval_dataset_file and self.config.eval_dataset_file.exists():
            try:
                items = load_eval_dataset(
                    dataset_path=self.config.eval_dataset_file,
                    skill_name=self.config.skill_name,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.error(f"Lỗi nạp dataset {self.config.eval_dataset_file}: {e}")

            if not items:
                try:
                    with open(self.config.eval_dataset_file, encoding="utf-8") as f:
                        raw_data = json.load(f)
                    if isinstance(raw_data, list):
                        for idx, row in enumerate(raw_data):
                            if isinstance(row, dict):
                                prompt = row.get("input_prompt") or row.get("prompt", "")
                                rubric = row.get("rubric", "")
                                cid = row.get("id", f"item_{idx:02d}")
                                items.append(EvalItem(id=cid, input_prompt=prompt, rubric=rubric))
                except Exception as e:
                    logger.error(f"Lỗi đọc raw JSON dataset: {e}")

        if not items:
            # Fallback default test items
            items = [
                EvalItem(
                    id="default_01",
                    input_prompt="Soạn thảo văn bản hành chính theo Nghị định 30/2020/NĐ-CP",
                    rubric="Phải tuân thủ thể thức Nghị định 30.",
                ),
                EvalItem(
                    id="default_02",
                    input_prompt="Kiểm tra bậc chịu lửa công trình theo QCVN 06:2022/BXD",
                    rubric="Phải xác định đúng bậc chịu lửa.",
                ),
            ]
        return items

    def preserve_yaml_frontmatter(self, original_content: str, edited_content: str) -> str:
        """Preserves YAML frontmatter metadata when mutating SKILL.md body."""
        return preserve_yaml_frontmatter(original_content, edited_content)

    def _build_eval_task(self, content: str) -> Callable[[EvalItem], Any]:
        """Resolves task callable (custom, real LLM, or domain mock simulation)."""
        if self.custom_task is not None:
            return self.custom_task

        if self.config.use_real_llm and self.llm_adapter is not None:
            return self.llm_adapter.create_async_eval_task(content)

        return build_mock_agent_task(
            content=content,
            skill_name=getattr(self.config, "skill_name", ""),
        )

    def _verify_eval_report(self, report: EvalReport) -> None:
        """Verifies report for circuit breaker or token budget failures and raises appropriate errors."""
        for item_res in report.item_results:
            if item_res.exception is not None:
                if isinstance(item_res.exception, CircuitBreakerOpenError):
                    raise item_res.exception
                if isinstance(item_res.exception, TokenBudgetExceededError):
                    raise item_res.exception
            if item_res.error:
                err_l = item_res.error.lower()
                if "circuit" in err_l and ("open" in err_l or "breaker" in err_l):
                    raise CircuitBreakerOpenError(item_res.error)
                if "token budget" in err_l and "exceeded" in err_l:
                    raise TokenBudgetExceededError(item_res.error)

        if self.token_tracker.is_exhausted:
            raise TokenBudgetExceededError(
                f"Token budget ceiling ({self.token_tracker.budget_ceiling:,} tokens) exceeded."
            )

    async def evaluate_content_async(
        self, content: str, dataset: list[EvalItem] | None = None
    ) -> EvalReport:
        """Asynchronously evaluates skill prompt content against test dataset.

        Native coroutine for running within existing asyncio event loops.
        """
        target_dataset = dataset if dataset is not None else self.tuning_dataset
        task = self._build_eval_task(content)
        concurrency = (
            self.config.max_concurrency
            if (self.config.use_real_llm and self.llm_adapter is not None)
            else None
        )
        report = await self.runner.run(
            dataset=target_dataset,
            task=task,
            scorers=self.scorers,
            max_concurrency=concurrency,
        )
        self._verify_eval_report(report)
        return report

    def evaluate_content(self, content: str, dataset: list[EvalItem] | None = None) -> EvalReport:
        """Synchronously evaluates given skill prompt content against test dataset (or tuning/holdout subset)."""
        target_dataset = dataset if dataset is not None else self.tuning_dataset
        task = self._build_eval_task(content)
        concurrency = (
            self.config.max_concurrency
            if (self.config.use_real_llm and self.llm_adapter is not None)
            else None
        )
        report = self.runner.run_sync(
            dataset=target_dataset,
            task=task,
            scorers=self.scorers,
            max_concurrency=concurrency,
        )
        self._verify_eval_report(report)
        return report

    def propose_mutation(self, current_content: str, iteration: int) -> str:
        """Generates a prompt mutation proposition based on multi-strategy optimization operators."""
        arch = resolve_domain_archetype(self.config.skill_name)
        arch_name = arch.name if arch else "general"

        all_strategies = load_mutation_strategies()
        strategies = all_strategies.get(arch_name) or all_strategies.get("general", [])

        if not strategies:
            return current_content

        # Extract only body to apply mutations, preserving frontmatter untouched
        fm_match = re.match(r"^\s*---\r?\n(.*?)\r?\n---\r?\n?", current_content, re.DOTALL)
        if fm_match:
            body = current_content[fm_match.end() :]
        else:
            body = current_content

        # Find first strategy not yet fully present in body (Goodhart's Law Trap Breaker)
        chosen_strategy = None
        base_idx = (iteration - 1) % len(strategies)
        norm_body = ADR_HEADER_TAG_REGEX.sub("", body).replace("\r\n", "\n")
        for offset in range(len(strategies)):
            idx = (base_idx + offset) % len(strategies)
            s_name, s_enhancement = strategies[idx]
            norm_enhancement = ADR_HEADER_TAG_REGEX.sub("", s_enhancement.strip()).replace(
                "\r\n", "\n"
            )
            if s_enhancement.strip() not in body and norm_enhancement not in norm_body:
                chosen_strategy = (s_name, s_enhancement)
                break

        # If all strategies are already applied, return current content untouched
        # (Cleanly triggers HALT_NO_FURTHER_STRATEGIES in optimization loop without junk comments)
        if chosen_strategy is None:
            return current_content

        _name, enhancement = chosen_strategy

        # Surgical Section Patching (Frontier 3)
        section_header = enhancement.strip().split("\n")[0]
        clean_header = ADR_HEADER_TAG_REGEX.sub("", section_header).strip()
        header_pattern = re.escape(clean_header)
        section_regex = re.compile(
            rf"(?m)^[ \t]*{header_pattern}(?P<adr_suffix>(?:[ \t]*\([^)\n\r]*(?:HUB[-_]ADR|ADR)[-_\s]*[0-9]+[^)\n\r]*\))+)?(?:[ \t]*\r?$)\r?\n?"
            r"(?P<section_body>.*?)(?=(?:\r?\n## |\Z))",
            re.DOTALL | re.IGNORECASE,
        )

        match = section_regex.search(body)
        if match:
            lines = enhancement.strip().split("\n")
            adr_suffix = match.group("adr_suffix")
            if adr_suffix:
                lines[0] = f"{clean_header}{adr_suffix}"
            effective_enhancement = "\n".join(lines)
            mutated_body = (
                body[: match.start()] + effective_enhancement.strip() + "\n" + body[match.end() :]
            )
        else:
            mutated_body = body.strip() + "\n\n" + enhancement.strip()

        # Compaction guard: prevent prompt bloat beyond ~300 lines
        lines = mutated_body.splitlines()
        if len(lines) > 300:
            cleaned_lines = [
                line
                for line in lines
                if not line.startswith("<!-- Ratchet Optimization Refinement")
                and not line.startswith("- Cập nhật quy chuẩn rà soát vòng")
            ]
            mutated_body = "\n".join(cleaned_lines)

        return self.preserve_yaml_frontmatter(current_content, mutated_body)

    def mutate_skill(self, current_content: str, iteration: int) -> str:
        """Mutates skill content by applying unapplied optimization strategies without junk comments."""
        return self.propose_mutation(current_content, iteration)

    def git_commit_improvement(self, score_diff: str) -> bool:
        """Commits target file change to Git repository."""
        if self.dry_run_git:
            logger.info(
                f"💾 [DRY-RUN] Git Commit: ratchet(opt): {self.target_file.name} {score_diff}"
            )
            return True

        try:
            rel_path = self.target_file.relative_to(self.project_root)
        except ValueError:
            rel_path = self.target_file

        rel_path_str = str(rel_path.as_posix())

        try:
            subprocess.run(
                ["git", "add", rel_path_str],
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            msg = f"ratchet(opt): {self.target_file.name} {score_diff}"
            subprocess.run(
                ["git", "commit", "-m", msg, "--", rel_path_str],
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            logger.info(f"✅ Git Commit thành công: '{msg}'")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Git commit thất bại: {e}")
            try:
                subprocess.run(
                    ["git", "restore", "--staged", rel_path_str],
                    cwd=str(self.project_root),
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception:
                pass
            return False

    def git_rollback_target(self, original_content: str, has_committed: bool = False) -> None:
        """Rolls back the target file either via git checkout or file overwrite."""
        try:
            self.target_file.write_text(original_content, encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to restore file content: {e}")

        try:
            rel_path = self.target_file.relative_to(self.project_root)
        except ValueError:
            rel_path = self.target_file

        rel_path_str = str(rel_path.as_posix())

        if not has_committed:
            try:
                subprocess.run(
                    ["git", "restore", "--staged", rel_path_str],
                    cwd=str(self.project_root),
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception:
                pass

        if self.dry_run_git or not has_committed:
            if self.dry_run_git:
                logger.info(f"⏪ [DRY-RUN] Git Rollback: {self.target_file.name}")
            return

        try:
            subprocess.run(
                ["git", "checkout", "--", rel_path_str],
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            logger.info(f"⏪ Đã khôi phục file qua 'git checkout -- {rel_path_str}'")
        except Exception:
            try:
                self.target_file.write_text(original_content, encoding="utf-8")
            except Exception:
                pass

    def _eval_sync(self, content: str, dataset: list[EvalItem] | None = None) -> EvalReport:
        """Internal synchronous evaluation dispatcher with backward-compatible mock signature handling."""
        if dataset is not None:
            try:
                return self.evaluate_content(content, dataset)
            except TypeError:
                return self.evaluate_content(content)
        return self.evaluate_content(content)

    async def _eval_async(self, content: str, dataset: list[EvalItem] | None = None) -> EvalReport:
        """Internal asynchronous evaluation dispatcher supporting both sync mocks and native coroutines."""
        if "evaluate_content_async" in self.__dict__ or hasattr(
            self.evaluate_content_async, "mock_calls"
        ):
            try:
                res_async = (
                    self.evaluate_content_async(content, dataset)
                    if dataset is not None
                    else self.evaluate_content_async(content)
                )
            except TypeError:
                res_async = self.evaluate_content_async(content)
            return (
                await res_async if inspect.isawaitable(res_async) else cast(EvalReport, res_async)
            )

        if "evaluate_content" in self.__dict__ or hasattr(self.evaluate_content, "mock_calls"):
            try:
                res_sync = (
                    self.evaluate_content(content, dataset)
                    if dataset is not None
                    else self.evaluate_content(content)
                )
            except TypeError:
                res_sync = self.evaluate_content(content)
            return await res_sync if inspect.isawaitable(res_sync) else res_sync

        return await self.evaluate_content_async(content, dataset)

    def _init_ratchet_budget(self, baseline_score: float) -> tuple[int, int]:
        """Calculates effective max iterations and patience based on baseline score."""
        if baseline_score >= 100.0:
            effective_max_iter = 1
            effective_patience = 1
        elif baseline_score >= 90.0:
            effective_max_iter = min(self.config.max_iterations, 5)
            effective_patience = min(self.config.patience, 2)
        else:
            effective_max_iter = min(self.config.max_iterations, 10)
            effective_patience = min(self.config.patience, 3)

        logger.info(f"🏁 Bắt đầu Git-Ratchet Loop cho {self.target_file.name}")
        logger.info(
            f"📊 Điểm chuẩn ban đầu (Baseline Score): {baseline_score:.2f}% | "
            f"Mục tiêu: {self.config.target_score}% | "
            f"Budget: {effective_max_iter} vòng (Patience={effective_patience})"
        )
        return effective_max_iter, effective_patience

    def _record_trial(
        self,
        iter_idx: int,
        score: float,
        crit_fails: int,
        decision: str,
        summary: str,
        t0: float,
        prev_tokens: tuple[int, int, int],
        state: _RatchetLoopState,
    ) -> None:
        """Appends a new RatchetTrialResult to loop state history."""
        trial = RatchetTrialResult(
            iteration=iter_idx,
            score=score,
            passed=(score >= self.config.target_score and crit_fails == 0),
            critical_fails=crit_fails,
            decision=decision,
            summary=summary,
            prompt_tokens=self.token_tracker.prompt_tokens - prev_tokens[0],
            completion_tokens=self.token_tracker.completion_tokens - prev_tokens[1],
            total_tokens=self.token_tracker.total_tokens - prev_tokens[2],
            latency_s=time.perf_counter() - t0,
        )
        state.history.append(trial)

    def _run_pre_eval_guards(
        self,
        mutated_content: str,
        iter_idx: int,
        t0: float,
        prev_tokens: tuple[int, int, int],
        state: _RatchetLoopState,
    ) -> bool:
        """Applies candidate mutation to disk and validates pre-eval invariants (ADRs, link integrity).

        Returns:
            True if mutation was rejected by pre-eval guards (and reverted), False if valid to evaluate.
        """
        self.target_file.write_text(mutated_content, encoding="utf-8")

        # Pillar 3: ADR Monotonic Token Guard (ADR-0058)
        best_adr_nums = set(ADR_REF_PATTERN.findall(state.best_content))
        mutated_adr_nums = set(ADR_REF_PATTERN.findall(mutated_content))
        dropped_adrs = sorted(
            [f"ADR-{int(num):04d}" for num in best_adr_nums if num not in mutated_adr_nums]
        )
        if dropped_adrs:
            dropped_str = ", ".join(dropped_adrs)
            logger.warning(
                f"⚠️ [PRE-EVAL FAST-FAIL] Từ chối mutation vì làm mất thẻ ADR bắt buộc: {dropped_str}"
            )
            self.git_rollback_target(state.best_content, has_committed=state.has_committed)
            state.reverted_count += 1
            state.stagnant_trials += 1
            summary = f"Từ chối mutation vì làm mất thẻ ADR: {dropped_str}"
            self._record_trial(
                iter_idx, state.best_score, 0, "REVERT", summary, t0, prev_tokens, state
            )
            return True

        # ADR-0058 Pre-Evaluation Working Tree Fast-Fail Guard
        link_issues = []
        try:
            if str(self.project_root) not in sys.path:
                sys.path.insert(0, str(self.project_root))
            from scripts.governance.link_auditor import LinkAuditor

            link_issues = [
                item_issue
                for item_issue in LinkAuditor(self.project_root).audit(self.target_file)
                if item_issue.category in ("links", "okf_links", "okf_conflicts")
            ]
        except Exception as e:
            logger.warning(f"⚠️ LinkAuditor check encountered error: {e}")

        if link_issues:
            logger.warning(
                f"⚠️ [PRE-EVAL FAST-FAIL] Từ chối mutation vì vi phạm liên kết ({link_issues[0].category}): {link_issues[0].message}"
            )
            self.git_rollback_target(state.best_content, has_committed=state.has_committed)
            state.reverted_count += 1
            state.stagnant_trials += 1
            summary = f"Từ chối mutation vì vi phạm liên kết: {link_issues[0].message}"
            self._record_trial(
                iter_idx, state.best_score, 0, "REVERT", summary, t0, prev_tokens, state
            )
            return True

        return False

    def _apply_trial_verdict(
        self,
        iter_idx: int,
        eval_report: EvalReport,
        mutated_content: str,
        t0: float,
        prev_tokens: tuple[int, int, int],
        state: _RatchetLoopState,
    ) -> None:
        """Evaluates trial results against ratchet criteria and executes commit/rollback."""
        current_score = eval_report.overall_score
        crit_fails = sum(1 for r in eval_report.item_results if r.critical_failed)

        if current_score > state.best_score and crit_fails == 0:
            diff_str = f"{state.best_score:.1f}% -> {current_score:.1f}% (+{current_score - state.best_score:.1f}%)"
            committed = self.git_commit_improvement(diff_str)
            if committed:
                state.has_committed = True
            state.best_score = current_score
            state.best_content = mutated_content
            state.kept_count += 1
            state.stagnant_trials = 0
            decision = "KEEP"
            summary = f"Cải thiện điểm số thành công: {diff_str}"
        else:
            self.git_rollback_target(state.best_content, has_committed=state.has_committed)
            state.reverted_count += 1
            state.stagnant_trials += 1
            decision = "REVERT"
            summary = (
                f"Không cải thiện (Score {current_score:.1f}% vs Best {state.best_score:.1f}%)"
                if crit_fails == 0
                else f"Vi phạm điều kiện nghiêm ngặt: {crit_fails} Điểm Liệt."
            )

        self._record_trial(
            iter_idx, current_score, crit_fails, decision, summary, t0, prev_tokens, state
        )
        logger.info(f"📌 Quyết định [{decision}]: {summary}")

    def _check_budget_and_early_stop(
        self,
        iter_idx: int,
        effective_patience: int,
        baseline_tokens: int,
        state: _RatchetLoopState,
    ) -> tuple[bool, str | None]:
        """Checks if optimization should halt due to target reached, token budgets, or early stopping."""
        if state.best_score >= self.config.target_score and not self.config.full_sweep:
            logger.info(
                f"🎉 Đã đạt điểm mục tiêu {self.config.target_score}% tại iteration {iter_idx}!"
            )
            return True, None

        # Hard max tokens per skill ceiling (regardless of kept_count) (Issue #368)
        mutation_tokens = self.token_tracker.total_tokens - baseline_tokens
        if (
            self.config.hard_max_tokens_per_skill is not None
            and mutation_tokens >= self.config.hard_max_tokens_per_skill
        ):
            logger.info(
                f"🛑 [HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED] Mutation tokens ({mutation_tokens:,}) "
                f"đã chạm ngưỡng trần tuyệt đối ({self.config.hard_max_tokens_per_skill:,}) sau {iter_idx} trials. "
                f"Dừng đột biến để bảo vệ ngân sách toàn đêm."
            )
            return True, "HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED"

        # Per-skill mutation budget check
        if (
            self.config.per_skill_mutation_budget is not None
            and mutation_tokens >= self.config.per_skill_mutation_budget
            and state.kept_count == 0
            and iter_idx >= 2
        ):
            logger.info(
                f"🛑 [PER_SKILL_TOKEN_BUDGET_EXCEEDED] Mutation tokens ({mutation_tokens:,}) "
                f"đã vượt trần ngân sách ({self.config.per_skill_mutation_budget:,}) sau {iter_idx} trials (kept_count=0)."
            )
            return True, "PER_SKILL_TOKEN_BUDGET_EXCEEDED"

        # Adaptive Early Stopping (Grilling Frontier 2)
        if effective_patience > 0 and state.stagnant_trials >= effective_patience:
            logger.info(
                f"🛑 [Adaptive Early Stopping] Dừng sớm sau {state.stagnant_trials} vòng liên tiếp không cải thiện điểm số (Patience={effective_patience})."
            )
            return True, None

        return False, None

    def _handle_iteration_exception(
        self,
        exc: Exception,
        iter_idx: int,
        t0: float,
        prev_tokens: tuple[int, int, int],
        state: _RatchetLoopState,
    ) -> tuple[str | None, bool]:
        """Handles loop exceptions, restores working tree, records trial, and determines halt status."""
        self.git_rollback_target(state.best_content, has_committed=state.has_committed)
        state.reverted_count += 1
        if isinstance(exc, TokenBudgetExceededError):
            logger.error(f"🛑 [Token Budget Halt] {exc}")
            self._record_trial(
                iter_idx, 0.0, 1, "REVERT", f"Dừng sớm: {exc}", t0, prev_tokens, state
            )
            return "TOKEN_BUDGET_EXCEEDED", True
        elif isinstance(exc, CircuitBreakerOpenError):
            logger.error(f"⚡ [Circuit Breaker Fast-Fail] {exc}")
            self._record_trial(
                iter_idx,
                0.0,
                1,
                "REVERT",
                "Dừng sớm: Circuit Breaker ngắt kết nối AI Gateway (Fast-fail).",
                t0,
                prev_tokens,
                state,
            )
            return "CIRCUIT_BREAKER_OPEN", True
        else:
            logger.error(f"Error during iteration {iter_idx}: {exc}")
            self._record_trial(
                iter_idx, 0.0, 1, "REVERT", f"Lỗi thực thi vòng lặp: {exc}", t0, prev_tokens, state
            )
            return None, False

    def _finalize_disk_state(self, initial_content: str, state: _RatchetLoopState) -> None:
        """Ensures target file on disk matches expected final state."""
        if self.target_file.exists():
            try:
                final_target = (
                    initial_content
                    if (self.dry_run_git or not state.has_committed)
                    else state.best_content
                )
                current_disk = self.target_file.read_text(encoding="utf-8")
                if current_disk != final_target:
                    self.git_rollback_target(final_target, has_committed=state.has_committed)
            except Exception as e:
                logger.error(f"Error restoring disk file: {e}")

    def _build_init_error_report(
        self, init_err: TokenBudgetExceededError | CircuitBreakerOpenError
    ) -> RatchetReport:
        """Constructs an immediate halt report when baseline evaluation fails."""
        logger.error(f"Lỗi trong quá trình chấm điểm ban đầu: {init_err}")
        reason = (
            "CIRCUIT_BREAKER_OPEN"
            if isinstance(init_err, CircuitBreakerOpenError)
            else "TOKEN_BUDGET_EXCEEDED"
        )
        slicing_tier_str = self.sliced_data.tier.value if self.sliced_data else None
        return RatchetReport(
            target_file=str(self.target_file),
            initial_score=0.0,
            final_score=0.0,
            total_iterations=0,
            kept_commits=0,
            reverted_trials=0,
            history=[],
            total_tokens=self.token_tracker.total_tokens,
            prompt_tokens=self.token_tracker.prompt_tokens,
            completion_tokens=self.token_tracker.completion_tokens,
            avg_latency_s=self.token_tracker.avg_latency_s,
            halt_reason=reason,
            slicing_tier=slicing_tier_str,
            tuning_size=len(self.tuning_dataset),
            holdout_size=len(self.holdout_dataset),
        )

    def _build_final_report(
        self,
        baseline_score: float,
        initial_holdout_score: float | None,
        final_holdout_score: float | None,
        halt_reason: str | None,
        state: _RatchetLoopState,
    ) -> RatchetReport:
        """Synthesizes final RatchetReport from session state and holdout metrics."""
        slicing_tier_str = self.sliced_data.tier.value if self.sliced_data else None
        return RatchetReport(
            target_file=str(self.target_file),
            initial_score=baseline_score,
            final_score=state.best_score,
            total_iterations=len(state.history),
            kept_commits=state.kept_count,
            reverted_trials=state.reverted_count,
            history=state.history,
            total_tokens=self.token_tracker.total_tokens,
            prompt_tokens=self.token_tracker.prompt_tokens,
            completion_tokens=self.token_tracker.completion_tokens,
            avg_latency_s=self.token_tracker.avg_latency_s,
            halt_reason=halt_reason,
            slicing_tier=slicing_tier_str,
            tuning_size=len(self.tuning_dataset),
            holdout_size=len(self.holdout_dataset),
            holdout_score=final_holdout_score,
            holdout_initial_score=initial_holdout_score,
        )

    def _token_snapshot(self) -> tuple[int, int, int]:
        """Takes a snapshot of current token counters (prompt, completion, total)."""
        return (
            self.token_tracker.prompt_tokens,
            self.token_tracker.completion_tokens,
            self.token_tracker.total_tokens,
        )

    def _propose_candidate(
        self, iter_idx: int, state: _RatchetLoopState
    ) -> tuple[str | None, str | None]:
        """Proposes a mutation candidate and validates uniqueness against seen hashes."""
        mutated = self.propose_mutation(state.best_content, iter_idx)
        if mutated == state.best_content:
            logger.info(
                f"🛑 [HALT_NO_FURTHER_STRATEGIES] Không còn chiến lược mới nào chưa áp dụng. Dừng sạch tại iteration {iter_idx}."
            )
            return None, "HALT_NO_FURTHER_STRATEGIES"

        content_hash = hashlib.sha256(mutated.encode("utf-8")).hexdigest()
        if content_hash in state.seen_hashes:
            logger.info(
                f"🛑 [HALT_NO_FURTHER_STRATEGIES] Đột biến trùng lặp ({content_hash[:8]}). Dừng sớm."
            )
            return None, "HALT_NO_FURTHER_STRATEGIES"
        state.seen_hashes.add(content_hash)
        return mutated, None

    def _eval_holdout_base_sync(self, content: str) -> float | None:
        """Evaluates baseline holdout dataset synchronously if configured."""
        if not self.holdout_dataset:
            return None
        try:
            report = self._eval_sync(content, dataset=self.holdout_dataset)
            score = report.overall_score
            logger.info(
                f"🔒 Holdout Baseline Score: {score:.2f}% ({len(self.holdout_dataset)} items)"
            )
            return score
        except Exception as e:
            logger.warning(f"Không thể chấm điểm holdout ban đầu: {e}")
            return None

    def _eval_holdout_final_sync(
        self, best_content: str, initial_score: float | None, kept_count: int
    ) -> float | None:
        """Evaluates final holdout score synchronously, reusing baseline when kept_count == 0."""
        if not self.holdout_dataset:
            return None
        if kept_count == 0 and initial_score is not None:
            logger.info(
                f"🎯 Holdout Final Score: {initial_score:.2f}% (Tái sử dụng Baseline do kept_count == 0, bỏ qua re-eval)"
            )
            return initial_score
        try:
            report = self._eval_sync(best_content, dataset=self.holdout_dataset)
            score = report.overall_score
            logger.info(f"🎯 Holdout Final Score: {score:.2f}% (Baseline: {initial_score}%)")
            return score
        except Exception as e:
            logger.warning(f"Không thể chấm điểm holdout cuối: {e}")
            return None

    async def _eval_holdout_base_async(self, content: str) -> float | None:
        """Evaluates baseline holdout dataset asynchronously if configured."""
        if not self.holdout_dataset:
            return None
        try:
            report = await self._eval_async(content, dataset=self.holdout_dataset)
            score = report.overall_score
            logger.info(
                f"🔒 Holdout Baseline Score: {score:.2f}% ({len(self.holdout_dataset)} items)"
            )
            return score
        except Exception as e:
            logger.warning(f"Không thể chấm điểm holdout ban đầu: {e}")
            return None

    async def _eval_holdout_final_async(
        self, best_content: str, initial_score: float | None, kept_count: int
    ) -> float | None:
        """Evaluates final holdout score asynchronously, reusing baseline when kept_count == 0."""
        if not self.holdout_dataset:
            return None
        if kept_count == 0 and initial_score is not None:
            logger.info(
                f"🎯 Holdout Final Score: {initial_score:.2f}% (Tái sử dụng Baseline do kept_count == 0, bỏ qua re-eval)"
            )
            return initial_score
        try:
            report = await self._eval_async(best_content, dataset=self.holdout_dataset)
            score = report.overall_score
            logger.info(f"🎯 Holdout Final Score: {score:.2f}% (Baseline: {initial_score}%)")
            return score
        except Exception as e:
            logger.warning(f"Không thể chấm điểm holdout cuối: {e}")
            return None

    def run(self) -> RatchetReport:
        """Executes the full ratchet autonomous optimization loop synchronously."""
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        initial_content = self.target_file.read_text(encoding="utf-8")
        try:
            baseline_report = self._eval_sync(initial_content)
        except (TokenBudgetExceededError, CircuitBreakerOpenError) as init_err:
            return self._build_init_error_report(init_err)

        baseline_score = baseline_report.overall_score
        baseline_tokens = self.token_tracker.total_tokens
        effective_max_iter, effective_patience = self._init_ratchet_budget(baseline_score)
        state = _RatchetLoopState(
            best_score=baseline_score,
            best_content=initial_content,
            seen_hashes={hashlib.sha256(initial_content.encode("utf-8")).hexdigest()},
        )
        initial_holdout_score = self._eval_holdout_base_sync(initial_content)
        halt_reason: str | None = None

        try:
            for i in range(1, effective_max_iter + 1):
                logger.info(f"🔄 --- Iteration {i}/{effective_max_iter} ---")
                prev_tokens, t0 = self._token_snapshot(), time.perf_counter()
                try:
                    mutated, cand_halt = self._propose_candidate(i, state)
                    if cand_halt:
                        halt_reason = cand_halt
                        break
                    if not mutated or self._run_pre_eval_guards(mutated, i, t0, prev_tokens, state):
                        continue

                    eval_report = self._eval_sync(mutated)
                    self._apply_trial_verdict(i, eval_report, mutated, t0, prev_tokens, state)
                    should_stop, stop_reason = self._check_budget_and_early_stop(
                        i, effective_patience, baseline_tokens, state
                    )
                    if should_stop:
                        if stop_reason:
                            halt_reason = stop_reason
                        break
                except Exception as exc:
                    exc_halt, should_break = self._handle_iteration_exception(
                        exc, i, t0, prev_tokens, state
                    )
                    if exc_halt:
                        halt_reason = exc_halt
                    if should_break:
                        break
        finally:
            self._finalize_disk_state(initial_content, state)

        final_holdout_score = self._eval_holdout_final_sync(
            state.best_content, initial_holdout_score, state.kept_count
        )
        return self._build_final_report(
            baseline_score, initial_holdout_score, final_holdout_score, halt_reason, state
        )

    async def run_async(self) -> RatchetReport:
        """Executes the full ratchet autonomous optimization loop asynchronously.

        Native coroutine for running within existing asyncio event loops.
        """
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        initial_content = self.target_file.read_text(encoding="utf-8")
        try:
            baseline_report = await self._eval_async(initial_content)
        except (TokenBudgetExceededError, CircuitBreakerOpenError) as init_err:
            return self._build_init_error_report(init_err)

        baseline_score = baseline_report.overall_score
        baseline_tokens = self.token_tracker.total_tokens
        effective_max_iter, effective_patience = self._init_ratchet_budget(baseline_score)
        state = _RatchetLoopState(
            best_score=baseline_score,
            best_content=initial_content,
            seen_hashes={hashlib.sha256(initial_content.encode("utf-8")).hexdigest()},
        )
        initial_holdout_score = await self._eval_holdout_base_async(initial_content)
        halt_reason: str | None = None

        try:
            for i in range(1, effective_max_iter + 1):
                logger.info(f"🔄 --- Iteration {i}/{effective_max_iter} ---")
                prev_tokens, t0 = self._token_snapshot(), time.perf_counter()
                try:
                    mutated, cand_halt = self._propose_candidate(i, state)
                    if cand_halt:
                        halt_reason = cand_halt
                        break
                    if not mutated or self._run_pre_eval_guards(mutated, i, t0, prev_tokens, state):
                        continue

                    eval_report = await self._eval_async(mutated)
                    self._apply_trial_verdict(i, eval_report, mutated, t0, prev_tokens, state)
                    should_stop, stop_reason = self._check_budget_and_early_stop(
                        i, effective_patience, baseline_tokens, state
                    )
                    if should_stop:
                        if stop_reason:
                            halt_reason = stop_reason
                        break
                except Exception as exc:
                    exc_halt, should_break = self._handle_iteration_exception(
                        exc, i, t0, prev_tokens, state
                    )
                    if exc_halt:
                        halt_reason = exc_halt
                    if should_break:
                        break
        finally:
            self._finalize_disk_state(initial_content, state)

        final_holdout_score = await self._eval_holdout_final_async(
            state.best_content, initial_holdout_score, state.kept_count
        )
        return self._build_final_report(
            baseline_score, initial_holdout_score, final_holdout_score, halt_reason, state
        )


# Public alias for backwards compatibility
GitRatchetTuner = GitRatchetOptimizer


def mutate_skill(content: str, iteration: int, skill_name: str = "generic") -> str:
    """Mutates skill content by applying unapplied optimization strategies without junk comments."""
    from pathlib import Path

    cfg = RatchetConfig(target_file=Path("SKILL.md"), skill_name=skill_name)
    optimizer = GitRatchetOptimizer(cfg, dry_run_git=True)
    return optimizer.propose_mutation(content, iteration)
