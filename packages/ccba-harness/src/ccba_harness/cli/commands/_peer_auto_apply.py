"""_peer_auto_apply.py - Auto-apply helpers for peer dispatch and co-review (ADR-0065)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


# ccba:quarantine seam_id=cli.peer_dispatch_auto_apply reason=thin_shell_refactor until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/494
def handle_peer_dispatch_auto_apply(
    prompt_path: Path,
    root: str | None,
    verify_preset: str | None,
    keep_backups: bool,
    active_profile: str | None,
) -> int:
    """Handles Level-3 auto-apply verification gate for peer-dispatch (ADR-0065)."""
    from ccba_harness.peer import (
        auto_apply_and_verify_patch,
        extract_anchor_payload,
        parse_envelope_from_md,
        parse_verdict_from_md,
        safe_read_and_hash,
    )

    content, _ = safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(content or "")
    profile = active_profile or (envelope.profile if envelope else None)

    if profile != "patch_fast":
        print(
            f"[FAIL] --auto-apply is strictly restricted to 'patch_fast' profile, got '{profile}' (COND-LEVEL3-TRUST).",
            file=sys.stderr,
        )
        return 1

    out_name = Path(envelope.output_path).name if (envelope and envelope.output_path) else None
    if not out_name:
        print(
            "[FAIL] --auto-apply requested but envelope does not specify output_path.",
            file=sys.stderr,
        )
        return 1

    output_path = (prompt_path.parent / out_name).resolve()
    if not output_path.exists():
        print(f"[FAIL] Output file not found for auto-apply: {output_path}", file=sys.stderr)
        return 1

    out_content, _ = safe_read_and_hash(output_path)
    out_verdict_block = parse_verdict_from_md(out_content or "")
    worker_verdict = out_verdict_block.verdict if out_verdict_block else None

    if worker_verdict != "HANDOFF":
        print(
            f"[FAIL] --auto-apply rejected worker verdict '{worker_verdict}': only HANDOFF is accepted (COND-LEVEL3-TRUST).",
            file=sys.stderr,
        )
        return 1

    payload = extract_anchor_payload(out_content or "")
    if payload is None:
        print(
            "[FAIL] --auto-apply requested but output contains no AnchorPatchPayload.",
            file=sys.stderr,
        )
        return 1

    auto_res = auto_apply_and_verify_patch(
        root=root,
        patch_payload=payload,
        verify_preset=verify_preset or "ci",
        keep_backups=keep_backups,
    )

    return record_auto_apply_gate_result(
        gate_file=output_path.with_suffix(".gate.md"),
        auto_res=auto_res,
        preset=verify_preset or "ci",
        title="Level-3 Orchestrator Gate Result",
    )


def record_auto_apply_gate_result(
    gate_file: Path,
    auto_res: Any,
    preset: str,
    title: str,
) -> int:
    """Writes gate result markdown and outputs formatted CLI status message."""
    from ccba_harness.peer import atomic_write_text

    gate_body = (
        f"---\n"
        f"gate_verdict: {auto_res.gate_verdict}\n"
        f"success: {str(auto_res.success).lower()}\n"
        f"rollback_proven: {str(auto_res.rollback_proven).lower()}\n"
        f"preset: {preset}\n"
        f"transaction_id: {auto_res.transaction_id}\n"
        f"---\n\n"
        f"# 🛡️ {title}\n\n"
        f"- **Verdict:** `{auto_res.gate_verdict}`\n"
        f"- **Success:** `{auto_res.success}`\n"
        f"- **Rollback Proven:** `{auto_res.rollback_proven}`\n"
        f"- **Summary:** {auto_res.summary}\n"
    )
    atomic_write_text(gate_file, gate_body)

    if auto_res.success:
        print(f"[OK] {title} passed: {auto_res.summary}")
        return 0
    if auto_res.rollback_proven:
        print(
            f"[GATE_FAIL] {title} verification failed and workspace rolled back cleanly: {auto_res.summary}",
            file=sys.stderr,
        )
        return 4
    print(
        f"[ERROR] {title} rollback verification mismatch or failure: {auto_res.summary}",
        file=sys.stderr,
    )
    return 1


# ccba:quarantine seam_id=cli.peer_co_review_auto_apply reason=thin_shell_refactor until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/494
def handle_peer_co_review_auto_apply(
    prompt_path: Path,
    output_path: Path | None,
    report: Any,
    patch_file: str | None,
    root: str | None,
    verify_preset: str | None,
    keep_backups: bool,
) -> int:
    """Handles Level-3 auto-apply verification gate for peer-co-review (ADR-0065)."""
    from ccba_harness.peer import (
        auto_apply_and_verify_patch,
        extract_anchor_payload,
        safe_read_and_hash,
    )

    if not patch_file:
        print(
            "[FAIL] --auto-apply on co-review requires an explicit --patch-file (COND-LEVEL3-TRUST).",
            file=sys.stderr,
        )
        return 1

    blocking_conditions = [c for c in report.conditions if c.blocking]
    is_clean_approval = (
        report.verdict in ("APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT")
        and report.risk_score <= 3
        and len(blocking_conditions) == 0
    )

    if not is_clean_approval:
        print(
            f"[FAIL] Consensus conditions not met for --auto-apply (verdict: {report.verdict}, "
            f"risk: {report.risk_score}/5, blocking conditions: {len(blocking_conditions)}) (COND-LEVEL3-TRUST).",
            file=sys.stderr,
        )
        return 2 if report.verdict.startswith("APPROVE") else 4

    patch_path = Path(patch_file).resolve()
    if not patch_path.exists():
        print(f"[FAIL] Specified patch file not found: {patch_path}", file=sys.stderr)
        return 1

    patch_content, _ = safe_read_and_hash(patch_path)
    payload = extract_anchor_payload(patch_content or "")
    if payload is None:
        print(
            f"[FAIL] No valid AnchorPatchPayload found in patch file: {patch_path}",
            file=sys.stderr,
        )
        return 1

    auto_res = auto_apply_and_verify_patch(
        root=root,
        patch_payload=payload,
        verify_preset=verify_preset or "ci",
        keep_backups=keep_backups,
    )

    gate_target = (
        output_path
        if output_path
        else prompt_path.parent / f"grok_consensus_{prompt_path.stem.replace('prompt_', '')}.md"
    )
    return record_auto_apply_gate_result(
        gate_file=gate_target.with_suffix(".gate.md"),
        auto_res=auto_res,
        preset=verify_preset or "ci",
        title="Level-3 Consensus Orchestrator Gate Result",
    )
