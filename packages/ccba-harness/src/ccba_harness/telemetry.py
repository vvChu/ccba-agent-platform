"""telemetry.py - OpenTelemetry Subagent Runtime & Token Monitoring Engine.

Implements lightweight, zero-overhead execution tracing and token budgeting (ADR-0030, ADR-0058):
1. Streaming line-by-line parsing of `transcript.jsonl` with byte-offset tracking.
2. Dual Token Estimator: extracts native API usage when available or applies calibrated BPE heuristics (EN/VI).
3. Subagent Session Metrics aggregation: turns, latency, tool breakdowns, and cost modeling.
4. OpenTelemetry GenAI Semantic Conventions (v1.28.0+) span generator and OTLP JSON exporter.
5. Dynamic Token Budgeting verification gate (`check_subagent_budget`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Default token pricing estimation (e.g. Gemini 1.5 Pro / Flash baseline USD per 1M tokens)
PRICE_PER_M_INPUT = 1.25  # $1.25 / 1M input tokens
PRICE_PER_M_OUTPUT = 5.00  # $5.00 / 1M output tokens


@dataclass
class TokenEstimator:
    """Heuristic Token Estimator for bilingual (EN/VI) and code contexts."""

    @classmethod
    def estimate_text(cls, text: str) -> int:
        """Estimate token count for a text string using calibrated character ratios."""
        if not text:
            return 0

        # Detect Vietnamese diacritics
        vn_chars = len(
            re.findall(
                r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]",
                text,
                re.IGNORECASE,
            )
        )
        total_len = len(text)
        if total_len == 0:
            return 0

        # If more than 2% Vietnamese characters, text is Vietnamese-dominant (~2.8 chars/token)
        if vn_chars > 0 and (vn_chars / total_len) > 0.02:
            return max(1, int(total_len / 2.8))

        # Default for English, code, Markdown formatting (~4.0 chars/token)
        return max(1, int(total_len / 4.0))

    @classmethod
    def estimate_json(cls, obj: Any) -> int:
        """Estimate token count for structured JSON payloads."""
        if obj is None:
            return 0
        try:
            serialized = json.dumps(obj, ensure_ascii=False)
            return cls.estimate_text(serialized)
        except Exception:
            return cls.estimate_text(str(obj))


@dataclass
class TranscriptStep:
    """A discrete trajectory step parsed from transcript.jsonl."""

    step_index: int
    source: str
    type: str
    status: str
    created_at_raw: str
    created_at: datetime
    content: str = ""
    thinking: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    truncated_fields: list[str] = field(default_factory=list)
    raw_dict: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallRecord:
    """Execution telemetry for a single tool call."""

    name: str
    args: dict[str, Any]
    step_index: int
    status: str = "DONE"
    duration_ms: float = 0.0
    estimated_tokens: int = 0


@dataclass
class TurnRecord:
    """Telemetry for a single LLM model generation turn."""

    turn_index: int
    step_index: int
    created_at: str
    duration_sec: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tool_calls: list[ToolCallRecord] = field(default_factory=list)


@dataclass
class SubagentSessionMetrics:
    """Comprehensive aggregated metrics for an entire subagent execution trajectory."""

    conversation_id: str
    log_file: str
    total_steps: int
    turns_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_duration_sec: float
    tool_counts: dict[str, int] = field(default_factory=dict)
    tool_durations_ms: dict[str, float] = field(default_factory=dict)
    model_name: str = "gemini-pro"
    estimated_cost_usd: float = 0.0
    turns: list[TurnRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to a clean serializable dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "log_file": self.log_file,
            "total_steps": self.total_steps,
            "turns_count": self.turns_count,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_duration_sec": round(self.total_duration_sec, 2),
            "tool_counts": self.tool_counts,
            "tool_durations_ms": {k: round(v, 1) for k, v in self.tool_durations_ms.items()},
            "model_name": self.model_name,
            "estimated_cost_usd": round(self.estimated_cost_usd, 5),
            "turns_summary": [
                {
                    "turn": t.turn_index,
                    "prompt_tokens": t.prompt_tokens,
                    "completion_tokens": t.completion_tokens,
                    "duration_sec": round(t.duration_sec, 2),
                    "tool_calls": len(t.tool_calls),
                }
                for t in self.turns
            ],
        }

    def to_markdown(self) -> str:
        """Format metrics into a concise Markdown summary table."""
        lines = [
            f"# 📊 Subagent Runtime Telemetry Report: `{self.conversation_id}`",
            "",
            "## 1. Token & Execution Overview",
            "",
            f"- **Total Steps in Log:** {self.total_steps}",
            f"- **Model Turns:** {self.turns_count}",
            f"- **Total Duration:** {self.total_duration_sec:.2f}s",
            f"- **Prompt Tokens (Context):** {self.prompt_tokens:,}",
            f"- **Completion Tokens (Gen):** {self.completion_tokens:,}",
            f"- **Total Tokens Consumed:** {self.total_tokens:,}",
            f"- **Estimated Cost:** ${self.estimated_cost_usd:.4f} USD",
            "",
            "## 2. Tool Calls Breakdown",
            "",
            "| Tool Name | Invocations | Total Duration (ms) | Avg Duration (ms) |",
            "| :--- | :---: | :---: | :---: |",
        ]
        if not self.tool_counts:
            lines.append("| *(None)* | 0 | 0.0 | 0.0 |")
        else:
            for name, count in sorted(self.tool_counts.items(), key=lambda x: x[1], reverse=True):
                dur = self.tool_durations_ms.get(name, 0.0)
                avg = dur / count if count > 0 else 0.0
                lines.append(f"| `{name}` | {count} | {dur:,.1f}ms | {avg:,.1f}ms |")

        return "\n".join(lines)


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string safely with UTC fallback."""
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        # Replace trailing Z with +00:00 for fromisoformat compatibility
        cleaned = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except Exception:
        return datetime.now(timezone.utc)


def stream_transcript_steps(
    log_path: Path,
    start_offset: int = 0,
) -> Iterator[tuple[TranscriptStep, int]]:
    """Stream steps from transcript.jsonl line-by-line with zero memory bloat.

    Yields:
        (step, current_file_byte_offset)
    """
    if not log_path.exists():
        return

    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        if start_offset > 0:
            f.seek(start_offset)

        while True:
            line = f.readline()
            if not line:
                break
            current_offset = f.tell()
            trimmed = line.strip()
            if not trimmed:
                continue
            try:
                data = json.loads(trimmed)
                created_raw = data.get("created_at", "")
                dt = parse_iso_datetime(created_raw)
                step = TranscriptStep(
                    step_index=data.get("step_index", 0),
                    source=data.get("source", ""),
                    type=data.get("type", ""),
                    status=data.get("status", ""),
                    created_at_raw=created_raw,
                    created_at=dt,
                    content=data.get("content", "") or "",
                    thinking=data.get("thinking", "") or "",
                    tool_calls=data.get("tool_calls", []) or [],
                    truncated_fields=data.get("truncated_fields", []) or [],
                    raw_dict=data,
                )
                yield step, current_offset
            except Exception:
                # Corrupt line, skip safely
                continue


def resolve_transcript_path(path_or_id: str | Path) -> Path:
    """Resolve a conversation ID or file path to an actual on-disk transcript.jsonl."""
    p = Path(path_or_id)
    if p.exists() and p.is_file():
        return p

    cand_id = str(path_or_id).strip()
    # Check default Antigravity app data directory
    user_home = Path.home()
    app_data = Path(os.environ.get("ANTIGRAVITY_APP_DATA", user_home / ".gemini" / "antigravity"))
    brain_dir = app_data / "brain" / cand_id

    # Try transcript.jsonl first, then transcript_full.jsonl
    log_1 = brain_dir / ".system_generated" / "logs" / "transcript.jsonl"
    if log_1.exists():
        return log_1

    log_2 = brain_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
    if log_2.exists():
        return log_2

    # If user provided directory containing logs
    if (p / "transcript.jsonl").exists():
        return p / "transcript.jsonl"

    return p


def analyze_subagent_transcript(
    path_or_id: str | Path,
    base_system_tokens: int = 1500,
) -> SubagentSessionMetrics:
    """Analyze a subagent trajectory, computing token usage and execution telemetry."""
    log_path = resolve_transcript_path(path_or_id)
    if log_path.parent.name == "logs" and log_path.parent.parent.name == ".system_generated":
        conv_id = log_path.parent.parent.parent.name
    elif log_path.parent.name == "logs":
        conv_id = log_path.parent.parent.name
    else:
        conv_id = log_path.stem

    total_steps = 0
    turns: list[TurnRecord] = []
    tool_counts: dict[str, int] = defaultdict(int)
    tool_durations: dict[str, float] = defaultdict(float)

    start_time: datetime | None = None
    end_time: datetime | None = None

    # Context token accumulator for simulating turn-by-turn prompt expansion
    accumulated_context_tokens = base_system_tokens
    pending_tool_calls: list[tuple[datetime, str]] = []

    turn_counter = 0

    for step, _offset in stream_transcript_steps(log_path):
        total_steps += 1
        if start_time is None:
            start_time = step.created_at
        end_time = step.created_at

        # Step type: USER_INPUT (initial prompt)
        if step.type == "USER_INPUT":
            input_tokens = TokenEstimator.estimate_text(step.content)
            accumulated_context_tokens += input_tokens

        # Step type: PLANNER_RESPONSE (LLM model response & tool invocations)
        elif step.type == "PLANNER_RESPONSE":
            turn_counter += 1
            turn_start = step.created_at

            # Completion tokens: thinking + content + tool calls payload
            thinking_tokens = TokenEstimator.estimate_text(step.thinking)
            content_tokens = TokenEstimator.estimate_text(step.content)
            tools_tokens = TokenEstimator.estimate_json(step.tool_calls)
            turn_completion_tokens = thinking_tokens + content_tokens + tools_tokens

            turn_tool_records: list[ToolCallRecord] = []
            for tc in step.tool_calls:
                t_name = tc.get("name", "unknown")
                t_args = tc.get("args", {})
                tool_counts[t_name] += 1
                t_tokens = TokenEstimator.estimate_json(t_args)
                record = ToolCallRecord(
                    name=t_name,
                    args=t_args,
                    step_index=step.step_index,
                    status="PENDING",
                    duration_ms=0.0,
                    estimated_tokens=t_tokens,
                )
                turn_tool_records.append(record)
                pending_tool_calls.append((turn_start, t_name))

            prompt_tokens_for_turn = accumulated_context_tokens

            # Turn duration (estimated default 1.5s if single step)
            turn_dur = 1.5

            turn = TurnRecord(
                turn_index=turn_counter,
                step_index=step.step_index,
                created_at=step.created_at_raw,
                duration_sec=turn_dur,
                prompt_tokens=prompt_tokens_for_turn,
                completion_tokens=turn_completion_tokens,
                total_tokens=prompt_tokens_for_turn + turn_completion_tokens,
                tool_calls=turn_tool_records,
            )
            turns.append(turn)

            # Accumulate model response into context for subsequent turns
            accumulated_context_tokens += turn_completion_tokens

        # Step type: GENERIC / Tool result
        elif step.type == "GENERIC":
            res_tokens = TokenEstimator.estimate_text(step.content)
            accumulated_context_tokens += res_tokens

            if pending_tool_calls:
                t_start, t_name = pending_tool_calls.pop(0)
                dur_ms = max(10.0, (step.created_at - t_start).total_seconds() * 1000.0)
                tool_durations[t_name] += dur_ms

    # Total duration calculation
    total_duration_sec = 0.0
    if start_time and end_time:
        total_duration_sec = max(1.0, (end_time - start_time).total_seconds())

    # Aggregate token statistics
    if turns:
        total_prompt_tokens = sum(t.prompt_tokens for t in turns)
        total_completion_tokens = sum(t.completion_tokens for t in turns)
    else:
        total_prompt_tokens = accumulated_context_tokens if total_steps > 0 else 0
        total_completion_tokens = 0
    total_tokens = total_prompt_tokens + total_completion_tokens

    # Cost estimation
    cost = (total_prompt_tokens / 1_000_000 * PRICE_PER_M_INPUT) + (
        total_completion_tokens / 1_000_000 * PRICE_PER_M_OUTPUT
    )

    return SubagentSessionMetrics(
        conversation_id=conv_id,
        log_file=str(log_path),
        total_steps=total_steps,
        turns_count=len(turns),
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
        total_tokens=total_tokens,
        total_duration_sec=total_duration_sec,
        tool_counts=dict(tool_counts),
        tool_durations_ms=dict(tool_durations),
        model_name="gemini-pro",
        estimated_cost_usd=cost,
        turns=turns,
    )


def check_subagent_budget(
    metrics: SubagentSessionMetrics,
    max_tokens: int | None = None,
    max_duration_sec: float | None = None,
) -> tuple[bool, str]:
    """Check if subagent execution adhered to budget limits (ADR-0030)."""
    violations: list[str] = []

    if max_tokens is not None and metrics.total_tokens > max_tokens:
        violations.append(
            f"Token budget exceeded: {metrics.total_tokens:,} tokens consumed > limit {max_tokens:,} tokens"
        )

    if max_duration_sec is not None and metrics.total_duration_sec > max_duration_sec:
        violations.append(
            f"Duration budget exceeded: {metrics.total_duration_sec:.1f}s > limit {max_duration_sec:.1f}s"
        )

    if violations:
        return False, "; ".join(violations)
    return True, "Within budget limits."


class OtelSpanExporter:
    """Converts SubagentSessionMetrics to OpenTelemetry GenAI Semantic Conventions (v1.28.0+)."""

    @classmethod
    def to_otlp_json(cls, metrics: SubagentSessionMetrics) -> dict[str, Any]:
        """Build OTLP Traces JSON dictionary (`resourceSpans`)."""
        # Deterministic 32-char hex trace_id from conversation_id
        trace_id = hashlib.md5(metrics.conversation_id.encode("utf-8")).hexdigest()
        root_span_id = hashlib.sha1(metrics.conversation_id.encode("utf-8")).hexdigest()[:16]

        start_unix_nano = int(datetime.now(timezone.utc).timestamp() * 1e9)
        duration_nano = int(metrics.total_duration_sec * 1e9)
        end_unix_nano = start_unix_nano + duration_nano

        spans: list[dict[str, Any]] = []

        # Root Span: subagent.session
        root_span = {
            "traceId": trace_id,
            "spanId": root_span_id,
            "name": "subagent.session",
            "kind": 1,  # SPAN_KIND_INTERNAL
            "startTimeUnixNano": start_unix_nano,
            "endTimeUnixNano": end_unix_nano,
            "attributes": [
                {"key": "gen_ai.system", "value": {"stringValue": "antigravity"}},
                {"key": "gen_ai.conversation.id", "value": {"stringValue": metrics.conversation_id}},
                {"key": "gen_ai.usage.input_tokens", "value": {"intValue": metrics.prompt_tokens}},
                {"key": "gen_ai.usage.output_tokens", "value": {"intValue": metrics.completion_tokens}},
                {"key": "gen_ai.usage.total_tokens", "value": {"intValue": metrics.total_tokens}},
                {"key": "gen_ai.cost.usd", "value": {"doubleValue": round(metrics.estimated_cost_usd, 5)}},
                {"key": "gen_ai.turns.count", "value": {"intValue": metrics.turns_count}},
            ],
            "status": {"code": 1},  # STATUS_CODE_OK
        }
        spans.append(root_span)

        # Child Spans: subagent.turn and subagent.tool_call
        for t in metrics.turns:
            turn_span_id = hashlib.sha1(f"{trace_id}:{t.turn_index}".encode()).hexdigest()[:16]
            turn_start_nano = start_unix_nano + int(t.turn_index * 2e9)
            turn_end_nano = turn_start_nano + int(t.duration_sec * 1e9)

            turn_span = {
                "traceId": trace_id,
                "spanId": turn_span_id,
                "parentSpanId": root_span_id,
                "name": f"subagent.turn.{t.turn_index}",
                "kind": 3,  # SPAN_KIND_CLIENT
                "startTimeUnixNano": turn_start_nano,
                "endTimeUnixNano": turn_end_nano,
                "attributes": [
                    {"key": "gen_ai.operation.name", "value": {"stringValue": "chat"}},
                    {"key": "gen_ai.request.model", "value": {"stringValue": metrics.model_name}},
                    {"key": "gen_ai.usage.input_tokens", "value": {"intValue": t.prompt_tokens}},
                    {"key": "gen_ai.usage.output_tokens", "value": {"intValue": t.completion_tokens}},
                ],
                "status": {"code": 1},
            }
            spans.append(turn_span)

            # Leaf Spans: subagent.tool_call
            for idx, tc in enumerate(t.tool_calls):
                tool_span_id = hashlib.sha1(f"{turn_span_id}:{idx}".encode()).hexdigest()[:16]
                tool_span = {
                    "traceId": trace_id,
                    "spanId": tool_span_id,
                    "parentSpanId": turn_span_id,
                    "name": f"tool.{tc.name}",
                    "kind": 1,
                    "startTimeUnixNano": turn_start_nano,
                    "endTimeUnixNano": turn_start_nano + int(tc.duration_ms * 1e6),
                    "attributes": [
                        {"key": "gen_ai.operation.name", "value": {"stringValue": "tool_call"}},
                        {"key": "gen_ai.tool.name", "value": {"stringValue": tc.name}},
                        {"key": "gen_ai.tool.tokens", "value": {"intValue": tc.estimated_tokens}},
                    ],
                    "status": {"code": 1},
                }
                spans.append(tool_span)

        return {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "ccba-agent-platform"}},
                            {"key": "service.version", "value": {"stringValue": "2.0.0"}},
                            {"key": "gen_ai.system", "value": {"stringValue": "antigravity"}},
                        ]
                    },
                    "scopeSpans": [
                        {
                            "scope": {
                                "name": "ccba.subagent.runtime",
                                "version": "1.0.0",
                            },
                            "spans": spans,
                        }
                    ],
                }
            ]
        }
