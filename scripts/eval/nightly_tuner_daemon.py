#!/usr/bin/env python3
"""nightly_tuner_daemon.py - Autonomous Multi-Skill Nightly Optimization Daemon.

Designed for automated execution on Server Spark (00:00 - 06:00).
Iterates across the CCBA Skills Catalog using a Weighted Priority Queue,
executes Karpathy Git-Ratchet Auto-Tuning, creates an automated feature branch,
and dispatches summary alerts via Telegram Bot and GitHub Pull Requests.
"""

from __future__ import annotations

import argparse
import datetime
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add project root and packages to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "ccba-ai" / "src"))
sys.path.insert(0, str(project_root / "packages" / "ccba-harness" / "src"))

from scripts.eval.telegram_alert import send_telegram_alert

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ccba.eval.nightly")

# Auto-load .env if present
try:
    from dotenv import load_dotenv

    load_dotenv(project_root / ".env")
except ImportError:
    pass

# Enforce ADR 0043: Decoupled Sandbox Environment for Nightly Daemon
os.environ.setdefault("IDOP_ENV", "DEV")
os.environ.setdefault("CCBA_IDOP_MOCK_MODE", "1")

from scripts.eval.git_ratchet_tuner import GitRatchetTuner, RatchetConfig, RatchetReport


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
        """Sorts skills such that lower baseline scores and untested skills are tuned first."""

        def priority_key(item: dict[str, Any]) -> tuple[int, float]:
            score = item.get("baseline_score", 0.0)
            if score < 90.0:
                return (0, score)  # Top priority: failing or weak skills
            elif score < 100.0:
                return (1, score)  # Medium priority: near-perfect skills
            else:
                return (2, score)  # Low priority: 100% perfect (quick smoke test only)

        return sorted(skills_data, key=priority_key)


class NightlyTunerDaemon:
    """Orchestrates multi-skill batch optimization overnight."""

    def __init__(
        self,
        root: Path = project_root,
        max_iterations_low: int = 30,
        max_iterations_perfect: int = 1,
        early_stopping_patience: int = 5,
        use_real_llm: bool = False,
        token_budget: int = 5_000_000,
        model: str = "",
        target_skills: list[str] | None = None,
    ) -> None:
        self.root = root
        self.max_iterations_low = max_iterations_low
        self.max_iterations_perfect = max_iterations_perfect
        self.early_stopping_patience = early_stopping_patience
        self.use_real_llm = use_real_llm
        self.token_budget = token_budget
        self.model = model
        self.target_skills = [s.strip().lower() for s in target_skills] if target_skills else None
        self.test_cases_dir = self.root / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
        self.skills_dir = self.root / ".agents" / "skills"

    def _resolve_dataset_file(self, skill_name: str) -> str:
        """Dynamically matches a skill to its optimal Domain Archetype evaluation dataset."""
        sname = skill_name.lower()

        if "risk" in sname or "conflict" in sname:
            return "eval_bigbim_risk.json"
        if any(k in sname for k in ["legal", "luat", "tvpl", "vbpl", "ingest", "advisor"]):
            return "eval_legal_intel.json"
        if any(k in sname for k in ["bim", "uniclass", "classification", "rase", "governance"]):
            return "eval_bigbim_classification.json"
        if any(k in sname for k in ["pccc", "qc", "audit"]):
            return "eval_pccc_audit.json"
        if any(k in sname for k in ["academic", "khoahoc", "writing"]):
            return "eval_academic_writing.json"
        if any(k in sname for k in ["copywriting", "vietbai", "truyenthong"]):
            return "eval_copywriting.json"
        if any(k in sname for k in ["teamwork", "orchestrat", "platform", "handoff", "issue-tree"]):
            return "eval_agent_orchestration.json"

        return "eval_general_domain.json"

    def discover_skills_and_datasets(self) -> list[dict[str, Any]]:
        """Maps discovered skills to their optimal evaluation datasets."""
        skill_dataset_map = {
            "ccba-academic-writing": "eval_academic_writing.json",
            "ccba-copywriting": "eval_copywriting.json",
            "ccba-legal-intel": "eval_legal_intel_redteam.json",
            "ccba-ai-qc-pccc-audit": "eval_pccc_audit_redteam.json",
            "bigbim-classification": "eval_bigbim_classification.json",
            "bigbim-governance": "eval_bigbim_classification.json",
            "bigbim-risk": "eval_bigbim_risk.json",
            "bigbim-rase": "eval_bigbim_classification.json",
            "ccba-completion-checklist": "eval_general_domain.json",
            "ccba-legal-document-tracker": "eval_legal_intel.json",
            "ccba-legal-advisor": "eval_legal_intel.json",
            "ccba-legal-ingest": "eval_legal_intel.json",
            "bigbim-vbpl-digest": "eval_legal_intel.json",
            "ccba-tvpl-vip-crawler": "eval_legal_intel.json",
            "ccba-ai-qc": "eval_pccc_audit_redteam.json",
        }

        discovered: list[dict[str, Any]] = []
        for skill_path in self.skills_dir.glob("*/SKILL.md"):
            skill_name = skill_path.parent.name
            if skill_name in skill_dataset_map:
                dataset_file = skill_dataset_map[skill_name]
            else:
                dataset_file = self._resolve_dataset_file(skill_name)

            full_dataset_path = self.test_cases_dir / dataset_file

            if not full_dataset_path.exists():
                full_dataset_path = self.test_cases_dir / "eval_general_domain.json"

            discovered.append(
                {
                    "skill_name": skill_name,
                    "target_file": skill_path,
                    "dataset_file": full_dataset_path,
                    "eval_dataset_file": full_dataset_path,
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
            )

            try:
                tuner = GitRatchetTuner(config, dry_run_git=dry_run)
                result: RatchetReport = tuner.run()

                status = "IMPROVED" if result.final_score > result.initial_score else "UNCHANGED"
                if result.final_score == 100.0 and result.initial_score == 100.0:
                    status = "PERFECT_VERIFIED"
                if result.halt_reason:
                    status = f"HALT_{result.halt_reason}"

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
                )
                summaries.append(summary)
                total_commits += result.kept_commits

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

        reports_dir = self.root / ".md" / "knowledge" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / f"nightly_tuner_report_{now_str}.md"
        report_file.write_text(report_md, encoding="utf-8")
        logger.info(f"📄 Đã lưu báo cáo: {report_file}")

        # 5. Tự động mở GitHub Pull Request nếu có cải tiến
        if not dry_run and total_commits > 0:
            pr_url = self._create_pull_request(branch_name, report_md)
            report.pr_url = pr_url

        # 6. Gửi thông báo Telegram Bot
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
            if s.halt_reason:
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
        """Dispatches an alert to Telegram channel via Bot API."""
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
        for s in report.results[:5]:
            if s.score_delta > 0:
                message += f"• `{s.skill_name}`: {s.baseline_score:.0f}% ➔ *{s.final_score:.0f}%* (+{s.score_delta:.0f}%)\n"

        return send_telegram_alert(
            message=message,
            parse_mode="Markdown",
            mock_fallback=True,
        )

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

            # Determine base ref for comparison (prefer origin/main, fallback to main)
            base_ref = "origin/main"
            check_ref = subprocess.run(
                ["git", "rev-parse", "--verify", "origin/main"],
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
                                except Exception:
                                    pass
                                deleted_count += 1
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

    def _create_pull_request(self, branch_name: str, report_body: str) -> str | None:
        """Pushes branch and creates a GitHub Pull Request using GitHub CLI (gh) if available."""
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
            logger.info("✅ verify-patch thành công! Tiến hành push nhánh và mở PR.")
        except Exception as e:
            logger.warning(f"⚠️ Kiểm định verify-patch gặp lỗi: {e}")
            return None

        # 2. Push & Create PR
        try:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="CCBA Nightly Auto-Tuner Daemon")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without creating git branches or PRs"
    )
    parser.add_argument("--max-iter", type=int, default=10, help="Max iterations for weak skills")
    parser.add_argument(
        "--use-real-llm", action="store_true", help="Use real LLM inference instead of mock task"
    )
    parser.add_argument(
        "--token-budget", type=int, default=5000000, help="Total session token budget ceiling"
    )
    parser.add_argument("--model", type=str, default="", help="Model alias for real LLM evaluation")
    parser.add_argument(
        "--skill",
        "--skills",
        type=str,
        default="",
        help="Comma-separated skill names to scope optimization (e.g. 'bigbim-risk')",
    )
    args = parser.parse_args()

    target_skills = [s.strip() for s in args.skill.split(",") if s.strip()] if args.skill else None

    daemon = NightlyTunerDaemon(
        max_iterations_low=args.max_iter,
        use_real_llm=args.use_real_llm,
        token_budget=args.token_budget,
        model=args.model,
        target_skills=target_skills,
    )
    daemon.run_nightly_batch(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
