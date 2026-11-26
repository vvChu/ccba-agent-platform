"""_turn_stream.py - Canonical Turn Stream, Zero-LLM Behavioral Probes, and Invocation Ledger.

Internal decomposition module for `ccba_harness.evals` (Wave 1 Telemetry Overhaul).
Reuses `ccba_harness.telemetry.stream_transcript_steps()` and `_miner_catalog` redaction
without changing legacy `miner.py` / `_miner_catalog.py` public contracts.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .._skill_content_checks import (
    _PLACEHOLDER_SLASH_CMDS,
    ALLOWED_HOST_COMMANDS,
    COMMON_PATH_SEGMENTS,
)
from ..telemetry import TranscriptStep, stream_transcript_steps
from ._miner_catalog import extract_clean_user_prompt, load_catalog, redact_sensitive_info

DEFAULT_INVOCATION_LEDGER_PATH = Path(".md/telemetry/skill_invocations.jsonl")

MUTATING_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "write_file",
        "write_to_file",
        "edit_file",
        "replace_file_content",
        "multi_replace_file_content",
        "delete_file",
    }
)

READ_ONLY_SKILLS: frozenset[str] = frozenset(
    {
        "ccba-ask",
        "ccba-code-review",
        "ccba-legal-intel",
        "ccba-legal-advisor",
        "ccba-eval-gate",
    }
)

MODE_B_ALLOWED_ARTIFACT_MARKERS: tuple[str, ...] = ("brainstorm", "research")

SHORT_CONFIRMATION_TOKENS: frozenset[str] = frozenset(
    {
        "1",
        "2",
        "3",
        "ok",
        "yes",
        "y",
        "proceed",
        "approve",
        "continue",
        "go",
        "merge",
        "tiếp",
        "tiếp tục",
        "đồng ý",
        "chốt",
        "pa1",
        "pa2",
        "pa3",
    }
)

_LEADING_SLASH_RE = re.compile(r"^\s*(/[a-z][a-z0-9_-]*)(?=\s|$|[.,!?;:])", re.IGNORECASE)
_CLAUSE_SLASH_RE = re.compile(r"(?:[.,;!?]\s+)(/[a-z][a-z0-9_-]*)(?=\s|$|[.,!?;:])", re.IGNORECASE)
_ALL_SLASH_RE = re.compile(
    r"(?<![a-zA-Z0-9_./\\<@:])(/[a-z][a-z0-9_-]*)(?![a-zA-Z0-9_./\\-])",
    re.IGNORECASE,
)
_META_PREFIX_RE = re.compile(
    r"(?:skill|lệnh|command|slash|gọi|dùng|chạy|về|của|cho|qua)\s*$",
    re.IGNORECASE,
)
_CCBA_CMD_NAMESPACE_RE = re.compile(r"^/(?:ccba|bigbim)-[a-z0-9-]+$", re.IGNORECASE)
_WORKSPACE_ROOT_RE = re.compile(
    r"(?:/(?:ccba|worktrees|projects|repos|works)/|[A-Za-z]:[\\/][^\\/\s\"']+[\\/])([A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_URL_RE = re.compile(r"(?:https?|file)://\S+", re.IGNORECASE)
_INLINE_TEST_MARKERS: tuple[str, ...] = (
    "pytest",
    "test_case",
    "inline smoke",
    ">>> ",
    "unittest",
)
_TRACEBACK_MARKER = "Traceback (most recent call last)"


@dataclass
class TurnToolCall:
    """Sanitized summary of a single tool invocation within a user turn."""

    name: str
    target_basename: str = ""
    is_mutating: bool = False
    step_index: int = 0


@dataclass
class UserTurn:
    """Canonical representation of one user turn and all subsequent planner/tool steps."""

    conversation_id: str
    turn_index: int
    step_index: int
    created_at: str
    workspace_hash: str
    user_prompt: str
    invoked_skill: str | None = None
    invoked_command: str | None = None
    mentioned_commands: list[str] = field(default_factory=list)
    planner_responses: list[str] = field(default_factory=list)
    recommended_commands: list[str] = field(default_factory=list)
    tool_calls: list[TurnToolCall] = field(default_factory=list)
    mutating_tool_count: int = 0
    planner_steps: int = 0
    error_snippets: list[str] = field(default_factory=list)

    @property
    def combined_response(self) -> str:
        """Join all planner response chunks emitted during this turn."""
        return "\n\n".join(r for r in self.planner_responses if r)

    @property
    def tool_counts(self) -> dict[str, int]:
        """Aggregate deterministic invocation counts per tool name."""
        counts = Counter(tc.name for tc in self.tool_calls if tc.name)
        return dict(sorted(counts.items()))


@dataclass
class BehavioralProbeFinding:
    """Zero-LLM confirmed behavioral or contract violation finding for a UserTurn."""

    conversation_id: str
    turn_index: int
    step_index: int
    created_at: str
    invoked_skill: str | None
    probe_type: str
    confidence: str = "confirmed"
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def hash_workspace_key(raw_workspace: str) -> str:
    """Compute a one-way 16-hex SHA-256 hash for a normalized workspace identifier."""
    cleaned = raw_workspace.strip().replace("\\", "/").rstrip("/").lower()
    if not cleaned:
        return ""
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:16]


def build_command_skill_map(catalog_path: Path | str | None = None) -> dict[str, str]:
    """Build normalized `/command -> canonical_skill_name` mapping from catalog SSOT."""
    mapping: dict[str, str] = {}
    for entry in load_catalog(catalog_path):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip()
        if not name:
            continue
        mapping[f"/{name.lower()}"] = name
        cmd = str(entry.get("command", "") or "").strip().lower()
        if cmd.startswith("/"):
            mapping[cmd] = name
    return mapping


def _canonicalize_command(cmd: str, command_map: dict[str, str]) -> str:
    """Resolve a slash command to its canonical skill name when registered."""
    cmd_lower = cmd.lower()
    if cmd_lower in command_map:
        return command_map[cmd_lower]
    return cmd_lower.lstrip("/")


def _extract_all_slash_commands(text: str) -> list[str]:
    """Extract deduplicated slash commands from text while excluding URLs and common paths."""
    cleaned = _URL_RE.sub(" ", text)
    commands: list[str] = []
    seen: set[str] = set()
    for match in _ALL_SLASH_RE.finditer(cleaned):
        cmd = match.group(1).lower()
        seg = cmd.lstrip("/")
        if cmd in _PLACEHOLDER_SLASH_CMDS or seg in COMMON_PATH_SEGMENTS or len(seg) < 2:
            continue
        if cmd not in seen:
            seen.add(cmd)
            commands.append(cmd)
    return commands


def extract_slash_invocation(
    prompt: str,
    command_map: dict[str, str] | None = None,
) -> tuple[str | None, str | None, list[str]]:
    """Split user prompt slash commands into invoked skill (+100 leading rule) vs mentioned."""
    if not prompt or not prompt.strip():
        return None, None, []
    cmap = command_map if command_map is not None else build_command_skill_map()
    all_cmds = _extract_all_slash_commands(prompt)
    if not all_cmds:
        return None, None, []

    lead = _LEADING_SLASH_RE.match(prompt)
    if lead:
        inv_cmd = lead.group(1).lower()
        mentioned = [c for c in all_cmds if c != inv_cmd]
        return _canonicalize_command(inv_cmd, cmap), inv_cmd, mentioned

    for match in _CLAUSE_SLASH_RE.finditer(prompt):
        inv_cmd = match.group(1).lower()
        prefix = prompt[: match.start()].strip()
        if _META_PREFIX_RE.search(prefix):
            continue
        if inv_cmd in cmap or _CCBA_CMD_NAMESPACE_RE.match(inv_cmd):
            mentioned = [c for c in all_cmds if c != inv_cmd]
            return _canonicalize_command(inv_cmd, cmap), inv_cmd, mentioned

    return None, None, all_cmds


def extract_recommended_commands(response_text: str) -> list[str]:
    """Extract slash commands recommended in assistant prose (ignoring fenced code blocks)."""
    if not response_text:
        return []
    prose = _CODE_FENCE_RE.sub(" ", response_text)
    return _extract_all_slash_commands(prose)


def _extract_target_basename(args: dict[str, Any]) -> str:
    """Extract only the safe filename basename from tool call arguments (never raw path)."""
    for key in ("Path", "TargetFile", "path", "target_file", "file_path"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            cleaned = val.strip().strip("\"'")
            return Path(cleaned.replace("\\", "/")).name
    return ""


def _extract_workspace_hint(text_or_args: Any) -> str:
    """Extract a normalized repository workspace name from path hints without persisting paths."""
    raw = str(text_or_args or "")
    match = _WORKSPACE_ROOT_RE.search(raw)
    if match:
        return match.group(1).strip().lower()
    return ""


def _is_inline_test_noise(text: str) -> bool:
    """Return True when an error snippet comes from inline unit/smoke tests rather than runtime."""
    lower = text.lower()
    return any(marker in lower for marker in _INLINE_TEST_MARKERS)


def _record_planner_step(turn: UserTurn, step: TranscriptStep) -> str:
    """Attach a PLANNER_RESPONSE step to the active UserTurn and return workspace hint."""
    turn.planner_steps += 1
    if step.content.strip():
        turn.planner_responses.append(redact_sensitive_info(step.content.strip()))
    ws_hint = ""
    for tc in step.tool_calls:
        if not isinstance(tc, dict):
            continue
        t_name = str(tc.get("name", "") or "").strip()
        if not t_name:
            continue
        raw_args = tc.get("args")
        args: dict[str, Any] = raw_args if isinstance(raw_args, dict) else {}
        if not ws_hint:
            ws_hint = _extract_workspace_hint(args)
        is_mut = t_name in MUTATING_TOOL_NAMES
        turn.tool_calls.append(
            TurnToolCall(
                name=t_name,
                target_basename=_extract_target_basename(args),
                is_mutating=is_mut,
                step_index=step.step_index,
            )
        )
        if is_mut:
            turn.mutating_tool_count += 1
    return ws_hint


def _record_error_step(turn: UserTurn, step: TranscriptStep) -> None:
    """Record genuine runtime tool errors while filtering SYSTEM_MESSAGE and inline test noise."""
    if step.type == "SYSTEM_MESSAGE":
        return
    content = step.content.strip()
    if step.status == "ERROR" or (
        step.type in ("TOOL_EXECUTION", "RUN_COMMAND") and _TRACEBACK_MARKER in content
    ):
        if _is_inline_test_noise(content):
            return
        snippet = (
            redact_sensitive_info(content[:240]) or f"{step.type} failed (status={step.status})"
        )
        turn.error_snippets.append(snippet)


def _finalize_turn(turn: UserTurn, conv_workspace_hash: str) -> UserTurn:
    """Populate derived fields (recommended commands and fallback workspace hash) on a UserTurn."""
    if not turn.workspace_hash and conv_workspace_hash:
        turn.workspace_hash = conv_workspace_hash
    turn.recommended_commands = extract_recommended_commands(turn.combined_response)
    return turn


def _derive_conversation_id(log_path: Path) -> str:
    """Derive a stable conversation ID from a transcript file path."""
    if log_path.parent.name == "logs" and log_path.parent.parent.name == ".system_generated":
        return log_path.parent.parent.parent.name
    if len(log_path.parents) >= 3 and log_path.name == "transcript.jsonl":
        return log_path.parents[2].name
    return log_path.stem


def _start_user_turn(
    step: TranscriptStep,
    conv_id: str,
    turn_counter: int,
    command_map: dict[str, str],
) -> UserTurn | None:
    """Create a canonical UserTurn from a USER_INPUT step, preserving short prompts."""
    clean_prompt = extract_clean_user_prompt(step.content)
    if not clean_prompt:
        return None
    inv_skill, inv_cmd, mentioned = extract_slash_invocation(clean_prompt, command_map)
    ws_hint = _extract_workspace_hint(step.content)
    ws_hash = hash_workspace_key(ws_hint) if ws_hint else ""
    created = step.created_at_raw or step.created_at.isoformat()
    return UserTurn(
        conversation_id=conv_id,
        turn_index=turn_counter,
        step_index=step.step_index,
        created_at=created,
        workspace_hash=ws_hash,
        user_prompt=clean_prompt,
        invoked_skill=inv_skill,
        invoked_command=inv_cmd,
        mentioned_commands=mentioned,
    )


def stream_user_turns(
    log_path: Path,
    catalog_path: Path | str | None = None,
) -> list[UserTurn]:
    """Stream a transcript.jsonl via telemetry.stream_transcript_steps into canonical UserTurns."""
    if not log_path.is_file():
        return []
    conv_id = _derive_conversation_id(log_path)
    command_map = build_command_skill_map(catalog_path)
    turns: list[UserTurn] = []
    active: UserTurn | None = None
    conv_ws_hash = ""
    turn_counter = 0

    for step, _offset in stream_transcript_steps(log_path):
        if step.type == "USER_INPUT":
            if active is not None:
                turns.append(_finalize_turn(active, conv_ws_hash))
            candidate = _start_user_turn(step, conv_id, turn_counter + 1, command_map)
            if candidate is None:
                active = None
                continue
            turn_counter += 1
            if candidate.workspace_hash and not conv_ws_hash:
                conv_ws_hash = candidate.workspace_hash
            active = candidate
            continue
        if active is None:
            continue
        if step.type == "PLANNER_RESPONSE":
            ws_hint = _record_planner_step(active, step)
            if ws_hint:
                ws_hash = hash_workspace_key(ws_hint)
                conv_ws_hash = conv_ws_hash or ws_hash
                active.workspace_hash = active.workspace_hash or ws_hash
        elif step.type in ("GENERIC", "TOOL_EXECUTION", "RUN_COMMAND", "SYSTEM_MESSAGE"):
            _record_error_step(active, step)

    if active is not None:
        turns.append(_finalize_turn(active, conv_ws_hash))
    return turns


def collect_turns_from_dir(
    log_dir: Path,
    catalog_path: Path | str | None = None,
) -> list[UserTurn]:
    """Collect canonical UserTurns deterministically across all JSONL transcripts in log_dir."""
    from .miner import find_transcript_files

    turns: list[UserTurn] = []
    for tfile in find_transcript_files(log_dir):
        if tfile.suffix.lower() != ".jsonl":
            continue
        turns.extend(stream_user_turns(tfile, catalog_path=catalog_path))
    return turns


def detect_side_effect_violation(
    turn: UserTurn,
    read_only_skills: frozenset[str] = READ_ONLY_SKILLS,
) -> BehavioralProbeFinding | None:
    """Flag confirmed SIDE_EFFECT_VIOLATION when a read-only skill executes mutating tools."""
    if not turn.tool_calls or turn.mutating_tool_count <= 0:
        return None
    if not turn.invoked_skill or turn.invoked_skill not in read_only_skills:
        return None

    mut_calls = [tc for tc in turn.tool_calls if tc.is_mutating]
    if turn.invoked_skill == "ccba-ask" and not turn.mentioned_commands:
        if mut_calls and all(
            any(m in tc.target_basename.lower() for m in MODE_B_ALLOWED_ARTIFACT_MARKERS)
            for tc in mut_calls
            if tc.target_basename
        ):
            if any(tc.target_basename for tc in mut_calls):
                return None

    mut_names = sorted({tc.name for tc in mut_calls})
    targets = [tc.target_basename for tc in mut_calls if tc.target_basename]
    return BehavioralProbeFinding(
        conversation_id=turn.conversation_id,
        turn_index=turn.turn_index,
        step_index=turn.step_index,
        created_at=turn.created_at,
        invoked_skill=turn.invoked_skill,
        probe_type="SIDE_EFFECT_VIOLATION",
        confidence="confirmed",
        reason=(
            f"Read-only skill '{turn.invoked_skill}' executed {turn.mutating_tool_count} "
            f"mutating tool call(s): {', '.join(mut_names)}"
        ),
        details={
            "mutating_tools": mut_names,
            "mutating_tool_count": turn.mutating_tool_count,
            "mentioned_commands": list(turn.mentioned_commands),
            "target_basenames": targets[:5],
        },
    )


def detect_routing_contract_drift(
    turn: UserTurn,
    valid_commands: frozenset[str] | None = None,
    catalog_path: Path | str | None = None,
) -> BehavioralProbeFinding | None:
    """Flag confirmed ROUTING_CONTRACT_DRIFT when assistant recommends unregistered CCBA commands."""
    if not turn.recommended_commands:
        return None
    if valid_commands is None:
        cmap = build_command_skill_map(catalog_path)
        valid_commands = frozenset(cmap.keys()) | frozenset(
            c.lower() for c in ALLOWED_HOST_COMMANDS
        )
    user_cmds = set(_extract_all_slash_commands(turn.user_prompt))
    drifted = [
        cmd
        for cmd in turn.recommended_commands
        if _CCBA_CMD_NAMESPACE_RE.match(cmd) and cmd not in valid_commands and cmd not in user_cmds
    ]
    if not drifted:
        return None
    return BehavioralProbeFinding(
        conversation_id=turn.conversation_id,
        turn_index=turn.turn_index,
        step_index=turn.step_index,
        created_at=turn.created_at,
        invoked_skill=turn.invoked_skill,
        probe_type="ROUTING_CONTRACT_DRIFT",
        confidence="confirmed",
        reason=f"Recommended unregistered command(s): {', '.join(drifted)}",
        details={"unregistered_commands": drifted},
    )


def detect_behavioral_probes(
    turns: list[UserTurn],
    catalog_path: Path | str | None = None,
    read_only_skills: frozenset[str] = READ_ONLY_SKILLS,
) -> list[BehavioralProbeFinding]:
    """Run all Zero-LLM confirmed behavioral probes over a list of UserTurns."""
    cmap = build_command_skill_map(catalog_path)
    valid_cmds = frozenset(cmap.keys()) | frozenset(c.lower() for c in ALLOWED_HOST_COMMANDS)
    findings: list[BehavioralProbeFinding] = []
    for turn in turns:
        se = detect_side_effect_violation(turn, read_only_skills=read_only_skills)
        if se is not None:
            findings.append(se)
        drift = detect_routing_contract_drift(turn, valid_commands=valid_cmds)
        if drift is not None:
            findings.append(drift)
        if turn.error_snippets:
            findings.append(
                BehavioralProbeFinding(
                    conversation_id=turn.conversation_id,
                    turn_index=turn.turn_index,
                    step_index=turn.step_index,
                    created_at=turn.created_at,
                    invoked_skill=turn.invoked_skill,
                    probe_type="UNEXPECTED_TOOL_ERROR",
                    confidence="confirmed",
                    reason=f"Captured {len(turn.error_snippets)} runtime tool error(s).",
                    details={"error_count": len(turn.error_snippets)},
                )
            )
    return findings


def is_short_confirmation_prompt(prompt: str) -> bool:
    """Return True if prompt is a concise user confirmation or option selection."""
    norm = prompt.strip().lower().rstrip(".!?")
    if not norm or len(norm) > 32:
        return False
    if norm in SHORT_CONFIRMATION_TOKENS:
        return True
    return bool(re.match(r"^(?:phương án|option|chặng|pha|bước|pa)\s*[a-z0-9]+$", norm))


def build_invocation_event(
    turn: UserTurn,
    probe_types: list[str] | None = None,
) -> dict[str, Any]:
    """Build a zero-prompt, zero-path, Maskara-sanitized structured invocation record."""
    event_id = f"{turn.conversation_id}:{turn.turn_index}"
    sanitized_mentions = [redact_sensitive_info(c) for c in turn.mentioned_commands]
    sanitized_recs = [redact_sensitive_info(c) for c in turn.recommended_commands]
    sanitized_skill = redact_sensitive_info(turn.invoked_skill) if turn.invoked_skill else None
    return {
        "schema_version": 1,
        "event_id": event_id,
        "conversation_id": turn.conversation_id,
        "turn_index": turn.turn_index,
        "step_index": turn.step_index,
        "created_at": turn.created_at,
        "workspace_hash": turn.workspace_hash,
        "invoked_skill": sanitized_skill,
        "mentioned_commands": sanitized_mentions,
        "recommended_commands": sanitized_recs,
        "prompt_char_len": len(turn.user_prompt),
        "is_short_confirmation": is_short_confirmation_prompt(turn.user_prompt),
        "tool_counts": turn.tool_counts,
        "mutating_tool_count": turn.mutating_tool_count,
        "planner_steps": turn.planner_steps,
        "probe_violations": sorted(set(probe_types or [])),
        "has_error": bool(turn.error_snippets),
    }


def _load_existing_event_ids(ledger_path: Path) -> set[str]:
    """Read previously recorded event_id keys from an append-only JSONL ledger."""
    existing: set[str] = set()
    if not ledger_path.is_file():
        return existing
    for line in ledger_path.read_text(encoding="utf-8", errors="replace").splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        try:
            row = json.loads(trimmed)
        except Exception:
            continue
        if isinstance(row, dict) and isinstance(row.get("event_id"), str):
            existing.add(row["event_id"])
    return existing


def record_skill_invocations(
    turns: list[UserTurn],
    ledger_path: Path = DEFAULT_INVOCATION_LEDGER_PATH,
    catalog_path: Path | str | None = None,
) -> int:
    """Append sanitized, idempotent structured invocation events to a local JSONL ledger."""
    if not turns:
        return 0
    probes = detect_behavioral_probes(turns, catalog_path=catalog_path)
    probes_by_key: dict[str, list[str]] = {}
    for p in probes:
        key = f"{p.conversation_id}:{p.turn_index}"
        probes_by_key.setdefault(key, []).append(p.probe_type)

    existing_ids = _load_existing_event_ids(ledger_path)
    new_lines: list[str] = []
    for turn in turns:
        ev_id = f"{turn.conversation_id}:{turn.turn_index}"
        if ev_id in existing_ids:
            continue
        event = build_invocation_event(turn, probe_types=probes_by_key.get(ev_id, []))
        new_lines.append(json.dumps(event, ensure_ascii=False))
        existing_ids.add(ev_id)

    if not new_lines:
        return 0
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines) + "\n")
    return len(new_lines)
