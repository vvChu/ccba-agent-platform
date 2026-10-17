"""tuner.py - Autonomous Git-Ratchet Prompt & Skill Optimizer (ADR-0023).

Adapted from Andrej Karpathy's autoresearch paradigm (Propose -> Evaluate -> Keep/Revert via Git).
Optimizes AI skill prompts (SKILL.md) and prompt templates iteratively, committing on score
improvements and instantly rolling back (git checkout / file restore) on regressions or critical failures.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ._tuner_llm import (
    AdaptiveRateLimiter,
    AIClient,
    AsyncAIClient,
    CircuitBreaker,
    CircuitBreakerOpenError,
    LLMTaskAdapter,
    TokenUsageTracker,
)
from ._tuner_models import (
    _UNSET,
    ADR_HEADER_TAG_REGEX,
    ADR_REF_PATTERN,
    DEFAULT_MUTATION_STRATEGIES_PATH,
    GitMutexLock,
    RatchetConfig,
    RatchetReport,
    RatchetTrialResult,
    RateLimiter,
    TokenBudgetExceededError,
    _detect_program_root,
    _RatchetLoopState,
    _RatchetSession,
    _resolve_cfg_bool,
    _resolve_cfg_float,
    _resolve_cfg_int,
    load_mutation_strategies,
    load_tuner_config,
    reload_mutation_strategies,
    reload_tuner_config,
)
from ._tuner_mutator import (
    _RatchetMutationGitMixin,
    preserve_yaml_frontmatter,
    remaining_strategies,
)
from .archetypes import (
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
from .legal_index import LegalFlatIndex, load_legal_flat_index
from .models import EvalItem, EvalReport
from .runner import EvalRunner, load_eval_dataset
from .scorers import BaseScorer
from .simulation import build_mock_agent_task
from .slicing import AdaptiveDataSlicer, SlicedDataset

logger = logging.getLogger("ccba.eval.ratchet")


class GitRatchetOptimizer(_RatchetMutationGitMixin):
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
        git_lock: GitMutexLock | None = None,
        lock_enabled: bool = True,
    ) -> None:
        self.config = config
        self.target_file = Path(config.target_file).resolve()
        self.dry_run_git = dry_run_git
        self.custom_task = task
        self.client = client
        self.async_client = async_client
        self.circuit_breaker = circuit_breaker
        self.rate_limiter = rate_limiter or config.rate_limiter

        _lock_active = lock_enabled and not dry_run_git
        self.git_lock = git_lock if git_lock is not None else GitMutexLock(enabled=_lock_active)
        self.project_root = self._resolve_project_root(
            project_root if project_root is not None else root
        )
        if git_lock is None and self.git_lock.lock_path is None and self.git_lock.enabled:
            self.git_lock.lock_path = self._resolve_default_lock_path()

        self.scorers = scorers or get_default_domain_scorers(config.skill_name)
        self.runner = EvalRunner(
            default_pass_threshold=config.target_score, max_concurrency=config.max_concurrency
        )
        self.dataset: list[EvalItem] = dataset if dataset is not None else self._load_dataset()
        self._init_slicing_and_llm(config, client, async_client, circuit_breaker)

    def _resolve_project_root(self, effective_root: Path | None) -> Path:
        """Resolves repository root from explicit argument or target_file ancestors."""
        if effective_root is not None:
            return Path(effective_root).resolve()
        cur = self.target_file.parent
        for p in [cur, *cur.parents]:
            if (p / ".git").exists() or (p / ".agents").exists() or (p / "pyproject.toml").exists():
                return p
        return Path.cwd().resolve()

    def _resolve_default_lock_path(self) -> Path:
        """Resolves default Git mutex lock path supporting both standard repos and git worktrees."""
        git_entry = self.project_root / ".git"
        if git_entry.is_file():
            try:
                content = git_entry.read_text(encoding="utf-8").strip()
                if content.startswith("gitdir:"):
                    gitdir = Path(content.split(":", 1)[1].strip())
                    if not gitdir.is_absolute():
                        gitdir = (self.project_root / gitdir).resolve()
                    return gitdir / "evals_tuner.lock"
            except Exception:
                pass
            return self.project_root / ".evals_tuner.lock"
        return git_entry / "evals_tuner.lock"

    def _init_slicing_and_llm(
        self,
        config: RatchetConfig,
        client: Any | None,
        async_client: Any | None,
        circuit_breaker: Any | None,
    ) -> None:
        """Initializes dataset slicing, token tracker, LLMTaskAdapter, and failure mutator state."""
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

        self._applied_failure_patches: int = 0
        self._applied_fingerprints: set[str] = set()
        try:
            self.legal_index: LegalFlatIndex | None = load_legal_flat_index()
        except Exception:
            self.legal_index = None

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
        """Asynchronously evaluates skill prompt content against test dataset."""
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

        if "_eval_sync" in self.__dict__ or hasattr(self._eval_sync, "mock_calls"):
            try:
                res_sync_override = (
                    self._eval_sync(content, dataset)
                    if dataset is not None
                    else self._eval_sync(content)
                )
            except TypeError:
                res_sync_override = self._eval_sync(content)
            return (
                await res_sync_override
                if inspect.isawaitable(res_sync_override)
                else res_sync_override
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

    async def _close_async_resources(self) -> None:
        """Closes owned AsyncAIClient HTTP transport before the event loop terminates."""
        if self.async_client is not None:
            return
        if (
            self.llm_adapter is not None
            and getattr(self.llm_adapter, "async_client", None) is not None
        ):
            aclose_fn = getattr(self.llm_adapter.async_client, "aclose", None)
            if callable(aclose_fn):
                try:
                    res = aclose_fn()
                    if inspect.isawaitable(res):
                        await res
                except Exception:
                    pass

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

    def _has_sync_eval_override(self) -> bool:
        """Returns True if any synchronous evaluation method was overridden on this instance."""
        for attr in (
            "_eval_sync",
            "evaluate_content",
            "_eval_holdout_base_sync",
            "_eval_holdout_final_sync",
        ):
            if attr in self.__dict__ or hasattr(getattr(self, attr, None), "mock_calls"):
                return True
        return False

    def _run_sync_iterations(
        self,
        effective_max_iter: int,
        effective_patience: int,
        baseline_tokens: int,
        state: _RatchetLoopState,
    ) -> str | None:
        """Executes synchronous ratchet optimization iterations and returns optional halt_reason."""
        halt_reason: str | None = None
        for i in range(1, effective_max_iter + 1):
            logger.info(f"🔄 --- Iteration {i}/{effective_max_iter} ---")
            prev_tokens, t0 = self._token_snapshot(), time.perf_counter()
            try:
                mutated, cand_halt = self._propose_candidate(i, state)
                if cand_halt:
                    return cand_halt
                if not mutated or self._run_pre_eval_guards(mutated, i, t0, prev_tokens, state):
                    continue
                eval_report = self._eval_sync(mutated)
                self._apply_trial_verdict(i, eval_report, mutated, t0, prev_tokens, state)
                should_stop, stop_reason = self._check_budget_and_early_stop(
                    i, effective_patience, baseline_tokens, state
                )
                if should_stop:
                    return stop_reason or halt_reason
            except Exception as exc:
                exc_halt, should_break = self._handle_iteration_exception(
                    exc, i, t0, prev_tokens, state
                )
                if exc_halt:
                    halt_reason = exc_halt
                if should_break:
                    break
        return halt_reason

    async def _run_async_iterations(
        self,
        effective_max_iter: int,
        effective_patience: int,
        baseline_tokens: int,
        state: _RatchetLoopState,
    ) -> str | None:
        """Executes asynchronous ratchet optimization iterations and returns optional halt_reason."""
        halt_reason: str | None = None
        for i in range(1, effective_max_iter + 1):
            logger.info(f"🔄 --- Iteration {i}/{effective_max_iter} ---")
            prev_tokens, t0 = self._token_snapshot(), time.perf_counter()
            try:
                mutated, cand_halt = self._propose_candidate(i, state)
                if cand_halt:
                    return cand_halt
                if not mutated or self._run_pre_eval_guards(mutated, i, t0, prev_tokens, state):
                    continue
                eval_report = await self._eval_async(mutated)
                self._apply_trial_verdict(i, eval_report, mutated, t0, prev_tokens, state)
                should_stop, stop_reason = self._check_budget_and_early_stop(
                    i, effective_patience, baseline_tokens, state
                )
                if should_stop:
                    return stop_reason or halt_reason
            except Exception as exc:
                exc_halt, should_break = self._handle_iteration_exception(
                    exc, i, t0, prev_tokens, state
                )
                if exc_halt:
                    halt_reason = exc_halt
                if should_break:
                    break
        return halt_reason

    def _should_delegate_sync_to_async(self) -> bool:
        """Returns True when synchronous run() should delegate to run_async() on a single loop."""
        if not (
            self.config.use_real_llm
            and self.llm_adapter is not None
            and not self._has_sync_eval_override()
        ):
            return False
        try:
            asyncio.get_running_loop()
            return False
        except RuntimeError:
            return True

    def run(self) -> RatchetReport:
        """Executes the full ratchet autonomous optimization loop synchronously."""
        if self._should_delegate_sync_to_async():
            return asyncio.run(self.run_async())
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        initial_content = self.target_file.read_text(encoding="utf-8")
        arch_name, sc_report = self._check_zero_token_short_circuit(initial_content)
        if sc_report is not None:
            return sc_report

        try:
            baseline_report = self._eval_sync(initial_content)
        except (TokenBudgetExceededError, CircuitBreakerOpenError) as init_err:
            return self._build_init_error_report(init_err)

        base_sc, base_tok, max_it, pat, state, early_rep = self._prepare_post_baseline_state(
            arch_name, baseline_report, initial_content
        )
        if early_rep is not None:
            return early_rep

        initial_holdout_score = self._eval_holdout_base_sync(initial_content)
        try:
            halt_reason = self._run_sync_iterations(max_it, pat, base_tok, state)
        finally:
            self._finalize_disk_state(initial_content, state)

        if state.finalize_error:
            raise RuntimeError(f"Failed to finalize disk state: {state.finalize_error}")

        final_holdout_score = self._eval_holdout_final_sync(
            state.best_content, initial_holdout_score, state.kept_count
        )
        return self._build_final_report(
            base_sc, initial_holdout_score, final_holdout_score, halt_reason, state
        )

    async def run_async(self) -> RatchetReport:
        """Executes the full ratchet autonomous optimization loop asynchronously."""
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        initial_content = self.target_file.read_text(encoding="utf-8")
        arch_name, sc_report = self._check_zero_token_short_circuit(initial_content)
        if sc_report is not None:
            return sc_report

        try:
            try:
                baseline_report = await self._eval_async(initial_content)
            except (TokenBudgetExceededError, CircuitBreakerOpenError) as init_err:
                return self._build_init_error_report(init_err)

            base_sc, base_tok, max_it, pat, state, early_rep = self._prepare_post_baseline_state(
                arch_name, baseline_report, initial_content
            )
            if early_rep is not None:
                return early_rep

            initial_holdout_score = await self._eval_holdout_base_async(initial_content)
            try:
                halt_reason = await self._run_async_iterations(max_it, pat, base_tok, state)
            finally:
                self._finalize_disk_state(initial_content, state)

            if state.finalize_error:
                raise RuntimeError(f"Failed to finalize disk state: {state.finalize_error}")

            final_holdout_score = await self._eval_holdout_final_async(
                state.best_content, initial_holdout_score, state.kept_count
            )
            return self._build_final_report(
                base_sc, initial_holdout_score, final_holdout_score, halt_reason, state
            )
        finally:
            await self._close_async_resources()


GitRatchetTuner = GitRatchetOptimizer


def mutate_skill(content: str, iteration: int, skill_name: str = "generic") -> str:
    """Mutates skill content by applying unapplied optimization strategies without junk comments."""
    cfg = RatchetConfig(target_file=Path("SKILL.md"), skill_name=skill_name)
    optimizer = GitRatchetOptimizer(cfg, dry_run_git=True)
    return optimizer.propose_mutation(content, iteration)


__all__ = [
    "ACADEMIC_ARCHETYPE_KEYWORDS",
    "ADR_ARCHETYPE_KEYWORDS",
    "ADR_HEADER_TAG_REGEX",
    "ADR_REF_PATTERN",
    "AIClient",
    "AdaptiveRateLimiter",
    "AsyncAIClient",
    "BIM_ARCHETYPE_KEYWORDS",
    "BIM_GOVERNANCE_ARCHETYPE_KEYWORDS",
    "BIM_RASE_ARCHETYPE_KEYWORDS",
    "CODING_ARCHETYPE_KEYWORDS",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "DEFAULT_MUTATION_STRATEGIES_PATH",
    "DOMAIN_ARCHETYPES",
    "DomainArchetype",
    "GRILLING_ARCHETYPE_KEYWORDS",
    "GitMutexLock",
    "GitRatchetOptimizer",
    "GitRatchetTuner",
    "LEGAL_ARCHETYPE_KEYWORDS",
    "LLMTaskAdapter",
    "OFFICE_ARCHETYPE_KEYWORDS",
    "ORCHESTRATION_ARCHETYPE_KEYWORDS",
    "RISK_ARCHETYPE_KEYWORDS",
    "RatchetConfig",
    "RatchetReport",
    "RatchetTrialResult",
    "RateLimiter",
    "TECH_QC_ARCHETYPE_KEYWORDS",
    "TokenBudgetExceededError",
    "TokenUsageTracker",
    "VISUAL_ARCHETYPE_KEYWORDS",
    "_RatchetLoopState",
    "_RatchetSession",
    "_UNSET",
    "_detect_program_root",
    "_resolve_cfg_bool",
    "_resolve_cfg_float",
    "_resolve_cfg_int",
    "get_default_domain_scorers",
    "load_mutation_strategies",
    "load_tuner_config",
    "mutate_skill",
    "preserve_yaml_frontmatter",
    "reload_mutation_strategies",
    "reload_tuner_config",
    "remaining_strategies",
    "resolve_domain_archetype",
    "resolve_domain_dataset",
]
