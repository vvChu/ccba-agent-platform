"""_peer_telemetry.py - Telemetry extraction helper for Grok sessions (ADR-0064)."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any


def extract_grok_session_telemetry(
    session_id: str,
    timeout: float = 3.0,
    fallback_prompt_text: str | None = None,
    fallback_resp_text: str | None = None,
    duration_seconds: float = 0.0,
    fallback_model: str = "unknown",
) -> Any | None:
    """Safely extracts telemetry metrics from grok usage CLI with bounded retry & graceful degradation (ADR-0064).

    Args:
        session_id: UUID string of the session.
        timeout: Subprocess timeout in seconds (default: 3.0s).
        fallback_prompt_text: Prompt text for heuristic fallback estimation.
        fallback_resp_text: Response text for heuristic fallback estimation.
        duration_seconds: Execution wall-clock duration in seconds.
        fallback_model: Target model name if usage command fails.

    Returns:
        PeerVerdictTelemetry instance, or None if extraction and fallback both fail.
    """
    from .peer import CostMode, PeerVerdictTelemetry

    cmd = ["grok", "usage", session_id]
    deadline = time.time() + timeout

    # Bounded retry loop (up to 2 retries, 100ms interval) within overall timeout budget
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
                data = json.loads(proc.stdout)
                session_data = data.get("session", {})
                primary_model = session_data.get("primaryModelId") or fallback_model
                inp = int(session_data.get("inputTokens", 0))
                outp = int(session_data.get("outputTokens", 0))
                rsn = int(session_data.get("reasoningTokens", 0))
                cached = int(session_data.get("cachedReadTokens", 0))
                total = int(session_data.get("totalTokens", inp + outp))
                calls = int(session_data.get("modelCalls", 1))
                turns = int(session_data.get("turnCount", 1))

                # COND-2: Cost provenance distinction
                cost_mode: CostMode = "estimated"
                cost_usd = 0.0
                if "costUsdTicks" in session_data:
                    cost_usd = round(float(session_data["costUsdTicks"]) / 10000.0, 4)
                    cost_mode = "exact"
                else:
                    # Estimate based on rate card in ccba_harness.telemetry
                    from .telemetry import PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT

                    cost_usd = round(
                        (inp / 1_000_000 * PRICE_PER_M_INPUT)
                        + (outp / 1_000_000 * PRICE_PER_M_OUTPUT),
                        4,
                    )
                    cost_mode = "estimated"

                return PeerVerdictTelemetry(
                    session_id=session_id,
                    primary_model=primary_model,
                    input_tokens=inp,
                    output_tokens=outp,
                    reasoning_tokens=rsn,
                    cached_read_tokens=cached,
                    total_tokens=total,
                    model_calls=calls,
                    turn_count=turns,
                    cost_usd=cost_usd,
                    cost_mode=cost_mode,
                    duration_seconds=round(duration_seconds, 2),
                )
        except Exception:
            pass

        if attempt < 2 and time.time() < deadline:
            time.sleep(0.1)

    # COND-1: Graceful degradation fallback using TokenEstimator
    try:
        from .telemetry import PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT, TokenEstimator

        est_inp = TokenEstimator.estimate_text(fallback_prompt_text or "")
        est_out = TokenEstimator.estimate_text(fallback_resp_text or "")
        est_cost = round(
            (est_inp / 1_000_000 * PRICE_PER_M_INPUT) + (est_out / 1_000_000 * PRICE_PER_M_OUTPUT),
            4,
        )
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
        )
    except Exception:
        return None
