"""_peer_models.py - Pydantic v2 schemas and YAML frontmatter helpers for Peer Exchange (ADR-0007 / ADR-0063..0065)."""

from __future__ import annotations

import datetime
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

FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


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
    timestamp: str | None = None
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
