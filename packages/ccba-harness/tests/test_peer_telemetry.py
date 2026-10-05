"""packages/ccba-harness/tests/test_peer_telemetry.py - Unit tests for Model Provenance & Token Telemetry (ADR-0064).

Validates Pydantic schema validation, backward-compatibility, out-of-band extraction,
cost mode provenance, bounded retry with fallback degradation, and status.json aggregation.
"""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from ccba_harness.peer import (
    PeerVerdictBlock,
    PeerVerdictTelemetry,
    extract_grok_session_telemetry,
    parse_verdict_from_md,
    render_verdict_header,
    update_status_json,
)


def test_peer_verdict_telemetry_schema_validation():
    """Validates PeerVerdictTelemetry fields and extra="forbid" constraint."""
    telemetry = PeerVerdictTelemetry(
        session_id="test-session-123",
        primary_model="grok-4.7",
        input_tokens=1500,
        output_tokens=350,
        reasoning_tokens=800,
        cached_read_tokens=400,
        total_tokens=1850,
        model_calls=2,
        turn_count=3,
        cost_usd=0.0125,
        cost_mode="exact",
        duration_seconds=12.45,
    )
    assert telemetry.session_id == "test-session-123"
    assert telemetry.primary_model == "grok-4.7"
    assert telemetry.input_tokens == 1500
    assert telemetry.output_tokens == 350
    assert telemetry.reasoning_tokens == 800
    assert telemetry.cached_read_tokens == 400
    assert telemetry.total_tokens == 1850
    assert telemetry.model_calls == 2
    assert telemetry.turn_count == 3
    assert telemetry.cost_usd == 0.0125
    assert telemetry.cost_mode == "exact"
    assert telemetry.duration_seconds == 12.45

    # Extra fields must raise ValidationError
    with pytest.raises(ValidationError):
        PeerVerdictTelemetry(
            session_id="test-session-extra",
            primary_model="grok-4.7",
            input_tokens=100,
            output_tokens=50,
            unexpected_field="forbidden",  # type: ignore[call-arg]
        )


def test_peer_verdict_telemetry_backward_compatibility():
    """Validates that historical verdicts without telemetry field parse seamlessly."""
    legacy_md = """---
request_id: req-legacy-001
verdict: APPROVE
summary: Legacy verdict without telemetry
---
All tests passed cleanly without telemetry block.
"""
    verdict = parse_verdict_from_md(legacy_md)
    assert verdict is not None
    assert verdict.request_id == "req-legacy-001"
    assert verdict.verdict == "APPROVE"
    assert verdict.telemetry is None


def test_peer_verdict_telemetry_roundtrip_rendering():
    """Validates roundtrip serialization and parsing of verdict with telemetry."""
    telemetry = PeerVerdictTelemetry(
        session_id="sess-roundtrip-999",
        primary_model="grok-4.7",
        input_tokens=5000,
        output_tokens=1200,
        reasoning_tokens=3000,
        cached_read_tokens=2000,
        total_tokens=6200,
        model_calls=1,
        turn_count=2,
        cost_usd=0.035,
        cost_mode="exact",
        duration_seconds=8.2,
    )
    verdict = PeerVerdictBlock(
        request_id="req-telemetry-001",
        verdict="GATE_PASS",
        summary="Verdict with comprehensive telemetry",
        telemetry=telemetry,
    )
    rendered = render_verdict_header(verdict)
    body = "Detailed architecture review report content.\n"
    full_doc = rendered + body

    parsed = parse_verdict_from_md(full_doc)
    assert parsed is not None
    assert parsed.request_id == "req-telemetry-001"
    assert parsed.verdict == "GATE_PASS"
    assert parsed.telemetry is not None
    assert parsed.telemetry.session_id == "sess-roundtrip-999"
    assert parsed.telemetry.primary_model == "grok-4.7"
    assert parsed.telemetry.input_tokens == 5000
    assert parsed.telemetry.reasoning_tokens == 3000
    assert parsed.telemetry.cost_usd == 0.035
    assert parsed.telemetry.cost_mode == "exact"


def test_extract_grok_session_telemetry_exact_cost(monkeypatch):
    """Validates extraction of exact cost from xAI session payload (costUsdTicks)."""
    fake_session_output = {
        "session": {
            "primaryModelId": "grok-4.7",
            "inputTokens": 2500,
            "outputTokens": 800,
            "reasoningTokens": 1200,
            "cachedReadTokens": 1000,
            "totalTokens": 3300,
            "modelCalls": 1,
            "turnCount": 2,
            "costUsdTicks": 150,  # 150 / 10000 = $0.0150
        }
    }

    mock_run = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=["grok", "usage", "sess-test-1"],
            returncode=0,
            stdout=json.dumps(fake_session_output),
            stderr="",
        )
    )
    monkeypatch.setattr(subprocess, "run", mock_run)

    telemetry = extract_grok_session_telemetry(
        session_id="sess-test-1",
        timeout=2.0,
        fallback_prompt_text="Prompt text",
        fallback_resp_text="Response text",
        duration_seconds=5.5,
        fallback_model="grok-4.7",
    )

    assert telemetry.session_id == "sess-test-1"
    assert telemetry.primary_model == "grok-4.7"
    assert telemetry.input_tokens == 2500
    assert telemetry.output_tokens == 800
    assert telemetry.reasoning_tokens == 1200
    assert telemetry.cached_read_tokens == 1000
    assert telemetry.total_tokens == 3300
    assert telemetry.cost_usd == 0.0150
    assert telemetry.cost_mode == "exact"
    assert telemetry.duration_seconds == 5.5
    assert mock_run.call_count == 1


def test_extract_grok_session_telemetry_estimated_cost_gateway(monkeypatch):
    """Validates fallback to estimated cost when costUsdTicks is absent (e.g. Gateway)."""
    fake_session_output = {
        "session": {
            "primaryModelId": "gemini-38-flash",
            "inputTokens": 1_000_000,
            "outputTokens": 1_000_000,
            "reasoningTokens": 0,
            "cachedReadTokens": 0,
            "totalTokens": 2_000_000,
            "modelCalls": 2,
            "turnCount": 4,
        }
    }

    mock_run = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=["grok", "usage", "sess-test-2"],
            returncode=0,
            stdout=json.dumps(fake_session_output),
            stderr="",
        )
    )
    monkeypatch.setattr(subprocess, "run", mock_run)

    telemetry = extract_grok_session_telemetry(
        session_id="sess-test-2",
        timeout=2.0,
        fallback_prompt_text="Short prompt",
        fallback_resp_text="Short response",
        duration_seconds=3.2,
        fallback_model="gemini-38-flash",
    )

    assert telemetry.session_id == "sess-test-2"
    assert telemetry.primary_model == "gemini-38-flash"
    assert telemetry.cost_mode == "estimated"
    # rate card: $1.25/1M in + $5.00/1M out = $6.25
    assert telemetry.cost_usd == pytest.approx(6.25, abs=0.01)


def test_extract_grok_session_telemetry_fallback_graceful_degradation(monkeypatch):
    """Validates bounded retry (3 attempts) and graceful fallback to TokenEstimator on error."""
    call_count = 0

    def mock_run(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr="Session not found"
        )

    monkeypatch.setattr(subprocess, "run", mock_run)

    prompt = "This is a sample prompt for testing token fallback degradation." * 10
    resp = "This is a sample response generated during test." * 5

    telemetry = extract_grok_session_telemetry(
        session_id="sess-missing",
        timeout=2.0,
        fallback_prompt_text=prompt,
        fallback_resp_text=resp,
        duration_seconds=4.0,
        fallback_model="grok-4.7",
    )

    assert call_count == 3  # Initial + 2 retries
    assert telemetry.session_id == "sess-missing"
    assert telemetry.primary_model == "grok-4.7"
    assert telemetry.cost_mode == "estimated"
    assert telemetry.input_tokens > 0
    assert telemetry.output_tokens > 0
    assert telemetry.total_tokens == telemetry.input_tokens + telemetry.output_tokens
    assert telemetry.cost_usd >= 0.0


def test_update_status_json_telemetry_accumulation(tmp_path):
    """Validates accumulation of tokens and USD cost in status.json."""
    status_file = tmp_path / "status.json"

    # Initial registry with verdict 1
    verdict1 = PeerVerdictBlock(
        request_id="req-1",
        verdict="APPROVE",
        summary="Verdict 1",
        telemetry=PeerVerdictTelemetry(
            session_id="sess-1",
            primary_model="grok-4.7",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            cost_usd=0.01,
            cost_mode="exact",
        ),
    )
    registry = {
        "resp_1.md": {
            "path": tmp_path / "resp_1.md",
            "role": "GROK_RESPONSE",
            "sha256": "abc1",
            "verdict": verdict1,
        }
    }
    update_status_json(status_file, registry, pending_anti=[], pending_grok=[])

    data1 = json.loads(status_file.read_text(encoding="utf-8"))
    stats1 = data1["exchange_stats"]
    assert stats1["total_tokens"] == 1500
    assert stats1["total_cost_usd"] == 0.01
    assert stats1["by_model"]["grok-4.7"]["tokens"] == 1500
    assert stats1["by_model"]["grok-4.7"]["cost_usd"] == 0.01

    # Second verdict with different model added to registry
    verdict2 = PeerVerdictBlock(
        request_id="req-2",
        verdict="GATE_PASS",
        summary="Verdict 2",
        telemetry=PeerVerdictTelemetry(
            session_id="sess-2",
            primary_model="gemini-38-flash",
            input_tokens=2000,
            output_tokens=1000,
            total_tokens=3000,
            cost_usd=0.005,
            cost_mode="estimated",
        ),
    )
    registry["resp_2.md"] = {
        "path": tmp_path / "resp_2.md",
        "role": "GROK_RESPONSE",
        "sha256": "abc2",
        "verdict": verdict2,
    }
    update_status_json(status_file, registry, pending_anti=[], pending_grok=[])

    data2 = json.loads(status_file.read_text(encoding="utf-8"))
    stats2 = data2["exchange_stats"]
    assert stats2["total_tokens"] == 4500
    assert stats2["total_cost_usd"] == 0.015
    assert stats2["by_model"]["grok-4.7"]["tokens"] == 1500
    assert stats2["by_model"]["gemini-38-flash"]["tokens"] == 3000
    assert stats2["by_model"]["gemini-38-flash"]["cost_usd"] == 0.005
