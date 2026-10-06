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
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Literal, NamedTuple

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._mutex import FileMutexLock
from .verifier import resolve_preset_commands, verify_patch_execution

AgentIdentity = Literal["antigravity", "grok"]
PeerExecutionProfile = Literal[
    "audit_plan",
    "agentic_code",
    "patch_fast",
    "code_review",
    "arch_audit",
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

VERDICT_LATTICE_RANK: dict[VerdictType, int] = {
    # Blocker tokens (highest rank)
    "REJECT": 100,
    "REJECT_PLAN": 95,
    "GATE_FAIL": 90,
    # Revision required
    "REVISE_PLAN": 80,
    # Incomplete review / Handoff
    "HANDOFF": 70,
    # Conditional pass
    "APPROVE_WITH_CONDITIONS": 60,
    "APPROVE_WITH_RESERVATIONS": 55,
    # Clean pass tokens
    "APPROVE_PLAN": 40,
    "FINAL_ACCEPT": 35,
    "GATE_PASS": 30,
    "APPROVE": 20,
}

EffortType = Literal["XS", "S", "M", "L", "XL"]

DEFAULT_PRIMARY_AUDITOR_MODEL = "grok-4.7"  # ccba:allow-raw-model
DEFAULT_FALLBACK_AUDITOR_MODEL = "gemini-38-flash"  # ccba:allow-raw-model

TIER_DEFAULT_MODELS: dict[str, str] = {
    "local": "qwen-local",  # ccba:allow-raw-model
    "gateway": "gemini-38-flash",  # ccba:allow-raw-model
    "cloud": "grok-4.7",  # ccba:allow-raw-model
}

PROFILE_SPECS: dict[str, dict[str, Any]] = {
    "audit_plan": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 12,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": [
            "run_terminal_command",
            "search_replace",
            "write_file",
            "spawn_subagent",
        ],
        "reasoning_effort": "xhigh",
        "timeout": 900.0,
    },
    "agentic_code": {
        "model": "grok-4.7-build-fast",  # ccba:allow-raw-model
        "fallback_model": "claude-sonnet-4-6",  # ccba:allow-raw-model
        "max_turns": 8,
        "tools": ["read_file", "search_replace", "list_dir"],
        "disallowed_tools": ["spawn_subagent", "run_terminal_command"],
        "reasoning_effort": "high",
        "timeout": 600.0,
    },
    "patch_fast": {
        "model": "qwen-local",  # ccba:allow-raw-model
        "fallback_model": "grok-4.7-build-fast",  # ccba:allow-raw-model
        "max_turns": 1,
        "tools": None,
        "disallowed_tools": [
            "read_file",
            "grep",
            "list_dir",
            "run_terminal_command",
            "search_replace",
            "write_file",
            "spawn_subagent",
        ],
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
        "disallowed_tools": [
            "run_terminal_command",
            "search_replace",
            "write_file",
            "spawn_subagent",
        ],
        "reasoning_effort": "high",
        "system_prompt": (
            "You are an expert peer code reviewer. You MUST start your response immediately with "
            "YAML frontmatter enclosed in '---' containing request_id, verdict, risk_score, conditions, "
            "and summary, followed by your structured code review findings."
        ),
        "timeout": 300.0,
    },
    "arch_audit": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 8,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": [
            "run_terminal_command",
            "search_replace",
            "write_file",
            "spawn_subagent",
        ],
        "reasoning_effort": "xhigh",
        "system_prompt": (
            "You are an expert software and system architecture auditor. You MUST start your response "
            "immediately with YAML frontmatter enclosed in '---' containing request_id, verdict, risk_score, "
            "conditions, and summary, followed by your architectural audit findings."
        ),
        "timeout": 600.0,
    },
}

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


class PeerCondition(BaseModel):
    """A requirement or condition attached to a verdict."""

    model_config = ConfigDict(extra="ignore")

    id: str
    description: str
    blocking: bool = True
    source_profile: str | None = None
    source_profiles: list[str] = Field(default_factory=list)


CostMode = Literal["exact", "estimated", "unknown"]


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


class PeerVerdictBlock(BaseModel):
    """Structured verdict issued by a peer agent in response to a prompt."""

    model_config = ConfigDict(extra="ignore")

    request_id: str
    verdict: VerdictType
    conditions: list[PeerCondition] = Field(default_factory=list)
    risk_score: int | None = Field(default=None, ge=1, le=5)
    effort: EffortType | None = None
    summary: str = ""
    telemetry: PeerVerdictTelemetry | None = None

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
    body = content[match.end() :]
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
    total_tokens = 0
    total_cost_usd = 0.0
    by_model: dict[str, dict[str, Any]] = {}
    for item in registry.values():
        v = item.get("verdict")
        if v and getattr(v, "telemetry", None):
            t = v.telemetry
            total_tokens += t.total_tokens
            total_cost_usd += t.cost_usd
            m = t.primary_model
            if m not in by_model:
                by_model[m] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
            by_model[m]["calls"] += 1
            by_model[m]["tokens"] += t.total_tokens
            by_model[m]["cost_usd"] = round(by_model[m]["cost_usd"] + t.cost_usd, 4)

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
                [
                    i
                    for i in registry.values()
                    if i["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION")
                ]
            ),
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
    """Renders a concise, lightweight summary (< 5 KB) to grok_live_summary.md.

    Args:
        summary_file: Target grok_live_summary.md Path.
        registry: Metadata registry of scanned files.
        pending_anti: List of file names pending for Antigravity.
        pending_grok: List of file names pending for Grok.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    resps = [
        i
        for i in registry.values()
        if i["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and i["verdict"]
    ]
    resps.sort(key=lambda x: x["mtime"], reverse=True)

    lines = [
        "# ⚡ Grok & Antigravity Live Peer Summary\n",
        f"> **Thời điểm cập nhật**: `{now_iso}` | **Cơ chế**: Delta SHA-256 Bridge (ADR-0063)\n\n",
        "## 1. Trạng Thái Vận Hành\n",
        f"- **Antigravity**: `{'waiting_for_grok' if pending_grok else 'idle'}` (Đang chờ Grok: {len(pending_grok)} requests)",
        f"- **Grok**: `{'in_progress' if pending_grok else 'idle'}` (Đang chờ Antigravity: {len(pending_anti)} requests)\n\n",
        "## 2. Hàng Đợi Đang Chờ (Pending Queue)\n",
    ]
    lines.append(
        "### ⏳ Grok cần xử lý:" if pending_grok else "### ✅ Grok: Không có yêu cầu tồn đọng."
    )
    for p in pending_grok[:5]:
        lines.append(f"- `{p}`")
    if pending_anti:
        lines.append("\n### ⏳ Antigravity cần xử lý:")
    for p in pending_anti[:5]:
        lines.append(f"- `{p}`")

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
    """Executes a single serialized observation and synchronization cycle.

    Args:
        peer_exchange_dir: Directory where peer exchange files reside.
        auto_gate: Whether to trigger peer implementation gate on new code.
        auto_grok: Whether to automatically invoke Grok CLI on new prompts.

    Returns:
        List of detected file changes in this cycle.
    """
    actions_to_run: list[tuple[str, Path]] = []
    changes: list[FileChange] = []

    # COND-01: Narrow _SYNC_MUTEX to the critical section (cache, status, summary updates)
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
                    actions_to_run.append(("grok", change.path))
                elif auto_gate and change.role == "GROK_IMPLEMENTATION":
                    actions_to_run.append(("gate", change.path))

    # Long-running subprocesses execute OUTSIDE _SYNC_MUTEX (COND-01 / ADR-0065)
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


def extract_anchor_payload(text: str) -> AnchorPatchPayload | None:
    """Extracts and validates an AnchorPatchPayload from raw markdown or JSON string.

    Args:
        text: Raw response string.

    Returns:
        Validated AnchorPatchPayload or None if invalid or absent.
    """
    if not text:
        return None
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw_json = match.group(1) if match else text.strip()
    try:
        data = json.loads(raw_json)
        return AnchorPatchPayload.model_validate(data)
    except Exception:
        return None


def apply_anchor_patch(
    root: Path,
    payload: AnchorPatchPayload | dict[str, Any],
    dry_run: bool = False,
    backup: bool = False,
) -> list[Path]:
    """Applies a Level-2 anchor patch payload atomically with SHA-256 pre-verification and rollback (ADR-0063).

    Args:
        root: Workspace root directory.
        payload: AnchorPatchPayload instance or equivalent dictionary.
        dry_run: If True, validates integrity and returns target files without modifying disk.
        backup: If True, creates .bak copies before writing modified content.

    Returns:
        List of Path instances successfully modified (or validated if dry_run=True).

    Raises:
        ValueError: If SHA-256 mismatch occurs, duplicate target files exist, anchor string is not unique,
            or write transaction aborts.
    """
    if isinstance(payload, dict):
        patch = AnchorPatchPayload.model_validate(payload)
    else:
        patch = payload

    root_resolved = root.resolve()
    target_files_seen: set[Path] = set()
    prepared_writes: list[
        tuple[Path, str, str]
    ] = []  # (target_file, original_content, new_content)

    # Phase 1: Pre-validation of all files and content preparation (Fail-Fast)
    for file_patch in patch.files:
        target_file = (root_resolved / file_patch.path).resolve()
        # Security invariant: prevent path traversal outside workspace root
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
        # Line ending normalization (\r\n -> \n) for cross-OS resilience
        text_normalized = text.replace("\r\n", "\n")
        new_text = text_normalized
        for rep in file_patch.replacements:
            old_normalized = rep.old.replace("\r\n", "\n")
            new_normalized = rep.new.replace("\r\n", "\n")
            count = new_text.count(old_normalized)
            if count == 0:
                raise ValueError(
                    f"Target old anchor text not found in {file_patch.path}: '{old_normalized[:50]}...'"
                )
            if count > 1:
                raise ValueError(
                    f"Target old anchor text is not unique in {file_patch.path} (found {count} matches): '{old_normalized[:50]}...'"
                )
            new_text = new_text.replace(old_normalized, new_normalized, 1)

        prepared_writes.append((target_file, text, new_text))

    if dry_run:
        return [target_file for target_file, _, _ in prepared_writes]

    # Phase 2: Atomic commit with automatic rollback on error
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


def get_git_toplevel(cwd: Path | str | None = None) -> Path | None:
    """Resolves the git repository top-level root directory (COND-LEVEL3-ROOT).

    Args:
        cwd: Directory or path to execute git rev-parse from. Defaults to current directory.

    Returns:
        Resolved Path to git top-level root directory, or None if outside git repository.
    """
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


def recover_pending_anchor_transactions(
    backup_dir: Path | None = None,
    root: Path | None = None,
) -> list[str]:
    """Scans and recovers interrupted anchor transactions from disk pre-images (COND-LEVEL3-TXN).

    Any transaction directory under .md/backups/anchor-txn/ that has a journal.json but lacks
    a commit.marker or aborted.marker indicates a process crash/interruption during patch
    application or verification. This function restores the target files from raw pre-image
    bytes and stamps an aborted.marker to ensure workspace hygiene.

    Args:
        backup_dir: Optional explicit path to anchor-txn directory.
        root: Optional workspace root directory to resolve backup directory against.

    Returns:
        List of transaction IDs recovered.
    """
    if backup_dir is None:
        effective_root = root or get_git_toplevel() or Path.cwd()
        backup_dir = effective_root / ".md" / "backups" / "anchor-txn"

    if not backup_dir.exists() or not backup_dir.is_dir():
        return []

    recovered_txns: list[str] = []
    # Deterministic sorting per user rule
    for txn_path in sorted(backup_dir.iterdir(), key=lambda p: p.name):
        if not txn_path.is_dir() or txn_path.name.startswith("."):
            continue
        journal_file = txn_path / "journal.json"
        commit_marker = txn_path / "commit.marker"
        aborted_marker = txn_path / "aborted.marker"

        if journal_file.exists() and not commit_marker.exists() and not aborted_marker.exists():
            try:
                journal_data = json.loads(journal_file.read_text(encoding="utf-8"))
                target_root = Path(
                    journal_data.get("root", str(backup_dir.parent.parent.parent))
                ).resolve()
                files_entries = journal_data.get("files", [])
                for f_entry in files_entries:
                    rel_p = f_entry.get("path")
                    backup_fname = f_entry.get("backup_filename")
                    if not rel_p or not backup_fname:
                        continue
                    backup_file = txn_path / backup_fname
                    if not backup_file.exists():
                        continue
                    target_file = (target_root / rel_p).resolve()
                    # Restore verbatim raw bytes (preserves CRLF/exact bytes)
                    target_file.write_bytes(backup_file.read_bytes())
                aborted_marker.write_text(
                    f"Recovered at {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
                    encoding="utf-8",
                )
                recovered_txns.append(txn_path.name)
            except Exception:
                pass

    return recovered_txns


def auto_apply_and_verify_patch(
    root: Path | str | None,
    patch_payload: AnchorPatchPayload | dict[str, Any],
    verify_preset: str = "ci",
    timeout: float = 180.0,
    keep_backups: bool = False,
    extra_commands: Sequence[str] | None = None,
) -> AutoApplyResult:
    """Atomically applies anchor patch with pre-image byte journaling, closed-loop verification, and auto-rollback (Level-3 / ADR-0065).

    Args:
        root: Workspace repository root directory. If None, resolves via git rev-parse --show-toplevel.
        patch_payload: AnchorPatchPayload instance or equivalent dictionary.
        verify_preset: Verification preset to execute ('code', 'doc', 'skill', 'adr', 'telemetry', 'ci', 'eval').
        timeout: Execution timeout in seconds per verification command.
        keep_backups: Whether to preserve transaction backup directory on verification pass.
        extra_commands: Additional verification shell commands to execute.

    Returns:
        AutoApplyResult containing execution status, gate verdict, and rollback proof.

    Raises:
        ValueError: If root is outside a git repository, preset is invalid, or payload fails validation.
    """

    # 1. Resolve root directory (COND-LEVEL3-ROOT)
    if root is None:
        effective_root = get_git_toplevel()
        if effective_root is None:
            raise ValueError(
                "Root directory resolution failed: current working directory is not inside a git repository."
            )
    else:
        effective_root = Path(root).resolve()
        git_top = get_git_toplevel(effective_root)
        if git_top is None:
            raise ValueError(f"Specified root is not inside a git repository: {effective_root}")

    # 2. Validate payload
    if isinstance(patch_payload, dict):
        patch = AnchorPatchPayload.model_validate(patch_payload)
    else:
        patch = patch_payload

    if not patch.files:
        raise ValueError("Anchor patch payload contains no files to patch.")

    # 3. Validate verify preset (COND-LEVEL3-SCOPE)
    resolve_preset_commands(preset=verify_preset)

    # 4. Recover any prior interrupted transactions (COND-LEVEL3-TXN)
    recover_pending_anchor_transactions(root=effective_root)

    # 5. Initialize isolated transaction backup directory (COND-LEVEL3-BACKUP)
    backup_base = effective_root / ".md" / "backups" / "anchor-txn"
    backup_base.mkdir(parents=True, exist_ok=True)
    txn_id = f"txn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    txn_dir = backup_base / txn_id

    if txn_dir.exists():
        raise ValueError(f"Transaction backup directory already exists: {txn_dir}")

    # Verify no target in payload collides with txn_dir
    for fp in patch.files:
        t_path = (effective_root / fp.path).resolve()
        if t_path == txn_dir.resolve() or txn_dir.resolve().is_relative_to(t_path):
            raise ValueError(f"Payload target collides with transaction directory: {fp.path}")

    lock_file = backup_base / ".lock"
    preimage_sha256: dict[str, str] = {}
    journal_files: list[dict[str, Any]] = []

    with FileMutexLock(lock_file):
        # Phase 1: Pre-validation & Pre-image byte journaling (Fail-Fast)
        txn_dir.mkdir(parents=True, exist_ok=False)
        try:
            # Validate patch structure, anchors, and target integrity
            apply_anchor_patch(root=effective_root, payload=patch, dry_run=True, backup=False)

            # Record pre-image raw bytes
            for idx, file_patch in enumerate(patch.files):
                target_file = (effective_root / file_patch.path).resolve()
                raw_bytes = target_file.read_bytes()
                current_sha = hashlib.sha256(raw_bytes).hexdigest()
                preimage_sha256[file_patch.path] = current_sha

                backup_filename = f"file_{idx}.bin"
                backup_file = txn_dir / backup_filename
                backup_file.write_bytes(raw_bytes)

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
        except Exception as exc:
            shutil.rmtree(txn_dir, ignore_errors=True)
            raise ValueError(f"Pre-apply validation failed: {exc}") from exc

        # Phase 2: Atomic commit to disk
        modified_paths: list[Path] = []
        try:
            modified_paths = apply_anchor_patch(
                root=effective_root, payload=patch, dry_run=False, backup=False
            )
        except Exception as exc:
            # Emergency rollback
            rollback_ok = True
            for f_entry in journal_files:
                try:
                    t_file = (effective_root / f_entry["path"]).resolve()
                    b_file = txn_dir / f_entry["backup_filename"]
                    t_file.write_bytes(b_file.read_bytes())
                except Exception:
                    rollback_ok = False
            if rollback_ok and not keep_backups:
                shutil.rmtree(txn_dir, ignore_errors=True)
            return AutoApplyResult(
                success=False,
                gate_verdict="GATE_FAIL",
                rollback_proven=rollback_ok,
                preimage_sha256=preimage_sha256,
                summary=f"Disk commit aborted: {exc}. Workspace rolled back {'cleanly' if rollback_ok else 'WITH ERRORS'}.",
                transaction_id=txn_id,
            )

        # Phase 3: Closed-Loop Verification Gate (ADR-0058 / COND-LEVEL3-SCOPE)
        commands_to_run: list[str] = list(extra_commands or [])
        if verify_preset == "ci":
            commands_to_run.append(
                f"{sys.executable} -m pytest packages/ccba-harness/tests/test_peer*.py -q"
            )

        verification_report = None
        try:
            verification_report = verify_patch_execution(
                preset=verify_preset,
                cwd=effective_root,
                timeout=timeout,
                commands=commands_to_run if commands_to_run else None,
            )
        except Exception as v_err:
            rollback_ok = True
            for f_entry in journal_files:
                try:
                    t_file = (effective_root / f_entry["path"]).resolve()
                    b_file = txn_dir / f_entry["backup_filename"]
                    t_file.write_bytes(b_file.read_bytes())
                    restored_sha = hashlib.sha256(t_file.read_bytes()).hexdigest()
                    if restored_sha.lower() != f_entry["blob_sha256"].lower():
                        rollback_ok = False
                except Exception:
                    rollback_ok = False
            return AutoApplyResult(
                success=False,
                gate_verdict="GATE_FAIL",
                rollback_proven=rollback_ok,
                preimage_sha256=preimage_sha256,
                summary=f"Verification execution crashed: {v_err}. Workspace rolled back {'cleanly' if rollback_ok else 'WITH ERRORS'}.",
                transaction_id=txn_id,
            )

        # Phase 4: Decision & Automatic Byte Rollback (COND-LEVEL3-TXN & COND-LEVEL3-EXIT)
        rel_modified = [
            str(p.relative_to(effective_root)) if p.is_relative_to(effective_root) else str(p)
            for p in modified_paths
        ]

        if verification_report.all_passed:
            (txn_dir / "commit.marker").write_text("committed", encoding="utf-8")
            if not keep_backups:
                shutil.rmtree(txn_dir, ignore_errors=True)
            return AutoApplyResult(
                success=True,
                gate_verdict="GATE_PASS",
                rollback_proven=False,
                preimage_sha256=preimage_sha256,
                report=verification_report,
                summary=f"Patch successfully applied and verified with preset '{verify_preset}'.",
                transaction_id=txn_id,
                modified_files=rel_modified,
            )

        # Verification failed -> Automatic Byte Rollback with SHA-256 verification
        rollback_proven = True
        for f_entry in journal_files:
            try:
                t_file = (effective_root / f_entry["path"]).resolve()
                b_file = txn_dir / f_entry["backup_filename"]
                t_file.write_bytes(b_file.read_bytes())
                restored_sha = hashlib.sha256(t_file.read_bytes()).hexdigest()
                if restored_sha.lower() != f_entry["blob_sha256"].lower():
                    rollback_proven = False
            except Exception:
                rollback_proven = False

        if rollback_proven:
            (txn_dir / "rollback.marker").write_text("clean", encoding="utf-8")
            if not keep_backups:
                shutil.rmtree(txn_dir, ignore_errors=True)
            summary_msg = (
                f"Verification failed ({verification_report.failed_count}/{verification_report.total_commands} "
                f"commands failed). Workspace rolled back cleanly."
            )
        else:
            summary_msg = (
                f"Verification failed ({verification_report.failed_count}/{verification_report.total_commands} "
                f"commands failed) AND byte rollback verification mismatch! Transaction preserved at {txn_dir}."
            )

        return AutoApplyResult(
            success=False,
            gate_verdict="GATE_FAIL",
            rollback_proven=rollback_proven,
            preimage_sha256=preimage_sha256,
            report=verification_report,
            summary=summary_msg,
            transaction_id=txn_id,
            modified_files=rel_modified,
        )


def extract_grok_session_telemetry(
    session_id: str,
    timeout: float = 3.0,
    fallback_prompt_text: str | None = None,
    fallback_resp_text: str | None = None,
    duration_seconds: float = 0.0,
    fallback_model: str = "unknown",
) -> PeerVerdictTelemetry | None:
    """Safely extracts telemetry metrics from grok usage CLI with bounded retry & graceful degradation (ADR-0064).

    Args:
        session_id: UUID string of the session.
        timeout: Subprocess timeout in seconds (default: 3.0s).
        fallback_prompt_text: Prompt text for heuristic fallback estimation.
        fallback_resp_text: Response text for heuristic fallback estimation.
        duration_seconds: Execution wall-clock duration in seconds.
        fallback_model: Target model name if usage command fails.

    Returns:
        PeerVerdictTelemetry instance, or None if extraction and fallback both fail.
    """
    cmd = ["grok", "usage", session_id]
    deadline = time.time() + timeout

    # Bounded retry loop (up to 2 retries, 100ms interval) within overall timeout budget
    for attempt in range(3):
        remaining = max(0.2, deadline - time.time())
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=remaining,
                check=False,
                stdin=subprocess.DEVNULL,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout)
                session_data = data.get("session", {})
                primary_model = session_data.get("primaryModelId") or fallback_model
                inp = int(session_data.get("inputTokens", 0))
                outp = int(session_data.get("outputTokens", 0))
                rsn = int(session_data.get("reasoningTokens", 0))
                cached = int(session_data.get("cachedReadTokens", 0))
                total = int(session_data.get("totalTokens", inp + outp))
                calls = int(session_data.get("modelCalls", 1))
                turns = int(session_data.get("turnCount", 1))

                # COND-2: Cost provenance distinction
                cost_mode: CostMode = "estimated"
                cost_usd = 0.0
                if "costUsdTicks" in session_data:
                    cost_usd = round(float(session_data["costUsdTicks"]) / 10000.0, 4)
                    cost_mode = "exact"
                else:
                    # Estimate based on rate card in ccba_harness.telemetry
                    from .telemetry import PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT

                    cost_usd = round(
                        (inp / 1_000_000 * PRICE_PER_M_INPUT)
                        + (outp / 1_000_000 * PRICE_PER_M_OUTPUT),
                        4,
                    )
                    cost_mode = "estimated"

                return PeerVerdictTelemetry(
                    session_id=session_id,
                    primary_model=primary_model,
                    input_tokens=inp,
                    output_tokens=outp,
                    reasoning_tokens=rsn,
                    cached_read_tokens=cached,
                    total_tokens=total,
                    model_calls=calls,
                    turn_count=turns,
                    cost_usd=cost_usd,
                    cost_mode=cost_mode,
                    duration_seconds=round(duration_seconds, 2),
                )
        except Exception:
            pass

        if attempt < 2 and time.time() < deadline:
            time.sleep(0.1)

    # COND-1: Graceful degradation fallback using TokenEstimator
    try:
        from .telemetry import PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT, TokenEstimator

        est_inp = TokenEstimator.estimate_text(fallback_prompt_text or "")
        est_out = TokenEstimator.estimate_text(fallback_resp_text or "")
        est_cost = round(
            (est_inp / 1_000_000 * PRICE_PER_M_INPUT) + (est_out / 1_000_000 * PRICE_PER_M_OUTPUT),
            4,
        )
        return PeerVerdictTelemetry(
            session_id=session_id,
            primary_model=fallback_model,
            input_tokens=est_inp,
            output_tokens=est_out,
            reasoning_tokens=0,
            cached_read_tokens=0,
            total_tokens=est_inp + est_out,
            model_calls=1,
            turn_count=1,
            cost_usd=est_cost,
            cost_mode="estimated",
            duration_seconds=round(duration_seconds, 2),
        )
    except Exception:
        return None


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
) -> list[str]:
    """Constructs canonical grok CLI command list for headless execution (ADR-0063 / ADR-0064).

    Args:
        prompt_path: Path to prompt file containing PeerPromptEnvelope.
        model: Model slug as defined in ~/.grok/config.toml.
        max_turns: Optional hard cap on agent turns.
        tools: Optional explicit allowlist of tools.
        disallowed_tools: Optional explicit denylist of tools.
        reasoning_effort: Optional reasoning effort ('low', 'medium', 'high', 'xhigh').
        output_format: Output format ('plain', 'json', etc. Default: 'plain').
        worktree: Whether to execute in an isolated git worktree.
        session_id: Optional session UUID string.
        system_prompt: Optional system prompt string to override agent default.
        deny: Optional tool permission deny rule or list of rules.

    Returns:
        Command arguments list.
    """
    cmd = ["grok", "-m", model, "--always-approve", "--no-subagents"]
    if session_id:
        cmd.extend(["--session-id", session_id])
    if system_prompt:
        cmd.extend(["--system-prompt-override", system_prompt])
    if deny:
        if isinstance(deny, (list, tuple)):
            for d in deny:
                cmd.extend(["--deny", str(d)])
        else:
            cmd.extend(["--deny", str(deny)])
    if reasoning_effort:
        cmd.extend(["--reasoning-effort", reasoning_effort])
    if max_turns is not None:
        cmd.extend(["--max-turns", str(max_turns)])
    if tools:
        cmd.extend(["--tools", ",".join(tools)])
    if disallowed_tools:
        cmd.extend(["--disallowed-tools", ",".join(disallowed_tools)])
    if output_format:
        cmd.extend(["--output-format", output_format])
    if worktree:
        cmd.append("--worktree")
    cmd.extend(["--prompt-file", str(prompt_path)])
    return cmd


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
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
            except OSError:
                proc.terminate()
        else:
            proc.terminate()
        proc.wait(timeout=2.0)
    except Exception:
        try:
            if sys.platform != "win32" and hasattr(os, "killpg") and hasattr(os, "getpgid"):
                try:
                    pgid = os.getpgid(pid)
                    os.killpg(pgid, signal.SIGKILL)
                except OSError:
                    proc.kill()
            else:
                proc.kill()
            proc.wait(timeout=2.0)
        except Exception:
            pass


def _run_single_grok_attempt(
    cmd: list[str],
    prompt_path: Path,
    output_file: Path,
    timeout: float,
    session_id: str | None = None,
    candidate_model: str = "unknown",
) -> bool:
    """Executes a single invocation of grok CLI and verifies output verdict (ADR-0064 / ADR-0065).

    Args:
        cmd: Command arguments list to execute.
        prompt_path: Source prompt file path.
        output_file: Target output file path to write result.
        timeout: Subprocess timeout in seconds.
        session_id: Optional session UUID for telemetry extraction.
        candidate_model: Target model name for telemetry fallback.

    Returns:
        True if output contains a valid PeerVerdictBlock, False otherwise.
    """
    start_time = time.time()
    try:
        with (
            tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as temp_out,
            tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as temp_err,
        ):
            popen_kwargs: dict[str, Any] = {
                "stdout": temp_out,
                "stderr": temp_err,
                "stdin": subprocess.DEVNULL,
                "text": True,
                "encoding": "utf-8",
                "errors": "replace",
            }
            if sys.platform != "win32":
                popen_kwargs["start_new_session"] = True
            proc = subprocess.Popen(cmd, **popen_kwargs)
            deadline = start_time + timeout
            stdout_text = ""
            while time.time() < deadline:
                ret = proc.poll()
                if ret is not None:
                    temp_out.seek(0)
                    stdout_text = temp_out.read()
                    if not stdout_text and hasattr(proc, "communicate"):
                        comm_out, _ = proc.communicate()
                        if comm_out:
                            stdout_text = comm_out
                    break

                # cond-3-verdict-atomic-validation: Watchdog checks if output file was generated during this run
                if output_file.exists() and output_file.stat().st_mtime >= start_time:
                    content, _ = safe_read_and_hash(output_file)
                    if content and (
                        parse_verdict_from_md(content) or extract_anchor_payload(content)
                    ):
                        stdout_text = content
                        _terminate_proc_tree(proc)
                        break

                time.sleep(1.0)
            else:
                _terminate_proc_tree(proc)
                return False

        if (not stdout_text.strip() or parse_verdict_from_md(stdout_text) is None) and session_id:
            try:
                session_root = Path.home() / ".grok" / "sessions"
                max_bytes = 2 * 1024 * 1024
                for p in session_root.glob(f"**/{session_id}/chat_history.jsonl"):
                    if p.exists():
                        file_size = p.stat().st_size
                        with p.open("r", encoding="utf-8", errors="replace") as f:
                            if file_size > max_bytes:
                                f.seek(file_size - max_bytes)
                                f.readline()
                            lines = f.readlines()
                        for line in reversed(lines):
                            if line.strip():
                                d = json.loads(line)
                                if d.get("type") == "assistant" and d.get("content"):
                                    cand = d["content"]
                                    if parse_verdict_from_md(cand) is not None:
                                        stdout_text = cand
                                        break
                        if stdout_text and parse_verdict_from_md(stdout_text) is not None:
                            break
            except Exception:
                pass

        if not stdout_text.strip():
            return False

        duration = time.time() - start_time
        verdict = parse_verdict_from_md(stdout_text)
        if verdict is None:
            anchor_payload = extract_anchor_payload(stdout_text)
            if anchor_payload is not None:
                prompt_content, _ = safe_read_and_hash(prompt_path)
                envelope = parse_envelope_from_md(prompt_content or "")
                req_id = envelope.request_id if envelope else "req-auto"
                # COND-02: Never fabricate synthetic APPROVE from anchor patch alone
                verdict = PeerVerdictBlock(
                    request_id=req_id,
                    verdict="HANDOFF",
                    summary="Fast-path anchor patch generated; pending orchestrator apply and verification.",
                )
                stdout_text = render_verdict_header(verdict) + "\n" + stdout_text.lstrip()
            else:
                return False

        if session_id:
            prompt_content, _ = safe_read_and_hash(prompt_path)
            telemetry = extract_grok_session_telemetry(
                session_id=session_id,
                timeout=3.0,
                fallback_prompt_text=prompt_content,
                fallback_resp_text=stdout_text,
                duration_seconds=duration,
                fallback_model=candidate_model,
            )
            if telemetry:
                verdict.telemetry = telemetry
                _, body = extract_frontmatter(stdout_text)
                rendered_fm = render_verdict_header(verdict)
                stdout_text = rendered_fm + body.lstrip()

        atomic_write_text(output_file, stdout_text)
        return True
    except Exception:
        return False


def invoke_grok_cli(
    prompt_path: Path,
    model: str | None = None,
    profile: PeerExecutionProfile | str | None = None,
    tier: ModelTier | str | None = None,
    max_turns: int | None = None,
    timeout: float | None = None,
    worktree: bool = False,
) -> bool:
    """Invokes Grok CLI with Level-2 execution profile mapping and budget guardrails (ADR-0063 / ADR-0064).

    Args:
        prompt_path: Path to prompt file containing PeerPromptEnvelope.
        model: Optional explicit model override.
        profile: Execution profile ('audit_plan', 'agentic_code', 'patch_fast').
        tier: Model tier ('local', 'gateway', 'cloud').
        max_turns: Optional turns override.
        timeout: Subprocess execution timeout in seconds.
        worktree: Whether to run inside a detached git worktree.

    Returns:
        True if response was successfully generated and verified, False otherwise.
    """
    content, _ = safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(content or "")
    if not envelope or not envelope.output_path:
        return False

    out_name = Path(envelope.output_path).name
    output_file = prompt_path.parent / out_name

    active_profile = profile or (envelope.profile if envelope else None)
    spec: dict[str, Any] = PROFILE_SPECS.get(
        str(active_profile),
        {
            "model": DEFAULT_PRIMARY_AUDITOR_MODEL,
            "fallback_model": DEFAULT_FALLBACK_AUDITOR_MODEL,
            "max_turns": 12,
            "tools": None,
            "disallowed_tools": ["spawn_subagent"],
            "reasoning_effort": "xhigh",
            "timeout": 180.0,
        },
    )

    spec_max_turns = (
        max_turns
        if max_turns is not None
        else (
            envelope.max_turns
            if envelope and envelope.max_turns is not None
            else spec.get("max_turns")
        )
    )
    tools = spec.get("tools")
    disallowed_tools = spec.get("disallowed_tools")
    deny = spec.get("deny")
    reasoning_effort = spec.get("reasoning_effort")
    system_prompt = spec.get("system_prompt")
    spec_timeout = timeout if timeout is not None else spec.get("timeout", 180.0)

    target_models: list[str] = []
    if model:
        target_models.append(model)
    elif tier and str(tier) in TIER_DEFAULT_MODELS:
        target_models.append(TIER_DEFAULT_MODELS[str(tier)])
    elif os.getenv("CCBA_GROK_MODEL"):
        target_models.append(os.environ["CCBA_GROK_MODEL"])
    else:
        target_models.append(spec["model"])
        fallback = spec.get("fallback_model")
        if fallback and fallback not in target_models:
            target_models.append(fallback)

    for candidate in target_models:
        candidate_session_id = str(uuid.uuid4())
        cmd = build_grok_cmd(
            prompt_path=prompt_path,
            model=candidate,
            max_turns=spec_max_turns,
            tools=tools,
            disallowed_tools=disallowed_tools,
            deny=deny,
            reasoning_effort=reasoning_effort,
            worktree=worktree,
            session_id=candidate_session_id,
            system_prompt=system_prompt,
        )
        if _run_single_grok_attempt(
            cmd,
            prompt_path,
            output_file,
            spec_timeout,
            session_id=candidate_session_id,
            candidate_model=candidate,
        ):
            return True
    return False


def synthesize_verdicts(
    request_id: str,
    verdicts: dict[str, PeerVerdictBlock],
    expected_profiles: Sequence[str] | None = None,
    duration_seconds: float = 0.0,
) -> PeerConsensusReport:
    """Synthesizes multiple peer verdicts into a unified deterministic consensus report (ADR-0065).

    Args:
        request_id: Request identifier matching the prompt.
        verdicts: Mapping of profile name to PeerVerdictBlock.
        expected_profiles: Optional expected profiles list for quorum enforcement.
        duration_seconds: Execution wall-clock duration in seconds.

    Returns:
        PeerConsensusReport with synthesized verdict, conditions, and telemetry.
    """
    if not verdicts and not expected_profiles:
        raise ValueError(
            "Cannot synthesize consensus from empty verdicts and empty expected profiles."
        )

    exp_profiles = (
        list(expected_profiles) if expected_profiles is not None else list(verdicts.keys())
    )
    comp_profiles = [p for p in exp_profiles if p in verdicts]
    failed_profiles = [p for p in exp_profiles if p not in verdicts]

    pass_verdicts: set[VerdictType] = {
        "APPROVE",
        "APPROVE_PLAN",
        "FINAL_ACCEPT",
        "GATE_PASS",
        "APPROVE_WITH_RESERVATIONS",
    }

    # 1. Determine baseline consensus verdict by strict lattice rank (COND-LATTICE-QUORUM)
    completed_verdicts = [verdicts[p].verdict for p in comp_profiles]
    if not completed_verdicts:
        consensus_verdict: VerdictType = "HANDOFF"
    else:
        completed_max = max(completed_verdicts, key=lambda t: VERDICT_LATTICE_RANK.get(t, 0))
        if failed_profiles:
            # Monotonic quorum join: if highest completed verdict is at or above HANDOFF (e.g. REVISE_PLAN, REJECT),
            # preserve it. Otherwise (e.g. APPROVE, APPROVE_WITH_CONDITIONS), quorum failure falls back to HANDOFF.
            handoff_rank = VERDICT_LATTICE_RANK.get("HANDOFF", 70)
            if VERDICT_LATTICE_RANK.get(completed_max, 0) >= handoff_rank:
                consensus_verdict = completed_max
            else:
                consensus_verdict = "HANDOFF"
        else:
            consensus_verdict = completed_max

    # 2. Consolidate conditions with deterministic ordering & OR-merge on blocking
    consolidated_conds: list[PeerCondition] = []
    seen_cond_descs: dict[str, PeerCondition] = {}

    for prof in comp_profiles:
        vb = verdicts[prof]
        for cond in vb.conditions:
            key = cond.description.strip().lower()
            if key in seen_cond_descs:
                existing = seen_cond_descs[key]
                existing.blocking = existing.blocking or cond.blocking
                if prof not in existing.source_profiles:
                    existing.source_profiles.append(prof)
            else:
                new_cond = PeerCondition(
                    id=cond.id,
                    description=cond.description,
                    blocking=cond.blocking,
                    source_profile=prof,
                    source_profiles=[prof],
                )
                seen_cond_descs[key] = new_cond
                consolidated_conds.append(new_cond)

    if failed_profiles:
        fail_cond = PeerCondition(
            id="COND-QUORUM-FAIL",
            description=f"Missing peer review from profiles: {', '.join(failed_profiles)}",
            blocking=True,
            source_profile="orchestrator",
            source_profiles=["orchestrator"],
        )
        consolidated_conds.append(fail_cond)

    # 3. Dynamic escalation: blocking conditions or risk_score >= 4 upgrade PASS to APPROVE_WITH_CONDITIONS
    has_blocking = any(c.blocking for c in consolidated_conds)
    if consensus_verdict in pass_verdicts and has_blocking:
        consensus_verdict = "APPROVE_WITH_CONDITIONS"

    valid_risks = [
        verdicts[p].risk_score for p in comp_profiles if verdicts[p].risk_score is not None
    ]
    consensus_risk = max(valid_risks) if valid_risks else 1
    if consensus_verdict in pass_verdicts and consensus_risk >= 4:
        consensus_verdict = "APPROVE_WITH_CONDITIONS"

    # 4. Consolidate telemetry breakdown (isolated to protect consensus report - COND-LEVEL3-GATE)
    combined_telemetry: CombinedTelemetry | None = None
    try:
        agg_total = 0
        agg_input = 0
        agg_output = 0
        agg_reasoning = 0
        agg_cached = 0
        cost_usd = 0.0
        sum_agent_seconds = 0.0
        all_exact = True
        has_any_telemetry = False
        profile_breakdown: dict[str, ProfileTelemetryItem] = {}

        for prof in comp_profiles:
            vb = verdicts[prof]
            tel = vb.telemetry
            if tel:
                has_any_telemetry = True
                agg_total += tel.total_tokens or 0
                agg_input += tel.input_tokens or 0
                agg_output += tel.output_tokens or 0
                agg_reasoning += tel.reasoning_tokens or 0
                agg_cached += tel.cached_read_tokens or 0
                cost_usd += tel.cost_usd or 0.0
                sum_agent_seconds += tel.duration_seconds or 0.0
                if tel.cost_mode != "exact":
                    all_exact = False
                item_payload = {
                    "model": tel.primary_model,
                    "input_tokens": tel.input_tokens or 0,
                    "output_tokens": tel.output_tokens or 0,
                    "reasoning_tokens": tel.reasoning_tokens or 0,
                    "cached_read_tokens": tel.cached_read_tokens or 0,
                    "total_tokens": tel.total_tokens or 0,
                    "cost_usd": round(tel.cost_usd or 0.0, 4),
                    "duration_seconds": round(tel.duration_seconds or 0.0, 2),
                }
                profile_breakdown[prof] = ProfileTelemetryItem.model_validate(item_payload)
            else:
                all_exact = False

        if has_any_telemetry:
            comb_payload = {
                "total_tokens": agg_total,
                "input_tokens": agg_input,
                "output_tokens": agg_output,
                "reasoning_tokens": agg_reasoning,
                "cached_read_tokens": agg_cached,
                "cost_usd": round(cost_usd, 4),
                "wall_seconds": round(duration_seconds, 2),
                "sum_agent_seconds": round(sum_agent_seconds, 2),
                "cost_mode": "exact" if all_exact else "estimated",
                "profile_breakdown": profile_breakdown,
            }
            combined_telemetry = CombinedTelemetry.model_validate(comb_payload)
    except Exception:
        combined_telemetry = None

    # 5. Build consolidated summary
    summary_lines = [
        f"Consensus Verdict: **{consensus_verdict}** (Risk Score: {consensus_risk}/5).",
        f"Quorum: {len(comp_profiles)}/{len(exp_profiles)} completed.",
    ]
    if failed_profiles:
        summary_lines.append(f"Failed Profiles: {', '.join(failed_profiles)}.")
    for prof in comp_profiles:
        vb = verdicts[prof]
        summary_lines.append(f"- **{prof}** ({vb.verdict}): {vb.summary}")
    unified_summary = "\n".join(summary_lines)

    return PeerConsensusReport(
        request_id=request_id,
        verdict=consensus_verdict,
        risk_score=consensus_risk,
        summary=unified_summary,
        expected_profiles=exp_profiles,
        completed_profiles=comp_profiles,
        failed_profiles=failed_profiles,
        individual_verdicts=verdicts,
        conditions=consolidated_conds,
        combined_telemetry=combined_telemetry,
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

    yaml_str = yaml.dump(fm_payload, sort_keys=False, allow_unicode=True)
    header = f"---\n{yaml_str}---\n"

    body_lines = [
        f"# 🤝 Multi-Agent Peer Consensus Report: `{report.request_id}`\n",
        f"- **Consensus Verdict**: `{report.verdict}`",
        f"- **Consolidated Risk Score**: `{report.risk_score}/5`",
        f"- **Quorum**: `{len(report.completed_profiles)}/{len(report.expected_profiles)}` profiles completed\n",
        "## 1. Executive Summary\n",
        report.summary,
        "\n## 2. Consolidated Conditions\n",
    ]
    if report.conditions:
        for c in report.conditions:
            blocking_tag = "🔴 [BLOCKING]" if c.blocking else "🟡 [ADVISORY]"
            sources = (
                ", ".join(c.source_profiles)
                if c.source_profiles
                else (c.source_profile or "unknown")
            )
            body_lines.append(f"- **{c.id}** {blocking_tag} ({sources}): {c.description}")
    else:
        body_lines.append("*(No conditions attached)*")

    body_lines.append("\n## 3. Individual Profile Verdicts\n")
    for prof, vb in report.individual_verdicts.items():
        body_lines.append(f"### Profile: `{prof}`")
        body_lines.append(f"- **Verdict**: `{vb.verdict}` (Risk: `{vb.risk_score or 'N/A'}`)")
        body_lines.append(f"- **Summary**: {vb.summary}\n")

    if report.combined_telemetry:
        tel = report.combined_telemetry
        body_lines.append("## 4. Telemetry & Cost Provenance\n")
        body_lines.append(
            f"- **Total Tokens**: {tel.total_tokens:,} (Input: {tel.input_tokens:,}, Output: {tel.output_tokens:,}, Reasoning: {tel.reasoning_tokens:,})"
        )
        body_lines.append(f"- **Total Cost**: ${tel.cost_usd:.4f} (mode: `{tel.cost_mode}`)")
        body_lines.append(
            f"- **Duration**: Wall clock `{tel.wall_seconds}s` | Sum agent time `{tel.sum_agent_seconds}s`\n"
        )

    return header + "\n".join(body_lines) + "\n"


def orchestrate_peer_co_review(
    prompt_path: Path,
    profiles: Sequence[str] = ("code_review", "arch_audit"),
    output_file: Path | None = None,
    max_workers: int | None = None,
    timeout: float | None = None,
    worktree: bool = False,
) -> PeerConsensusReport | None:
    """Orchestrates multi-agent co-review execution in parallel threads with isolated outputs (ADR-0065).

    Args:
        prompt_path: Path to markdown prompt file containing PeerPromptEnvelope.
        profiles: Sequence of peer profile names to dispatch.
        output_file: Path to final consensus markdown file.
        max_workers: ThreadPoolExecutor worker count cap.
        timeout: Optional timeout override for agent executions.
        worktree: Whether to execute agents inside a git worktree.

    Returns:
        PeerConsensusReport on success, or None if prompt is unreadable.
    """
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

    request_id = envelope.request_id

    # COND-04: Isolated TemporaryDirectory with 0700 permissions outside peer_exchange
    temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"peer_co_review_{request_id[:8]}_")
    temp_dir = Path(temp_dir_obj.name)
    try:
        try:
            os.chmod(temp_dir, 0o700)
        except Exception:
            pass

        start_time = time.time()
        tasks: list[tuple[str, Path, Path]] = []

        for prof in profiles:
            prof_prompt = temp_dir / f"prompt_{prof}.md"
            prof_out_name = f"grok_{prof}.md"
            prof_env = envelope.model_copy()
            prof_env.profile = prof  # type: ignore[assignment]
            prof_env.output_path = prof_out_name
            rendered = render_prompt_header(prof_env)
            _, body = extract_frontmatter(content or "")
            atomic_write_text(prof_prompt, rendered + body.lstrip())
            tasks.append((prof, prof_prompt, temp_dir / prof_out_name))

        def _worker(item: tuple[str, Path, Path]) -> tuple[str, PeerVerdictBlock | None]:
            p_name, p_prompt, p_out = item
            spec = PROFILE_SPECS.get(p_name, {})
            p_model = spec.get("model")
            p_timeout = timeout if timeout is not None else spec.get("timeout")
            ok = invoke_grok_cli(
                prompt_path=p_prompt,
                model=p_model,
                profile=p_name,
                timeout=p_timeout,
                worktree=worktree,
            )
            if not ok or not p_out.exists():
                return p_name, None
            out_str, _ = safe_read_and_hash(p_out)
            vb = parse_verdict_from_md(out_str or "")
            return p_name, vb

        workers_count = max_workers if max_workers is not None else min(len(profiles), 4)
        verdicts: dict[str, PeerVerdictBlock] = {}

        with ThreadPoolExecutor(max_workers=max(1, workers_count)) as pool:
            futures = [pool.submit(_worker, t) for t in tasks]
            for fut in futures:
                try:
                    p_name, vb = fut.result()
                    if vb is not None:
                        verdicts[p_name] = vb
                except Exception:
                    pass

        elapsed = time.time() - start_time
        report = synthesize_verdicts(
            request_id=request_id,
            verdicts=verdicts,
            expected_profiles=profiles,
            duration_seconds=elapsed,
        )

        final_out = output_file
        if not final_out:
            stem = prompt_path.stem.replace("prompt_", "")
            final_out = prompt_path.parent / f"grok_consensus_{stem}.md"

        report_md = render_consensus_report_markdown(report)
        atomic_write_text(final_out, report_md)
        return report
    finally:
        temp_dir_obj.cleanup()
