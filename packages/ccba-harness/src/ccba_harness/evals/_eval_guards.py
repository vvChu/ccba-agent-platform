"""_eval_guards.py - Private deterministic eval guards for Wave 0 (Issue #910, ADR-0067).

Centralizes FailureKind classification, Baseline Sanity Gate, Hard Holdout Gate
(sync/async), single-skill CI Ratchet post-mutation verification, and daemon
production guards to keep daemon.py and _tuner_mutator.py <= 800 LOC.
Not exported in ccba_harness.__all__.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ..economy import (
    DEFAULT_DMI_TOKEN_CEILING,
    DEFAULT_MI_TOKEN_CEILING,
    count_skill_tokens_lf,
    load_skill_token_baseline,
)
from .models import EvalItem, EvalReport

logger = logging.getLogger("ccba.eval.guards")

_SPOKE_LEAKAGE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("vvc_notes_ref", re.compile(r"\b(?:vvc-notes|Friday Alpha Arena)\b", re.IGNORECASE)),
    (
        "windows_drive_path",
        re.compile(r"""(?:[rR]?["']|[=:]\s*)[A-Za-z]:(?:[\\/]+[A-Za-z0-9_.-]*|[\\/]*["'])"""),
    ),
)


class FailureKind(str, Enum):
    """Explicit failure taxonomy for velocity circuit-breaker accounting."""

    ORACLE_INVALID = "ORACLE_INVALID"
    ALREADY_OPTIMAL = "ALREADY_OPTIMAL"
    INFRA_ERROR = "INFRA_ERROR"
    MUTATION_REGRESSION = "MUTATION_REGRESSION"
    HOLDOUT_REGRESSION = "HOLDOUT_REGRESSION"


QUARANTINE_COUNTING_FAILURES: frozenset[str] = frozenset(
    {
        FailureKind.MUTATION_REGRESSION.value,
        FailureKind.HOLDOUT_REGRESSION.value,
    }
)


@dataclass(frozen=True)
class BaselineSanityResult:
    """Outcome of the post-baseline oracle sanity gate."""

    passed: bool
    halt_reason: str | None = None
    failure_kind: FailureKind | None = None


@dataclass(frozen=True)
class HoldoutGateDecision:
    """Outcome of evaluating candidate content on holdout BEFORE Git commit."""

    passed: bool
    candidate_score: float | None = None
    failure_kind: FailureKind | None = None
    reason: str = ""


def compute_lf_sha256(text: str) -> str:
    """Computes normalized LF SHA-256 hex digest for text content."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_dataset_sha256(items: Sequence[EvalItem]) -> str:
    """Computes deterministic SHA-256 digest of an evaluation dataset."""
    payload = [
        {
            "id": str(it.id),
            "input_prompt": str(it.input_prompt),
            "rubric": str(it.rubric or ""),
            "golden_answer": it.golden_answer,
        }
        for it in items
    ]
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def evaluate_baseline_sanity(
    baseline_score: float,
    target_score: float,
    item_count: int,
    *,
    verify_only: bool = False,
) -> BaselineSanityResult:
    """Halts at 0 mutation tokens when oracle baseline is broken (<=0) or already optimal."""
    if item_count <= 0 or baseline_score <= 0.0:
        return BaselineSanityResult(
            passed=False,
            halt_reason="ORACLE_MISMATCH_HALT",
            failure_kind=FailureKind.ORACLE_INVALID,
        )
    if baseline_score >= target_score and not verify_only:
        return BaselineSanityResult(
            passed=False,
            halt_reason="ALREADY_OPTIMAL_SKIP",
            failure_kind=FailureKind.ALREADY_OPTIMAL,
        )
    return BaselineSanityResult(passed=True)


def evaluate_candidate_holdout_sync(
    eval_fn: Callable[[str, list[EvalItem]], EvalReport],
    mutated_content: str,
    holdout_dataset: list[EvalItem],
    baseline_holdout_score: float | None,
    *,
    require_holdout_for_keep: bool,
) -> HoldoutGateDecision:
    """Synchronously validates candidate content against holdout dataset prior to commit."""
    if not holdout_dataset:
        if require_holdout_for_keep:
            return HoldoutGateDecision(
                passed=False,
                failure_kind=FailureKind.HOLDOUT_REGRESSION,
                reason="Hard Holdout Gate: holdout_size == 0 (Tier A) không cho phép KEEP.",
            )
        return HoldoutGateDecision(passed=True, candidate_score=baseline_holdout_score)

    try:
        report = eval_fn(mutated_content, holdout_dataset)
        score = float(report.overall_score)
    except Exception as exc:
        return HoldoutGateDecision(
            passed=False,
            failure_kind=FailureKind.HOLDOUT_REGRESSION,
            reason=f"Hard Holdout Gate: lỗi chấm holdout ({exc}).",
        )

    if baseline_holdout_score is not None and score < baseline_holdout_score:
        return HoldoutGateDecision(
            passed=False,
            candidate_score=score,
            failure_kind=FailureKind.HOLDOUT_REGRESSION,
            reason=(
                f"Hard Holdout Gate: điểm holdout sụt giảm "
                f"({score:.2f}% < baseline {baseline_holdout_score:.2f}%)."
            ),
        )
    return HoldoutGateDecision(passed=True, candidate_score=score)


async def evaluate_candidate_holdout_async(
    eval_fn: Callable[[str, list[EvalItem]], Awaitable[EvalReport]],
    mutated_content: str,
    holdout_dataset: list[EvalItem],
    baseline_holdout_score: float | None,
    *,
    require_holdout_for_keep: bool,
) -> HoldoutGateDecision:
    """Asynchronously validates candidate content against holdout dataset prior to commit."""
    if not holdout_dataset:
        if require_holdout_for_keep:
            return HoldoutGateDecision(
                passed=False,
                failure_kind=FailureKind.HOLDOUT_REGRESSION,
                reason="Hard Holdout Gate: holdout_size == 0 (Tier A) không cho phép KEEP.",
            )
        return HoldoutGateDecision(passed=True, candidate_score=baseline_holdout_score)

    try:
        report = await eval_fn(mutated_content, holdout_dataset)
        score = float(report.overall_score)
    except Exception as exc:
        return HoldoutGateDecision(
            passed=False,
            failure_kind=FailureKind.HOLDOUT_REGRESSION,
            reason=f"Hard Holdout Gate: lỗi chấm holdout ({exc}).",
        )

    if baseline_holdout_score is not None and score < baseline_holdout_score:
        return HoldoutGateDecision(
            passed=False,
            candidate_score=score,
            failure_kind=FailureKind.HOLDOUT_REGRESSION,
            reason=(
                f"Hard Holdout Gate: điểm holdout sụt giảm "
                f"({score:.2f}% < baseline {baseline_holdout_score:.2f}%)."
            ),
        )
    return HoldoutGateDecision(passed=True, candidate_score=score)


def _extract_is_dmi_from_content(content: str) -> bool:
    """Returns True if frontmatter explicitly disables model invocation."""
    return bool(re.search(r"(?m)^\s*disable-model-invocation:\s*true\s*$", content))


def _scan_spoke_leakage(content: str) -> str | None:
    """Detects hardcoded Spoke references or unexempted Windows machine paths."""
    for line in content.splitlines():
        if "# ccba:allow-machine-path" in line:
            continue
        for label, pat in _SPOKE_LEAKAGE_PATTERNS:
            if pat.search(line):
                return f"Phát hiện rò rỉ Spoke/đường dẫn máy ({label})."
    return None


def run_ci_ratchet_post_mutation_gate(
    skill_name: str,
    mutated_content: str,
    repo_root: Path,
    *,
    mi_ceiling: int = DEFAULT_MI_TOKEN_CEILING,
    dmi_ceiling: int = DEFAULT_DMI_TOKEN_CEILING,
) -> tuple[bool, str | None, str]:
    """Runs single-skill CI token ratchet, Spoke-leakage, and GPI checks (COND-TOKEN-GATE).

    Missing baseline key falls back to ceiling (MI/DMI) identically to
    economy._scan_ratchet_entries without KeyError or repo-wide orphan scans.
    """
    baseline_path = repo_root / "scripts" / "skill_token_budget_baseline.json"
    baseline = load_skill_token_baseline(baseline_path) if baseline_path.is_file() else {}
    tokens = count_skill_tokens_lf(mutated_content)
    ceiling = dmi_ceiling if _extract_is_dmi_from_content(mutated_content) else mi_ceiling
    prev = baseline.get(skill_name)
    allowed = max(ceiling, prev) if prev is not None else ceiling
    if tokens > allowed:
        return (
            False,
            "CI_TOKEN_BUDGET_EXCEEDED",
            f"CI Token Ratchet: {skill_name} ({tokens} tok) > allowed {allowed} "
            f"(ceiling={ceiling}, baseline={prev})",
        )

    leak = _scan_spoke_leakage(mutated_content)
    if leak:
        return False, "CI_SPOKE_LEAKAGE_DETECTED", f"CI Cleanliness Gate: {leak}"

    try:
        from .._skill_frontmatter import parse_markdown_frontmatter
        from .._skill_gpi_gates import audit_granularity_and_gpi_impl

        spec = parse_markdown_frontmatter(mutated_content)
        if spec.has_frontmatter and spec.error is None and "gpi" in spec.metadata:
            gpi_issues = audit_granularity_and_gpi_impl(
                repo_root / ".agents" / "skills" / skill_name / "SKILL.md",
                skill_name,
                spec.metadata,
                enforce_gpi=True,
                content=mutated_content,
            )
            if gpi_issues:
                return False, "CI_GPI_GATE_FAILED", f"CI GPI Gate: {gpi_issues[0].message}"
    except Exception as exc:
        logger.debug("Optional GPI check skipped in post-mutation gate: %s", exc)

    return True, None, ""


def _commit_kept_trial(
    optimizer: Any,
    iter_idx: int,
    current_score: float,
    mutated_content: str,
    candidate_holdout_score: float | None,
    t0: float,
    prev_tokens: tuple[int, int, int],
    state: Any,
) -> None:
    """Commits an accepted trial after passing tuning and Hard Holdout Gate."""
    diff_str = (
        f"{state.best_score:.1f}% -> {current_score:.1f}% "
        f"(+{current_score - state.best_score:.1f}%)"
    )
    if optimizer.git_commit_improvement(diff_str):
        state.has_committed = True
    state.best_score, state.best_content = current_score, mutated_content
    state.best_holdout_score = candidate_holdout_score
    state.kept_count, state.stagnant_trials = state.kept_count + 1, 0
    summary = f"Cải thiện điểm số thành công: {diff_str}"
    if hasattr(optimizer, "velocity_tracker") and not optimizer.dry_run_git:
        optimizer.velocity_tracker.record_patch_keep(mutated_content, score=current_score)
    optimizer._record_trial(iter_idx, current_score, 0, "KEEP", summary, t0, prev_tokens, state)
    logger.info("📌 Quyết định [KEEP]: %s", summary)


def _revert_trial(
    optimizer: Any,
    iter_idx: int,
    current_score: float,
    crit_fails: int,
    mutated_content: str,
    summary: str,
    failure_kind: FailureKind,
    t0: float,
    prev_tokens: tuple[int, int, int],
    state: Any,
) -> None:
    """Rolls back a rejected trial and records failure accounting without poisoning dry-runs."""
    optimizer.git_rollback_target(state.best_content, has_committed=state.has_committed)
    state.reverted_count += 1
    state.stagnant_trials += 1
    if hasattr(optimizer, "velocity_tracker") and not optimizer.dry_run_git:
        optimizer.velocity_tracker.record_patch_failure(
            mutated_content, reason=summary, failure_kind=failure_kind.value
        )
    optimizer._record_trial(
        iter_idx, current_score, crit_fails, "REVERT", summary, t0, prev_tokens, state
    )
    logger.info("📌 Quyết định [REVERT]: %s", summary)


def _resolve_candidate_holdout(
    optimizer: Any,
    mutated_content: str,
    state: Any,
    holdout_decision: HoldoutGateDecision | None,
) -> HoldoutGateDecision:
    """Returns precomputed async holdout decision or evaluates synchronously."""
    if holdout_decision is not None:
        return holdout_decision
    req_ho = bool(getattr(optimizer.config, "require_holdout_for_keep", False))
    return evaluate_candidate_holdout_sync(
        optimizer._eval_sync,
        mutated_content,
        optimizer.holdout_dataset,
        state.best_holdout_score,
        require_holdout_for_keep=req_ho,
    )


def apply_verdict_with_holdout(
    optimizer: Any,
    iter_idx: int,
    eval_report: EvalReport,
    mutated_content: str,
    t0: float,
    prev_tokens: tuple[int, int, int],
    state: Any,
    holdout_decision: HoldoutGateDecision | None = None,
) -> None:
    """Applies trial verdict with Hard Holdout Gate BEFORE git_commit_improvement."""
    score = eval_report.overall_score
    crit_fails = sum(1 for r in eval_report.item_results if r.critical_failed)
    failure_kind = FailureKind.MUTATION_REGRESSION

    if score > state.best_score and crit_fails == 0:
        ho = _resolve_candidate_holdout(optimizer, mutated_content, state, holdout_decision)
        if ho.passed:
            _commit_kept_trial(
                optimizer,
                iter_idx,
                score,
                mutated_content,
                ho.candidate_score,
                t0,
                prev_tokens,
                state,
            )
            return
        failure_kind = ho.failure_kind or FailureKind.HOLDOUT_REGRESSION
        summary = ho.reason
    elif crit_fails == 0:
        summary = f"Không cải thiện (Score {score:.1f}% vs Best {state.best_score:.1f}%)"
    else:
        summary = f"Vi phạm điều kiện nghiêm ngặt: {crit_fails} Điểm Liệt."

    _revert_trial(
        optimizer,
        iter_idx,
        score,
        crit_fails,
        mutated_content,
        summary,
        failure_kind,
        t0,
        prev_tokens,
        state,
    )


def should_skip_daemon_mock_engine(use_real_llm: bool, allow_mock_simulator: bool) -> bool:
    """Returns True when daemon must block Mock Simulator execution in production."""
    return not use_real_llm and not allow_mock_simulator


def resolve_daemon_dataset_path(
    skill_name: str,
    test_cases_dir: Path,
    flagship_overrides: dict[str, str],
) -> tuple[Path | None, str]:
    """Resolves dataset Path for NightlyTunerDaemon using flagship override or fail-closed contract."""
    from .archetypes import resolve_domain_dataset_contract

    override = flagship_overrides.get(skill_name)
    if override:
        override_path = test_cases_dir / override
        if override_path.is_file():
            return override_path.resolve(), ""
    contract = resolve_domain_dataset_contract(skill_name, test_cases_dir)
    if contract.status == "CONFIGURED" and contract.dataset_path is not None:
        return contract.dataset_path, ""
    return None, contract.reason


def run_pre_eval_governance_guards(
    optimizer: Any,
    baseline_content: str,
    mutated_content: str,
) -> str | None:
    """Runs Regression Gate and single-skill CI Ratchet gate before LLM evaluation."""
    from .skill_governance import evaluate_regression_gate, has_explicit_stability_zone

    enforce = has_explicit_stability_zone(baseline_content)
    gate_verdict = evaluate_regression_gate(
        baseline_content,
        mutated_content,
        enforce_token_ratio=enforce,
    )
    if not gate_verdict.passed:
        if hasattr(optimizer, "velocity_tracker") and not optimizer.dry_run_git:
            optimizer.velocity_tracker.record_patch_failure(
                mutated_content,
                reason=gate_verdict.reason,
                failure_kind=FailureKind.MUTATION_REGRESSION.value,
            )
        return f"Từ chối mutation [{gate_verdict.failure_code}]: {gate_verdict.reason}"

    if optimizer.target_file.name.lower() == "skill.md":
        skill_id = optimizer.config.skill_name or optimizer.target_file.parent.name
        ci_ok, ci_code, ci_reason = run_ci_ratchet_post_mutation_gate(
            skill_id, mutated_content, optimizer.project_root
        )
        if not ci_ok:
            if hasattr(optimizer, "velocity_tracker") and not optimizer.dry_run_git:
                optimizer.velocity_tracker.record_patch_failure(
                    mutated_content,
                    reason=ci_reason,
                    failure_kind=FailureKind.MUTATION_REGRESSION.value,
                )
            return f"Từ chối mutation [{ci_code}]: {ci_reason}"
    return None


def build_chatops_boost_payload(message: str, stagnant: Sequence[Any]) -> dict[str, Any]:
    """Builds JSON notification payload with interactive /boost actions for ChatOps Gateway."""
    actions = [
        {
            "action_id": f"boost_{s.skill_name}",
            "label": f"🚀 /boost {s.skill_name}",
            "command": "ccba.skill.boost",
            "params": {"skill": s.skill_name},
            "ttl_seconds": 86400,
            "timeout": 600,
        }
        for s in list(stagnant)[:3]
    ]
    return {
        "title": "CCBA NIGHTLY AUTO-TUNER REPORT",
        "body": message,
        "severity": "WARNING",
        "actions": actions,
    }


def build_daemon_summary_from_report(
    skill_name: str,
    target_file: Path,
    result: Any,
    summary_cls: Any,
) -> Any:
    """Converts a RatchetReport into a SkillEvolutionSummary."""
    status = "IMPROVED" if result.final_score > result.initial_score else "UNCHANGED"
    if result.final_score == 100.0 and result.initial_score == 100.0:
        status = "PERFECT_VERIFIED"
    if result.halt_reason:
        status = (
            result.halt_reason
            if result.halt_reason.startswith("HALT_")
            else f"HALT_{result.halt_reason}"
        )
    return summary_cls(
        skill_name=skill_name,
        target_file=target_file,
        baseline_score=result.initial_score,
        final_score=result.final_score,
        commits_kept=result.kept_commits,
        rollbacks=result.reverted_trials,
        status=status,
        total_tokens=result.total_tokens,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        halt_reason=result.halt_reason,
        slicing_tier=result.slicing_tier,
        holdout_score=result.holdout_score,
        tuning_size=result.tuning_size,
        holdout_size=result.holdout_size,
    )


def resolve_daemon_target_ref(root: Path, target_ref: str) -> str:
    """Falls back from origin/main to main when origin/main ref is absent."""
    if target_ref != "origin/main":
        return target_ref
    import subprocess

    chk = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/main"],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    return "main" if chk.returncode != 0 else target_ref


def seed_legal_failure_ledger_post_baseline(
    optimizer: Any, arch_name: str, baseline_report: EvalReport, initial_content: str
) -> None:
    """Seeds legal failure ledger after baseline evaluation for legal archetypes."""
    if arch_name not in {"legal", "legal_tooling"}:
        return
    try:
        from .failure_mutator import extract_failure_signals, save_failure_ledger

        signals = extract_failure_signals(
            baseline_report, optimizer.tuning_dataset, optimizer.legal_index
        )
        if signals:
            save_failure_ledger(optimizer.config.skill_name, signals, initial_content)
            logger.info(
                "⚖️ [LEDGER_SEEDED] Ghi nhận %d tín hiệu lỗi cho '%s'.",
                len(signals),
                optimizer.config.skill_name,
            )
    except Exception as exc:
        logger.warning("Lỗi trích xuất tín hiệu lỗi sau baseline: %s", exc)


def is_eligible_for_boost_escalation(summary: Any) -> bool:
    """Returns True only when a skill cleared baseline sanity and had an actual mutation attempt."""
    blocked_halts = {
        "ORACLE_MISMATCH_HALT",
        "ALREADY_OPTIMAL_SKIP",
        "UNCONFIGURED",
        "SKILL_LOCKED_STABILITY_ZONE",
        "MOCK_SIMULATOR_FORBIDDEN",
        "ERROR",
    }
    if summary.halt_reason in blocked_halts:
        return False
    return bool(
        summary.baseline_score > 0.0
        and summary.baseline_score < 90.0
        and summary.commits_kept == 0
        and summary.final_score < 90.0
    )
