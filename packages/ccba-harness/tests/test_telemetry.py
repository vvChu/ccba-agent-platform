"""test_telemetry.py - Unit test suite for OpenTelemetry Subagent Runtime & Token Monitoring Engine.

Verifies:
1. TokenEstimator accuracy for English, Vietnamese, and JSON payloads.
2. Zero-overhead streaming transcript parsing with byte-offsets.
3. SubagentSessionMetrics computation and turn-by-turn aggregation.
4. OpenTelemetry GenAI OTLP JSON trace compliance.
5. Dynamic Token Budgeting enforcement (ADR-0030).
6. CLI entry point operations for inspect and budget-check.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccba_harness.cli import run_telemetry_cli
from ccba_harness.telemetry import (
    OtelSpanExporter,
    SubagentSessionMetrics,
    TokenEstimator,
    analyze_subagent_transcript,
    check_subagent_budget,
    stream_transcript_steps,
)


def test_token_estimator_bilingual_and_json() -> None:
    """Verify TokenEstimator handles empty, English, Vietnamese, and JSON inputs."""
    assert TokenEstimator.estimate_text("") == 0

    # English text (~4 chars/token)
    en_text = "The quick brown fox jumps over the lazy dog."
    en_tokens = TokenEstimator.estimate_text(en_text)
    assert 10 <= en_tokens <= 15

    # Vietnamese text with diacritics (~2.8 chars/token)
    vi_text = "Hệ sinh thái kỹ năng của CCBA Agent Platform được thiết kế theo tiêu chuẩn công nghiệp."
    vi_tokens = TokenEstimator.estimate_text(vi_text)
    assert 25 <= vi_tokens <= 38

    # JSON payload
    payload = {"query": "test", "limit": 10, "nested": {"active": True}}
    json_tokens = TokenEstimator.estimate_json(payload)
    assert json_tokens > 0


def test_stream_transcript_steps(tmp_path: Path) -> None:
    """Verify stream_transcript_steps reads line-by-line and records byte offsets."""
    log_file = tmp_path / "transcript.jsonl"
    steps_data = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:00Z",
            "content": "Hello Agent",
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:02Z",
            "thinking": "Thinking about response",
            "tool_calls": [{"name": "list_dir", "args": {"path": "."}}],
        },
        {
            "step_index": 2,
            "source": "MODEL",
            "type": "GENERIC",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:03Z",
            "content": "file1.txt, file2.txt",
        },
    ]

    with log_file.open("w", encoding="utf-8") as f:
        for item in steps_data:
            f.write(json.dumps(item) + "\n")

    streamed = list(stream_transcript_steps(log_file))
    assert len(streamed) == 3

    step_0, offset_0 = streamed[0]
    assert step_0.step_index == 0
    assert step_0.type == "USER_INPUT"
    assert offset_0 > 0

    step_1, offset_1 = streamed[1]
    assert step_1.step_index == 1
    assert len(step_1.tool_calls) == 1
    assert offset_1 > offset_0


def test_analyze_subagent_transcript_and_markdown(tmp_path: Path) -> None:
    """Verify analyze_subagent_transcript aggregates metrics, turns, and tools."""
    log_file = tmp_path / "transcript.jsonl"
    steps = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:00Z",
            "content": "Scan repository files",
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:01Z",
            "thinking": "Starting discovery",
            "tool_calls": [{"name": "grep_search", "args": {"Query": "test"}}],
        },
        {
            "step_index": 2,
            "source": "MODEL",
            "type": "GENERIC",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:03Z",
            "content": "Found 5 matches",
        },
        {
            "step_index": 3,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:05Z",
            "thinking": "Completed scan",
            "content": "Report ready",
        },
    ]

    with log_file.open("w", encoding="utf-8") as f:
        for s in steps:
            f.write(json.dumps(s) + "\n")

    metrics = analyze_subagent_transcript(log_file)
    assert isinstance(metrics, SubagentSessionMetrics)
    assert metrics.total_steps == 4
    assert metrics.turns_count == 2
    assert metrics.tool_counts.get("grep_search") == 1
    assert metrics.total_tokens > 0
    assert metrics.total_duration_sec == 5.0
    assert metrics.estimated_cost_usd > 0

    md = metrics.to_markdown()
    assert "# 📊 Subagent Runtime Telemetry Report" in md
    assert "grep_search" in md

    d = metrics.to_dict()
    assert d["total_steps"] == 4
    assert "turns_summary" in d


def test_check_subagent_budget() -> None:
    """Verify check_subagent_budget enforces token and duration thresholds."""
    metrics = SubagentSessionMetrics(
        conversation_id="conv_123",
        log_file="fake.jsonl",
        total_steps=10,
        turns_count=5,
        prompt_tokens=40_000,
        completion_tokens=5_000,
        total_tokens=45_000,
        total_duration_sec=120.0,
    )

    # 1. Within limits
    ok, msg = check_subagent_budget(metrics, max_tokens=50_000, max_duration_sec=300.0)
    assert ok is True
    assert "Within budget" in msg

    # 2. Token budget exceeded
    ok_tok, msg_tok = check_subagent_budget(metrics, max_tokens=30_000)
    assert ok_tok is False
    assert "Token budget exceeded" in msg_tok

    # 3. Duration budget exceeded
    ok_dur, msg_dur = check_subagent_budget(metrics, max_duration_sec=60.0)
    assert ok_dur is False
    assert "Duration budget exceeded" in msg_dur


def test_otel_span_exporter_compliance(tmp_path: Path) -> None:
    """Verify OtelSpanExporter produces valid OpenTelemetry GenAI OTLP JSON."""
    log_file = tmp_path / "transcript.jsonl"
    steps = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:00Z",
            "content": "Run tests",
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:02Z",
            "thinking": "Invoking runner",
            "tool_calls": [{"name": "run_command", "args": {"CommandLine": "pytest"}}],
        },
    ]
    with log_file.open("w", encoding="utf-8") as f:
        for s in steps:
            f.write(json.dumps(s) + "\n")

    metrics = analyze_subagent_transcript(log_file)
    otlp = OtelSpanExporter.to_otlp_json(metrics)

    assert "resourceSpans" in otlp
    res = otlp["resourceSpans"][0]
    assert any(attr["key"] == "gen_ai.system" for attr in res["resource"]["attributes"])

    spans = res["scopeSpans"][0]["spans"]
    assert len(spans) >= 2  # Root span + turn span + tool span

    root = spans[0]
    assert root["name"] == "subagent.session"
    assert len(root["traceId"]) == 32
    assert len(root["spanId"]) == 16


def test_cli_telemetry_inspect_and_budget_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify run_telemetry_cli executes inspect and budget-check subcommands."""
    log_file = tmp_path / "transcript.jsonl"
    log_file.write_text(
        json.dumps(
            {
                "step_index": 0,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "status": "DONE",
                "created_at": "2026-09-10T08:00:00Z",
                "content": "Short test",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    # 1. Test inspect --json
    exit_code = run_telemetry_cli(["inspect", str(log_file), "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total_steps"] == 1

    # 2. Test budget-check pass
    exit_pass = run_telemetry_cli(["budget-check", str(log_file), "--max-tokens", "10000"])
    assert exit_pass == 0
    captured_pass = capsys.readouterr()
    assert "[PASS]" in captured_pass.out

    # 3. Test budget-check fail
    exit_fail = run_telemetry_cli(["budget-check", str(log_file), "--max-tokens", "1"])
    assert exit_fail == 1
    captured_fail = capsys.readouterr()
    assert "[FAIL]" in captured_fail.err
