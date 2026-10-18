"""_peer_co_review.py - Multi-agent peer co-review orchestration and consensus synthesis (ADR-0065)."""

from __future__ import annotations

import os
import re
import tempfile
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import yaml

from ._peer_models import (
    CombinedTelemetry,
    PeerCondition,
    PeerConsensusReport,
    PeerPromptEnvelope,
    PeerVerdictBlock,
    PeerVerdictTelemetry,
    ProfileTelemetryItem,
    extract_frontmatter,
    parse_envelope_from_md,
    parse_verdict_from_md,
    render_prompt_header,
)
from ._peer_watchdog import PROFILE_SPECS, VERDICT_LATTICE_RANK, VerdictType


def _merge_profile_conditions(
    comp_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
) -> list[PeerCondition]:
    """Deduplicates and OR-merges blocking conditions across completed profiles."""
    consolidated: list[PeerCondition] = []
    seen_descs: dict[str, PeerCondition] = {}
    for prof in comp_profiles:
        for cond in verdicts[prof].conditions:
            key = cond.description.strip().lower()
            if key in seen_descs:
                seen_descs[key].blocking = seen_descs[key].blocking or cond.blocking
                if prof not in seen_descs[key].source_profiles:
                    seen_descs[key].source_profiles.append(prof)
            else:
                new_c = PeerCondition(
                    id=cond.id,
                    description=cond.description,
                    blocking=cond.blocking,
                    source_profile=prof,
                    source_profiles=[prof],
                )
                seen_descs[key] = new_c
                consolidated.append(new_c)
    return consolidated


def _consolidate_peer_conditions(
    comp_profiles: list[str],
    failed_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
) -> list[PeerCondition]:
    """Consolidates conditions with deterministic ordering, quorum failure, and degraded-reasoning checks."""
    consolidated = _merge_profile_conditions(comp_profiles, verdicts)
    if failed_profiles:
        msg = f"Missing peer review from profiles: {', '.join(failed_profiles)}"
        consolidated.append(
            PeerCondition(
                id="COND-QUORUM-FAIL",
                description=msg,
                blocking=True,
                source_profile="orchestrator",
                source_profiles=["orchestrator"],
            )
        )
    degraded = [
        p
        for p in comp_profiles
        if isinstance(verdicts[p].telemetry, PeerVerdictTelemetry)
        and verdicts[p].telemetry.degraded_reasoning  # type: ignore[union-attr]
    ]
    if degraded:
        msg = f"High/xhigh reasoning profile returned 0 reasoning_tokens (silent reasoning degradation in: {', '.join(degraded)})."
        consolidated.append(
            PeerCondition(
                id="COND-DEGRADED-REASONING",
                description=msg,
                blocking=True,
                source_profile="telemetry",
                source_profiles=degraded,
            )
        )
    return consolidated


def _to_profile_telemetry_item(tel: PeerVerdictTelemetry) -> ProfileTelemetryItem:
    """Converts a single PeerVerdictTelemetry into a ProfileTelemetryItem."""
    return ProfileTelemetryItem(
        model=tel.primary_model,
        input_tokens=tel.input_tokens or 0,
        output_tokens=tel.output_tokens or 0,
        reasoning_tokens=tel.reasoning_tokens or 0,
        cached_read_tokens=tel.cached_read_tokens or 0,
        total_tokens=tel.total_tokens or 0,
        cost_usd=round(tel.cost_usd or 0.0, 4),
        duration_seconds=round(tel.duration_seconds or 0.0, 2),
    )


def _consolidate_peer_telemetry(
    comp_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
    duration_seconds: float,
) -> CombinedTelemetry | None:
    """Consolidates profile telemetry into CombinedTelemetry without failing consensus synthesis."""
    try:
        agg = {"total": 0, "inp": 0, "out": 0, "rsn": 0, "cached": 0}
        cost_usd, sum_secs, all_exact, has_any = 0.0, 0.0, True, False
        breakdown: dict[str, ProfileTelemetryItem] = {}
        for prof in comp_profiles:
            tel = verdicts[prof].telemetry
            if isinstance(tel, PeerVerdictTelemetry):
                has_any = True
                agg["total"] += tel.total_tokens or 0
                agg["inp"] += tel.input_tokens or 0
                agg["out"] += tel.output_tokens or 0
                agg["rsn"] += tel.reasoning_tokens or 0
                agg["cached"] += tel.cached_read_tokens or 0
                cost_usd += tel.cost_usd or 0.0
                sum_secs += tel.duration_seconds or 0.0
                all_exact = all_exact and (tel.cost_mode == "exact")
                breakdown[prof] = _to_profile_telemetry_item(tel)
            else:
                all_exact = False
        if not has_any:
            return None
        return CombinedTelemetry(
            total_tokens=agg["total"],
            input_tokens=agg["inp"],
            output_tokens=agg["out"],
            reasoning_tokens=agg["rsn"],
            cached_read_tokens=agg["cached"],
            cost_usd=round(cost_usd, 4),
            wall_seconds=round(duration_seconds, 2),
            sum_agent_seconds=round(sum_secs, 2),
            cost_mode="exact" if all_exact else "estimated",
            profile_breakdown=breakdown,
        )
    except Exception:
        return None


def _resolve_baseline_consensus_verdict(
    comp_profiles: list[str],
    failed_profiles: list[str],
    verdicts: dict[str, PeerVerdictBlock],
) -> VerdictType:
    """Computes baseline consensus verdict using strict lattice rank and quorum rules."""
    completed_verdicts = [verdicts[p].verdict for p in comp_profiles]
    if not completed_verdicts:
        return "HANDOFF"
    completed_max = max(completed_verdicts, key=lambda t: VERDICT_LATTICE_RANK.get(t, 0))
    handoff_rank = VERDICT_LATTICE_RANK.get("HANDOFF", 70)
    if failed_profiles and VERDICT_LATTICE_RANK.get(completed_max, 0) < handoff_rank:
        return "HANDOFF"
    return completed_max


def synthesize_verdicts(
    request_id: str,
    verdicts: dict[str, PeerVerdictBlock],
    expected_profiles: Sequence[str] | None = None,
    duration_seconds: float = 0.0,
) -> PeerConsensusReport:
    """Synthesizes multiple peer verdicts into a unified deterministic consensus report (ADR-0065)."""
    if not verdicts and not expected_profiles:
        raise ValueError(
            "Cannot synthesize consensus from empty verdicts and empty expected profiles."
        )
    exp = list(expected_profiles) if expected_profiles is not None else list(verdicts.keys())
    comp = [p for p in exp if p in verdicts]
    failed = [p for p in exp if p not in verdicts]
    pass_set = {"APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS", "APPROVE_WITH_RESERVATIONS"}

    c_verdict = _resolve_baseline_consensus_verdict(comp, failed, verdicts)
    conds = _consolidate_peer_conditions(comp, failed, verdicts)
    valid_risks = [r for p in comp if (r := verdicts[p].risk_score) is not None]
    c_risk = max(valid_risks) if valid_risks else 1
    if c_verdict in pass_set and (any(c.blocking for c in conds) or c_risk >= 4):
        c_verdict = "APPROVE_WITH_CONDITIONS"

    lines = [
        f"Consensus Verdict: **{c_verdict}** (Risk Score: {c_risk}/5).",
        f"Quorum: {len(comp)}/{len(exp)} completed.",
    ]
    if failed:
        lines.append(f"Failed Profiles: {', '.join(failed)}.")
    lines.extend(f"- **{p}** ({verdicts[p].verdict}): {verdicts[p].summary}" for p in comp)
    return PeerConsensusReport(
        request_id=request_id,
        verdict=c_verdict,
        risk_score=c_risk,
        summary="\n".join(lines),
        expected_profiles=exp,
        completed_profiles=comp,
        failed_profiles=failed,
        individual_verdicts=verdicts,
        conditions=conds,
        combined_telemetry=_consolidate_peer_telemetry(comp, verdicts, duration_seconds),
    )


def render_consensus_report_markdown(report: PeerConsensusReport) -> str:
    """Renders a complete markdown document for a consensus report with standard frontmatter."""
    fm_payload: dict[str, Any] = {
        "request_id": report.request_id,
        "verdict": report.verdict,
        "risk_score": report.risk_score,
        "summary": report.summary,
        "profiles": report.completed_profiles,
        "expected_profiles": report.expected_profiles,
        "failed_profiles": report.failed_profiles,
        "conditions": [c.model_dump(exclude_none=True) for c in report.conditions],
    }
    if report.combined_telemetry:
        fm_payload["telemetry"] = report.combined_telemetry.model_dump(exclude_none=True)
    header = f"---\n{yaml.dump(fm_payload, sort_keys=False, allow_unicode=True)}---\n"

    body = [
        f"# 🤝 Multi-Agent Peer Consensus Report: `{report.request_id}`\n",
        f"- **Consensus Verdict**: `{report.verdict}`",
        f"- **Consolidated Risk Score**: `{report.risk_score}/5`",
        f"- **Quorum**: `{len(report.completed_profiles)}/{len(report.expected_profiles)}` profiles completed\n",
        "## 1. Executive Summary\n",
        report.summary,
        "\n## 2. Consolidated Conditions\n",
    ]
    for c in report.conditions or []:
        tag = "🔴 [BLOCKING]" if c.blocking else "🟡 [ADVISORY]"
        srcs = (
            ", ".join(c.source_profiles) if c.source_profiles else (c.source_profile or "unknown")
        )
        body.append(f"- **{c.id}** {tag} ({srcs}): {c.description}")
    if not report.conditions:
        body.append("*(No conditions attached)*")
    body.append("\n## 3. Individual Profile Verdicts\n")
    for prof, vb in report.individual_verdicts.items():
        body.append(
            f"### Profile: `{prof}`\n- **Verdict**: `{vb.verdict}` (Risk: `{vb.risk_score or 'N/A'}`)\n- **Summary**: {vb.summary}\n"
        )
    if report.combined_telemetry:
        t = report.combined_telemetry
        body.append(
            f"## 4. Telemetry & Cost Provenance\n\n- **Total Tokens**: {t.total_tokens:,} (Input: {t.input_tokens:,}, Output: {t.output_tokens:,}, Reasoning: {t.reasoning_tokens:,})\n- **Total Cost**: ${t.cost_usd:.4f} (mode: `{t.cost_mode}`)\n- **Duration**: Wall clock `{t.wall_seconds}s` | Sum agent time `{t.sum_agent_seconds}s`\n"
        )
    return header + "\n".join(body) + "\n"


def _run_co_review_workers(
    tasks: list[tuple[str, Path, Path]],
    max_workers: int,
    timeout: float | None,
    worktree: bool,
) -> dict[str, PeerVerdictBlock]:
    """Dispatches co-review profile tasks in parallel via ThreadPoolExecutor."""
    from . import peer as _peer_mod

    def _worker(item: tuple[str, Path, Path]) -> tuple[str, PeerVerdictBlock | None]:
        p_name, p_prompt, p_out = item
        spec = PROFILE_SPECS.get(p_name, {})
        ok = _peer_mod.invoke_grok_cli(
            prompt_path=p_prompt,
            model=spec.get("model"),
            profile=p_name,
            timeout=timeout if timeout is not None else spec.get("timeout"),
            worktree=worktree,
        )
        if not ok or not p_out.exists():
            return p_name, None
        out_str, _ = _peer_mod.safe_read_and_hash(p_out)
        return p_name, parse_verdict_from_md(out_str or "")

    verdicts: dict[str, PeerVerdictBlock] = {}
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
        for fut in [pool.submit(_worker, t) for t in tasks]:
            try:
                p_name, vb = fut.result()
                if vb is not None:
                    verdicts[p_name] = vb
            except Exception:
                pass
    return verdicts


def _prepare_co_review_tasks(
    profiles: Sequence[str],
    envelope: PeerPromptEnvelope,
    content: str,
    temp_dir: Path,
) -> list[tuple[str, Path, Path]]:
    """Writes isolated per-profile prompt files inside temp_dir and returns worker task tuples."""
    from . import peer as _peer_mod

    tasks: list[tuple[str, Path, Path]] = []
    _, body = extract_frontmatter(content)
    for prof in profiles:
        prof_prompt = temp_dir / f"prompt_{prof}.md"
        prof_out_name = f"grok_{prof}.md"
        prof_env = envelope.model_copy()
        prof_env.profile = prof  # type: ignore[assignment]
        prof_env.output_path = prof_out_name
        _peer_mod.atomic_write_text(prof_prompt, render_prompt_header(prof_env) + body.lstrip())
        tasks.append((prof, prof_prompt, temp_dir / prof_out_name))
    return tasks


def orchestrate_peer_co_review(
    prompt_path: Path,
    profiles: Sequence[str] = ("code_review", "arch_audit"),
    output_file: Path | None = None,
    max_workers: int | None = None,
    timeout: float | None = None,
    worktree: bool = False,
) -> PeerConsensusReport | None:
    """Orchestrates multi-agent co-review execution in parallel threads with isolated outputs (ADR-0065)."""
    from . import peer as _peer_mod

    for prof in profiles:
        if not re.match(r"^[a-z0-9_]{1,32}$", prof):
            raise ValueError(f"Invalid profile name '{prof}': must match ^[a-z0-9_]{{1,32}}$")
        if prof not in PROFILE_SPECS:
            raise ValueError(
                f"Unknown execution profile '{prof}': must be one of {sorted(PROFILE_SPECS.keys())}"
            )

    content, _ = _peer_mod.safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(content or "")
    if not envelope:
        return None

    temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"peer_co_review_{envelope.request_id[:8]}_")
    temp_dir = Path(temp_dir_obj.name)
    try:
        try:
            os.chmod(temp_dir, 0o700)
        except Exception:
            pass
        start_time = time.time()
        tasks = _prepare_co_review_tasks(profiles, envelope, content or "", temp_dir)
        workers_count = max_workers if max_workers is not None else min(len(profiles), 4)
        verdicts = _run_co_review_workers(tasks, workers_count, timeout, worktree)
        report = synthesize_verdicts(
            request_id=envelope.request_id,
            verdicts=verdicts,
            expected_profiles=profiles,
            duration_seconds=time.time() - start_time,
        )
        final_out = output_file or (
            prompt_path.parent / f"grok_consensus_{prompt_path.stem.replace('prompt_', '')}.md"
        )
        _peer_mod.atomic_write_text(final_out, render_consensus_report_markdown(report))
        return report
    finally:
        temp_dir_obj.cleanup()
