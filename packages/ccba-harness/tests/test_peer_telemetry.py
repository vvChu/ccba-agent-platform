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
            "costUsdTicks": 150_000_000,  # 150_000_000 / 10^10 = $0.0150
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


def test_extract_grok_session_telemetry_estimated_cost_qwen_local(monkeypatch):
    """Validates that qwen-local (offline DGX GB10 GPU) estimates $0.00 cost."""
    fake_session_output = {
        "session": {
            "primaryModelId": "qwen-local",
            "inputTokens": 500_000,
            "outputTokens": 50_000,
            "reasoningTokens": 0,
            "cachedReadTokens": 0,
            "totalTokens": 550_000,
            "modelCalls": 1,
            "turnCount": 1,
        }
    }

    mock_run = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=["grok", "usage", "sess-test-qwen"],
            returncode=0,
            stdout=json.dumps(fake_session_output),
            stderr="",
        )
    )
    monkeypatch.setattr(subprocess, "run", mock_run)

    telemetry = extract_grok_session_telemetry(
        session_id="sess-test-qwen",
        timeout=2.0,
        fallback_prompt_text="Short prompt",
        fallback_resp_text="Short response",
        duration_seconds=1.5,
        fallback_model="qwen-local",
    )

    assert telemetry.session_id == "sess-test-qwen"
    assert telemetry.primary_model == "qwen-local"
    assert telemetry.cost_mode == "estimated"
    assert telemetry.cost_usd == 0.0


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


def test_update_status_json_combined_telemetry_accumulation(tmp_path):
    """Validates CombinedTelemetry parsing in PeerVerdictBlock and status.json breakdown accumulation."""
    from ccba_harness.peer import CombinedTelemetry, ProfileTelemetryItem, parse_verdict_from_md

    consensus_md = (
        "---\n"
        "request_id: req-consensus-01\n"
        "verdict: APPROVE_WITH_CONDITIONS\n"
        "risk_score: 2\n"
        "summary: Consensus report\n"
        "telemetry:\n"
        "  total_tokens: 15000\n"
        "  input_tokens: 12000\n"
        "  output_tokens: 3000\n"
        "  reasoning_tokens: 1000\n"
        "  cached_read_tokens: 8000\n"
        "  cost_usd: 0.045\n"
        "  wall_seconds: 25.0\n"
        "  sum_agent_seconds: 40.0\n"
        "  cost_mode: exact\n"
        "  profile_breakdown:\n"
        "    code_review:\n"
        "      model: gemini-3.8-flash-high\n"
        "      total_tokens: 5000\n"
        "      cost_usd: 0.015\n"
        "    arch_audit:\n"
        "      model: grok-4.7-build\n"
        "      total_tokens: 10000\n"
        "      cost_usd: 0.030\n"
        "---\n"
        "# Consensus\n"
    )
    vb = parse_verdict_from_md(consensus_md)
    assert vb is not None
    assert isinstance(vb.telemetry, CombinedTelemetry)
    assert isinstance(vb.telemetry.profile_breakdown["code_review"], ProfileTelemetryItem)

    status_file = tmp_path / "status.json"
    registry = {
        "grok_consensus_01.md": {
            "path": tmp_path / "grok_consensus_01.md",
            "role": "GROK_RESPONSE",
            "mtime": 100.0,
            "sha256": "def456",
            "verdict": vb,
        }
    }
    update_status_json(status_file, registry, pending_anti=[], pending_grok=[])
    stats = json.loads(status_file.read_text(encoding="utf-8"))["exchange_stats"]
    assert stats["total_tokens"] == 15000
    assert stats["total_cost_usd"] == 0.045
    assert stats["by_model"]["gemini-3.8-flash-high"]["tokens"] == 5000
    assert stats["by_model"]["grok-4.7-build"]["tokens"] == 10000


def test_extract_grok_session_telemetry_multi_turn_resume_and_degraded_reasoning(monkeypatch):
    """Verifies turns[-1] selection on resumed sessions and degraded_reasoning flag when reasoningTokens==0."""
    from ccba_harness.peer import synthesize_verdicts

    usage_payload = {
        "sessionId": "sess-resumed",
        "session": {
            "primaryModelId": "grok-4.7",
            "inputTokens": 100000,
            "outputTokens": 2000,
            "reasoningTokens": 5000,
            "cachedReadTokens": 20000,
            "totalTokens": 102000,
            "modelCalls": 4,
            "turnCount": 2,
        },
        "turns": [
            {
                "turnNumber": 1,
                "inputTokens": 100000,
                "outputTokens": 2000,
                "reasoningTokens": 5000,
                "cachedReadTokens": 20000,
                "totalTokens": 102000,
                "modelCalls": 4,
            },
            {
                "turnNumber": 2,
                "inputTokens": 110000,
                "outputTokens": 1500,
                "reasoningTokens": 0,
                "cachedReadTokens": 98000,
                "totalTokens": 111500,
                "modelCalls": 2,
                "costUsdTicks": 250000000,
            },
        ],
    }

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=json.dumps(usage_payload), stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)

    tel = extract_grok_session_telemetry(
        session_id="sess-resumed",
        duration_seconds=12.3,
        fallback_model="grok-4.7",
        expected_reasoning_effort="xhigh",
    )
    assert tel is not None
    assert tel.input_tokens == 110000
    assert tel.cached_read_tokens == 98000
    assert tel.reasoning_tokens == 0
    assert tel.degraded_reasoning is True

    vb = PeerVerdictBlock(
        request_id="req-deg-1",
        verdict="APPROVE",
        risk_score=1,
        summary="Looks clean",
        telemetry=tel,
    )
    report = synthesize_verdicts("req-deg-1", {"arch_audit": vb})
    assert report.verdict == "APPROVE_WITH_CONDITIONS"
    assert any(c.id == "COND-DEGRADED-REASONING" and c.blocking for c in report.conditions)

    # Verify synthesize_turns=2 sums turns[-2:] while keeping last-turn degraded_reasoning (COND-02)
    tel_synth = extract_grok_session_telemetry(
        session_id="sess-resumed",
        duration_seconds=35.0,
        fallback_model="grok-4.7",
        expected_reasoning_effort="xhigh",
        synthesize_turns=2,
    )
    assert tel_synth is not None
    assert tel_synth.turn_count == 2
    assert tel_synth.input_tokens == 210000
    assert tel_synth.output_tokens == 3500
    assert tel_synth.reasoning_tokens == 5000
    assert tel_synth.cached_read_tokens == 118000
    assert tel_synth.total_tokens == 213500
    assert tel_synth.model_calls == 6
    assert tel_synth.degraded_reasoning is True

    # Verify forked child session (len(turns) == 1) sums parent_session_id counters (COND-02)
    child_payload = {
        "session": {"primaryModelId": "grok-4.7", "turnCount": 1},
        "turns": [
            {
                "turnNumber": 1,
                "inputTokens": 40000,
                "outputTokens": 1200,
                "reasoningTokens": 800,
                "cachedReadTokens": 38000,
                "totalTokens": 41200,
                "modelCalls": 1,
                "costUsdTicks": 100000000,
            }
        ],
    }
    parent_payload = {
        "session": {"primaryModelId": "grok-4.7", "turnCount": 1},
        "turns": [
            {
                "turnNumber": 1,
                "inputTokens": 60000,
                "outputTokens": 800,
                "reasoningTokens": 4000,
                "cachedReadTokens": 10000,
                "totalTokens": 60800,
                "modelCalls": 8,
                "costUsdTicks": 300000000,
            }
        ],
    }

    def mock_run_fork(cmd, **kwargs):
        target_sid = cmd[2]
        body = child_payload if target_sid == "child-sid" else parent_payload
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=json.dumps(body), stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run_fork)
    tel_fork = extract_grok_session_telemetry(
        session_id="child-sid",
        duration_seconds=42.5,
        fallback_model="grok-4.7",
        expected_reasoning_effort="xhigh",
        synthesize_turns=2,
        parent_session_id="parent-sid",
    )
    assert tel_fork is not None
    assert tel_fork.turn_count == 2
    assert tel_fork.input_tokens == 100000
    assert tel_fork.output_tokens == 2000
    assert tel_fork.reasoning_tokens == 4800
    assert tel_fork.cached_read_tokens == 48000
    assert tel_fork.total_tokens == 102000
    assert tel_fork.model_calls == 9
    assert tel_fork.cost_usd == 0.04
    assert tel_fork.degraded_reasoning is False

    # Verify synthesize_turns=1 on 1-turn child_payload still overlays turns[0] counters
    tel_single = extract_grok_session_telemetry(
        session_id="child-sid",
        duration_seconds=10.0,
        fallback_model="grok-4.7",
        expected_reasoning_effort="xhigh",
        synthesize_turns=1,
    )
    assert tel_single is not None
    assert tel_single.turn_count == 1
    assert tel_single.input_tokens == 40000
    assert tel_single.reasoning_tokens == 800
    assert tel_single.degraded_reasoning is False


def test_single_dispatch_finalize_degraded_reasoning_and_unconditional_rerender(
    tmp_path, monkeypatch
):
    """Verifies single-profile _finalize_grok_verdict_and_telemetry enforces degraded_reasoning and COND-RE-RENDER-ON-MUTATION."""
    from ccba_harness.peer import _build_latest_verdict, _finalize_grok_verdict_and_telemetry

    prompt_file = tmp_path / "prompt_single.md"
    prompt_file.write_text("---\nrequest_id: req-s1\n---\nBody", encoding="utf-8")
    out_file = tmp_path / "grok_single.md"

    # Case 1: session_id=None, verdict=APPROVE but risk_score=4 -> must downgrade and re-render on disk
    raw_high_risk = "---\nrequest_id: req-s1\nverdict: APPROVE\nrisk_score: 4\nsummary: High risk\n---\n# Body\n"
    ok1 = _finalize_grok_verdict_and_telemetry(
        stdout_text=raw_high_risk,
        prompt_path=prompt_file,
        output_file=out_file,
        duration=1.5,
        session_id=None,
        candidate_model="grok-4.7",
        expected_reasoning_effort="xhigh",
    )
    assert ok1 is True
    parsed1 = parse_verdict_from_md(out_file.read_text(encoding="utf-8"))
    assert parsed1 is not None
    assert parsed1.verdict == "APPROVE_WITH_CONDITIONS"

    # Case 2: session_id provided, grok usage reports reasoningTokens=0 on xhigh -> injects COND-DEGRADED-REASONING
    usage_zero = {
        "session": {
            "primaryModelId": "grok-4.7",
            "inputTokens": 1000,
            "outputTokens": 200,
            "reasoningTokens": 0,
            "totalTokens": 1200,
        }
    }
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(
            args=a[0], returncode=0, stdout=json.dumps(usage_zero), stderr=""
        ),
    )
    raw_clean = (
        "---\nrequest_id: req-s2\nverdict: APPROVE\nrisk_score: 1\nsummary: Clean\n---\n# Body\n"
    )
    ok2 = _finalize_grok_verdict_and_telemetry(
        stdout_text=raw_clean,
        prompt_path=prompt_file,
        output_file=out_file,
        duration=2.0,
        session_id="sess-zero-rsn",
        candidate_model="grok-4.7",
        expected_reasoning_effort="xhigh",
    )
    assert ok2 is True
    parsed2 = parse_verdict_from_md(out_file.read_text(encoding="utf-8"))
    assert parsed2 is not None
    assert parsed2.verdict == "APPROVE_WITH_CONDITIONS"
    assert any(c.id == "COND-DEGRADED-REASONING" and c.blocking for c in parsed2.conditions)

    # Case 3: Deterministic tie-breaking in _build_latest_verdict when mtime is equal
    reg = {
        "b.md": {
            "role": "GROK_RESPONSE",
            "path": tmp_path / "grok_b.md",
            "mtime": 100.0,
            "verdict": parsed1,
        },
        "a.md": {
            "role": "GROK_RESPONSE",
            "path": tmp_path / "grok_a.md",
            "mtime": 100.0,
            "verdict": parsed2,
        },
    }
    latest = _build_latest_verdict(reg)
    assert latest is not None
    assert latest["output_path"] == "grok_b.md"

    # Case 4: same mtime, newer frontmatter timestamp wins over the greater filename
    reg_ts = {
        "b.md": {
            "role": "GROK_RESPONSE",
            "path": tmp_path / "grok_b.md",
            "mtime": 100.0,
            "timestamp": "2026-10-01T00:00:00Z",
            "verdict": parsed1,
        },
        "a.md": {
            "role": "GROK_RESPONSE",
            "path": tmp_path / "grok_a.md",
            "mtime": 100.0,
            "timestamp": "2026-10-18T00:00:00Z",
            "verdict": parsed2,
        },
    }
    latest_ts = _build_latest_verdict(reg_ts)
    assert latest_ts is not None
    assert latest_ts["output_path"] == "grok_a.md"


def test_auto_discover_resume_session_3_tiers_bloat_and_dedup(tmp_path, capsys):
    """Verifies 3-tier session auto-discovery, fork_session=False default, bloat warning, and snapshot dedup."""
    from ccba_harness.peer import (
        PROFILE_SPECS,
        PeerPromptEnvelope,
        _resolve_grok_profile_options,
        render_prompt_header,
        render_verdict_header,
    )

    # 1. Seed Round 1 prompt and verdict for Chapter 8 (Tier 1 & Tier 2)
    p1_env = PeerPromptEnvelope(
        request_id="req-20261108-ai-eos-ch08",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Ch 8 v1",
        timestamp="2026-11-08T16:00:00+07:00",
        source_documents=["04 - Permanent/topics/chuong_8.md"],
        output_path="grok_review_chuong_8.md",
        profile="audit_direct",
    )
    (tmp_path / "prompt_grok_review_chuong_8.md").write_text(
        render_prompt_header(p1_env) + "Body v1", encoding="utf-8"
    )
    v1 = PeerVerdictBlock(
        request_id="req-20261108-ai-eos-ch08",
        verdict="APPROVE_WITH_CONDITIONS",
        summary="v1",
        telemetry=PeerVerdictTelemetry(
            session_id="sess-ch08-v1",
            primary_model="gemini-3.8-flash-high",
            input_tokens=1000,
            output_tokens=200,
            total_tokens=1200,
            turn_count=1,
            cost_usd=0.02,
        ),
    )
    (tmp_path / "grok_review_chuong_8.md").write_text(
        render_verdict_header(v1) + "\n# V1", encoding="utf-8"
    )

    # Tier 1: v2 prompt without explicit resume_session_id auto-discovers sess-ch08-v1 with fork_session=False
    p2_env = PeerPromptEnvelope(
        request_id="req-20261108-ai-eos-ch08-v2",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Ch 8 v2",
        timestamp="2026-11-08T18:16:00+07:00",
        output_path="grok_review_chuong_8_v2.md",
        profile="audit_direct",
    )
    p2_path = tmp_path / "prompt_grok_review_chuong_8_v2.md"
    p2_path.write_text(render_prompt_header(p2_env) + ("Line\n" * 405), encoding="utf-8")
    opts_t1 = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_direct"], p2_env, None, None, False, None, None, p2_path
    )
    assert opts_t1["resume_session_id"] == "sess-ch08-v1"
    assert opts_t1["fork_session"] is False
    assert "[WARN-RESUMED-PAYLOAD-BLOAT]" in capsys.readouterr().err

    # Opt-out ("new") disables auto-resume
    opts_new = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_direct"], p2_env, None, None, False, "new", None, p2_path
    )
    assert opts_new["resume_session_id"] is None

    # Tier 2: Different request_id stem but matching source_documents auto-discovers sess-ch08-v1
    p_doc_env = PeerPromptEnvelope(
        request_id="req-custom-delta-check",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Delta check",
        timestamp="2026-11-08T18:20:00+07:00",
        source_documents=["04 - Permanent/topics/chuong_8.md"],
        output_path="grok_custom_delta.md",
    )
    p_doc_path = tmp_path / "prompt_custom_delta.md"
    p_doc_path.write_text(render_prompt_header(p_doc_env) + "Short delta", encoding="utf-8")
    opts_t2 = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_plan"], p_doc_env, None, None, False, None, None, p_doc_path
    )
    assert opts_t2["resume_session_id"] == "sess-ch08-v1"
    assert opts_t2["fork_session"] is False

    # Tier 3: Continuous discussion session
    v_disc = PeerVerdictBlock(
        request_id="req-discuss-arch-01",
        verdict="APPROVE_PLAN",
        summary="Discuss turn 1",
        telemetry=PeerVerdictTelemetry(
            session_id="sess-discuss-01",
            primary_model="grok-4.7",
            input_tokens=500,
            output_tokens=100,
            total_tokens=600,
            turn_count=1,
            cost_usd=0.01,
        ),
    )
    (tmp_path / "grok_discuss_01.md").write_text(
        render_verdict_header(v_disc) + "\n# D1", encoding="utf-8"
    )
    p_disc2 = PeerPromptEnvelope(
        request_id="req-topic-next-step",
        from_agent="antigravity",
        to_agent="grok",
        request_type="discuss",
        subject="Turn 2",
        timestamp="2026-11-08T18:25:00+07:00",
        output_path="grok_discuss_02.md",
    )
    p_disc2_path = tmp_path / "prompt_discuss_02.md"
    p_disc2_path.write_text(render_prompt_header(p_disc2) + "Turn 2 question", encoding="utf-8")
    opts_t3 = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_plan"], p_disc2, None, None, False, None, None, p_disc2_path
    )
    assert opts_t3["resume_session_id"] == "sess-discuss-01"

    # Snapshot deduplication in update_status_json: identical (session_id, turn_count, total_tokens, cost) not double-counted
    v1_Turn2 = PeerVerdictBlock(
        request_id="req-20261108-ai-eos-ch08-v2",
        verdict="APPROVE",
        summary="v2",
        telemetry=PeerVerdictTelemetry(
            session_id="sess-ch08-v1",
            primary_model="gemini-3.8-flash-high",
            input_tokens=300,
            output_tokens=100,
            total_tokens=400,
            turn_count=2,
            cost_usd=0.005,
        ),
    )
    status_f = tmp_path / "status.json"
    reg_dedup = {
        "r1.md": {"path": tmp_path / "r1.md", "role": "GROK_RESPONSE", "verdict": v1},
        "r1_dup.md": {"path": tmp_path / "r1_dup.md", "role": "GROK_RESPONSE", "verdict": v1},
        "r2.md": {"path": tmp_path / "r2.md", "role": "GROK_RESPONSE", "verdict": v1_Turn2},
    }
    update_status_json(status_f, reg_dedup, pending_anti=[], pending_grok=[])
    st = json.loads(status_f.read_text(encoding="utf-8"))["exchange_stats"]
    assert st["total_tokens"] == 1600
    assert st["total_cost_usd"] == 0.025


def test_auto_discover_blocks_cross_phase_plan_to_code_across_tiers(tmp_path):
    """Verifies G1 Cross-Phase Guard blocks Plan->Code leaks across Tier 1/2 while keeping same-phase resumes."""
    from ccba_harness.peer import (
        PROFILE_SPECS,
        PeerPromptEnvelope,
        _resolve_grok_profile_options,
        parse_envelope_from_md,
        render_prompt_header,
        render_verdict_header,
    )

    shared_files = ["packages/ccba-harness/src/ccba_harness/peer.py"]
    # 1. Seed Plan Pass 1 (normalized alias path: missing from_agent -> plan aliases to discuss + audit_plan)
    raw_norm_plan = (
        "---\nrequest_id: req-20261112-plan-compiler-001\ntask_type: plan\n"
        "profile: discuss\nsubject: Plan v1\ntimestamp: '2026-11-12T10:00:00+07:00'\n"
        f"target_files: {shared_files}\noutput_path: grok_compiler_plan_audit.md\n---\nPlan body\n"
    )
    (tmp_path / "prompt_grok_compiler_plan_audit.md").write_text(raw_norm_plan, encoding="utf-8")
    norm_env = parse_envelope_from_md(raw_norm_plan)
    assert norm_env is not None and norm_env.request_type == "discuss"
    v_plan1 = PeerVerdictBlock(
        request_id="req-20261112-plan-compiler-001",
        verdict="REVISE_PLAN",
        summary="Revise plan",
        telemetry=PeerVerdictTelemetry(session_id="sess-plan-p1", primary_model="grok-4.7"),
    )
    (tmp_path / "grok_compiler_plan_audit.md").write_text(
        render_verdict_header(v_plan1) + "\n# Plan P1", encoding="utf-8"
    )

    # Same-phase Plan Pass 2 (signoff_diff) MUST still auto-resume sess-plan-p1
    p_plan_s2 = PeerPromptEnvelope(
        request_id="req-20261112-plan-compiler-002-signoff",
        from_agent="antigravity",
        to_agent="grok",
        request_type="verify",
        profile="signoff_diff",
        subject="Plan signoff",
        timestamp="2026-11-12T10:15:00+07:00",
        target_files=shared_files,
        output_path="grok_compiler_plan_audit_reverify.md",
    )
    p_s2_path = tmp_path / "prompt_grok_compiler_plan_audit_reverify.md"
    p_s2_path.write_text(render_prompt_header(p_plan_s2) + "Delta", encoding="utf-8")
    opts_plan_s2 = _resolve_grok_profile_options(
        PROFILE_SPECS["signoff_diff"],
        p_plan_s2,
        None,
        None,
        False,
        None,
        None,
        p_s2_path,
        effective_profile="signoff_diff",
    )
    assert opts_plan_s2["resume_session_id"] == "sess-plan-p1"

    # Seed Plan Pass 2 verdict with FINAL_ACCEPT (e.g. grok_*_plan_audit_reverify.md)
    v_plan_fin = PeerVerdictBlock(
        request_id="req-20261112-reverify-compiler-003",
        verdict="FINAL_ACCEPT",
        summary="Plan accepted",
        telemetry=PeerVerdictTelemetry(session_id="sess-plan-fin", primary_model="grok-4.7"),
    )
    (tmp_path / "grok_compiler_plan_audit_reverify.md").write_text(
        render_verdict_header(v_plan_fin) + "\n# Plan Final", encoding="utf-8"
    )

    # 2. Cross-phase Post-Impl Code Review copying template (`from_agent` present -> `request_type: plan` preserved!)
    # with `profile: arch_audit` MUST NOT inherit sess-plan-p1 or sess-plan-fin via Tier 2 Jaccard
    p_impl = PeerPromptEnvelope(
        request_id="req-20261112-impl-compiler-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="plan",
        profile="arch_audit",
        subject="Post-impl code audit",
        timestamp="2026-11-12T11:00:00+07:00",
        target_files=shared_files,
        output_path="grok_compiler_impl_audit.md",
    )
    p_impl_path = tmp_path / "prompt_grok_compiler_impl_audit.md"
    p_impl_path.write_text(render_prompt_header(p_impl) + "Impl body", encoding="utf-8")
    opts_impl = _resolve_grok_profile_options(
        PROFILE_SPECS["arch_audit"],
        p_impl,
        None,
        None,
        False,
        None,
        None,
        p_impl_path,
        effective_profile="arch_audit",
    )
    assert opts_impl["resume_session_id"] is None

    # 3. Tier-1 stem collision (`_STAGE_PREFIX_RE` strips `plan_` and `arch_audit_`) with `-reverify` suffix
    # on a code-phase profile MUST ALSO block inheriting prior Plan sessions
    p_impl_tier1 = PeerPromptEnvelope(
        request_id="req-20261112-arch-audit-compiler-reverify",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        profile="code_review",
        subject="Code review v2 without prior code session",
        timestamp="2026-11-12T11:05:00+07:00",
        target_files=shared_files,
        output_path="grok_arch_audit_compiler_reverify.md",
    )
    p_t1_path = tmp_path / "prompt_grok_arch_audit_compiler_reverify.md"
    p_t1_path.write_text(render_prompt_header(p_impl_tier1) + "Code v2", encoding="utf-8")
    opts_t1_blk = _resolve_grok_profile_options(
        PROFILE_SPECS["code_review"],
        p_impl_tier1,
        None,
        None,
        False,
        None,
        None,
        p_t1_path,
        effective_profile="code_review",
    )
    assert opts_t1_blk["resume_session_id"] is None

    # 4. AEC domain noun `floor_plan` in a prior code review MUST NOT be misclassified as a Plan session
    p_aec1 = PeerPromptEnvelope(
        request_id="req-20261112-qc-floor-plan-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        profile="arch_audit",
        subject="Floor plan QC code review",
        timestamp="2026-11-12T11:10:00+07:00",
        target_files=["packages/ccba-qc/floor_plan_parser.py"],
        output_path="grok_qc_floor_plan_review.md",
    )
    (tmp_path / "prompt_grok_qc_floor_plan_review.md").write_text(
        render_prompt_header(p_aec1) + "QC", encoding="utf-8"
    )
    v_aec1 = PeerVerdictBlock(
        request_id="req-20261112-qc-floor-plan-001",
        verdict="APPROVE_WITH_CONDITIONS",
        summary="Fix parser",
        telemetry=PeerVerdictTelemetry(session_id="sess-floor-code-1", primary_model="grok-4.7"),
    )
    (tmp_path / "grok_qc_floor_plan_review.md").write_text(
        render_verdict_header(v_aec1) + "\n# Code V1", encoding="utf-8"
    )
    p_aec2 = PeerPromptEnvelope(
        request_id="req-20261112-qc-floor-plan-002-reverify",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        profile="code_review",
        subject="Floor plan QC code review v2",
        timestamp="2026-11-12T11:20:00+07:00",
        target_files=["packages/ccba-qc/floor_plan_parser.py"],
        output_path="grok_qc_floor_plan_review_v2.md",
    )
    p_aec2_path = tmp_path / "prompt_grok_qc_floor_plan_review_v2.md"
    p_aec2_path.write_text(render_prompt_header(p_aec2) + "Delta", encoding="utf-8")
    opts_aec2 = _resolve_grok_profile_options(
        PROFILE_SPECS["code_review"],
        p_aec2,
        None,
        None,
        False,
        None,
        None,
        p_aec2_path,
        effective_profile="code_review",
    )
    assert opts_aec2["resume_session_id"] == "sess-floor-code-1"

    # 5. Same-phase Code Pass 2 (`arch_audit` -> `signoff_diff`) auto-resumes prior code session,
    # even if prior `arch_audit` prompt kept copied `request_type: plan` (`p_impl` above)
    v_impl1 = PeerVerdictBlock(
        request_id="req-20261112-impl-compiler-001",
        verdict="APPROVE_WITH_CONDITIONS",
        summary="Fix one edge case",
        telemetry=PeerVerdictTelemetry(session_id="sess-code-p1", primary_model="grok-4.7"),
    )
    (tmp_path / "grok_compiler_impl_audit.md").write_text(
        render_verdict_header(v_impl1) + "\n# Code P1", encoding="utf-8"
    )
    p_code_s2 = PeerPromptEnvelope(
        request_id="req-20261112-impl-compiler-002-signoff",
        from_agent="antigravity",
        to_agent="grok",
        request_type="verify",
        profile="signoff_diff",
        subject="Code signoff",
        timestamp="2026-11-12T11:25:00+07:00",
        target_files=shared_files,
        output_path="grok_compiler_impl_signoff.md",
    )
    p_cs2_path = tmp_path / "prompt_grok_compiler_impl_signoff.md"
    p_cs2_path.write_text(render_prompt_header(p_code_s2) + "Delta", encoding="utf-8")
    opts_code_s2 = _resolve_grok_profile_options(
        PROFILE_SPECS["signoff_diff"],
        p_code_s2,
        None,
        None,
        False,
        None,
        None,
        p_cs2_path,
        effective_profile="signoff_diff",
    )
    assert opts_code_s2["resume_session_id"] == "sess-code-p1"
    opts_code_rev2 = _resolve_grok_profile_options(
        PROFILE_SPECS["code_review"],
        p_code_s2,
        None,
        None,
        False,
        None,
        None,
        p_cs2_path,
        effective_profile="code_review",
    )
    assert opts_code_rev2["resume_session_id"] == "sess-code-p1"


def test_response_grok_prefix_ttl_bound_and_overwritten_telemetry_merge(tmp_path):
    """Verifies response_grok_*.md recognition, 12h auto-resume TTL cap, and overwritten telemetry merge."""
    from ccba_harness._peer_telemetry import merge_overwritten_telemetry
    from ccba_harness.peer import (
        PROFILE_SPECS,
        PeerPromptEnvelope,
        _resolve_grok_profile_options,
        classify_file_role,
        compute_pending_queues,
        render_prompt_header,
        render_verdict_header,
        scan_peer_exchange,
    )

    assert classify_file_role(tmp_path / "response_grok_wave1_signoff.md") == "GROK_RESPONSE"
    assert classify_file_role(tmp_path / "response_wave2.md") == "GROK_RESPONSE"

    # 1. Stale session (5 days old) must NOT be auto-resumed by Tier 1 or Tier 2
    p_old = PeerPromptEnvelope(
        request_id="req-hermes-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Old thread",
        timestamp="2026-11-05T08:00:00Z",
        source_documents=["scripts/hermes_executive_mcp.py"],
        output_path="response_grok_hermes_001.md",
    )
    (tmp_path / "prompt_grok_hermes_001.md").write_text(
        render_prompt_header(p_old) + "Old", encoding="utf-8"
    )
    v_old = PeerVerdictBlock(
        request_id="req-hermes-001",
        verdict="APPROVE_WITH_CONDITIONS",
        timestamp="2026-11-05T08:10:00Z",
        summary="Old v1",
        telemetry=PeerVerdictTelemetry(
            session_id="sess-stale-5d",
            primary_model="grok-4.7",
            input_tokens=500,
            output_tokens=100,
            total_tokens=600,
            turn_count=1,
            cost_usd=0.01,
        ),
    )
    out_f = tmp_path / "response_grok_hermes_001.md"
    out_f.write_text(render_verdict_header(v_old) + "\n# Old", encoding="utf-8")

    p_new = PeerPromptEnvelope(
        request_id="req-hermes-001-v2",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="New thread 5d later",
        timestamp="2026-11-10T10:00:00Z",
        source_documents=["scripts/hermes_executive_mcp.py"],
        output_path="response_grok_hermes_002.md",
    )
    p_new_path = tmp_path / "prompt_grok_hermes_001_v2.md"
    p_new_path.write_text(render_prompt_header(p_new) + "New", encoding="utf-8")
    opts_stale = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_plan"], p_new, None, None, False, None, None, p_new_path
    )
    assert opts_stale["resume_session_id"] is None

    # 2. Fresh response_grok_*.md (within 12h) is discovered by both scan_peer_exchange and auto-resume
    v_old.timestamp = "2026-11-10T09:00:00Z"
    v_old.telemetry.session_id = "sess-fresh-1h"
    out_f.write_text(render_verdict_header(v_old) + "\n# Fresh", encoding="utf-8")
    opts_fresh = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_plan"], p_new, None, None, False, None, None, p_new_path
    )
    assert opts_fresh["resume_session_id"] == "sess-fresh-1h"

    _, _, reg = scan_peer_exchange(tmp_path, {})
    assert reg["response_grok_hermes_001.md"]["role"] == "GROK_RESPONSE"
    _, pending_grok = compute_pending_queues(reg)
    assert "prompt_grok_hermes_001.md" not in pending_grok

    # 3. Overwriting out_f with a Round 2 session accumulates prior telemetry
    t_r2 = PeerVerdictTelemetry(
        session_id="sess-round2",
        primary_model="grok-4.7",
        input_tokens=300,
        output_tokens=50,
        total_tokens=350,
        model_calls=2,
        turn_count=1,
        cost_usd=0.02,
        cost_mode="exact",
        duration_seconds=5.0,
    )
    merged = merge_overwritten_telemetry(out_f, t_r2)
    assert merged is not None
    assert merged.session_id == "sess-round2"
    assert merged.total_tokens == 950
    assert merged.cost_usd == 0.03
    assert merged.turn_count == 2


def test_resumed_audit_direct_cache_prefix_preamble_and_cost_isolation(tmp_path, monkeypatch):
    """Verifies resumed audit_direct KV-cache prefix preservation, multi-turn preamble detection, and costUsdTicks isolation."""
    from ccba_harness._peer_watchdog import (
        AUDIT_BASE_SYSTEM_PROMPT,
        _build_synthesis_opts,
        is_max_turns_exhausted,
    )
    from ccba_harness.peer import PROFILE_SPECS, PeerPromptEnvelope, _resolve_grok_profile_options

    # 1. Resumed audit_direct preserves AUDIT_BASE_SYSTEM_PROMPT and read-only tools (KV-cache prefix)
    env = PeerPromptEnvelope(
        request_id="req-nb-v2",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="v2",
        timestamp="2026-11-10T16:10:00+07:00",
        output_path="grok_nb_v2.md",
        profile="audit_direct",
        resume_session_id="d00ec01c-05d9-427b-a6db-1703ee48ddfa",
    )
    opts_resumed = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_direct"], env, None, None, False, None, None, None
    )
    assert opts_resumed["system_prompt"] == AUDIT_BASE_SYSTEM_PROMPT
    assert opts_resumed["tools"] == ["read_file", "grep", "list_dir"]
    assert opts_resumed["deny"] == ["Bash", "Write", "Edit", "WebFetch"]
    assert opts_resumed["max_turns"] == 3
    synth_opts = _build_synthesis_opts(opts_resumed, "d00ec01c-05d9-427b-a6db-1703ee48ddfa")
    assert synth_opts["timeout"] >= 180.0

    # 2. Multi-turn resumed session (turn_ends == 3) stopping on preamble triggers synthesis
    sid = "d00ec01c-05d9-427b-a6db-1703ee48ddfa"
    sdir = tmp_path / "sessions" / sid
    sdir.mkdir(parents=True)
    (sdir / "events.jsonl").write_text(
        '{"type":"turn_ended","outcome":"cancelled","cancellation_context":{"reason":"max_turns_reached"}}\n'
        '{"type":"turn_ended","outcome":"completed"}\n'
        '{"type":"turn_ended","outcome":"completed"}\n',
        encoding="utf-8",
    )
    chat_f = sdir / "chat_history.jsonl"
    chat_f.write_text(
        '{"type":"assistant","content":"---\\nrequest_id: r1\\nverdict: REVISE_PLAN\\n---"}\n'
        '{"type":"user","content":"Round 2 delta"}\n'
        '{"type":"assistant","content":"The round-2 plan claims all 13 conditions are adopted. I will check deltas."}\n',
        encoding="utf-8",
    )
    assert is_max_turns_exhausted(sid, session_root=tmp_path / "sessions") is True
    with chat_f.open("a", encoding="utf-8") as cf:
        cf.write(
            '{"type":"assistant","content":"---\\nrequest_id: r2\\nverdict: APPROVE_PLAN\\n---"}\n'
        )
    assert is_max_turns_exhausted(sid, session_root=tmp_path / "sessions") is False

    # 3. Turn 4 without costUsdTicks does not inherit cumulative session costUsdTicks
    usage_d00 = {
        "session": {"primaryModelId": "grok-4.7-build", "costUsdTicks": 2627812400, "turnCount": 4},
        "turns": [
            {
                "turnNumber": 1,
                "inputTokens": 532633,
                "outputTokens": 9705,
                "costUsdTicks": 1608200000,
            },
            {
                "turnNumber": 3,
                "primaryModelId": "gemini-3.8-flash-high",
                "inputTokens": 40000,
                "outputTokens": 500,
                "reasoningTokens": 600,
                "totalTokens": 40500,
                "modelCalls": 1,
            },
            {
                "turnNumber": 4,
                "primaryModelId": "gemini-3.8-flash-high",
                "inputTokens": 84315,
                "outputTokens": 2088,
                "reasoningTokens": 1938,
                "totalTokens": 86403,
                "modelCalls": 1,
            },
        ],
    }
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(
            args=a[0], returncode=0, stdout=json.dumps(usage_d00), stderr=""
        ),
    )
    tel = extract_grok_session_telemetry(
        session_id=sid, fallback_model="gemini-3.8-flash-high", synthesize_turns=1
    )
    assert tel is not None
    assert tel.cost_mode == "estimated"
    assert tel.cost_usd < 0.20
    tel2 = extract_grok_session_telemetry(
        session_id=sid, fallback_model="gemini-3.8-flash-high", synthesize_turns=2
    )
    assert tel2 is not None
    assert tel2.cost_mode == "estimated"
    assert tel2.cost_usd < 0.25
