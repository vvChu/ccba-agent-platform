#!/usr/bin/env python3
"""doc_refactor_daemon.py - Autonomous Document Evolution & Grounding Engine.

Thin CLI facade delegating to ccba_harness.docs.daemon (ADR-0023, ADR-0035, ADR-0057).
Designed for automated execution on Server Spark (00:00 - 06:00).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Resolve project root
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "ccba-harness" / "src"))

from ccba_harness.docs.daemon import (
    CodeGroundingEngine,
    DocAutoEvolutionEngine,
    DocEvolutionReport,
    DocHealthReport,
    GroundingCheckResult,
    PillarBalanceAuditor,
    PillarBloatInfo,
    ZeroDeletionGuard,
)

if sys.platform.startswith("win"):
    try:
        reconfig_out = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfig_out):
            reconfig_out(encoding="utf-8")
        reconfig_err = getattr(sys.stderr, "reconfigure", None)
        if callable(reconfig_err):
            reconfig_err(encoding="utf-8")
    except Exception:
        pass

__all__ = [
    "GroundingCheckResult",
    "PillarBloatInfo",
    "DocHealthReport",
    "DocEvolutionReport",
    "CodeGroundingEngine",
    "ZeroDeletionGuard",
    "PillarBalanceAuditor",
    "DocAutoEvolutionEngine",
    "main",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="CCBA Document Auto-Evolution Engine")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode without git mutations"
    )
    parser.add_argument(
        "--audit-only", action="store_true", help="Audit documents and print summary"
    )
    parser.add_argument(
        "--check-bloat", action="store_true", help="Only check for pillar over-expansion"
    )

    args = parser.parse_args()
    engine = DocAutoEvolutionEngine(root=project_root)

    if args.check_bloat or args.audit_only:
        health = engine.audit_all_documents()
        print("\n============================================================")
        print("📊 CCBA DOCUMENT HEALTH & PILLAR BALANCE AUDIT")
        print("============================================================")
        print(f"Timestamp: {health.timestamp}")
        print(
            f"Trạng thái tổng thể: {'🟢 100% HEALTHY' if health.is_healthy else '⚠️ CẦN TINH CHỈNH'}"
        )
        print("\nChi tiết các Trụ Cột:")
        for p in health.bloated_pillars:
            status_icon = "🔴" if p.is_bloated else "🟢"
            print(
                f"  {status_icon} Trụ Cột {p.pillar_index}: {p.pillar_title} ({p.pattern_count} patterns)"
            )
        print("============================================================\n")
        return

    report = engine.run_nightly_evolution(dry_run=args.dry_run)
    print(f"\n✅ Đã hoàn tất chu trình Doc-Auto-Evolution! (Dry-run={report.dry_run})\n")


if __name__ == "__main__":
    main()
