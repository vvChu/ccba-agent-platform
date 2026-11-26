#!/usr/bin/env python3
"""Pre/Post UTC skill effectiveness A/B auditor & Top-10 routing/coverage drift guard."""

from __future__ import annotations

import argparse
import datetime
import json
import re
import statistics
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "packages/ccba-harness/src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ccba_harness.evals.archetypes import resolve_domain_dataset_contract  # noqa: E402
from ccba_harness.evals.miner import (  # noqa: E402
    DEFAULT_INVOCATION_LEDGER_PATH,
    load_catalog,
    load_invocation_events,
)
from scripts.governance.audit_peer_effectiveness import (  # noqa: E402
    _has_regression_test_or_guard,
    _parse_git_commits,
    parse_utc_timestamp,
)

DEFAULT_PR909_CUTOFF_UTC = "2026-11-25T14:32:25Z"
_SLASH_NAME_RE = re.compile(r"/(ccba-[a-z0-9-]+|bigbim-[a-z0-9-]+)", re.IGNORECASE)
_DatedEvent = tuple[datetime.datetime, dict[str, Any]]


def _slug(val: Any) -> str:
    """Normalize a skill/command string to a lowercase slug without leading slash."""
    return str(val or "").strip().lower().lstrip("/")


def _index_events(
    events: Sequence[dict[str, Any]],
) -> tuple[dict[str, list[_DatedEvent]], list[_DatedEvent], int]:
    """Attach UTC timestamps, index turns per conversation, and build chronological stream."""
    by_conv: dict[str, list[_DatedEvent]] = {}
    dated: list[_DatedEvent] = []
    undated = 0
    for ev in events:
        if (ts := parse_utc_timestamp(ev.get("created_at"))) is None:
            undated += 1
            continue
        dated.append((ts, ev))
        by_conv.setdefault(str(ev.get("conversation_id", "")), []).append((ts, ev))
    dated.sort(
        key=lambda x: (x[0], str(x[1].get("conversation_id", "")), int(x[1].get("turn_index", 0)))
    )
    for rows in by_conv.values():
        rows.sort(key=lambda x: (int(x[1].get("turn_index", 0)), x[0]))
    return by_conv, dated, undated


def _has_cross_follow(
    ts: datetime.datetime,
    ev: dict[str, Any],
    recs: set[str],
    dated: Sequence[_DatedEvent],
    win_s: float,
) -> bool:
    """Return True when another session invokes a recommended skill within win_s."""
    cid, ws = str(ev.get("conversation_id", "")), str(ev.get("workspace_hash", "") or "")
    for o_ts, o_ev in dated:
        delta = (o_ts - ts).total_seconds()
        if delta <= 0:
            continue
        if delta > win_s:
            break
        o_ws = str(o_ev.get("workspace_hash", "") or "")
        if str(o_ev.get("conversation_id", "")) != cid and (not ws or not o_ws or o_ws == ws):
            if _slug(o_ev.get("invoked_skill")) in recs:
                return True
    return False


def _score_heuristics(
    rows: Sequence[_DatedEvent],
    by_conv: dict[str, list[_DatedEvent]],
    dated: Sequence[_DatedEvent],
    win_h: float,
) -> dict[str, Any]:
    """Compute <= win_h same-session and cross-session adoption heuristics."""
    nxt = conf = cross = eff = 0
    win_s = max(0.0, win_h * 3600.0)
    for ts, ev in rows:
        cid, tidx = str(ev.get("conversation_id", "")), int(ev.get("turn_index", 0) or 0)
        recs = {_slug(c) for c in (ev.get("recommended_commands") or []) if c}
        n_ev = next(
            (r for _, r in by_conv.get(cid, []) if int(r.get("turn_index", 0) or 0) > tidx), None
        )
        ok = False
        if n_ev is not None:
            if _slug(n_ev.get("invoked_skill")) in recs:
                nxt, ok = nxt + 1, True
            elif bool(n_ev.get("is_short_confirmation", False)):
                conf, ok = conf + 1, True
        if not ok and recs and _has_cross_follow(ts, ev, recs, dated, win_s):
            cross, ok = cross + 1, True
        eff += int(ok)
    n = len(rows)
    return {
        "next_turn_adoption": nxt,
        "choice_confirmation": conf,
        "cross_session_follow_through": cross,
        "effective_turns": eff,
        "effective_rate": round(eff / n, 4) if n else 0.0,
        "window_hours": win_h,
        "attribution_note": f"Heuristic <= {win_h:g}h lacks causal attribution; rely on confirmed probes.",
    }


def _summarize_cohort(
    rows: Sequence[_DatedEvent],
    by_conv: dict[str, list[_DatedEvent]],
    dated: Sequence[_DatedEvent],
    win_h: float,
) -> dict[str, Any]:
    """Summarize confirmed Zero-LLM probe metrics alongside candidate adoption heuristics."""
    steps = [int(ev.get("planner_steps", 0) or 0) for _, ev in rows]
    probes = Counter(p for _, ev in rows for p in (ev.get("probe_violations") or []))
    confirmed = {
        "invocations": len(rows),
        "conversations": len({str(ev.get("conversation_id", "")) for _, ev in rows}),
        "bare_invocations": sum(int(ev.get("prompt_char_len", 0) or 0) < 10 for _, ev in rows),
        "side_effect_violations": probes["SIDE_EFFECT_VIOLATION"],
        "routing_drift_violations": probes["ROUTING_CONTRACT_DRIFT"],
        "unexpected_tool_errors": probes["UNEXPECTED_TOOL_ERROR"],
        "median_planner_steps": round(float(statistics.median(steps)), 2) if steps else 0.0,
    }
    return {
        "confirmed": confirmed,
        "candidate_heuristic": _score_heuristics(rows, by_conv, dated, win_h),
    }


def _audit_guards(
    root: Path, skill: str, cutoff_utc: datetime.datetime, use_git: bool
) -> dict[str, int]:
    """Check whether git commits touching `.agents/skills/<skill>/` include regression guards."""
    keys = (
        "total_skill_commits",
        "post_cutoff_commits",
        "post_with_regression_guard",
        "post_missing_regression_guard",
    )
    if not use_git or not root.is_dir():
        return dict.fromkeys(keys, 0)
    pfx = f".agents/skills/{skill}/"
    matched = [
        c
        for c in _parse_git_commits(root)
        if any(f.replace("\\", "/").startswith(pfx) for f in c["files"])
    ]
    post = [c for c in matched if c["ts"] >= cutoff_utc]
    guarded = sum(1 for c in post if _has_regression_test_or_guard(c["files"]))
    return dict(zip(keys, (len(matched), len(post), guarded, len(post) - guarded), strict=True))


def _top_skills(
    dated: Sequence[_DatedEvent], days: int, top_n: int
) -> tuple[list[tuple[str, int]], dict[str, set[str]]]:
    """Rank Top-N CCBA/BIGBIM skills deterministically within trailing days."""
    anchor = dated[-1][0] if dated else datetime.datetime.now(datetime.timezone.utc)
    since = anchor - datetime.timedelta(days=days)
    counts: Counter[str] = Counter()
    convs: dict[str, set[str]] = {}
    for ts, ev in dated:
        sk = _slug(ev.get("invoked_skill"))
        if ts >= since and sk.startswith(("ccba-", "bigbim-")):
            counts[sk] += 1
            convs.setdefault(sk, set()).add(str(ev.get("conversation_id", "")))
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:top_n], convs


def audit_routing_and_coverage_drift(
    events: Sequence[dict[str, Any]],
    repo_root: Path,
    *,
    window_days: int = 30,
    top_n: int = 10,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    """Flag Top-N skills missing from the `ccba-ask` router map or UNCONFIGURED in evals."""
    _, dated, _ = _index_events(events)
    ranked, convs = _top_skills(dated, window_days, top_n)
    ask_p = repo_root / ".agents/skills/ccba-ask/SKILL.md"
    ask_txt = ask_p.read_text(encoding="utf-8", errors="replace") if ask_p.is_file() else ""
    ask_sk = {_slug(m.group(1)) for m in _SLASH_NAME_RE.finditer(ask_txt)}
    cat_sk = {_slug(s.get("name")) for s in load_catalog(catalog_path)}
    tc_dir = repo_root / ".agents/skills/ccba-eval-gate/test_cases"
    rows, miss_r, unconf = [], [], []
    for sk, inv in ranked:
        in_r = sk in ask_sk or sk == "ccba-ask"
        ct = resolve_domain_dataset_contract(sk, tc_dir if tc_dir.is_dir() else None)
        if not in_r:
            miss_r.append(sk)
        if ct.status != "CONFIGURED":
            unconf.append(sk)
        rows.append(
            {
                "skill": sk,
                "invocations": inv,
                "conversations": len(convs.get(sk, set())),
                "in_ask_router": in_r,
                "in_catalog": sk in cat_sk,
                "dataset_status": ct.status,
                "dataset_tier": ct.tier,
            }
        )
    return {
        "window_days": window_days,
        "top_n": top_n,
        "top_skills": rows,
        "missing_from_router": miss_r,
        "unconfigured_evals": unconf,
        "drift_detected": bool(miss_r or unconf),
    }


def evaluate_skill_effectiveness(
    events: Sequence[dict[str, Any]],
    *,
    skill: str = "ccba-ask",
    cutoff: str = DEFAULT_PR909_CUTOFF_UTC,
    follow_window_hours: float = 2.0,
    repo_root: Path | None = None,
    use_git: bool = True,
    include_drift_check: bool = False,
    drift_days: int = 30,
    top_n: int = 10,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run Pre/Post UTC cohort A/B audit, git regression guard check, and optional drift guard."""
    if (cutoff_utc := parse_utc_timestamp(cutoff)) is None:
        raise ValueError(f"Invalid timezone-aware ISO cutoff timestamp: {cutoff!r}")
    target, root = _slug(skill), repo_root or _REPO_ROOT
    by_conv, dated, undated = _index_events(events)
    sk_rows = [(t, e) for t, e in dated if _slug(e.get("invoked_skill")) == target]
    pre = [(t, e) for t, e in sk_rows if t < cutoff_utc]
    post = [(t, e) for t, e in sk_rows if t >= cutoff_utc]
    report: dict[str, Any] = {
        "skill": target,
        "cutoff_utc": cutoff_utc.isoformat(),
        "total_events_scanned": len(events),
        "undated_excluded": undated,
        "pre": _summarize_cohort(pre, by_conv, dated, follow_window_hours),
        "post": _summarize_cohort(post, by_conv, dated, follow_window_hours),
        "regression_guards": _audit_guards(root, target, cutoff_utc, use_git),
    }
    if include_drift_check:
        report["drift_check"] = audit_routing_and_coverage_drift(
            events, root, window_days=drift_days, top_n=top_n, catalog_path=catalog_path
        )
    return report


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render concise GitHub Markdown summary for Pre/Post skill effectiveness & drift guard."""
    pc, qc = report["pre"]["confirmed"], report["post"]["confirmed"]
    ph, qh = report["pre"]["candidate_heuristic"], report["post"]["candidate_heuristic"]
    rg = report["regression_guards"]
    lines = [
        f"# Skill Effectiveness Pre/Post A/B Audit: `{report['skill']}` (Cutoff `{report['cutoff_utc']}`)",
        f"- Events scanned: `{report['total_events_scanned']}` | Undated excluded: `{report['undated_excluded']}`",
        "",
        "| KPI (Tier) | Pre-Cutoff | Post-Cutoff |",
        "| :--- | ---: | ---: |",
        f"| Invocations / Conversations (`confirmed`) | {pc['invocations']} / {pc['conversations']} | {qc['invocations']} / {qc['conversations']} |",
        f"| Bare Invocations <10 chars (`confirmed`) | {pc['bare_invocations']} | {qc['bare_invocations']} |",
        f"| Side-Effect Violations (`confirmed`) | {pc['side_effect_violations']} | {qc['side_effect_violations']} |",
        f"| Routing Contract Drift (`confirmed`) | {pc['routing_drift_violations']} | {qc['routing_drift_violations']} |",
        f"| Unexpected Tool Errors (`confirmed`) | {pc['unexpected_tool_errors']} | {qc['unexpected_tool_errors']} |",
        f"| Median Planner Steps (`confirmed`) | {pc['median_planner_steps']} | {qc['median_planner_steps']} |",
        f"| Candidate Effective Rate <= {ph['window_hours']:g}h (`heuristic`) | {ph['effective_rate']:.1%} ({ph['effective_turns']}/{pc['invocations']}) | {qh['effective_rate']:.1%} ({qh['effective_turns']}/{qc['invocations']}) |",
        "",
        f"- **Git Regression Guards (Post-Cutoff):** `{rg['post_with_regression_guard']}/{rg['post_cutoff_commits']}` with guard (`{rg['post_missing_regression_guard']}` missing).",
        f"- *Attribution Note:* {ph['attribution_note']}",
    ]
    if isinstance(drift := report.get("drift_check"), dict):
        lines += [
            "",
            f"## Top-{drift['top_n']} Routing & Eval Coverage Drift ({drift['window_days']}d)",
            "",
            "| Skill | Invocations | In `ccba-ask` | Eval Contract | Tier |",
            "| :--- | ---: | :---: | :---: | :---: |",
            *(
                f"| `{r['skill']}` | {r['invocations']} | {'YES' if r['in_ask_router'] else 'MISSING'} | {r['dataset_status']} | {r['dataset_tier']} |"
                for r in drift["top_skills"]
            ),
        ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for Pre/Post skill effectiveness & Top-10 routing drift audit."""
    p = argparse.ArgumentParser(description="Pre/Post UTC skill effectiveness & drift auditor.")
    p.add_argument("--skill", default="ccba-ask")
    p.add_argument("--cutoff", default=DEFAULT_PR909_CUTOFF_UTC)
    p.add_argument("--ledger", type=Path, default=DEFAULT_INVOCATION_LEDGER_PATH)
    p.add_argument("--transcript-dir", type=Path, default=None)
    p.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    p.add_argument("--follow-window-hours", type=float, default=2.0)
    p.add_argument("--drift-check", action="store_true")
    p.add_argument("--drift-days", type=int, default=30)
    p.add_argument("--top-n", type=int, default=10)
    p.add_argument("--no-git", action="store_true")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    a = p.parse_args(list(argv) if argv is not None else None)
    ev = load_invocation_events(ledger_path=a.ledger, transcript_dir=a.transcript_dir)
    rep = evaluate_skill_effectiveness(
        ev,
        skill=a.skill,
        cutoff=a.cutoff,
        follow_window_hours=a.follow_window_hours,
        repo_root=a.repo_root,
        use_git=not a.no_git,
        include_drift_check=a.drift_check,
        drift_days=a.drift_days,
        top_n=a.top_n,
    )
    print(
        json.dumps(rep, indent=2, ensure_ascii=False)
        if a.format == "json"
        else render_markdown_report(rep)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
