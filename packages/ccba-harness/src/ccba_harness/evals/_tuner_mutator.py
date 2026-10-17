"""_tuner_mutator.py - Skill markdown mutation operators, pre-eval guards, and Git commit/rollback mixin."""

from __future__ import annotations

import hashlib
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ._tuner_llm import CircuitBreakerOpenError, TokenUsageTracker
from ._tuner_models import (
    ADR_HEADER_TAG_REGEX,
    ADR_REF_PATTERN,
    GitMutexLock,
    RatchetConfig,
    RatchetReport,
    RatchetTrialResult,
    TokenBudgetExceededError,
    _RatchetLoopState,
    load_mutation_strategies,
)
from .archetypes import resolve_domain_archetype
from .failure_mutator import (
    extract_failure_signals,
    get_unapplied_failure_signals,
    load_failure_ledger,
    render_failure_patch,
    save_failure_ledger,
)
from .legal_index import LegalFlatIndex
from .models import EvalItem, EvalReport
from .slicing import SlicedDataset

logger = logging.getLogger("ccba.eval.ratchet")


def preserve_yaml_frontmatter(original_content: str, edited_content: str) -> str:
    """Preserves YAML frontmatter metadata byte-for-byte when mutating SKILL.md body."""
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", original_content, re.DOTALL)
    if not fm_match:
        fm_match = re.match(r"^\s*---\r?\n(.*?)\r?\n---\r?\n?", original_content, re.DOTALL)
        if not fm_match:
            return edited_content

    frontmatter_block = fm_match.group(0).strip()
    edited_fm_match = re.match(r"^\s*---\r?\n.*?\r?\n---\r?\n?(.*)$", edited_content, re.DOTALL)
    body = edited_fm_match.group(1) if edited_fm_match else edited_content

    clean_body = body.strip()
    nl = "\r\n" if "\r\n" in original_content else "\n"
    if clean_body:
        return f"{frontmatter_block}{nl}{nl}{clean_body}{nl}"
    return f"{frontmatter_block}{nl}"


def remaining_strategies(
    content: str,
    skill_name: str,
    strategies_path: Path | None = None,
) -> list[tuple[str, str]]:
    """Returns unapplied mutation strategies for a skill prompt (Sprint 3 / ADR-0058)."""
    arch = resolve_domain_archetype(skill_name)
    arch_name = arch.name if arch else "general"

    all_strategies = load_mutation_strategies(strategies_path)
    strategies = all_strategies.get(arch_name) or all_strategies.get("general", [])
    if not strategies:
        return []

    fm_match = re.match(r"^\s*---\r?\n(.*?)\r?\n---\r?\n?", content, re.DOTALL)
    body = content[fm_match.end() :] if fm_match else content

    norm_body = ADR_HEADER_TAG_REGEX.sub("", body).replace("\r\n", "\n")
    unapplied: list[tuple[str, str]] = []
    for s_name, s_enhancement in strategies:
        norm_enhancement = ADR_HEADER_TAG_REGEX.sub("", s_enhancement.strip()).replace("\r\n", "\n")
        if s_enhancement.strip() not in body and norm_enhancement not in norm_body:
            unapplied.append((s_name, s_enhancement))
    return unapplied


class _RatchetMutationGitMixin:
    """Mixin providing skill mutation, Git commit/rollback, pre-eval guards, and report builders."""

    config: RatchetConfig
    target_file: Path
    project_root: Path
    dry_run_git: bool
    git_lock: GitMutexLock
    token_tracker: TokenUsageTracker
    sliced_data: SlicedDataset | None
    tuning_dataset: list[EvalItem]
    holdout_dataset: list[EvalItem]
    legal_index: LegalFlatIndex | None
    _applied_failure_patches: int
    _applied_fingerprints: set[str]

    def preserve_yaml_frontmatter(self, original_content: str, edited_content: str) -> str:
        """Preserves YAML frontmatter metadata when mutating SKILL.md body."""
        return preserve_yaml_frontmatter(original_content, edited_content)

    def _try_propose_failure_patch(self, current_content: str, arch_name: str) -> str | None:
        """Attempts to propose a failure-driven provenance patch if unapplied signals exist."""
        max_patches = getattr(self.config, "max_failure_patches", 3)
        if (
            arch_name not in {"legal", "legal_tooling"}
            or self._applied_failure_patches >= max_patches
        ):
            return None
        ledger = load_failure_ledger(self.config.skill_name)
        if not ledger or not ledger.signals:
            return None
        unapplied_sigs = get_unapplied_failure_signals(current_content, list(ledger.signals))
        candidates = [s for s in unapplied_sigs if s.fingerprint not in self._applied_fingerprints]
        if not candidates:
            return None

        sig = candidates[0]
        card = render_failure_patch(sig, self.legal_index)
        self._applied_fingerprints.add(sig.fingerprint)
        self._applied_failure_patches += 1
        logger.info(
            f"⚖️ [FAILURE_MUTATION_APPLIED] Chèn thẻ lỗi '{sig.code}' "
            f"(fingerprint: {sig.fingerprint[:8]}). ({self._applied_failure_patches}/{max_patches})"
        )
        fm_match = re.match(r"^\s*---\r?\n(.*?)\r?\n---\r?\n?", current_content, re.DOTALL)
        fm = current_content[: fm_match.end()] if fm_match else ""
        body_c = current_content[fm_match.end() :] if fm_match else current_content
        mutated_body = body_c.strip() + "\n\n" + card.strip()
        lines = mutated_body.splitlines()
        if len(lines) > 300:
            mutated_body = "\n".join(lines[:300])
        return (fm + mutated_body) if fm else mutated_body

    @staticmethod
    def _apply_strategy_to_body(body: str, enhancement: str) -> str:
        """Applies surgical section patching and compaction guard to SKILL.md body."""
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

        lines = mutated_body.splitlines()
        if len(lines) > 300:
            cleaned_lines = [
                line
                for line in lines
                if not line.startswith("<!-- Ratchet Optimization Refinement")
                and not line.startswith("- Cập nhật quy chuẩn rà soát vòng")
            ]
            mutated_body = "\n".join(cleaned_lines)
        return mutated_body

    def propose_mutation(self, current_content: str, iteration: int) -> str:
        """Generates a prompt mutation proposition based on multi-strategy optimization operators."""
        arch = resolve_domain_archetype(self.config.skill_name)
        arch_name = arch.name if arch else "general"

        failure_patched = self._try_propose_failure_patch(current_content, arch_name)
        if failure_patched is not None:
            return failure_patched

        all_strategies = load_mutation_strategies()
        strategies = all_strategies.get(arch_name) or all_strategies.get("general", [])
        if not strategies:
            return current_content

        fm_match = re.match(r"^\s*---\r?\n(.*?)\r?\n---\r?\n?", current_content, re.DOTALL)
        body = current_content[fm_match.end() :] if fm_match else current_content

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

        if chosen_strategy is None:
            return current_content

        _name, enhancement = chosen_strategy
        mutated_body = self._apply_strategy_to_body(body, enhancement)
        return self.preserve_yaml_frontmatter(current_content, mutated_body)

    def mutate_skill(self, current_content: str, iteration: int) -> str:
        """Mutates skill content by applying unapplied optimization strategies without junk comments."""
        return self.propose_mutation(current_content, iteration)

    def _rel_target_path_str(self) -> str:
        """Returns target_file POSIX path relative to project_root when possible."""
        try:
            rel_path = self.target_file.relative_to(self.project_root)
        except ValueError:
            rel_path = self.target_file
        return str(rel_path.as_posix())

    def git_commit_improvement(self, score_diff: str) -> bool:
        """Commits target file change to Git repository."""
        with self.git_lock:
            return self._git_commit_improvement_locked(score_diff)

    def _git_commit_improvement_locked(self, score_diff: str) -> bool:
        """Inner commit logic executed under git_lock."""
        if self.dry_run_git:
            logger.info(
                f"💾 [DRY-RUN] Git Commit: ratchet(opt): {self.target_file.name} {score_diff}"
            )
            return True

        rel_path_str = self._rel_target_path_str()
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
        with self.git_lock:
            self._git_rollback_target_locked(original_content, has_committed)

    def _git_rollback_target_locked(
        self, original_content: str, has_committed: bool = False
    ) -> None:
        """Inner rollback logic executed under git_lock."""
        try:
            self.target_file.write_text(original_content, encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to restore file content: {e}")

        rel_path_str = self._rel_target_path_str()
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

    def _find_link_audit_issues(self) -> list[Any]:
        """Runs LinkAuditor against target_file and returns any link/OKF violation issues."""
        try:
            if str(self.project_root) not in sys.path:
                sys.path.insert(0, str(self.project_root))
            from scripts.governance.link_auditor import LinkAuditor

            return [
                item_issue
                for item_issue in LinkAuditor(self.project_root).audit(self.target_file)
                if item_issue.category in ("links", "okf_links", "okf_conflicts")
            ]
        except Exception as e:
            logger.warning(f"⚠️ LinkAuditor check encountered error: {e}")
            return []

    def _run_pre_eval_guards(
        self,
        mutated_content: str,
        iter_idx: int,
        t0: float,
        prev_tokens: tuple[int, int, int],
        state: _RatchetLoopState,
    ) -> bool:
        """Applies candidate mutation to disk and validates pre-eval invariants (ADRs, link integrity)."""
        self.target_file.write_text(mutated_content, encoding="utf-8")

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

        link_issues = self._find_link_audit_issues()
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

        total_session_tokens = self.token_tracker.total_tokens
        if (
            self.config.hard_max_tokens_per_skill is not None
            and total_session_tokens >= self.config.hard_max_tokens_per_skill
        ):
            logger.info(
                f"🛑 [HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED] Tổng session tokens ({total_session_tokens:,}) "
                f"đã chạm ngưỡng trần tuyệt đối ({self.config.hard_max_tokens_per_skill:,}) sau {iter_idx} trials. "
                f"Dừng đột biến để bảo vệ ngân sách toàn đêm."
            )
            return True, "HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED"

        mutation_tokens = self.token_tracker.total_tokens - baseline_tokens
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
                state.finalize_error = str(e)

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

    def _check_zero_token_short_circuit(
        self, initial_content: str
    ) -> tuple[str, RatchetReport | None]:
        """Checks if all strategies and failure signals are already applied, returning short-circuit report."""
        unapplied = remaining_strategies(initial_content, self.config.skill_name)
        has_unapplied_signals = False
        arch = resolve_domain_archetype(self.config.skill_name)
        arch_name = arch.name if arch else "general"
        if arch_name in {"legal", "legal_tooling"}:
            ledger = load_failure_ledger(self.config.skill_name)
            if ledger and ledger.signals:
                unapplied_sigs = get_unapplied_failure_signals(
                    initial_content, list(ledger.signals)
                )
                has_unapplied_signals = len(unapplied_sigs) > 0

        if not unapplied and not has_unapplied_signals:
            logger.info(
                f"🛑 [HALT_NO_FURTHER_STRATEGIES] Skill '{self.config.skill_name}' đã áp dụng toàn bộ "
                f"chiến lược đột biến có sẵn và không còn tín hiệu lỗi chưa áp. Bỏ qua chấm điểm baseline và holdout để bảo toàn 100% token ngân sách."
            )
            base_score = (
                self.config.baseline_score if self.config.baseline_score is not None else 0.0
            )
            return arch_name, RatchetReport(
                target_file=str(self.target_file),
                initial_score=base_score,
                final_score=base_score,
                total_iterations=0,
                kept_commits=0,
                reverted_trials=0,
                history=[],
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                avg_latency_s=0.0,
                halt_reason="HALT_NO_FURTHER_STRATEGIES",
                slicing_tier=self.sliced_data.tier.value if self.sliced_data else None,
                tuning_size=len(self.tuning_dataset),
                holdout_size=len(self.holdout_dataset),
                holdout_score=base_score if base_score > 0 else None,
                holdout_initial_score=base_score if base_score > 0 else None,
            )
        return arch_name, None

    def _prepare_post_baseline_state(
        self, arch_name: str, baseline_report: EvalReport, initial_content: str
    ) -> tuple[float, int, int, int, _RatchetLoopState, RatchetReport | None]:
        """Seeds failure ledger and initializes ratchet loop state after baseline evaluation."""
        if arch_name in {"legal", "legal_tooling"}:
            try:
                signals = extract_failure_signals(
                    baseline_report, self.tuning_dataset, self.legal_index
                )
                if signals:
                    save_failure_ledger(self.config.skill_name, signals, initial_content)
                    logger.info(
                        f"⚖️ [LEDGER_SEEDED] Ghi nhận {len(signals)} tín hiệu lỗi vào sổ cái cho '{self.config.skill_name}'."
                    )
            except Exception as e:
                logger.warning(f"Lỗi trích xuất tín hiệu lỗi sau baseline: {e}")

        baseline_score = baseline_report.overall_score
        baseline_tokens = self.token_tracker.total_tokens
        effective_max_iter, effective_patience = self._init_ratchet_budget(baseline_score)
        state = _RatchetLoopState(
            best_score=baseline_score,
            best_content=initial_content,
            seen_hashes={hashlib.sha256(initial_content.encode("utf-8")).hexdigest()},
        )
        if (
            self.config.hard_max_tokens_per_skill is not None
            and self.token_tracker.total_tokens >= self.config.hard_max_tokens_per_skill
        ):
            logger.info(
                f"🛑 [HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED] Baseline tokens ({self.token_tracker.total_tokens:,}) "
                f"đã chạm hoặc vượt trần tuyệt đối ({self.config.hard_max_tokens_per_skill:,}). Dừng đột biến."
            )
            return (
                baseline_score,
                baseline_tokens,
                effective_max_iter,
                effective_patience,
                state,
                self._build_final_report(
                    baseline_score, None, None, "HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED", state
                ),
            )
        return baseline_score, baseline_tokens, effective_max_iter, effective_patience, state, None
