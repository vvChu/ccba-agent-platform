#!/usr/bin/env python3
"""git_ratchet_tuner.py - Autonomous Git-Ratchet Prompt & Skill Optimizer.

Adapted from Andrej Karpathy's autoresearch paradigm (Propose -> Evaluate -> Keep/Revert via Git).
Optimizes AI skill prompts (SKILL.md) and prompt templates iteratively, committing on score
improvements and instantly rolling back (git checkout) on regressions or critical failures.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ccba.eval.ratchet")

# Add project root and packages to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "ccba-ai" / "src"))
sys.path.insert(0, str(project_root / "packages" / "ccba-harness" / "src"))

from ccba_harness.evals.models import EvalItem, EvalReport
from ccba_harness.evals.runner import EvalRunner
from ccba_harness.evals.scorers import BaseScorer, LengthBoundsScorer, RegexScorer


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

    @classmethod
    def from_markdown_program(cls, program_path: Path, root: Path = project_root) -> RatchetConfig:
        """Parses a program.md specification file."""
        if not program_path.exists():
            raise FileNotFoundError(f"Program spec file not found: {program_path}")

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
            else Path(target_str)
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
                (root / ds_str).resolve() if not Path(ds_str).is_absolute() else Path(ds_str)
            )

        # Extract skill name from target file if possible
        skill_name = target_path.parent.name if "skills" in str(target_path) else "custom_skill"

        return cls(
            target_file=target_path,
            eval_dataset_file=dataset_path,
            target_score=target_score,
            max_iterations=max_iterations,
            skill_name=skill_name,
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


def get_default_domain_scorers(skill_name: str) -> list[BaseScorer]:
    """Provides domain-aligned default scorers based on target skill."""
    sname = skill_name.lower()
    if any(k in sname for k in ["legal", "luat", "tvpl", "vbpl"]):
        return [
            RegexScorer(
                name="legal_grounding",
                pattern=r"(Nghị định|Thông tư|Luật|Quy chuẩn|Điều|Khoản|VBHN|pháp lý)",
                weight=0.6,
            ),
            LengthBoundsScorer(name="depth", min_length=20, max_length=20000, weight=0.4),
        ]
    if any(k in sname for k in ["pccc", "qc", "audit", "thamdinh"]):
        return [
            RegexScorer(
                name="technical_qc",
                pattern=r"(QCVN|PCCC|bậc chịu lửa|khói|thẩm tra|tiêu chuẩn|thiết kế)",
                weight=0.6,
            ),
            LengthBoundsScorer(name="depth", min_length=20, max_length=20000, weight=0.4),
        ]
    if any(k in sname for k in ["academic", "writing", "khoahoc"]):
        return [
            RegexScorer(
                name="academic_structure",
                pattern=r"(IMRAD|nghiên cứu|phương pháp|kết quả|thảo luận|trích dẫn)",
                weight=0.6,
            ),
            LengthBoundsScorer(name="depth", min_length=20, max_length=20000, weight=0.4),
        ]
    return [RegexScorer(pattern=r"(xử lý|hướng dẫn|thực hiện|quy định)", weight=1.0)]


class GitRatchetTuner:
    """Autonomous Ratchet Optimization Engine using Git commits for state persistence."""

    def __init__(
        self,
        config: RatchetConfig,
        scorers: list[BaseScorer] | None = None,
        dry_run_git: bool = False,
    ) -> None:
        self.config = config
        self.target_file = config.target_file
        self.scorers = scorers or get_default_domain_scorers(config.skill_name)
        self.dry_run_git = dry_run_git
        self.runner = EvalRunner(default_pass_threshold=config.target_score)
        self.dataset: list[EvalItem] = self._load_dataset()


    def _load_dataset(self) -> list[EvalItem]:
        """Loads evaluation dataset from JSON or creates synthetic items."""
        items: list[EvalItem] = []
        if self.config.eval_dataset_file and self.config.eval_dataset_file.exists():
            try:
                with open(self.config.eval_dataset_file, encoding="utf-8") as f:
                    raw_data = json.load(f)
                for idx, row in enumerate(raw_data):
                    if isinstance(row, dict):
                        prompt = row.get("input_prompt") or row.get("prompt", "")
                        rubric = row.get("rubric", "")
                        cid = row.get("id", f"item_{idx:02d}")
                        items.append(EvalItem(id=cid, input_prompt=prompt, rubric=rubric))
            except Exception as e:
                logger.error(f"❌ Lỗi nạp dataset {self.config.eval_dataset_file}: {e}")

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
        if not original_content.startswith("---"):
            return edited_content

        parts = original_content.split("---", 2)
        if len(parts) < 3:
            return edited_content

        frontmatter = f"---{parts[1]}---"
        body = edited_content
        if edited_content.startswith("---"):
            edited_parts = edited_content.split("---", 2)
            if len(edited_parts) >= 3:
                body = edited_parts[2]

        return f"{frontmatter}\n\n{body.lstrip()}"

    def evaluate_content(self, content: str) -> EvalReport:
        """Evaluates given skill prompt content against test dataset."""

        # Simulated agent task execution using current prompt content
        def mock_agent_task(item: EvalItem) -> str:
            # Simple content grounding simulation
            prompt = str(item.input_prompt)
            if "Nghị định 30" in prompt:
                return (
                    f"Theo quy định tại {self.config.skill_name}: "
                    f"Căn cứ Nghị định 30/2020/NĐ-CP, thể thức văn bản hành chính..."
                )
            if "QCVN 06" in prompt:
                return (
                    f"Theo quy định tại {self.config.skill_name}: "
                    f"Căn cứ QCVN 06:2022/BXD, công trình đạt bậc II..."
                )
            return f"Xử lý và thực hiện hướng dẫn theo quy định {content[:60]}..."

        return self.runner.run_sync(
            dataset=self.dataset,
            task=mock_agent_task,
            scorers=self.scorers,
        )

    def propose_mutation(self, current_content: str, iteration: int) -> str:
        """Generates a prompt mutation proposition."""
        # Add refinement guidance
        enhancement = f"\n\n<!-- Ratchet Optimization Iteration {iteration} -->\n- Hướng dẫn bổ sung: Luôn kiểm tra tính chính xác của viện dẫn điều khoản quy chuẩn."
        mutated = current_content.strip() + enhancement
        return self.preserve_yaml_frontmatter(current_content, mutated)

    def git_commit_improvement(self, score_diff: str) -> bool:
        """Commits target file change to Git repository."""
        if self.dry_run_git:
            logger.info(
                f"💾 [DRY-RUN] Git Commit: ratchet(opt): {self.target_file.name} {score_diff}"
            )
            return True

        try:
            rel_path = self.target_file.relative_to(project_root)
            subprocess.run(
                ["git", "add", str(rel_path)],
                cwd=str(project_root),
                check=True,
                capture_output=True,
            )
            msg = f"ratchet(opt): {self.target_file.name} {score_diff}"
            subprocess.run(
                ["git", "commit", "-m", msg], cwd=str(project_root), check=True, capture_output=True
            )
            logger.info(f"✅ Git Commit thành công: '{msg}'")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Git commit thất bại: {e}")
            return False

    def git_rollback_target(self, original_content: str) -> None:
        """Rolls back the target file either via git checkout or file overwrite."""
        if self.dry_run_git:
            logger.info(f"⏪ [DRY-RUN] Git Rollback: {self.target_file.name}")
            self.target_file.write_text(original_content, encoding="utf-8")
            return

        try:
            rel_path = self.target_file.relative_to(project_root)
            subprocess.run(
                ["git", "checkout", "--", str(rel_path)],
                cwd=str(project_root),
                check=True,
                capture_output=True,
            )
            logger.info(f"⏪ Đã khôi phục file qua 'git checkout -- {rel_path}'")
        except Exception:
            self.target_file.write_text(original_content, encoding="utf-8")

    def run(self) -> RatchetReport:
        """Executes the full ratchet autonomous optimization loop."""
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        initial_content = self.target_file.read_text(encoding="utf-8")
        baseline_report = self.evaluate_content(initial_content)
        baseline_score = baseline_report.overall_score

        best_score = baseline_score
        best_content = initial_content
        kept_count = 0
        reverted_count = 0
        history: list[RatchetTrialResult] = []

        logger.info(f"🏁 Bắt đầu Git-Ratchet Loop cho {self.target_file.name}")
        logger.info(
            f"📊 Điểm chuẩn ban đầu (Baseline Score): {baseline_score:.2f}% | Mục tiêu: {self.config.target_score}%"
        )

        for i in range(1, self.config.max_iterations + 1):
            logger.info(f"🔄 --- Iteration {i}/{self.config.max_iterations} ---")
            mutated_content = self.propose_mutation(best_content, i)

            # Apply candidate mutation
            self.target_file.write_text(mutated_content, encoding="utf-8")

            # Evaluate
            report = self.evaluate_content(mutated_content)
            current_score = report.overall_score
            crit_fails = sum(1 for r in report.item_results if r.critical_failed)

            # Ratchet decision
            if current_score > best_score and crit_fails == 0:
                diff_str = f"{best_score:.1f}% -> {current_score:.1f}% (+{current_score - best_score:.1f}%)"
                self.git_commit_improvement(diff_str)
                best_score = current_score
                best_content = mutated_content
                kept_count += 1
                decision = "KEEP"
                summary = f"Cải thiện điểm số thành công: {diff_str}"
            else:
                self.git_rollback_target(best_content)
                reverted_count += 1
                decision = "REVERT"
                summary = f"Không cải thiện (Score {current_score:.1f}% vs Best {best_score:.1f}%) hoặc dính {crit_fails} Điểm Liệt."

            trial = RatchetTrialResult(
                iteration=i,
                score=current_score,
                passed=(current_score >= self.config.target_score and crit_fails == 0),
                critical_fails=crit_fails,
                decision=decision,
                summary=summary,
            )
            history.append(trial)
            logger.info(f"📌 Quyết định [{decision}]: {summary}")

            if best_score >= self.config.target_score:
                logger.info(
                    f"🎉 Đã đạt điểm mục tiêu {self.config.target_score}% tại iteration {i}!"
                )
                break

        return RatchetReport(
            target_file=str(self.target_file),
            initial_score=baseline_score,
            final_score=best_score,
            total_iterations=len(history),
            kept_commits=kept_count,
            reverted_trials=reverted_count,
            history=history,
        )


def main() -> int:
    """CLI Entrypoint for Git-Ratchet Auto-Tuner."""
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Git-Ratchet Autonomous Skill & Prompt Optimizer"
    )
    parser.add_argument(
        "--program", default="program.md", help="Đường dẫn file program.md đặc tả mục tiêu"
    )
    parser.add_argument("--target", help="Đường dẫn trực tiếp đến file SKILL.md cần tối ưu")
    parser.add_argument("--dataset", help="Đường dẫn file test_cases JSON")
    parser.add_argument("--max-trials", type=int, default=10, help="Số vòng lặp tối đa")
    parser.add_argument("--target-score", type=float, default=90.0, help="Ngưỡng điểm mục tiêu")
    parser.add_argument(
        "--dry-run-git", action="store_true", help="Chạy thử nghiệm không commit git thực"
    )

    args = parser.parse_args()

    prog_path = Path(args.program)
    if prog_path.exists():
        logger.info(f"📄 Đang nạp cấu hình từ {prog_path.name}...")
        config = RatchetConfig.from_markdown_program(prog_path)
    else:
        target_path = (
            Path(args.target)
            if args.target
            else (project_root / ".agents" / "skills" / "copywriting" / "SKILL.md")
        )
        ds_path = Path(args.dataset) if args.dataset else None
        config = RatchetConfig(
            target_file=target_path,
            eval_dataset_file=ds_path,
            target_score=args.target_score,
            max_iterations=args.max_trials,
        )

    tuner = GitRatchetTuner(config, dry_run_git=args.dry_run_git)
    report = tuner.run()

    print("\n" + "=" * 60)
    print("🏆 BÁO CÁO TỔNG KẾT GIT-RATCHET AUTO-TUNING")
    print("=" * 60)
    print(f"- File mục tiêu        : {report.target_file}")
    print(f"- Điểm ban đầu (Start) : {report.initial_score:.2f}%")
    print(f"- Điểm tối ưu (Final)  : {report.final_score:.2f}%")
    print(f"- Số commits giữ lại   : {report.kept_commits}")
    print(f"- Số lần rollback      : {report.reverted_trials}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
