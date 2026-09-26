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

from .models import EvalItem, EvalReport
from .runner import EvalRunner, load_eval_dataset
from .scorers import (
    BaseScorer,
)
from .simulation import create_domain_mock_agent_task
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


@dataclass
class TokenUsageTracker:
    """Session-wide token consumption tracker and circuit breaker observer."""

    budget_ceiling: int = 5_000_000
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_calls: int = 0
    total_latency_s: float = 0.0
    warning_triggered: bool = False
    halt_triggered: bool = False
    reserved_tokens: int = 0

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
        latency_threshold_s: float = 4.0,
        backoff_multiplier: float = 1.5,
        sleeper: Callable[[float], None] = time.sleep,
        time_fn: Callable[[], float] = time.monotonic,
        async_sleeper: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.requests_per_minute = max(1.0, requests_per_minute)
        self.min_interval = 60.0 / self.requests_per_minute
        self.min_delay_s = min_delay_s
        self.max_delay_s = max_delay_s
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
        self.model = model or os.getenv("CCBA_TUNER_MODEL", "gemini-3.7-flash-high")
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
    target_score: float = 90.0
    max_iterations: int = 10
    allowed_files: list[str] = field(default_factory=list)
    prohibited_files: list[str] = field(default_factory=list)
    skill_name: str = ""
    full_sweep: bool = False
    patience: int = 3
    use_real_llm: bool = False
    llm_model: str = ""
    token_budget: int | None = None
    rate_limiter: RateLimiter | None = None
    enable_adaptive_slicing: bool = True
    split_ratio: float = 0.7
    slicing_seed: int = 42
    enable_perturbation: bool = True
    per_skill_mutation_budget: int | None = cast(Any, _UNSET)
    hard_max_tokens_per_skill: int | None = cast(Any, _UNSET)
    max_concurrency: int = cast(Any, _UNSET)

    def __post_init__(self) -> None:
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
            self.llm_model = os.getenv("CCBA_TUNER_MODEL", "gemini-3.7-flash-high")
        if self.token_budget is not None:
            if isinstance(self.token_budget, str):
                try:
                    self.token_budget = int(self.token_budget.replace(",", "").replace("_", ""))
                except ValueError:
                    self.token_budget = 5_000_000
        else:
            env_budget = os.getenv("CCBA_TUNER_TOKEN_BUDGET")
            if env_budget:
                try:
                    self.token_budget = int(env_budget.replace(",", "").replace("_", ""))
                except ValueError:
                    self.token_budget = 5_000_000
            else:
                self.token_budget = 5_000_000

        # Configuration Precedence via Sentinel (Issue #368): User > Env > Default
        if self.per_skill_mutation_budget is not _UNSET:
            if isinstance(self.per_skill_mutation_budget, str):
                try:
                    self.per_skill_mutation_budget = int(
                        self.per_skill_mutation_budget.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.per_skill_mutation_budget = 250_000
        else:
            env_ps_budget = os.getenv("CCBA_TUNER_PER_SKILL_MUTATION_BUDGET")
            if env_ps_budget:
                try:
                    self.per_skill_mutation_budget = int(
                        env_ps_budget.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.per_skill_mutation_budget = 250_000
            else:
                self.per_skill_mutation_budget = 250_000

        if self.hard_max_tokens_per_skill is not _UNSET:
            if isinstance(self.hard_max_tokens_per_skill, str):
                try:
                    self.hard_max_tokens_per_skill = int(
                        self.hard_max_tokens_per_skill.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.hard_max_tokens_per_skill = 500_000
        else:
            env_hard_max = os.getenv("CCBA_TUNER_HARD_MAX_PER_SKILL")
            if env_hard_max:
                try:
                    self.hard_max_tokens_per_skill = int(
                        env_hard_max.replace(",", "").replace("_", "")
                    )
                except ValueError:
                    self.hard_max_tokens_per_skill = 500_000
            else:
                self.hard_max_tokens_per_skill = 500_000

        if self.max_concurrency is not _UNSET:
            if isinstance(self.max_concurrency, str):
                try:
                    self.max_concurrency = int(self.max_concurrency)
                except ValueError:
                    self.max_concurrency = 5
        else:
            env_concurrency = os.getenv("CCBA_TUNER_CONCURRENCY")
            if env_concurrency:
                try:
                    self.max_concurrency = int(env_concurrency)
                except ValueError:
                    self.max_concurrency = 5
            else:
                self.max_concurrency = 5

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


class _RatchetSession:
    """Encapsulates mutable loop state and shared trial transitions for GitRatchetOptimizer."""

    def __init__(self, optimizer: GitRatchetOptimizer) -> None:
        self.opt = optimizer
        self.target_file = optimizer.target_file
        self.initial_content = self.target_file.read_text(encoding="utf-8")
        self.halt_reason: str | None = None
        self.best_score: float = 0.0
        self.best_content: str = self.initial_content
        self.baseline_score: float = 0.0
        self.baseline_tokens: int = 0
        self.effective_max_iter: int = 1
        self.effective_patience: int = 1
        self.has_committed: bool = False
        self.kept_count: int = 0
        self.reverted_count: int = 0
        self.stagnant_trials: int = 0
        self.seen_hashes: set[str] = {
            hashlib.sha256(self.initial_content.encode("utf-8")).hexdigest()
        }
        self.history: list[RatchetTrialResult] = []
        self.initial_holdout_score: float | None = None

    def build_init_error_report(
        self, init_err: TokenBudgetExceededError | CircuitBreakerOpenError
    ) -> RatchetReport:
        logger.error(f"Lỗi trong quá trình chấm điểm ban đầu: {init_err}")
        reason = (
            "CIRCUIT_BREAKER_OPEN"
            if isinstance(init_err, CircuitBreakerOpenError)
            else "TOKEN_BUDGET_EXCEEDED"
        )
        slicing_tier_str = self.opt.sliced_data.tier.value if self.opt.sliced_data else None
        return RatchetReport(
            target_file=str(self.target_file),
            initial_score=0.0,
            final_score=0.0,
            total_iterations=0,
            kept_commits=0,
            reverted_trials=0,
            history=[],
            total_tokens=self.opt.token_tracker.total_tokens,
            prompt_tokens=self.opt.token_tracker.prompt_tokens,
            completion_tokens=self.opt.token_tracker.completion_tokens,
            avg_latency_s=self.opt.token_tracker.avg_latency_s,
            halt_reason=reason,
            slicing_tier=slicing_tier_str,
            tuning_size=len(self.opt.tuning_dataset),
            holdout_size=len(self.opt.holdout_dataset),
        )

    def init_baseline(self, baseline_report: EvalReport) -> None:
        self.baseline_score = baseline_report.overall_score
        self.best_score = self.baseline_score
        self.baseline_tokens = self.opt.token_tracker.total_tokens

        # Tiered budget & patience based on baseline score (ADR-0023 / Grilling Frontier 2)
        if self.baseline_score >= 100.0:
            self.effective_max_iter = 1
            self.effective_patience = 1
        elif self.baseline_score >= 90.0:
            self.effective_max_iter = min(self.opt.config.max_iterations, 5)
            self.effective_patience = min(self.opt.config.patience, 2)
        else:
            self.effective_max_iter = min(self.opt.config.max_iterations, 10)
            self.effective_patience = min(self.opt.config.patience, 3)

        logger.info(f"🏁 Bắt đầu Git-Ratchet Loop cho {self.target_file.name}")
        logger.info(
            f"📊 Điểm chuẩn ban đầu (Baseline Score): {self.baseline_score:.2f}% | Mục tiêu: {self.opt.config.target_score}% | Budget: {self.effective_max_iter} vòng (Patience={self.effective_patience})"
        )

    def prepare_mutation(
        self, i: int, iter_t0: float, prev_p: int, prev_c: int, prev_tot: int
    ) -> tuple[str | None, bool]:
        logger.info(f"🔄 --- Iteration {i}/{self.effective_max_iter} ---")
        mutated_content = self.opt.propose_mutation(self.best_content, i)
        if mutated_content == self.best_content:
            logger.info(
                f"🛑 [HALT_NO_FURTHER_STRATEGIES] Không còn chiến lược mới nào chưa áp dụng. Dừng sạch tại iteration {i}."
            )
            self.halt_reason = "HALT_NO_FURTHER_STRATEGIES"
            return None, False

        content_hash = hashlib.sha256(mutated_content.encode("utf-8")).hexdigest()
        if content_hash in self.seen_hashes:
            logger.info(
                f"🛑 [HALT_NO_FURTHER_STRATEGIES] Đột biến trùng lặp ({content_hash[:8]}). Dừng sớm."
            )
            self.halt_reason = "HALT_NO_FURTHER_STRATEGIES"
            return None, False
        self.seen_hashes.add(content_hash)

        # Apply candidate mutation
        self.target_file.write_text(mutated_content, encoding="utf-8")

        # Pillar 3: ADR Monotonic Token Guard (ADR-0058)
        best_adr_nums = set(ADR_REF_PATTERN.findall(self.best_content))
        mutated_adr_nums = set(ADR_REF_PATTERN.findall(mutated_content))
        dropped_adrs = sorted(
            [f"ADR-{int(num):04d}" for num in best_adr_nums if num not in mutated_adr_nums]
        )
        if dropped_adrs:
            dropped_str = ", ".join(dropped_adrs)
            logger.warning(
                f"⚠️ [PRE-EVAL FAST-FAIL] Từ chối mutation vì làm mất thẻ ADR bắt buộc: {dropped_str}"
            )
            self.opt.git_rollback_target(self.best_content, has_committed=self.has_committed)
            self.reverted_count += 1
            self.stagnant_trials += 1
            summary = f"Từ chối mutation vì làm mất thẻ ADR: {dropped_str}"
            self._record_trial(
                i, self.best_score, 0, "REVERT", summary, iter_t0, prev_p, prev_c, prev_tot
            )
            return None, True

        # ADR-0058 Pre-Evaluation Working Tree Fast-Fail Guard
        link_issues = []
        try:
            if str(self.opt.project_root) not in sys.path:
                sys.path.insert(0, str(self.opt.project_root))
            from scripts.governance.link_auditor import LinkAuditor

            link_issues = [
                item_issue
                for item_issue in LinkAuditor(self.opt.project_root).audit(self.target_file)
                if item_issue.category in ("links", "okf_links", "okf_conflicts")
            ]
        except Exception as e:
            logger.warning(f"⚠️ LinkAuditor check encountered error: {e}")

        if link_issues:
            logger.warning(
                f"⚠️ [PRE-EVAL FAST-FAIL] Từ chối mutation vì vi phạm liên kết ({link_issues[0].category}): {link_issues[0].message}"
            )
            self.opt.git_rollback_target(self.best_content, has_committed=self.has_committed)
            self.reverted_count += 1
            self.stagnant_trials += 1
            summary = f"Từ chối mutation vì vi phạm liên kết: {link_issues[0].message}"
            self._record_trial(
                i, self.best_score, 0, "REVERT", summary, iter_t0, prev_p, prev_c, prev_tot
            )
            return None, True

        return mutated_content, True

    def process_eval_report(
        self,
        i: int,
        mutated_content: str,
        report: EvalReport,
        iter_t0: float,
        prev_p: int,
        prev_c: int,
        prev_tot: int,
    ) -> bool:
        current_score = report.overall_score
        crit_fails = sum(1 for r in report.item_results if r.critical_failed)

        # Ratchet decision
        if current_score > self.best_score and crit_fails == 0:
            diff_str = f"{self.best_score:.1f}% -> {current_score:.1f}% (+{current_score - self.best_score:.1f}%)"
            committed = self.opt.git_commit_improvement(diff_str)
            if committed:
                self.has_committed = True
            self.best_score = current_score
            self.best_content = mutated_content
            self.kept_count += 1
            self.stagnant_trials = 0
            decision = "KEEP"
            summary = f"Cải thiện điểm số thành công: {diff_str}"
        else:
            self.opt.git_rollback_target(self.best_content, has_committed=self.has_committed)
            self.reverted_count += 1
            self.stagnant_trials += 1
            decision = "REVERT"
            summary = (
                f"Không cải thiện (Score {current_score:.1f}% vs Best {self.best_score:.1f}%)"
                if crit_fails == 0
                else f"Vi phạm điều kiện nghiêm ngặt: {crit_fails} Điểm Liệt."
            )

        self._record_trial(
            i, current_score, crit_fails, decision, summary, iter_t0, prev_p, prev_c, prev_tot
        )
        logger.info(f"📌 Quyết định [{decision}]: {summary}")

        if self.best_score >= self.opt.config.target_score and not self.opt.config.full_sweep:
            logger.info(
                f"🎉 Đã đạt điểm mục tiêu {self.opt.config.target_score}% tại iteration {i}!"
            )
            return False

        # Hard max tokens per skill ceiling (regardless of kept_count) (Issue #368)
        mutation_tokens = self.opt.token_tracker.total_tokens - self.baseline_tokens
        if (
            self.opt.config.hard_max_tokens_per_skill is not None
            and mutation_tokens >= self.opt.config.hard_max_tokens_per_skill
        ):
            logger.info(
                f"🛑 [HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED] Mutation tokens ({mutation_tokens:,}) đã chạm ngưỡng trần tuyệt đối ({self.opt.config.hard_max_tokens_per_skill:,}) sau {i} trials. Dừng đột biến để bảo vệ ngân sách toàn đêm."
            )
            self.halt_reason = "HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED"
            return False

        # Per-skill mutation budget check
        if (
            self.opt.config.per_skill_mutation_budget is not None
            and mutation_tokens >= self.opt.config.per_skill_mutation_budget
            and self.kept_count == 0
            and i >= 2
        ):
            logger.info(
                f"🛑 [PER_SKILL_TOKEN_BUDGET_EXCEEDED] Mutation tokens ({mutation_tokens:,}) đã vượt trần ngân sách ({self.opt.config.per_skill_mutation_budget:,}) sau {i} trials (kept_count=0)."
            )
            self.halt_reason = "PER_SKILL_TOKEN_BUDGET_EXCEEDED"
            return False

        # Adaptive Early Stopping (Grilling Frontier 2)
        if self.effective_patience > 0 and self.stagnant_trials >= self.effective_patience:
            logger.info(
                f"🛑 [Adaptive Early Stopping] Dừng sớm sau {self.stagnant_trials} vòng liên tiếp không cải thiện điểm số (Patience={self.effective_patience})."
            )
            return False

        return True

    def _record_trial(
        self,
        i: int,
        score: float,
        crit_fails: int,
        decision: str,
        summary: str,
        iter_t0: float,
        prev_p: int,
        prev_c: int,
        prev_tot: int,
    ) -> None:
        trial = RatchetTrialResult(
            iteration=i,
            score=score,
            passed=(score >= self.opt.config.target_score and crit_fails == 0),
            critical_fails=crit_fails,
            decision=decision,
            summary=summary,
            prompt_tokens=self.opt.token_tracker.prompt_tokens - prev_p,
            completion_tokens=self.opt.token_tracker.completion_tokens - prev_c,
            total_tokens=self.opt.token_tracker.total_tokens - prev_tot,
            latency_s=time.perf_counter() - iter_t0,
        )
        self.history.append(trial)

    def handle_budget_error(
        self,
        i: int,
        err: TokenBudgetExceededError,
        iter_t0: float,
        prev_p: int,
        prev_c: int,
        prev_tot: int,
    ) -> None:
        logger.error(f"🛑 [Token Budget Halt] {err}")
        self.opt.git_rollback_target(self.best_content, has_committed=self.has_committed)
        self.reverted_count += 1
        self.halt_reason = "TOKEN_BUDGET_EXCEEDED"
        self._record_trial(
            i, 0.0, 1, "REVERT", f"Dừng sớm: {err}", iter_t0, prev_p, prev_c, prev_tot
        )

    def handle_circuit_breaker_error(
        self,
        i: int,
        err: CircuitBreakerOpenError,
        iter_t0: float,
        prev_p: int,
        prev_c: int,
        prev_tot: int,
    ) -> None:
        logger.error(f"⚡ [Circuit Breaker Fast-Fail] {err}")
        self.opt.git_rollback_target(self.best_content, has_committed=self.has_committed)
        self.reverted_count += 1
        self.halt_reason = "CIRCUIT_BREAKER_OPEN"
        self._record_trial(
            i,
            0.0,
            1,
            "REVERT",
            "Dừng sớm: Circuit Breaker ngắt kết nối AI Gateway (Fast-fail).",
            iter_t0,
            prev_p,
            prev_c,
            prev_tot,
        )

    def handle_iteration_error(
        self, i: int, err: Exception, iter_t0: float, prev_p: int, prev_c: int, prev_tot: int
    ) -> None:
        logger.error(f"Error during iteration {i}: {err}")
        self.opt.git_rollback_target(self.best_content, has_committed=self.has_committed)
        self.reverted_count += 1
        self._record_trial(
            i, 0.0, 1, "REVERT", f"Lỗi thực thi vòng lặp: {err}", iter_t0, prev_p, prev_c, prev_tot
        )

    def finalize_disk(self) -> None:
        if self.target_file.exists():
            try:
                final_target = self.initial_content if self.opt.dry_run_git else self.best_content
                current_disk = self.target_file.read_text(encoding="utf-8")
                if current_disk != final_target:
                    self.opt.git_rollback_target(final_target, has_committed=self.has_committed)
            except Exception as e:
                logger.error(f"Error restoring disk file: {e}")

    def build_report(self, final_holdout_score: float | None = None) -> RatchetReport:
        slicing_tier_str = self.opt.sliced_data.tier.value if self.opt.sliced_data else None
        return RatchetReport(
            target_file=str(self.target_file),
            initial_score=self.baseline_score,
            final_score=self.best_score,
            total_iterations=len(self.history),
            kept_commits=self.kept_count,
            reverted_trials=self.reverted_count,
            history=self.history,
            total_tokens=self.opt.token_tracker.total_tokens,
            prompt_tokens=self.opt.token_tracker.prompt_tokens,
            completion_tokens=self.opt.token_tracker.completion_tokens,
            avg_latency_s=self.opt.token_tracker.avg_latency_s,
            halt_reason=self.halt_reason,
            slicing_tier=slicing_tier_str,
            tuning_size=len(self.opt.tuning_dataset),
            holdout_size=len(self.opt.holdout_dataset),
            holdout_score=final_holdout_score,
            holdout_initial_score=self.initial_holdout_score,
        )


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

        return create_domain_mock_agent_task(
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

        if arch_name == "academic":
            strategies = [
                (
                    "CARS 3-Move Blueprint & Sentence Stems",
                    "\n\n## Khung Mẫu CARS 3-Move Chi Tiết & Mẫu Câu Học Thuật (Sentence Stems)\n"
                    "* **Move 1 (Establish Territory):** Dùng các mẫu câu: *'Recent advances in... have heightened the need for...', 'A central issue in... is...'*.\n"
                    "* **Move 2 (Find a Niche):** Dùng các mẫu câu: *'However, previous studies have largely overlooked...', 'A critical limitation of current methods is...'*.\n"
                    "* **Move 3 (Occupy Niche):** Dùng các mẫu câu: *'To address this gap, this paper proposes...', 'The principal contribution of this study is threefold...'*",
                ),
                (
                    "Yale Academic Style & De-nominalization Invariants",
                    "\n\n## Quy Chuẩn Văn Phong Khoa Học & Loại Bỏ Danh Từ Hóa (Yale Style Guide)\n"
                    "* **Quy tắc cấm tuyệt đối:** Không sử dụng trạng từ khuếch đại chủ quan (`clearly`, `obviously`, `really`, `very`, `basically`).\n"
                    "* **Khử danh từ hóa (De-nominalization):** Bắt buộc chuyển đổi cụm từ rườm rà thành động từ hành động trực tiếp:\n"
                    "  - `conduct an investigation into` -> `investigate`\n"
                    "  - `reach a conclusion that` -> `conclude that`\n"
                    "  - `give an explanation of` -> `explain`",
                ),
                (
                    "Discussion Zoom-out Framework & Limitation Disclosure",
                    "\n\n## Khung Cấu Trúc Thảo Luận Mở Rộng (Discussion Zoom-out) & Thừa Nhận Giới Hạn\n"
                    "* Cấu trúc phần Discussion bắt buộc đi qua 3 tầng phân tích:\n"
                    "  1. **Tầng 1 (Major Findings):** Trả lời trực tiếp câu hỏi nghiên cứu đặt ra ở Mở bài.\n"
                    "  2. **Tầng 2 (Context & Limitations):** So sánh với các nghiên cứu đối chuẩn và **bắt buộc dành tối thiểu 1 đoạn văn nêu rõ các giới hạn phương pháp luận (Methodological Limitations)**.\n"
                    "  3. **Tầng 3 (Implications & Future Work):** Đề xuất ứng dụng thực tiễn và định hướng mở rộng.",
                ),
                (
                    "APA 7th Edition & BibTeX Standards Integration",
                    "\n\n## Chuẩn Hóa Trích Dẫn APA 7th & Khối Mã BibTeX Song Hành\n"
                    "* Mọi tài liệu tham khảo trong bài báo bắt buộc phải trình bày song hành dưới 2 định dạng:\n"
                    "  - Định dạng trích dẫn văn bản chuẩn **APA 7th Edition** (Author, Year, Title, Journal, DOI).\n"
                    "  - Khối mã **BibTeX** chuẩn hóa để các nhà nghiên cứu có thể trích xuất trực tiếp vào LaTeX/Overleaf.",
                ),
                (
                    "Peer-Review Self-Assessment Checklist",
                    "\n\n## Bảng Kiểm Tự Phản Biện Học Thuật (Peer-Review Checklist)\n"
                    "* Trước khi xuất bản bản thảo, Agent tự đối soát qua 4 tiêu chí phản biện độc lập:\n"
                    "  - [ ] Mục tiêu nghiên cứu ở Introduction có khớp 100% với kết luận ở Discussion không?\n"
                    "  - [ ] Phương pháp thực nghiệm ở Methods có đủ chi tiết để phòng thí nghiệm khác tái lập (reproducibility) không?\n"
                    "  - [ ] Các hình ảnh, bảng biểu đã có chú thích và đơn vị đo lường đầy đủ chưa?\n"
                    "  - [ ] Không có bất kỳ câu văn nào mang định kiến cảm xúc cá nhân.",
                ),
            ]
        elif arch_name == "bim_governance":
            strategies = [
                (
                    "Golden Thread & Security Classification Invariants",
                    "\n\n## Kiểm Duyệt Sợi Chỉ Vàng & Phân Cấp An Ninh ISO 19650-5\n"
                    "* **Sợi Chỉ Vàng (Golden Thread):** Cưỡng chế quản trị dữ liệu tài sản tầm nhìn 75 năm (PM_80), chống đứt gãy thông tin qua các thế hệ chuyển giao.\n"
                    "* **Phân cấp an ninh ST2:** Toàn bộ thông tin tài sản phải được phân loại và gắn thẻ an ninh đạt cấp độ ST2 theo ISO 19650-5.\n"
                    "* **Đoạn Đò-3 & LMS Lock-in:** Đảm bảo dữ liệu bàn giao tích hợp đầy đủ ICT protocol tương thích LMS, triệt tiêu rủi ro LMS vendor lock-in.",
                ),
                (
                    "Red Thread Risk Matrix & Operational Verification",
                    "\n\n## Rào Chắn Sợi Chỉ Đỏ & Ma Trận Rủi Ro Thông Tin Chuẩn Hóa\n"
                    "* **Bộ 4 mã rủi ro thông tin:** Tuyệt đối không dùng mô tả tự do, bắt buộc nhận diện chính xác:\n"
                    "  - `RK_50_40_35` (No-Risk): Bàn giao C2 thiếu người nhận hoặc không khớp sơ đồ tổ chức.\n"
                    "  - `RK_10_70_04` (Time-Risk): Nghiệm thu C1 thiếu đội ngũ FM hoặc quy trình tự vận hành.\n"
                    "  - `RK_50_40_45` (Do-Risk): Không tuân thủ cấu trúc IFC hoặc thiếu ICT protocol đồng bộ.\n"
                    "  - `RK_50_60_28` (Use-Risk): Thiếu AIM hoàn thiện dẫn đến đứt gãy Trí Nhớ Số (En_25_70_47).",
                ),
                (
                    "Unique ID Invariance & 3-Way Traceability Guardrails",
                    "\n\n## Cưỡng Chế Unique ID Bất Biến & Đối Soát 3 Chiều\n"
                    "* **Khóa Unique ID từ BBP-A0:** Cấp và khóa mã Unique ID bất biến ngay từ pha BBP-A0, nghiêm cấm đổi tên ở các pha sau.\n"
                    "* **Đối soát 3 chiều (3-Way Traceability):** Kiểm tra đối soát bắt buộc: Bản vẽ thiết kế == Hệ thống AIM == Biển hiệu thực tế tại công trình.\n"
                    "* **Chống trôi dạt định danh:** Bắt buộc gắn cờ không đạt khi phát hiện bất kỳ sai lệch ký tự nào giữa 3 phương tiện đối soát.",
                ),
            ]
        elif arch_name == "bim_rase":
            strategies = [
                (
                    "RASE Decomposition & 4-Tier Logic Matrix",
                    "\n\n## Phân Rã Ma Trận RASE & Cấu Trúc 4 Tầng Logic\n"
                    "* **R - Requirement:** Xác định chỉ số kỹ thuật hoặc ngưỡng tới hạn bắt buộc phải đạt được.\n"
                    "* **A - Applicability:** Xác định thực thể IFC cụ thể chịu sự điều chỉnh (ví dụ: `IfcSpace`, `IfcWall`).\n"
                    "* **S - Selection:** Khai báo chính xác thuộc tính IFC4X3 lưu trữ thông số thông qua `IfcRelDefinesByProperties`.\n"
                    "* **E - Exception:** Xác định điều kiện loại trừ không cần áp dụng quy tắc kiểm soát.",
                ),
                (
                    "IFC4X3 Property Mapping & Indirect Relationship Invariants",
                    "\n\n## Quy Chuẩn Gán Thuộc Tính IFC4X3 & Quan Hệ Gián Tiếp Bắt Buộc\n"
                    "* **Cấm gán trực tiếp:** Tuyệt đối không gán thuộc tính trực tiếp vào `IfcObject`.\n"
                    "* **Quan hệ trung gian:** Mọi thuộc tính phải được đóng gói trong `IfcPropertySet` (Pset_) và liên kết qua `IfcRelDefinesByProperties`.\n"
                    "* **Đồng bộ ISO 16739-1:** Đảm bảo kiểu dữ liệu thuộc tính khớp chính xác với định nghĩa schema IFC4X3.",
                ),
                (
                    "Quantity Take-Off (Qto) Integration & BaseQuantities Mapping",
                    "\n\n## Tích Hợp Dữ Liệu Khối Lượng Qto & BaseQuantities\n"
                    "* **Khối lượng không gian:** Sử dụng `Qto_SpaceBaseQuantities` (GrossVolume, NetFloorArea) cho các chỉ số thông gió và tải trọng.\n"
                    "* **Khối lượng cấu kiện:** Sử dụng `Qto_WallBaseQuantities`, `Qto_SlabBaseQuantities` cho các chỉ tiêu truyền nhiệt và kết cấu.\n"
                    "* **Bảo toàn Trí Nhớ Số:** Kết nối ma trận RASE với Unique ID để duy trì tính truy nguyên xuyên suốt vòng đời công trình.",
                ),
            ]
        elif arch_name == "bim":
            strategies = [
                (
                    "BIM Classification Rules & ISO Alignment",
                    "\n\n## Quy Tắc Phân Tầng Uniclass & Chuẩn ISO Nền Tảng\n"
                    "* **Bảng phân loại Uniclass 200:** Co (Complexes) -> En (Entities) -> SL (Spaces) -> EF (Elements) -> Ss (Systems) -> Pr (Products) -> PM (Project Management).\n"
                    "* **Tuân thủ ISO 12006-2:2015 & ISO 22274:** Phân tách rõ ràng giữa Resources, Processes, Results, Properties.\n"
                    "* **Quy ước đặt tên ISO 19650 & IFC Alignment:** Đảm bảo tính nhất quán định danh Container cho mọi BIM Object.\n"
                    "* **Bảo tồn Trí Nhớ Số (Digital Memory):** Đảm bảo tính nhất quán định danh Container và cấu trúc dữ liệu cho mọi BIM Object.",
                ),
                (
                    "Digital Memory & Spatial Structure Invariants",
                    "\n\n## Bất Biến Trí Nhớ Số (Digital Memory) & Cấu Trúc Không Gian (Spatial Structure)\n"
                    "* **Trí Nhớ Số (Digital Memory):** Chuyển hóa toàn bộ dữ liệu mô hình BIM thành tài sản thông tin dài hạn kế thừa suốt vòng đời.\n"
                    "* **IFC4X3 Spatial Hierarchy:** Ánh xạ cấu trúc không gian chuẩn xác từ Site -> Building -> Floor -> Space/Room.",
                ),
                (
                    "BIM WBS & IFC Entity Mapping",
                    "\n\n## Phân Rã WBS Chuẩn ISO 21511 & Ánh Xạ Thực Thể IFC4X3\n"
                    "* **WBS Level 1-4:** Phân cấp cấu trúc công việc tích hợp mã phân loại chi phí và tiến độ.\n"
                    "* **IFC Entity Alignment:** Đồng bộ các lớp IfcSystem, IfcProduct, IfcSpace theo tiêu chuẩn OpenBIM.",
                ),
                (
                    "Red-Team Disambiguation & Slang Normalization Invariants",
                    "\n\n## Rào Chắn Phân Định Bẫy Red-Team & Chuẩn Hóa Lỗi Viết Tắt\n"
                    "* **Bẫy Hộp Kỹ Thuật (Hybrid Enclosure):** Phân loại vỏ hộp bao che là `EF_25_10` (Kiến trúc Result), chứa các hệ thống MEP con `Ss` bên trong.\n"
                    "* **Bẫy Viết Tắt (Slang Normalization):** Tự động chuẩn hóa `btct` -> Bê tông cốt thép (`EF_20_20`), `san T3` -> `L03`, `mc D800` -> Móng cọc (`EF_20_10`).\n"
                    "* **Bẫy Hai Góc Nhìn (Result vs Resource):** Bóc tách rõ `EF_25_30` (Mô hình BIM Object Result) vs `Pr_30_59_24` (Mua sắm BOQ Resource) bảo tồn Trí Nhớ Số.\n"
                    "* **Bẫy Khoang Đệm Ngăn Cháy (Airlock Buffer):** Bắt buộc phân loại là `SL_25_30_70` (Không gian đệm an toàn/Air-lock).\n"
                    "* **Bẫy Tường Vây vs Vách Ngăn:** Phân định kết cấu ngầm `EF_20_05` (Tường vây Barrette) tách biệt với vách thạch cao `EF_25_10`.\n"
                    "* **Bẫy Thang Máy Đa Góc Nhìn:** Phân định Mô hình kiến trúc `EF_25_50` vs Hệ thống cơ điện `Ss_70_50_10`.\n"
                    "* **Bẫy Sơn Chống Cháy & Trạm Kiosk:** Phân định vật tư `Pr_60_60_15` vs Property Set kết cấu, Thực thể quy hoạch `En_50_10` vs Hệ thống `Ss_70_10_10`.\n"
                    "* **Định danh Tuyến Hạ tầng IFC Alignment & ISO 19650:** Định danh cấu trúc không gian Spatial Structure và Trí Nhớ Số dọc tim tuyến (KM).",
                ),
            ]
        elif arch_name == "coding":
            strategies = [
                (
                    "Operational Invariants & Hard Completion Lock",
                    "\n\n## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất\n"
                    "* **Tiêu chí hoàn thành tất định:** Mọi thay đổi mã nguồn, kỹ năng hoặc tài liệu bắt buộc phải vượt qua bộ kiểm thử tự động.\n"
                    "* **Hard Completion Lock:** Nghiêm cấm tuyên bố hoàn thành task hoặc yêu cầu nghiệm thu nếu lệnh xác minh chưa vượt qua:\n"
                    "  ```bash\n"
                    "  python -m ccba_harness verify-patch\n"
                    "  ```\n"
                    "* **Zero Tolerance Exit Code:** Lệnh kiểm thử phải thoát với mã exit code 0; tuyệt đối không bỏ qua các lỗi linter hay hồi quy.",
                ),
                (
                    "Double-Pass Review Discipline & Verification Invariants",
                    "\n\n## Kỷ Luật Rà Soát Hai Vòng (Double-Pass Adversarial Review)\n"
                    "* **Vòng 1 (Code-First Research):** Luôn đọc implementation thực tế và kiểm tra data flow end-to-end trước khi sửa đổi. Không suy đoán hành vi từ tên hàm hay docstring.\n"
                    "* **Vòng 2 (Self-Adversarial Review):** Tự đặt câu hỏi: *Đề xuất này có thể SAI ở đâu?* Kiểm chứng tối thiểu 3 giả định cốt lõi bằng dữ liệu và kiểm thử thực tế trước khi bàn giao.\n"
                    "* **Bảo tồn Invariants:** Không bao giờ xóa hoặc nới lỏng (weaken) các bài test hiện có để làm cho bài test vượt qua.",
                ),
                (
                    "KISS, Idempotency & Explicit Error Handling Guardrails",
                    "\n\n## Chuẩn Mực Thiết Kế Mã Nguồn: KISS, Idempotency & Error Handling\n"
                    "* **KISS (Keep It Simple, Stupid):** Ưu tiên giải pháp đơn giản nhất; không tạo abstraction/seam giả định khi chưa có ít nhất 2 adapter thực tế.\n"
                    "* **Idempotency:** Mọi script thao tác tệp, database hay git worktree phải đảm bảo tính lũy kế an toàn (chạy nhiều lần cho ra cùng một kết quả vững chắc).\n"
                    "* **Explicit Error Handling:** Xử lý ngoại lệ cụ thể (Specific Exceptions); nghiêm cấm sử dụng bare `except:` hoặc nuốt lỗi âm thầm.\n"
                    "* **Type Hints & Docstrings:** Mọi hàm/phương thức public bắt buộc có type annotations đầy đủ và docstrings chuẩn mực.",
                ),
            ]
        elif arch_name == "orchestration":
            strategies = [
                (
                    "Deterministic Routing & Boundary Invariants",
                    "\n\n## Bất Biến Ranh Giới Điều Phối, Single-Writer & Handoff Protocol\n"
                    "* **Single-Writer & Isolated Sandbox:** Duy nhất Lead Orchestrator ghi nhận dữ liệu chính thức; subagents chỉ xuất kết quả trung gian vào sandbox `.agents/<agent_name>/scratch/`.\n"
                    "* **Handoff Protocol & Autonomous Notification:** Chuyển giao ngữ cảnh qua `send_message` gửi parent agent kèm báo cáo bàn giao (handoff report) và kết luận hoàn tất (`verdict`).\n"
                    "* **Bộc Lộ Dần (Progressive Disclosure):** Tổ chức tài liệu và chỉ dẫn theo [Hiến pháp AGENTS.md](../../AGENTS.md) tuân thủ mô hình bộc lộ dần theo cấp độ.\n"
                    "* **Hard Completion Lock:** Bắt buộc vượt qua xác minh tất định `python -m ccba_harness verify-patch` trước khi hoàn tất.",
                ),
            ]
        elif arch_name == "tech_qc":
            strategies = [
                (
                    "QCVN 06:2022/BXD & Map 1 Invariants",
                    "\n\n## Quy Chuẩn Kỹ Thuật PCCC QCVN 06:2022/BXD & Bảng Đối Soát Bậc H.1 (Map 1)\n"
                    "* **Bậc chịu lửa & Chiều cao:** Nhà nhóm F1.3 có chiều cao PCCC > 50m bắt buộc phải thiết kế Bậc chịu lửa Bậc I (Bảng H.1).\n"
                    "* **Kiểm soát khói:** Hành lang dài > 15m không có thông gió tự nhiên bắt buộc phải trang bị hệ thống hút khói cơ khí sự cố và van ngăn khói.\n"
                    "* **Thang bộ thoát nạn:** Nhà có chiều cao PCCC > 28m bắt buộc sử dụng buồng thang bộ không nhiễm khói loại N1 hoặc N2/N3 có hệ thống tăng áp.",
                ),
                (
                    "Fire Compartment & Structural Protection Hard Floor",
                    "\n\n## Rào Chắn Chống Cháy Lan & Giới Hạn Chịu Lửa Kết Cấu QCVN 06:2022/BXD\n"
                    "* **Kết cấu chịu lực chính:** Kết cấu chịu lực chính và giàn mái công trình Bậc I bắt buộc đạt giới hạn chịu lửa R45/R90/R120; nghiêm cấm để thép trần.\n"
                    "* **Ngăn cháy lan qua tường:** Ống dẫn gió xuyên qua tường ngăn cháy bắt buộc phải lắp van ngăn cháy tự động và bọc cách nhiệt đạt EI tương ứng.",
                ),
                (
                    "PCCC Evacuation & Dead-End Corridor Limits",
                    "\n\n## Giới Hạn Khoảng Cách Thoát Nạn Hành Lang Cụt QCVN 06:2022/BXD\n"
                    "* **Khoảng cách thoát nạn:** Khoảng cách thoát nạn từ cửa phòng đến buồng thang bộ ở hành lang cụt tối đa chỉ từ 15m - 20m (hoặc 25m nếu có chữa cháy tự động).\n"
                    "* **Cơ quan thẩm tra:** Phân định rõ thẩm quyền: Công an PC07 thẩm duyệt hệ thống PCCC MEP; Cơ quan chuyên môn về xây dựng thẩm tra kiến trúc và thoát nạn.",
                ),
            ]
        elif arch_name == "legal":
            strategies = [
                (
                    "XML Envelopes & Strict Output Schema",
                    "\n\n## Quy Chuẩn Đóng Gói Phản Hồi & Thẻ Cấu Trúc XML\n"
                    "* Mọi kết quả tra cứu và phân tích pháp lý bắt buộc phải được đóng gói qua cấu trúc thẻ:\n"
                    "  - `<legal_context>`: Tóm tắt bối cảnh và văn bản quy phạm pháp luật áp dụng (Luật, Nghị định, Thông tư).\n"
                    "  - `<legal_citation>`: Viện dẫn chính xác Điều, Khoản, Điểm kèm trích dẫn nguyên văn.\n"
                    "  - `<compliance_verdict>`: Kết luận tuân thủ pháp luật và khuyến nghị chuyên môn.\n"
                    "* Đảm bảo không phát sinh disclaimer từ chối đối với các yêu cầu hợp lệ trong lĩnh vực xây dựng.",
                ),
                (
                    "Hard-Floor Legal Guardrails (Cấm Viện Dẫn Văn Bản Hết Hiệu Lực)",
                    "\n\n## Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)\n"
                    "* **TUYỆT ĐỐI KHÔNG** trích dẫn các văn bản quy phạm pháp luật đã hết hiệu lực thi hành hoặc bị thay thế:\n"
                    "  - Nghị định 136/2020/NĐ-CP -> Bắt buộc sử dụng **Nghị định 105/2025/NĐ-CP**.\n"
                    "  - QCVN 06:2020/BXD -> Bắt buộc sử dụng **QCVN 06:2022/BXD & Sửa đổi 1:2023**.\n"
                    "  - Thông tư 149/2020/TT-BCA -> Bắt buộc tra cứu văn bản cập nhật mới nhất.\n"
                    "* Mọi vi phạm trích dẫn văn bản hết hiệu lực sẽ bị đánh rớt ngay lập tức (Hard Floor Fail-Fast: 0.0%).",
                ),
                (
                    "AST Mapping & Flat Index Synchronization",
                    "\n\n## Đồng Bộ Cây Cấu Trúc AST & Danh Mục Điều Khoản (clauses.json)\n"
                    "* Khi bóc tách văn bản quy phạm pháp luật, Agent phải đối soát với danh mục `clauses.json`:\n"
                    "  - Cấu trúc cây: Chương -> Mục -> Điều -> Khoản -> Điểm.\n"
                    "  - Đặt ID điều khoản chuẩn hóa (ví dụ: `dieu-1`, `dieu-2`) hỗ trợ liên kết chéo hai chiều (Cross-References).\n"
                    "  - Bảo tồn 100% các bảng số liệu và phụ lục đính kèm theo định dạng Markdown bảng chuẩn.",
                ),
                (
                    "Grounded Authority & Issuing Body Verification",
                    "\n\n## Xác Thực Thẩm Quyền Ban Hành & Số Hiệu Pháp Lý\n"
                    "* Mọi kết quả trích dẫn pháp luật phải nêu rõ:\n"
                    "  1. Cơ quan ban hành (Chính phủ, Bộ Xây dựng, Bộ Công an, Quốc hội).\n"
                    "  2. Số/Ký hiệu văn bản, ngày ban hành và ngày có hiệu lực thi hành.\n"
                    "  3. Mối quan hệ pháp lý (Văn bản hướng dẫn, Sửa đổi bổ sung, hoặc Thay thế) qua 11 nhóm quan hệ TVPL.",
                ),
                (
                    "Evaluator-Optimizer Self-Correction Loop",
                    "\n\n## Vòng Lặp Tự Kiểm Định & Hiệu Chỉnh Trước Khi Trả Lời (Self-Healing Loop)\n"
                    "* Trước khi hoàn tất câu trả lời, Agent tự kích hoạt checklist 3 bước:\n"
                    "  - Bước 1: Kiểm tra xem có trích dẫn đúng số hiệu văn bản đang còn hiệu lực không.\n"
                    "  - Bước 2: Kiểm tra xem các câu hỏi về thủ tục/thẩm định có viện dẫn đầy đủ căn cứ không.\n"
                    "  - Bước 3: Đảm bảo độ sâu phân tích đạt yêu cầu và không bỏ sót các điều khoản loại trừ/ngoại lệ.",
                ),
            ]
        else:
            strategies = [
                (
                    "Lean Structural Architecture & Progressive Disclosure",
                    "\n\n## Bộc Lộ Dần & Cấu Trúc Tinh Gọn (Progressive Disclosure)\n"
                    "* **Cấu trúc tài liệu Level 3:** Phân tách rõ ràng giữa quy trình cốt lõi và tài liệu hướng dẫn chuyên sâu qua bảng chỉ mục Level 3.\n"
                    "* **Tham chiếu liên kết:** Mọi tài liệu mở rộng tuân thủ cơ chế bộc lộ dần theo cấp độ (Level 1/2/3 Progressive Disclosure) và được dẫn xuất qua bảng chỉ mục Level 3.\n"
                    "* **Chống rác dữ liệu (Anti-Debris Invariant):** Không để lại comment nháp, TODO tạm thời hay các chỉ thị thừa không cần thiết.",
                ),
                (
                    "Operational Clarity & Verification Standard",
                    "\n\n## Chuẩn Mực Vận Hành & Khảo Sát Kiểm Chứng\n"
                    "* **Ranh giới trách nhiệm rõ ràng:** Phân tách rành mạch dữ liệu đầu vào và kết quả đầu ra.\n"
                    "* **Kiểm chứng độc lập:** Đối soát kết quả với các tiêu chuẩn tham chiếu trước khi nghiệm thu.",
                ),
            ]

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

    def run(self) -> RatchetReport:
        """Executes the full ratchet autonomous optimization loop synchronously."""
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        session = _RatchetSession(self)
        try:
            baseline_report = self._eval_sync(session.initial_content)
        except (TokenBudgetExceededError, CircuitBreakerOpenError) as init_err:
            return session.build_init_error_report(init_err)

        session.init_baseline(baseline_report)

        if self.holdout_dataset:
            try:
                holdout_base = self._eval_sync(
                    session.initial_content, dataset=self.holdout_dataset
                )
                session.initial_holdout_score = holdout_base.overall_score
                logger.info(
                    f"🔒 Holdout Baseline Score: {session.initial_holdout_score:.2f}% ({len(self.holdout_dataset)} items)"
                )
            except Exception as e:
                logger.warning(f"Không thể chấm điểm holdout ban đầu: {e}")

        try:
            for i in range(1, session.effective_max_iter + 1):
                prev_p = self.token_tracker.prompt_tokens
                prev_c = self.token_tracker.completion_tokens
                prev_tot = self.token_tracker.total_tokens
                t0 = time.perf_counter()

                try:
                    mutated, can_continue = session.prepare_mutation(
                        i, t0, prev_p, prev_c, prev_tot
                    )
                    if not can_continue:
                        break
                    if mutated is None:
                        continue

                    report = self._eval_sync(mutated)
                    if not session.process_eval_report(
                        i, mutated, report, t0, prev_p, prev_c, prev_tot
                    ):
                        break
                except TokenBudgetExceededError as budget_err:
                    session.handle_budget_error(i, budget_err, t0, prev_p, prev_c, prev_tot)
                    break
                except CircuitBreakerOpenError as cb_err:
                    session.handle_circuit_breaker_error(i, cb_err, t0, prev_p, prev_c, prev_tot)
                    break
                except Exception as iter_err:
                    session.handle_iteration_error(i, iter_err, t0, prev_p, prev_c, prev_tot)
        finally:
            session.finalize_disk()

        final_holdout_score: float | None = None
        if self.holdout_dataset:
            if session.kept_count == 0 and session.initial_holdout_score is not None:
                final_holdout_score = session.initial_holdout_score
                logger.info(
                    f"🎯 Holdout Final Score: {final_holdout_score:.2f}% (Tái sử dụng Baseline do kept_count == 0, bỏ qua re-eval)"
                )
            else:
                try:
                    holdout_final = self._eval_sync(
                        session.best_content, dataset=self.holdout_dataset
                    )
                    final_holdout_score = holdout_final.overall_score
                    logger.info(
                        f"🎯 Holdout Final Score: {final_holdout_score:.2f}% (Baseline: {session.initial_holdout_score}%)"
                    )
                except Exception as e:
                    logger.warning(f"Không thể chấm điểm holdout cuối: {e}")

        return session.build_report(final_holdout_score)

    async def run_async(self) -> RatchetReport:
        """Executes the full ratchet autonomous optimization loop asynchronously.

        Native coroutine for running within existing asyncio event loops.
        """
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        session = _RatchetSession(self)
        try:
            baseline_report = await self._eval_async(session.initial_content)
        except (TokenBudgetExceededError, CircuitBreakerOpenError) as init_err:
            return session.build_init_error_report(init_err)

        session.init_baseline(baseline_report)

        if self.holdout_dataset:
            try:
                holdout_base = await self._eval_async(
                    session.initial_content, dataset=self.holdout_dataset
                )
                session.initial_holdout_score = holdout_base.overall_score
                logger.info(
                    f"🔒 Holdout Baseline Score: {session.initial_holdout_score:.2f}% ({len(self.holdout_dataset)} items)"
                )
            except Exception as e:
                logger.warning(f"Không thể chấm điểm holdout ban đầu: {e}")

        try:
            for i in range(1, session.effective_max_iter + 1):
                prev_p = self.token_tracker.prompt_tokens
                prev_c = self.token_tracker.completion_tokens
                prev_tot = self.token_tracker.total_tokens
                t0 = time.perf_counter()

                try:
                    mutated, can_continue = session.prepare_mutation(
                        i, t0, prev_p, prev_c, prev_tot
                    )
                    if not can_continue:
                        break
                    if mutated is None:
                        continue

                    report = await self._eval_async(mutated)
                    if not session.process_eval_report(
                        i, mutated, report, t0, prev_p, prev_c, prev_tot
                    ):
                        break
                except TokenBudgetExceededError as budget_err:
                    session.handle_budget_error(i, budget_err, t0, prev_p, prev_c, prev_tot)
                    break
                except CircuitBreakerOpenError as cb_err:
                    session.handle_circuit_breaker_error(i, cb_err, t0, prev_p, prev_c, prev_tot)
                    break
                except Exception as iter_err:
                    session.handle_iteration_error(i, iter_err, t0, prev_p, prev_c, prev_tot)
        finally:
            session.finalize_disk()

        final_holdout_score: float | None = None
        if self.holdout_dataset:
            if session.kept_count == 0 and session.initial_holdout_score is not None:
                final_holdout_score = session.initial_holdout_score
                logger.info(
                    f"🎯 Holdout Final Score: {final_holdout_score:.2f}% (Tái sử dụng Baseline do kept_count == 0, bỏ qua re-eval)"
                )
            else:
                try:
                    holdout_final = await self._eval_async(
                        session.best_content, dataset=self.holdout_dataset
                    )
                    final_holdout_score = holdout_final.overall_score
                    logger.info(
                        f"🎯 Holdout Final Score: {final_holdout_score:.2f}% (Baseline: {session.initial_holdout_score}%)"
                    )
                except Exception as e:
                    logger.warning(f"Không thể chấm điểm holdout cuối: {e}")

        return session.build_report(final_holdout_score)


# Public alias for backwards compatibility
GitRatchetTuner = GitRatchetOptimizer


def mutate_skill(content: str, iteration: int, skill_name: str = "generic") -> str:
    """Mutates skill content by applying unapplied optimization strategies without junk comments."""
    from pathlib import Path

    cfg = RatchetConfig(target_file=Path("SKILL.md"), skill_name=skill_name)
    optimizer = GitRatchetOptimizer(cfg, dry_run_git=True)
    return optimizer.propose_mutation(content, iteration)
