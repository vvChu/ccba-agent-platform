#!/usr/bin/env python3
"""scripts/peer_bridge_watcher.py - Event-driven Peer Agent Bridge Watcher (ADR-0007 / Issue #458).

Coordinates bidirectional state, delta detection via SHA-256 caching, front-matter parsing,
and automated gate triggering between Antigravity and Grok.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, NamedTuple

try:
    from ccba_harness.peer import (
        PeerPromptEnvelope,
        PeerVerdictBlock,
        parse_envelope_from_md,
        parse_verdict_from_md,
    )
except ImportError:
    try:
        from scripts.peer_protocol import (
            PeerPromptEnvelope,
            PeerVerdictBlock,
            parse_envelope_from_md,
            parse_verdict_from_md,
        )
    except ImportError:
        from peer_protocol import (
            PeerPromptEnvelope,
            PeerVerdictBlock,
            parse_envelope_from_md,
            parse_verdict_from_md,
        )

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
PEER_EXCHANGE_DIR = WORKSPACE_DIR / ".md" / "peer_exchange"
CACHE_FILE = PEER_EXCHANGE_DIR / ".bridge_cache.json"
STATUS_FILE = PEER_EXCHANGE_DIR / "status.json"
SUMMARY_FILE = PEER_EXCHANGE_DIR / "grok_live_summary.md"
HANDSHAKE_FILE = PEER_EXCHANGE_DIR / "PEER_HANDSHAKE.md"


class FileChange(NamedTuple):
    path: Path
    role: str
    sha256: str
    envelope: PeerPromptEnvelope | None = None
    verdict: PeerVerdictBlock | None = None


def atomic_write_text(target: Path, content: str) -> None:
    """Writes text content to target file atomically using a temporary file (Grok C2)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target.with_suffix(f"{target.suffix}.tmp_{os.getpid()}_{time.time_ns()}")
    try:
        temp_file.write_text(content, encoding="utf-8")
        temp_file.replace(target)
    except Exception:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise


def safe_read_and_hash(path: Path, max_retries: int = 3) -> tuple[str | None, str | None]:
    """Safely reads file content and computes SHA-256 with retry against partial writes (Grok C2)."""
    for attempt in range(max_retries):
        try:
            content = path.read_text(encoding="utf-8")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return content, digest
        except (OSError, UnicodeDecodeError):
            if attempt < max_retries - 1:
                time.sleep(0.05)
    return None, None


def classify_file_role(path: Path) -> str:
    """Classifies the role of a peer exchange file based on its naming convention."""
    name = path.name
    if name in (
        "grok_live_summary.md",
        "status.json",
        "PEER_HANDSHAKE.md",
        "README.md",
    ) or name.startswith("."):
        return "AUXILIARY"
    if name.startswith("grok_request_antigravity_"):
        return "GROK_REQUEST"
    if name.startswith("antigravity_response_"):
        return "ANTIGRAVITY_RESPONSE"
    if name.startswith("prompt_grok_") or name.startswith("prompt_"):
        return "PROMPT_TO_GROK"
    if name.startswith("grok_implementation_") or name.startswith("grok_implement_"):
        return "GROK_IMPLEMENTATION"
    if name.startswith("grok_"):
        return "GROK_RESPONSE"
    return "AUXILIARY"


def load_cache() -> dict[str, str]:
    """Loads SHA-256 hash cache from disk."""
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_cache(cache: dict[str, str]) -> None:
    """Saves SHA-256 hash cache to disk atomically."""
    atomic_write_text(CACHE_FILE, json.dumps(cache, indent=2))


def scan_peer_exchange(
    cache: dict[str, str],
) -> tuple[list[FileChange], dict[str, str], dict[str, Any]]:
    """Scans peer_exchange directory, detects delta changes, and extracts active metadata."""
    if not PEER_EXCHANGE_DIR.exists():
        return [], cache, {}

    new_cache = dict(cache)
    changes: list[FileChange] = []
    registry: dict[str, dict[str, Any]] = {}

    for entry in sorted(os.scandir(PEER_EXCHANGE_DIR), key=lambda e: e.name):
        if not entry.is_file() or not entry.name.endswith(".md"):
            continue
        path = Path(entry.path)
        role = classify_file_role(path)
        if role == "AUXILIARY":
            continue

        content, digest = safe_read_and_hash(path)
        if not content or not digest:
            continue

        prev_hash = cache.get(entry.name)
        envelope = parse_envelope_from_md(content)
        verdict = parse_verdict_from_md(content)

        registry[entry.name] = {
            "role": role,
            "path": path,
            "mtime": entry.stat().st_mtime,
            "envelope": envelope,
            "verdict": verdict,
            "sha256": digest,
        }

        if prev_hash != digest:
            changes.append(
                FileChange(path=path, role=role, sha256=digest, envelope=envelope, verdict=verdict)
            )
            new_cache[entry.name] = digest

    return changes, new_cache, registry


def compute_pending_queues(registry: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Matches request_ids to identify unanswered prompts for Antigravity and Grok."""
    answered_ids: set[str] = set()

    for item in registry.values():
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]:
            answered_ids.add(item["verdict"].request_id)
        elif item["role"] == "ANTIGRAVITY_RESPONSE" and item["verdict"]:
            answered_ids.add(item["verdict"].request_id)

    pending_grok: list[str] = []
    pending_antigravity: list[str] = []

    for name, item in registry.items():
        if item["role"] == "PROMPT_TO_GROK" and item["envelope"]:
            if item["envelope"].request_id not in answered_ids:
                pending_grok.append(name)
        elif item["role"] == "GROK_REQUEST" and item["envelope"]:
            if item["envelope"].request_id not in answered_ids:
                pending_antigravity.append(name)

    return pending_antigravity, pending_grok


def _build_latest_verdict(registry: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Extracts the most recent Grok verdict details from registry."""
    latest_grok_resp = [
        item
        for item in registry.values()
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]
    ]
    if not latest_grok_resp:
        return None
    latest_grok_resp.sort(key=lambda x: x["mtime"], reverse=True)
    top = latest_grok_resp[0]
    v = top["verdict"]
    return {
        "request_id": v.request_id,
        "verdict": v.verdict,
        "blocking_conditions": len([c for c in v.conditions if c.blocking]),
        "output_path": top["path"].name,
        "summary": v.summary,
    }


def update_status_json(
    registry: dict[str, dict[str, Any]], pending_anti: list[str], pending_grok: list[str]
) -> None:
    """Updates status.json with latest state and verdicts."""
    now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    latest_verdict = _build_latest_verdict(registry)

    status_data = {
        "timestamp": now_iso,
        "peers": {
            "antigravity": {
                "name": "Antigravity (Pair Architect & Builder)",
                "status": "waiting_for_grok" if pending_grok else "idle",
                "pending_requests": len(pending_anti),
                "latest_request": pending_grok[-1] if pending_grok else None,
            },
            "grok": {
                "name": "Grok 4.7 xhigh (Auditor & Gatekeeper)",
                "status": "in_progress" if pending_grok else "idle",
                "pending_requests": len(pending_grok),
                "latest_verdict": latest_verdict,
            },
        },
        "exchange_stats": {
            "total_prompts": len([i for i in registry.values() if i["role"] == "PROMPT_TO_GROK"]),
            "total_responses": len(
                [
                    i
                    for i in registry.values()
                    if i["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION")
                ]
            ),
            "pending_antigravity": pending_anti,
            "pending_grok": pending_grok,
        },
    }
    atomic_write_text(STATUS_FILE, json.dumps(status_data, indent=2, ensure_ascii=False))


def update_live_summary(
    registry: dict[str, dict[str, Any]], pending_anti: list[str], pending_grok: list[str]
) -> None:
    """Renders a concise, lightweight summary (< 5 KB) to grok_live_summary.md."""
    now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    recent_responses = [
        item
        for item in registry.values()
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]
    ]
    recent_responses.sort(key=lambda x: x["mtime"], reverse=True)

    summary_lines = [
        "# ⚡ Grok & Antigravity Live Peer Summary\n",
        f"> **Thời điểm cập nhật**: `{now_iso}` | **Cơ chế**: Delta SHA-256 Bridge (ADR-0007)\n\n",
        "## 1. Trạng Thái Vận Hành\n",
        f"- **Antigravity**: `{'waiting_for_grok' if pending_grok else 'idle'}` (Đang chờ Grok: {len(pending_grok)} requests)",
        f"- **Grok**: `{'in_progress' if pending_grok else 'idle'}` (Đang chờ Antigravity: {len(pending_anti)} requests)\n\n",
        "## 2. Hàng Đợi Đang Chờ (Pending Queue)\n",
    ]

    if pending_grok:
        summary_lines.append("### ⏳ Grok cần xử lý:")
        for p in pending_grok[:5]:
            summary_lines.append(f"- `{p}`")
    else:
        summary_lines.append("### ✅ Grok: Không có yêu cầu tồn đọng.")

    if pending_anti:
        summary_lines.append("\n### ⏳ Antigravity cần xử lý:")
        for p in pending_anti[:5]:
            summary_lines.append(f"- `{p}`")

    summary_lines.append("\n## 3. Phán Quyết Gần Nhất (Recent Verdicts)\n")
    summary_lines.append("| Tệp Phản Hồi | Phán Quyết (Verdict) | Điều Kiện | Tóm Tắt |")
    summary_lines.append("|---|:---:|:---:|---|")

    for item in recent_responses[:8]:
        v = item["verdict"]
        c_count = len(v.conditions)
        summary_lines.append(
            f"| `{item['path'].name}` | **`{v.verdict}`** | {c_count} | {v.summary[:50]}... |"
        )

    content = "\n".join(summary_lines) + "\n"
    atomic_write_text(SUMMARY_FILE, content)


def run_cycle(auto_gate: bool = False) -> list[FileChange]:
    """Executes a single observation and synchronization cycle."""
    cache = load_cache()
    changes, new_cache, registry = scan_peer_exchange(cache)

    if changes or not STATUS_FILE.exists() or not SUMMARY_FILE.exists():
        pending_anti, pending_grok = compute_pending_queues(registry)
        update_status_json(registry, pending_anti, pending_grok)
        update_live_summary(registry, pending_anti, pending_grok)
        save_cache(new_cache)

        for change in changes:
            print(f"[{change.role}] Detected change in: {change.path.name}")
            if auto_gate and change.role == "GROK_IMPLEMENTATION":
                print(f"⚡ Auto-gate triggered for {change.path.name}...")
                gate_script = WORKSPACE_DIR / "scripts" / "peer_implementation_gate.py"
                if gate_script.exists():
                    subprocess.run(
                        [sys.executable, str(gate_script), "--output-verdict"], check=False
                    )

    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Peer Agent Bridge Watcher (Delta SHA-256).")
    parser.add_argument(
        "--once", action="store_true", help="Run a single delta sync cycle and exit."
    )
    parser.add_argument(
        "--watch", action="store_true", help="Run continuously watching for changes."
    )
    parser.add_argument(
        "--interval", type=int, default=5, help="Polling interval in seconds (default: 5)."
    )
    parser.add_argument(
        "--auto-gate",
        action="store_true",
        help="Trigger peer_implementation_gate on new implementation.",
    )
    args = parser.parse_args()

    if args.once or not args.watch:
        changes = run_cycle(auto_gate=args.auto_gate)
        print(f"[OK] Bridge sync completed. Detected {len(changes)} change(s).")
        return 0

    print(
        f"🚀 Starting Peer Bridge Watcher (interval={args.interval}s, auto_gate={args.auto_gate})... Press Ctrl+C to stop."
    )
    try:
        while True:
            run_cycle(auto_gate=args.auto_gate)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nWatcher stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
