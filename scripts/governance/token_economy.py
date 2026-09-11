#!/usr/bin/env python3
"""token_economy.py - Dedicated Platform CLI for Prompt Density & Token Economy Optimization.

Usage:
  python scripts/governance/token_economy.py scan [--json]
  python scripts/governance/token_economy.py report [--out .md/reports/prompt_economy_report.md]
  python scripts/governance/token_economy.py roi <conversation_id_or_log> [--role coder]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure monorepo package is resolvable
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CCBA_HARNESS = _REPO_ROOT / "packages" / "ccba-harness" / "src"
if str(_CCBA_HARNESS) not in sys.path:
    sys.path.insert(0, str(_CCBA_HARNESS))

from ccba_harness.economy import (
    audit_token_economy,
    calculate_role_aware_roi,
    generate_prompt_pruning_report,
)
from ccba_harness.telemetry import analyze_subagent_transcript


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point for token economy governance."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(
        prog="token_economy.py",
        description="CCBA Prompt Density & Token Economy Optimization Engine.",
    )
    sub = parser.add_subparsers(dest="action", help="Action to perform")

    # Action: scan
    p_scan = sub.add_parser("scan", help="Scan and audit prompt density for all skills")
    p_scan.add_argument("--json", action="store_true", help="Output raw JSON format")
    p_scan.add_argument("--root", type=str, default=None, help="Root directory for skills")

    # Action: report
    p_rep = sub.add_parser("report", help="Generate actionable prompt pruning markdown report")
    p_rep.add_argument(
        "--out",
        type=str,
        default=".md/reports/prompt_economy_report.md",
        help="Path to save report (default: .md/reports/prompt_economy_report.md)",
    )

    # Action: roi
    p_roi = sub.add_parser("roi", help="Calculate Token ROI for an agent execution session")
    p_roi.add_argument("target", help="Conversation ID, transcript file, or directory")
    p_roi.add_argument(
        "--role", type=str, default=None, help="Override role (coder, investigator, reviewer)"
    )
    p_roi.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args(argv)

    if not args.action or args.action == "scan":
        root = Path(args.root) if getattr(args, "root", None) else _REPO_ROOT / ".agents" / "skills"
        report = audit_token_economy(skills_dir=root)
        if getattr(args, "json", False):
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(report.to_markdown())
        return 0

    elif args.action == "report":
        out_p = Path(args.out)
        if not out_p.is_absolute():
            out_p = _REPO_ROOT / out_p
        report = audit_token_economy(skills_dir=_REPO_ROOT / ".agents" / "skills")
        generate_prompt_pruning_report(report, output_path=out_p)
        print(f"[Success] Generated Prompt Pruning Report at: {out_p}")
        print(f"  Total Skills: {report.total_skills}")
        print(f"  Average PDI: {report.avg_pdi:.1f} / 100.0")
        print(f"  Bloated Skills: {report.bloated_skills_count}")
        print(f"  Potential Token Savings: ~{report.estimated_token_savings:,} tokens")
        return 0

    elif args.action == "roi":
        try:
            metrics = analyze_subagent_transcript(args.target)
            roi = calculate_role_aware_roi(metrics, role_override=args.role)
            if args.json:
                print(json.dumps(roi.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(f"# 📊 Token ROI Analysis: `{roi.conversation_id}`")
                print(f"- **Assigned Role:** {roi.role}")
                print(f"- **Prompt Tokens:** {roi.prompt_tokens:,}")
                print(f"- **Completion Tokens:** {roi.completion_tokens:,}")
                print(f"- **Productive Output Score:** {roi.productive_score:.1f}")
                print(f"- **Token ROI (Score / 100K prompt tokens):** {roi.token_roi:.2f}")
                print(f"- **Efficiency Classification:** {roi.efficiency_tier}")
                print(f"- **Notes:** {roi.summary_notes}")
            return 0
        except Exception as err:
            print(f"[Error] Failed to calculate ROI for '{args.target}': {err}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
