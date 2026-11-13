"""_peer_telemetry.py - Telemetry extraction and aggregation helpers for Grok sessions (ADR-0064 / ADR-0065)."""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ._peer_models import (
    PeerCondition,
    PeerVerdictBlock,
    PeerVerdictTelemetry,
    _sort_key_latest_exchange,
    extract_env_conversation_id,
    parse_envelope_from_md,
    parse_verdict_from_md,
    resolve_spoke_slug_from_path,
)
from ._peer_watchdog import CostMode

_STAGE_PREFIX_RE = re.compile(
    r"^(?:final[-_])?(?:signoff|acceptance|review[-_]plan|review[-_]walkthrough|review|discuss|plan|arch[-_]audit|arch|audit)[-_]+",
    re.IGNORECASE,
)
_ROUND_SUFFIX_RE = re.compile(
    r"(?:[-_](?:v\d+|r\d+|round\d*|pass\d+|turn\d+|supplemental|followup|follow[-_]up|recheck|reverify|re[-_]verify|signoff|final[-_]?signoff|final[-_]?acceptance|retry|stage\d+|audit|plan|\d{3}))+$",
    re.IGNORECASE,
)
_FOLLOWUP_HINT_RE = re.compile(
    r"(?:^|[-_])(?:v[2-9]\d*|r[2-9]\d*|round[2-9]\d*|pass[2-9]\d*|turn[2-9]\d*|supplemental|followup|follow[-_]up|recheck|reverify|re[-_]verify|signoff|final[-_]?signoff|final[-_]?acceptance|retry|stage[23]|00[2-9])(?:[-_]|$)",
    re.IGNORECASE,
)
_PREFIX_ROLE_RE = re.compile(
    r"^(?:prompt_grok_review_|prompt_grok_|prompt_|grok_response_|grok_review_|grok_implementation_|grok_implement_|grok_|response_|verdict_|req[-_])+",
    re.IGNORECASE,
)
_OPT_OUT_RESUME_TOKENS: frozenset[str] = frozenset({"new", "none", "false", "0"})
_RESUMED_BLOAT_MAX_LINES = 400
_RESUMED_BLOAT_MAX_BYTES = 20_480
_MAX_RESUME_AGE_SECONDS = 43_200.0
_VERDICT_FILE_PREFIXES: tuple[str, ...] = ("grok_", "verdict_", "response_grok_", "response_")

_PASS_VERDICTS: frozenset[str] = frozenset(
    {"APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS", "APPROVE_WITH_RESERVATIONS"}
)
_CODE_AUDIT_PROFILES: frozenset[str] = frozenset(
    {"arch_audit", "code_review", "audit_direct", "agentic_code", "patch_fast"}
)
_PLAN_AUDIT_PROFILES: frozenset[str] = frozenset({"audit_plan", "deep_spec_audit"})
_PLAN_PHASE_RE = re.compile(r"(?:^|[-_.])plan(?:[-_.]|$)", re.IGNORECASE)
_NON_PHASE_PLAN_RE = re.compile(r"(?:floor|site|master|key|roof)[-_]plan", re.IGNORECASE)


def _is_degraded_reasoning(expected_effort: str | None, reasoning_tokens: int) -> bool:
    """Checks whether a high/xhigh reasoning profile silently returned 0 reasoning tokens."""
    return bool(expected_effort in ("high", "xhigh") and reasoning_tokens <= 0)


def _enforce_single_verdict_guardrails(verdict: PeerVerdictBlock) -> bool:
    """Applies degraded reasoning condition and downgrades pass verdicts if blocking conditions exist."""
    modified = False
    telemetry = verdict.telemetry
    has_degraded = bool(telemetry and getattr(telemetry, "degraded_reasoning", False))
    existing_cond_ids = {c.id for c in verdict.conditions}

    if has_degraded and "COND-DEGRADED-REASONING" not in existing_cond_ids:
        verdict.conditions.append(
            PeerCondition(
                id="COND-DEGRADED-REASONING",
                description="High/xhigh reasoning profile returned 0 reasoning_tokens (silent reasoning degradation).",
                blocking=True,
                source_profile="telemetry",
                source_profiles=["telemetry"],
            )
        )
        modified = True

    has_blocking = any(c.blocking for c in verdict.conditions)
    has_high_risk = (verdict.risk_score or 1) >= 4
    if verdict.verdict in _PASS_VERDICTS and (has_blocking or has_high_risk):
        verdict.verdict = "APPROVE_WITH_CONDITIONS"
        modified = True

    return modified


def _compute_session_cost(
    s_data: dict[str, Any], primary_model: str, inp: int, outp: int
) -> tuple[float, CostMode]:
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


_SUMMABLE_TURN_KEYS: tuple[str, ...] = (
    "inputTokens",
    "outputTokens",
    "reasoningTokens",
    "cachedReadTokens",
    "totalTokens",
    "costUsdTicks",
    "modelCalls",
)


def _merge_synthesis_turns(
    s_data: dict[str, Any],
    turns_list: Any,
    synthesize_turns: int,
    parent_data: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int, int]:
    """Resolves turn counters, session turn_count, and last-turn reasoning tokens."""
    t_list = [t for t in turns_list if isinstance(t, dict)] if isinstance(turns_list, list) else []
    turn_count = int(s_data.get("turnCount") or (len(t_list) if t_list else 1))
    base_s_data = {k: v for k, v in s_data.items() if k != "costUsdTicks"} if t_list else s_data
    if synthesize_turns <= 1:
        if t_list:
            s_data = base_s_data | t_list[-1]
            if "primaryModelId" in t_list[-1]:
                s_data["primaryModelId"] = t_list[-1]["primaryModelId"]
        return s_data, turn_count, int(s_data.get("reasoningTokens", 0))

    last_turn = t_list[-1] if t_list else s_data
    last_rsn = int(last_turn.get("reasoningTokens", s_data.get("reasoningTokens", 0)))
    window = (
        list(t_list[-synthesize_turns:]) if len(t_list) >= 2 else (list(t_list) or [dict(s_data)])
    )
    if len(window) == 1 and isinstance(parent_data, dict):
        p_sess = dict(parent_data.get("session") or {})
        p_turns = parent_data.get("turns")
        p_last = (
            p_turns[-1]
            if isinstance(p_turns, list) and p_turns and isinstance(p_turns[-1], dict)
            else p_sess
        )
        if p_last:
            window.insert(0, p_last)
            p_tc = int(p_sess.get("turnCount") or 1)
            turn_count = max(turn_count + 1, p_tc + 1)
    merged = {**base_s_data, **(t_list[-1] if t_list else {})}
    for key in _SUMMABLE_TURN_KEYS:
        if any(key in t for t in window):
            merged[key] = sum(int(t.get(key, 0) or 0) for t in window)
    return merged, turn_count, last_rsn


def _build_telemetry_from_usage_json(
    session_id: str,
    data: dict[str, Any],
    duration_seconds: float,
    fallback_model: str,
    expected_reasoning_effort: str | None = None,
    synthesize_turns: int = 1,
    parent_data: dict[str, Any] | None = None,
) -> PeerVerdictTelemetry:
    """Constructs PeerVerdictTelemetry from parsed `grok usage <session_id>` JSON output."""
    s_data, turn_count, last_rsn = _merge_synthesis_turns(
        dict(data.get("session") or {}),
        data.get("turns"),
        synthesize_turns,
        parent_data=parent_data,
    )
    primary_model = str(s_data.get("primaryModelId") or fallback_model)
    inp, outp = int(s_data.get("inputTokens", 0)), int(s_data.get("outputTokens", 0))
    rsn, cached = int(s_data.get("reasoningTokens", 0)), int(s_data.get("cachedReadTokens", 0))
    total = int(s_data.get("totalTokens", inp + outp))
    calls = int(s_data.get("modelCalls", 1))
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
        degraded_reasoning=_is_degraded_reasoning(expected_reasoning_effort, last_rsn),
    )


def _build_fallback_telemetry(
    session_id: str,
    fallback_prompt_text: str | None,
    fallback_resp_text: str | None,
    duration_seconds: float,
    fallback_model: str,
    expected_reasoning_effort: str | None = None,
) -> PeerVerdictTelemetry | None:
    """Constructs heuristic fallback PeerVerdictTelemetry when `grok usage` fails."""
    try:
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
            degraded_reasoning=False,
        )
    except Exception:
        return None


def _fetch_usage_json(session_id: str, timeout: float) -> dict[str, Any] | None:
    """Queries `grok usage <session_id>` with up to 3 bounded attempts."""
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
                parsed = json.loads(proc.stdout)
                if isinstance(parsed, dict):
                    return parsed
        except Exception:
            pass
        if attempt < 2 and time.time() < deadline:
            time.sleep(0.1)
    return None


def extract_grok_session_telemetry(
    session_id: str,
    timeout: float = 3.0,
    fallback_prompt_text: str | None = None,
    fallback_resp_text: str | None = None,
    duration_seconds: float = 0.0,
    fallback_model: str = "unknown",
    expected_reasoning_effort: str | None = None,
    synthesize_turns: int = 1,
    parent_session_id: str | None = None,
) -> PeerVerdictTelemetry | None:
    """Safely extracts telemetry metrics from grok usage CLI with bounded retry & fallback (ADR-0064)."""
    data = _fetch_usage_json(session_id, timeout)
    if data is not None:
        parent_data: dict[str, Any] | None = None
        turns = data.get("turns")
        if (
            synthesize_turns >= 2
            and parent_session_id
            and parent_session_id != session_id
            and (not isinstance(turns, list) or len(turns) <= 1)
        ):
            parent_data = _fetch_usage_json(parent_session_id, max(0.5, timeout / 2))
        return _build_telemetry_from_usage_json(
            session_id,
            data,
            duration_seconds,
            fallback_model,
            expected_reasoning_effort,
            synthesize_turns=synthesize_turns,
            parent_data=parent_data,
        )

    return _build_fallback_telemetry(
        session_id,
        fallback_prompt_text,
        fallback_resp_text,
        duration_seconds,
        fallback_model,
        expected_reasoning_effort,
    )


def merge_overwritten_telemetry(
    output_file: Path | None, current: PeerVerdictTelemetry | None
) -> PeerVerdictTelemetry | None:
    """Accumulates prior round telemetry when overwriting an existing verdict file on disk."""
    if current is None or output_file is None or not output_file.is_file():
        return current
    try:
        prior_verdict = parse_verdict_from_md(output_file.read_text(encoding="utf-8"))
    except OSError:
        return current
    prior = getattr(prior_verdict, "telemetry", None) if prior_verdict else None
    if not isinstance(prior, PeerVerdictTelemetry):
        return current
    if not prior.session_id or prior.session_id.lower() in ("none", "unknown"):
        return current
    if prior.session_id == current.session_id and prior.turn_count >= current.turn_count:
        return current
    new_turns = (
        current.turn_count
        if prior.session_id == current.session_id
        else (prior.turn_count + current.turn_count)
    )
    return PeerVerdictTelemetry(
        session_id=current.session_id,
        primary_model=current.primary_model,
        input_tokens=prior.input_tokens + current.input_tokens,
        output_tokens=prior.output_tokens + current.output_tokens,
        reasoning_tokens=prior.reasoning_tokens + current.reasoning_tokens,
        cached_read_tokens=prior.cached_read_tokens + current.cached_read_tokens,
        total_tokens=prior.total_tokens + current.total_tokens,
        model_calls=prior.model_calls + current.model_calls,
        turn_count=new_turns,
        cost_usd=round(prior.cost_usd + current.cost_usd, 4),
        cost_mode=(
            "exact" if prior.cost_mode == "exact" and current.cost_mode == "exact" else "estimated"
        ),
        duration_seconds=round(prior.duration_seconds + current.duration_seconds, 2),
        degraded_reasoning=current.degraded_reasoning,
    )


def _accumulate_verdict_telemetry(
    t: Any,
    by_model: dict[str, dict[str, Any]],
    seen_snapshots: set[tuple[str, int, int, float]] | None = None,
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
        sid = str(getattr(t, "session_id", "") or "").strip()
        tc = int(getattr(t, "turn_count", 1) or 1)
        tot = int(getattr(t, "total_tokens", 0) or 0)
        cost = float(getattr(t, "cost_usd", 0.0) or 0.0)
        if seen_snapshots is not None and sid and sid.lower() not in ("none", "unknown"):
            snap_key = (sid, tc, tot, round(cost, 4))
            if snap_key in seen_snapshots:
                return 0, 0.0
            seen_snapshots.add(snap_key)
        m = str(getattr(t, "primary_model", "unknown"))
        entry = by_model.setdefault(m, {"calls": 0, "tokens": 0, "cost_usd": 0.0})
        entry["calls"] += 1
        entry["tokens"] += tot
        entry["cost_usd"] = round(entry["cost_usd"] + cost, 4)
        return tot, cost

    return 0, 0.0


def _normalize_thread_stem(value: str) -> str:
    """Normalizes a request_id or filename stem by stripping prefixes, date tokens, and round suffixes."""
    cleaned = Path(value).stem.strip().lower()
    cleaned = _PREFIX_ROLE_RE.sub("", cleaned)
    cleaned = re.sub(r"^\d{8}[-_]+", "", cleaned)
    cleaned = _STAGE_PREFIX_RE.sub("", cleaned)
    cleaned = _ROUND_SUFFIX_RE.sub("", cleaned)
    return re.sub(r"[-_]+", "_", cleaned).strip("_")


def _has_round_suffix(value: str) -> bool:
    """Checks whether a request_id or filename stem carries a follow-up round/version marker."""
    return bool(_FOLLOWUP_HINT_RE.search(Path(value).stem.strip()))


def _parse_iso_ts(raw_ts: str | None) -> float | None:
    """Parses ISO-8601 timestamp string into epoch seconds, or None if invalid/missing."""
    if raw_ts:
        try:
            dt = datetime.datetime.fromisoformat(str(raw_ts).strip().replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.timestamp()
        except Exception:
            pass
    return None


def _is_stale_prompt(item: dict[str, Any], env: Any, ref_ts: float, max_age_seconds: float) -> bool:
    """Returns True if prompt age exceeds max_age_seconds using min(mtime, envelope timestamp)."""
    if max_age_seconds <= 0 or ref_ts <= 0:
        return False
    mtime = float(item.get("mtime", 0.0))
    env_ts = _parse_iso_ts(getattr(env, "timestamp", None))
    birth_ts = (
        min(mtime, env_ts)
        if (env_ts is not None and mtime > 0)
        else (env_ts if env_ts is not None else mtime)
    )
    return (ref_ts - birth_ts) > max_age_seconds


def _collect_prior_verdict_sessions(
    peer_dir: Path, cur_req_id: str, cur_out_name: str, p_iso: float | None, p_mtime: float
) -> tuple[dict[str, Any], list[tuple[float, float, str, Any, str]]]:
    """Scans peer_dir deterministically for prior prompt envelopes and verdicts with valid session_id."""
    prompts_by_req: dict[str, Any] = {}
    raw_verdicts: list[tuple[float, str, Any, str]] = []
    if not peer_dir.is_dir():
        return prompts_by_req, []
    for entry in sorted(os.scandir(peer_dir), key=lambda e: e.name):
        if not entry.is_file() or not entry.name.endswith(".md") or entry.name.startswith("."):
            continue
        try:
            p = Path(entry.path)
            text, mtime = p.read_text(encoding="utf-8"), entry.stat().st_mtime
        except (OSError, UnicodeDecodeError):
            continue
        if entry.name.startswith("prompt_"):
            env = parse_envelope_from_md(text, prompt_path=p)
            if env and env.request_id:
                prompts_by_req[env.request_id] = env
        elif entry.name.startswith(_VERDICT_FILE_PREFIXES) and entry.name != cur_out_name:
            v = parse_verdict_from_md(text)
            sid = (
                str(getattr(v.telemetry, "session_id", "") or "").strip()
                if v and v.telemetry
                else ""
            )
            if v and v.request_id != cur_req_id and sid and sid.lower() not in ("none", "unknown"):
                raw_verdicts.append((mtime, entry.name, v, sid))
    verdicts: list[tuple[float, float, str, Any, str]] = []
    for mt, v_name, v, sid in raw_verdicts:
        p_env = prompts_by_req.get(v.request_id)
        v_iso = _parse_iso_ts(v.timestamp or (p_env.timestamp if p_env else None))
        delta_sec = (p_iso - v_iso) if (p_iso is not None and v_iso is not None) else (p_mtime - mt)
        if -60.0 <= delta_sec <= _MAX_RESUME_AGE_SECONDS:
            verdicts.append((delta_sec, mt, v_name, v, sid))
    verdicts.sort(key=lambda item: (round(item[0], 4), -round(item[1], 4), item[2]))
    return prompts_by_req, verdicts


def _extract_clean_doc_set(envelope: Any) -> set[str]:
    """Returns normalized document/target path set excluding internal .md/peer_exchange paths."""
    if envelope is None:
        return set()
    raw = (getattr(envelope, "source_documents", None) or []) + (
        getattr(envelope, "target_files", None) or []
    )
    return {
        str(d).strip()
        for d in raw
        if str(d).strip() and not str(d).strip().startswith(".md/peer_exchange/")
    }


def _has_plan_phase_token(*texts: str) -> bool:
    """Returns True if any identifier contains a phase-level `plan` segment (excluding AEC nouns)."""
    for raw in texts:
        cleaned = _NON_PHASE_PLAN_RE.sub("", str(raw or ""))
        if _PLAN_PHASE_RE.search(cleaned):
            return True
    return False


def _is_prior_plan_session(prior_env: Any, verdict: Any, verdict_name: str) -> bool:
    """Returns True when a prior prompt/verdict pair belongs to the Plan Audit phase."""
    p_prof = getattr(prior_env, "profile", None) if prior_env is not None else None
    p_req = getattr(prior_env, "request_type", None) if prior_env is not None else None
    v_type = getattr(verdict, "verdict", None)
    if v_type in ("APPROVE_PLAN", "REVISE_PLAN", "REJECT_PLAN") or p_prof in _PLAN_AUDIT_PROFILES:
        return True
    if p_prof in _CODE_AUDIT_PROFILES:
        return False
    if p_req == "plan":
        return True
    has_tok = _has_plan_phase_token(verdict_name, str(getattr(verdict, "request_id", "") or ""))
    if p_req == "discuss" or v_type in ("FINAL_ACCEPT", "APPROVE_WITH_CONDITIONS", "APPROVE"):
        return has_tok
    return False


def _is_code_phase_target(envelope: Any, effective_profile: str | None = None) -> bool:
    """Returns True when the current dispatch targets post-implementation code review/audit."""
    if envelope is None and not effective_profile:
        return False
    prof = effective_profile or (
        getattr(envelope, "profile", None) if envelope is not None else None
    )
    if prof in _CODE_AUDIT_PROFILES:
        return True
    if prof in _PLAN_AUDIT_PROFILES or prof == "signoff_diff":
        return False
    req_type = getattr(envelope, "request_type", None) if envelope is not None else None
    if req_type in ("review", "audit", "implement"):
        return not _has_plan_phase_token(
            str(getattr(envelope, "request_id", "") or ""),
            str(getattr(envelope, "output_path", "") or ""),
        )
    return False


def _match_tier1_stem_session(
    cur_req: str,
    prompt_name: str,
    verdicts: list[tuple[float, float, str, Any, str]],
    prompts_by_req: dict[str, Any] | None = None,
    block_plan_sessions: bool = False,
) -> str | None:
    """Matches follow-up prompt stem against prior verdict request_id or filename stems."""
    req_stem, file_stem = _normalize_thread_stem(cur_req), _normalize_thread_stem(prompt_name)
    for _, _, v_name, v, sid in verdicts:
        if block_plan_sessions and _is_prior_plan_session(
            (prompts_by_req or {}).get(v.request_id), v, v_name
        ):
            continue
        vr_stem, vf_stem = _normalize_thread_stem(v.request_id), _normalize_thread_stem(v_name)
        if (req_stem and vr_stem == req_stem) or (file_stem and vf_stem == file_stem):
            return sid
        if (
            req_stem
            and vr_stem
            and (req_stem in vr_stem or vr_stem in req_stem)
            and min(len(req_stem), len(vr_stem)) >= 8
        ):
            return sid
    return None


def _match_tier2_doc_session(
    envelope: Any,
    is_fu: bool,
    block_plan: bool,
    prompts_by_req: dict[str, Any],
    verdicts: list[tuple[float, float, str, Any, str]],
) -> str | None:
    """Matches prior session via document/target_files Jaccard >= 0.5 or active discuss thread."""
    cur_docs, req_type = _extract_clean_doc_set(envelope), getattr(envelope, "request_type", None)
    if not cur_docs:
        return None
    for delta_sec, _, v_name, v, sid in verdicts:
        if block_plan and _is_prior_plan_session(prompts_by_req.get(v.request_id), v, v_name):
            continue
        if (
            not is_fu
            and req_type not in ("verify", "patch", "discuss", "architecture")
            and _has_round_suffix(v_name)
        ):
            continue
        if req_type in ("discuss", "architecture") and not is_fu and delta_sec <= 7200:
            return sid
        p_docs = _extract_clean_doc_set(prompts_by_req.get(v.request_id))
        if p_docs and (
            cur_docs == p_docs or len(cur_docs & p_docs) / len(cur_docs | p_docs) >= 0.5
        ):
            return sid
    return None


def _auto_discover_resume_session_id(
    prompt_path: Path | None, envelope: Any, *, effective_profile: str | None = None
) -> str | None:
    """Discovers prior session_id across 3 tiers while blocking Plan->Code phase leaks."""
    if prompt_path is None or envelope is None or not prompt_path.parent.is_dir():
        return None
    cur_req = str(getattr(envelope, "request_id", "") or "")
    cur_out = Path(str(getattr(envelope, "output_path", "") or "")).name
    p_mtime = prompt_path.stat().st_mtime if prompt_path.exists() else time.time()
    prompts_by_req, verdicts = _collect_prior_verdict_sessions(
        prompt_path.parent,
        cur_req,
        cur_out,
        _parse_iso_ts(getattr(envelope, "timestamp", None)),
        p_mtime,
    )
    if not verdicts:
        return None
    eff_prof = effective_profile or getattr(envelope, "profile", None)
    block_plan = _is_code_phase_target(envelope, eff_prof)
    is_fu = (
        _has_round_suffix(cur_req)
        or _has_round_suffix(prompt_path.name)
        or eff_prof == "signoff_diff"
    )
    if is_fu:
        hit = _match_tier1_stem_session(
            cur_req, prompt_path.name, verdicts, prompts_by_req, block_plan
        )
        if hit:
            return hit
    hit_t2 = _match_tier2_doc_session(envelope, is_fu, block_plan, prompts_by_req, verdicts)
    if hit_t2:
        return hit_t2
    if getattr(envelope, "request_type", None) in ("discuss", "architecture") and not block_plan:
        for delta_sec, _, _, _, sid in verdicts:
            if delta_sec <= 14400:
                return sid
    return None


def _check_resumed_payload_bloat(prompt_path: Path | None, eff_resume: str | None) -> bool:
    """Emits stderr warning when a resumed prompt re-injects full-document payload (>400 lines or >20KB)."""
    if not eff_resume or prompt_path is None or not prompt_path.is_file():
        return False
    try:
        raw_bytes = prompt_path.read_bytes()
        line_count = len(raw_bytes.decode("utf-8", errors="replace").splitlines())
    except OSError:
        return False
    if line_count > _RESUMED_BLOAT_MAX_LINES or len(raw_bytes) > _RESUMED_BLOAT_MAX_BYTES:
        print(
            f"[WARN-RESUMED-PAYLOAD-BLOAT] Prompt '{prompt_path.name}' ({line_count} lines, "
            f"{len(raw_bytes)}B) resumes session {eff_resume} with full-text payload; "
            "prefer sending only conditions resolution + diff.",
            file=sys.stderr,
        )
        return True
    return False


def _resolve_effective_resume_session(
    resume_session_id: str | None,
    envelope: Any,
    prompt_path: Path | None = None,
    *,
    effective_profile: str | None = None,
) -> str | None:
    """Resolves explicit or auto-discovered resume_session_id and checks payload bloat."""
    raw = resume_session_id or (envelope.resume_session_id if envelope is not None else None)
    if raw is not None and str(raw).strip().lower() in _OPT_OUT_RESUME_TOKENS:
        return None
    eff_resume = (
        str(raw).strip()
        if raw
        else _auto_discover_resume_session_id(
            prompt_path, envelope, effective_profile=effective_profile
        )
    )
    _check_resumed_payload_bloat(prompt_path, eff_resume)
    return eff_resume


def _build_latest_verdict(registry: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Extracts the most recent Grok verdict details from registry."""
    grok_resps = [
        item
        for item in registry.values()
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]
    ]
    if not grok_resps:
        return None
    grok_resps.sort(key=_sort_key_latest_exchange, reverse=True)
    top = grok_resps[0]
    verdict = top["verdict"]
    return {
        "request_id": verdict.request_id,
        "verdict": verdict.verdict,
        "blocking_conditions": len([c for c in verdict.conditions if c.blocking]),
        "output_path": top["path"].name,
        "summary": verdict.summary,
    }


def _aggregate_registry_telemetry(
    registry: dict[str, dict[str, Any]],
) -> tuple[int, float, dict[str, dict[str, Any]]]:
    """Aggregates token and cost telemetry across all registry verdict entries."""
    total_tokens = 0
    total_cost_usd = 0.0
    by_model: dict[str, dict[str, Any]] = {}
    seen_snapshots: set[tuple[str, int, int, float]] = set()
    for item in registry.values():
        v = item.get("verdict")
        if v and getattr(v, "telemetry", None):
            tok_delta, cost_delta = _accumulate_verdict_telemetry(
                v.telemetry, by_model, seen_snapshots
            )
            total_tokens += tok_delta
            total_cost_usd += cost_delta
    return total_tokens, total_cost_usd, by_model


def _attach_verdict_lineage(
    verdict: PeerVerdictBlock,
    prompt_path: Path,
    prompt_content: str | None,
) -> None:
    """Populates verdict lineage in-memory from prompt envelope and runtime env without rewriting prompt."""
    content = prompt_content
    if content is None:
        try:
            content = prompt_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            content = ""
    envelope = parse_envelope_from_md(content or "", prompt_path=prompt_path)
    env_cid = extract_env_conversation_id()
    verdict.conversation_id = (
        verdict.conversation_id or (envelope.conversation_id if envelope else None) or env_cid
    )
    verdict.task_id = verdict.task_id or (envelope.task_id if envelope else None)
    verdict.spoke_name = (
        verdict.spoke_name
        or (envelope.spoke_name if envelope else None)
        or resolve_spoke_slug_from_path(prompt_path, allow_ancestor_walk=bool(env_cid))
    )
    verdict.tags = verdict.tags or ((envelope.tags or None) if envelope else None)
