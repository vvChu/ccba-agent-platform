"""Unit tests for Real-Time Telemetry Streaming Bridge to Server Spark."""

from __future__ import annotations

import http.server
import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from ccba_harness.cli import main as ccba_harness_main
from ccba_harness.streamer import (
    OfflineBufferManager,
    StreamingConfig,
    StreamingStatus,
    TelemetryEvent,
    TelemetryEventType,
    TelemetryStreamingBridge,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


class _MockTelemetryServer(http.server.HTTPServer):
    """Local mock HTTP server recording incoming telemetry events."""

    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.received_payloads: list[Any] = []


class _MockTelemetryHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler storing POSTed JSON payloads."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(body)
            self.server.received_payloads.append(data)
        except Exception:
            pass
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format, *args):
        pass  # suppress stderr logging


@pytest.fixture
def mock_spark_server():
    """Start an ephemeral localhost HTTP server simulating Server Spark."""
    server = _MockTelemetryServer(("127.0.0.1", 0), _MockTelemetryHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{port}/telemetry/events"
    yield endpoint, server
    server.shutdown()
    server.server_close()


@pytest.fixture
def sample_transcript_file(tmp_path: Path) -> Path:
    """Create a minimal transcript.jsonl with user and agent steps."""
    log_file = tmp_path / "transcript.jsonl"
    lines = [
        json.dumps(
            {
                "step_index": 1,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "status": "DONE",
                "created_at": "2026-09-10T10:00:00Z",
                "content": "Kiểm tra bản vẽ tầng 3",
            }
        ),
        json.dumps(
            {
                "step_index": 2,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-09-10T10:00:05Z",
                "content": "Tôi đang kiểm tra bản vẽ kết cấu.",
                "tool_calls": [{"name": "view_file", "args": {"path": "drawing.pdf"}}],
            }
        ),
    ]
    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_file


def test_telemetry_event_serialization():
    """Test TelemetryEvent creation, serialization and deserialization."""
    ev = TelemetryEvent(
        event_id="test-id-123",
        event_type=TelemetryEventType.TURN_COMPLETE.value,
        conversation_id="conv-abc",
        timestamp="2026-09-10T10:00:00Z",
        step_index=2,
        model_name="gemini-pro",
        payload={"prompt_tokens": 100, "completion_tokens": 50},
    )

    ev_dict = ev.to_dict()
    assert ev_dict["event_id"] == "test-id-123"
    assert ev_dict["payload"]["prompt_tokens"] == 100

    json_str = ev.to_json()
    assert "conv-abc" in json_str

    restored = TelemetryEvent.from_dict(json.loads(json_str))
    assert restored.event_id == ev.event_id
    assert restored.step_index == 2
    assert restored.payload["completion_tokens"] == 50


def test_offline_buffer_manager(tmp_path: Path):
    """Test OfflineBufferManager appending, counting, reading and clearing."""
    buffer_file = tmp_path / "offline_buffer.jsonl"
    mgr = OfflineBufferManager(buffer_file)

    assert mgr.count_buffered() == 0

    ev1 = TelemetryEvent(
        event_id="e1",
        event_type="turn_start",
        conversation_id="conv-1",
        timestamp="2026-09-10T10:00:00Z",
        step_index=1,
        model_name="user",
    )
    ev2 = TelemetryEvent(
        event_id="e2",
        event_type="turn_complete",
        conversation_id="conv-1",
        timestamp="2026-09-10T10:00:05Z",
        step_index=2,
        model_name="gemini-pro",
    )

    mgr.append_event(ev1)
    mgr.append_event(ev2)

    assert mgr.count_buffered() == 2

    events = mgr.read_buffered_events()
    assert len(events) == 2
    assert events[0].event_id == "e1"
    assert events[1].event_id == "e2"

    mgr.clear()
    assert mgr.count_buffered() == 0


def test_streamer_bridge_dry_run():
    """Test TelemetryStreamingBridge in dry-run mode."""
    cfg = StreamingConfig(dry_run=True)
    bridge = TelemetryStreamingBridge(config=cfg)

    ev = TelemetryEvent(
        event_id="e-dry",
        event_type="test",
        conversation_id="c-dry",
        timestamp="2026-09-10T10:00:00Z",
        step_index=1,
        model_name="test",
    )

    success = bridge.send_event(ev)
    assert success is True
    assert bridge.test_connection() is True


def test_streamer_bridge_offline_fallback(tmp_path: Path):
    """Test graceful degradation to offline buffer when network fails."""
    buffer_file = tmp_path / "fallback_buffer.jsonl"
    # Use an unallocated port to guarantee connection refusal
    cfg = StreamingConfig(
        endpoint_url="http://127.0.0.1:59991/telemetry/events",
        buffer_path=buffer_file,
        timeout_sec=0.5,
        dry_run=False,
    )
    bridge = TelemetryStreamingBridge(config=cfg)

    ev = TelemetryEvent(
        event_id="e-fallback",
        event_type="turn_complete",
        conversation_id="c-fallback",
        timestamp="2026-09-10T10:00:00Z",
        step_index=1,
        model_name="gemini-pro",
    )

    # Invariant: Never raise exceptions to caller
    delivered = bridge.send_batch([ev])
    assert delivered == 0
    assert bridge.status == StreamingStatus.OFFLINE_BUFFERING

    # Verify event was safely persisted to offline buffer
    assert buffer_file.exists()
    assert bridge.buffer.count_buffered() == 1


def test_stream_transcript_mock_http_server(
    mock_spark_server, sample_transcript_file: Path, tmp_path: Path
):
    """Test end-to-end streaming from transcript file to local mock server."""
    endpoint, server = mock_spark_server
    buffer_file = tmp_path / "buffer.jsonl"

    cfg = StreamingConfig(
        endpoint_url=endpoint,
        buffer_path=buffer_file,
        dry_run=False,
    )
    bridge = TelemetryStreamingBridge(config=cfg)

    assert bridge.test_connection() is True

    report = bridge.stream_transcript_file(sample_transcript_file)
    assert report.events_emitted == 2
    assert report.events_delivered == 2
    assert report.events_buffered == 0
    assert report.status == StreamingStatus.CONNECTED.value

    assert len(server.received_payloads) >= 1

    # Test flush buffer when empty
    flushed = bridge.flush_buffer()
    assert flushed == 0


def test_cli_telemetry_stream_subcommand(sample_transcript_file: Path):
    """Test ccba-harness telemetry stream CLI integration."""
    rc = ccba_harness_main(
        ["telemetry", "stream", str(sample_transcript_file), "--dry-run", "--json"]
    )
    assert rc == 0


def test_cli_telemetry_streamer_script(sample_transcript_file: Path):
    """Test standalone scripts/governance/telemetry_streamer.py execution."""
    script_path = (
        Path(__file__).resolve().parent.parent.parent
        / "scripts"
        / "governance"
        / "telemetry_streamer.py"
    )

    res = subprocess.run(
        [sys.executable, str(script_path), "status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0
    assert "Telemetry Streaming Status" in res.stdout

    res_stream = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "stream",
            str(sample_transcript_file),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert res_stream.returncode == 0
    data = json.loads(res_stream.stdout)
    assert data["events_emitted"] == 2
