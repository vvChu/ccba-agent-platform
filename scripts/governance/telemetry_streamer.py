#!/usr/bin/env python3
"""telemetry_streamer.py - Platform CLI for Real-Time Telemetry Streaming to Server Spark.

Usage:
  python scripts/governance/telemetry_streamer.py ping [--endpoint http://100.83.192.30:8090/telemetry/events]
  python scripts/governance/telemetry_streamer.py stream <conversation_id_or_log> [--dry-run] [--json]
  python scripts/governance/telemetry_streamer.py flush [--endpoint http://100.83.192.30:8090/telemetry/events]
  python scripts/governance/telemetry_streamer.py status
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

from ccba_harness.streamer import (
    DEFAULT_BUFFER_PATH,
    DEFAULT_SPARK_TELEMETRY_URL,
    OfflineBufferManager,
    StreamingConfig,
    TelemetryStreamingBridge,
)


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point for telemetry streaming governance."""
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
        prog="telemetry_streamer.py",
        description="CCBA Real-Time Telemetry Streaming Bridge to Server Spark (:8090).",
    )
    sub = parser.add_subparsers(dest="action", help="Action to perform")

    # Action: ping
    p_ping = sub.add_parser("ping", help="Ping Spark telemetry endpoint to test connectivity")
    p_ping.add_argument(
        "--endpoint", type=str, default=DEFAULT_SPARK_TELEMETRY_URL, help="Endpoint URL"
    )

    # Action: stream
    p_stream = sub.add_parser("stream", help="Stream transcript events to Spark or offline buffer")
    p_stream.add_argument("target", help="Conversation ID or transcript.jsonl path")
    p_stream.add_argument(
        "--endpoint", type=str, default=DEFAULT_SPARK_TELEMETRY_URL, help="Endpoint URL"
    )
    p_stream.add_argument(
        "--buffer-file", type=str, default=str(DEFAULT_BUFFER_PATH), help="Offline buffer file path"
    )
    p_stream.add_argument("--dry-run", action="store_true", help="Simulate streaming locally")
    p_stream.add_argument("--json", action="store_true", help="Output raw JSON summary")

    # Action: flush
    p_flush = sub.add_parser("flush", help="Flush offline buffer to Server Spark")
    p_flush.add_argument(
        "--endpoint", type=str, default=DEFAULT_SPARK_TELEMETRY_URL, help="Endpoint URL"
    )
    p_flush.add_argument(
        "--buffer-file", type=str, default=str(DEFAULT_BUFFER_PATH), help="Offline buffer file path"
    )

    # Action: status
    p_status = sub.add_parser("status", help="Inspect local buffer count and connectivity status")
    p_status.add_argument(
        "--endpoint", type=str, default=DEFAULT_SPARK_TELEMETRY_URL, help="Endpoint URL"
    )
    p_status.add_argument(
        "--buffer-file", type=str, default=str(DEFAULT_BUFFER_PATH), help="Offline buffer file path"
    )

    args = parser.parse_args(argv)

    if not args.action:
        parser.print_help()
        return 0

    cfg = StreamingConfig(
        endpoint_url=getattr(args, "endpoint", DEFAULT_SPARK_TELEMETRY_URL),
        buffer_path=Path(getattr(args, "buffer_file", DEFAULT_BUFFER_PATH)),
        dry_run=getattr(args, "dry_run", False),
    )
    bridge = TelemetryStreamingBridge(config=cfg)

    if args.action == "ping":
        online = bridge.test_connection()
        status_text = (
            "ONLINE (Reachable)" if online else "OFFLINE (Unreachable - will buffer locally)"
        )
        print(f"Server Spark Telemetry Endpoint ({cfg.endpoint_url}): {status_text}")
        return 0 if online else 1

    if args.action == "flush":
        flushed = bridge.flush_buffer()
        print(f"[Streaming Bridge] Flushed {flushed} buffered event(s) to Spark.")
        return 0

    if args.action == "status":
        online = bridge.test_connection()
        buf_mgr = OfflineBufferManager(cfg.buffer_path)
        pending = buf_mgr.count_buffered()
        print("📊 Telemetry Streaming Status:")
        print(f"  Server Spark Endpoint : {cfg.endpoint_url}")
        print(f"  Connection Status     : {'ONLINE' if online else 'OFFLINE (Graceful Buffering)'}")
        print(f"  Offline Buffer File   : {cfg.buffer_path}")
        print(f"  Pending Offline Events: {pending}")
        return 0

    if args.action == "stream":
        report = bridge.stream_transcript_file(args.target, dry_run=args.dry_run)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            return 0 if report.status != "FAILED" else 1

        print("📡 Real-Time Telemetry Streaming Bridge:")
        print(f"  Target: {args.target}")
        print(f"  Endpoint: {report.endpoint}")
        print(f"  Status: {report.status}")
        print(f"  Events Emitted: {report.events_emitted}")
        print(f"  Events Delivered: {report.events_delivered}")
        print(f"  Events Buffered Offline: {report.events_buffered}")
        if report.errors:
            for err in report.errors:
                print(f"  [Error] {err}", file=sys.stderr)
            return 1
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
