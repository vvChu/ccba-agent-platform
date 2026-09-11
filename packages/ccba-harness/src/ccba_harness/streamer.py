"""streamer.py - Real-Time Telemetry Streaming Bridge to Server Spark.

Provides real-time event streaming for Antigravity subagent transcripts (ADR-0046, ADR-0058):
1. TelemetryEvent: Standardized telemetry schema for turns, tool calls, and lifecycle events.
2. OfflineBufferManager: Resilient append-only file buffer for offline & disconnected states.
3. AsyncTranscriptFollower: Async watcher extracting events from live transcript.jsonl.
4. TelemetryStreamingBridge: High-throughput, non-blocking bridge to Server Spark (:8090).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .telemetry import TokenEstimator, resolve_transcript_path

logger = logging.getLogger(__name__)

DEFAULT_SPARK_TELEMETRY_URL = os.environ.get(
    "CCBA_TELEMETRY_STREAM_URL", "http://100.83.192.30:8090/telemetry/events"
)
DEFAULT_BUFFER_PATH = Path(".md/telemetry/offline_buffer.jsonl")


class StreamingStatus(str, Enum):
    """Network connection status of the telemetry bridge."""

    CONNECTED = "CONNECTED"
    OFFLINE_BUFFERING = "OFFLINE_BUFFERING"
    DRAINED = "DRAINED"
    FAILED = "FAILED"


class TelemetryEventType(str, Enum):
    """Types of real-time telemetry events emitted during agent execution."""

    SESSION_START = "session_start"
    TURN_START = "turn_start"
    TOOL_CALL = "tool_call"
    TURN_COMPLETE = "turn_complete"
    BUDGET_ALERT = "budget_alert"
    ERROR = "error"
    SESSION_COMPLETE = "session_complete"


@dataclass
class TelemetryEvent:
    """Standardized event emitted over the real-time telemetry stream."""

    event_id: str
    event_type: str
    conversation_id: str
    timestamp: str
    step_index: int
    model_name: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to a serializable dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TelemetryEvent:
        """Construct a TelemetryEvent from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=data.get("event_type", TelemetryEventType.TURN_COMPLETE.value),
            conversation_id=data.get("conversation_id", "unknown"),
            timestamp=data.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            step_index=data.get("step_index", 0),
            model_name=data.get("model_name", "gemini-pro"),
            payload=data.get("payload", {}),
        )


@dataclass
class StreamingConfig:
    """Configuration options for the Telemetry Streaming Bridge."""

    endpoint_url: str = DEFAULT_SPARK_TELEMETRY_URL
    buffer_path: Path = DEFAULT_BUFFER_PATH
    timeout_sec: float = 3.0
    batch_size: int = 10
    flush_interval_sec: float = 0.5
    max_buffer_events: int = 5000
    dry_run: bool = False


@dataclass
class StreamingReport:
    """Summary metrics of a streaming session or batch dispatch."""

    events_emitted: int = 0
    events_buffered: int = 0
    events_delivered: int = 0
    status: str = StreamingStatus.CONNECTED.value
    endpoint: str = DEFAULT_SPARK_TELEMETRY_URL
    buffer_file: str = str(DEFAULT_BUFFER_PATH)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OfflineBufferManager:
    """Manages resilient local append-only buffer when Server Spark is unreachable."""

    def __init__(self, buffer_path: Path | str, max_events: int = 5000) -> None:
        self.buffer_path = Path(buffer_path)
        self.max_events = max_events

    def append_event(self, event: TelemetryEvent) -> bool:
        """Append an event to the local offline buffer file safely."""
        try:
            self.buffer_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.buffer_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
            return True
        except Exception as exc:
            logger.warning("Failed to write offline telemetry buffer: %s", exc)
            return False

    def count_buffered(self) -> int:
        """Count number of events waiting in local buffer."""
        if not self.buffer_path.exists():
            return 0
        try:
            with open(self.buffer_path, encoding="utf-8", errors="replace") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def read_buffered_events(self, limit: int | None = None) -> list[TelemetryEvent]:
        """Read pending events from the offline buffer."""
        if not self.buffer_path.exists():
            return []
        events: list[TelemetryEvent] = []
        try:
            with open(self.buffer_path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(TelemetryEvent.from_dict(json.loads(line)))
                        if limit and len(events) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            logger.warning("Failed to read buffered events: %s", exc)
        return events

    def clear(self) -> None:
        """Clear the offline buffer file after successful draining."""
        if self.buffer_path.exists():
            try:
                self.buffer_path.unlink()
            except Exception as exc:
                logger.warning("Failed to clear offline buffer file: %s", exc)


class AsyncTranscriptFollower:
    """Watches and streams events from a transcript.jsonl file asynchronously."""

    def __init__(self, log_path: Path | str, poll_interval_sec: float = 0.2) -> None:
        self.log_path = Path(log_path)
        self.poll_interval_sec = poll_interval_sec
        self._last_seek = 0
        self._turn_index = 0

    async def follow(
        self,
        stop_on_eof: bool = False,
        max_idle_seconds: float = 5.0,
    ) -> AsyncGenerator[TelemetryEvent, None]:
        """Asynchronously yield TelemetryEvent instances as lines are written."""
        idle_time = 0.0
        while True:
            if not self.log_path.exists():
                if stop_on_eof:
                    break
                await asyncio.sleep(self.poll_interval_sec)
                idle_time += self.poll_interval_sec
                if idle_time > max_idle_seconds:
                    break
                continue

            new_lines = self._read_new_lines()
            if not new_lines:
                if stop_on_eof:
                    break
                await asyncio.sleep(self.poll_interval_sec)
                idle_time += self.poll_interval_sec
                if idle_time > max_idle_seconds:
                    break
                continue

            idle_time = 0.0
            for line in new_lines:
                event = self._parse_line_to_event(line)
                if event:
                    yield event

    def _read_new_lines(self) -> list[str]:
        """Read newly appended lines since last seek position."""
        lines = []
        try:
            with open(self.log_path, encoding="utf-8", errors="replace") as f:
                f.seek(self._last_seek)
                for line in f:
                    if line.endswith("\n"):
                        lines.append(line)
                        self._last_seek = f.tell()
        except Exception:
            pass
        return lines

    def _parse_line_to_event(self, line: str) -> TelemetryEvent | None:
        """Parse raw JSON transcript line into a TelemetryEvent."""
        try:
            data = json.loads(line)
        except Exception:
            return None

        step_type = data.get("type", "")
        step_index = data.get("step_index", 0)
        created_at = data.get("created_at", "")
        content = data.get("content", "") or ""
        tool_calls = data.get("tool_calls", []) or []
        status = data.get("status", "DONE")

        conv_id = (
            self.log_path.parent.parent.name if self.log_path.parent.name == "logs" else "unknown"
        )

        if step_type == "USER_INPUT":
            self._turn_index += 1
            return TelemetryEvent(
                event_id=str(uuid.uuid4()),
                event_type=TelemetryEventType.TURN_START.value,
                conversation_id=conv_id,
                timestamp=created_at,
                step_index=step_index,
                model_name="user",
                payload={"turn_index": self._turn_index, "content_len": len(content)},
            )

        if step_type == "PLANNER_RESPONSE":
            compl_toks = TokenEstimator.estimate_text(content)
            tool_toks = TokenEstimator.estimate_json(tool_calls)
            prompt_toks = 1500
            return TelemetryEvent(
                event_id=str(uuid.uuid4()),
                event_type=TelemetryEventType.TURN_COMPLETE.value,
                conversation_id=conv_id,
                timestamp=created_at,
                step_index=step_index,
                model_name="gemini-pro",
                payload={
                    "turn_index": self._turn_index,
                    "prompt_tokens": prompt_toks,
                    "completion_tokens": compl_toks + tool_toks,
                    "total_tokens": prompt_toks + compl_toks + tool_toks,
                    "tool_calls_count": len(tool_calls),
                    "status": status,
                },
            )

        return None


class TelemetryStreamingBridge:
    """High-throughput bridge dispatching real-time telemetry to Server Spark (:8090).

    Graceful degradation:
    - Never raises network exceptions to callers.
    - If Spark is unreachable, queues events to local OfflineBufferManager.
    - Supports flushing buffered events once connection is restored.
    """

    def __init__(self, config: StreamingConfig | None = None) -> None:
        self.config = config or StreamingConfig()
        self.buffer = OfflineBufferManager(
            self.config.buffer_path, max_events=self.config.max_buffer_events
        )
        self.status = StreamingStatus.CONNECTED

    def test_connection(self) -> bool:
        """Ping the telemetry endpoint to verify Server Spark connectivity."""
        if self.config.dry_run:
            return True
        try:
            req = urllib.request.Request(
                self.config.endpoint_url,
                data=json.dumps({"ping": True}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CCBA-Telemetry-Bridge/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout_sec) as resp:
                return resp.status in (200, 201, 202, 204)
        except Exception:
            return False

    def send_event(self, event: TelemetryEvent) -> bool:
        """Send a single telemetry event synchronously or buffer offline."""
        return self.send_batch([event]) > 0

    def send_batch(self, events: Sequence[TelemetryEvent]) -> int:
        """Send a batch of events to Server Spark or fallback to offline buffer.

        Returns:
            Number of events successfully delivered over network or dry-run.
        """
        if not events:
            return 0

        if self.config.dry_run:
            return len(events)

        payload_bytes = json.dumps([e.to_dict() for e in events], ensure_ascii=False).encode(
            "utf-8"
        )
        try:
            req = urllib.request.Request(
                self.config.endpoint_url,
                data=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CCBA-Telemetry-Bridge/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout_sec) as resp:
                if resp.status in (200, 201, 202, 204):
                    self.status = StreamingStatus.CONNECTED
                    return len(events)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            logger.debug(
                "Telemetry endpoint unreachable, buffering %d events: %s", len(events), exc
            )

        # Fallback to local offline buffer
        self.status = StreamingStatus.OFFLINE_BUFFERING
        for e in events:
            self.buffer.append_event(e)
        return 0

    def flush_buffer(self) -> int:
        """Attempt to flush pending offline events to Server Spark."""
        buffered_events = self.buffer.read_buffered_events()
        if not buffered_events:
            return 0

        delivered = self.send_batch(buffered_events)
        if delivered == len(buffered_events):
            self.buffer.clear()
            self.status = StreamingStatus.DRAINED
            logger.info("Successfully flushed %d offline telemetry events to Spark", delivered)
            return delivered

        return delivered

    def stream_transcript_file(
        self,
        target: str | Path,
        dry_run: bool = False,
    ) -> StreamingReport:
        """Stream an existing or active transcript to Server Spark."""
        log_path = resolve_transcript_path(str(target))
        if not log_path or not log_path.exists():
            return StreamingReport(
                events_emitted=0,
                status=StreamingStatus.FAILED.value,
                errors=[f"Transcript file not found: {target}"],
            )

        report = StreamingReport(
            endpoint=self.config.endpoint_url,
            buffer_file=str(self.config.buffer_path),
        )

        follower = AsyncTranscriptFollower(log_path)
        events_to_send: list[TelemetryEvent] = []

        # Synchronous read of all events in file
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            ev = follower._parse_line_to_event(line)
            if ev:
                events_to_send.append(ev)

        report.events_emitted = len(events_to_send)

        old_dry = self.config.dry_run
        if dry_run:
            self.config.dry_run = True

        try:
            delivered = self.send_batch(events_to_send)
            report.events_delivered = delivered
            report.events_buffered = report.events_emitted - delivered
            report.status = self.status.value
        finally:
            self.config.dry_run = old_dry

        return report
