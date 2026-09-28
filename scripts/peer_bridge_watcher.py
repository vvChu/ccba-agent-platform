#!/usr/bin/env python3
"""peer_bridge_watcher.py - Peer Agent Bridge: Antigravity <-> Grok.

Coordinates automated, non-interactive handshakes and data exchange between
Antigravity and Grok on the ccba-agent-platform workspace.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
PEER_EXCHANGE_DIR = WORKSPACE_DIR / ".md" / "peer_exchange"
GROK_BINARY = Path("/home/vvc/.local/bin/grok")
GROK_SESSIONS_DIR = Path("/home/vvc/.grok/sessions/%2Fhome%2Fvvc%2Fccba%2Fccba-agent-platform")
STATUS_FILE = PEER_EXCHANGE_DIR / "status.json"
ANTIGRAVITY_TO_GROK_FILE = PEER_EXCHANGE_DIR / "ANTIGRAVITY_TO_GROK.md"
GROK_TO_ANTIGRAVITY_FILE = PEER_EXCHANGE_DIR / "GROK_TO_ANTIGRAVITY.md"


def load_status() -> dict[str, Any]:
    """Reads peer status metadata from status.json."""
    if not STATUS_FILE.is_file():
        return {}
    try:
        with open(STATUS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def update_status(updates: dict[str, Any]) -> None:
    """Updates peer status metadata in status.json."""
    data = load_status()
    data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(data.get(k), dict):
            data[k].update(v)
        else:
            data[k] = v

    PEER_EXCHANGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_target_session_dir() -> Path | None:
    """Resolves the pinned target session directory for Grok."""
    status = load_status()
    session_id = status.get("peers", {}).get("grok", {}).get("target_session_id")
    if session_id and (GROK_SESSIONS_DIR / session_id).is_dir():
        return GROK_SESSIONS_DIR / session_id

    # Fallback to the latest modified directory
    if GROK_SESSIONS_DIR.is_dir():
        candidates = [
            d for d in GROK_SESSIONS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
        if candidates:
            candidates.sort(key=lambda d: d.stat().st_mtime, reverse=True)
            return candidates[0]
    return None


def is_session_locked(session_dir: Path) -> bool:
    """Checks whether the Grok session is actively locked by another process.

    Uses POSIX non-blocking advisory file locking (fcntl.flock) instead of
    file existence check, because empty lock files remain on disk indefinitely.
    """
    lock_file = session_dir / "chat_history.jsonl.lock"
    if not lock_file.exists():
        return False
    try:
        with open(lock_file, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f, fcntl.LOCK_UN)
            return False
    except (BlockingIOError, OSError):
        return True


def extract_latest_grok_response(session_dir: Path) -> str:
    """Extracts the latest assistant completion text from chat_history.jsonl."""
    chat_file = session_dir / "chat_history.jsonl"
    if not chat_file.is_file():
        return ""

    latest_text = ""
    try:
        with open(chat_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # Detect assistant messages
                    role = record.get("role")
                    content = record.get("content", "")
                    if role in ("assistant", "model", None) and content:
                        latest_text = content
                except Exception:
                    continue
    except Exception as e:
        return f"Error reading chat history: {e}"

    return latest_text


def trigger_grok_headless(
    prompt_file: Path,
    session_uuid: str | None = None,
    timeout_s: int = 180,
    max_retries: int = 2,
) -> tuple[int, str]:
    """Invokes Grok CLI headlessly using non-interactive flags."""
    if not GROK_BINARY.is_file():
        return 127, f"Grok binary not found at: {GROK_BINARY}"

    if not prompt_file.is_file():
        return 1, f"Prompt file not found: {prompt_file}"

    target_uuid = session_uuid
    if not target_uuid:
        target_dir = get_target_session_dir()
        if target_dir:
            target_uuid = target_dir.name

    cmd = [
        str(GROK_BINARY),
        "--output-format",
        "plain",
        "--always-approve",
        "--no-alt-screen",
        "--prompt-file",
        str(prompt_file),
    ]
    if target_uuid:
        cmd.extend(["--resume", target_uuid])

    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            update_status(
                {
                    "peers": {
                        "grok": {"status": f"running_attempt_{attempt}"},
                        "antigravity": {"status": "waiting_grok"},
                    }
                }
            )
            result = subprocess.run(
                cmd,
                cwd=WORKSPACE_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=timeout_s,
                check=False,
            )
            if result.returncode == 0:
                output_content = result.stdout.strip()
                GROK_TO_ANTIGRAVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
                GROK_TO_ANTIGRAVITY_FILE.write_text(output_content, encoding="utf-8")
                update_status(
                    {
                        "peers": {
                            "grok": {"status": "idle_response_ready"},
                            "antigravity": {"status": "processing_grok_response"},
                        }
                    }
                )
                return 0, output_content

            last_error = result.stderr.strip() or result.stdout.strip()
            time.sleep(2)
        except subprocess.TimeoutExpired:
            last_error = f"Execution timed out after {timeout_s}s"
            time.sleep(2)
        except Exception as ex:
            last_error = str(ex)

    update_status(
        {
            "peers": {
                "grok": {"status": f"error: {last_error}"},
                "antigravity": {"status": "error_handling"},
            }
        }
    )
    return 1, f"Failed after {max_retries} attempts. Last error: {last_error}"


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Peer Bridge Watcher: Antigravity <-> Grok automated coordination."
    )
    parser.add_argument("--check-status", action="store_true", help="Print current peer status.")
    parser.add_argument("--check-lock", action="store_true", help="Check session file lock status.")
    parser.add_argument(
        "--sync", action="store_true", help="Extract latest Grok message to exchange file."
    )
    parser.add_argument(
        "--trigger-grok",
        action="store_true",
        help="Trigger Grok headless execution with ANTIGRAVITY_TO_GROK.md prompt file.",
    )
    args = parser.parse_args()

    session_dir = get_target_session_dir()

    if args.check_lock:
        if not session_dir:
            print("❌ No target session directory found.")
            return 1
        locked = is_session_locked(session_dir)
        print(f"Session Dir: {session_dir}")
        print(f"Lock Status: {'🔒 LOCKED' if locked else '🟢 UNLOCKED (Ready)'}")
        return 0

    if args.sync:
        if not session_dir:
            print("❌ No target session directory found.")
            return 1
        resp = extract_latest_grok_response(session_dir)
        if resp:
            GROK_TO_ANTIGRAVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
            GROK_TO_ANTIGRAVITY_FILE.write_text(resp, encoding="utf-8")
            print(
                f"✅ Extracted latest Grok response ({len(resp)} chars) to {GROK_TO_ANTIGRAVITY_FILE}"
            )
            return 0
        print("⚠️ No assistant response found in session.")
        return 1

    if args.trigger_grok:
        retcode, out = trigger_grok_headless(ANTIGRAVITY_TO_GROK_FILE)
        if retcode == 0:
            print(f"✅ Grok headless completed successfully ({len(out)} chars output).")
            return 0
        print(f"❌ Grok headless failed: {out}")
        return retcode

    # Default: --check-status
    status = load_status()
    print("=================================================================")
    print("      PEER BRIDGE STATUS: ANTIGRAVITY <-> GROK                   ")
    print("=================================================================")
    print(f"Workspace Dir       : {WORKSPACE_DIR}")
    print(f"Session Dir Target  : {session_dir}")
    print(f"Grok Binary Exists  : {GROK_BINARY.is_file()}")
    if session_dir:
        print(
            f"Session Lock Status : {'🔒 LOCKED' if is_session_locked(session_dir) else '🟢 UNLOCKED (Ready)'}"
        )
    print(f"Exchange Status     :\n{json.dumps(status, indent=2)}")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
