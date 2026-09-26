#!/usr/bin/env python3
"""nightly_tuner_daemon.py - Autonomous Multi-Skill Nightly Optimization Daemon.

Thin CLI facade delegating to ccba_harness.evals.daemon (ADR-0023, ADR-0035, ADR-0057).
Designed for automated execution on Server Spark (00:00 - 06:00).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add project root and packages to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "ccba-ai" / "src"))
sys.path.insert(0, str(project_root / "packages" / "ccba-harness" / "src"))

# Auto-load .env if present
try:
    from dotenv import load_dotenv

    load_dotenv(project_root / ".env")
except ImportError:
    pass

# Enforce ADR 0043: Decoupled Sandbox Environment for Nightly Daemon
os.environ.setdefault("IDOP_ENV", "DEV")
os.environ.setdefault("CCBA_IDOP_MOCK_MODE", "1")

from ccba_harness.evals.daemon import (
    NightlyDaemonReport,
    NightlyTunerDaemon,
    SkillEvolutionSummary,
    WeightedPriorityQueue,
    send_telegram_alert,
)

__all__ = [
    "NightlyDaemonReport",
    "NightlyTunerDaemon",
    "SkillEvolutionSummary",
    "WeightedPriorityQueue",
    "main",
]


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description="CCBA Nightly Auto-Tuner Daemon")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without creating git branches or PRs"
    )
    parser.add_argument("--max-iter", type=int, default=10, help="Max iterations for weak skills")
    parser.add_argument(
        "--use-real-llm", action="store_true", help="Use real LLM inference instead of mock task"
    )
    parser.add_argument(
        "--token-budget", type=int, default=10000000, help="Total session token budget ceiling"
    )
    parser.add_argument(
        "--per-skill-mutation-budget",
        type=int,
        default=None,
        help="Per-skill token budget ceiling for mutations (default: 250,000 or CCBA_TUNER_PER_SKILL_MUTATION_BUDGET)",
    )
    parser.add_argument(
        "--hard-max-tokens-per-skill",
        type=int,
        default=None,
        help="Absolute hard token ceiling per skill (default: 500,000 or CCBA_TUNER_HARD_MAX_PER_SKILL)",
    )
    parser.add_argument("--model", type=str, default="", help="Model alias for real LLM evaluation")
    parser.add_argument(
        "--skill",
        "--skills",
        type=str,
        default="",
        help="Comma-separated skill names to scope optimization (e.g. 'bigbim-risk')",
    )
    parser.add_argument(
        "--ref",
        type=str,
        default="origin/main",
        help="Git target ref for baseline comparison (default: origin/main)",
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Disable Telegram notifications (useful for sub-runners like run_boost_worktree.sh)",
    )
    parser.add_argument(
        "--skip-cooldown",
        action="store_true",
        help="Skip skills that are currently in cooldown (tuned recently without progress)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Concurrency limit for async batching evaluations (default: 5 or CCBA_TUNER_CONCURRENCY)",
    )
    args = parser.parse_args()

    target_skills = [s.strip() for s in args.skill.split(",") if s.strip()] if args.skill else None

    daemon_kwargs: dict[str, Any] = {
        "root": project_root,
        "max_iterations_low": args.max_iter,
        "use_real_llm": args.use_real_llm,
        "token_budget": args.token_budget,
        "model": args.model,
        "target_skills": target_skills,
        "alert_emitter": send_telegram_alert,
        "target_ref": args.ref,
        "no_telegram": args.no_telegram,
        "skip_cooldown": args.skip_cooldown,
    }
    if args.concurrency is not None:
        daemon_kwargs["concurrency"] = args.concurrency
    if args.per_skill_mutation_budget is not None:
        daemon_kwargs["per_skill_mutation_budget"] = args.per_skill_mutation_budget
    if args.hard_max_tokens_per_skill is not None:
        daemon_kwargs["hard_max_tokens_per_skill"] = args.hard_max_tokens_per_skill

    daemon = NightlyTunerDaemon(**daemon_kwargs)
    daemon.run_nightly_batch(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
