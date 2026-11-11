"""_peer_models.py - Pydantic v2 schemas and YAML frontmatter helpers for Peer Exchange (ADR-0007 / ADR-0063..0065)."""

from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._peer_watchdog import (
    _VERDICT_ALIASES,
    AgentIdentity,
    CostMode,
    EffortType,
    PeerExecutionProfile,
    RequestType,
    VerdictType,
)

FRONTMATTER_PATTERN = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)
INLINE_FRONTMATTER_PATTERN = re.compile(
    r"(?:^|\r?\n|(?<=[.!*`]))---\s*\r?\n(.*?)(?=(\r?\n---\s*(?:\r?\n|$)))", re.DOTALL
)
FENCED_YAML_PATTERN = re.compile(r"```(?:yaml|yml)\s*\r?\n(.*?)\r?\n```", re.DOTALL | re.IGNORECASE)
_NESTED_VERDICT_KEYS: tuple[str, ...] = ("PeerVerdictBlock", "peer_verdict", "verdict_block")
_FRONTMATTER_KEYS: tuple[str, ...] = (
    "verdict",
    "from_agent",
    "author",
    "from",
    "sender",
    "request_id",
    "task_id",
    "id",
    "question",
    "profile",
    "output_path",
    "request_type",
    "task_type",
)
_ENVELOPE_MARKER_KEYS: frozenset[str] = frozenset(
    {
        "from_agent",
        "sender",
        "author",
        "from",
        "to_agent",
        "recipient",
        "target",
        "to",
        "request_id",
        "task_id",
        "id",
        "subject",
        "question",
        "chapter",
        "title",
        "wave",
        "output_path",
        "output_file",
        "profile",
        "resume_session_id",
        "session_id",
        "request_type",
        "task_type",
        "target_files",
        "target_scope",
    }
)
_ENVELOPE_ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "request_id",
        "from_agent",
        "to_agent",
        "request_type",
        "subject",
        "timestamp",
        "source_documents",
        "output_path",
        "context",
        "profile",
        "max_turns",
        "target_files",
        "resume_session_id",
        "fork_session",
        "conversation_id",
        "task_id",
        "spoke_name",
        "tags",
    }
)
_REQUEST_TYPE_ALIASES: dict[str, str] = {
    "signoff": "review",
    "signoff_diff": "verify",
    "reverify": "verify",
    "re-verify": "verify",
    "re_verify": "verify",
    "verification": "verify",
    "code_review": "review",
    "editorial_review": "review",
    "architecture_review": "review",
    "architectural_and_editorial_review": "review",
    "arch_audit": "audit",
    "audit_plan": "audit",
    "audit_direct": "audit",
    "deep_spec_audit": "audit",
    "plan": "discuss",
    "brainstorm": "discuss",
    "discussion": "discuss",
    "consultation": "consult",
}
_PROFILE_ALIASES: dict[str, str] = {
    "discuss": "audit_plan",
    "code_audit": "code_review",
    "review": "code_review",
    "audit": "arch_audit",
    "signoff": "signoff_diff",
}

_EFFORT_ALIASES: dict[str, str] = {
    "LOW": "S",
    "SMALL": "S",
    "MEDIUM": "M",
    "MODERATE": "M",
    "HIGH": "L",
    "LARGE": "L",
    "XHIGH": "XL",
}


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


def _sanitize_optional_id(v: Any) -> str | None:
    """Strips optional identifier strings and normalizes empty strings to None."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _sanitize_spoke_slug(v: Any) -> str | None:
    """Sanitizes spoke_name into a machine-path-free alphanumeric slug."""
    if v is None:
        return None
    raw = str(v).strip()
    if not raw:
        return None
    spoke_base = Path(raw).name if ("/" in raw or "\\" in raw) else raw
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "", spoke_base).strip()
    return slug or None


_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def extract_env_conversation_id() -> str | None:
    """Extracts validated UUID conversationId from ANTIGRAVITY_SOURCE_METADATA if set."""
    raw = os.environ.get("ANTIGRAVITY_SOURCE_METADATA", "").strip()
    if not raw:
        return None
    try:
        meta = json.loads(raw)
        if not isinstance(meta, dict):
            return None
        tool_meta = meta.get("tool")
        cid = (
            tool_meta.get("conversationId")
            if isinstance(tool_meta, dict)
            else meta.get("conversationId")
        )
        if isinstance(cid, str) and _UUID_PATTERN.match(cid.strip()):
            return cid.strip()
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
    return None


def resolve_spoke_slug_from_path(
    target_path: Path | None, *, allow_ancestor_walk: bool = False
) -> str | None:
    """Resolves spoke_name slug from canonical <repo>/.md/peer_exchange/ layout or .git ancestor."""
    if target_path is None:
        return None
    parent = target_path.parent
    if parent.name == "peer_exchange" and parent.parent.name == ".md":
        repo_root = parent.parent.parent
        if (repo_root / ".git").exists():
            return _sanitize_spoke_slug(repo_root.name)
    if allow_ancestor_walk:
        for candidate in (parent, *parent.parents):
            if (candidate / ".git").exists():
                return _sanitize_spoke_slug(candidate.name)
    return None


def _normalize_condition_dict(d: dict[str, Any], index: int) -> dict[str, Any]:
    """Normalizes a single condition dict (aliases and multi-key structured items)."""
    aliases = ("text", "statement", "condition", "summary", "observation", "title")
    out = dict(d)
    if not out.get("description"):
        for alias in aliases:
            if out.get(alias):
                out["description"] = str(out[alias])
                break
    if not out.get("description"):
        reserved = {"id", "blocking", "source_profile", "source_profiles", *aliases}
        extra = [
            (str(k), str(val).strip())
            for k, val in out.items()
            if k not in reserved and val is not None and str(val).strip()
        ]
        if len(extra) == 1 and len(out) == 1:
            k, val = extra[0]
            return {"id": k, "description": val, "blocking": True}
        if extra:
            head_k, head_val = extra[0]
            tail = "; ".join(f"{k}: {val}" for k, val in extra[1:])
            out["description"] = f"{head_val} ({tail})" if tail else head_val
            if not out.get("id"):
                out["id"] = f"{head_k}-{index + 1:02d}"
    if not out.get("id"):
        out["id"] = f"COND-{index + 1:02d}"
    return out


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
    conversation_id: str | None = None
    task_id: str | None = None
    spoke_name: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("conversation_id", "task_id", mode="before")
    @classmethod
    def _clean_optional_id(cls, v: Any) -> str | None:
        return _sanitize_optional_id(v)

    @field_validator("spoke_name", mode="before")
    @classmethod
    def _clean_spoke_name(cls, v: Any) -> str | None:
        return _sanitize_spoke_slug(v)

    @field_validator("tags", mode="before")
    @classmethod
    def _clean_tags(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return [str(t).strip()[:40] for t in v if str(t).strip()][:8]
        if isinstance(v, str) and v.strip():
            return [t.strip()[:40] for t in v.split(",") if t.strip()][:8]
        return []


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
    primary_model: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cached_read_tokens: int = 0
    total_tokens: int = 0
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
    conversation_id: str | None = None
    task_id: str | None = None
    spoke_name: str | None = None
    verdict: VerdictType
    conditions: list[PeerCondition] = Field(default_factory=list)
    risk_score: int | None = Field(default=None, ge=1, le=5)
    effort: EffortType | None = None
    summary: str = ""
    timestamp: str | None = None
    telemetry: PeerVerdictTelemetry | CombinedTelemetry | None = None

    @field_validator("conversation_id", "task_id", mode="before")
    @classmethod
    def _clean_verdict_optional_id(cls, v: Any) -> str | None:
        return _sanitize_optional_id(v)

    @field_validator("spoke_name", mode="before")
    @classmethod
    def _clean_verdict_spoke_name(cls, v: Any) -> str | None:
        return _sanitize_spoke_slug(v)

    @field_validator("risk_score", mode="before")
    @classmethod
    def _normalize_risk_score(cls, v: Any) -> Any:
        if isinstance(v, float):
            if 0.0 <= v < 1.0:
                return max(1, min(5, int(round(v * 5)) or 1))
            if 1.0 <= v <= 5.0:
                return int(round(v))
        return v

    @field_validator("effort", mode="before")
    @classmethod
    def _normalize_effort(cls, v: Any) -> Any:
        if not isinstance(v, str) or not v.strip():
            return None
        parts = [t for t in re.split(r"[\s—–\-:/,;()]+", v.strip().upper()) if t]
        if not parts:
            return None
        head = parts[0]
        if head in ("XS", "S", "M", "L", "XL"):
            return head
        return _EFFORT_ALIASES.get(head)

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
            elif isinstance(item, dict):
                normalized.append(_normalize_condition_dict(item, i))
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


def _unwrap_nested_verdict_dict(data: Any) -> dict[str, Any] | None:
    """Unwraps nested PeerVerdictBlock/peer_verdict dict if present while preserving sibling keys."""
    if not isinstance(data, dict):
        return None
    for key in _NESTED_VERDICT_KEYS:
        inner = data.get(key)
        if isinstance(inner, dict):
            return {k: v for k, v in data.items() if k != key} | inner
    return data


def _extract_all_frontmatter_blocks(md_content: str) -> list[tuple[dict[str, Any], str]]:
    """Extracts all valid YAML frontmatter dicts and their trailing bodies from markdown text."""
    if not md_content:
        return []
    content = md_content.lstrip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z0-9_-]*\r?\n", "", content)
    blocks: list[tuple[dict[str, Any], str]] = []
    consumed_until = 0
    if content.startswith("---"):
        match = FRONTMATTER_PATTERN.match(content)
        if match:
            try:
                data = _unwrap_nested_verdict_dict(yaml.safe_load(match.group(1)))
                if data is not None:
                    blocks.append((data, content[match.end() :]))
                    consumed_until = match.end()
            except Exception:
                pass
    for match in INLINE_FRONTMATTER_PATTERN.finditer(content):
        if match.start() < consumed_until or (blocks and match.start() == 0):
            continue
        try:
            data = _unwrap_nested_verdict_dict(yaml.safe_load(match.group(1)))
            if data is not None and any(k in data for k in _FRONTMATTER_KEYS):
                closing_end = match.end() + len(match.group(2))
                blocks.append((data, content[closing_end:]))
                consumed_until = closing_end
        except Exception:
            continue
    if not blocks:
        for match in FENCED_YAML_PATTERN.finditer(md_content):
            try:
                data = _unwrap_nested_verdict_dict(yaml.safe_load(match.group(1)))
                if data is not None and any(k in data for k in _FRONTMATTER_KEYS):
                    blocks.append((data, md_content[match.end() :]))
            except Exception:
                continue
    return blocks


def extract_frontmatter(md_content: str) -> tuple[dict[str, Any] | None, str]:
    """Extracts raw YAML frontmatter dictionary and remaining body from markdown content.

    Args:
        md_content: Raw markdown text possibly containing YAML frontmatter.

    Returns:
        A tuple of (parsed_dict, body_text). If absent or invalid, returns (None, md_content).
    """
    blocks = _extract_all_frontmatter_blocks(md_content)
    if not blocks:
        return None, md_content
    for data, body in blocks:
        if "verdict" in data:
            return data, body
    return blocks[0]


def _coerce_doc_list(raw: Any) -> list[str]:
    """Coerces string or dict items into a clean list of file path strings."""
    if not isinstance(raw, (list, tuple)):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            val = str(item.get("path") or item.get("file") or "").strip()
        else:
            val = str(item or "").strip()
        if val:
            out.append(val)
    return out


def _apply_envelope_doc_and_session_aliases(data: dict[str, Any], d: dict[str, Any]) -> None:
    """Applies document list coercions and session_id resume aliases onto normalized envelope dict."""
    if "source_documents" in data or "context_files" in data:
        d["source_documents"] = _coerce_doc_list(
            data.get("source_documents") or data.get("context_files")
        )
    if "target_files" in data or "target_scope" in data:
        d["target_files"] = _coerce_doc_list(data.get("target_files") or data.get("target_scope"))
    if "resume_session_id" not in d and data.get("session_id"):
        d["resume_session_id"] = str(data["session_id"]).strip()
        if data.get("stage") == 3 or d.get("profile") == "signoff_diff":
            d.setdefault("fork_session", True)


def _normalize_envelope_frontmatter(
    data: dict[str, Any], prompt_path: Path | None = None
) -> dict[str, Any] | None:
    """Normalizes common agent frontmatter aliases and defaults into canonical PeerPromptEnvelope fields."""
    if "verdict" in data or not any(k in data for k in _ENVELOPE_MARKER_KEYS):
        return None
    d = {k: v for k, v in data.items() if k in _ENVELOPE_ALLOWED_KEYS}
    req_id = str(
        data.get("request_id")
        or data.get("task_id")
        or data.get("id")
        or (prompt_path.stem if prompt_path else "")
    ).strip()
    if not req_id:
        return None
    d["request_id"] = req_id
    d["from_agent"] = str(
        data.get("from_agent")
        or data.get("sender")
        or data.get("author")
        or data.get("from")
        or "antigravity"
    ).strip()
    d["to_agent"] = str(
        data.get("to_agent")
        or data.get("recipient")
        or data.get("target")
        or data.get("to")
        or "grok"
    ).strip()
    raw_rt = str(data.get("request_type") or data.get("task_type") or data.get("type") or "review")
    d["request_type"] = _REQUEST_TYPE_ALIASES.get(raw_rt.strip().lower(), raw_rt.strip().lower())
    if d.get("profile") is not None:
        raw_p = str(d["profile"]).strip().lower()
        d["profile"] = _PROFILE_ALIASES.get(raw_p, raw_p)
    subj = (
        data.get("subject")
        or data.get("question")
        or data.get("chapter")
        or data.get("title")
        or data.get("wave")
    )
    d["subject"] = str(subj or req_id).strip()
    d["timestamp"] = str(
        data.get("timestamp") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    stem = (
        re.sub(r"^prompt_(?:grok_)?", "", prompt_path.stem, flags=re.IGNORECASE)
        if prompt_path
        else req_id
    )
    d["output_path"] = str(
        data.get("output_path") or data.get("output_file") or f"grok_{stem}.md"
    ).strip()
    _apply_envelope_doc_and_session_aliases(data, d)

    # Lineage metadata extraction (ADR-0063 / COND-09)
    raw_conv_id = str(data.get("conversation_id") or "").strip()
    d["conversation_id"] = raw_conv_id or None

    raw_task_id = str(data.get("task_id") or "").strip()
    d["task_id"] = raw_task_id or None

    raw_spoke = str(data.get("spoke_name") or data.get("spoke") or "").strip()
    if raw_spoke:
        spoke_base = Path(raw_spoke).name if ("/" in raw_spoke or "\\" in raw_spoke) else raw_spoke
        slug = re.sub(r"[^a-zA-Z0-9_\-]", "", spoke_base).strip()
        d["spoke_name"] = slug or None
    else:
        d["spoke_name"] = None

    raw_tags = data.get("tags")
    if isinstance(raw_tags, (list, tuple)):
        clean_tags = [str(t).strip()[:40] for t in raw_tags if str(t).strip()][:8]
        d["tags"] = clean_tags
    elif isinstance(raw_tags, str) and raw_tags.strip():
        clean_tags = [t.strip()[:40] for t in raw_tags.split(",") if t.strip()][:8]
        d["tags"] = clean_tags
    else:
        d["tags"] = []

    return d


def parse_envelope_from_md(
    md_content: str, prompt_path: Path | None = None
) -> PeerPromptEnvelope | None:
    """Parses PeerPromptEnvelope from markdown frontmatter with alias normalization."""
    for data, _ in _extract_all_frontmatter_blocks(md_content):
        if "from_agent" in data:
            try:
                return PeerPromptEnvelope.model_validate(data)
            except Exception:
                pass
        norm = _normalize_envelope_frontmatter(data, prompt_path=prompt_path)
        if norm is not None:
            try:
                return PeerPromptEnvelope.model_validate(norm)
            except Exception:
                continue
    return None


def _coerce_frontmatter_risk_score(raw: Any) -> Any:
    """Coerces out-of-range or string/fraction LLM frontmatter risk_score scales into 1..5."""
    if isinstance(raw, str):
        s = raw.strip()
        frac = re.match(r"^(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)$", s)
        if frac:
            num, den = float(frac.group(1)), float(frac.group(2))
            if den <= 0:
                return 1
            scaled = (num / den * 5.0) if den > 5.0 else num
            return max(1, min(5, int(round(scaled))))
        try:
            raw = float(s)
        except ValueError:
            return raw
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return raw
    if isinstance(raw, float) and 0.0 < raw < 1.0:
        return raw
    if raw <= 0:
        return 1
    if raw <= 5:
        return int(round(raw))
    if raw <= 10:
        return max(1, min(5, int(round(raw / 2))))
    if raw <= 100:
        return max(1, min(5, int(round(raw / 20))))
    return 5


def parse_verdict_from_md(md_content: str) -> PeerVerdictBlock | None:
    """Parses PeerVerdictBlock from markdown frontmatter.

    Args:
        md_content: Markdown content to parse.

    Returns:
        PeerVerdictBlock instance if valid, or None if invalid or absent.
    """
    for data, _ in _extract_all_frontmatter_blocks(md_content):
        if "verdict" not in data:
            continue
        cand = (
            {**data, "risk_score": _coerce_frontmatter_risk_score(data["risk_score"])}
            if "risk_score" in data
            else data
        )
        try:
            return PeerVerdictBlock.model_validate(cand)
        except Exception:
            continue
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


def _registry_timestamp(
    envelope: PeerPromptEnvelope | None,
    verdict: PeerVerdictBlock | None,
) -> str:
    """Prefer a verdict frontmatter timestamp, then the prompt envelope timestamp."""
    if verdict is not None and verdict.timestamp:
        return str(verdict.timestamp)
    if envelope is not None and envelope.timestamp:
        return str(envelope.timestamp)
    return ""


def _sort_key_latest_exchange(item: dict[str, Any]) -> tuple[float, str, str]:
    """Newer mtime, then newer ISO timestamp, then greater filename."""
    return (
        round(float(item.get("mtime", 0.0)), 4),
        str(item.get("timestamp") or ""),
        item["path"].name,
    )
