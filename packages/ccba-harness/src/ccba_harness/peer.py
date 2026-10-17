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
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._mutex import FileMutexLock
from ._peer_telemetry import (
    _accumulate_verdict_telemetry,
)
from ._peer_telemetry import (
    extract_grok_session_telemetry as extract_grok_session_telemetry,
)
from ._peer_watchdog import (
    _VERDICT_ALIASES as _VERDICT_ALIASES,
)
from ._peer_watchdog import (
    DEFAULT_FALLBACK_AUDITOR_MODEL as DEFAULT_FALLBACK_AUDITOR_MODEL,
)
from ._peer_watchdog import (
    DEFAULT_PRIMARY_AUDITOR_MODEL as DEFAULT_PRIMARY_AUDITOR_MODEL,
)
from ._peer_watchdog import (
    NO_TOOLS_DISALLOW_LIST as NO_TOOLS_DISALLOW_LIST,
)
from ._peer_watchdog import (
    PROFILE_SPECS as PROFILE_SPECS,
)
from ._peer_watchdog import (  # noqa: F401
    READ_ONLY_DISALLOW_LIST as READ_ONLY_DISALLOW_LIST,
)
from ._peer_watchdog import (
    TIER_DEFAULT_MODELS as TIER_DEFAULT_MODELS,
)
from ._peer_watchdog import (
    VERDICT_LATTICE_RANK as VERDICT_LATTICE_RANK,
)
from ._peer_watchdog import (
    AgentIdentity as AgentIdentity,
)
from ._peer_watchdog import (
    CostMode as CostMode,
)
from ._peer_watchdog import (
    EffortType as EffortType,
)
from ._peer_watchdog import (
    ModelTier as ModelTier,
)
from ._peer_watchdog import (
    PeerExecutionProfile as PeerExecutionProfile,
)
from ._peer_watchdog import (
    RequestType as RequestType,
)
from ._peer_watchdog import (
    VerdictType as VerdictType,
)
from ._peer_watchdog import (
    _poll_grok_process_with_watchdog,
    _recover_verdict_from_chat_history,
)
from ._peer_watchdog import (  # noqa: F401
    _terminate_proc_tree as _terminate_proc_tree,
)
from ._peer_watchdog import (
    _unwrap_grok_json_stdout as _unwrap_grok_json_stdout,
)
from ._peer_watchdog import (  # noqa: F401
    inspect_session_liveness as inspect_session_liveness,
)
from .verifier import resolve_preset_commands, verify_patch_execution

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


class PatchReplacement(BaseModel):
    """Represents a single verbatim string replacement in a file."""

    model_config = ConfigDict(extra="forbid")

    old: str
    new: str


class FilePatch(BaseModel):
    """Represents an atomic patch target with SHA-256 pre-condition."""

    model_config = ConfigDict(extra="forbid")

    path: str
    blob_sha256: str
    replacements: list[PatchReplacement]


class AnchorPatchPayload(BaseModel):
    """Root container for Level-2 anchor-based code patches."""

    model_config = ConfigDict(extra="forbid")

    files: list[FilePatch]


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
    profile: PeerExecutionProfile | None = None
    max_turns: int | None = None
    target_files: list[str] = Field(default_factory=list)
    resume_session_id: str | None = None
    fork_session: bool | None = None


class PeerCondition(BaseModel):
    """A requirement or condition attached to a verdict."""

    model_config = ConfigDict(extra="ignore")

    id: str
    description: str
    blocking: bool = True
    source_profile: str | None = None
    source_profiles: list[str] = Field(default_factory=list)


class PeerVerdictTelemetry(BaseModel):
    """Execution telemetry and token provenance for peer interactions (ADR-0064)."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    primary_model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int = 0
    cached_read_tokens: int = 0
    total_tokens: int
    model_calls: int = 1
    turn_count: int = 1
    cost_usd: float = 0.0
    cost_mode: CostMode = "estimated"
    duration_seconds: float = 0.0
    degraded_reasoning: bool = False


class ProfileTelemetryItem(BaseModel):
    """Telemetry breakdown item for a single peer agent profile (ADR-0065)."""

    model_config = ConfigDict(extra="ignore")

    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cached_read_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0


class CombinedTelemetry(BaseModel):
    """Consolidated telemetry aggregated across multi-agent executions (ADR-0065)."""

    model_config = ConfigDict(extra="ignore")

    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cached_read_tokens: int = 0
    cost_usd: float = 0.0
    wall_seconds: float = 0.0
    sum_agent_seconds: float = 0.0
    cost_mode: CostMode = "exact"
    profile_breakdown: dict[str, ProfileTelemetryItem] = Field(default_factory=dict)


class PeerVerdictBlock(BaseModel):
    """Structured verdict issued by a peer agent in response to a prompt."""

    model_config = ConfigDict(extra="ignore")

    request_id: str
    verdict: VerdictType
    conditions: list[PeerCondition] = Field(default_factory=list)
    risk_score: int | None = Field(default=None, ge=1, le=5)
    effort: EffortType | None = None
    summary: str = ""
    telemetry: PeerVerdictTelemetry | CombinedTelemetry | None = None

    @field_validator("risk_score", mode="before")
    @classmethod
    def _normalize_risk_score(cls, v: Any) -> Any:
        if isinstance(v, float):
            if 0.0 <= v < 1.0:
                return max(1, min(5, int(round(v * 5)) or 1))
            if 1.0 <= v <= 5.0:
                return int(round(v))
        return v

    @field_validator("verdict", mode="before")
    @classmethod
    def _normalize_verdict(cls, v: Any) -> Any:
        if isinstance(v, str):
            cleaned = v.strip().upper().replace(" ", "_").replace("-", "_")
            return _VERDICT_ALIASES.get(cleaned, cleaned)
        return v

    @field_validator("conditions", mode="before")
    @classmethod
    def _normalize_conditions(cls, v: Any) -> list[Any]:
        if not isinstance(v, (list, tuple)):
            return []
        normalized: list[Any] = []
        for i, item in enumerate(v):
            if isinstance(item, str):
                normalized.append(
                    {"id": f"COND-{i + 1:02d}", "description": item, "blocking": True}
                )
            else:
                normalized.append(item)
        return normalized


class PeerConsensusReport(BaseModel):
    """Aggregated consensus report synthesized from multi-agent peer reviews (ADR-0065)."""

    model_config = ConfigDict(extra="ignore")

    request_id: str
    verdict: VerdictType
    risk_score: int = Field(default=1, ge=1, le=5)
    summary: str
    expected_profiles: list[str]
    completed_profiles: list[str]
    failed_profiles: list[str] = Field(default_factory=list)
    individual_verdicts: dict[str, PeerVerdictBlock] = Field(default_factory=dict)
    conditions: list[PeerCondition] = Field(default_factory=list)
    combined_telemetry: CombinedTelemetry | None = None
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


class AutoApplyResult(BaseModel):
    """Result of Level-3 autonomous loopback patch application and verification (ADR-0065)."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    success: bool
    gate_verdict: VerdictType
    rollback_proven: bool
    preimage_sha256: dict[str, str] = Field(default_factory=dict)
    report: Any = None
    summary: str = ""
    transaction_id: str = ""
    modified_files: list[str] = Field(default_factory=list)


def extract_frontmatter(md_content: str) -> tuple[dict[str, Any] | None, str]:
    """Extracts raw YAML frontmatter dictionary and remaining body from markdown content.

    Args:
        md_content: Raw markdown text possibly starting with YAML frontmatter.

    Returns:
        A tuple of (parsed_dict, body_text). If absent or invalid, returns (None, md_content).
    """
    if not md_content:
        return None, md_content

    content = md_content.lstrip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z0-9_-]*\r?\n", "", content)

    if not content.startswith("---"):
        return None, md_content
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return None, md_content
    yaml_text = match.group(1)
    end_pos = match.end()
    body = content[end_pos:]
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


def atomic_write_text(target: Path, content: str, max_retries: int = 3) -> None:
    """Writes text content to target file atomically using a temporary file with retry (ADR-0063 / ADR-0065).

    Args:
        target: Destination file path.
        content: Text string content to persist.
        max_retries: Retry attempts on transient OS lock errors (e.g. Windows file locking).
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target.with_suffix(f"{target.suffix}.tmp_{os.getpid()}_{time.time_ns()}")
    mode = None
    if target.exists():
        try:
            mode = target.stat().st_mode
        except OSError:
            pass
    try:
        temp_file.write_text(content, encoding="utf-8")
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


def atomic_write_bytes(target: Path, data: bytes, max_retries: int = 3) -> None:
    """Writes binary data to target file atomically using a temporary file with retry (ADR-0065).

    Args:
        target: Destination file path.
        data: Binary bytes content to persist verbatim.
        max_retries: Retry attempts on transient OS lock errors (e.g. Windows file locking).
    """
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
        or name.endswith(".gate.md")
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
    grok_resps.sort(key=lambda x: x.get("mtime", 0.0), reverse=True)
    top = grok_resps[0]
    verdict = top["verdict"]
    return {
        "request_id": verdict.request_id,
        "verdict": verdict.verdict,
        "blocking_conditions": len([c for c in verdict.conditions if c.blocking]),
        "output_path": top["path"].name,
        "summary": verdict.summary,
    }


def _aggregate_registry_telemetry(
    registry: dict[str, dict[str, Any]],
) -> tuple[int, float, dict[str, dict[str, Any]]]:
    """Aggregates token and cost telemetry across all registry verdict entries."""
    total_tokens = 0
    total_cost_usd = 0.0
    by_model: dict[str, dict[str, Any]] = {}
    for item in registry.values():
        v = item.get("verdict")
        if v and getattr(v, "telemetry", None):
            tok_delta, cost_delta = _accumulate_verdict_telemetry(v.telemetry, by_model)
            total_tokens += tok_delta
            total_cost_usd += cost_delta
    return total_tokens, total_cost_usd, by_model


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
    resps.sort(key=lambda x: x["mtime"], reverse=True)

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


def extract_anchor_payload(text: str) -> AnchorPatchPayload | None:
    """Extracts and validates an AnchorPatchPayload from raw markdown or JSON string."""
    if not text:
        return None
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw_json = match.group(1) if match else text.strip()
    try:
        data = json.loads(raw_json)
        return AnchorPatchPayload.model_validate(data)
    except Exception:
        return None


def _prepare_single_file_patch(
    root_resolved: Path,
    file_patch: Any,
    target_files_seen: set[Path],
) -> tuple[Path, str, str]:
    """Validates a single file patch and returns (target_file, original_text, new_text)."""
    target_file = (root_resolved / file_patch.path).resolve()
    if not target_file.is_relative_to(root_resolved):
        raise ValueError(f"Path traversal detected in patch: {file_patch.path}")
    if target_file in target_files_seen:
        raise ValueError(f"Payload contains duplicate target file: {file_patch.path}")
    target_files_seen.add(target_file)
    if not target_file.exists():
        raise ValueError(f"Target patch file does not exist: {file_patch.path}")
    if not target_file.is_file():
        raise ValueError(f"Target patch path is not a regular file: {file_patch.path}")

    raw_bytes = target_file.read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if actual_sha256.lower() != file_patch.blob_sha256.lower():
        raise ValueError(
            f"Anchor patch SHA-256 mismatch for {file_patch.path}: "
            f"expected {file_patch.blob_sha256}, got {actual_sha256}"
        )

    text = raw_bytes.decode("utf-8")
    new_text = text.replace("\r\n", "\n")
    for rep in file_patch.replacements:
        old_norm = rep.old.replace("\r\n", "\n")
        new_norm = rep.new.replace("\r\n", "\n")
        count = new_text.count(old_norm)
        if count == 0:
            raise ValueError(
                f"Target old anchor text not found in {file_patch.path}: '{old_norm[:50]}...'"
            )
        if count > 1:
            raise ValueError(
                f"Target old anchor text is not unique in {file_patch.path} (found {count} matches): '{old_norm[:50]}...'"
            )
        new_text = new_text.replace(old_norm, new_norm, 1)
    return target_file, text, new_text


def _commit_anchor_patch_writes(
    prepared_writes: list[tuple[Path, str, str]],
    backup: bool,
) -> list[Path]:
    """Commits prepared anchor patch writes atomically with rollback on write failure."""
    written_backups: dict[Path, str] = {}
    modified_paths: list[Path] = []
    try:
        for target_file, original_content, new_content in prepared_writes:
            written_backups[target_file] = original_content
            if backup:
                bak_file = target_file.with_suffix(target_file.suffix + ".bak")
                atomic_write_text(bak_file, original_content)
            atomic_write_text(target_file, new_content)
            modified_paths.append(target_file)
        return modified_paths
    except Exception as exc:
        rollback_errors: list[str] = []
        for failed_file, old_content in written_backups.items():
            try:
                atomic_write_text(failed_file, old_content)
            except Exception as r_err:
                rollback_errors.append(f"{failed_file.name}: {r_err}")
        err_msg = f"Transaction aborted during write phase: {exc}"
        if rollback_errors:
            err_msg += f" (Rollback errors: {'; '.join(rollback_errors)})"
        raise ValueError(err_msg) from exc


def apply_anchor_patch(
    root: Path,
    payload: AnchorPatchPayload | dict[str, Any],
    dry_run: bool = False,
    backup: bool = False,
) -> list[Path]:
    """Applies a Level-2 anchor patch payload atomically with SHA-256 pre-verification and rollback (ADR-0063)."""
    patch = AnchorPatchPayload.model_validate(payload) if isinstance(payload, dict) else payload
    root_resolved = root.resolve()
    target_files_seen: set[Path] = set()
    prepared_writes = [
        _prepare_single_file_patch(root_resolved, fp, target_files_seen) for fp in patch.files
    ]
    if dry_run:
        return [target_file for target_file, _, _ in prepared_writes]
    return _commit_anchor_patch_writes(prepared_writes, backup)


def get_git_toplevel(cwd: Path | str | None = None) -> Path | None:
    """Resolves the git repository top-level root directory (COND-LEVEL3-ROOT)."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=True,
        )
        top = res.stdout.strip()
        if top:
            return Path(top).resolve()
    except Exception:
        pass
    return None


def _recover_single_anchor_txn(txn_path: Path, backup_dir: Path) -> bool:
    """Restores a single interrupted anchor transaction directory if uncommitted."""
    journal_file = txn_path / "journal.json"
    commit_marker = txn_path / "commit.marker"
    aborted_marker = txn_path / "aborted.marker"
    if not (journal_file.exists() and not commit_marker.exists() and not aborted_marker.exists()):
        return False
    try:
        journal_data = json.loads(journal_file.read_text(encoding="utf-8"))
        target_root = Path(journal_data.get("root", str(backup_dir.parent.parent.parent))).resolve()
        for f_entry in journal_data.get("files", []):
            rel_p = f_entry.get("path")
            backup_fname = f_entry.get("backup_filename")
            if not rel_p or not backup_fname:
                continue
            backup_file = txn_path / backup_fname
            if backup_file.exists():
                atomic_write_bytes((target_root / rel_p).resolve(), backup_file.read_bytes())
        aborted_marker.write_text(
            f"Recovered at {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def recover_pending_anchor_transactions(
    backup_dir: Path | None = None,
    root: Path | None = None,
) -> list[str]:
    """Scans and recovers interrupted anchor transactions from disk pre-images (COND-LEVEL3-TXN)."""
    if backup_dir is None:
        effective_root = root or get_git_toplevel() or Path.cwd()
        backup_dir = effective_root / ".md" / "backups" / "anchor-txn"
    if not backup_dir.exists() or not backup_dir.is_dir():
        return []
    recovered_txns: list[str] = []
    for txn_path in sorted(backup_dir.iterdir(), key=lambda p: p.name):
        if not txn_path.is_dir() or txn_path.name.startswith("."):
            continue
        if _recover_single_anchor_txn(txn_path, backup_dir):
            recovered_txns.append(txn_path.name)
    return recovered_txns


def _resolve_auto_apply_root(root: Path | str | None) -> Path:
    """Resolves and validates workspace git root for auto_apply_and_verify_patch."""
    if root is None:
        effective_root = get_git_toplevel()
        if effective_root is None:
            raise ValueError(
                "Root directory resolution failed: current working directory is not inside a git repository."
            )
        return effective_root
    effective_root = Path(root).resolve()
    if get_git_toplevel(effective_root) is None:
        raise ValueError(f"Specified root is not inside a git repository: {effective_root}")
    return effective_root


def _journal_anchor_preimages(
    effective_root: Path,
    patch: AnchorPatchPayload,
    txn_dir: Path,
    txn_id: str,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Validates patch in dry_run mode and records pre-image raw bytes into txn_dir."""
    preimage_sha256: dict[str, str] = {}
    journal_files: list[dict[str, Any]] = []
    txn_dir.mkdir(parents=True, exist_ok=False)
    try:
        apply_anchor_patch(root=effective_root, payload=patch, dry_run=True, backup=False)
        for idx, file_patch in enumerate(patch.files):
            target_file = (effective_root / file_patch.path).resolve()
            raw_bytes = target_file.read_bytes()
            current_sha = hashlib.sha256(raw_bytes).hexdigest()
            preimage_sha256[file_patch.path] = current_sha
            backup_filename = f"file_{idx}.bin"
            (txn_dir / backup_filename).write_bytes(raw_bytes)
            journal_files.append(
                {
                    "index": idx,
                    "path": file_patch.path,
                    "blob_sha256": current_sha,
                    "backup_filename": backup_filename,
                }
            )
        journal_data = {
            "txn_id": txn_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "root": str(effective_root),
            "files": journal_files,
        }
        atomic_write_text(txn_dir / "journal.json", json.dumps(journal_data, indent=2))
        return preimage_sha256, journal_files
    except Exception as exc:
        shutil.rmtree(txn_dir, ignore_errors=True)
        raise ValueError(f"Pre-apply validation failed: {exc}") from exc


def _rollback_from_journal(
    effective_root: Path,
    txn_dir: Path,
    journal_files: list[dict[str, Any]],
    verify_sha: bool = True,
) -> bool:
    """Restores pre-image raw bytes from txn_dir journal and optionally verifies SHA-256."""
    rollback_ok = True
    for f_entry in journal_files:
        try:
            t_file = (effective_root / f_entry["path"]).resolve()
            b_file = txn_dir / f_entry["backup_filename"]
            atomic_write_bytes(t_file, b_file.read_bytes())
            if verify_sha:
                restored_sha = hashlib.sha256(t_file.read_bytes()).hexdigest()
                if restored_sha.lower() != f_entry["blob_sha256"].lower():
                    rollback_ok = False
        except Exception:
            rollback_ok = False
    return rollback_ok


def _finalize_auto_apply_decision(
    root: Path,
    txn_dir: Path,
    txn_id: str,
    preset: str,
    keep_backups: bool,
    mod_paths: list[Path],
    preimage_sha: dict[str, str],
    j_files: list[dict[str, Any]],
    v_rep: Any,
) -> AutoApplyResult:
    """Finalizes commit marker or executes verified byte rollback after verification gate."""
    rel_mod = [str(p.relative_to(root)) if p.is_relative_to(root) else str(p) for p in mod_paths]
    common = {
        "preimage_sha256": preimage_sha,
        "report": v_rep,
        "transaction_id": txn_id,
        "modified_files": rel_mod,
    }
    if v_rep.all_passed:
        (txn_dir / "commit.marker").write_text("committed", encoding="utf-8")
        if not keep_backups:
            shutil.rmtree(txn_dir, ignore_errors=True)
        msg = f"Patch successfully applied and verified with preset '{preset}'."
        return AutoApplyResult(
            success=True, gate_verdict="GATE_PASS", rollback_proven=False, summary=msg, **common
        )

    rb_ok = _rollback_from_journal(root, txn_dir, j_files, True)
    if rb_ok:
        (txn_dir / "rollback.marker").write_text("clean", encoding="utf-8")
        if not keep_backups:
            shutil.rmtree(txn_dir, ignore_errors=True)
    tail = (
        "Workspace rolled back cleanly."
        if rb_ok
        else f"AND byte rollback verification mismatch! Transaction preserved at {txn_dir}."
    )
    msg = (
        f"Verification failed ({v_rep.failed_count}/{v_rep.total_commands} commands failed). {tail}"
    )
    return AutoApplyResult(
        success=False, gate_verdict="GATE_FAIL", rollback_proven=rb_ok, summary=msg, **common
    )


def _execute_locked_patch_transaction(
    root: Path,
    patch: AnchorPatchPayload,
    txn_dir: Path,
    txn_id: str,
    preset: str,
    timeout: float,
    keep_backups: bool,
    extra_commands: Sequence[str] | None,
) -> AutoApplyResult:
    """Executes journaled patch commit, verification gate, and rollback under FileMutexLock."""
    preimage_sha, j_files = _journal_anchor_preimages(root, patch, txn_dir, txn_id)
    try:
        mod_paths = apply_anchor_patch(root=root, payload=patch, dry_run=False, backup=False)
    except Exception as exc:
        rb_ok = _rollback_from_journal(root, txn_dir, j_files, False)
        if rb_ok and not keep_backups:
            shutil.rmtree(txn_dir, ignore_errors=True)
        msg = f"Disk commit aborted: {exc}. Workspace rolled back {'cleanly' if rb_ok else 'WITH ERRORS'}."
        return AutoApplyResult(
            success=False,
            gate_verdict="GATE_FAIL",
            rollback_proven=rb_ok,
            preimage_sha256=preimage_sha,
            summary=msg,
            transaction_id=txn_id,
        )

    cmds = list(extra_commands or [])
    if preset == "ci":
        cmds.append(f"{sys.executable} -m pytest packages/ccba-harness/tests/test_peer*.py -q")
    try:
        v_rep = verify_patch_execution(
            preset=preset, cwd=root, timeout=timeout, commands=cmds or None
        )
    except Exception as v_err:
        rb_ok = _rollback_from_journal(root, txn_dir, j_files, True)
        msg = f"Verification execution crashed: {v_err}. Workspace rolled back {'cleanly' if rb_ok else 'WITH ERRORS'}."
        return AutoApplyResult(
            success=False,
            gate_verdict="GATE_FAIL",
            rollback_proven=rb_ok,
            preimage_sha256=preimage_sha,
            summary=msg,
            transaction_id=txn_id,
        )
    return _finalize_auto_apply_decision(
        root, txn_dir, txn_id, preset, keep_backups, mod_paths, preimage_sha, j_files, v_rep
    )


def auto_apply_and_verify_patch(
    root: Path | str | None,
    patch_payload: AnchorPatchPayload | dict[str, Any],
    verify_preset: str = "ci",
    timeout: float = 180.0,
    keep_backups: bool = False,
    extra_commands: Sequence[str] | None = None,
) -> AutoApplyResult:
    """Atomically applies anchor patch with pre-image byte journaling, verification, and rollback (ADR-0065)."""
    effective_root = _resolve_auto_apply_root(root)
    patch = (
        AnchorPatchPayload.model_validate(patch_payload)
        if isinstance(patch_payload, dict)
        else patch_payload
    )
    if not patch.files:
        raise ValueError("Anchor patch payload contains no files to patch.")
    resolve_preset_commands(preset=verify_preset)
    recover_pending_anchor_transactions(root=effective_root)

    backup_base = effective_root / ".md" / "backups" / "anchor-txn"
    backup_base.mkdir(parents=True, exist_ok=True)
    txn_id = f"txn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    txn_dir = backup_base / txn_id
    if txn_dir.exists():
        raise ValueError(f"Transaction backup directory already exists: {txn_dir}")
    for fp in patch.files:
        t_path = (effective_root / fp.path).resolve()
        if t_path == txn_dir.resolve() or txn_dir.resolve().is_relative_to(t_path):
            raise ValueError(f"Payload target collides with transaction directory: {fp.path}")

    with FileMutexLock(backup_base / ".lock"):
        return _execute_locked_patch_transaction(
            effective_root,
            patch,
            txn_dir,
            txn_id,
            verify_preset,
            timeout,
            keep_backups,
            extra_commands,
        )


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
) -> bool:
    """Validates parsed verdict or anchor patch, attaches session telemetry, and writes output_file."""
    verdict = parse_verdict_from_md(stdout_text)
    if verdict is None:
        if extract_anchor_payload(stdout_text) is None:
            return False
        prompt_content, _ = safe_read_and_hash(prompt_path)
        envelope = parse_envelope_from_md(prompt_content or "")
        verdict = PeerVerdictBlock(
            request_id=envelope.request_id if envelope else "req-auto",
            verdict="HANDOFF",
            summary="Fast-path anchor patch generated; pending orchestrator apply and verification.",
        )
        stdout_text = render_verdict_header(verdict) + "\n" + stdout_text.lstrip()

    if session_id:
        prompt_content, _ = safe_read_and_hash(prompt_path)
        telemetry = extract_grok_session_telemetry(
            session_id=session_id,
            timeout=3.0,
            fallback_prompt_text=prompt_content,
            fallback_resp_text=stdout_text,
            duration_seconds=duration,
            fallback_model=candidate_model,
            expected_reasoning_effort=expected_reasoning_effort,
        )
        if telemetry:
            verdict.telemetry = telemetry
            _, body = extract_frontmatter(stdout_text)
            stdout_text = render_verdict_header(verdict) + body.lstrip()

    atomic_write_text(output_file, stdout_text)
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
) -> bool:
    """Executes a single invocation of grok CLI and verifies output verdict (ADR-0064 / ADR-0065)."""
    start_time = time.time()
    try:
        stdout_text, ok = _spawn_and_poll_grok(cmd, output_file, start_time, timeout, session_id)
        if not ok:
            return False
        stdout_text, json_sid, _ = _unwrap_grok_json_stdout(stdout_text)
        session_id = session_id or json_sid
        if (not stdout_text.strip() or parse_verdict_from_md(stdout_text) is None) and session_id:
            stdout_text = (
                _recover_verdict_from_chat_history(session_id, parse_verdict_from_md) or stdout_text
            )
        if not stdout_text.strip():
            return False
        return _finalize_grok_verdict_and_telemetry(
            stdout_text,
            prompt_path,
            output_file,
            time.time() - start_time,
            session_id,
            candidate_model,
            expected_reasoning_effort,
        )
    except Exception:
        return False


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
    envelope: PeerPromptEnvelope,
    max_turns: int | None,
    timeout: float | None,
    no_tools: bool,
    resume_session_id: str | None,
    fork_session: bool | None,
) -> dict[str, Any]:
    """Resolves effective CLI options from profile spec, prompt envelope, and caller overrides."""
    eff_turns = (
        max_turns
        if max_turns is not None
        else (envelope.max_turns if envelope.max_turns is not None else spec.get("max_turns"))
    )
    tools, disallowed, deny = spec.get("tools"), spec.get("disallowed_tools"), spec.get("deny")
    if no_tools:
        tools, disallowed, deny = None, list(NO_TOOLS_DISALLOW_LIST), ["*"]
        if max_turns is None and (eff_turns is None or eff_turns > 3):
            eff_turns = 3
    eff_resume = resume_session_id or envelope.resume_session_id
    eff_fork = (
        fork_session
        if fork_session is not None
        else (
            envelope.fork_session
            if envelope.fork_session is not None
            else bool(spec.get("fork_session", bool(eff_resume)))
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


def _dispatch_grok_candidate(
    prompt_path: Path,
    output_file: Path,
    candidate: str,
    opts: dict[str, Any],
    worktree: bool,
) -> bool:
    """Builds CLI command for a single candidate model and executes _run_single_grok_attempt."""
    cand_sid = str(uuid.uuid4())
    cmd = build_grok_cmd(
        prompt_path=prompt_path,
        model=candidate,
        max_turns=opts["max_turns"],
        tools=opts["tools"],
        disallowed_tools=opts["disallowed_tools"],
        deny=opts["deny"],
        reasoning_effort=opts["reasoning_effort"],
        output_format=opts["output_format"],
        worktree=worktree,
        session_id=cand_sid,
        system_prompt=opts["system_prompt"],
        resume_session_id=opts["resume_session_id"],
        fork_session=opts["fork_session"],
        verbatim=opts["verbatim"],
        disable_web_search=opts["disable_web_search"],
    )
    eff_sid = (
        cand_sid
        if (not opts["resume_session_id"] or opts["fork_session"])
        else opts["resume_session_id"]
    )
    return _run_single_grok_attempt(
        cmd,
        prompt_path,
        output_file,
        opts["timeout"],
        session_id=eff_sid,
        candidate_model=candidate,
        expected_reasoning_effort=opts["reasoning_effort"],
    )


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
) -> bool:
    """Invokes Grok CLI with Level-2 execution profile mapping and budget guardrails (ADR-0063 / ADR-0064)."""
    content, _ = safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(content or "")
    if not envelope or not envelope.output_path:
        return False

    output_file = prompt_path.parent / Path(envelope.output_path).name
    default_spec: dict[str, Any] = {
        "model": DEFAULT_PRIMARY_AUDITOR_MODEL,
        "fallback_model": DEFAULT_FALLBACK_AUDITOR_MODEL,
        "max_turns": 12,
        "tools": None,
        "disallowed_tools": ["spawn_subagent"],
        "reasoning_effort": "xhigh",
        "timeout": 180.0,
    }
    spec = PROFILE_SPECS.get(str(profile or envelope.profile), default_spec)
    opts = _resolve_grok_profile_options(
        spec, envelope, max_turns, timeout, no_tools, resume_session_id, fork_session
    )
    return any(
        _dispatch_grok_candidate(prompt_path, output_file, cand, opts, worktree)
        for cand in _resolve_target_models(model, tier, spec)
    )


def _merge_profile_conditions(
    comp_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
) -> list[PeerCondition]:
    """Deduplicates and OR-merges blocking conditions across completed profiles."""
    consolidated: list[PeerCondition] = []
    seen_descs: dict[str, PeerCondition] = {}
    for prof in comp_profiles:
        for cond in verdicts[prof].conditions:
            key = cond.description.strip().lower()
            if key in seen_descs:
                seen_descs[key].blocking = seen_descs[key].blocking or cond.blocking
                if prof not in seen_descs[key].source_profiles:
                    seen_descs[key].source_profiles.append(prof)
            else:
                new_c = PeerCondition(
                    id=cond.id,
                    description=cond.description,
                    blocking=cond.blocking,
                    source_profile=prof,
                    source_profiles=[prof],
                )
                seen_descs[key] = new_c
                consolidated.append(new_c)
    return consolidated


def _consolidate_peer_conditions(
    comp_profiles: list[str],
    failed_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
) -> list[PeerCondition]:
    """Consolidates conditions with deterministic ordering, quorum failure, and degraded-reasoning checks."""
    consolidated = _merge_profile_conditions(comp_profiles, verdicts)
    if failed_profiles:
        msg = f"Missing peer review from profiles: {', '.join(failed_profiles)}"
        consolidated.append(
            PeerCondition(
                id="COND-QUORUM-FAIL",
                description=msg,
                blocking=True,
                source_profile="orchestrator",
                source_profiles=["orchestrator"],
            )
        )
    degraded = [
        p
        for p in comp_profiles
        if isinstance(verdicts[p].telemetry, PeerVerdictTelemetry)
        and verdicts[p].telemetry.degraded_reasoning  # type: ignore[union-attr]
    ]
    if degraded:
        msg = f"High/xhigh reasoning profile returned 0 reasoning_tokens (silent reasoning degradation in: {', '.join(degraded)})."
        consolidated.append(
            PeerCondition(
                id="COND-DEGRADED-REASONING",
                description=msg,
                blocking=True,
                source_profile="telemetry",
                source_profiles=degraded,
            )
        )
    return consolidated


def _consolidate_peer_telemetry(
    comp_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
    duration_seconds: float,
) -> CombinedTelemetry | None:
    """Consolidates profile telemetry into CombinedTelemetry without failing consensus synthesis."""
    try:
        agg = {"total": 0, "inp": 0, "out": 0, "rsn": 0, "cached": 0}
        cost_usd, sum_secs, all_exact, has_any = 0.0, 0.0, True, False
        breakdown: dict[str, ProfileTelemetryItem] = {}
        for prof in comp_profiles:
            tel = verdicts[prof].telemetry
            if isinstance(tel, PeerVerdictTelemetry):
                has_any = True
                agg["total"] += tel.total_tokens or 0
                agg["inp"] += tel.input_tokens or 0
                agg["out"] += tel.output_tokens or 0
                agg["rsn"] += tel.reasoning_tokens or 0
                agg["cached"] += tel.cached_read_tokens or 0
                cost_usd += tel.cost_usd or 0.0
                sum_secs += tel.duration_seconds or 0.0
                all_exact = all_exact and (tel.cost_mode == "exact")
                breakdown[prof] = ProfileTelemetryItem(
                    model=tel.primary_model,
                    input_tokens=tel.input_tokens or 0,
                    output_tokens=tel.output_tokens or 0,
                    reasoning_tokens=tel.reasoning_tokens or 0,
                    cached_read_tokens=tel.cached_read_tokens or 0,
                    total_tokens=tel.total_tokens or 0,
                    cost_usd=round(tel.cost_usd or 0.0, 4),
                    duration_seconds=round(tel.duration_seconds or 0.0, 2),
                )
            else:
                all_exact = False
        if not has_any:
            return None
        return CombinedTelemetry(
            total_tokens=agg["total"],
            input_tokens=agg["inp"],
            output_tokens=agg["out"],
            reasoning_tokens=agg["rsn"],
            cached_read_tokens=agg["cached"],
            cost_usd=round(cost_usd, 4),
            wall_seconds=round(duration_seconds, 2),
            sum_agent_seconds=round(sum_secs, 2),
            cost_mode="exact" if all_exact else "estimated",
            profile_breakdown=breakdown,
        )
    except Exception:
        return None


def _resolve_baseline_consensus_verdict(
    comp_profiles: list[str],
    failed_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
) -> VerdictType:
    """Computes baseline consensus verdict using strict lattice rank and quorum rules."""
    completed_verdicts = [verdicts[p].verdict for p in comp_profiles]
    if not completed_verdicts:
        return "HANDOFF"
    completed_max = max(completed_verdicts, key=lambda t: VERDICT_LATTICE_RANK.get(t, 0))
    handoff_rank = VERDICT_LATTICE_RANK.get("HANDOFF", 70)
    if failed_profiles and VERDICT_LATTICE_RANK.get(completed_max, 0) < handoff_rank:
        return "HANDOFF"
    return completed_max


def synthesize_verdicts(
    request_id: str,
    verdicts: dict[str, PeerVerdictBlock],
    expected_profiles: Sequence[str] | None = None,
    duration_seconds: float = 0.0,
) -> PeerConsensusReport:
    """Synthesizes multiple peer verdicts into a unified deterministic consensus report (ADR-0065)."""
    if not verdicts and not expected_profiles:
        raise ValueError(
            "Cannot synthesize consensus from empty verdicts and empty expected profiles."
        )
    exp = list(expected_profiles) if expected_profiles is not None else list(verdicts.keys())
    comp = [p for p in exp if p in verdicts]
    failed = [p for p in exp if p not in verdicts]
    pass_set = {"APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS", "APPROVE_WITH_RESERVATIONS"}

    c_verdict = _resolve_baseline_consensus_verdict(comp, failed, verdicts)
    conds = _consolidate_peer_conditions(comp, failed, verdicts)
    valid_risks = [r for p in comp if (r := verdicts[p].risk_score) is not None]
    c_risk = max(valid_risks) if valid_risks else 1
    if c_verdict in pass_set and (any(c.blocking for c in conds) or c_risk >= 4):
        c_verdict = "APPROVE_WITH_CONDITIONS"

    lines = [
        f"Consensus Verdict: **{c_verdict}** (Risk Score: {c_risk}/5).",
        f"Quorum: {len(comp)}/{len(exp)} completed.",
    ]
    if failed:
        lines.append(f"Failed Profiles: {', '.join(failed)}.")
    lines.extend(f"- **{p}** ({verdicts[p].verdict}): {verdicts[p].summary}" for p in comp)
    return PeerConsensusReport(
        request_id=request_id,
        verdict=c_verdict,
        risk_score=c_risk,
        summary="\n".join(lines),
        expected_profiles=exp,
        completed_profiles=comp,
        failed_profiles=failed,
        individual_verdicts=verdicts,
        conditions=conds,
        combined_telemetry=_consolidate_peer_telemetry(comp, verdicts, duration_seconds),
    )


def render_consensus_report_markdown(report: PeerConsensusReport) -> str:
    """Renders a complete markdown document for a consensus report with standard frontmatter."""
    fm_payload: dict[str, Any] = {
        "request_id": report.request_id,
        "verdict": report.verdict,
        "risk_score": report.risk_score,
        "summary": report.summary,
        "profiles": report.completed_profiles,
        "expected_profiles": report.expected_profiles,
        "failed_profiles": report.failed_profiles,
        "conditions": [c.model_dump(exclude_none=True) for c in report.conditions],
    }
    if report.combined_telemetry:
        fm_payload["telemetry"] = report.combined_telemetry.model_dump(exclude_none=True)
    header = f"---\n{yaml.dump(fm_payload, sort_keys=False, allow_unicode=True)}---\n"

    body = [
        f"# 🤝 Multi-Agent Peer Consensus Report: `{report.request_id}`\n",
        f"- **Consensus Verdict**: `{report.verdict}`",
        f"- **Consolidated Risk Score**: `{report.risk_score}/5`",
        f"- **Quorum**: `{len(report.completed_profiles)}/{len(report.expected_profiles)}` profiles completed\n",
        "## 1. Executive Summary\n",
        report.summary,
        "\n## 2. Consolidated Conditions\n",
    ]
    for c in report.conditions or []:
        tag = "🔴 [BLOCKING]" if c.blocking else "🟡 [ADVISORY]"
        srcs = (
            ", ".join(c.source_profiles) if c.source_profiles else (c.source_profile or "unknown")
        )
        body.append(f"- **{c.id}** {tag} ({srcs}): {c.description}")
    if not report.conditions:
        body.append("*(No conditions attached)*")
    body.append("\n## 3. Individual Profile Verdicts\n")
    for prof, vb in report.individual_verdicts.items():
        body.append(
            f"### Profile: `{prof}`\n- **Verdict**: `{vb.verdict}` (Risk: `{vb.risk_score or 'N/A'}`)\n- **Summary**: {vb.summary}\n"
        )
    if report.combined_telemetry:
        t = report.combined_telemetry
        body.append(
            f"## 4. Telemetry & Cost Provenance\n\n- **Total Tokens**: {t.total_tokens:,} (Input: {t.input_tokens:,}, Output: {t.output_tokens:,}, Reasoning: {t.reasoning_tokens:,})\n- **Total Cost**: ${t.cost_usd:.4f} (mode: `{t.cost_mode}`)\n- **Duration**: Wall clock `{t.wall_seconds}s` | Sum agent time `{t.sum_agent_seconds}s`\n"
        )
    return header + "\n".join(body) + "\n"


def _run_co_review_workers(
    tasks: list[tuple[str, Path, Path]],
    max_workers: int,
    timeout: float | None,
    worktree: bool,
) -> dict[str, PeerVerdictBlock]:
    """Dispatches co-review profile tasks in parallel via ThreadPoolExecutor."""

    def _worker(item: tuple[str, Path, Path]) -> tuple[str, PeerVerdictBlock | None]:
        p_name, p_prompt, p_out = item
        spec = PROFILE_SPECS.get(p_name, {})
        ok = invoke_grok_cli(
            prompt_path=p_prompt,
            model=spec.get("model"),
            profile=p_name,
            timeout=timeout if timeout is not None else spec.get("timeout"),
            worktree=worktree,
        )
        if not ok or not p_out.exists():
            return p_name, None
        out_str, _ = safe_read_and_hash(p_out)
        return p_name, parse_verdict_from_md(out_str or "")

    verdicts: dict[str, PeerVerdictBlock] = {}
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
        for fut in [pool.submit(_worker, t) for t in tasks]:
            try:
                p_name, vb = fut.result()
                if vb is not None:
                    verdicts[p_name] = vb
            except Exception:
                pass
    return verdicts


def _prepare_co_review_tasks(
    profiles: Sequence[str],
    envelope: PeerPromptEnvelope,
    content: str,
    temp_dir: Path,
) -> list[tuple[str, Path, Path]]:
    """Writes isolated per-profile prompt files inside temp_dir and returns worker task tuples."""
    tasks: list[tuple[str, Path, Path]] = []
    _, body = extract_frontmatter(content)
    for prof in profiles:
        prof_prompt = temp_dir / f"prompt_{prof}.md"
        prof_out_name = f"grok_{prof}.md"
        prof_env = envelope.model_copy()
        prof_env.profile = prof  # type: ignore[assignment]
        prof_env.output_path = prof_out_name
        atomic_write_text(prof_prompt, render_prompt_header(prof_env) + body.lstrip())
        tasks.append((prof, prof_prompt, temp_dir / prof_out_name))
    return tasks


def orchestrate_peer_co_review(
    prompt_path: Path,
    profiles: Sequence[str] = ("code_review", "arch_audit"),
    output_file: Path | None = None,
    max_workers: int | None = None,
    timeout: float | None = None,
    worktree: bool = False,
) -> PeerConsensusReport | None:
    """Orchestrates multi-agent co-review execution in parallel threads with isolated outputs (ADR-0065)."""
    for prof in profiles:
        if not re.match(r"^[a-z0-9_]{1,32}$", prof):
            raise ValueError(f"Invalid profile name '{prof}': must match ^[a-z0-9_]{{1,32}}$")
        if prof not in PROFILE_SPECS:
            raise ValueError(
                f"Unknown execution profile '{prof}': must be one of {sorted(PROFILE_SPECS.keys())}"
            )

    content, _ = safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(content or "")
    if not envelope:
        return None

    temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"peer_co_review_{envelope.request_id[:8]}_")
    temp_dir = Path(temp_dir_obj.name)
    try:
        try:
            os.chmod(temp_dir, 0o700)
        except Exception:
            pass
        start_time = time.time()
        tasks = _prepare_co_review_tasks(profiles, envelope, content or "", temp_dir)
        workers_count = max_workers if max_workers is not None else min(len(profiles), 4)
        verdicts = _run_co_review_workers(tasks, workers_count, timeout, worktree)
        report = synthesize_verdicts(
            request_id=envelope.request_id,
            verdicts=verdicts,
            expected_profiles=profiles,
            duration_seconds=time.time() - start_time,
        )
        final_out = output_file or (
            prompt_path.parent / f"grok_consensus_{prompt_path.stem.replace('prompt_', '')}.md"
        )
        atomic_write_text(final_out, render_consensus_report_markdown(report))
        return report
    finally:
        temp_dir_obj.cleanup()
