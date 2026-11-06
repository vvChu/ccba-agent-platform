"""_peer_watchdog.py - Execution profiles, liveness watchdog, and stdout/history helpers (ADR-0063..0067)."""

from __future__ import annotations

import datetime
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

AgentIdentity = Literal["antigravity", "grok"]
PeerExecutionProfile = Literal[
    "audit_plan",
    "agentic_code",
    "patch_fast",
    "code_review",
    "arch_audit",
    "audit_direct",
    "deep_spec_audit",
    "signoff_diff",
]
ModelTier = Literal["local", "gateway", "cloud"]
RequestType = Literal[
    "review",
    "implement",
    "verify",
    "consult",
    "research",
    "audit",
    "incident",
    "discuss",
    "plan",
]
VerdictType = Literal[
    "APPROVE",
    "APPROVE_WITH_CONDITIONS",
    "APPROVE_WITH_RESERVATIONS",
    "APPROVE_PLAN",
    "REVISE_PLAN",
    "REJECT_PLAN",
    "REJECT",
    "FINAL_ACCEPT",
    "GATE_PASS",
    "GATE_FAIL",
    "HANDOFF",
]
EffortType = Literal["XS", "S", "M", "L", "XL"]
CostMode = Literal["exact", "estimated", "unknown"]

VERDICT_LATTICE_RANK: dict[VerdictType, int] = {
    "REJECT": 100,
    "REJECT_PLAN": 95,
    "GATE_FAIL": 90,
    "REVISE_PLAN": 80,
    "HANDOFF": 70,
    "APPROVE_WITH_CONDITIONS": 60,
    "APPROVE_WITH_RESERVATIONS": 55,
    "APPROVE_PLAN": 40,
    "FINAL_ACCEPT": 35,
    "GATE_PASS": 30,
    "APPROVE": 20,
}

DEFAULT_PRIMARY_AUDITOR_MODEL = "grok-4.7"  # ccba:allow-raw-model
DEFAULT_FALLBACK_AUDITOR_MODEL = "gemini-38-flash"  # ccba:allow-raw-model

TIER_DEFAULT_MODELS: dict[str, str] = {
    "local": "qwen-local",  # ccba:allow-raw-model
    "gateway": "gemini-38-flash",  # ccba:allow-raw-model
    "cloud": "grok-4.7",  # ccba:allow-raw-model
}

READ_ONLY_DISALLOW_LIST: list[str] = [
    "Agent",
    "run_terminal_command",
    "search_replace",
    "write_file",
    "write",
    "spawn_subagent",
    "search_tool",
    "use_tool",
    "image_gen",
    "image_edit",
    "image_to_video",
    "reference_to_video",
]

NO_TOOLS_DISALLOW_LIST: list[str] = [
    "read_file",
    "grep",
    "list_dir",
    "glob",
    "bash",
    "run_terminal_command",
    "edit_file",
    "search_replace",
    "write_file",
    "write",
    "spawn_subagent",
    "todo_write",
    "monitor",
    "search_tool",
    "use_tool",
    "workflow",
    "enter_plan_mode",
    "exit_plan_mode",
    "ask_user_question",
    "send_feedback",
    "web_fetch",
    "image_gen",
    "image_edit",
    "image_to_video",
    "reference_to_video",
]

VERDICT_RESERVE_TURNS: int = 2

BOUNDED_TOOL_BUDGET_PROMPT: str = (
    "You have read-only tools (read_file, grep, list_dir) to inspect cross-file invariants, "
    "AST structures, and linters. Budget your tool usage strictly: complete repository exploration "
    f"with at least {VERDICT_RESERVE_TURNS} turns remaining before max_turns, and in your final synthesis "
    "turn (containing zero tool calls) emit your complete YAML frontmatter verdict enclosed in '---' "
    "with risk_score as an integer 1..5 and conditions items containing id, description, and blocking."
)

AUDIT_BASE_SYSTEM_PROMPT: str = (
    "You are an expert software, architecture, and specification peer auditor. "
    "In your final synthesis turn (containing zero tool calls), start your response with YAML frontmatter "
    "enclosed in '---' containing request_id, verdict "
    "(APPROVE | APPROVE_WITH_CONDITIONS | APPROVE_PLAN | REVISE_PLAN | REJECT_PLAN | REJECT | FINAL_ACCEPT | HANDOFF), "
    "risk_score (integer 1..5), conditions (list of {id, description, blocking}), and summary, "
    "followed by your structured audit findings. " + BOUNDED_TOOL_BUDGET_PROMPT
)

SYNTHESIS_FALLBACK_PROMPT: str = (
    "You are synthesizing the final peer audit verdict from evidence already gathered in this session. "
    "Emit zero tool calls. Start your response with YAML frontmatter enclosed in '---' containing "
    "request_id, verdict (APPROVE | APPROVE_WITH_CONDITIONS | APPROVE_PLAN | REVISE_PLAN | REJECT | FINAL_ACCEPT | HANDOFF), "
    "risk_score (integer 1..5), conditions (list of items with id, description, and blocking), and summary, "
    "followed by your structured findings."
)

PROFILE_SPECS: dict[str, dict[str, Any]] = {
    "audit_plan": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 12,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": list(READ_ONLY_DISALLOW_LIST),
        "deny": ["Bash", "Write", "Edit", "WebFetch"],
        "disable_web_search": True,
        "verbatim": True,
        "reasoning_effort": "xhigh",
        "system_prompt": AUDIT_BASE_SYSTEM_PROMPT,
        "timeout": 900.0,
    },
    "agentic_code": {
        "model": "grok-4.7-build-fast",  # ccba:allow-raw-model
        "fallback_model": "claude-sonnet-4-6",  # ccba:allow-raw-model
        "max_turns": 8,
        "tools": ["read_file", "search_replace", "list_dir"],
        "disallowed_tools": [
            "spawn_subagent",
            "run_terminal_command",
            "image_gen",
            "image_edit",
            "image_to_video",
            "reference_to_video",
        ],
        "disable_web_search": True,
        "verbatim": True,
        "reasoning_effort": "high",
        "timeout": 600.0,
    },
    "patch_fast": {
        "model": "qwen-local",  # ccba:allow-raw-model
        "fallback_model": "grok-4.7-build-fast",  # ccba:allow-raw-model
        "max_turns": 1,
        "tools": None,
        "disallowed_tools": list(NO_TOOLS_DISALLOW_LIST),
        "disable_web_search": True,
        "verbatim": True,
        "reasoning_effort": None,
        "timeout": 120.0,
        "deny": ["*"],
        "system_prompt": (
            "You are a pure JSON and markdown patch generator. "
            "You MUST start your response with YAML frontmatter enclosed in --- containing request_id, verdict: HANDOFF, and summary, "
            "followed directly by a ```json block containing the AnchorPatchPayload. "
            "DO NOT chat, DO NOT explain, DO NOT output introductory prose. "
            "Respond immediately with the required formatted blocks."
        ),
    },
    "code_review": {
        "model": "gemini-38-flash",  # ccba:allow-raw-model
        "fallback_model": "grok-4.7-build-fast",  # ccba:allow-raw-model
        "max_turns": 10,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": list(READ_ONLY_DISALLOW_LIST),
        "deny": ["Bash", "Write", "Edit", "WebFetch"],
        "disable_web_search": True,
        "verbatim": True,
        "reasoning_effort": "high",
        "system_prompt": AUDIT_BASE_SYSTEM_PROMPT,
        "timeout": 300.0,
    },
    "arch_audit": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 8,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": list(READ_ONLY_DISALLOW_LIST),
        "deny": ["Bash", "Write", "Edit", "WebFetch"],
        "disable_web_search": True,
        "verbatim": True,
        "reasoning_effort": "xhigh",
        "system_prompt": AUDIT_BASE_SYSTEM_PROMPT,
        "timeout": 600.0,
    },
    "audit_direct": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 3,
        "tools": None,
        "disallowed_tools": list(NO_TOOLS_DISALLOW_LIST),
        "deny": ["*"],
        "disable_web_search": True,
        "verbatim": True,
        "reasoning_effort": "high",
        "system_prompt": (
            "You are an expert software and system architecture auditor. Start your response "
            "with YAML frontmatter enclosed in '---' containing request_id, verdict "
            "(APPROVE | APPROVE_WITH_CONDITIONS | REVISE_PLAN | REJECT | HANDOFF), risk_score (integer 1..5), "
            "conditions (list of {id, description, blocking}), and summary, followed by your architectural audit findings. "
            "Respond directly without invoking external tools."
        ),
        "timeout": 120.0,
    },
    "deep_spec_audit": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 25,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": list(READ_ONLY_DISALLOW_LIST),
        "deny": ["Bash", "Write", "Edit", "WebFetch"],
        "disable_web_search": True,
        "verbatim": True,
        "output_format": "json",
        "reasoning_effort": "xhigh",
        "system_prompt": AUDIT_BASE_SYSTEM_PROMPT,
        "timeout": 900.0,
    },
    "signoff_diff": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 8,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": list(READ_ONLY_DISALLOW_LIST),
        "deny": ["Bash", "Write", "Edit", "WebFetch"],
        "disable_web_search": True,
        "verbatim": True,
        "fork_session": True,
        "output_format": "json",
        "reasoning_effort": "high",
        "system_prompt": AUDIT_BASE_SYSTEM_PROMPT,
        "timeout": 600.0,
    },
}

_VERDICT_ALIASES: dict[str, str] = {
    "CONDITIONAL_APPROVAL": "APPROVE_WITH_CONDITIONS",
    "CONDITIONAL_APPROVE": "APPROVE_WITH_CONDITIONS",
    "APPROVE_CONDITIONAL": "APPROVE_WITH_CONDITIONS",
    "APPROVED_WITH_CONDITIONS": "APPROVE_WITH_CONDITIONS",
    "APPROVED_WITH_RESERVATIONS": "APPROVE_WITH_RESERVATIONS",
    "APPROVED": "APPROVE",
    "APPROVED_PLAN": "APPROVE_PLAN",
    "IMPLEMENTATION_READY": "APPROVE",
    "PLAN_SUBMITTED": "APPROVE_PLAN",
    "REJECTED": "REJECT",
    "REJECTED_PLAN": "REJECT_PLAN",
    "REVISE": "REVISE_PLAN",
    "NEEDS_REVISION": "REVISE_PLAN",
    "REQUEST_CHANGES": "REVISE_PLAN",
    "CHANGES_REQUESTED": "REVISE_PLAN",
    "CONDITIONAL": "APPROVE_WITH_CONDITIONS",
    "CONDITIONAL_PASS": "APPROVE_WITH_CONDITIONS",
    "ACCEPTED_WITH_REVISED_CONDITIONS": "APPROVE_WITH_CONDITIONS",
    "PASS": "GATE_PASS",
    "FAIL": "GATE_FAIL",
    "APPROVE_CODE": "FINAL_ACCEPT",
    "CONDITIONAL_GO": "APPROVE_WITH_CONDITIONS",
    "APPROVE_WITH_CORRECTIONS": "APPROVE_WITH_CONDITIONS",
}


def _unwrap_grok_json_stdout(stdout_text: str) -> tuple[str, str | None, bool]:
    """Unwraps `--output-format json` stdout from Grok CLI and checks `stopReason == 'end_turn'`.

    Args:
        stdout_text: Raw stdout captured from Grok CLI.

    Returns:
        Tuple of (extracted_markdown_text, session_id_from_json, is_aborted_json).
    """
    stripped = stdout_text.strip()
    if not stripped.startswith("{"):
        return stdout_text, None, False
    try:
        payload = json.loads(stripped)
    except Exception:
        return stdout_text, None, False
    if not isinstance(payload, dict) or ("text" not in payload and "stopReason" not in payload):
        return stdout_text, None, False
    stop_reason = payload.get("stopReason")
    sid = str(payload["sessionId"]) if isinstance(payload.get("sessionId"), str) else None
    if stop_reason is not None and stop_reason != "end_turn":
        return "", sid, True
    return str(payload.get("text") or ""), sid, False


def _terminate_proc_tree(proc: subprocess.Popen[Any]) -> None:
    """Terminates a process and its child process group safely (COND-03 / ADR-0065)."""
    pid = proc.pid
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        elif hasattr(os, "killpg") and hasattr(os, "getpgid"):
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except OSError:
                proc.terminate()
        else:
            proc.terminate()
        proc.wait(timeout=2.0)
    except Exception:
        try:
            if sys.platform != "win32" and hasattr(os, "killpg") and hasattr(os, "getpgid"):
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except OSError:
                    proc.kill()
            else:
                proc.kill()
            proc.wait(timeout=2.0)
        except Exception:
            pass


def _parse_event_timestamp(raw_ts: Any, fallback_mtime: float) -> float:
    """Parses ISO-8601 or numeric timestamp from an events.jsonl record."""
    if isinstance(raw_ts, (int, float)):
        return float(raw_ts) if raw_ts < 1e11 else float(raw_ts) / 1000.0
    if isinstance(raw_ts, str) and raw_ts.strip():
        try:
            return datetime.datetime.fromisoformat(
                raw_ts.strip().replace("Z", "+00:00")
            ).timestamp()
        except ValueError:
            pass
    return fallback_mtime


def inspect_session_liveness(
    session_id: str,
    session_root: Path | None = None,
) -> tuple[str | None, float | None]:
    """Inspects the latest event in ~/.grok/sessions/**/<session_id>/events.jsonl.

    Args:
        session_id: UUID of the active Grok session.
        session_root: Optional override root directory for sessions.

    Returns:
        Tuple of (state_string 'type:phase_or_outcome', age_seconds) or (None, None).
    """
    if not session_id:
        return None, None
    root = session_root or (Path.home() / ".grok" / "sessions")
    if not root.exists():
        return None, None
    try:
        for p in root.rglob(f"{session_id}/events.jsonl"):
            if not p.is_file():
                continue
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            for raw in reversed(lines):
                cleaned = raw.strip(" \t\r\n\x00")
                if not cleaned:
                    continue
                try:
                    evt = json.loads(cleaned)
                except Exception:
                    continue
                if not isinstance(evt, dict):
                    continue
                etype = str(evt.get("type") or "")
                detail = str(evt.get("phase") or evt.get("outcome") or "")
                ts = _parse_event_timestamp(evt.get("ts"), p.stat().st_mtime)
                return f"{etype}:{detail}", max(0.0, time.time() - ts)
    except Exception:
        pass
    return None, None


def is_max_turns_exhausted(
    session_id: str,
    session_root: Path | None = None,
) -> bool:
    """Checks if a Grok session terminated due to max_turns_reached in events.jsonl."""
    if not session_id:
        return False
    root = session_root or (Path.home() / ".grok" / "sessions")
    if not root.exists():
        return False
    try:
        for p in root.rglob(f"{session_id}/events.jsonl"):
            if p.is_file() and "max_turns_reached" in p.read_text(
                encoding="utf-8", errors="replace"
            ):
                return True
    except Exception:
        pass
    return False


def _build_synthesis_opts(opts: dict[str, Any], eff_sid: str) -> dict[str, Any]:
    """Constructs KV-cache-preserving in-place synthesis options after max_turns exploration."""
    return {
        **opts,
        "max_turns": 2,
        "resume_session_id": eff_sid,
        "fork_session": False,
        "is_synthesis_turn": True,
    }


def write_synthesis_prompt_file(prompt_path: Path, request_id: str | None = None) -> Path:
    """Writes a temporary user-turn synthesis prompt file preserving Turn 1 KV-cache prefix."""
    req_id = request_id
    if not req_id and prompt_path.exists():
        raw = prompt_path.read_text(encoding="utf-8", errors="replace")
        for line in raw.splitlines()[:30]:
            if line.strip().startswith("request_id:"):
                req_id = line.split(":", 1)[1].strip().strip("'\"")
                break
    req_clause = f"\nTarget request_id: {req_id}\n" if req_id else "\n"
    fd, tmp_name = tempfile.mkstemp(prefix="grok_synth_", suffix=".md")
    tmp_path = Path(tmp_name)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(f"{SYNTHESIS_FALLBACK_PROMPT}{req_clause}")
    return tmp_path


def _recover_verdict_from_chat_history(
    session_id: str,
    parse_fn: Callable[[str], Any],
    session_root: Path | None = None,
) -> str:
    """Recovers assistant markdown containing a valid verdict from chat_history.jsonl.

    Args:
        session_id: UUID of the Grok session to inspect.
        parse_fn: Callable (`parse_verdict_from_md`) used to validate candidate content.
        session_root: Optional override root directory for sessions.

    Returns:
        Recovered markdown string if found, or empty string.
    """
    root = session_root or (Path.home() / ".grok" / "sessions")
    max_bytes = 2 * 1024 * 1024
    try:
        for p in root.glob(f"**/{session_id}/chat_history.jsonl"):
            if not p.exists():
                continue
            file_size = p.stat().st_size
            with p.open("r", encoding="utf-8", errors="replace") as f:
                if file_size > max_bytes:
                    f.seek(file_size - max_bytes)
                    f.readline()
                lines = f.readlines()
            for line in reversed(lines):
                cleaned = line.strip(" \t\r\n\x00")
                if not cleaned:
                    continue
                try:
                    d = json.loads(cleaned)
                except Exception:
                    continue
                if not isinstance(d, dict):
                    continue
                cand = d.get("content") if d.get("type") == "assistant" else None
                if isinstance(cand, str) and cand and parse_fn(cand) is not None:
                    return cand
    except Exception:
        pass
    return ""


def _poll_grok_process_with_watchdog(
    proc: subprocess.Popen[Any],
    temp_out: Any,
    output_file: Path,
    start_time: float,
    timeout: float,
    session_id: str | None,
    has_valid_output_fn: Callable[[Path], str | None],
) -> tuple[str, bool]:
    """Polls Grok CLI subprocess with liveness-aware grace window and stall fail-fast."""
    deadline, grace_granted = start_time + timeout, False
    stream_states = ("phase_changed:streaming_text", "phase_changed:streaming_reasoning")
    while True:
        if proc.poll() is not None:
            temp_out.seek(0)
            stdout_text = temp_out.read()
            if not stdout_text and hasattr(proc, "communicate"):
                comm_out, _ = proc.communicate()
                stdout_text = comm_out or ""
            return stdout_text, True
        if output_file.exists() and output_file.stat().st_mtime >= start_time:
            valid_content = has_valid_output_fn(output_file)
            if valid_content:
                _terminate_proc_tree(proc)
                return valid_content, True
        last_state, age_s = inspect_session_liveness(session_id or "")
        if last_state and age_s is not None:
            if last_state in ("turn_ended:error", "turn_ended:cancelled") or (
                last_state == "mcp_init_completed:" and age_s > 90.0
            ):
                _terminate_proc_tree(proc)
                return "", False
            if last_state.startswith("turn_ended:") and age_s > 5.0:
                temp_out.seek(0)
                stdout_text = temp_out.read()
                _terminate_proc_tree(proc)
                return stdout_text, True
        if time.time() >= deadline:
            if (
                not grace_granted
                and last_state in stream_states
                and age_s is not None
                and age_s < 5.0
            ):
                deadline, grace_granted = deadline + 45.0, True
            else:
                _terminate_proc_tree(proc)
                return "", False
        time.sleep(1.0)


def _resolve_target_models(
    model: str | None,
    tier: ModelTier | str | None,
    spec: dict[str, Any],
) -> list[str]:
    """Resolves ordered list of candidate Grok models (primary + fallback)."""
    if model:
        return [model]
    if tier and str(tier) in TIER_DEFAULT_MODELS:
        return [TIER_DEFAULT_MODELS[str(tier)]]
    if os.getenv("CCBA_GROK_MODEL"):
        return [os.environ["CCBA_GROK_MODEL"]]
    targets = [spec["model"]]
    fallback = spec.get("fallback_model")
    if fallback and fallback not in targets:
        targets.append(fallback)
    return targets


def _resolve_grok_profile_options(
    spec: dict[str, Any],
    envelope: Any,
    max_turns: int | None,
    timeout: float | None,
    no_tools: bool,
    resume_session_id: str | None,
    fork_session: bool | None,
) -> dict[str, Any]:
    """Resolves effective CLI options from profile spec, prompt envelope, and caller overrides."""
    env_turns = envelope.max_turns if envelope is not None else None
    eff_turns = (
        max_turns
        if max_turns is not None
        else (env_turns if env_turns is not None else spec.get("max_turns"))
    )
    tools, disallowed, deny = spec.get("tools"), spec.get("disallowed_tools"), spec.get("deny")
    if no_tools:
        tools, disallowed, deny = None, list(NO_TOOLS_DISALLOW_LIST), ["*"]
        if max_turns is None and (eff_turns is None or eff_turns > 3):
            eff_turns = 3
    eff_resume = resume_session_id or (envelope.resume_session_id if envelope is not None else None)
    env_fork = envelope.fork_session if envelope is not None else None
    eff_fork = (
        fork_session
        if fork_session is not None
        else (
            env_fork if env_fork is not None else bool(spec.get("fork_session", bool(eff_resume)))
        )
    )
    return {
        "max_turns": eff_turns,
        "tools": tools,
        "disallowed_tools": disallowed,
        "deny": deny,
        "reasoning_effort": spec.get("reasoning_effort"),
        "system_prompt": spec.get("system_prompt"),
        "timeout": timeout if timeout is not None else spec.get("timeout", 180.0),
        "resume_session_id": eff_resume,
        "fork_session": eff_fork,
        "verbatim": bool(spec.get("verbatim", False)),
        "disable_web_search": bool(spec.get("disable_web_search", False)),
        "output_format": str(spec.get("output_format") or "plain"),
    }
