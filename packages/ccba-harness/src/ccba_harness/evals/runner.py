"""runner.py - Orchestrator for evaluation benchmarks in CCBA Evals Framework.

Executes dataset evaluations, aggregates multi-scorer metrics, enforces critical failure rules,
and generates structured evaluation reports.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from .models import EvalItem, EvalItemResult, EvalReport, ScoreResult
from .scorers import BaseScorer


class EvalRunner:
    """Orchestrates test execution over evaluation datasets with multi-scorer weighting."""

    def __init__(
        self,
        default_pass_threshold: float = 85.0,
        max_concurrency: int = 5,
    ) -> None:
        self.default_pass_threshold = default_pass_threshold
        self.max_concurrency = max_concurrency

    async def _evaluate_single_item(
        self,
        item: EvalItem,
        task: Callable[[EvalItem], Awaitable[Any] | Any],
        scorers: list[BaseScorer],
        pass_threshold: float,
        semaphore: asyncio.Semaphore,
    ) -> EvalItemResult:
        """Evaluates a single item through the task and all attached scorers."""
        async with semaphore:
            task_output = None
            error_msg = None
            try:
                if asyncio.iscoroutinefunction(task):
                    task_output = await task(item)
                else:
                    res = task(item)
                    if asyncio.iscoroutine(res):
                        task_output = await res
                    else:
                        task_output = res
            except Exception as e:
                error_msg = f"Task execution failed: {e}"
                task_output = None

            if error_msg is not None:
                # Automatic failure across all scorers
                scores = [
                    ScoreResult(
                        scorer_name=s.name,
                        score=0.0,
                        reasoning=error_msg,
                        is_critical_fail=s.is_critical,
                    )
                    for s in scorers
                ]
                return EvalItemResult(
                    item_id=item.id,
                    task_output=None,
                    scores=scores,
                    composite_score=0.0,
                    passed=False,
                    critical_failed=any(s.is_critical for s in scorers),
                    error=error_msg,
                )

            # Score output against all scorers concurrently
            score_tasks = [s.score(task_output, item) for s in scorers]
            scores = await asyncio.gather(*score_tasks)

            # Calculate weighted composite score (0.0 to 100.0)
            total_weight = sum(s.weight for s in scorers)
            if total_weight > 0:
                weighted_sum = sum(
                    s.weight * res.score for s, res in zip(scorers, scores, strict=False)
                )
                composite_score = round((weighted_sum / total_weight) * 100.0, 2)
            else:
                composite_score = 0.0

            has_critical_fail = any(res.is_critical_fail for res in scores)
            passed = (composite_score >= pass_threshold) and not has_critical_fail

            return EvalItemResult(
                item_id=item.id,
                task_output=task_output,
                scores=scores,
                composite_score=composite_score,
                passed=passed,
                critical_failed=has_critical_fail,
            )

    async def run(
        self,
        dataset: list[EvalItem],
        task: Callable[[EvalItem], Awaitable[Any] | Any],
        scorers: list[BaseScorer],
        pass_threshold: float | None = None,
        max_concurrency: int | None = None,
    ) -> EvalReport:
        """Asynchronously executes evaluation across dataset with concurrent workers.

        Args:
            dataset: List of EvalItem test cases.
            task: Async/sync callable accepting EvalItem and returning model output.
            scorers: List of BaseScorer instances.
            pass_threshold: Composite percentage required to pass (default: 85.0).
            max_concurrency: Max parallel task workers (default: 5).

        Returns:
            EvalReport containing summary metrics and per-item results.
        """
        threshold = pass_threshold if pass_threshold is not None else self.default_pass_threshold
        concurrency = max_concurrency if max_concurrency is not None else self.max_concurrency
        semaphore = asyncio.Semaphore(concurrency)

        if not dataset:
            return EvalReport(
                total_items=0,
                passed_items=0,
                failed_items=0,
                overall_score=0.0,
                pass_rate=0.0,
                item_results=[],
                summary_by_scorer={},
            )

        tasks = [
            self._evaluate_single_item(item, task, scorers, threshold, semaphore)
            for item in dataset
        ]
        results = await asyncio.gather(*tasks)

        total_items = len(results)
        passed_items = sum(1 for r in results if r.passed)
        failed_items = total_items - passed_items
        overall_score = round(sum(r.composite_score for r in results) / total_items, 2)
        pass_rate = round((passed_items / total_items) * 100.0, 2)

        # Summarize average score per scorer
        summary_by_scorer: dict[str, float] = {}
        for s in scorers:
            scorer_scores = []
            for r in results:
                for score_res in r.scores:
                    if score_res.scorer_name == s.name:
                        scorer_scores.append(score_res.score)
            if scorer_scores:
                summary_by_scorer[s.name] = round(
                    (sum(scorer_scores) / len(scorer_scores)) * 100.0, 2
                )

        return EvalReport(
            total_items=total_items,
            passed_items=passed_items,
            failed_items=failed_items,
            overall_score=overall_score,
            pass_rate=pass_rate,
            item_results=results,
            summary_by_scorer=summary_by_scorer,
        )

    def run_sync(
        self,
        dataset: list[EvalItem],
        task: Callable[[EvalItem], Any],
        scorers: list[BaseScorer],
        pass_threshold: float | None = None,
        max_concurrency: int | None = None,
    ) -> EvalReport:
        """Synchronous wrapper for run(). Enforces event-loop boundary invariant (P1.5)."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "EvalRunner.run_sync() cannot be called from within a running event loop. "
                "Please use 'await runner.run()' directly."
            )

        return asyncio.run(
            self.run(
                dataset=dataset,
                task=task,
                scorers=scorers,
                pass_threshold=pass_threshold,
                max_concurrency=max_concurrency,
            )
        )
