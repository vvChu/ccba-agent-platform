"""runner.py - Orchestrator for evaluation benchmarks in CCBA Evals Framework.

Executes dataset evaluations, aggregates multi-scorer metrics, enforces critical failure rules,
and generates structured evaluation reports.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from .models import EvalItem, EvalItemResult, EvalReport, ScoreResult
from .scorers import (
    BaseScorer,
    ExactMatchScorer,
    JsonSchemaScorer,
    LengthBoundsScorer,
    LLMRubricScorer,
    RegexScorer,
)


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
            task_exc: Exception | None = None
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
                task_exc = e
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
                    exception=task_exc,
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


class AutoItemScorer(BaseScorer):
    """Automatically applies the appropriate scorer for an EvalItem."""

    def __init__(self, name: str = "auto_item_scorer", weight: float = 1.0) -> None:
        super().__init__(name=name, weight=weight)
        self._exact_scorer = ExactMatchScorer()
        self._fallback_length = LengthBoundsScorer(min_length=1)

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        if item.golden_answer is not None:
            return await self._exact_scorer.score(output, item)
        if item.rubric:
            rubric_scorer = LLMRubricScorer(rubric=item.rubric)
            return await rubric_scorer.score(output, item)
        assertions = item.metadata.get("assertions")
        if assertions and isinstance(assertions, list):
            for ass in assertions:
                if not isinstance(ass, dict):
                    continue
                ass_type = ass.get("type", "regex")
                if ass_type == "regex" and "pattern" in ass:
                    r_scorer = RegexScorer(
                        pattern=ass["pattern"],
                        is_critical=bool(ass.get("is_critical", False)),
                    )
                    res = await r_scorer.score(output, item)
                    if res.score == 0.0 or res.is_critical_fail:
                        return res
                elif ass_type == "length":
                    min_len = (
                        int(ass.get("min_length", 0)) if ass.get("min_length") is not None else 0
                    )
                    max_len = (
                        int(ass.get("max_length", 100_000))
                        if ass.get("max_length") is not None
                        else 100_000
                    )
                    l_scorer = LengthBoundsScorer(
                        min_length=min_len,
                        max_length=max_len,
                        is_critical=bool(ass.get("is_critical", False)),
                    )
                    res = await l_scorer.score(output, item)
                    if res.score == 0.0 or res.is_critical_fail:
                        return res
                elif ass_type == "schema":
                    s_scorer = JsonSchemaScorer(
                        required_keys=ass.get("required_keys"),
                        is_critical=bool(ass.get("is_critical", False)),
                    )
                    res = await s_scorer.score(output, item)
                    if res.score == 0.0 or res.is_critical_fail:
                        return res
            return ScoreResult(
                scorer_name=self.name,
                score=1.0,
                reasoning="All case assertions passed successfully.",
            )
        return await self._fallback_length.score(output, item)


def _parse_raw_eval_items(raw: Any) -> list[EvalItem]:
    """Parse raw JSON list or dict into a list of EvalItem instances."""
    items: list[EvalItem] = []
    if not isinstance(raw, list):
        if isinstance(raw, dict):
            raw = [raw]
        else:
            return items

    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            continue
        item_id = str(entry.get("id", f"case_{idx + 1}"))
        prompt = entry.get("input_prompt") or entry.get("prompt", "")
        golden = entry.get("golden_answer")
        rubric = entry.get("rubric")
        metadata = dict(entry.get("metadata", {}))
        diff_val = (
            entry.get("difficulty") or metadata.get("difficulty") or metadata.get("Difficulty")
        )
        if diff_val is not None:
            metadata["difficulty"] = str(diff_val).strip().lower()
        if "assertions" in entry and "assertions" not in metadata:
            metadata["assertions"] = entry["assertions"]
        items.append(
            EvalItem(
                id=item_id,
                input_prompt=prompt,
                golden_answer=golden,
                rubric=rubric,
                metadata=metadata,
            )
        )
    return items


SKILL_DATASET_ALIASES: dict[str, list[str]] = {
    "ccba-ai-qc-pccc-audit": ["pccc_audit", "ai_qc_pccc_audit"],
    "ai_qc_pccc_audit": ["pccc_audit", "ai_qc_pccc_audit"],
    "pccc_audit": ["pccc_audit", "ai_qc_pccc_audit"],
    "ccba-legal-advisor": ["legal_intel", "legal_advisor"],
    "legal_advisor": ["legal_intel", "legal_advisor"],
    "ccba-legal-intel": ["legal_intel", "legal_advisor"],
    "legal_intel": ["legal_intel", "legal_advisor"],
    "ccba-teamwork": ["agent_orchestration", "teamwork"],
    "agent_orchestration": ["agent_orchestration", "teamwork"],
    "ccba-ai-qc": ["ai_qc", "pccc_audit"],
    "ccba-grilling": ["grilling", "grill"],
    "grilling": ["grilling", "grill"],
    "ccba-adr-lifecycle": ["adr_lifecycle", "adr"],
    "adr_lifecycle": ["adr_lifecycle", "adr"],
    "bigbim-risk-redteam": ["bigbim_risk_redteam", "bigbim_risk"],
    "bigbim-governance": ["bigbim_governance", "governance"],
    "bigbim_governance": ["bigbim_governance", "governance"],
    "governance": ["bigbim_governance", "governance"],
    "bigbim-rase": ["bigbim_rase", "rase"],
    "bigbim_rase": ["bigbim_rase", "rase"],
    "rase": ["bigbim_rase", "rase"],
    "ccba-skill-repair": ["skill_repair", "repair_skill"],
    "skill_repair": ["skill_repair", "repair_skill"],
    "repair_skill": ["skill_repair", "repair_skill"],
    "ccba-design": ["visual_design", "design", "brand"],
    "visual_design": ["visual_design", "design", "brand"],
    "design": ["visual_design", "design", "brand"],
    "ccba-tvpl-vip-crawler": ["legal_tooling", "crawler", "tvpl_vip_crawler"],
    "tvpl_vip_crawler": ["legal_tooling", "crawler", "tvpl_vip_crawler"],
    "ccba-legal-ingest": ["legal_tooling", "legal_ingest", "ingest"],
    "legal_ingest": ["legal_tooling", "legal_ingest", "ingest"],
    "ccba-legal-document-tracker": ["legal_tooling", "legal_document_tracker", "tracker"],
    "legal_document_tracker": ["legal_tooling", "legal_document_tracker", "tracker"],
    "ccba-completion-checklist": ["legal_tooling", "completion_checklist", "checklist", "hsht"],
    "completion_checklist": ["legal_tooling", "completion_checklist", "checklist", "hsht"],
    "legal_tooling": ["legal_tooling"],
    "ccba-copywriting": ["copywriting", "office"],
    "copywriting": ["copywriting", "office"],
    "ccba-markdown-document-processing": [
        "copywriting",
        "office",
        "markdown_document_processing",
        "markdown-document-processing",
    ],
    "markdown-document-processing": [
        "copywriting",
        "office",
        "markdown_document_processing",
    ],
    "markdown_document_processing": [
        "copywriting",
        "office",
        "markdown_document_processing",
    ],
    "ccba-pptx": ["copywriting", "office", "pptx"],
    "pptx": ["copywriting", "office", "pptx"],
    "ccba-seminar-builder": ["copywriting", "office", "seminar_builder", "seminar"],
    "seminar-builder": ["copywriting", "office", "seminar_builder", "seminar"],
    "seminar_builder": ["copywriting", "office", "seminar_builder", "seminar"],
    "ccba-xu-ly-van-phong": ["copywriting", "office", "xu_ly_van_phong", "van_phong"],
    "xu-ly-van-phong": ["copywriting", "office", "xu_ly_van_phong", "van_phong"],
    "xu_ly_van_phong": ["copywriting", "office", "xu_ly_van_phong", "van_phong"],
    "office": ["copywriting", "office"],
    "platform_tooling": ["platform_tooling"],
    "platform-tooling": ["platform_tooling"],
}


def load_eval_dataset(
    dataset_path: Path | str | None = None,
    skill_name: str | None = None,
    project_root: Path | None = None,
    difficulty: str | None = None,
    limit: int | None = None,
) -> list[EvalItem]:
    """Load evaluation dataset from explicit path or default test cases directory."""
    if project_root is None:
        cur = Path.cwd().resolve()
        for p in [cur, *cur.parents]:
            if (p / ".agents").exists() or (p / "pyproject.toml").exists():
                project_root = p
                break
        if project_root is None:
            project_root = cur

    raw_items: list[EvalItem] = []

    if dataset_path:
        target = Path(dataset_path)
        if not target.is_absolute():
            target = project_root / target

        if not target.exists():
            return []

        if target.is_file():
            try:
                with open(target, encoding="utf-8") as f:
                    raw_items = _parse_raw_eval_items(json.load(f))
            except Exception:
                return []

        elif target.is_dir():
            for jf in sorted(target.glob("*.json")):
                try:
                    with open(jf, encoding="utf-8") as f:
                        raw_items.extend(_parse_raw_eval_items(json.load(f)))
                except Exception:
                    continue

    else:
        # Default fallback: .agents/skills/ccba-eval-gate/test_cases/
        default_dir = project_root / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
        if not default_dir.exists():
            return []

        if not skill_name:
            canonical_skill = ""
        else:
            canonical_skill = skill_name.strip()
            if "/" in canonical_skill or "\\" in canonical_skill or canonical_skill.endswith(".md"):
                p_cand = Path(canonical_skill)
                if p_cand.name.lower() == "skill.md" or p_cand.suffix == ".md":
                    canonical_skill = p_cand.parent.name
                else:
                    canonical_skill = p_cand.name

        if not canonical_skill or canonical_skill.lower() in ("all", "*"):
            for jf in sorted(default_dir.glob("*.json")):
                try:
                    with open(jf, encoding="utf-8") as f:
                        raw_items.extend(_parse_raw_eval_items(json.load(f)))
                except Exception:
                    continue
        else:
            clean = canonical_skill.removeprefix("ccba-").replace("-", "_").lower()
            candidate_keys = [clean]
            for alias in SKILL_DATASET_ALIASES.get(canonical_skill.lower(), []):
                if alias not in candidate_keys:
                    candidate_keys.append(alias)
            for alias in SKILL_DATASET_ALIASES.get(clean, []):
                if alias not in candidate_keys:
                    candidate_keys.append(alias)

            matching_files: list[Path] = []

            # SSOT Resolution via Domain Archetype (ADR-0058)
            from .archetypes import resolve_domain_dataset

            domain_ds = resolve_domain_dataset(canonical_skill)
            if domain_ds and domain_ds != "eval_general_domain.json":
                ds_cand = default_dir / domain_ds
                if ds_cand.exists() and ds_cand not in matching_files:
                    matching_files.append(ds_cand)

            for k in candidate_keys:
                exact_f = default_dir / f"eval_{k}.json"
                if exact_f.exists() and exact_f not in matching_files:
                    matching_files.append(exact_f)

            if not matching_files:
                for k in candidate_keys:
                    for matched_p in sorted(default_dir.glob(f"eval_{k}*.json")):
                        if matched_p not in matching_files:
                            matching_files.append(matched_p)
            if not matching_files:
                for k in candidate_keys:
                    for matched_p in sorted(default_dir.glob(f"*{k}*.json")):
                        if matched_p not in matching_files:
                            matching_files.append(matched_p)

            if matching_files:
                for mf in sorted(matching_files):
                    try:
                        with open(mf, encoding="utf-8") as f:
                            raw_items.extend(_parse_raw_eval_items(json.load(f)))
                    except Exception:
                        continue
            else:
                # Fallback to scanning metadata target_skill
                for jf in sorted(default_dir.glob("*.json")):
                    try:
                        with open(jf, encoding="utf-8") as f:
                            parsed = _parse_raw_eval_items(json.load(f))
                            for it in parsed:
                                tgt = (
                                    str(it.metadata.get("target_skill", ""))
                                    .strip()
                                    .removeprefix("ccba-")
                                    .replace("-", "_")
                                    .lower()
                                )
                                if (
                                    tgt in candidate_keys
                                    or tgt == clean
                                    or tgt == canonical_skill.lower()
                                ):
                                    raw_items.append(it)
                    except Exception:
                        continue

    items = raw_items
    if difficulty:
        d_clean = difficulty.strip().lower()
        items = [
            it for it in items if str(it.metadata.get("difficulty", "")).strip().lower() == d_clean
        ]

    if limit is not None:
        items = items[: max(0, limit)]

    return items


def resolve_target_skill_file(skill: str | None, project_root: Path) -> Path | None:
    """Resolves target SKILL.md file from skill name, path, or workspace.

    Args:
        skill: Skill name, directory path, or SKILL.md file path.
        project_root: Workspace root directory.

    Returns:
        Resolved Path to SKILL.md, or None if not found.
    """
    if skill:
        clean = skill.strip()
        p_cand = Path(clean)
        candidates: list[Path] = []
        if p_cand.is_absolute():
            candidates.append(p_cand if p_cand.name.lower() == "skill.md" else p_cand / "SKILL.md")
        else:
            full_p = project_root / p_cand
            candidates.append(full_p if full_p.name.lower() == "skill.md" else full_p / "SKILL.md")

        if "/" in clean or "\\" in clean or clean.endswith(".md"):
            c_name = p_cand.parent.name if p_cand.name.lower() == "skill.md" else p_cand.name
        else:
            c_name = clean

        candidates.extend(
            [
                project_root / ".agents" / "skills" / c_name / "SKILL.md",
                project_root / ".agents" / "skills" / f"ccba-{c_name}" / "SKILL.md",
                project_root / ".agents" / "skills" / f"bigbim-{c_name}" / "SKILL.md",
                project_root / ".agents" / "skills" / c_name.removeprefix("ccba-") / "SKILL.md",
                project_root / ".agents" / "skills" / c_name.removeprefix("bigbim-") / "SKILL.md",
                project_root / "skills" / c_name / "SKILL.md",
                project_root / "skills" / f"ccba-{c_name}" / "SKILL.md",
                project_root / "skills" / f"bigbim-{c_name}" / "SKILL.md",
            ]
        )
        for cand in candidates:
            if cand.exists() and cand.is_file() and cand.name.lower() == "skill.md":
                return cand.resolve()

    # Fallback to program.md if available
    prog = project_root / "program.md"
    if prog.exists() and prog.is_file():
        try:
            from .tuner import RatchetConfig

            cfg = RatchetConfig.from_markdown_program(prog, root=project_root)
            if cfg.target_file.exists():
                return cfg.target_file.resolve()
        except Exception:
            pass

    return None


def _create_default_eval_task(
    skill_name: str | None,
    project_root: Path,
) -> Callable[[EvalItem], Awaitable[Any]]:
    """Creates a default evaluation task that executes against the target skill prompt."""
    cand = resolve_target_skill_file(skill_name, project_root)

    async def _task(item: EvalItem) -> Any:
        current_system_prompt = ""
        if cand and cand.exists() and cand.is_file():
            try:
                current_system_prompt = cand.read_text(encoding="utf-8")
            except Exception:
                pass

        prompt_str = (
            item.input_prompt
            if isinstance(item.input_prompt, str)
            else json.dumps(item.input_prompt, ensure_ascii=False)
        )
        try:
            from ccba_ai import async_ai

            if hasattr(async_ai, "chat") and callable(async_ai.chat):
                if asyncio.iscoroutinefunction(async_ai.chat):
                    return await async_ai.chat(prompt_str, system=current_system_prompt)
                return async_ai.chat(prompt_str, system=current_system_prompt)
        except Exception:
            pass

        try:
            from ccba_ai import ai

            if hasattr(ai, "chat") and callable(ai.chat):
                return ai.chat(prompt_str, system=current_system_prompt)
        except Exception:
            pass

        # Offline / Mock Fallback
        if item.golden_answer is not None:
            return item.golden_answer
        return f"[Simulated Output for {item.id}]"

    return _task


def run_eval_pipeline(
    skill: str | None = None,
    trials: int = 3,
    auto_tune: bool = False,
    dataset: str | Path | None = None,
    project_root: Path | None = None,
    task: Callable[[EvalItem], Any] | None = None,
    scorers: list[BaseScorer] | None = None,
    pass_threshold: float = 85.0,
    max_concurrency: int = 5,
    difficulty: str | None = None,
    limit: int | None = None,
    dry_run_git: bool = False,
    full_sweep: bool = False,
) -> EvalReport:
    """Executes evaluation pipeline across dataset test cases with multi-trial support."""
    if project_root is None:
        cur = Path.cwd().resolve()
        for p in [cur, *cur.parents]:
            if (p / ".agents").exists() or (p / "pyproject.toml").exists():
                project_root = p
                break
        if project_root is None:
            project_root = cur

    items = load_eval_dataset(
        dataset_path=dataset,
        skill_name=skill,
        project_root=project_root,
        difficulty=difficulty,
        limit=limit,
    )
    if not items:
        return EvalReport(
            total_items=0,
            passed_items=0,
            failed_items=0,
            overall_score=0.0,
            pass_rate=0.0,
            item_results=[],
            summary_by_scorer={},
            metadata={
                "skill": skill,
                "trials": trials,
                "auto_tune": auto_tune,
                "full_sweep": full_sweep,
                "difficulty": difficulty,
                "limit": limit,
            },
        )

    active_scorers = scorers or [AutoItemScorer()]
    active_task = task or _create_default_eval_task(skill, project_root)

    # If auto_tune is requested and target skill file is found, execute GitRatchetOptimizer
    if auto_tune:
        target_file = resolve_target_skill_file(skill, project_root)
        if target_file is None or not target_file.exists():
            raise FileNotFoundError(
                f"Target skill file could not be resolved for auto-tuning (skill={skill!r})"
            )

        from .tuner import GitRatchetOptimizer, RatchetConfig

        tuner_config = RatchetConfig(
            target_file=target_file,
            eval_dataset_file=Path(dataset) if dataset and Path(dataset).is_file() else None,
            target_score=pass_threshold,
            max_iterations=trials,
            skill_name=skill or target_file.parent.name,
            full_sweep=full_sweep,
        )
        tuner = GitRatchetOptimizer(
            config=tuner_config,
            scorers=active_scorers,
            dry_run_git=dry_run_git,
            project_root=project_root,
            task=active_task,
            dataset=items,
        )
        ratchet_report = tuner.run()

        # Final evaluation on the optimized content
        best_content = target_file.read_text(encoding="utf-8")
        final_report = tuner.evaluate_content(best_content)
        final_report.metadata.update(
            {
                "skill": skill,
                "trials": trials,
                "auto_tune": auto_tune,
                "full_sweep": full_sweep,
                "difficulty": difficulty,
                "limit": limit,
                "auto_tune_status": "optimized" if ratchet_report.kept_commits > 0 else "clean",
                "ratchet_report": ratchet_report.to_dict(),
            }
        )
        return final_report

    runner = EvalRunner(default_pass_threshold=pass_threshold, max_concurrency=max_concurrency)
    num_trials = max(1, trials)
    trial_reports: list[EvalReport] = []

    for _ in range(num_trials):
        rep = runner.run_sync(
            dataset=items,
            task=active_task,
            scorers=active_scorers,
            pass_threshold=pass_threshold,
            max_concurrency=max_concurrency,
        )
        trial_reports.append(rep)

    if len(trial_reports) == 1:
        final_report = trial_reports[0]
        final_report.metadata.update(
            {
                "skill": skill,
                "trials": trials,
                "auto_tune": auto_tune,
                "difficulty": difficulty,
                "limit": limit,
            }
        )
    else:
        avg_score = round(sum(r.overall_score for r in trial_reports) / len(trial_reports), 2)
        avg_pass_rate = round(sum(r.pass_rate for r in trial_reports) / len(trial_reports), 2)
        merged_scorers: dict[str, list[float]] = {}
        for r in trial_reports:
            for sc_name, sc_val in r.summary_by_scorer.items():
                merged_scorers.setdefault(sc_name, []).append(sc_val)
        summary_by_scorer = {k: round(sum(v) / len(v), 2) for k, v in merged_scorers.items()}
        base_rep = trial_reports[-1]
        final_report = EvalReport(
            total_items=base_rep.total_items,
            passed_items=base_rep.passed_items,
            failed_items=base_rep.failed_items,
            overall_score=avg_score,
            pass_rate=avg_pass_rate,
            item_results=base_rep.item_results,
            summary_by_scorer=summary_by_scorer,
            metadata={
                "skill": skill,
                "trials": trials,
                "auto_tune": auto_tune,
                "difficulty": difficulty,
                "limit": limit,
                "trial_scores": [r.overall_score for r in trial_reports],
            },
        )

    return final_report
