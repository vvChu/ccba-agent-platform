#!/usr/bin/env python3
"""git_ratchet_tuner.py - Autonomous Git-Ratchet Prompt & Skill Optimizer.

Thin facade delegating to ccba_harness.evals.tuner (ADR-0023).
Optimizes AI skill prompts (SKILL.md) and prompt templates iteratively, committing on score
improvements and instantly rolling back (git checkout) on regressions or critical failures.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root and packages to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "ccba-ai" / "src"))
sys.path.insert(0, str(project_root / "packages" / "ccba-harness" / "src"))

from ccba_harness.evals.tuner import (  # noqa: E402
    GitRatchetOptimizer,
    GitRatchetTuner,
    RatchetConfig,
    RatchetReport,
    RatchetTrialResult,
    get_default_domain_scorers,
    preserve_yaml_frontmatter,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ccba.eval.ratchet")

__all__ = [
    "GitRatchetOptimizer",
    "GitRatchetTuner",
    "RatchetConfig",
    "RatchetReport",
    "RatchetTrialResult",
    "get_default_domain_scorers",
    "preserve_yaml_frontmatter",
    "main",
]


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
    parser.add_argument(
        "--full-sweep",
        action="store_true",
        help="Chạy toàn bộ các vòng lặp mà không dừng sớm khi đạt điểm mục tiêu",
    )

    args = parser.parse_args()

    prog_path = Path(args.program)
    if prog_path.exists():
        logger.info(f"📄 Đang nạp cấu hình từ {prog_path.name}...")
        config = RatchetConfig.from_markdown_program(prog_path, root=project_root)
    else:
        target_path = (
            Path(args.target)
            if args.target
            else (project_root / ".agents" / "skills" / "ccba-copywriting" / "SKILL.md")
        )
        ds_path = Path(args.dataset) if args.dataset else None
        config = RatchetConfig(
            target_file=target_path,
            eval_dataset_file=ds_path,
            target_score=args.target_score,
            max_iterations=args.max_trials,
        )

    if args.full_sweep:
        config.full_sweep = True

    tuner = GitRatchetOptimizer(config, dry_run_git=args.dry_run_git, project_root=project_root)
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
