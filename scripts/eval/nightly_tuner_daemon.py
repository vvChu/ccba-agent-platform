#!/usr/bin/env python3
"""nightly_tuner_daemon.py - Autonomous Multi-Skill Nightly Optimization Daemon.

Thin CLI facade delegating to ccba_harness.evals.daemon (ADR-0023, ADR-0035, ADR-0057).
Designed for automated execution on Server Spark (00:00 - 06:00).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

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
        root=project_root,
        max_iterations_low=args.max_iter,
        use_real_llm=args.use_real_llm,
        token_budget=args.token_budget,
        model=args.model,
        target_skills=target_skills,
        alert_emitter=send_telegram_alert,
    )
    daemon.run_nightly_batch(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
