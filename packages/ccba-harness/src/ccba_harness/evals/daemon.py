"""daemon.py - Autonomous Multi-Skill Nightly Optimization Daemon (ADR-0023, ADR-0035, ADR-0057).

Extracts and encapsulates the batch optimization engine, WeightedPriorityQueue,
and Git-Ratchet iteration lifecycle into a first-class Deep Seam in ccba_harness.evals.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import subprocess
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import yaml

from ._daemon_reporting import (
    FLAGSHIP_REDTEAM_DATASET_OVERRIDES,
    NightlyDaemonReport,
    SkillEvolutionSummary,
    WeightedPriorityQueue,
    _DaemonReportingAndGitMixin,
    _resolve_daemon_env_int,
    find_project_root,
    get_last_applied_strategies_hash,
    get_mutation_strategies_hash,
    save_applied_strategies_hash,
)
from .archetypes import (
    resolve_domain_archetype,
    resolve_domain_dataset,
)
from .failure_mutator import (
    get_unapplied_failure_signals,
    load_failure_ledger,
)
from .tuner import (
    _UNSET,
    DEFAULT_MUTATION_STRATEGIES_PATH,
    GitRatchetTuner,
    RatchetConfig,
    RatchetReport,
    remaining_strategies,
)

logger = logging.getLogger("ccba.eval.nightly")


def send_telegram_alert(
    message: str,
    bot_token: str | None = None,
    chat_id: str | None = None,
    parse_mode: str = "Markdown",
    timeout: int = 10,
    mock_fallback: bool = False,
) -> bool:
    """Sends a notification message to Telegram Bot API or logs a mock fallback."""
    tg_bot_auth = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    target_channel = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not tg_bot_auth or not target_channel:
        if mock_fallback:
            logger.info(f"📱 [Mock Telegram Notification Sent]:\n{message}")
            return True
        logger.warning(
            "⚠️ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID. Telegram alert was not sent."
        )
        return False

    if "PYTEST_CURRENT_TEST" in os.environ and bot_token is None:
        logger.info(f"📱 [Mock Telegram Test Mode - Skipped Network Call]:\n{message}")
        return True

    endpoint_url = f"https://api.telegram.org/bot{tg_bot_auth}/sendMessage"
    data_dict: dict[str, str] = {"chat_id": str(target_channel), "text": message}
    if parse_mode:
        data_dict["parse_mode"] = parse_mode

    payload = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                logger.info("✅ Đã gửi thông báo Telegram thành công.")
                return True
            logger.warning(f"⚠️ Telegram API phản hồi mã: {resp.status}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Không thể gửi Telegram alert: {e}")
        return False


class NightlyTunerDaemon(_DaemonReportingAndGitMixin):
    """Orchestrates multi-skill batch optimization overnight."""

    def __init__(
        self,
        root: Path | None = None,
        max_iterations_low: int = 30,
        max_iterations_perfect: int = 1,
        early_stopping_patience: int = 5,
        use_real_llm: bool = False,
        token_budget: int = 10_000_000,
        per_skill_mutation_budget: int | None = cast(Any, _UNSET),
        model: str = "",
        target_skills: list[str] | None = None,
        alert_emitter: Callable[[str], bool] | None = None,
        target_ref: str = "origin/main",
        no_telegram: bool = False,
        skip_cooldown: bool = True,
        concurrency: int = cast(Any, _UNSET),
        hard_max_tokens_per_skill: int | None = cast(Any, _UNSET),
    ) -> None:
        self.root = (root or find_project_root()).resolve()
        self.max_iterations_low = max_iterations_low
        self.max_iterations_perfect = max_iterations_perfect
        self.early_stopping_patience = early_stopping_patience
        self.use_real_llm = use_real_llm
        self.concurrency = _resolve_daemon_env_int(concurrency, "CCBA_TUNER_CONCURRENCY", 5)
        self.token_budget = token_budget
        self.per_skill_mutation_budget = _resolve_daemon_env_int(
            per_skill_mutation_budget, "CCBA_TUNER_PER_SKILL_MUTATION_BUDGET", 250_000
        )
        self.hard_max_tokens_per_skill = _resolve_daemon_env_int(
            hard_max_tokens_per_skill, "CCBA_TUNER_HARD_MAX_PER_SKILL", 500_000
        )
        self.model = model
        self.target_skills = [s.strip().lower() for s in target_skills] if target_skills else None
        self.alert_emitter = alert_emitter
        self.no_telegram = no_telegram
        env_sc = os.getenv("CCBA_TUNER_SKIP_COOLDOWN")
        self.skip_cooldown = (
            env_sc.lower() in ("1", "true", "yes") if env_sc is not None else skip_cooldown
        )
        if target_ref == "origin/main":
            chk = subprocess.run(
                ["git", "rev-parse", "--verify", "origin/main"],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
            target_ref = "main" if chk.returncode != 0 else target_ref
        self.target_ref = target_ref
        self.test_cases_dir = self.root / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
        self.skills_dir = self.root / ".agents" / "skills"

    def _inspect_skill_status(
        self, skill_path: Path, skill_name: str
    ) -> tuple[bool, bool, bool, bool]:
        """Checks frontmatter auto-tune flag, strategy exhaustion, and failure ledger state."""
        skill_content = ""
        if not self.target_skills or skill_name.lower() not in self.target_skills:
            try:
                content = skill_path.read_text(encoding="utf-8", errors="replace")
                skill_content = content
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        fm = yaml.safe_load(parts[1])
                        if isinstance(fm, dict) and fm.get("auto-tune") is False:
                            logger.info(
                                f"⏭️ Bỏ qua {skill_name} do cấu hình auto-tune: false trong frontmatter."
                            )
                            return True, False, False, False
            except Exception as e:
                logger.debug(f"Failed to parse frontmatter for {skill_path}: {e}")

        if not skill_content:
            try:
                skill_content = skill_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return False, False, False, False

        is_exhausted = len(remaining_strategies(skill_content, skill_name)) == 0
        has_unapplied_signals = False
        needs_ledger_seed = False
        arch = resolve_domain_archetype(skill_name)
        arch_name = arch.name if arch else "general"
        if arch_name in {"legal", "legal_tooling"}:
            ledger = load_failure_ledger(skill_name)
            content_sha = hashlib.sha256(skill_content.encode("utf-8")).hexdigest()
            if ledger is not None and ledger.content_sha256 == content_sha:
                unapplied_sigs = get_unapplied_failure_signals(skill_content, list(ledger.signals))
                has_unapplied_signals = len(unapplied_sigs) > 0
            elif ledger is None:
                needs_ledger_seed = True
        return False, is_exhausted, has_unapplied_signals, needs_ledger_seed

    def discover_skills_and_datasets(self) -> list[dict[str, Any]]:
        """Maps discovered skills to their optimal evaluation datasets with historical baseline scores."""
        recent_scores, cooldown_skills, last_scanned_dates = self._load_historical_metrics(
            cooldown_days=3
        )
        curr_strat_hash = get_mutation_strategies_hash()
        last_strat_hash = get_last_applied_strategies_hash(self.root)
        strat_hash_unchanged = bool(curr_strat_hash and curr_strat_hash == last_strat_hash)

        discovered: list[dict[str, Any]] = []
        for skill_path in self.skills_dir.glob("*/SKILL.md"):
            skill_name = skill_path.parent.name
            skip, is_exhausted, has_unapplied_signals, needs_ledger_seed = (
                self._inspect_skill_status(skill_path, skill_name)
            )
            if skip:
                continue

            dataset_file = FLAGSHIP_REDTEAM_DATASET_OVERRIDES.get(
                skill_name, self._resolve_dataset_file(skill_name)
            )
            full_dataset_path = self.test_cases_dir / dataset_file
            if not full_dataset_path.exists():
                full_dataset_path = self.test_cases_dir / "eval_general_domain.json"

            discovered.append(
                {
                    "skill_name": skill_name,
                    "target_file": skill_path,
                    "dataset_file": full_dataset_path,
                    "eval_dataset_file": full_dataset_path,
                    "baseline_score": recent_scores.get(skill_name, 0.0),
                    "in_cooldown": skill_name in cooldown_skills,
                    "last_scanned_date": last_scanned_dates.get(skill_name),
                    "is_exhausted": is_exhausted,
                    "strat_hash_unchanged": strat_hash_unchanged,
                    "has_unapplied_signals": has_unapplied_signals,
                    "needs_ledger_seed": needs_ledger_seed,
                }
            )

        if self.target_skills:
            discovered = [d for d in discovered if d["skill_name"].lower() in self.target_skills]
        return discovered

    @staticmethod
    def _make_skip_summary(
        skill_name: str, target_file: Path, baseline_val: float, status: str, halt_reason: str
    ) -> SkillEvolutionSummary:
        """Creates a zero-token SkillEvolutionSummary for skipped or exhausted skills."""
        return SkillEvolutionSummary(
            skill_name=skill_name,
            target_file=target_file,
            baseline_score=baseline_val,
            final_score=baseline_val,
            commits_kept=0,
            rollbacks=0,
            status=status,
            total_tokens=0,
            prompt_tokens=0,
            completion_tokens=0,
            halt_reason=halt_reason,
            slicing_tier=None,
            holdout_score=baseline_val,
            tuning_size=0,
            holdout_size=0,
        )

    def _check_batch_item_skip(self, item: dict[str, Any]) -> SkillEvolutionSummary | None:
        """Returns a skip summary if the skill is in cooldown or already strategy-exhausted."""
        skill_name = item["skill_name"]
        target_file = item["target_file"]
        baseline_val = float(item.get("baseline_score", 0.0))

        if (
            self.skip_cooldown
            and item.get("in_cooldown")
            and not item.get("has_unapplied_signals")
            and not item.get("needs_ledger_seed")
        ):
            last_date_str = str(item.get("last_scanned_date") or "gần đây")
            logger.info(
                f"⏭️ [SKIP_COOLDOWN] Bỏ qua kỹ năng {skill_name} do đang trong cooldown "
                f"(lần quét trước: {last_date_str}, điểm: {baseline_val:.1f}%)."
            )
            return self._make_skip_summary(
                skill_name, target_file, baseline_val, "SKIPPED_COOLDOWN", "COOLDOWN_ACTIVE"
            )

        if (
            item.get("is_exhausted")
            and item.get("strat_hash_unchanged")
            and not item.get("has_unapplied_signals")
            and not item.get("needs_ledger_seed")
        ):
            logger.info(
                f"⏭️ [SKIP_EXHAUSTED] Bỏ qua kỹ năng {skill_name} do đã bão hòa chiến lược đột biến "
                f"và không còn tín hiệu lỗi chưa áp. Bảo lưu điểm số ({baseline_val:.1f}%), 0 token."
            )
            return self._make_skip_summary(
                skill_name,
                target_file,
                baseline_val,
                "HALT_NO_FURTHER_STRATEGIES",
                "HALT_NO_FURTHER_STRATEGIES",
            )
        return None

    def _build_skill_ratchet_config(
        self, item: dict[str, Any], remaining_budget: int
    ) -> RatchetConfig:
        """Constructs RatchetConfig for a single skill batch item."""
        max_iter = (
            1
            if (item.get("needs_ledger_seed") and not self.target_skills)
            else self.max_iterations_low
        )
        return RatchetConfig(
            target_file=item["target_file"],
            eval_dataset_file=item["dataset_file"],
            target_score=100.0,
            max_iterations=max_iter,
            skill_name=item["skill_name"],
            full_sweep=False,
            patience=self.early_stopping_patience,
            use_real_llm=self.use_real_llm,
            llm_model=self.model,
            token_budget=remaining_budget,
            per_skill_mutation_budget=self.per_skill_mutation_budget,
            hard_max_tokens_per_skill=self.hard_max_tokens_per_skill,
            max_concurrency=self.concurrency,
        )

    @staticmethod
    def _summary_from_ratchet_report(
        skill_name: str, target_file: Path, result: RatchetReport
    ) -> SkillEvolutionSummary:
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
        return SkillEvolutionSummary(
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

    def _run_single_skill_batch_item(
        self, item: dict[str, Any], remaining_budget: int, dry_run: bool
    ) -> tuple[SkillEvolutionSummary, bool]:
        """Executes GitRatchetTuner on a single skill item and returns (summary, should_halt_batch)."""
        skill_name, target_file = item["skill_name"], item["target_file"]
        logger.info(f"\n⚡ --- Tối ưu hóa Kỹ năng: {skill_name} ---")
        config = self._build_skill_ratchet_config(item, remaining_budget)
        try:
            tuner = GitRatchetTuner(config, dry_run_git=dry_run)
            result: RatchetReport = tuner.run()
            summary = self._summary_from_ratchet_report(skill_name, target_file, result)
            if not dry_run and result.final_score < 90.0 and result.kept_commits == 0:
                self._save_plateau_brief(skill_name, target_file, result)
            elif not dry_run and (result.final_score >= 90.0 or result.kept_commits > 0):
                self._remove_stale_plateau_brief(skill_name)

            if result.halt_reason in ("TOKEN_BUDGET_EXCEEDED", "CIRCUIT_BREAKER_OPEN"):
                logger.warning(
                    f"🛑 [Nightly Tuner Early Halt] Dừng quét toàn bộ hàng đợi kỹ năng do: {result.halt_reason}"
                )
                return summary, True
            return summary, False
        except Exception as e:
            logger.error(f"❌ Lỗi trong quá trình tối ưu {skill_name}: {e}")
            return (
                SkillEvolutionSummary(
                    skill_name=skill_name,
                    target_file=target_file,
                    baseline_score=0.0,
                    final_score=0.0,
                    commits_kept=0,
                    rollbacks=0,
                    status=f"ERROR: {e}",
                    halt_reason="ERROR",
                ),
                False,
            )

    def _finalize_nightly_report(
        self,
        report: NightlyDaemonReport,
        branch_name: str,
        now_str: str,
        total_commits: int,
        dry_run: bool,
    ) -> None:
        """Persists evolution markdown report, opens PR or cleans up branch, and sends Telegram alert."""
        report_md = self.generate_evolution_report_markdown(report)
        if not dry_run:
            reports_dir = self.root / ".md" / "knowledge" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_file = reports_dir / f"nightly_tuner_report_{now_str}.md"
            report_file.write_text(report_md, encoding="utf-8")
            logger.info(f"📄 Đã lưu báo cáo: {report_file}")
            curr_strat_hash = get_mutation_strategies_hash()
            if curr_strat_hash:
                save_applied_strategies_hash(self.root, curr_strat_hash)
        else:
            logger.info(
                "🧪 [DRY-RUN] Bỏ qua việc lưu báo cáo chính thức vào .md/knowledge/reports/"
            )

        if not dry_run and total_commits > 0:
            report.pr_url = self._create_pull_request(branch_name, report_md)
        elif not dry_run and total_commits == 0:
            self._cleanup_empty_branch(branch_name)

        if not self.no_telegram and not dry_run:
            report.telegram_notified = self.send_telegram_notification(report)

    def run_nightly_batch(self, dry_run: bool = False) -> NightlyDaemonReport:
        """Executes the full nightly optimization sweep across all prioritized skills."""
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"auto-tune/nightly-{now_str}"
        logger.info(f"🚀 Khởi chạy Nightly Auto-Tuner Daemon: {branch_name}")
        if not dry_run:
            self._cleanup_old_empty_branches(days=7)
            self._create_git_branch(branch_name)

        skills_info = self.discover_skills_and_datasets()
        logger.info(f"🔍 Đã phát hiện {len(skills_info)} kỹ năng trong catalog.")
        ranked_skills = WeightedPriorityQueue.rank_skills(skills_info)

        summaries: list[SkillEvolutionSummary] = []
        total_commits, total_tokens, total_p_tok, total_c_tok = 0, 0, 0, 0
        remaining_budget = self.token_budget

        for item in ranked_skills:
            skip_summary = self._check_batch_item_skip(item)
            if skip_summary is not None:
                summaries.append(skip_summary)
                continue
            summary, should_halt = self._run_single_skill_batch_item(
                item, remaining_budget, dry_run
            )
            summaries.append(summary)
            total_commits += summary.commits_kept
            total_tokens += summary.total_tokens
            total_p_tok += summary.prompt_tokens
            total_c_tok += summary.completion_tokens
            remaining_budget = max(0, remaining_budget - summary.total_tokens)
            if should_halt:
                break

        report = NightlyDaemonReport(
            timestamp=now_str,
            branch_name=branch_name,
            total_skills_scanned=len(summaries),
            skills_optimized=sum(1 for s in summaries if s.score_delta > 0),
            total_commits=total_commits,
            results=summaries,
            total_tokens=total_tokens,
            prompt_tokens=total_p_tok,
            completion_tokens=total_c_tok,
            engine="REAL_LLM" if self.use_real_llm else "MOCK",
        )
        self._finalize_nightly_report(report, branch_name, now_str, total_commits, dry_run)
        return report

    @staticmethod
    def _dispatch_chatops_gateway(
        message: str,
        stagnant: list[SkillEvolutionSummary],
        chatops_url: str,
        chatops_secret: str,
    ) -> bool:
        """Dispatches report and interactive /boost buttons to local ChatOps Gateway."""
        try:
            actions = [
                {
                    "action_id": f"boost_{s.skill_name}",
                    "label": f"🚀 /boost {s.skill_name}",
                    "command": "ccba.skill.boost",
                    "params": {"skill": s.skill_name},
                    "ttl_seconds": 86400,
                    "timeout": 600,
                }
                for s in stagnant[:3]
            ]
            payload = {
                "title": "CCBA NIGHTLY AUTO-TUNER REPORT",
                "body": message,
                "severity": "WARNING",
                "actions": actions,
            }
            req = urllib.request.Request(
                f"{chatops_url.rstrip('/')}/api/v1/notify",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-ChatOps-Secret": chatops_secret,
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    logger.info(
                        "✅ Đã gửi báo cáo Nightly Tuner kèm nút /boost qua ChatOps Gateway thành công."
                    )
                    return True
                logger.warning(f"⚠️ ChatOps Gateway phản hồi mã: {resp.status}")
        except Exception as e:
            logger.warning(f"⚠️ ChatOps Gateway dispatch thất bại, fallback: {e}")
        return False

    def send_telegram_notification(self, report: NightlyDaemonReport) -> bool:
        """Dispatches an alert to Telegram channel via Bot API or injected emitter."""
        message = (
            f"🌙 *CCBA NIGHTLY AUTO-TUNER REPORT* 🌙\n"
            f"📅 Thời gian: `{report.timestamp}` (Engine: `{report.engine}`)\n"
            f"🌿 Nhánh Git: `{report.branch_name}`\n"
            f"📈 Kỹ năng nâng cấp: *{report.skills_optimized}/{report.total_skills_scanned}*\n"
            f"💾 Số Git Commits: *{report.total_commits}*\n"
        )
        if report.total_tokens > 0:
            message += f"🪙 Tổng Token: *{report.total_tokens:,}*\n"
        if report.pr_url:
            message += f"🔗 Pull Request: {report.pr_url}\n"

        message += "\n🏆 *Top Cải Thiện:*\n"
        improved = [s for s in report.results if s.score_delta > 0]
        if improved:
            for s in improved[:5]:
                message += f"• `{s.skill_name}`: {s.baseline_score:.0f}% ➔ *{s.final_score:.0f}%* (+{s.score_delta:.0f}%)\n"
        else:
            message += "• Không có kỹ năng nào tăng điểm.\n"

        stagnant = [
            s
            for s in report.results
            if s.baseline_score < 90.0 and s.commits_kept == 0 and s.final_score < 90.0
        ]
        if stagnant:
            message += "\n⚠️ *Cần Can Thiệp (/boost):*\n"
            for s in stagnant[:3]:
                message += f"• `{s.skill_name}`: kẹt ở *{s.final_score:.0f}%*\n"

        chatops_secret = os.environ.get("CHATOPS_INTERNAL_SECRET")
        chatops_url = os.environ.get("CHATOPS_GATEWAY_URL", "http://127.0.0.1:8095")
        if stagnant and chatops_secret:
            if self._dispatch_chatops_gateway(message, stagnant, chatops_url, chatops_secret):
                return True

        if self.alert_emitter is not None:
            return self.alert_emitter(message)
        return send_telegram_alert(message=message, parse_mode="Markdown", mock_fallback=True)


__all__ = [
    "DEFAULT_MUTATION_STRATEGIES_PATH",
    "FLAGSHIP_REDTEAM_DATASET_OVERRIDES",
    "GitRatchetTuner",
    "NightlyDaemonReport",
    "NightlyTunerDaemon",
    "SkillEvolutionSummary",
    "WeightedPriorityQueue",
    "find_project_root",
    "get_last_applied_strategies_hash",
    "get_mutation_strategies_hash",
    "resolve_domain_dataset",
    "save_applied_strategies_hash",
    "send_telegram_alert",
]
