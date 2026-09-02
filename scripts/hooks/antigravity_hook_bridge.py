"""Antigravity Lifecycle Hook Bridge — Adapter Layer.

Translates between Antigravity Agent Engine's hooks.json stdin/stdout protocol
(camelCase JSON) and CCBA's internal HookCoordinator (snake_case, in-process).

This module contains NO business logic — all security/policy decisions are
delegated to the existing HookCoordinator and its 7 registered hooks.

Architecture:
    Antigravity Engine → stdin JSON → Bridge (translate) → HookCoordinator → 7 hooks
                                      Bridge (translate) ← HookResult      ←
                      ← stdout JSON ←

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
ADR: 0054 — Antigravity Lifecycle Hooks & Security Bridge
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.hooks.base import HookContext, HookResult
from scripts.hooks.coordinator import get_default_coordinator

# Pre-computed decision mapping: CCBA exit_code → Antigravity decision string
_EXIT_CODE_TO_DECISION: dict[int, str] = {
    0: "allow",   # PASS
    1: "ask",     # WARNING → prompt user
    2: "deny",    # BLOCK
}


def _configure_windows_encoding() -> None:
    """Reconfigure stdin/stdout to UTF-8 on Windows to prevent encoding errors."""
    if sys.platform != "win32":
        return
    try:
        if isinstance(sys.stdin, io.TextIOWrapper):
            sys.stdin.reconfigure(encoding="utf-8")
        if isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout.reconfigure(encoding="utf-8")
        if isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _read_stdin() -> dict[str, Any]:
    """Reads and parses JSON payload from stdin.

    Returns:
        Parsed JSON dict, or empty dict on any read/parse failure.
    """
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return {}


def _stdin_to_context(payload: dict[str, Any]) -> HookContext:
    """Translates Antigravity camelCase stdin payload → CCBA HookContext.

    Args:
        payload: Raw JSON dict from Antigravity Agent Engine stdin.

    Returns:
        HookContext compatible with HookCoordinator.run_event().
    """
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})

    # Extract path from common tool argument patterns
    path = (
        tool_args.get("TargetFile", "")
        or tool_args.get("AbsolutePath", "")
        or tool_args.get("SearchPath", "")
        or tool_args.get("DirectoryPath", "")
        or ""
    )

    # Serialize args as JSON string (CCBA HookContext expects string)
    args_str = json.dumps(tool_args) if tool_args else ""

    return HookContext(
        event="pre-tool",
        tool=tool_name,
        path=path,
        args=args_str,
        cwd=str(_PROJECT_ROOT),
        status="",
        raw_payload=payload,
    )


def _result_to_stdout(max_exit_code: int, results: list[HookResult]) -> dict[str, Any]:
    """Translates CCBA HookResult → Antigravity stdout JSON.

    Args:
        max_exit_code: Aggregate exit code from HookCoordinator.
        results: List of individual HookResults.

    Returns:
        Dict conforming to Antigravity PreToolUse output contract.
    """
    decision = _EXIT_CODE_TO_DECISION.get(max_exit_code, "allow")

    # Collect reasons from hooks that didn't pass
    reasons = [r.message for r in results if not r.is_passed and r.message]
    reason = "; ".join(reasons) if reasons else ""

    return {
        "decision": decision,
        "reason": reason,
    }


def _write_stdout(output: dict[str, Any]) -> None:
    """Writes JSON output to stdout for Antigravity Agent Engine.

    Args:
        output: Dict to serialize as JSON.
    """
    sys.stdout.write(json.dumps(output))
    sys.stdout.flush()


def main() -> None:
    """Entry point: stdin → translate → HookCoordinator → translate → stdout.

    Note: CCBA hooks use print() for diagnostic messages. We redirect stdout
    to stderr during hook execution so their output doesn't contaminate the
    JSON response expected by Antigravity Agent Engine.
    """
    _configure_windows_encoding()

    # Save real stdout before hooks can pollute it
    real_stdout = sys.stdout

    try:
        payload = _read_stdin()

        if not payload:
            # Empty/invalid stdin → fail-safe allow
            real_stdout.write(json.dumps({"decision": "allow", "reason": ""}))
            real_stdout.flush()
            return

        # Redirect stdout → stderr so hook print() goes to stderr
        sys.stdout = sys.stderr

        context = _stdin_to_context(payload)
        coordinator = get_default_coordinator()
        max_exit_code, results = coordinator.run_event("pre-tool", context)
        output = _result_to_stdout(max_exit_code, results)

        # Restore real stdout and write clean JSON
        sys.stdout = real_stdout
        real_stdout.write(json.dumps(output))
        real_stdout.flush()

    except Exception as exc:
        # Restore stdout in case of error
        sys.stdout = real_stdout
        # Fail-safe: NEVER block the IDE on unexpected errors
        real_stdout.write(json.dumps({
            "decision": "allow",
            "reason": f"Hook bridge fail-safe: {exc}",
        }))
        real_stdout.flush()


if __name__ == "__main__":
    main()

