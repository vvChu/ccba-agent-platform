"""ccba_harness.peer - Structured Peer Exchange Protocol (ADR-0007 / Issue #458).

Defines Pydantic v2 schemas and serialization helpers for bidirectional agent communication
between Antigravity and Grok (or other peer agents) using YAML front-matter envelopes.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Literal, NamedTuple

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ._mutex import FileMutexLock

# ccba:allow-raw-model
DEFAULT_PRIMARY_AUDITOR_MODEL = "grok-4.7"
# ccba:allow-raw-model
DEFAULT_FALLBACK_AUDITOR_MODEL = "gemini-38-flash"

AgentIdentity = Literal["antigravity", "grok"]
RequestType = Literal[
    "review",
    "implement",
    "verify",
    "consult",
    "research",
    "audit",
    "incident",
    "discuss",
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
]
EffortType = Literal["XS", "S", "M", "L", "XL"]

FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)

_SYNC_MUTEX = threading.Lock()
_PENDING_THREADS: list[threading.Thread] = []


class FileChange(NamedTuple):
    """Represents a detected delta file change in peer exchange directory."""

    path: Path
    role: str
    sha256: str
    envelope: PeerPromptEnvelope | None = None
    verdict: PeerVerdictBlock | None = None


class PeerPromptEnvelope(BaseModel):
    """Envelopes a prompt request sent from one peer agent to another."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    from_agent: AgentIdentity
    to_agent: AgentIdentity
    request_type: RequestType
    subject: str
    timestamp: str
    source_documents: list[str] = Field(default_factory=list)
    output_path: str
    context: str | None = None


class PeerCondition(BaseModel):
    """A requirement or condition attached to a verdict."""

    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    blocking: bool = True


class PeerVerdictBlock(BaseModel):
    """Structured verdict issued by a peer agent in response to a prompt."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    verdict: VerdictType
    conditions: list[PeerCondition] = Field(default_factory=list)
    risk_score: int | None = None
    effort: EffortType | None = None
    summary: str = ""


def extract_frontmatter(md_content: str) -> tuple[dict[str, Any] | None, str]:
    """Extracts raw YAML frontmatter dictionary and remaining body from markdown content.

    Args:
        md_content: Raw markdown text possibly starting with YAML frontmatter.

    Returns:
        A tuple of (parsed_dict, body_text). If absent or invalid, returns (None, md_content).
    """
    if not md_content or not md_content.startswith("---"):
        return None, md_content
    match = FRONTMATTER_PATTERN.match(md_content)
    if not match:
        return None, md_content
    yaml_text = match.group(1)
    body = md_content[match.end():]
    try:
        data = yaml.safe_load(yaml_text)
        if isinstance(data, dict):
            return data, body
        return None, md_content
    except Exception:
        return None, md_content


def parse_envelope_from_md(md_content: str) -> PeerPromptEnvelope | None:
    """Parses PeerPromptEnvelope from markdown frontmatter.

    Args:
        md_content: Markdown content to parse.

    Returns:
        PeerPromptEnvelope instance if valid, or None if invalid or absent.
    """
    data, _ = extract_frontmatter(md_content)
    if not data or "from_agent" not in data:
        return None
    try:
        return PeerPromptEnvelope.model_validate(data)
    except Exception:
        return None


def parse_verdict_from_md(md_content: str) -> PeerVerdictBlock | None:
    """Parses PeerVerdictBlock from markdown frontmatter.

    Args:
        md_content: Markdown content to parse.

    Returns:
        PeerVerdictBlock instance if valid, or None if invalid or absent.
    """
    data, _ = extract_frontmatter(md_content)
    if not data or "verdict" not in data:
        return None
    try:
        return PeerVerdictBlock.model_validate(data)
    except Exception:
        return None


def render_prompt_header(envelope: PeerPromptEnvelope) -> str:
    """Renders YAML frontmatter block for a prompt envelope.

    Args:
        envelope: PeerPromptEnvelope to serialize.

    Returns:
        YAML frontmatter string enclosed in '---'.
    """
    payload = envelope.model_dump(exclude_none=True)
    yaml_str = yaml.dump(payload, sort_keys=False, allow_unicode=True)
    return f"---\n{yaml_str}---\n"


def render_verdict_header(verdict: PeerVerdictBlock) -> str:
    """Renders YAML frontmatter block for a verdict block.

    Args:
        verdict: PeerVerdictBlock to serialize.

    Returns:
        YAML frontmatter string enclosed in '---'.
    """
    payload = verdict.model_dump(exclude_none=True)
    yaml_str = yaml.dump(payload, sort_keys=False, allow_unicode=True)
    return f"---\n{yaml_str}---\n"


def _clean_completed_threads() -> None:
    """Prunes completed threads from the global pending list to prevent memory bloat."""
    global _PENDING_THREADS
    _PENDING_THREADS = [t for t in _PENDING_THREADS if t.is_alive()]


def flush_pending_peer_triggers(timeout: float = 5.0) -> None:
    """Waits for all pending asynchronous peer sync threads to finish before process exit.

    Args:
        timeout: Maximum total seconds to wait across all active threads.
    """
    deadline = time.time() + timeout
    for thread in list(_PENDING_THREADS):
        remaining = max(0.001, deadline - time.time())
        thread.join(timeout=remaining)
    _PENDING_THREADS.clear()


def atomic_write_text(target: Path, content: str) -> None:
    """Writes text content to target file atomically using a temporary file (Grok C2).

    Args:
        target: Destination file path.
        content: Text string content to persist.
    """
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
    """Safely reads file content and computes SHA-256 with retry against partial writes.

    Args:
        path: Target file path to read.
        max_retries: Retry attempts on transient OS lock or read errors.

    Returns:
        Tuple of (content_string, sha256_hex) or (None, None) if unreadable.
    """
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
    """Classifies the role of a peer exchange file based on naming conventions.

    Args:
        path: File path to inspect.

    Returns:
        Identified role string.
    """
    name = path.name
    if (
        name in ("grok_live_summary.md", "status.json", "PEER_HANDSHAKE.md", "README.md")
        or name.endswith(".lock")
        or name.startswith(".")
    ):
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


def load_cache(cache_file: Path) -> dict[str, str]:
    """Loads SHA-256 hash cache from disk using FileMutexLock.

    Args:
        cache_file: Path to cache JSON file.

    Returns:
        Dictionary mapping filename to SHA-256 hex string.
    """
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
    """Saves SHA-256 hash cache to disk atomically under FileMutexLock.

    Args:
        cache_file: Path to cache JSON file.
        cache: Dictionary mapping filename to SHA-256 hex string.
    """
    lock_path = cache_file.with_name(f"{cache_file.name}.lock")
    with FileMutexLock(lock_path, timeout=5.0):
        atomic_write_text(cache_file, json.dumps(cache, indent=2))


def scan_peer_exchange(
    peer_exchange_dir: Path,
    cache: dict[str, str],
) -> tuple[list[FileChange], dict[str, str], dict[str, Any]]:
    """Scans peer_exchange directory, detects delta changes, and extracts metadata.

    Args:
        peer_exchange_dir: Directory containing peer exchange markdown files.
        cache: In-memory SHA-256 cache dictionary.

    Returns:
        Tuple of (detected_changes, updated_cache, registry_dict).
    """
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

        if cache.get(entry.name) != digest:
            changes.append(FileChange(path, role, digest, envelope, verdict))
            new_cache[entry.name] = digest

    return changes, new_cache, registry


def compute_pending_queues(registry: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Matches request_ids to identify unanswered prompts for Antigravity and Grok.

    Args:
        registry: Directory registry of all detected markdown files.

    Returns:
        Tuple of (pending_for_antigravity_list, pending_for_grok_list).
    """
    answered_ids: set[str] = set()
    for item in registry.values():
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]:
            answered_ids.add(item["verdict"].request_id)
        elif item["role"] == "ANTIGRAVITY_RESPONSE" and item["verdict"]:
            answered_ids.add(item["verdict"].request_id)

    pending_grok: list[str] = []
    pending_anti: list[str] = []
    for name, item in registry.items():
        if item["role"] == "PROMPT_TO_GROK" and item["envelope"]:
            if item["envelope"].request_id not in answered_ids:
                pending_grok.append(name)
        elif item["role"] == "GROK_REQUEST" and item["envelope"]:
            if item["envelope"].request_id not in answered_ids:
                pending_anti.append(name)

    return pending_anti, pending_grok


def _build_latest_verdict(registry: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Extracts the most recent Grok verdict details from registry.

    Args:
        registry: Directory registry of peer files.

    Returns:
        Dictionary summary of the latest verdict, or None.
    """
    grok_resps = [
        item
        for item in registry.values()
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]
    ]
    if not grok_resps:
        return None
    grok_resps.sort(key=lambda x: x["mtime"], reverse=True)
    top = grok_resps[0]
    verdict = top["verdict"]
    return {
        "request_id": verdict.request_id,
        "verdict": verdict.verdict,
        "blocking_conditions": len([c for c in verdict.conditions if c.blocking]),
        "output_path": top["path"].name,
        "summary": verdict.summary,
    }


def update_status_json(
    status_file: Path,
    registry: dict[str, dict[str, Any]],
    pending_anti: list[str],
    pending_grok: list[str],
) -> None:
    """Updates status.json with latest state and verdicts protected by FileMutexLock.

    Args:
        status_file: Target status.json Path.
        registry: Metadata registry of scanned files.
        pending_anti: List of file names pending for Antigravity.
        pending_grok: List of file names pending for Grok.
    """
    tz = datetime.timezone(datetime.timedelta(hours=7))
    now_iso = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
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
            "total_prompts": len([i for i in registry.values() if i["role"] == "PROMPT_TO_GROK"]),
            "total_responses": len(
                [i for i in registry.values() if i["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION")]
            ),
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
    """Renders a concise, lightweight summary (< 5 KB) to grok_live_summary.md.

    Args:
        summary_file: Target grok_live_summary.md Path.
        registry: Metadata registry of scanned files.
        pending_anti: List of file names pending for Antigravity.
        pending_grok: List of file names pending for Grok.
    """
    tz = datetime.timezone(datetime.timedelta(hours=7))
    now_iso = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    resps = [
        i for i in registry.values()
        if i["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and i["verdict"]
    ]
    resps.sort(key=lambda x: x["mtime"], reverse=True)

    lines = [
        "# ⚡ Grok & Antigravity Live Peer Summary\n",
        f"> **Thời điểm cập nhật**: `{now_iso}` | **Cơ chế**: Delta SHA-256 Bridge (ADR-0007)\n\n",
        "## 1. Trạng Thái Vận Hành\n",
        f"- **Antigravity**: `{'waiting_for_grok' if pending_grok else 'idle'}` (Đang chờ Grok: {len(pending_grok)} requests)",
        f"- **Grok**: `{'in_progress' if pending_grok else 'idle'}` (Đang chờ Antigravity: {len(pending_anti)} requests)\n\n",
        "## 2. Hàng Đợi Đang Chờ (Pending Queue)\n",
    ]
    lines.append("### ⏳ Grok cần xử lý:" if pending_grok else "### ✅ Grok: Không có yêu cầu tồn đọng.")
    for p in pending_grok[:5]:
        lines.append(f"- `{p}`")
    if pending_anti:
        lines.append("\n### ⏳ Antigravity cần xử lý:")
        for p in pending_anti[:5]:
            lines.append(f"- `{p}`")

    lines.extend([
        "\n## 3. Phán Quyết Gần Nhất (Recent Verdicts)\n",
        "| Tệp Phản Hồi | Phán Quyết (Verdict) | Điều Kiện | Tóm Tắt |",
        "|---|:---:|:---:|---|",
    ])
    for item in resps[:8]:
        v = item["verdict"]
        lines.append(f"| `{item['path'].name}` | **`{v.verdict}`** | {len(v.conditions)} | {v.summary[:50]}... |")

    atomic_write_text(summary_file, "\n".join(lines) + "\n")


def run_sync_cycle(
    peer_exchange_dir: Path,
    auto_gate: bool = False,
    auto_grok: bool = False,
) -> list[FileChange]:
    """Executes a single serialized observation and synchronization cycle.

    Args:
        peer_exchange_dir: Directory where peer exchange files reside.
        auto_gate: Whether to trigger peer implementation gate on new code.
        auto_grok: Whether to automatically invoke Grok CLI on new prompts.

    Returns:
        List of detected file changes in this cycle.
    """
    with _SYNC_MUTEX:
        cache_file = peer_exchange_dir / ".bridge_cache.json"
        status_file = peer_exchange_dir / "status.json"
        summary_file = peer_exchange_dir / "grok_live_summary.md"

        cache = load_cache(cache_file)
        changes, new_cache, registry = scan_peer_exchange(peer_exchange_dir, cache)

        if changes or not status_file.exists() or not summary_file.exists():
            pending_anti, pending_grok = compute_pending_queues(registry)
            update_status_json(status_file, registry, pending_anti, pending_grok)
            update_live_summary(summary_file, registry, pending_anti, pending_grok)
            save_cache(cache_file, new_cache)

            for change in changes:
                if auto_grok and change.role == "PROMPT_TO_GROK":
                    invoke_grok_cli(change.path)
                elif auto_gate and change.role == "GROK_IMPLEMENTATION":
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
    """Atomically publishes a peer exchange envelope and asynchronously syncs state.

    Args:
        envelope: PeerPromptEnvelope instance to serialize.
        body_text: Markdown body string following the front-matter.
        target_path: Destination file Path to write.
        on_publish_hook: Optional callback invoked immediately with target_path.
        auto_grok: Whether to automatically invoke Grok CLI on new prompts.

    Returns:
        Path to the written target file.
    """
    frontmatter = render_prompt_header(envelope)
    full_content = frontmatter + body_text.lstrip()
    atomic_write_text(target_path, full_content)

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


def _run_single_grok_attempt(
    cmd: list[str], prompt_path: Path, output_file: Path, timeout: float
) -> bool:
    """Executes a single invocation of grok CLI and verifies output verdict.

    Args:
        cmd: Command arguments list to execute.
        prompt_path: Source prompt file path.
        output_file: Target output file path to write result.
        timeout: Subprocess timeout in seconds.

    Returns:
        True if output contains a valid PeerVerdictBlock, False otherwise.
    """
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        if proc.returncode != 0 or not proc.stdout.strip():
            return False
        atomic_write_text(output_file, proc.stdout)
        verdict = parse_verdict_from_md(proc.stdout)
        return verdict is not None
    except Exception:
        return False


def invoke_grok_cli(
    prompt_path: Path,
    model: str | None = None,
    timeout: float = 180.0,
) -> bool:
    """Invokes Grok CLI with adaptive multi-tier fallback and high reasoning effort.

    Args:
        prompt_path: Path to prompt file containing PeerPromptEnvelope.
        model: Optional explicit model override.
        timeout: Subprocess execution timeout in seconds.

    Returns:
        True if response was successfully generated and verified, False otherwise.
    """
    content, _ = safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(content or "")
    if not envelope or not envelope.output_path:
        return False

    out_name = Path(envelope.output_path).name
    output_file = prompt_path.parent / out_name

    target_model = model or os.getenv("CCBA_GROK_MODEL")
    if target_model:
        cmd = [
            "grok", "-m", target_model, "--always-approve", "--no-subagents",
            "--reasoning-effort", "high", "--prompt-file", str(prompt_path),
        ]
        return _run_single_grok_attempt(cmd, prompt_path, output_file, timeout)

    for candidate in (DEFAULT_PRIMARY_AUDITOR_MODEL, DEFAULT_FALLBACK_AUDITOR_MODEL):
        cmd = [
            "grok", "-m", candidate, "--always-approve", "--no-subagents",
            "--reasoning-effort", "high", "--prompt-file", str(prompt_path),
        ]
        if _run_single_grok_attempt(cmd, prompt_path, output_file, timeout):
            return True
    return False
