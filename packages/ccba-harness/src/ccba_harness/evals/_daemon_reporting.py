"""_daemon_reporting.py - Data models, priority queue, Markdown/Plateau reporting, and Git PR mixin for NightlyTunerDaemon."""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .archetypes import resolve_domain_dataset
from .tuner import (
    _UNSET,
    DEFAULT_MUTATION_STRATEGIES_PATH,
    RatchetReport,
)

logger = logging.getLogger("ccba.eval.nightly")


def get_mutation_strategies_hash(path: Path | None = None) -> str:
    """Computes SHA-256 hash of mutation_strategies.yaml (Sprint 3 / ADR-0058)."""
    target_path = Path(path) if path else DEFAULT_MUTATION_STRATEGIES_PATH
    if not target_path.is_file():
        return ""
    return hashlib.sha256(target_path.read_bytes()).hexdigest()


def get_last_applied_strategies_hash(root: Path) -> str:
    """Reads the last recorded mutation strategies hash from reports directory."""
    hash_file = root / ".md" / "knowledge" / "reports" / ".eval_strategies_hash"
    if hash_file.is_file():
        try:
            return hash_file.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""


def save_applied_strategies_hash(root: Path, current_hash: str) -> None:
    """Persists the current mutation strategies hash to reports directory."""
    if not current_hash:
        return
    hash_file = root / ".md" / "knowledge" / "reports" / ".eval_strategies_hash"
    try:
        hash_file.parent.mkdir(parents=True, exist_ok=True)
        hash_file.write_text(current_hash.strip(), encoding="utf-8")
    except Exception as e:
        logger.warning(f"⚠️ Could not save strategies hash: {e}")


def find_project_root(start_dir: Path | None = None) -> Path:
    """Discovers project root by walking upward until .git or .agents is found."""
    current = (start_dir or Path.cwd()).resolve()
    for p in [current, *current.parents]:
        if (p / ".git").exists() or (p / ".agents").exists():
            return p
    pkg_ancestor = Path(__file__).resolve().parents[5]
    if (pkg_ancestor / ".git").exists() or (pkg_ancestor / ".agents").exists():
        return pkg_ancestor
    return current


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

        def priority_key(item: dict[str, Any]) -> tuple[int, int, datetime.date, int, float]:
            is_exhausted = (
                1
                if (
                    item.get("is_exhausted")
                    and item.get("strat_hash_unchanged")
                    and not item.get("has_unapplied_signals")
                    and not item.get("needs_ledger_seed")
                )
                else 0
            )
            in_cooldown = (
                1
                if (
                    item.get("in_cooldown")
                    and not item.get("has_unapplied_signals")
                    and not item.get("needs_ledger_seed")
                )
                else 0
            )
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
            return (is_exhausted, in_cooldown, scanned_date, tier, score)

        return sorted(skills_data, key=priority_key)


FLAGSHIP_REDTEAM_DATASET_OVERRIDES: dict[str, str] = {
    "ccba-legal-intel": "eval_legal_intel_redteam.json",
    "ccba-ai-qc-pccc-audit": "eval_pccc_audit_redteam.json",
    "bigbim-classification": "eval_bigbim_classification_redteam.json",
    "ccba-ai-qc": "eval_pccc_audit_redteam.json",
}


def _resolve_daemon_env_int(val: Any, env_key: str, default: int) -> int:
    """Resolves integer daemon config from explicit value, environment variable, or default."""
    if val is not _UNSET:
        return val
    env_v = os.getenv(env_key)
    if env_v:
        try:
            return int(env_v.replace(",", "").replace("_", ""))
        except ValueError:
            return default
    return default


class _DaemonReportingAndGitMixin:
    """Mixin encapsulating report parsing, Markdown/Plateau rendering, and Git branch/PR operations."""

    root: Path
    target_ref: str

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

    def _report_sort_key(self, f: Path) -> tuple[datetime.date, float]:
        """Computes sort key (report_date, mtime) for a nightly tuner report file."""
        try:
            fn_match = re.search(r"nightly_tuner_report_(\d{4})[-_]?(\d{2})[-_]?(\d{2})", f.name)
            if fn_match:
                d = datetime.date(
                    int(fn_match.group(1)), int(fn_match.group(2)), int(fn_match.group(3))
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

    def _ingest_report_metrics_file(
        self,
        r_file: Path,
        cutoff_date: datetime.date,
        pattern_7: re.Pattern[str],
        pattern_3: re.Pattern[str],
        scores: dict[str, float],
        cooldown_skills: set[str],
        evaluated_recent: set[str],
        last_scanned_dates: dict[str, datetime.date],
    ) -> None:
        """Parses a single report markdown file into scores, cooldowns, and last scanned dates."""
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
            if "SKIPPED_COOLDOWN" in status_str:
                continue
            if r_date is not None and s_name not in last_scanned_dates:
                last_scanned_dates[s_name] = r_date
            if is_within_cooldown and is_real_llm and s_name not in evaluated_recent:
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

    def _load_historical_metrics(
        self, cooldown_days: int = 3
    ) -> tuple[dict[str, float], set[str], dict[str, datetime.date]]:
        """Loads baseline scores across all available reports and identifies cooldown skills."""
        reports_dir = self.root / ".md" / "knowledge" / "reports"
        if not reports_dir.exists():
            return {}, set(), {}

        report_files = sorted(
            reports_dir.glob("nightly_tuner_report_*.md"),
            key=self._report_sort_key,
            reverse=True,
        )
        scores: dict[str, float] = {}
        cooldown_skills: set[str] = set()
        evaluated_recent: set[str] = set()
        last_scanned_dates: dict[str, datetime.date] = {}
        cutoff_date = datetime.date.today() - datetime.timedelta(days=cooldown_days)

        pattern_7 = re.compile(
            r"\|\s*`?([a-zA-Z0-9_-]+)`?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?\s*\|\s*`?[^|]*`?\s*\|\s*`?(\d+)`?\s*\|\s*[^|]*\|\s*([^|\r\n]+)\|"
        )
        pattern_3 = re.compile(
            r"\|\s*`?([a-zA-Z0-9_-]+)`?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?\s*\|\s*\*?\*?([0-9.]+)%\*?\*?"
        )

        for r_file in report_files:
            try:
                self._ingest_report_metrics_file(
                    r_file,
                    cutoff_date,
                    pattern_7,
                    pattern_3,
                    scores,
                    cooldown_skills,
                    evaluated_recent,
                    last_scanned_dates,
                )
            except Exception as e:
                logger.debug(f"Failed parsing report file {r_file}: {e}")
        return scores, cooldown_skills, last_scanned_dates

    def _load_recent_baseline_scores(self) -> dict[str, float]:
        """Loads historical scores from recent reports to calibrate priority queue ranking."""
        scores, _, _ = self._load_historical_metrics()
        return scores

    @staticmethod
    def _format_evolution_row(s: SkillEvolutionSummary) -> str:
        """Formats a single skill evolution result row for the Markdown matrix table."""
        delta_str = f"+{s.score_delta:.1f}%" if s.score_delta > 0 else f"{s.score_delta:.1f}%"
        if s.status.startswith("ERROR"):
            badge = f"❌ {s.status}"
        elif s.score_delta > 0:
            badge = "🟢 IMPROVED"
        elif s.final_score == 100.0:
            badge = "⭐ 100% PERFECT"
        elif s.halt_reason and s.score_delta <= 0:
            badge = f"⚠️ {s.status}"
        else:
            badge = "⚪ UNCHANGED"
        token_str = f"{s.total_tokens:,}" if s.total_tokens > 0 else "-"
        return (
            f"| `{s.skill_name}` | {s.baseline_score:.1f}% | **{s.final_score:.1f}%** "
            f"| `{delta_str}` | {s.commits_kept} | `{token_str}` | {badge} |"
        )

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
                "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
                *[self._format_evolution_row(s) for s in report.results],
                "",
                "---",
                "",
                "### 🛡️ Rào Chắn An Toàn (Safety Hard Floor Invariant)",
            ]
        )
        if any(s.status.startswith("ERROR") for s in report.results):
            lines.append(
                "- ⚠️ **Lưu ý Thất bại:** Một hoặc nhiều kỹ năng gặp lỗi ngoại lệ nghiêm trọng và không thể hoàn tất chu trình tối ưu."
            )
        else:
            lines.extend(
                [
                    "- ✅ **Zero-Regression:** 100% các đột biến làm giảm điểm hoặc dính Điểm Liệt đã được `git checkout` hoàn tác sạch.",
                    "- ✅ **Hard Floor Compliance:** Tuyệt đối không chấp thuận các điều luật bãi bỏ hoặc lỗi kỹ thuật nghiêm trọng.",
                ]
            )
        lines.extend(
            [
                "",
                "---",
                "*Báo cáo được tạo tự động bởi CCBA Nightly Auto-Tuner Daemon trên Server Spark.*",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _build_plateau_brief_sections(
        skill_name: str, target_file: Path, now_str: str, dataset_file: str, result: RatchetReport
    ) -> str:
        """Renders ADR-0052 5-section Markdown content for a stagnant skill plateau brief."""
        delta = result.final_score - result.initial_score
        delta_str = f"+{delta:.1f}%" if delta > 0 else f"{delta:.1f}%"
        tot_tok = f"{result.total_tokens:,}" if result.total_tokens is not None else "0"
        p_tok = f"{result.prompt_tokens:,}" if result.prompt_tokens is not None else "0"
        c_tok = f"{result.completion_tokens:,}" if result.completion_tokens is not None else "0"
        ho_score = f"{result.holdout_score:.1f}%" if result.holdout_score is not None else "N/A"
        ho_size = str(result.holdout_size) if result.holdout_size is not None else "0"
        tier_str = f"Tier {result.slicing_tier}" if result.slicing_tier else "N/A"
        lines = [
            f"# ⚠️ CCBA Plateau Escalation Brief (ADR-0052): {skill_name}\n",
            f"> **Mã hồ sơ:** `PLATEAU-{skill_name.upper()}`",
            f"> **Thời gian ghi nhận:** `{now_str}`",
            f"> **Tệp nguồn:** [`{target_file.name}`]({target_file})",
            "> **Trạng thái:** `STAGNANT_PLATEAU` (Cần can thiệp suy luận sâu)\n\n---\n",
            "## 1. Failure Manifest",
            f"- **Baseline Score:** `{result.initial_score:.1f}%`",
            f"- **Peak Score Achieved:** `{result.final_score:.1f}%` (Chênh lệch: `{delta_str}`)",
            f"- **Vòng lặp đã thử nghiệm:** `{result.total_iterations}` vòng (Ngừng bởi: `{result.halt_reason or 'PATIENCE_EXHAUSTED'}`)",
            f"- **Số lần Rollback:** `{result.reverted_trials}` lần",
            f"- **Tổng Token tiêu tốn:** `{tot_tok}` tokens (Prompt: `{p_tok}` | Completion: `{c_tok}`)\n",
            "## 2. Tested Hypotheses & Ineffective Mutations",
            "- Đã áp dụng các đột biến tri thức (Surgical Section Patching) theo tập chiến lược của archetype nhưng điểm số không vượt qua trần baseline.",
            "- Toàn bộ các thử nghiệm đột biến đều bị hoàn tác (REVERT) hoặc dừng sớm do:",
            "  + Dính Điểm Liệt (Critical Failures / Vi phạm điều kiện nghiêm ngặt).",
            "  + Không cải thiện điểm số vượt qua ngưỡng holdout split.",
            "  + Đột biến trùng lặp hoặc cạn kiệt chiến lược định sẵn (`HALT_NO_FURTHER_STRATEGIES`).\n",
            "## 3. Deep Seams & Archetype Involved",
            f"- **Evaluation Dataset:** `{dataset_file}`",
            f"- **Slicing Tier:** `{tier_str}` (Holdout Score: `{ho_score}`, Holdout Size: `{ho_size}`)",
            "- **Deep Seams liên quan:** Prompt Instruction Rules trong `SKILL.md`, Bộ quy chuẩn Scorer regex/deterministic parsing, và Test Case Fixtures.\n",
            "## 4. Error Logs & Failure Excerpts\n```text",
            f"Halt Reason: {result.halt_reason or 'EARLY_STOPPING_PATIENCE_EXHAUSTED'}\nTotal Iterations: {result.total_iterations}",
            f"Reverted Trials: {result.reverted_trials}/{result.total_iterations}\nFinal Holdout Score: {ho_score}\n```\n",
            "## 5. Actionable Recommendation (/boost Protocol)",
            "Kỹ năng này đã cạn kiệt ngân sách kiên nhẫn (`patience`) trên mô hình cục bộ mà không vượt qua được điểm nghẽn.",
            "Theo quy chuẩn **ADR-0052 (Boost Deep Reasoning Protocol)**, kỹ sư CCBA hãy chủ động can thiệp ban ngày:\n",
            f"1. **Khởi chạy Interactive Boost trên Worktree cô lập:**\n   ```bash\n   bash scripts/eval/run_boost_worktree.sh {skill_name}\n   ```",
            f"2. **Khởi chạy Daemon với mô hình suy luận cao cấp:**\n   ```bash\n   python scripts/eval/nightly_tuner_daemon.py --skill {skill_name} --use-real-llm --model gemini-3.8-flash-high --max-iter 3\n   ```",
            "3. **Kích hoạt qua Antigravity Chat:** Gõ `/boost` kèm nội dung brief này để rà soát Instruction Conflicts giữa `SKILL.md` và Scorer.\n",
        ]
        return "\n".join(lines)

    def _save_plateau_brief(
        self, skill_name: str, target_file: Path, result: RatchetReport
    ) -> Path:
        """Saves a Deep Problem Brief for stagnant skills under ADR-0052 Section 3.B for daytime human review."""
        escalations_dir = self.root / ".md" / "knowledge" / "escalations"
        escalations_dir.mkdir(parents=True, exist_ok=True)
        brief_file = escalations_dir / f"{skill_name}_plateau.md"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dataset_file = self._resolve_dataset_file(skill_name)
        content = self._build_plateau_brief_sections(
            skill_name, target_file, now_str, dataset_file, result
        )
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

    def _try_delete_stale_branch(
        self, branch: str, base_ref: str, cutoff_date: datetime.date
    ) -> bool:
        """Deletes a single stale branch locally and remotely if older than cutoff_date and empty."""
        match = re.search(r"(?:nightly|auto-refactor)-(\d{8})", branch)
        if not match:
            return False
        try:
            b_date = datetime.datetime.strptime(match.group(1), "%Y%m%d").date()
            if b_date >= cutoff_date:
                return False
            diff_res = subprocess.run(
                ["git", "cherry", base_ref, branch],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if diff_res.returncode == 0 and not diff_res.stdout.strip():
                subprocess.run(
                    ["git", "branch", "-D", branch],
                    cwd=str(self.root),
                    capture_output=True,
                    check=False,
                )
                logger.info(f"🧹 Đã dọn dẹp nhánh rác cục bộ: {branch}")
                try:
                    subprocess.run(
                        ["git", "push", "origin", "--delete", branch],
                        cwd=str(self.root),
                        capture_output=True,
                        check=False,
                    )
                    logger.info(f"🧹 Đã dọn dẹp nhánh rác remote: {branch}")
                    return True
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Bỏ qua nhánh {branch}: {e}")
        return False

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
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).date()

            base_ref = self.target_ref
            check_ref = subprocess.run(
                ["git", "rev-parse", "--verify", self.target_ref],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
            if check_ref.returncode != 0:
                base_ref = "main"

            return sum(
                1 for b in branches if self._try_delete_stale_branch(b, base_ref, cutoff_date)
            )
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
            if not self._get_main_repo_root():
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

    def _sync_traceability_matrix_before_pr(self) -> None:
        """Synchronizes and commits TRACEABILITY_MATRIX.md if modified prior to PR creation."""
        try:
            sync_script = self.root / "scripts" / "sync_hub_adr_matrix.py"
            if not sync_script.exists():
                return
            logger.info("🔄 Đang kiểm tra và tự động đồng bộ Traceability Matrix...")
            subprocess.run(
                [sys.executable, str(sync_script), "--hub-dir", str(self.root)],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
            matrix_file = self.root / "docs" / "adr" / "TRACEABILITY_MATRIX.md"
            if not matrix_file.exists():
                return
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

    def _verify_branch_before_pr(self) -> bool:
        """Runs ADR-0058 Hard Completion Lock (verify-patch and validate_docs) before pushing PR."""
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
                return False

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
                return False

            logger.info(
                "✅ verify-patch và validate_docs thành công! Tiến hành push nhánh và mở PR."
            )
            return True
        except Exception as e:
            logger.warning(f"⚠️ Kiểm định verify-patch/validate_docs gặp lỗi: {e}")
            return False

    def _submit_gh_pr_with_fallback(self, branch_name: str, report_body: str) -> str | None:
        """Invokes gh pr create and retries without --label if label assignment fails."""
        base_cmd = [
            "gh",
            "pr",
            "create",
            "--head",
            branch_name,
            "--title",
            f"auto-tune: nightly skill optimization {branch_name}",
            "--body",
            report_body,
        ]
        cmd = [*base_cmd, "--label", "needs-triage"]
        run_kw: dict[str, Any] = {
            "cwd": str(self.root),
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }
        res = subprocess.run(cmd, **run_kw)
        if res.returncode == 0:
            pr_url = res.stdout.strip()
            logger.info(f"🎉 Đã mở Pull Request: {pr_url}")
            return pr_url

        err_msg = res.stderr.strip() or f"exit code {res.returncode}"
        logger.warning(f"⚠️ gh pr create thất bại (exit {res.returncode}): {err_msg}")
        if "--label" in cmd:
            logger.info("🔄 Thử tạo lại PR không kèm nhãn (--label)...")
            retry_res = subprocess.run(base_cmd, **run_kw)
            if retry_res.returncode == 0:
                pr_url = retry_res.stdout.strip()
                logger.info(f"🎉 Đã mở Pull Request thành công (fallback không nhãn): {pr_url}")
                return pr_url
            retry_err = retry_res.stderr.strip() or f"exit code {retry_res.returncode}"
            logger.error(
                f"❌ Fallback gh pr create thất bại (exit {retry_res.returncode}): {retry_err}"
            )
        return None

    def _create_pull_request(self, branch_name: str, report_body: str) -> str | None:
        """Pushes branch and creates a GitHub Pull Request using GitHub CLI (gh) if available."""
        self._sync_traceability_matrix_before_pr()
        if not self._verify_branch_before_pr():
            return None

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
            return self._submit_gh_pr_with_fallback(branch_name, report_body)
        except Exception as e:
            logger.warning(f"⚠️ Không thể mở PR qua GitHub CLI: {e}")
        return None
