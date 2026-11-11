"""ccba_harness.peer - Structured Peer Exchange Protocol & Grok CLI Dispatcher (ADR-0007 / ADR-0063..0065)."""

# flake8: noqa: F401
# ruff: noqa: F401
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ._mutex import FileMutexLock
from ._peer_anchor import (
    apply_anchor_patch,
    auto_apply_and_verify_patch,
    extract_anchor_payload,
    get_git_toplevel,
    recover_pending_anchor_transactions,
)
from ._peer_co_review import (
    orchestrate_peer_co_review,
    render_consensus_report_markdown,
    synthesize_verdicts,
)
from ._peer_models import (
    FRONTMATTER_PATTERN,
    AnchorPatchPayload,
    AutoApplyResult,
    CombinedTelemetry,
    FileChange,
    FilePatch,
    PatchReplacement,
    PeerCondition,
    PeerConsensusReport,
    PeerPromptEnvelope,
    PeerVerdictBlock,
    PeerVerdictTelemetry,
    ProfileTelemetryItem,
    _registry_timestamp,
    _sort_key_latest_exchange,
    extract_env_conversation_id,
    extract_frontmatter,
    parse_envelope_from_md,
    parse_verdict_from_md,
    render_prompt_header,
    render_verdict_header,
    resolve_spoke_slug_from_path,
)
from ._peer_telemetry import (
    _VERDICT_FILE_PREFIXES,
    _aggregate_registry_telemetry,
    _attach_verdict_lineage,
    _build_latest_verdict,
    _enforce_single_verdict_guardrails,
    extract_grok_session_telemetry,
    merge_overwritten_telemetry,
)
from ._peer_watchdog import (
    _VERDICT_ALIASES,
    AUDIT_BASE_SYSTEM_PROMPT,
    DEFAULT_FALLBACK_AUDITOR_MODEL,
    DEFAULT_PRIMARY_AUDITOR_MODEL,
    NO_TOOLS_DISALLOW_LIST,
    PROFILE_SPECS,
    READ_ONLY_DISALLOW_LIST,
    TIER_DEFAULT_MODELS,
    VERDICT_LATTICE_RANK,
    AgentIdentity,
    CostMode,
    EffortType,
    ModelTier,
    PeerExecutionProfile,
    RequestType,
    VerdictType,
    _build_synthesis_opts,
    _poll_grok_process_with_watchdog,
    _recover_verdict_from_chat_history,
    _resolve_grok_profile_options,
    _resolve_target_models,
    _terminate_proc_tree,
    _unwrap_grok_json_stdout,
    inspect_session_liveness,
    is_max_turns_exhausted,
    write_synthesis_prompt_file,
)
from .verifier import resolve_preset_commands, verify_patch_execution

# fmt: off
__all__ = [
    "AUDIT_BASE_SYSTEM_PROMPT", "AgentIdentity", "AnchorPatchPayload", "AutoApplyResult",
    "CombinedTelemetry", "CostMode", "DEFAULT_FALLBACK_AUDITOR_MODEL", "DEFAULT_GROK_SPEC",
    "DEFAULT_PRIMARY_AUDITOR_MODEL", "EffortType", "FRONTMATTER_PATTERN", "FileChange",
    "FilePatch", "ModelTier", "NO_TOOLS_DISALLOW_LIST", "PROFILE_SPECS", "PatchReplacement",
    "PeerCondition", "PeerConsensusReport", "PeerExecutionProfile", "PeerPromptEnvelope",
    "PeerVerdictBlock", "PeerVerdictTelemetry", "ProfileTelemetryItem", "READ_ONLY_DISALLOW_LIST",
    "RequestType", "TIER_DEFAULT_MODELS", "VERDICT_LATTICE_RANK", "VerdictType",
    "_resolve_grok_profile_options", "_resolve_target_models", "_unwrap_grok_json_stdout",
    "apply_anchor_patch", "atomic_write_text", "auto_apply_and_verify_patch", "build_grok_cmd",
    "classify_file_role", "compute_pending_queues", "extract_anchor_payload",
    "extract_frontmatter", "extract_grok_session_telemetry", "flush_pending_peer_triggers",
    "get_git_toplevel", "inspect_session_liveness", "invoke_grok_cli", "is_max_turns_exhausted",
    "orchestrate_peer_co_review", "parse_envelope_from_md", "parse_verdict_from_md",
    "publish_peer_message", "recover_pending_anchor_transactions",
    "render_consensus_report_markdown", "render_prompt_header", "render_verdict_header",
    "run_sync_cycle", "safe_read_and_hash", "scan_peer_exchange", "synthesize_verdicts",
    "verify_patch_execution",
]
# fmt: on

_SYNC_MUTEX = threading.Lock()
_PENDING_THREADS: list[threading.Thread] = []

DEFAULT_GROK_SPEC: dict[str, Any] = {
    "model": DEFAULT_PRIMARY_AUDITOR_MODEL,
    "fallback_model": DEFAULT_FALLBACK_AUDITOR_MODEL,
    "max_turns": 12,
    "tools": ["read_file", "grep", "list_dir"],
    "disallowed_tools": list(READ_ONLY_DISALLOW_LIST),
    "deny": ["Bash", "Write", "Edit", "WebFetch"],
    "disable_web_search": True,
    "verbatim": True,
    "reasoning_effort": "xhigh",
    "timeout": 600.0,
}


def _clean_completed_threads() -> None:
    """Prunes completed threads from the global pending list to prevent memory bloat."""
    global _PENDING_THREADS
    _PENDING_THREADS = [t for t in _PENDING_THREADS if t.is_alive()]


def flush_pending_peer_triggers(timeout: float = 5.0) -> None:
    """Waits for all pending asynchronous peer sync threads to finish before process exit."""
    deadline = time.time() + timeout
    for thread in list(_PENDING_THREADS):
        remaining = max(0.001, deadline - time.time())
        thread.join(timeout=remaining)
    _PENDING_THREADS.clear()


def atomic_write_bytes(target: Path, data: bytes, max_retries: int = 3) -> None:
    """Writes binary data to target file atomically using a temporary file with retry (ADR-0065)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target.with_suffix(f"{target.suffix}.tmp_{os.getpid()}_{time.time_ns()}")
    mode = None
    if target.exists():
        try:
            mode = target.stat().st_mode
        except OSError:
            pass
    try:
        temp_file.write_bytes(data)
        if mode is not None:
            try:
                os.chmod(temp_file, mode)
            except OSError:
                pass
        for attempt in range(max_retries):
            try:
                temp_file.replace(target)
                break
            except (PermissionError, OSError):
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.05 * (attempt + 1))
    except Exception:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise


def atomic_write_text(target: Path, content: str, max_retries: int = 3) -> None:
    """Writes UTF-8 text content to target file atomically via atomic_write_bytes (ADR-0063)."""
    atomic_write_bytes(target, content.encode("utf-8"), max_retries=max_retries)


def safe_read_and_hash(path: Path, max_retries: int = 3) -> tuple[str | None, str | None]:
    """Safely reads file content and computes SHA-256 with retry against partial writes."""
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
    """Classifies the role of a peer exchange file based on naming conventions."""
    name = path.name
    if (
        name in ("grok_live_summary.md", "status.json", "PEER_HANDSHAKE.md", "README.md")
        or name.endswith(".lock")
        or name.endswith(".gate.md")
        or name.startswith(".")
    ):
        return "AUXILIARY"
    if name.startswith("grok_request_antigravity_"):
        return "GROK_REQUEST"
    if name.startswith("antigravity_response_"):
        return "ANTIGRAVITY_RESPONSE"
    if name.startswith("prompt_grok_") or name.startswith("prompt_") or name.endswith("_prompt.md"):
        return "PROMPT_TO_GROK"
    if name.startswith("grok_implementation_") or name.startswith("grok_implement_"):
        return "GROK_IMPLEMENTATION"
    if name.startswith(("peer_review_", "peer_consultation_")):
        return "GROK_RESPONSE"
    if name.startswith(_VERDICT_FILE_PREFIXES):
        return "GROK_RESPONSE"
    return "AUXILIARY"


def load_cache(cache_file: Path) -> dict[str, str]:
    """Loads SHA-256 hash cache from disk using FileMutexLock."""
    if not cache_file.exists():
        return {}
    lock_path = cache_file.with_name(f"{cache_file.name}.lock")
    try:
        with FileMutexLock(lock_path, timeout=5.0):
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_cache(cache_file: Path, cache: dict[str, str]) -> None:
    """Saves SHA-256 hash cache to disk atomically under FileMutexLock."""
    lock_path = cache_file.with_name(f"{cache_file.name}.lock")
    with FileMutexLock(lock_path, timeout=5.0):
        atomic_write_text(cache_file, json.dumps(cache, indent=2))


def scan_peer_exchange(
    peer_exchange_dir: Path,
    cache: dict[str, str],
) -> tuple[list[FileChange], dict[str, str], dict[str, Any]]:
    """Scans peer_exchange directory, detects delta changes, and extracts metadata."""
    if not peer_exchange_dir.exists():
        return [], cache, {}

    new_cache = dict(cache)
    changes: list[FileChange] = []
    registry: dict[str, dict[str, Any]] = {}

    for entry in sorted(os.scandir(peer_exchange_dir), key=lambda e: e.name):
        if not entry.is_file() or not entry.name.endswith(".md"):
            continue
        path = Path(entry.path)
        role = classify_file_role(path)
        if role == "AUXILIARY":
            continue

        content, digest = safe_read_and_hash(path)
        if not content or not digest:
            continue

        envelope = parse_envelope_from_md(content, prompt_path=path)
        verdict = (
            None if role in ("PROMPT_TO_GROK", "GROK_REQUEST") else parse_verdict_from_md(content)
        )
        registry[entry.name] = {
            "role": role,
            "path": path,
            "mtime": entry.stat().st_mtime,
            "timestamp": _registry_timestamp(envelope, verdict),
            "envelope": envelope,
            "verdict": verdict,
            "sha256": digest,
        }

        if cache.get(entry.name) != digest:
            changes.append(FileChange(path, role, digest, envelope, verdict))
            new_cache[entry.name] = digest

    return changes, new_cache, registry


def compute_pending_queues(registry: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Matches request_ids or fresher output_path verdicts to identify unanswered prompts."""
    answered_ids: set[str] = set()
    grok_verdict_mtimes: dict[str, float] = {}
    for name, item in registry.items():
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]:
            answered_ids.add(item["verdict"].request_id)
            grok_verdict_mtimes[name] = float(item.get("mtime", 0.0))
        elif item["role"] == "ANTIGRAVITY_RESPONSE" and item["verdict"]:
            answered_ids.add(item["verdict"].request_id)

    pending_grok: list[str] = []
    pending_anti: list[str] = []
    for name, item in registry.items():
        env = item.get("envelope")
        if item["role"] == "PROMPT_TO_GROK" and env:
            out_name = Path(env.output_path).name if env.output_path else ""
            stem = name.removeprefix("prompt_grok_").removeprefix("prompt_").removesuffix(".md")
            cand_outs = {out_name, *(f"{pfx}{stem}.md" for pfx in _VERDICT_FILE_PREFIXES)} - {""}
            is_fresher_out = any(
                c in grok_verdict_mtimes and grok_verdict_mtimes[c] >= float(item.get("mtime", 0.0))
                for c in cand_outs
            )
            if env.request_id not in answered_ids and not is_fresher_out:
                pending_grok.append(name)
        elif item["role"] == "GROK_REQUEST" and env:
            if env.request_id not in answered_ids:
                pending_anti.append(name)

    return pending_anti, pending_grok


def update_status_json(
    status_file: Path,
    registry: dict[str, dict[str, Any]],
    pending_anti: list[str],
    pending_grok: list[str],
) -> None:
    """Updates status.json with latest state and verdicts protected by FileMutexLock."""
    tz = datetime.timezone(datetime.timedelta(hours=7))
    now_iso = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    total_tokens, total_cost_usd, by_model = _aggregate_registry_telemetry(registry)
    resp_roles = ("GROK_RESPONSE", "GROK_IMPLEMENTATION")
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
                "latest_verdict": _build_latest_verdict(registry),
            },
        },
        "exchange_stats": {
            "total_prompts": sum(1 for i in registry.values() if i["role"] == "PROMPT_TO_GROK"),
            "total_responses": sum(1 for i in registry.values() if i["role"] in resp_roles),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 4),
            "by_model": by_model,
            "pending_antigravity": pending_anti,
            "pending_grok": pending_grok,
        },
    }
    lock_path = status_file.with_name(f"{status_file.name}.lock")
    with FileMutexLock(lock_path, timeout=5.0):
        atomic_write_text(status_file, json.dumps(status_data, indent=2, ensure_ascii=False))


def update_live_summary(
    summary_file: Path,
    registry: dict[str, dict[str, Any]],
    pending_anti: list[str],
    pending_grok: list[str],
) -> None:
    """Renders a concise, lightweight summary (< 5 KB) to grok_live_summary.md."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    resp_roles = ("GROK_RESPONSE", "GROK_IMPLEMENTATION")
    resps = [i for i in registry.values() if i["role"] in resp_roles and i["verdict"]]
    resps.sort(key=_sort_key_latest_exchange, reverse=True)

    lines = [
        "# ⚡ Grok & Antigravity Live Peer Summary\n",
        f"> **Thời điểm cập nhật**: `{now_iso}` | **Cơ chế**: Delta SHA-256 Bridge (ADR-0063)\n\n",
        "## 1. Trạng Thái Vận Hành\n",
        f"- **Antigravity**: `{'waiting_for_grok' if pending_grok else 'idle'}` (Đang chờ Grok: {len(pending_grok)} requests)",
        f"- **Grok**: `{'in_progress' if pending_grok else 'idle'}` (Đang chờ Antigravity: {len(pending_anti)} requests)\n\n",
        "## 2. Hàng Đợi Đang Chờ (Pending Queue)\n",
        "### ⏳ Grok cần xử lý:" if pending_grok else "### ✅ Grok: Không có yêu cầu tồn đọng.",
    ]
    lines.extend(f"- `{p}`" for p in pending_grok[:5])
    if pending_anti:
        lines.append("\n### ⏳ Antigravity cần xử lý:")
        lines.extend(f"- `{p}`" for p in pending_anti[:5])
    lines.extend(
        [
            "\n## 3. Phán Quyết Gần Nhất (Recent Verdicts)\n",
            "| Tệp Phản Hồi | Phán Quyết (Verdict) | Điều Kiện | Tóm Tắt |",
            "|---|:---:|:---:|---|",
        ]
    )
    for item in resps[:8]:
        v = item["verdict"]
        lines.append(
            f"| `{item['path'].name}` | **`{v.verdict}`** | {len(v.conditions)} | {v.summary[:50]}... |"
        )
    lock_path = summary_file.with_name(f"{summary_file.name}.lock")
    with FileMutexLock(lock_path, timeout=5.0):
        atomic_write_text(summary_file, "\n".join(lines) + "\n")


def run_sync_cycle(
    peer_exchange_dir: Path,
    auto_gate: bool = False,
    auto_grok: bool = False,
) -> list[FileChange]:
    """Executes a single serialized observation and synchronization cycle."""
    actions_to_run: list[tuple[str, Path]] = []
    changes: list[FileChange] = []

    sync_lock = peer_exchange_dir / ".sync.lock"
    with _SYNC_MUTEX, FileMutexLock(sync_lock, timeout=10.0):
        cache_file = peer_exchange_dir / ".bridge_cache.json"
        status_file = peer_exchange_dir / "status.json"
        summary_file = peer_exchange_dir / "grok_live_summary.md"
        cache = load_cache(cache_file)
        changes, new_cache, registry = scan_peer_exchange(peer_exchange_dir, cache)
        pending_anti, pending_grok = compute_pending_queues(registry)
        update_status_json(status_file, registry, pending_anti, pending_grok)
        update_live_summary(summary_file, registry, pending_anti, pending_grok)
        if changes or new_cache != cache or not cache_file.exists():
            save_cache(cache_file, new_cache)
        for change in changes:
            if auto_grok and change.role == "PROMPT_TO_GROK":
                actions_to_run.append(("grok", change.path))
            elif auto_gate and change.role == "GROK_IMPLEMENTATION":
                actions_to_run.append(("gate", change.path))

    for action_type, path in actions_to_run:
        if action_type == "grok":
            invoke_grok_cli(path)
        elif action_type == "gate":
            from .peer_gate import run_full_gate, write_verdict_file

            result = run_full_gate(peer_exchange_dir.parent.parent)
            write_verdict_file(result, peer_exchange_dir)
    return changes


def publish_peer_message(
    envelope: PeerPromptEnvelope,
    body_text: str,
    target_path: Path,
    on_publish_hook: Callable[[Path], None] | None = None,
    auto_grok: bool = False,
) -> Path:
    """Atomically publishes a peer exchange envelope and asynchronously syncs state."""
    env_cid = extract_env_conversation_id()
    eff_envelope = envelope.model_copy(
        update={
            "conversation_id": envelope.conversation_id or env_cid,
            "spoke_name": envelope.spoke_name
            or resolve_spoke_slug_from_path(target_path, allow_ancestor_walk=bool(env_cid)),
        }
    )
    atomic_write_text(target_path, render_prompt_header(eff_envelope) + body_text.lstrip())
    if on_publish_hook:
        on_publish_hook(target_path)
    _clean_completed_threads()

    def _async_sync() -> None:
        try:
            run_sync_cycle(target_path.parent, auto_grok=auto_grok)
            if auto_grok:
                run_sync_cycle(target_path.parent, auto_grok=False)
        except Exception:
            pass

    thread = threading.Thread(target=_async_sync, daemon=True)
    _PENDING_THREADS.append(thread)
    thread.start()
    return target_path


def build_grok_cmd(
    prompt_path: Path,
    model: str,
    max_turns: int | None = None,
    tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    reasoning_effort: str | None = None,
    output_format: str | None = "plain",
    worktree: bool = False,
    session_id: str | None = None,
    system_prompt: str | None = None,
    deny: list[str] | str | None = None,
    resume_session_id: str | None = None,
    fork_session: bool = False,
    verbatim: bool = False,
    disable_web_search: bool = False,
) -> list[str]:
    """Constructs canonical grok CLI command list for headless execution (ADR-0063 / ADR-0064)."""
    cmd = ["grok", "-m", model, "--always-approve", "--no-subagents"]
    if resume_session_id:
        cmd.extend(["--resume", resume_session_id])
        if fork_session:
            cmd.append("--fork-session")
            if session_id:
                cmd.extend(["--session-id", session_id])
    elif session_id:
        cmd.extend(["--session-id", session_id])
    for flag, enabled in (("--verbatim", verbatim), ("--disable-web-search", disable_web_search)):
        if enabled:
            cmd.append(flag)
    if system_prompt:
        cmd.extend(["--system-prompt-override", system_prompt])
    if deny:
        for d in deny if isinstance(deny, (list, tuple)) else [deny]:
            cmd.extend(["--deny", str(d)])
    for flag, val in (
        ("--reasoning-effort", reasoning_effort),
        ("--max-turns", str(max_turns) if max_turns is not None else None),
        ("--tools", ",".join(tools) if tools else None),
        ("--disallowed-tools", ",".join(disallowed_tools) if disallowed_tools else None),
        ("--output-format", output_format),
    ):
        if val:
            cmd.extend([flag, val])
    if worktree:
        cmd.append("--worktree")
    cmd.extend(["--prompt-file", str(prompt_path)])
    return cmd


def _check_valid_output_file(output_file: Path) -> str | None:
    """Checks if output_file contains a valid PeerVerdictBlock or AnchorPatchPayload."""
    content, _ = safe_read_and_hash(output_file)
    if content and (parse_verdict_from_md(content) or extract_anchor_payload(content)):
        return content
    return None


def _finalize_grok_verdict_and_telemetry(
    stdout_text: str,
    prompt_path: Path,
    output_file: Path,
    duration: float,
    session_id: str | None,
    candidate_model: str,
    expected_reasoning_effort: str | None,
    synthesize_turns: int = 1,
    parent_session_id: str | None = None,
) -> bool:
    """Validates parsed verdict or anchor patch, attaches session telemetry, and writes output_file."""
    verdict = parse_verdict_from_md(stdout_text)
    prompt_content: str | None = None
    if verdict is None:
        if extract_anchor_payload(stdout_text) is None:
            return False
        prompt_content, _ = safe_read_and_hash(prompt_path)
        envelope = parse_envelope_from_md(prompt_content or "", prompt_path=prompt_path)
        verdict = PeerVerdictBlock(
            request_id=envelope.request_id if envelope else "req-auto",
            verdict="HANDOFF",
            summary="Fast-path anchor patch generated; pending orchestrator apply and verification.",
        )

    if session_id:
        if prompt_content is None:
            prompt_content, _ = safe_read_and_hash(prompt_path)
        telemetry = extract_grok_session_telemetry(
            session_id=session_id,
            timeout=3.0,
            fallback_prompt_text=prompt_content,
            fallback_resp_text=stdout_text,
            duration_seconds=duration,
            fallback_model=candidate_model,
            expected_reasoning_effort=expected_reasoning_effort,
            synthesize_turns=synthesize_turns,
            parent_session_id=parent_session_id,
        )
        if telemetry:
            verdict.telemetry = merge_overwritten_telemetry(output_file, telemetry)

    _attach_verdict_lineage(verdict, prompt_path, prompt_content)
    _enforce_single_verdict_guardrails(verdict)
    _, body = extract_frontmatter(stdout_text)
    final_output = render_verdict_header(verdict) + "\n" + body.lstrip()
    atomic_write_text(output_file, final_output)
    return True


def _spawn_and_poll_grok(
    cmd: list[str],
    output_file: Path,
    start_time: float,
    timeout: float,
    session_id: str | None,
) -> tuple[str, bool]:
    """Spawns grok subprocess with temp stdout/stderr and runs watchdog poll loop."""
    with (
        tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as temp_out,
        tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as temp_err,
    ):
        popen_kw: dict[str, Any] = {
            "stdout": temp_out,
            "stderr": temp_err,
            "stdin": subprocess.DEVNULL,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "env": {
                **os.environ,
                "GROK_BACKEND_SEARCH": "0",
                "GROK_CLAUDE_MCPS_ENABLED": "0",
                "GROK_CURSOR_MCPS_ENABLED": "0",
            },
        }
        if sys.platform != "win32":
            popen_kw["start_new_session"] = True
        proc = subprocess.Popen(cmd, **popen_kw)
        return _poll_grok_process_with_watchdog(
            proc,
            temp_out,
            output_file,
            start_time,
            timeout,
            session_id,
            _check_valid_output_file,
        )


def _run_single_grok_attempt(
    cmd: list[str],
    prompt_path: Path,
    output_file: Path,
    timeout: float,
    session_id: str | None = None,
    candidate_model: str = "unknown",
    expected_reasoning_effort: str | None = None,
    prior_duration: float = 0.0,
    synthesize_turns: int = 1,
    parent_session_id: str | None = None,
) -> bool:
    """Executes a single invocation of grok CLI and verifies output verdict (ADR-0064 / ADR-0065)."""
    start_time = time.time()
    try:
        stdout_text, ok = _spawn_and_poll_grok(cmd, output_file, start_time, timeout, session_id)
        if not ok:
            return False
        stdout_text, json_sid, is_aborted = _unwrap_grok_json_stdout(stdout_text)
        session_id = session_id or json_sid
        if (
            not is_aborted
            and (not stdout_text.strip() or parse_verdict_from_md(stdout_text) is None)
            and session_id
        ):
            stdout_text = (
                _recover_verdict_from_chat_history(session_id, parse_verdict_from_md) or stdout_text
            )
        if not stdout_text.strip():
            return False
        return _finalize_grok_verdict_and_telemetry(
            stdout_text,
            prompt_path,
            output_file,
            (time.time() - start_time) + max(0.0, prior_duration),
            session_id,
            candidate_model,
            expected_reasoning_effort,
            synthesize_turns=synthesize_turns,
            parent_session_id=parent_session_id,
        )
    except Exception:
        return False


def _dispatch_grok_candidate(
    prompt_path: Path,
    output_file: Path,
    candidate: str,
    opts: dict[str, Any],
    worktree: bool,
) -> bool:
    """Builds CLI command for a single candidate model and executes _run_single_grok_attempt."""
    cand_sid, is_synth = str(uuid.uuid4()), bool(opts.get("is_synthesis_turn"))
    synth_prompt = write_synthesis_prompt_file(prompt_path) if is_synth else None
    eff_sid = (
        cand_sid
        if (not opts["resume_session_id"] or opts["fork_session"])
        else opts["resume_session_id"]
    )
    cmd_kw = {
        k: v for k, v in opts.items() if k not in ("timeout", "is_synthesis_turn", "prior_duration")
    }
    t0 = time.time()
    try:
        cmd = build_grok_cmd(
            synth_prompt or prompt_path,
            candidate,
            worktree=worktree,
            session_id=cand_sid,
            **cmd_kw,
        )
        ok = _run_single_grok_attempt(
            cmd,
            prompt_path,
            output_file,
            opts["timeout"],
            session_id=eff_sid,
            candidate_model=candidate,
            expected_reasoning_effort=opts["reasoning_effort"],
            prior_duration=float(opts.get("prior_duration", 0.0)),
            synthesize_turns=2 if is_synth else 1,
            parent_session_id=opts.get("resume_session_id") if is_synth else None,
        )
    finally:
        if synth_prompt is not None:
            synth_prompt.unlink(missing_ok=True)
    if ok or is_synth or not is_max_turns_exhausted(eff_sid):
        return ok
    synth_opts = {
        **_build_synthesis_opts(opts, eff_sid),
        "prior_duration": max(0.0, time.time() - t0),
    }
    return _dispatch_grok_candidate(prompt_path, output_file, candidate, synth_opts, worktree)


def _sync_if_peer_exchange_dir(directory: Path) -> None:
    """Runs best-effort sync cycle when directory is peer_exchange or tracks status.json."""
    is_pe = directory.name == "peer_exchange" or (directory / "status.json").exists()
    target = directory if is_pe else (directory.parent / "peer_exchange")
    if target.is_dir():
        try:
            run_sync_cycle(target, auto_grok=False)
        except Exception:
            pass


def invoke_grok_cli(
    prompt_path: Path,
    model: str | None = None,
    profile: PeerExecutionProfile | str | None = None,
    tier: ModelTier | str | None = None,
    max_turns: int | None = None,
    timeout: float | None = None,
    worktree: bool = False,
    no_tools: bool = False,
    resume_session_id: str | None = None,
    fork_session: bool | None = None,
    output_file: str | Path | None = None,
) -> bool:
    """Invokes Grok CLI with Level-2 execution profile mapping and budget guardrails (ADR-0063 / ADR-0064)."""
    content, _ = safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(content or "", prompt_path=prompt_path)
    if not envelope or (not envelope.output_path and not output_file):
        print(
            f"[PREFLIGHT-ENVELOPE-ERROR] Prompt '{prompt_path.name}' lacks valid YAML frontmatter (--- ... ---).",
            file=sys.stderr,
        )
        return False

    target_out = (
        Path(output_file).resolve()
        if output_file
        else (prompt_path.parent / Path(envelope.output_path).name)
    )
    spec = PROFILE_SPECS.get(str(profile or envelope.profile), DEFAULT_GROK_SPEC)
    opts = _resolve_grok_profile_options(
        spec, envelope, max_turns, timeout, no_tools, resume_session_id, fork_session, prompt_path
    )
    ok = any(
        _dispatch_grok_candidate(prompt_path, target_out, cand, opts, worktree)
        for cand in _resolve_target_models(model, tier, spec)
    )
    if ok:
        _sync_if_peer_exchange_dir(prompt_path.parent)
    return ok
