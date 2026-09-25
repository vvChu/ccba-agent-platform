"""daemon.py - Autonomous Multi-Skill Nightly Optimization Daemon (ADR-0023, ADR-0035, ADR-0057).

Extracts and encapsulates the batch optimization engine, WeightedPriorityQueue,
and Git-Ratchet iteration lifecycle into a first-class Deep Seam in ccba_harness.evals.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .archetypes import (
    resolve_domain_dataset,
)
from .tuner import (
    GitRatchetTuner,
    RatchetConfig,
    RatchetReport,
)

logger = logging.getLogger("ccba.eval.nightly")


def find_project_root(start_dir: Path | None = None) -> Path:
    """Discovers project root by walking upward until .git or pyproject.toml is found."""
    current = (start_dir or Path.cwd()).resolve()
    for p in [current, *current.parents]:
        if (p / ".git").exists() or (p / ".agents").exists():
            return p
    # Fallback to package ancestor if cwd is somewhere else
    pkg_ancestor = Path(__file__).resolve().parents[5]
    if (pkg_ancestor / ".git").exists() or (pkg_ancestor / ".agents").exists():
        return pkg_ancestor
    return current


def send_telegram_alert(
    message: str,
    bot_token: str | None = None,
    chat_id: str | None = None,
    parse_mode: str = "Markdown",
    timeout: int = 10,
    mock_fallback: bool = False,
) -> bool:
    """Send a notification message to Telegram Bot API.

    Args:
        message: The message body to send (supports Markdown or HTML).
        bot_token: Telegram Bot API Token. If omitted, read from TELEGRAM_BOT_TOKEN env.
        chat_id: Target Chat or Channel ID. If omitted, read from TELEGRAM_CHAT_ID env.
        parse_mode: Telegram parse mode ("Markdown", "MarkdownV2", "HTML", or empty).
        timeout: Network timeout in seconds for urllib request.
        mock_fallback: If True, missing credentials log a mock notification and return True
            (ideal for unattended nightly daemons). If False, returns False.

    Returns:
        bool: True if message was sent successfully (or mock-handled), False otherwise.
    """
    bot_credential = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    target_channel = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_credential or not target_channel:
        if mock_fallback:
            logger.info(f"📱 [Mock Telegram Notification Sent]:\n{message}")
            return True
        logger.warning(
            "⚠️ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID. Telegram alert was not sent."
        )
        return False

    endpoint_url = f"https://api.telegram.org/bot{bot_credential}/sendMessage"
    data_dict: dict[str, str] = {
        "chat_id": str(target_channel),
        "text": message,
    }
    if parse_mode:
        data_dict["parse_mode"] = parse_mode

    payload = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url,
        data=payload,
        headers={"Content-Type": "application/json"},
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


@dataclass
class SkillEvolutionSummary:
    """Summary of optimization progress for a single skill."""

    skill_name: str
    target_file: Path
    baseline_score: float
    final_score: float
    commits_kept: int
    rollbacks: int
    status: str = "UNCHANGED"
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    halt_reason: str | None = None
    slicing_tier: str | None = None
    holdout_score: float | None = None
    tuning_size: int = 0
    holdout_size: int = 0

    @property
    def score_delta(self) -> float:
        return self.final_score - self.baseline_score


@dataclass
class NightlyDaemonReport:
    """Aggregated report of a nightly optimization run across all skills."""

    timestamp: str
    branch_name: str
    total_skills_scanned: int
    skills_optimized: int
    total_commits: int
    results: list[SkillEvolutionSummary] = field(default_factory=list)
    pr_url: str | None = None
    telegram_notified: bool = False
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    engine: str = "MOCK"


class WeightedPriorityQueue:
    """Prioritizes skills based on baseline scores and test case freshness."""

    @staticmethod
    def rank_skills(skills_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sorts skills such that non-cooldown skills and lower baseline scores are tuned first."""

        def priority_key(item: dict[str, Any]) -> tuple[int, datetime.date, int, float]:
            in_cooldown = 1 if item.get("in_cooldown") else 0
            raw_date = item.get("last_scanned_date")
            if isinstance(raw_date, datetime.datetime):
                scanned_date = raw_date.date()
            elif isinstance(raw_date, datetime.date):
                scanned_date = raw_date
            elif isinstance(raw_date, str):
                try:
                    scanned_date = datetime.date.fromisoformat(raw_date[:10])
                except Exception:
                    scanned_date = datetime.date.min
            else:
                scanned_date = datetime.date.min
            raw_score = item.get("baseline_score")
            score = float(raw_score) if raw_score is not None else 0.0
            tier = 0 if score < 90.0 else (1 if score < 100.0 else 2)
            return (in_cooldown, scanned_date, tier, score)

        return sorted(skills_data, key=priority_key)


# Specialized Red-Team dataset overrides for flagship skills (all others resolve via SSOT)
FLAGSHIP_REDTEAM_DATASET_OVERRIDES: dict[str, str] = {
    "ccba-legal-intel": "eval_legal_intel_redteam.json",
    "ccba-ai-qc-pccc-audit": "eval_pccc_audit_redteam.json",
    "bigbim-classification": "eval_bigbim_classification_redteam.json",
    "ccba-ai-qc": "eval_pccc_audit_redteam.json",
}


class NightlyTunerDaemon:
    """Orchestrates multi-skill batch optimization overnight."""

    def __init__(
        self,
        root: Path | None = None,
        max_iterations_low: int = 30,
        max_iterations_perfect: int = 1,
        early_stopping_patience: int = 5,
        use_real_llm: bool = False,
        token_budget: int = 10_000_000,
        per_skill_mutation_budget: int | None = 250_000,
        model: str = "",
        target_skills: list[str] | None = None,
        alert_emitter: Callable[[str], bool] | None = None,
        target_ref: str = "origin/main",
        no_telegram: bool = False,
        skip_cooldown: bool = False,
    ) -> None:
        self.root = (root or find_project_root()).resolve()
        self.max_iterations_low = max_iterations_low
        self.max_iterations_perfect = max_iterations_perfect
        self.early_stopping_patience = early_stopping_patience
        self.use_real_llm = use_real_llm
        self.token_budget = token_budget
        self.per_skill_mutation_budget = per_skill_mutation_budget
        self.model = model
        self.target_skills = [s.strip().lower() for s in target_skills] if target_skills else None
        self.alert_emitter = alert_emitter
        self.no_telegram = no_telegram
        self.skip_cooldown = skip_cooldown
        # Determine valid target_ref (fallback to main if origin/main cannot be verified)
        if target_ref == "origin/main":
            check_ref = subprocess.run(
                ["git", "rev-parse", "--verify", "origin/main"],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
            if check_ref.returncode != 0:
                target_ref = "main"
        self.target_ref = target_ref
        self.test_cases_dir = self.root / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
        self.skills_dir = self.root / ".agents" / "skills"

    def _resolve_dataset_file(self, skill_name: str) -> str:
        """Dynamically matches a skill to its optimal Domain Archetype evaluation dataset (SSOT Delegation)."""
        return resolve_domain_dataset(skill_name)

    def _extract_report_date(self, r_file: Path, content: str) -> datetime.date | None:
        """Extracts date from report filename or content with fallback to file mtime."""
        fn_match = re.search(r"nightly_tuner_report_(\d{4})[-_]?(\d{2})[-_]?(\d{2})", r_file.name)
        if fn_match:
            try:
                return datetime.date(
                    int(fn_match.group(1)), int(fn_match.group(2)), int(fn_match.group(3))
                )
            except ValueError:
                pass

        content_match = re.search(
            r"\*\*Thời gian(?: thực thi)?:\*\*\s*`?(\d{4})[-_]?(\d{2})[-_]?(\d{2})", content
        )
        if content_match:
            try:
                return datetime.date(
                    int(content_match.group(1)),
                    int(content_match.group(2)),
                    int(content_match.group(3)),
                )
            except ValueError:
                pass

        try:
            return datetime.date.fromtimestamp(r_file.stat().st_mtime)
        except Exception:
            return None

    def _load_historical_metrics(
        self, cooldown_days: int = 3
    ) -> tuple[dict[str, float], set[str], dict[str, datetime.date]]:
        """Loads baseline scores across all available reports and identifies cooldown skills.

        Cooldown conditions (ADR-0052):
        - Report ran within the last `cooldown_days` (r_date >= cutoff_date)
        - Engine is REAL_LLM
        - commits == 0
        - final score < 90.0 or status is UNCHANGED / starts with HALT_
        """
        reports_dir = self.root / ".md" / "knowledge" / "reports"
        if not reports_dir.exists():
            return {}, set(), {}

        def _report_sort_key(f: Path) -> tuple[datetime.date, float]:
            try:
                fn_match = re.search(
                    r"nightly_tuner_report_(\d{4})[-_]?(\d{2})[-_]?(\d{2})", f.name
                )
                if fn_match:
                    d = datetime.date(
                        int(fn_match.group(1)),
                        int(fn_match.group(2)),
                        int(fn_match.group(3)),
                    )
                    return (d, f.stat().st_mtime)
                content = f.read_text(encoding="utf-8", errors="replace")
                extracted_d = self._extract_report_date(f, content)
                if extracted_d:
                    return (extracted_d, f.stat().st_mtime)
            except Exception:
                pass
            try:
                return (datetime.date.fromtimestamp(f.stat().st_mtime), f.stat().st_mtime)
            except Exception:
                return (datetime.date.min, 0.0)

        report_files = sorted(
            reports_dir.glob("nightly_tuner_report_*.md"), key=_report_sort_key, reverse=True
        )
        scores: dict[str, float] = {}
        cooldown_skills: set[str] = set()
        evaluated_recent: set[str] = set()
        last_scanned_dates: dict[str, datetime.date] = {}

        today = datetime.date.today()
        cutoff_date = today - datetime.timedelta(days=cooldown_days)

        pattern_7 = re.compile(
            r"\|\s*`?([a-zA-Z0-9_-]+)`?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?\s*\|\s*`?[^|]*`?\s*\|\s*`?(\d+)`?\s*\|\s*[^|]*\|\s*([^|\r\n]+)\|"
        )
        pattern_3 = re.compile(
            r"\|\s*`?([a-zA-Z0-9_-]+)`?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?"
        )

        for r_file in report_files:
            try:
                content = r_file.read_text(encoding="utf-8", errors="replace")
                r_date = self._extract_report_date(r_file, content)
                is_real_llm = bool(
                    re.search(r"\*\*Engine:\*\*\s*`?REAL_LLM`?", content, re.IGNORECASE)
                ) or ("Engine: REAL_LLM" in content)
                is_within_cooldown = r_date is not None and r_date >= cutoff_date

                matched_in_file: set[str] = set()

                for match in pattern_7.finditer(content):
                    s_name = match.group(1).strip()
                    s_final = float(match.group(3))
                    commits = int(match.group(4))
                    status_str = match.group(5).strip().upper()
                    matched_in_file.add(s_name)

                    if s_name not in scores:
                        scores[s_name] = s_final

                    if r_date is not None and s_name not in last_scanned_dates:
                        last_scanned_dates[s_name] = r_date

                    if is_within_cooldown and is_real_llm:
                        if s_name not in evaluated_recent:
                            evaluated_recent.add(s_name)
                            if commits == 0 and (
                                s_final < 90.0 or "UNCHANGED" in status_str or "HALT_" in status_str
                            ):
                                cooldown_skills.add(s_name)

                for match in pattern_3.finditer(content):
                    s_name = match.group(1).strip()
                    if s_name in matched_in_file:
                        continue
                    s_final = float(match.group(3))
                    if s_name not in scores:
                        scores[s_name] = s_final
                    if r_date is not None and s_name not in last_scanned_dates:
                        last_scanned_dates[s_name] = r_date
            except Exception as e:
                logger.debug(f"Failed parsing report file {r_file}: {e}")
                continue

        return scores, cooldown_skills, last_scanned_dates

    def _load_recent_baseline_scores(self) -> dict[str, float]:
        """Loads historical scores from recent reports to calibrate priority queue ranking."""
        scores, _, _ = self._load_historical_metrics()
        return scores

    def discover_skills_and_datasets(self) -> list[dict[str, Any]]:
        """Maps discovered skills to their optimal evaluation datasets with historical baseline scores."""
        recent_scores, cooldown_skills, last_scanned_dates = self._load_historical_metrics(
            cooldown_days=3
        )
        discovered: list[dict[str, Any]] = []
        for skill_path in self.skills_dir.glob("*/SKILL.md"):
            skill_name = skill_path.parent.name

            # Skip skills marked with auto-tune: false unless explicitly targeted
            if not self.target_skills or skill_name.lower() not in self.target_skills:
                try:
                    content = skill_path.read_text(encoding="utf-8", errors="replace")
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            fm = yaml.safe_load(parts[1])
                            if isinstance(fm, dict) and fm.get("auto-tune") is False:
                                logger.info(
                                    f"⏭️ Bỏ qua {skill_name} do cấu hình auto-tune: false trong frontmatter."
                                )
                                continue
                except Exception as e:
                    logger.debug(f"Failed to parse frontmatter for {skill_path}: {e}")

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
                }
            )

        if self.target_skills:
            discovered = [d for d in discovered if d["skill_name"].lower() in self.target_skills]

        return discovered

    def run_nightly_batch(self, dry_run: bool = False) -> NightlyDaemonReport:
        """Executes the full nightly optimization sweep across all prioritized skills."""
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"auto-tune/nightly-{now_str}"

        logger.info(f"🚀 Khởi chạy Nightly Auto-Tuner Daemon: {branch_name}")

        # 1. Dọn dẹp các nhánh rác cũ và tạo nhánh Git mới nếu không chạy dry_run
        if not dry_run:
            self._cleanup_old_empty_branches(days=7)
            self._create_git_branch(branch_name)

        # 2. Khám phá và chấm điểm sơ bộ để xếp hàng đợi ưu tiên
        skills_info = self.discover_skills_and_datasets()
        logger.info(f"🔍 Đã phát hiện {len(skills_info)} kỹ năng trong catalog.")

        # Xếp hàng đợi ưu tiên
        ranked_skills = WeightedPriorityQueue.rank_skills(skills_info)

        summaries: list[SkillEvolutionSummary] = []
        total_commits = 0
        total_tokens = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        remaining_budget = self.token_budget

        # 3. Chạy tối ưu từng kỹ năng theo hàng đợi
        for item in ranked_skills:
            skill_name = item["skill_name"]
            target_file = item["target_file"]
            dataset_file = item["dataset_file"]

            # Bỏ qua kỹ năng nếu đang trong thời gian cooldown và cờ skip_cooldown được kích hoạt
            if self.skip_cooldown and item.get("in_cooldown"):
                last_date_str = str(item.get("last_scanned_date") or "gần đây")
                baseline_val = float(item.get("baseline_score", 0.0))
                logger.info(
                    f"⏭️ [SKIP_COOLDOWN] Bỏ qua kỹ năng {skill_name} do đang trong cooldown "
                    f"(lần quét trước: {last_date_str}, điểm: {baseline_val:.1f}%)."
                )
                summary = SkillEvolutionSummary(
                    skill_name=skill_name,
                    target_file=target_file,
                    baseline_score=baseline_val,
                    final_score=baseline_val,
                    commits_kept=0,
                    rollbacks=0,
                    status="SKIPPED_COOLDOWN",
                    total_tokens=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    halt_reason="COOLDOWN_ACTIVE",
                    slicing_tier=None,
                    holdout_score=baseline_val,
                    tuning_size=0,
                    holdout_size=0,
                )
                summaries.append(summary)
                continue

            logger.info(f"\n⚡ --- Tối ưu hóa Kỹ năng: {skill_name} ---")

            # Cấu hình vòng lặp động
            config = RatchetConfig(
                target_file=target_file,
                eval_dataset_file=dataset_file,
                target_score=100.0,
                max_iterations=self.max_iterations_low,
                skill_name=skill_name,
                full_sweep=False,
                patience=self.early_stopping_patience,
                use_real_llm=self.use_real_llm,
                llm_model=self.model,
                token_budget=remaining_budget,
                per_skill_mutation_budget=self.per_skill_mutation_budget,
            )

            try:
                tuner = GitRatchetTuner(config, dry_run_git=dry_run)
                result: RatchetReport = tuner.run()

                status = "IMPROVED" if result.final_score > result.initial_score else "UNCHANGED"
                if result.final_score == 100.0 and result.initial_score == 100.0:
                    status = "PERFECT_VERIFIED"
                if result.halt_reason:
                    status = (
                        result.halt_reason
                        if result.halt_reason.startswith("HALT_")
                        else f"HALT_{result.halt_reason}"
                    )

                total_tokens += result.total_tokens
                total_prompt_tokens += result.prompt_tokens
                total_completion_tokens += result.completion_tokens
                remaining_budget = max(0, remaining_budget - result.total_tokens)

                summary = SkillEvolutionSummary(
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
                summaries.append(summary)
                total_commits += result.kept_commits

                # ADR-0052: Export Plateau Escalation Brief if skill remains stagnant < 90%
                if not dry_run and result.final_score < 90.0 and result.kept_commits == 0:
                    self._save_plateau_brief(skill_name, target_file, result)
                elif not dry_run and (result.final_score >= 90.0 or result.kept_commits > 0):
                    self._remove_stale_plateau_brief(skill_name)

                if result.halt_reason in ("TOKEN_BUDGET_EXCEEDED", "CIRCUIT_BREAKER_OPEN"):
                    logger.warning(
                        f"🛑 [Nightly Tuner Early Halt] Dừng quét toàn bộ hàng đợi kỹ năng do: {result.halt_reason}"
                    )
                    break

            except Exception as e:
                logger.error(f"❌ Lỗi trong quá trình tối ưu {skill_name}: {e}")
                summaries.append(
                    SkillEvolutionSummary(
                        skill_name=skill_name,
                        target_file=target_file,
                        baseline_score=0.0,
                        final_score=0.0,
                        commits_kept=0,
                        rollbacks=0,
                        status=f"ERROR: {e}",
                    )
                )

        # 4. Tổng hợp Báo Cáo Tiến Hóa (Evolution Report)
        skills_improved = sum(1 for s in summaries if s.score_delta > 0)
        report = NightlyDaemonReport(
            timestamp=now_str,
            branch_name=branch_name,
            total_skills_scanned=len(summaries),
            skills_optimized=skills_improved,
            total_commits=total_commits,
            results=summaries,
            total_tokens=total_tokens,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            engine="REAL_LLM" if self.use_real_llm else "MOCK",
        )

        report_md = self.generate_evolution_report_markdown(report)

        if not dry_run:
            reports_dir = self.root / ".md" / "knowledge" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_file = reports_dir / f"nightly_tuner_report_{now_str}.md"
            report_file.write_text(report_md, encoding="utf-8")
            logger.info(f"📄 Đã lưu báo cáo: {report_file}")
        else:
            logger.info(
                "🧪 [DRY-RUN] Bỏ qua việc lưu báo cáo chính thức vào .md/knowledge/reports/"
            )

        # 5. Tự động mở GitHub Pull Request nếu có cải tiến
        if not dry_run and total_commits > 0:
            pr_url = self._create_pull_request(branch_name, report_md)
            report.pr_url = pr_url
        elif not dry_run and total_commits == 0:
            self._cleanup_empty_branch(branch_name)

        # 6. Gửi thông báo Telegram Bot
        if not self.no_telegram and not dry_run:
            telegram_sent = self.send_telegram_notification(report)
            report.telegram_notified = telegram_sent

        return report

    def generate_evolution_report_markdown(self, report: NightlyDaemonReport) -> str:
        """Renders an evolution summary report in Markdown format."""
        lines = [
            "# 🌙 CCBA Nightly Auto-Tuner Evolution Report",
            f"> **Thời gian thực thi:** `{report.timestamp}` | **Engine:** `{report.engine}`  ",
            f"> **Nhánh Git:** `{report.branch_name}`  ",
            f"> **Tổng kỹ năng quét:** `{report.total_skills_scanned}` | **Kỹ năng cải thiện:** `{report.skills_optimized}` | **Số Commits:** `{report.total_commits}`",
        ]
        if report.total_tokens > 0:
            lines.append(
                f"> **Tổng Token Tiêu Thụ:** `{report.total_tokens:,}` (Prompt: `{report.prompt_tokens:,}` | Completion: `{report.completion_tokens:,}`)"
            )
        lines.extend(
            [
                "",
                "---",
                "",
                "### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)",
                "| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
            ]
        )

        for s in report.results:
            delta_str = f"+{s.score_delta:.1f}%" if s.score_delta > 0 else f"{s.score_delta:.1f}%"
            badge = (
                "🟢 IMPROVED"
                if s.score_delta > 0
                else ("⭐ 100% PERFECT" if s.final_score == 100.0 else "⚪ UNCHANGED")
            )
            if s.halt_reason and s.score_delta <= 0:
                badge = f"⚠️ {s.status}"
            token_str = f"{s.total_tokens:,}" if s.total_tokens > 0 else "-"
            lines.append(
                f"| `{s.skill_name}` | {s.baseline_score:.1f}% | **{s.final_score:.1f}%** | `{delta_str}` | {s.commits_kept} | `{token_str}` | {badge} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "### 🛡️ Rào Chắn An Toàn (Safety Hard Floor Invariant)",
                "- ✅ **Zero-Regression:** 100% các đột biến làm giảm điểm hoặc dính Điểm Liệt đã được `git checkout` hoàn tác sạch.",
                "- ✅ **Hard Floor Compliance:** Tuyệt đối không chấp thuận các điều luật bãi bỏ hoặc lỗi kỹ thuật nghiêm trọng.",
                "",
                "---",
                "*Báo cáo được tạo tự động bởi CCBA Nightly Auto-Tuner Daemon trên Server Spark.*",
            ]
        )
        return "\n".join(lines)

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

        if self.alert_emitter is not None:
            return self.alert_emitter(message)

        return send_telegram_alert(
            message=message,
            parse_mode="Markdown",
            mock_fallback=True,
        )

    def _save_plateau_brief(
        self, skill_name: str, target_file: Path, result: RatchetReport
    ) -> Path:
        """Saves a Deep Problem Brief for stagnant skills under ADR-0052 Section 3.B for daytime human review."""
        escalations_dir = self.root / ".md" / "knowledge" / "escalations"
        escalations_dir.mkdir(parents=True, exist_ok=True)
        brief_file = escalations_dir / f"{skill_name}_plateau.md"

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dataset_file = self._resolve_dataset_file(skill_name)
        delta = result.final_score - result.initial_score
        delta_str = f"+{delta:.1f}%" if delta > 0 else f"{delta:.1f}%"
        total_tokens_str = f"{result.total_tokens:,}" if result.total_tokens is not None else "0"
        prompt_tokens_str = f"{result.prompt_tokens:,}" if result.prompt_tokens is not None else "0"
        completion_tokens_str = (
            f"{result.completion_tokens:,}" if result.completion_tokens is not None else "0"
        )
        holdout_score_str = (
            f"{result.holdout_score:.1f}%" if result.holdout_score is not None else "N/A"
        )
        holdout_size_str = str(result.holdout_size) if result.holdout_size is not None else "0"
        slicing_tier_str = f"Tier {result.slicing_tier}" if result.slicing_tier else "N/A"

        content = f"""# ⚠️ CCBA Plateau Escalation Brief (ADR-0052): {skill_name}

> **Mã hồ sơ:** `PLATEAU-{skill_name.upper()}`
> **Thời gian ghi nhận:** `{now_str}`
> **Tệp nguồn:** [`{target_file.name}`]({target_file})
> **Trạng thái:** `STAGNANT_PLATEAU` (Cần can thiệp suy luận sâu)

---

## 1. Failure Manifest
- **Baseline Score:** `{result.initial_score:.1f}%`
- **Peak Score Achieved:** `{result.final_score:.1f}%` (Chênh lệch: `{delta_str}`)
- **Vòng lặp đã thử nghiệm:** `{result.total_iterations}` vòng (Ngừng bởi: `{result.halt_reason or "PATIENCE_EXHAUSTED"}`)
- **Số lần Rollback:** `{result.reverted_trials}` lần
- **Tổng Token tiêu tốn:** `{total_tokens_str}` tokens (Prompt: `{prompt_tokens_str}` | Completion: `{completion_tokens_str}`)

## 2. Tested Hypotheses & Ineffective Mutations
- Đã áp dụng các đột biến tri thức (Surgical Section Patching) theo tập chiến lược của archetype nhưng điểm số không vượt qua trần baseline.
- Toàn bộ các thử nghiệm đột biến đều bị hoàn tác (REVERT) hoặc dừng sớm do:
  + Dính Điểm Liệt (Critical Failures / Vi phạm điều kiện nghiêm ngặt).
  + Không cải thiện điểm số vượt qua ngưỡng holdout split.
  + Đột biến trùng lặp hoặc cạn kiệt chiến lược định sẵn (`HALT_NO_FURTHER_STRATEGIES`).

## 3. Deep Seams & Archetype Involved
- **Evaluation Dataset:** `{dataset_file}`
- **Slicing Tier:** `{slicing_tier_str}` (Holdout Score: `{holdout_score_str}`, Holdout Size: `{holdout_size_str}`)
- **Deep Seams liên quan:** Prompt Instruction Rules trong `SKILL.md`, Bộ quy chuẩn Scorer regex/deterministic parsing, và Test Case Fixtures.

## 4. Error Logs & Failure Excerpts
```text
Halt Reason: {result.halt_reason or "EARLY_STOPPING_PATIENCE_EXHAUSTED"}
Total Iterations: {result.total_iterations}
Reverted Trials: {result.reverted_trials}/{result.total_iterations}
Final Holdout Score: {holdout_score_str}
```

## 5. Actionable Recommendation (/boost Protocol)
Kỹ năng này đã cạn kiệt ngân sách kiên nhẫn (`patience`) trên mô hình cục bộ mà không vượt qua được điểm nghẽn.
Theo quy chuẩn **ADR-0052 (Boost Deep Reasoning Protocol)**, kỹ sư CCBA hãy chủ động can thiệp ban ngày:

1. **Khởi chạy Interactive Boost trên Worktree cô lập:**
   ```bash
   bash scripts/eval/run_boost_worktree.sh {skill_name}
   ```
2. **Khởi chạy Daemon với mô hình suy luận cao cấp:**
   ```bash
   python scripts/eval/nightly_tuner_daemon.py --skill {skill_name} --use-real-llm --model gemini-3.8-flash-high --max-iter 3
   ```
3. **Kích hoạt qua Antigravity Chat:** Gõ `/boost` kèm nội dung brief này để rà soát Instruction Conflicts giữa `SKILL.md` và Scorer.
"""
        brief_file.write_text(content, encoding="utf-8")
        logger.info(f"📋 Đã xuất Plateau Brief (ADR-0052 5-Fields): {brief_file}")
        return brief_file

    def _get_main_repo_root(self) -> Path | None:
        """If running inside a secondary git worktree, resolves the main repo root."""
        git_path = self.root / ".git"
        if git_path.is_file():
            try:
                content = git_path.read_text(encoding="utf-8").strip()
                if content.startswith("gitdir:"):
                    gitdir = Path(content.split(":", 1)[1].strip())
                    if not gitdir.is_absolute():
                        gitdir = (self.root / gitdir).resolve()
                    if "worktrees" in gitdir.parts:
                        # gitdir is /path/to/main/.git/worktrees/<name>
                        return gitdir.parent.parent.parent
            except Exception:
                pass
        return None

    def _remove_stale_plateau_brief(self, skill_name: str) -> bool:
        """Removes stale plateau escalation brief if skill achieved target score or made progress."""
        escalations_dir = self.root / ".md" / "knowledge" / "escalations"
        brief_file = escalations_dir / f"{skill_name}_plateau.md"
        removed = False
        if brief_file.exists():
            try:
                brief_file.unlink()
                logger.info(
                    f"🗑️ Đã xóa stale Plateau Brief do kỹ năng đã cải thiện/đạt mục tiêu: {brief_file.name}"
                )
                removed = True
            except Exception as e:
                logger.warning(f"Không thể xóa stale plateau brief {brief_file}: {e}")

        # If running inside a git worktree, also delete from main repo root
        main_root = self._get_main_repo_root()
        if main_root and main_root != self.root:
            main_brief = (
                main_root / ".md" / "knowledge" / "escalations" / f"{skill_name}_plateau.md"
            )
            if main_brief.exists():
                try:
                    main_brief.unlink()
                    logger.info(f"🗑️ Đã xóa stale Plateau Brief ở main repo: {main_brief.name}")
                    removed = True
                except Exception as e:
                    logger.warning(f"Không thể xóa main repo plateau brief {main_brief}: {e}")

        return removed

    def _cleanup_old_empty_branches(self, days: int = 7) -> int:
        """Cleans up local and remote auto-tune and doc-refactor branches older than `days` with no unique commits."""
        try:
            res = subprocess.run(
                ["git", "branch", "--list", "auto-tune/nightly-*", "docs/auto-refactor-*"],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            branches = [b.strip().lstrip("* ") for b in res.stdout.splitlines() if b.strip()]
            deleted_count = 0
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).date()

            # Determine base ref for comparison (prefer self.target_ref, fallback to main)
            base_ref = self.target_ref
            check_ref = subprocess.run(
                ["git", "rev-parse", "--verify", self.target_ref],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
            if check_ref.returncode != 0:
                base_ref = "main"

            for b in branches:
                match = re.search(r"(?:nightly|auto-refactor)-(\d{8})", b)
                if match:
                    date_str = match.group(1)
                    try:
                        b_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
                        if b_date < cutoff_date:
                            # Check if branch has unique commits not on base_ref
                            diff_res = subprocess.run(
                                ["git", "cherry", base_ref, b],
                                cwd=str(self.root),
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                            )
                            if diff_res.returncode == 0 and not diff_res.stdout.strip():
                                subprocess.run(
                                    ["git", "branch", "-D", b],
                                    cwd=str(self.root),
                                    capture_output=True,
                                    check=False,
                                )
                                logger.info(f"🧹 Đã dọn dẹp nhánh rác cục bộ: {b}")
                                # Best-effort deletion of remote branch if present
                                try:
                                    subprocess.run(
                                        ["git", "push", "origin", "--delete", b],
                                        cwd=str(self.root),
                                        capture_output=True,
                                        check=False,
                                    )
                                    logger.info(f"🧹 Đã dọn dẹp nhánh rác remote: {b}")
                                    deleted_count += 1
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.debug(f"Bỏ qua nhánh {b}: {e}")
            return deleted_count
        except Exception as e:
            logger.warning(f"⚠️ Lỗi dọn dẹp nhánh cũ: {e}")
            return 0

    def _create_git_branch(self, branch_name: str) -> None:
        """Creates and checks out a new feature branch for the nightly run."""
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(self.root),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            logger.info(f"🌿 Đã tạo nhánh Git mới: {branch_name}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Không thể tạo nhánh {branch_name}: {e}")

    def _cleanup_empty_branch(self, branch_name: str) -> None:
        """Detaches HEAD and deletes empty branch when total_commits == 0."""
        try:
            subprocess.run(
                ["git", "checkout", "--detach"],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
            is_worktree = bool(self._get_main_repo_root())
            if not is_worktree:
                subprocess.run(
                    ["git", "checkout", self.target_ref],
                    cwd=str(self.root),
                    capture_output=True,
                    check=False,
                )
                logger.info(f"🌿 Đã khôi phục HEAD repo chính về: {self.target_ref}")
            logger.info(f"🧹 Đã xóa nhánh rỗng không có commit: {branch_name}")
        except Exception as e:
            logger.warning(f"⚠️ Lỗi dọn dẹp nhánh rỗng {branch_name}: {e}")

    def _create_pull_request(self, branch_name: str, report_body: str) -> str | None:
        """Pushes branch and creates a GitHub Pull Request using GitHub CLI (gh) if available."""
        # 0. Tự động kiểm tra và đồng bộ Traceability Matrix để phòng ngừa lỗi lệch ma trận tài liệu
        try:
            sync_script = self.root / "scripts" / "sync_hub_adr_matrix.py"
            if sync_script.exists():
                logger.info("🔄 Đang kiểm tra và tự động đồng bộ Traceability Matrix...")
                subprocess.run(
                    [sys.executable, str(sync_script), "--hub-dir", str(self.root)],
                    cwd=str(self.root),
                    capture_output=True,
                    check=False,
                )
                matrix_file = self.root / "docs" / "adr" / "TRACEABILITY_MATRIX.md"
                if matrix_file.exists():
                    status_res = subprocess.run(
                        ["git", "status", "--porcelain", "docs/adr/TRACEABILITY_MATRIX.md"],
                        cwd=str(self.root),
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if status_res.stdout.strip():
                        subprocess.run(
                            ["git", "add", "docs/adr/TRACEABILITY_MATRIX.md"],
                            cwd=str(self.root),
                            check=False,
                        )
                        subprocess.run(
                            [
                                "git",
                                "commit",
                                "-m",
                                "chore(adr): sync traceability matrix before nightly PR creation",
                            ],
                            cwd=str(self.root),
                            check=False,
                        )
                        logger.info("✅ Đã tự động commit đồng bộ Traceability Matrix.")
        except Exception as e:
            logger.warning(f"⚠️ Tự động đồng bộ Traceability Matrix gặp lỗi: {e}")

        # 1. ADR-0058 Hard Completion Lock: Verify branch before pushing
        try:
            logger.info("🛡️ [ADR-0058] Đang thực thi Hard Completion Lock (verify-patch)...")
            verify_res = subprocess.run(
                [sys.executable, "-m", "ccba_harness", "verify-patch", "--preset", "skill"],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if verify_res.returncode != 0:
                logger.error(
                    f"❌ verify-patch thất bại (exit code {verify_res.returncode}), hủy tạo PR."
                )
                return None

            verify_docs = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_docs.py",
                    ".",
                    "--src",
                    "scripts,packages",
                    "--changed",
                ],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if verify_docs.returncode != 0:
                logger.error(
                    f"❌ validate_docs thất bại (exit code {verify_docs.returncode}), hủy tạo PR."
                )
                return None

            logger.info(
                "✅ verify-patch và validate_docs thành công! Tiến hành push nhánh và mở PR."
            )
        except Exception as e:
            logger.warning(f"⚠️ Kiểm định verify-patch/validate_docs gặp lỗi: {e}")
            return None

        # 2. Push & Create PR
        try:
            diff_check = subprocess.run(
                ["git", "diff", "-w", "--exit-code", f"{self.target_ref}...HEAD"],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                check=False,
            )
            if diff_check.returncode == 0:
                logger.warning(
                    "⚠️ Nhánh không có thay đổi ngữ nghĩa nào ngoài khoảng trắng. Hủy tạo PR."
                )
                return None
            if diff_check.returncode not in (0, 1):
                logger.warning(
                    f"⚠️ Lỗi kiểm tra git diff đối chiếu {self.target_ref} (mã {diff_check.returncode}): {diff_check.stderr.strip()}"
                )

            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=str(self.root),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            logger.info(f"🚀 Đã push nhánh {branch_name} lên remote.")

            cmd = [
                "gh",
                "pr",
                "create",
                "--head",
                branch_name,
                "--title",
                f"auto-tune: nightly skill optimization {branch_name}",
                "--body",
                report_body,
                "--label",
                "needs-triage",
            ]
            res = subprocess.run(
                cmd,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if res.returncode == 0:
                pr_url = res.stdout.strip()
                logger.info(f"🎉 Đã mở Pull Request: {pr_url}")
                return pr_url

            err_msg = res.stderr.strip() or f"exit code {res.returncode}"
            logger.warning(f"⚠️ gh pr create thất bại (exit {res.returncode}): {err_msg}")

            # Fallback: Retry without --label in case label fails or does not exist
            if "--label" in cmd:
                logger.info("🔄 Thử tạo lại PR không kèm nhãn (--label)...")
                cmd_no_label = [
                    arg
                    for i, arg in enumerate(cmd)
                    if arg != "--label" and (i == 0 or cmd[i - 1] != "--label")
                ]
                retry_res = subprocess.run(
                    cmd_no_label,
                    cwd=str(self.root),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if retry_res.returncode == 0:
                    pr_url = retry_res.stdout.strip()
                    logger.info(f"🎉 Đã mở Pull Request thành công (fallback không nhãn): {pr_url}")
                    return pr_url
                retry_err = retry_res.stderr.strip() or f"exit code {retry_res.returncode}"
                logger.error(
                    f"❌ Fallback gh pr create thất bại (exit {retry_res.returncode}): {retry_err}"
                )
        except Exception as e:
            logger.warning(f"⚠️ Không thể mở PR qua GitHub CLI: {e}")
        return None


__all__ = [
    "find_project_root",
    "send_telegram_alert",
    "SkillEvolutionSummary",
    "NightlyDaemonReport",
    "WeightedPriorityQueue",
    "NightlyTunerDaemon",
]
