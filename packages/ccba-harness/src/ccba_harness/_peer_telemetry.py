"""_peer_telemetry.py - Telemetry extraction and aggregation helpers for Grok sessions (ADR-0064 / ADR-0065)."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any


def _is_degraded_reasoning(expected_effort: str | None, reasoning_tokens: int) -> bool:
    """Checks whether a high/xhigh reasoning profile silently returned 0 reasoning tokens."""
    return bool(expected_effort in ("high", "xhigh") and reasoning_tokens <= 0)


def _compute_session_cost(
    s_data: dict[str, Any], primary_model: str, inp: int, outp: int
) -> tuple[float, Any]:
    """Computes normalized USD cost and cost mode from session usage dictionary."""
    from .telemetry import resolve_model_token_rates

    rate_in, rate_out = resolve_model_token_rates(primary_model)
    if "costUsdTicks" in s_data:
        cost = (
            0.0
            if (rate_in == 0.0 and rate_out == 0.0)
            else round(float(s_data["costUsdTicks"]) / 1e10, 4)
        )
        return cost, "exact"
    return round((inp / 1e6 * rate_in) + (outp / 1e6 * rate_out), 4), "estimated"


def _build_telemetry_from_usage_json(
    session_id: str,
    data: dict[str, Any],
    duration_seconds: float,
    fallback_model: str,
    expected_reasoning_effort: str | None = None,
) -> Any:
    """Constructs PeerVerdictTelemetry from parsed `grok usage <session_id>` JSON output."""
    from .peer import PeerVerdictTelemetry

    s_data = dict(data.get("session") or {})
    turns_list = data.get("turns")
    if isinstance(turns_list, list) and len(turns_list) > 1 and isinstance(turns_list[-1], dict):
        s_data = {**s_data, **turns_list[-1]}

    primary_model = str(s_data.get("primaryModelId") or fallback_model)
    inp, outp = int(s_data.get("inputTokens", 0)), int(s_data.get("outputTokens", 0))
    rsn, cached = int(s_data.get("reasoningTokens", 0)), int(s_data.get("cachedReadTokens", 0))
    total = int(s_data.get("totalTokens", inp + outp))
    calls = int(s_data.get("modelCalls", 1))
    turn_count = int(
        s_data.get("turnCount", len(turns_list) if isinstance(turns_list, list) else 1)
    )
    cost_usd, mode_typed = _compute_session_cost(s_data, primary_model, inp, outp)

    return PeerVerdictTelemetry(
        session_id=session_id,
        primary_model=primary_model,
        input_tokens=inp,
        output_tokens=outp,
        reasoning_tokens=rsn,
        cached_read_tokens=cached,
        total_tokens=total,
        model_calls=calls,
        turn_count=turn_count,
        cost_usd=cost_usd,
        cost_mode=mode_typed,
        duration_seconds=round(duration_seconds, 2),
        degraded_reasoning=_is_degraded_reasoning(expected_reasoning_effort, rsn),
    )


def _build_fallback_telemetry(
    session_id: str,
    fallback_prompt_text: str | None,
    fallback_resp_text: str | None,
    duration_seconds: float,
    fallback_model: str,
    expected_reasoning_effort: str | None = None,
) -> Any | None:
    """Constructs heuristic fallback PeerVerdictTelemetry when `grok usage` fails."""
    try:
        from .peer import PeerVerdictTelemetry
        from .telemetry import TokenEstimator, resolve_model_token_rates

        est_inp = TokenEstimator.estimate_text(fallback_prompt_text or "")
        est_out = TokenEstimator.estimate_text(fallback_resp_text or "")
        rate_in, rate_out = resolve_model_token_rates(fallback_model)
        est_cost = round((est_inp / 1_000_000 * rate_in) + (est_out / 1_000_000 * rate_out), 4)
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
            degraded_reasoning=_is_degraded_reasoning(expected_reasoning_effort, 0),
        )
    except Exception:
        return None


def extract_grok_session_telemetry(
    session_id: str,
    timeout: float = 3.0,
    fallback_prompt_text: str | None = None,
    fallback_resp_text: str | None = None,
    duration_seconds: float = 0.0,
    fallback_model: str = "unknown",
    expected_reasoning_effort: str | None = None,
) -> Any | None:
    """Safely extracts telemetry metrics from grok usage CLI with bounded retry & fallback (ADR-0064)."""
    cmd = ["grok", "usage", session_id]
    deadline = time.time() + timeout
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
                return _build_telemetry_from_usage_json(
                    session_id,
                    json.loads(proc.stdout),
                    duration_seconds,
                    fallback_model,
                    expected_reasoning_effort,
                )
        except Exception:
            pass
        if attempt < 2 and time.time() < deadline:
            time.sleep(0.1)

    return _build_fallback_telemetry(
        session_id,
        fallback_prompt_text,
        fallback_resp_text,
        duration_seconds,
        fallback_model,
        expected_reasoning_effort,
    )


def _accumulate_verdict_telemetry(
    t: Any,
    by_model: dict[str, dict[str, Any]],
) -> tuple[int, float]:
    """Accumulates either PeerVerdictTelemetry or CombinedTelemetry into status.json by_model map."""
    if hasattr(t, "profile_breakdown") and isinstance(getattr(t, "profile_breakdown", None), dict):
        for item in t.profile_breakdown.values():
            m = getattr(item, "model", None) or "unknown"
            entry = by_model.setdefault(m, {"calls": 0, "tokens": 0, "cost_usd": 0.0})
            entry["calls"] += 1
            entry["tokens"] += int(getattr(item, "total_tokens", 0))
            entry["cost_usd"] = round(entry["cost_usd"] + float(getattr(item, "cost_usd", 0.0)), 4)
        return int(getattr(t, "total_tokens", 0)), float(getattr(t, "cost_usd", 0.0))

    if hasattr(t, "primary_model"):
        m = str(getattr(t, "primary_model", "unknown"))
        entry = by_model.setdefault(m, {"calls": 0, "tokens": 0, "cost_usd": 0.0})
        entry["calls"] += 1
        entry["tokens"] += int(getattr(t, "total_tokens", 0))
        entry["cost_usd"] = round(entry["cost_usd"] + float(getattr(t, "cost_usd", 0.0)), 4)
        return int(getattr(t, "total_tokens", 0)), float(getattr(t, "cost_usd", 0.0))

    return 0, 0.0
