#!/usr/bin/env python3
"""scripts/governance/audit_peer_effectiveness.py - Pre/Post v2.6 effectiveness & escaped-defect auditor."""

from __future__ import annotations

import argparse
import datetime
import json
import re
import statistics
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

_DEFAULT_CUTOFF = "2026-11-25T07:08:00+07:00"
_DEFAULT_BASELINE_SINCE = "2026-11-11T00:00:00+07:00"
_MAX_INFER_RESUME_AGE_S = 43_200.0
_ESCAPED_PR_RE = re.compile(r"Escaped-From-PR:\s*#(\d+)", re.IGNORECASE)
_PRIOR_BY_RE = re.compile(
    r"Prior-Reviewed-By:\s*(grok\+coderabbit|grok|coderabbit|copilot|none)",
    re.IGNORECASE,
)
_FIX_SUBJECT_RE = re.compile(r"^(?:fix(?:\([^)]+\))?:|revert\b)", re.IGNORECASE)
_TRIAGE_TOKENS = ("[ADOPT_AS_IS]", "[ADOPT_ADAPTED]", "[REBUT_WITH_EVIDENCE]")
_HIGH_CHURN_PREFIXES = (".github/", "docs/rules/", ".md/")
_HIGH_CHURN_EXACT = ("AGENTS.md", "uv.lock")
_GUARD_PREFIXES = ("tests/", "scripts/tests/")
_GUARD_EXACT = ("_parameter_cleanliness.py", "peer_gate.py")
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
_CODE_AUDIT_PROFILES: frozenset[str] = frozenset(
    {"arch_audit", "code_review", "audit_direct", "agentic_code", "patch_fast"}
)
_PLAN_AUDIT_PROFILES: frozenset[str] = frozenset({"audit_plan", "deep_spec_audit"})
_PLAN_PHASE_RE = re.compile(r"(?:^|[-_.])plan(?:[-_.]|$)", re.IGNORECASE)
_NON_PHASE_PLAN_RE = re.compile(r"(?:floor|site|master|key|roof)[-_]plan", re.IGNORECASE)


def parse_utc_timestamp(raw: Any) -> datetime.datetime | None:
    """Parse an ISO-8601 timestamp with timezone (normalizing 'Z' for Python 3.10)."""
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = f"{cleaned[:-1]}+00:00"
    try:
        parsed = datetime.datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(datetime.timezone.utc)


def _discover_exchange_files(roots: Sequence[Path]) -> list[Path]:
    """Discover peer_exchange markdown files in deterministic inode-invariant order."""
    files: list[Path] = []
    seen: set[Path] = set()
    for root in sorted(roots, key=lambda p: str(p)):
        exchange_dir = root if root.name == "peer_exchange" else root / ".md" / "peer_exchange"
        if not exchange_dir.is_dir():
            continue
        for md_path in sorted(exchange_dir.glob("*.md"), key=lambda p: (p.stem, p.name)):
            if md_path.name in ("PEER_HANDSHAKE.md", "README.md"):
                continue
            resolved = md_path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(md_path)
    return files


def _extract_last_event_ts(text: str) -> datetime.datetime | None:
    """Return the latest valid UTC timestamp from an events.jsonl payload."""
    for raw in reversed(text.splitlines()):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            ts = parse_utc_timestamp(obj.get("ts"))
            if ts is not None:
                return ts
    return None


def _index_session_events(
    sessions_dir: Path | None,
) -> dict[str, tuple[bool, datetime.datetime | None]]:
    """Index Grok session_id -> (max_turns_reached_seen, last_event_utc_ts)."""
    if sessions_dir is None or not sessions_dir.is_dir():
        return {}
    result: dict[str, tuple[bool, datetime.datetime | None]] = {}
    for ev_path in sorted(sessions_dir.rglob("events.jsonl"), key=lambda p: str(p)):
        sid = ev_path.parent.name
        try:
            text = ev_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        result[sid] = ('"max_turns_reached"' in text, _extract_last_event_ts(text))
    return result


def _extract_telemetry_metrics(
    tel: Any,
    session_events: dict[str, tuple[bool, datetime.datetime | None]],
) -> dict[str, Any]:
    """Extract duration, cost, tokens, Auto-Synthesis, and session timestamp."""
    if tel is None:
        return {
            "dur": 0.0,
            "cost": 0.0,
            "inp": 0,
            "cached": 0,
            "auto_synth": False,
            "src": "none",
            "session_ts": None,
        }
    session_ts: datetime.datetime | None = None
    if hasattr(tel, "wall_seconds"):
        dur = float(getattr(tel, "wall_seconds", 0.0) or 0.0)
        auto_synth = False
        src = "combined"
    else:
        dur = float(getattr(tel, "duration_seconds", 0.0) or 0.0)
        sid = str(getattr(tel, "session_id", "") or "")
        if sid and sid in session_events:
            auto_synth, session_ts = session_events[sid]
            src = "session_events"
        else:
            auto_synth = int(getattr(tel, "turn_count", 1) or 1) >= 2
            src = "turn_count_fallback"
    return {
        "dur": dur,
        "cost": float(getattr(tel, "cost_usd", 0.0) or 0.0),
        "inp": int(getattr(tel, "input_tokens", 0) or 0),
        "cached": int(getattr(tel, "cached_read_tokens", 0) or 0),
        "auto_synth": auto_synth,
        "src": src,
        "session_ts": session_ts,
    }


def _normalize_thread_stem(value: str) -> str:
    """Normalize a request_id or filename stem by stripping prefixes, dates, and round suffixes."""
    cleaned = Path(value).stem.strip().lower()
    cleaned = _PREFIX_ROLE_RE.sub("", cleaned)
    cleaned = re.sub(r"^\d{8}[-_]+", "", cleaned)
    cleaned = _STAGE_PREFIX_RE.sub("", cleaned)
    cleaned = _ROUND_SUFFIX_RE.sub("", cleaned)
    return re.sub(r"[-_]+", "_", cleaned).strip("_")


def _has_round_suffix(value: str) -> bool:
    """Return True if a request_id or filename stem carries a follow-up round marker."""
    return bool(_FOLLOWUP_HINT_RE.search(Path(value).stem.strip()))


def _has_plan_phase_token(*texts: str) -> bool:
    """Return True if any identifier contains a phase-level plan segment (excluding AEC nouns)."""
    for raw in texts:
        cleaned = _NON_PHASE_PLAN_RE.sub("", str(raw or ""))
        if _PLAN_PHASE_RE.search(cleaned):
            return True
    return False


def _is_opt_out_resume(raw_resume: Any) -> bool:
    """Return True when resume_session_id explicitly opts out of chaining (None-safe)."""
    return raw_resume is not None and str(raw_resume).strip().lower() in _OPT_OUT_RESUME_TOKENS


def _is_prior_plan_record(rec: dict[str, Any]) -> bool:
    """Return True when a verdict record dict belongs to the Plan Audit phase."""
    p_prof, p_req, v_type = rec.get("profile"), rec.get("request_type"), rec.get("verdict")
    if v_type in ("APPROVE_PLAN", "REVISE_PLAN", "REJECT_PLAN") or p_prof in _PLAN_AUDIT_PROFILES:
        return True
    if p_prof in _CODE_AUDIT_PROFILES:
        return False
    if p_req == "plan":
        return True
    has_tok = _has_plan_phase_token(
        str(rec.get("file_name") or ""), str(rec.get("request_id") or "")
    )
    if p_req == "discuss" or v_type in ("FINAL_ACCEPT", "APPROVE_WITH_CONDITIONS", "APPROVE"):
        return has_tok
    return False


def _is_code_phase_record(rec: dict[str, Any]) -> bool:
    """Return True when a verdict record dict targets post-implementation code review/audit."""
    prof = rec.get("profile")
    if prof in _CODE_AUDIT_PROFILES:
        return True
    if prof in _PLAN_AUDIT_PROFILES or prof == "signoff_diff":
        return False
    if rec.get("request_type") in ("review", "audit", "implement"):
        return not _has_plan_phase_token(
            str(rec.get("request_id") or ""), str(rec.get("file_name") or "")
        )
    return False


def _matches_parent_stem(cur: dict[str, Any], prev: dict[str, Any]) -> bool:
    """Match file stems by equality and request stems by equality or >=8-char containment."""
    req_stem = _normalize_thread_stem(str(cur.get("request_id") or ""))
    file_stem = _normalize_thread_stem(str(cur.get("file_name") or ""))
    vr_stem = _normalize_thread_stem(str(prev.get("request_id") or ""))
    vf_stem = _normalize_thread_stem(str(prev.get("file_name") or ""))
    if (req_stem and vr_stem == req_stem) or (file_stem and vf_stem == file_stem):
        return True
    return bool(
        req_stem
        and vr_stem
        and (req_stem in vr_stem or vr_stem in req_stem)
        and min(len(req_stem), len(vr_stem)) >= 8
    )


def _find_inferred_parent_session(
    cur: dict[str, Any], prior_bucket: Sequence[dict[str, Any]]
) -> str | None:
    """Find the nearest prior same-dir parent session within 12h blocking Plan->Code leaks."""
    cur_sid = str(cur.get("session_id") or "").strip()
    block_plan = _is_code_phase_record(cur)
    for prev in reversed(prior_bucket):
        if prev["request_id"] == cur["request_id"]:
            continue
        prev_sid = str(prev.get("session_id") or "").strip()
        if not prev_sid or prev_sid.lower() in ("none", "unknown") or prev_sid == cur_sid:
            continue
        delta = (cur["ts"] - prev["ts"]).total_seconds()
        if delta <= 0:
            continue
        if delta > _MAX_INFER_RESUME_AGE_S:
            break
        if block_plan and _is_prior_plan_record(prev):
            continue
        if _matches_parent_stem(cur, prev):
            return prev_sid
    return None


def _infer_missing_resume_links(records: list[dict[str, Any]]) -> int:
    """Deterministically infer missing CLI-resumed Pass 2+ parent links per exchange directory."""
    by_dir: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        if rec.get("ts") is not None:
            by_dir.setdefault(str(rec.get("exchange_dir") or ""), []).append(rec)
    inferred = 0
    for bucket in by_dir.values():
        bucket.sort(key=lambda r: (r["ts"], r["request_id"]))
        for idx, cur in enumerate(bucket):
            if cur.get("resume_id") or cur.get("opt_out_resume"):
                continue
            is_fu = (
                cur.get("profile") == "signoff_diff"
                or _has_round_suffix(str(cur.get("request_id") or ""))
                or _has_round_suffix(str(cur.get("file_name") or ""))
            )
            if not is_fu:
                continue
            parent_sid = _find_inferred_parent_session(cur, bucket[:idx])
            if parent_sid:
                cur["resume_id"] = parent_sid
                cur["is_pass2_plus"] = True
                inferred += 1
    return inferred


def _attach_prompt_metadata(verdicts: dict[str, dict[str, Any]], prompts: dict[str, Any]) -> None:
    """Join prompt timestamps, profiles, request types, and resume_session_id onto verdicts."""
    for rid, rec in verdicts.items():
        env = prompts.get(rid)
        if rec["ts"] is None and env is not None:
            rec["ts"] = parse_utc_timestamp(getattr(env, "timestamp", None))
        if rec["ts"] is None:
            rec["ts"] = rec.get("session_ts")
        raw_resume = getattr(env, "resume_session_id", None) if env is not None else None
        opt_out = _is_opt_out_resume(raw_resume)
        clean_res = (
            None
            if (raw_resume is None or opt_out or not str(raw_resume).strip())
            else str(raw_resume).strip()
        )
        rec["profile"] = getattr(env, "profile", None) if env is not None else None
        rec["request_type"] = getattr(env, "request_type", None) if env is not None else None
        rec["opt_out_resume"] = opt_out
        rec["resume_id"] = clean_res
        rec["is_pass2_plus"] = bool(clean_res)


def _collect_verdict_records(
    roots: Sequence[Path],
    session_events: dict[str, tuple[bool, datetime.datetime | None]],
) -> tuple[list[dict[str, Any]], int, dict[str, int], int]:
    """Parse exchange files ensuring verdict overrides prompt per request_id."""
    from ccba_harness.peer import parse_envelope_from_md, parse_verdict_from_md

    prompts: dict[str, Any] = {}
    verdicts: dict[str, dict[str, Any]] = {}
    triage_counts = dict.fromkeys(_TRIAGE_TOKENS, 0)
    for md_path in _discover_exchange_files(roots):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for tok in _TRIAGE_TOKENS:
            triage_counts[tok] += text.count(tok)
        verdict = parse_verdict_from_md(text)
        if verdict is not None:
            tel_meta = _extract_telemetry_metrics(verdict.telemetry, session_events)
            verdicts[verdict.request_id] = {
                "request_id": verdict.request_id,
                "file_name": md_path.name,
                "exchange_dir": str(md_path.parent.resolve()),
                "ts": parse_utc_timestamp(verdict.timestamp),
                "blocking": sum(1 for c in verdict.conditions if c.blocking),
                "session_id": getattr(verdict.telemetry, "session_id", None),
                "verdict": verdict.verdict,
                **tel_meta,
            }
            continue
        env = parse_envelope_from_md(text, prompt_path=md_path)
        if env is not None:
            prompts[env.request_id] = env
    _attach_prompt_metadata(verdicts, prompts)
    verdict_list = list(verdicts.values())
    inferred_links = _infer_missing_resume_links(verdict_list)
    prompt_only = sum(1 for rid in prompts if rid not in verdicts)
    return verdict_list, prompt_only, triage_counts, inferred_links


def _summarize_cohort(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute latency, cost, KV-cache, Auto-Synthesis, and pass blocking metrics."""
    if not records:
        return {"runs": 0, "chains": 0, "median_chain_s": 0.0, "median_chain_cost_usd": 0.0}
    sid_to_parent: dict[str, str] = {}
    for rec in records:
        sid = rec.get("session_id")
        res = rec.get("resume_id")
        if sid and res and res != "new":
            sid_to_parent[sid] = res
    chains: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        cur = rec.get("session_id") or rec["request_id"]
        seen: set[str] = set()
        while cur in sid_to_parent and sid_to_parent[cur] not in seen:
            seen.add(cur)
            cur = sid_to_parent[cur]
        chains.setdefault(cur, []).append(rec)
    chain_durs = [sum(r["dur"] for r in items) for items in chains.values()]
    chain_costs = [sum(r["cost"] for r in items) for items in chains.values()]
    total_inp = sum(r["inp"] for r in records)
    total_cached = sum(r["cached"] for r in records)
    p1 = [r for r in records if not r["is_pass2_plus"]]
    p2 = [r for r in records if r["is_pass2_plus"]]
    src_counts = {
        s: sum(1 for r in records if r["src"] == s) for s in sorted({r["src"] for r in records})
    }
    return {
        "runs": len(records),
        "chains": len(chains),
        "median_chain_s": round(statistics.median(chain_durs), 2),
        "median_chain_cost_usd": round(statistics.median(chain_costs), 4),
        "total_cost_usd": round(sum(chain_costs), 4),
        "kv_cache_ratio": round(total_cached / total_inp, 4) if total_inp > 0 else 0.0,
        "auto_synthesis_rate": round(sum(1 for r in records if r["auto_synth"]) / len(records), 4),
        "auto_synthesis_sources": src_counts,
        "pass1_blocking_rate": round(sum(1 for r in p1 if r["blocking"] > 0) / len(p1), 4)
        if p1
        else 0.0,
        "pass2_blocking_rate": round(sum(1 for r in p2 if r["blocking"] > 0) / len(p2), 4)
        if p2
        else 0.0,
    }


def _is_churn_or_docs_path(path: str) -> bool:
    """Filter high-churn governance/doc paths from untagged escaped-defect matching."""
    norm = path.replace("\\", "/")
    if norm in _HIGH_CHURN_EXACT or norm.endswith(".lock") or "catalog" in norm.lower():
        return True
    return norm.startswith(_HIGH_CHURN_PREFIXES)


def _has_regression_test_or_guard(paths: Sequence[str]) -> bool:
    """Return True if commit paths include a unit test or static guard check."""
    for p in paths:
        norm = p.replace("\\", "/")
        name = Path(norm).name
        if (
            norm.startswith(_GUARD_PREFIXES)
            or "/tests/" in norm
            or name.startswith("test_")
            or name in _GUARD_EXACT
        ):
            return True
    return False


def _parse_git_commits(repo_root: Path) -> list[dict[str, Any]]:
    """Read git commits with timestamps, bodies, and changed file names."""
    fmt = "%x1e%H%x1f%cI%x1f%s%x1f%b%x1d"
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "log", "--name-only", f"--format={fmt}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        return []
    commits: list[dict[str, Any]] = []
    for block in proc.stdout.split("\x1e"):
        if not block.strip() or "\x1d" not in block:
            continue
        meta_raw, files_raw = block.split("\x1d", 1)
        parts = meta_raw.split("\x1f")
        if len(parts) < 4:
            continue
        ts = parse_utc_timestamp(parts[1])
        if ts is None:
            continue
        files = [f.strip() for f in files_raw.splitlines() if f.strip()]
        commits.append(
            {
                "sha": parts[0],
                "ts": ts,
                "subject": parts[2].strip(),
                "body": parts[3],
                "files": files,
            }
        )
    return commits


def _analyze_escaped_defects(
    commits: list[dict[str, Any]],
    cutoff_utc: datetime.datetime,
    window_days: int,
) -> dict[str, Any]:
    """Compute confirmed_tagged, missing regression guard count, and candidate_untagged."""
    confirmed: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    missing_guard = 0
    window = datetime.timedelta(days=window_days)
    for idx, c in enumerate(commits):
        text = f"{c['subject']}\n{c['body']}"
        tag_m = _ESCAPED_PR_RE.search(text)
        cohort = "post_v26" if c["ts"] >= cutoff_utc else "pre_v26"
        if tag_m:
            by_m = _PRIOR_BY_RE.search(text)
            has_guard = _has_regression_test_or_guard(c["files"])
            if not has_guard:
                missing_guard += 1
            confirmed.append(
                {
                    "sha": c["sha"][:8],
                    "cohort": cohort,
                    "escaped_from_pr": f"#{tag_m.group(1)}",
                    "prior_reviewed_by": by_m.group(1).lower() if by_m else "unspecified",
                    "has_regression_guard": has_guard,
                }
            )
            continue
        if not _FIX_SUBJECT_RE.match(c["subject"]):
            continue
        code_files = {f for f in c["files"] if not _is_churn_or_docs_path(f)}
        if not code_files:
            continue
        for prev in commits[idx + 1 :]:
            delta = c["ts"] - prev["ts"]
            if delta > window:
                break
            if delta.total_seconds() >= 0 and (code_files & set(prev["files"])):
                candidates.append({"sha": c["sha"][:8], "cohort": cohort, "subject": c["subject"]})
                break
    return {
        "confirmed_tagged": confirmed,
        "confirmed_missing_regression_test": missing_guard,
        "candidate_untagged_count": len(candidates),
        "candidate_heuristic_note": (
            f"Git {window_days}-day file-overlap heuristic excluding churn paths; "
            "git log alone lacks Grok/AI review attribution."
        ),
    }


def _parse_baseline_since_utc(baseline_since: str | None) -> datetime.datetime | None:
    """Parse optional timezone-aware baseline_since lower bound ('all' or None disables)."""
    if baseline_since is None or baseline_since.strip().lower() == "all":
        return None
    parsed = parse_utc_timestamp(baseline_since)
    if parsed is None:
        raise ValueError(f"Invalid timezone-aware ISO baseline_since timestamp: {baseline_since!r}")
    return parsed


def _partition_verdicts_by_window(
    verdicts: Sequence[dict[str, Any]],
    cutoff_utc: datetime.datetime,
    baseline_utc: datetime.datetime | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int]:
    """Split verdicts into pre/post cohorts while counting undated and pre-baseline exclusions."""
    pre_recs: list[dict[str, Any]] = []
    post_recs: list[dict[str, Any]] = []
    undated_excluded = 0
    pre_baseline_excluded = 0
    for rec in verdicts:
        ts = rec["ts"]
        if ts is None:
            undated_excluded += 1
        elif ts >= cutoff_utc:
            post_recs.append(rec)
        elif baseline_utc is not None and ts < baseline_utc:
            pre_baseline_excluded += 1
        else:
            pre_recs.append(rec)
    return pre_recs, post_recs, undated_excluded, pre_baseline_excluded


def evaluate_peer_effectiveness(
    roots: Sequence[Path],
    *,
    cutoff: str = _DEFAULT_CUTOFF,
    baseline_since: str | None = None,
    window_days: int = 14,
    sessions_dir: Path | None = None,
    use_git: bool = True,
) -> dict[str, Any]:
    """Evaluate Pre-v2.6 vs Post-v2.6 peer collaboration KPIs and escaped defects."""
    cutoff_utc = parse_utc_timestamp(cutoff)
    if cutoff_utc is None:
        raise ValueError(f"Invalid timezone-aware ISO cutoff timestamp: {cutoff!r}")
    baseline_utc = _parse_baseline_since_utc(baseline_since)
    sess_map = _index_session_events(sessions_dir)
    verdicts, prompt_only_cnt, triage_counts, inferred_links = _collect_verdict_records(
        roots, sess_map
    )
    pre_recs, post_recs, undated_excluded, pre_baseline_excluded = _partition_verdicts_by_window(
        verdicts, cutoff_utc, baseline_utc
    )
    commits = _parse_git_commits(roots[0]) if use_git and roots else []
    escaped = (
        _analyze_escaped_defects(commits, cutoff_utc, window_days)
        if use_git
        else {
            "confirmed_tagged": [],
            "confirmed_missing_regression_test": 0,
            "candidate_untagged_count": 0,
            "candidate_heuristic_note": "Skipped (--no-git).",
        }
    )
    return {
        "cutoff_utc": cutoff_utc.isoformat(),
        "baseline_since_utc": baseline_utc.isoformat() if baseline_utc is not None else None,
        "pre_baseline_excluded": pre_baseline_excluded,
        "undated_excluded": undated_excluded,
        "inferred_chain_links": inferred_links,
        "prompt_only_count": prompt_only_cnt,
        "pre_v26": _summarize_cohort(pre_recs),
        "post_v26": _summarize_cohort(post_recs),
        "triage_counts": triage_counts,
        "escaped_defects": escaped,
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render effectiveness audit report in concise GitHub Markdown."""
    pre, post, esc = report["pre_v26"], report["post_v26"], report["escaped_defects"]
    baseline_label = report.get("baseline_since_utc") or "all"
    lines = [
        f"# Peer Collaboration v2.6 A/B & Escaped-Defect Audit (Cutoff `{report['cutoff_utc']}`, Baseline `>= {baseline_label}`)",
        (
            f"- Pre-baseline excluded: `{report.get('pre_baseline_excluded', 0)}` | "
            f"Undated excluded: `{report['undated_excluded']}` | "
            f"Inferred Pass 2+ links: `{report.get('inferred_chain_links', 0)}` | "
            f"Prompt-only: `{report['prompt_only_count']}`"
        ),
        "",
        "| KPI | Pre-v2.6 | Post-v2.6 |",
        "| :--- | ---: | ---: |",
        f"| Verdicts / Chains | {pre['runs']} / {pre['chains']} | {post['runs']} / {post['chains']} |",
        f"| Median Chain Duration (s) | {pre['median_chain_s']} | {post['median_chain_s']} |",
        f"| Median Chain Cost (USD) | \\${pre['median_chain_cost_usd']} | \\${post['median_chain_cost_usd']} |",
        f"| KV-Cache Ratio | {pre.get('kv_cache_ratio', 0.0):.1%} | {post.get('kv_cache_ratio', 0.0):.1%} |",
        f"| Auto-Synthesis Rate | {pre.get('auto_synthesis_rate', 0.0):.1%} | {post.get('auto_synthesis_rate', 0.0):.1%} |",
        f"| Pass 1 / Pass 2+ Blocking | {pre.get('pass1_blocking_rate', 0.0):.1%} / {pre.get('pass2_blocking_rate', 0.0):.1%} | {post.get('pass1_blocking_rate', 0.0):.1%} / {post.get('pass2_blocking_rate', 0.0):.1%} |",
        "",
        f"- Escaped Defects (`confirmed_tagged`): `{len(esc['confirmed_tagged'])}` (missing regression test/guard warn: `{esc['confirmed_missing_regression_test']}`)",
        f"- Untagged 14d Candidates (`candidate_untagged`): `{esc['candidate_untagged_count']}` — *{esc['candidate_heuristic_note']}*",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for Pre/Post v2.6 peer collaboration effectiveness audit."""
    parser = argparse.ArgumentParser(description="Audit Pre/Post v2.6 peer effectiveness.")
    parser.add_argument("--roots", nargs="+", type=Path, default=[Path.cwd()])
    parser.add_argument("--cutoff", default=_DEFAULT_CUTOFF)
    parser.add_argument(
        "--baseline-since",
        default=_DEFAULT_BASELINE_SINCE,
        help="ISO-8601 UTC/TZ lower bound for Pre-v2.6 cohort, or 'all' for unfiltered history.",
    )
    parser.add_argument("--git-window-days", type=int, default=14)
    parser.add_argument("--sessions-dir", type=Path, default=Path.home() / ".grok" / "sessions")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--no-git", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = evaluate_peer_effectiveness(
        args.roots,
        cutoff=args.cutoff,
        baseline_since=args.baseline_since,
        window_days=args.git_window_days,
        sessions_dir=args.sessions_dir,
        use_git=not args.no_git,
    )
    print(
        json.dumps(report, indent=2, ensure_ascii=False)
        if args.format == "json"
        else render_markdown_report(report)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
