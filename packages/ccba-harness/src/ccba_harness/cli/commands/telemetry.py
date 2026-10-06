"""commands/telemetry.py - CLI handlers for subagent runtime telemetry and token monitoring."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path


# ccba:quarantine seam_id=cli.telemetry reason=thin_shell_refactor until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/494
def run_telemetry_cli(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for subagent runtime telemetry (`ccba-harness telemetry`)."""
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

    from ccba_harness.telemetry import (
        OtelSpanExporter,
        analyze_subagent_transcript,
        audit_swarm_session,
        check_subagent_budget,
    )

    parser = argparse.ArgumentParser(
        prog="ccba-harness telemetry",
        description="Subagent runtime telemetry and token monitoring.",
    )
    sub = parser.add_subparsers(dest="telemetry_cmd", required=True)

    # Subcommand: inspect
    p_insp = sub.add_parser("inspect", help="Inspect subagent trajectory & tokens")
    p_insp.add_argument("target", help="Conversation ID or transcript.jsonl path")
    p_insp.add_argument("--json", action="store_true", help="Output raw JSON")

    # Subcommand: budget-check
    p_bud = sub.add_parser("budget-check", help="Enforce token/duration budget")
    p_bud.add_argument("target", help="Conversation ID or transcript.jsonl path")
    p_bud.add_argument("--max-tokens", type=int, default=None, help="Maximum allowed tokens")
    p_bud.add_argument("--max-duration", type=float, default=None, help="Maximum allowed seconds")

    # Subcommand: export-otel
    p_otel = sub.add_parser("export-otel", help="Export OpenTelemetry GenAI OTLP JSON trace")
    p_otel.add_argument("target", help="Conversation ID or transcript.jsonl path")
    p_otel.add_argument("--out", type=str, default=None, help="Output file path")

    # Subcommand: audit-swarm
    p_swarm = sub.add_parser(
        "audit-swarm", help="Audit token consumption across a multi-agent swarm session"
    )
    p_swarm.add_argument("target", help="Parent conversation ID, transcript path, or directory")
    p_swarm.add_argument(
        "--max-swarm-tokens", type=int, default=None, help="Max total tokens for whole swarm"
    )
    p_swarm.add_argument(
        "--max-subagent-tokens", type=int, default=None, help="Max tokens per subagent"
    )
    p_swarm.add_argument("--max-cost", type=float, default=None, help="Max total cost in USD")
    p_swarm.add_argument("--json", action="store_true", help="Output raw JSON")
    p_swarm.add_argument("--out", type=str, default=None, help="Save markdown/json report to file")

    # Subcommand: dashboard
    p_dash = sub.add_parser("dashboard", help="Generate interactive HTML Swarm Telemetry Dashboard")
    p_dash.add_argument("target", help="Parent conversation ID, transcript path, or directory")
    p_dash.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output HTML file path (default: .md/reports/swarm_telemetry_dashboard.html)",
    )
    p_dash.add_argument("--title", type=str, default=None, help="Custom dashboard title")

    # Subcommand: fleet
    p_fleet = sub.add_parser("fleet", help="Cross-Spoke enterprise fleet telemetry & analytics")
    p_fleet.add_argument(
        "--json", action="store_true", help="Output fleet metrics as raw JSON dictionary"
    )
    p_fleet.add_argument(
        "--dashboard", action="store_true", help="Generate standalone HTML fleet dashboard"
    )
    p_fleet.add_argument(
        "--out",
        type=str,
        default=None,
        help="File path to save the HTML dashboard or JSON report",
    )
    p_fleet.add_argument("--title", type=str, default=None, help="Custom fleet dashboard title")

    # Subcommand: economy
    p_eco = sub.add_parser("economy", help="Prompt density & token economy optimization")
    p_eco.add_argument(
        "--scan-skills",
        action="store_true",
        help="Scan and score Prompt Density Index (PDI) for all skills",
    )
    p_eco.add_argument(
        "--session",
        type=str,
        default=None,
        help="Evaluate role-aware Token ROI for a subagent session",
    )
    p_eco.add_argument(
        "--role",
        type=str,
        default=None,
        help="Override role for ROI evaluation (coder, investigator, reviewer, general)",
    )
    p_eco.add_argument(
        "--prune-report",
        action="store_true",
        help="Generate actionable prompt pruning diff report",
    )
    p_eco.add_argument("--json", action="store_true", help="Output results as raw JSON")
    p_eco.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output file path (default for report: .md/reports/prompt_economy_report.md)",
    )

    # Subcommand: stream
    p_stream = sub.add_parser("stream", help="Real-time telemetry streaming bridge to Server Spark")
    p_stream.add_argument(
        "target", nargs="?", default=None, help="Conversation ID or transcript.jsonl path"
    )
    p_stream.add_argument(
        "--endpoint", type=str, default=None, help="Server Spark telemetry endpoint URL"
    )
    p_stream.add_argument("--buffer-file", type=str, default=None, help="Offline buffer file path")
    p_stream.add_argument(
        "--flush-buffer", action="store_true", help="Flush offline buffer to Spark endpoint"
    )
    p_stream.add_argument(
        "--ping", action="store_true", help="Test connectivity to Server Spark endpoint"
    )
    p_stream.add_argument(
        "--dry-run", action="store_true", help="Simulate streaming without network calls"
    )
    p_stream.add_argument("--json", action="store_true", help="Output summary as raw JSON")

    args = parser.parse_args(argv)

    if args.telemetry_cmd == "stream":
        from ccba_harness.streamer import StreamingConfig, TelemetryStreamingBridge

        cfg = StreamingConfig(dry_run=args.dry_run)
        if args.endpoint:
            cfg.endpoint_url = args.endpoint
        if args.buffer_file:
            cfg.buffer_path = Path(args.buffer_file)

        bridge = TelemetryStreamingBridge(config=cfg)

        if args.ping:
            online = bridge.test_connection()
            status_text = (
                "ONLINE (Reachable)" if online else "OFFLINE (Unreachable - will buffer locally)"
            )
            print(f"Server Spark Telemetry Endpoint ({cfg.endpoint_url}): {status_text}")
            return 0 if online else 1

        if args.flush_buffer:
            flushed = bridge.flush_buffer()
            print(f"[Streaming Bridge] Flushed {flushed} buffered event(s) to Spark.")
            return 0

        if not args.target:
            print(
                "[Error] Must provide conversation ID or transcript path, or use --ping / --flush-buffer",
                file=sys.stderr,
            )
            return 1

        stream_report = bridge.stream_transcript_file(args.target, dry_run=args.dry_run)
        if args.json:
            print(json.dumps(stream_report.to_dict(), indent=2, ensure_ascii=False))
            return 0 if stream_report.status != "FAILED" else 1

        print("📡 Real-Time Telemetry Streaming Bridge:")
        print(f"  Target: {args.target}")
        print(f"  Endpoint: {stream_report.endpoint}")
        print(f"  Status: {stream_report.status}")
        print(f"  Events Emitted: {stream_report.events_emitted}")
        print(f"  Events Delivered: {stream_report.events_delivered}")
        print(f"  Events Buffered Offline: {stream_report.events_buffered}")
        if stream_report.errors:
            for err in stream_report.errors:
                print(f"  [Error] {err}", file=sys.stderr)
            return 1
        return 0

    if args.telemetry_cmd == "economy":
        from ccba_harness.economy import (
            audit_token_economy,
            calculate_role_aware_roi,
            generate_prompt_pruning_report,
        )

        session_metrics = None
        if args.session:
            try:
                session_metrics = analyze_subagent_transcript(args.session)
            except Exception as err:
                print(f"[Warning] Could not load session '{args.session}': {err}", file=sys.stderr)

        economy_report = audit_token_economy(session_metrics=session_metrics)
        if args.session and session_metrics and args.role:
            economy_report.session_roi = calculate_role_aware_roi(
                session_metrics, role_override=args.role
            )

        if args.prune_report:
            out_file = Path(args.out) if args.out else Path(".md/reports/prompt_economy_report.md")
            generate_prompt_pruning_report(economy_report, output_path=out_file)
            print(f"[Success] Generated Prompt Pruning Report at: {out_file.resolve()}")
            print(f"  Total Skills: {economy_report.total_skills}")
            print(f"  Average PDI: {economy_report.avg_pdi:.1f} / 100.0")
            print(f"  Bloated Skills: {economy_report.bloated_skills_count}")
            print(f"  Estimated Token Savings: ~{economy_report.estimated_token_savings:,} tokens")
            return 0

        if args.json:
            payload = json.dumps(economy_report.to_dict(), indent=2, ensure_ascii=False)
            if args.out:
                Path(args.out).write_text(payload, encoding="utf-8")
                print(f"[Success] Saved JSON economy report to {args.out}")
            else:
                print(payload)
            return 0

        # Markdown output
        md_text = economy_report.to_markdown()
        if args.out:
            Path(args.out).write_text(md_text, encoding="utf-8")
            print(f"[Success] Saved economy report to {args.out}")
        else:
            print(md_text)
        return 0

    if args.telemetry_cmd == "fleet":
        from ccba_harness.fleet import aggregate_fleet_telemetry, render_fleet_dashboard

        if args.dashboard:
            try:
                out_path, fleet_report = render_fleet_dashboard(
                    output_path=Path(args.out) if args.out else None,
                    title=args.title,
                )
                print(f"[Success] Generated Cross-Spoke Fleet Dashboard at: {out_path.resolve()}")
                print(f"  Fleet Hub: {fleet_report.hub_name}")
                print(
                    f"  Spokes: {fleet_report.total_spokes} ({fleet_report.online_spokes} Online)"
                )
                print(f"  Total Fleet Tokens: {fleet_report.total_fleet_tokens:,}")
                print(f"  Total Fleet Cost: ${fleet_report.total_fleet_cost_usd:.4f} USD")
                return 0
            except Exception as err:
                print(f"[Error] Failed to render fleet dashboard: {err}", file=sys.stderr)
                return 1
        else:
            try:
                fleet_report = aggregate_fleet_telemetry()
                if args.json:
                    out_content = json.dumps(fleet_report.to_dict(), indent=2, ensure_ascii=False)
                else:
                    out_content = fleet_report.to_markdown()

                if args.out:
                    out_p = Path(args.out)
                    out_p.parent.mkdir(parents=True, exist_ok=True)
                    out_p.write_text(out_content, encoding="utf-8")
                    print(f"[Success] Saved fleet telemetry report to {out_p}")
                else:
                    print(out_content)
                return 0
            except Exception as err:
                print(f"[Error] Failed to aggregate fleet telemetry: {err}", file=sys.stderr)
                return 1

    if args.telemetry_cmd == "dashboard":
        from ccba_harness.dashboard import render_swarm_dashboard

        try:
            out_path, swarm_dash_report = render_swarm_dashboard(
                args.target,
                output_path=args.out,
                title=args.title,
            )
            print(f"[Success] Generated Swarm Telemetry Dashboard at: {out_path.resolve()}")
            print(f"  Parent Session: {swarm_dash_report.parent_conversation_id}")
            print(f"  Subagents: {swarm_dash_report.total_subagents}")
            print(f"  Total Tokens: {swarm_dash_report.total_swarm_tokens:,}")
            print(f"  Estimated Cost: ${swarm_dash_report.total_cost_usd:.4f} USD")
            return 0
        except Exception as err:
            print(
                f"[Error] Failed to render dashboard for '{args.target}': {err}",
                file=sys.stderr,
            )
            return 1

    if args.telemetry_cmd == "audit-swarm":
        try:
            swarm_audit_report, passed, msg = audit_swarm_session(
                args.target,
                max_swarm_tokens=args.max_swarm_tokens,
                max_subagent_tokens=args.max_subagent_tokens,
                max_total_cost_usd=args.max_cost,
            )
        except Exception as err:
            print(f"[Error] Failed to audit swarm for '{args.target}': {err}", file=sys.stderr)
            return 1

        out_content = (
            json.dumps(swarm_audit_report.to_dict(), indent=2, ensure_ascii=False)
            if args.json
            else swarm_audit_report.to_markdown()
        )
        if args.out:
            out_p = Path(args.out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(out_content, encoding="utf-8")
            print(f"[Success] Saved swarm report to {out_p}")
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

    if args.telemetry_cmd == "inspect":
        if args.json:
            print(json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(metrics.to_markdown())
        return 0

    elif args.telemetry_cmd == "budget-check":
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

    elif args.telemetry_cmd == "export-otel":
        otlp = OtelSpanExporter.to_otlp_json(metrics)
        payload = json.dumps(otlp, indent=2, ensure_ascii=False)
        if args.out:
            out_p = Path(args.out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(payload, encoding="utf-8")
            print(f"[Success] Exported OTLP trace to {out_p}")
        else:
            print(payload)
        return 0

    return 0
