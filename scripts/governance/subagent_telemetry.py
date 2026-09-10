#!/usr/bin/env python3
"""subagent_telemetry.py - OpenTelemetry Subagent Runtime & Token Monitoring CLI.

Provides command-line utilities for Lead Orchestrators and CI to monitor,
trace, and enforce token budgeting across AI Subagent trajectories (ADR-0030, ADR-0058).

Usage:
  python scripts/governance/subagent_telemetry.py inspect <conv_id_or_log> [--json]
  python scripts/governance/subagent_telemetry.py budget-check <conv_id_or_log> --max-tokens 100000
  python scripts/governance/subagent_telemetry.py export-otel <conv_id_or_log> [--out otel.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent

# Ensure packages/ccba-harness/src is in sys.path
try:
    from ccba_harness.dashboard import render_swarm_dashboard
    from ccba_harness.telemetry import (
        OtelSpanExporter,
        analyze_subagent_transcript,
        audit_swarm_session,
        check_subagent_budget,
    )
except ImportError:
    sys.path.insert(0, str(HUB_ROOT / "packages" / "ccba-harness" / "src"))
    from ccba_harness.dashboard import render_swarm_dashboard
    from ccba_harness.telemetry import (
        OtelSpanExporter,
        analyze_subagent_transcript,
        audit_swarm_session,
        check_subagent_budget,
    )


def main() -> int:
    """CLI Entry point for subagent_telemetry."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="OpenTelemetry Subagent Runtime & Token Monitoring Engine."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: inspect
    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect subagent execution trajectory and token consumption"
    )
    inspect_parser.add_argument(
        "target",
        type=str,
        help="Subagent conversation ID or path to transcript.jsonl",
    )
    inspect_parser.add_argument(
        "--json", action="store_true", help="Output metrics as raw JSON dictionary"
    )

    # Subcommand: budget-check
    budget_parser = subparsers.add_parser(
        "budget-check", help="Enforce token/duration budget on a subagent trajectory"
    )
    budget_parser.add_argument(
        "target",
        type=str,
        help="Subagent conversation ID or path to transcript.jsonl",
    )
    budget_parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum allowable total tokens consumed (e.g., 50000)",
    )
    budget_parser.add_argument(
        "--max-duration",
        type=float,
        default=None,
        help="Maximum allowable execution duration in seconds (e.g., 600.0)",
    )

    # Subcommand: export-otel
    otel_parser = subparsers.add_parser(
        "export-otel", help="Export trajectory to OpenTelemetry GenAI OTLP JSON trace"
    )
    otel_parser.add_argument(
        "target",
        type=str,
        help="Subagent conversation ID or path to transcript.jsonl",
    )
    otel_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="File path to save the OTLP JSON (default: stdout)",
    )

    # Subcommand: audit-swarm
    swarm_parser = subparsers.add_parser(
        "audit-swarm", help="Audit token consumption across a multi-agent swarm session"
    )
    swarm_parser.add_argument(
        "target",
        type=str,
        help="Parent conversation ID, transcript path, or directory containing subagents",
    )
    swarm_parser.add_argument(
        "--max-swarm-tokens",
        type=int,
        default=None,
        help="Maximum allowable total tokens across all subagents",
    )
    swarm_parser.add_argument(
        "--max-subagent-tokens",
        type=int,
        default=None,
        help="Maximum allowable tokens per individual subagent",
    )
    swarm_parser.add_argument(
        "--max-cost",
        type=float,
        default=None,
        help="Maximum allowable total USD cost across the swarm",
    )
    swarm_parser.add_argument(
        "--json",
        action="store_true",
        help="Output metrics as raw JSON dictionary",
    )
    swarm_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="File path to save the Markdown or JSON report",
    )

    # Subcommand: dashboard
    dash_parser = subparsers.add_parser(
        "dashboard", help="Generate interactive HTML Swarm Telemetry Dashboard"
    )
    dash_parser.add_argument(
        "target",
        type=str,
        help="Parent conversation ID, transcript path, or directory containing subagents",
    )
    dash_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="File path to save the HTML dashboard (default: .md/reports/swarm_telemetry_dashboard.html)",
    )
    dash_parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom dashboard title",
    )

    args = parser.parse_args()

    if args.command == "dashboard":
        try:
            out_file, report = render_swarm_dashboard(
                args.target,
                output_path=args.out,
                title=args.title,
            )
            print(f"[Success] Generated Swarm Telemetry Dashboard at: {out_file.resolve()}")
            print(f"  Parent Session: {report.parent_conversation_id}")
            print(f"  Subagents: {report.total_subagents}")
            print(f"  Total Tokens: {report.total_swarm_tokens:,}")
            print(f"  Estimated Cost: ${report.total_cost_usd:.4f} USD")
            return 0
        except Exception as err:
            print(
                f"[Error] Failed to render dashboard for '{args.target}': {err}",
                file=sys.stderr,
            )
            return 1

    if args.command == "audit-swarm":
        try:
            report, passed, msg = audit_swarm_session(
                args.target,
                max_swarm_tokens=args.max_swarm_tokens,
                max_subagent_tokens=args.max_subagent_tokens,
                max_total_cost_usd=args.max_cost,
            )
        except Exception as err:
            print(f"[Error] Failed to audit swarm for '{args.target}': {err}", file=sys.stderr)
            return 1

        out_content = (
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
            if args.json
            else report.to_markdown()
        )
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(out_content, encoding="utf-8")
            print(f"[Success] Saved swarm report to {args.out}")
        else:
            print(out_content)

        if not passed:
            print(f"[FAIL] Swarm budget violation: {msg}", file=sys.stderr)
            return 1
        return 0

    try:
        metrics = analyze_subagent_transcript(args.target)
    except Exception as err:
        print(f"[Error] Failed to analyze transcript for '{args.target}': {err}", file=sys.stderr)
        return 1

    if args.command == "inspect":
        if args.json:
            print(json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(metrics.to_markdown())
        return 0

    elif args.command == "budget-check":
        passed, msg = check_subagent_budget(
            metrics,
            max_tokens=args.max_tokens,
            max_duration_sec=args.max_duration,
        )
        if passed:
            print(f"[PASS] {msg}")
            print(
                f"  Consumed: {metrics.total_tokens:,} tokens in {metrics.total_duration_sec:.1f}s"
            )
            return 0
        else:
            print(f"[FAIL] Budget violation: {msg}", file=sys.stderr)
            print(
                f"  Actual: {metrics.total_tokens:,} tokens in {metrics.total_duration_sec:.1f}s",
                file=sys.stderr,
            )
            return 1

    elif args.command == "export-otel":
        otlp = OtelSpanExporter.to_otlp_json(metrics)
        payload = json.dumps(otlp, indent=2, ensure_ascii=False)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload, encoding="utf-8")
            print(f"[Success] Exported OTLP trace to {args.out}")
        else:
            print(payload)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
