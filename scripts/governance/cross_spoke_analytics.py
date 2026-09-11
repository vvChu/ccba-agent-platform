#!/usr/bin/env python3
"""cross_spoke_analytics.py - Cross-Spoke Enterprise Fleet Telemetry & Analytics CLI.

Provides command-line utilities for Lead Orchestrators and Hub administrators to monitor,
audit, and visualize token consumption and costs across all registered Spokes (ADR-0030, ADR-0046, ADR-0058).

Usage:
  python scripts/governance/cross_spoke_analytics.py scan [--json] [--out report.md]
  python scripts/governance/cross_spoke_analytics.py dashboard [--out dashboard.html] [--title "Enterprise Fleet"]
  python scripts/governance/cross_spoke_analytics.py export-spoke-summary [--target <spoke_path>] [--out summary.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent

# Ensure packages/ccba-harness/src is in sys.path
try:
    from ccba_harness.fleet import (
        aggregate_fleet_telemetry,
        render_fleet_dashboard,
        scan_spoke_telemetry,
    )
except ImportError:
    sys.path.insert(0, str(HUB_ROOT / "packages" / "ccba-harness" / "src"))
    from ccba_harness.fleet import (
        aggregate_fleet_telemetry,
        render_fleet_dashboard,
        scan_spoke_telemetry,
    )


def main() -> int:
    """CLI Entry point for cross_spoke_analytics."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Cross-Spoke Enterprise Fleet Telemetry & Analytics Engine (ADR-0046, ADR-0058)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: scan
    scan_parser = subparsers.add_parser(
        "scan", help="Scan and summarize token consumption across all registered Spokes"
    )
    scan_parser.add_argument(
        "--json", action="store_true", help="Output fleet metrics as raw JSON dictionary"
    )
    scan_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="File path to save the Markdown or JSON report",
    )

    # Subcommand: dashboard
    dash_parser = subparsers.add_parser(
        "dashboard", help="Generate interactive HTML Cross-Spoke Fleet Dashboard"
    )
    dash_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="File path to save the HTML dashboard (default: .md/reports/cross_spoke_fleet_dashboard.html)",
    )
    dash_parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom dashboard title",
    )

    # Subcommand: export-spoke-summary
    export_parser = subparsers.add_parser(
        "export-spoke-summary",
        help="Export a sanitized telemetry summary for a single Spoke (ADR-0046)",
    )
    export_parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Path to the Spoke project directory (default: current directory)",
    )
    export_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Target file path (default: <spoke>/.md/data/telemetry_summary.json)",
    )

    args = parser.parse_args()

    if args.command == "dashboard":
        try:
            out_file, report = render_fleet_dashboard(
                output_path=args.out,
                title=args.title,
                hub_root=HUB_ROOT,
            )
            print(f"[Success] Generated Cross-Spoke Fleet Dashboard at: {out_file.resolve()}")
            print(f"  Fleet Hub: {report.hub_name}")
            print(f"  Spokes: {report.total_spokes} ({report.online_spokes} Online)")
            print(f"  Total Fleet Tokens: {report.total_fleet_tokens:,}")
            print(f"  Total Fleet Cost: ${report.total_fleet_cost_usd:.4f} USD")
            return 0
        except Exception as err:
            print(f"[Error] Failed to render fleet dashboard: {err}", file=sys.stderr)
            return 1

    elif args.command == "scan":
        try:
            report = aggregate_fleet_telemetry(hub_root=HUB_ROOT)
            out_content = (
                json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
                if args.json
                else report.to_markdown()
            )
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(out_content, encoding="utf-8")
                print(f"[Success] Saved fleet telemetry report to {args.out}")
            else:
                print(out_content)
            return 0
        except Exception as err:
            print(f"[Error] Failed to scan fleet telemetry: {err}", file=sys.stderr)
            return 1

    elif args.command == "export-spoke-summary":
        try:
            spoke_dir = args.target.resolve()
            spoke_dict = {
                "name": spoke_dir.name,
                "path": str(spoke_dir),
                "project_type": "Auto-detected",
            }
            summary = scan_spoke_telemetry(spoke_dict)
            out_path = args.out or (spoke_dir / ".md" / "data" / "telemetry_summary.json")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(summary.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"[Success] Exported sanitized spoke telemetry summary to: {out_path.resolve()}")
            print(f"  Project: {summary.project_name}")
            print(f"  Total Tokens: {summary.total_tokens:,}")
            print(f"  Estimated Cost: ${summary.total_cost_usd:.4f} USD")
            return 0
        except Exception as err:
            print(f"[Error] Failed to export spoke summary: {err}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
