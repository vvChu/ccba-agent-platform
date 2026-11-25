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


def _index_session_max_turns(sessions_dir: Path | None) -> dict[str, bool]:
    """Index Grok session_id -> whether events.jsonl recorded max_turns_reached."""
    if sessions_dir is None or not sessions_dir.is_dir():
        return {}
    result: dict[str, bool] = {}
    for ev_path in sorted(sessions_dir.rglob("events.jsonl"), key=lambda p: str(p)):
        sid = ev_path.parent.name
        try:
            text = ev_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        result[sid] = '"max_turns_reached"' in text
    return result


def _extract_telemetry_metrics(
    tel: Any,
    session_max_turns: dict[str, bool],
) -> dict[str, Any]:
    """Extract duration, cost, tokens, and Auto-Synthesis flags across telemetry union."""
    if tel is None:
        return {"dur": 0.0, "cost": 0.0, "inp": 0, "cached": 0, "auto_synth": False, "src": "none"}
    if hasattr(tel, "wall_seconds"):
        dur = float(getattr(tel, "wall_seconds", 0.0) or 0.0)
        sid = ""
        auto_synth = False
        src = "combined"
    else:
        dur = float(getattr(tel, "duration_seconds", 0.0) or 0.0)
        sid = str(getattr(tel, "session_id", "") or "")
        if sid and sid in session_max_turns:
            auto_synth = session_max_turns[sid]
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
    }


def _collect_verdict_records(
    roots: Sequence[Path],
    session_max_turns: dict[str, bool],
) -> tuple[list[dict[str, Any]], int, dict[str, int]]:
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
            tel_meta = _extract_telemetry_metrics(verdict.telemetry, session_max_turns)
            verdicts[verdict.request_id] = {
                "request_id": verdict.request_id,
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
    for rid, rec in verdicts.items():
        env = prompts.get(rid)
        resume_id = getattr(env, "resume_session_id", None) if env is not None else None
        rec["resume_id"] = resume_id
        rec["is_pass2_plus"] = bool(resume_id and resume_id != "new")
    prompt_only = sum(1 for rid in prompts if rid not in verdicts)
    return list(verdicts.values()), prompt_only, triage_counts


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


def evaluate_peer_effectiveness(
    roots: Sequence[Path],
    *,
    cutoff: str = _DEFAULT_CUTOFF,
    window_days: int = 14,
    sessions_dir: Path | None = None,
    use_git: bool = True,
) -> dict[str, Any]:
    """Evaluate Pre-v2.6 vs Post-v2.6 peer collaboration KPIs and escaped defects."""
    cutoff_utc = parse_utc_timestamp(cutoff)
    if cutoff_utc is None:
        raise ValueError(f"Invalid timezone-aware ISO cutoff timestamp: {cutoff!r}")
    sess_map = _index_session_max_turns(sessions_dir)
    verdicts, prompt_only_cnt, triage_counts = _collect_verdict_records(roots, sess_map)
    pre_recs: list[dict[str, Any]] = []
    post_recs: list[dict[str, Any]] = []
    undated_excluded = 0
    for rec in verdicts:
        ts = rec["ts"]
        if ts is None:
            undated_excluded += 1
        elif ts >= cutoff_utc:
            post_recs.append(rec)
        else:
            pre_recs.append(rec)
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
        "undated_excluded": undated_excluded,
        "prompt_only_count": prompt_only_cnt,
        "pre_v26": _summarize_cohort(pre_recs),
        "post_v26": _summarize_cohort(post_recs),
        "triage_counts": triage_counts,
        "escaped_defects": escaped,
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render effectiveness audit report in concise GitHub Markdown."""
    pre, post, esc = report["pre_v26"], report["post_v26"], report["escaped_defects"]
    lines = [
        f"# Peer Collaboration v2.6 A/B & Escaped-Defect Audit (Cutoff `{report['cutoff_utc']}`)",
        f"- Undated verdicts excluded: `{report['undated_excluded']}` | Prompt-only files: `{report['prompt_only_count']}`",
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
    parser.add_argument("--git-window-days", type=int, default=14)
    parser.add_argument("--sessions-dir", type=Path, default=Path.home() / ".grok" / "sessions")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--no-git", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = evaluate_peer_effectiveness(
        args.roots,
        cutoff=args.cutoff,
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
