"""commands/peer.py - CLI handlers for Level-2 peer agent collaboration, co-review, watch, and anchor patch (ADR-0063 / ADR-0065)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def find_workspace_root(start_dir: Path | None = None) -> Path:
    """Finds workspace root by walking upwards looking for .git, workspace_context.yaml, or AGENTS.md."""
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (
            (parent / ".git").exists()
            or (parent / "workspace_context.yaml").exists()
            or (parent / ".md" / "workspace_context.yaml").exists()
            or (parent / "AGENTS.md").exists()
        ):
            return parent
    return current


def resolve_peer_exchange_dir(
    dir_arg: str | None = None,
    root_arg: str | None = None,
) -> Path:
    """Resolves target peer_exchange directory with upward discovery (ADR-0007 / ADR-0061)."""
    if dir_arg:
        target = Path(dir_arg).resolve()
        target.mkdir(parents=True, exist_ok=True)
        return target
    root = Path(root_arg).resolve() if root_arg else find_workspace_root()
    target = root / ".md" / "peer_exchange"
    target.mkdir(parents=True, exist_ok=True)
    return target


def run_peer_gate_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for automated 6-stage implementation gate (`ccba-harness peer-gate`)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness peer-gate",
        description="Automated 6-stage post-implementation gate verification (ADR-0007 / ADR-0009).",
    )
    parser.add_argument(
        "--branch", type=str, default=None, help="Target git branch to diff against"
    )
    parser.add_argument(
        "--file", action="append", default=None, help="Specific files to gate-check"
    )
    parser.add_argument("--root", type=str, default=None, help="Project workspace root directory")
    parser.add_argument(
        "--output-verdict",
        action="store_true",
        help="Write YAML frontmatter verdict to .md/peer_exchange/",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output full gate result in JSON format"
    )

    args = parser.parse_args(args_list)
    root_p = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    from ccba_harness.peer_gate import print_summary_table, run_full_gate, write_verdict_file

    result = run_full_gate(workspace_dir=root_p, branch=args.branch, changed_files=args.file)

    if args.output_verdict:
        peer_dir = root_p / ".md" / "peer_exchange"
        out_file = write_verdict_file(result, peer_dir)
        print(f"Saved gate verdict to: {out_file.name}")

    if args.json:
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    else:
        print_summary_table(result)

    return 0 if result.gate == "PASS" else 1


def run_peer_watch_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for peer exchange watcher (`ccba-harness peer-watch`)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness peer-watch",
        description="Peer Agent Bridge Watcher and delta synchronizer (ADR-0007 / ADR-0009 / Issue #467).",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run a single delta sync cycle and exit (default)."
    )
    parser.add_argument(
        "-w", "--watch", action="store_true", help="Run continuous polling watch loop."
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=5, help="Polling interval in seconds (default: 5)."
    )
    parser.add_argument(
        "--auto-gate", action="store_true", help="Trigger peer implementation gate on new code."
    )
    parser.add_argument(
        "--auto-grok", action="store_true", help="Automatically invoke Grok CLI on new prompts."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Target peer exchange directory (default: ./.md/peer_exchange/).",
    )
    parser.add_argument("--root", type=str, default=None, help="Project workspace root directory.")

    args = parser.parse_args(args_list)
    peer_dir = resolve_peer_exchange_dir(args.dir, args.root)

    from ccba_harness.peer import flush_pending_peer_triggers, run_sync_cycle

    if args.once or not args.watch:
        changes = run_sync_cycle(peer_dir, auto_gate=args.auto_gate, auto_grok=args.auto_grok)
        for c in changes:
            print(f"[{c.role}] Detected change in: {c.path.name}")
        print(f"[OK] Bridge sync completed. Detected {len(changes)} change(s).")
        return 0

    print(
        f"🚀 Starting Peer Bridge Watcher on {peer_dir} (interval={args.interval}s)... Press Ctrl+C to stop."
    )
    try:
        while True:
            changes = run_sync_cycle(peer_dir, auto_gate=args.auto_gate, auto_grok=args.auto_grok)
            for c in changes:
                print(f"[{c.role}] Detected change in: {c.path.name}")
            time.sleep(args.interval)
    except (KeyboardInterrupt, SystemExit):
        flush_pending_peer_triggers(timeout=2.0)
        print("\n[OK] Peer watcher stopped cleanly.")
    return 0


def run_peer_dispatch_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for peer prompt dispatch (`ccba-harness peer-dispatch` - ADR-0063)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness peer-dispatch",
        description="Level-2 Peer Agent Dispatcher and budget guardrail (ADR-0063).",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        required=True,
        help="Path to markdown prompt file containing PeerPromptEnvelope.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["audit_plan", "agentic_code", "patch_fast", "code_review", "arch_audit"],
        default=None,
        help="Execution profile ('audit_plan', 'agentic_code', 'patch_fast', 'code_review', 'arch_audit').",
    )
    parser.add_argument(
        "--tier",
        type=str,
        choices=["local", "gateway", "cloud"],
        default=None,
        help="Model infrastructure tier ('local' DGX, 'gateway' Spark, 'cloud' xAI).",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        help="Explicit model slug override (e.g. qwen-local, grok-4.7).",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Hard cap on agent turns (overrides profile defaults).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Execution timeout in seconds.",
    )
    parser.add_argument(
        "--worktree",
        action="store_true",
        help="Execute agent in an isolated git worktree.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print constructed command and parameters without executing.",
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        help="Automatically apply and verify patch if output contains valid AnchorPatchPayload (Level-3 / ADR-0065).",
    )
    parser.add_argument(
        "--verify-preset",
        type=str,
        choices=["code", "doc", "skill", "adr", "telemetry", "ci", "eval"],
        default="ci",
        help="Verification preset to run upon auto-apply (default: ci).",
    )
    parser.add_argument(
        "--keep-backups",
        action="store_true",
        help="Preserve transaction backup directories under .md/backups/anchor-txn/.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root directory for workspace (default: git rev-parse --show-toplevel).",
    )

    args = parser.parse_args(args_list)
    prompt_path = Path(args.prompt_file).resolve()
    if not prompt_path.exists():
        print(f"[FAIL] Prompt file not found: {prompt_path}", file=sys.stderr)
        return 1

    from ccba_harness.peer import (
        DEFAULT_FALLBACK_AUDITOR_MODEL,
        DEFAULT_PRIMARY_AUDITOR_MODEL,
        PROFILE_SPECS,
        TIER_DEFAULT_MODELS,
        build_grok_cmd,
        invoke_grok_cli,
        parse_envelope_from_md,
        safe_read_and_hash,
    )

    if args.dry_run:
        content, _ = safe_read_and_hash(prompt_path)
        envelope = parse_envelope_from_md(content or "")
        active_profile = args.profile or (envelope.profile if envelope else None)
        spec = PROFILE_SPECS.get(
            str(active_profile),
            {
                "model": DEFAULT_PRIMARY_AUDITOR_MODEL,
                "fallback_model": DEFAULT_FALLBACK_AUDITOR_MODEL,
                "max_turns": 12,
                "tools": None,
                "disallowed_tools": ["spawn_subagent"],
                "reasoning_effort": "high",
                "timeout": 180.0,
            },
        )
        model = args.model
        if not model:
            if args.tier and str(args.tier) in TIER_DEFAULT_MODELS:
                model = TIER_DEFAULT_MODELS[str(args.tier)]
            elif os.getenv("CCBA_GROK_MODEL"):
                model = os.environ["CCBA_GROK_MODEL"]
            else:
                model = spec["model"]

        max_turns = (
            args.max_turns
            if args.max_turns is not None
            else (
                envelope.max_turns
                if envelope and envelope.max_turns is not None
                else spec.get("max_turns")
            )
        )
        cmd = build_grok_cmd(
            prompt_path=prompt_path,
            model=model,
            max_turns=max_turns,
            tools=spec.get("tools"),
            disallowed_tools=spec.get("disallowed_tools"),
            deny=spec.get("deny"),
            reasoning_effort=spec.get("reasoning_effort"),
            worktree=args.worktree,
            system_prompt=spec.get("system_prompt"),
        )
        out_name = (
            Path(envelope.output_path).name if envelope and envelope.output_path else "stdout"
        )
        print(f"[DRY-RUN] Profile: {active_profile}")
        print(f"[DRY-RUN] Model: {model}")
        print(f"[DRY-RUN] Max Turns: {max_turns}")
        print(f"[DRY-RUN] Expected Output: {prompt_path.parent / out_name}")
        print(f"[DRY-RUN] Command: {' '.join(cmd)}")
        return 0

    success = invoke_grok_cli(
        prompt_path=prompt_path,
        model=args.model,
        profile=args.profile,
        tier=args.tier,
        max_turns=args.max_turns,
        timeout=args.timeout,
        worktree=args.worktree,
    )
    if not success:
        print("[FAIL] Peer dispatch failed or returned invalid verdict.", file=sys.stderr)
        return 1

    if args.auto_apply:
        return _handle_peer_dispatch_auto_apply(
            prompt_path=prompt_path,
            root=args.root,
            verify_preset=args.verify_preset,
            keep_backups=args.keep_backups,
            active_profile=args.profile,
        )

    print("[OK] Peer dispatch completed successfully with valid verdict.")
    return 0


def _handle_peer_dispatch_auto_apply(
    prompt_path: Path,
    root: str | None,
    verify_preset: str | None,
    keep_backups: bool,
    active_profile: str | None,
) -> int:
    """Handles Level-3 auto-apply verification gate for peer-dispatch (ADR-0065)."""
    from ccba_harness.peer import (
        atomic_write_text,
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

    gate_file = output_path.with_suffix(".gate.md")
    gate_body = (
        f"---\n"
        f"gate_verdict: {auto_res.gate_verdict}\n"
        f"success: {str(auto_res.success).lower()}\n"
        f"rollback_proven: {str(auto_res.rollback_proven).lower()}\n"
        f"preset: {verify_preset or 'ci'}\n"
        f"transaction_id: {auto_res.transaction_id}\n"
        f"---\n\n"
        f"# 🛡️ Level-3 Orchestrator Gate Result\n\n"
        f"- **Verdict:** `{auto_res.gate_verdict}`\n"
        f"- **Success:** `{auto_res.success}`\n"
        f"- **Rollback Proven:** `{auto_res.rollback_proven}`\n"
        f"- **Summary:** {auto_res.summary}\n"
    )
    atomic_write_text(gate_file, gate_body)

    if auto_res.success:
        print(f"[OK] Level-3 Auto-Apply passed: {auto_res.summary}")
        return 0
    if auto_res.rollback_proven:
        print(
            f"[GATE_FAIL] Level-3 Auto-Apply verification failed and workspace rolled back cleanly: {auto_res.summary}",
            file=sys.stderr,
        )
        return 4
    print(
        f"[ERROR] Level-3 Auto-Apply rollback verification mismatch or failure: {auto_res.summary}",
        file=sys.stderr,
    )
    return 1


def run_peer_co_review_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for parallel multi-agent co-review orchestration (`ccba-harness peer-co-review` - ADR-0065)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness peer-co-review",
        description="Parallel Multi-Agent Co-Review Orchestration and Consensus Engine (Level-2.5 / ADR-0065).",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        required=True,
        help="Path to markdown prompt file containing PeerPromptEnvelope.",
    )
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=["code_review", "arch_audit"],
        help="Profiles to dispatch in parallel (default: code_review arch_audit).",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        default=None,
        help="Path for saving the consolidated consensus markdown report.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Hard cap on parallel worker threads.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Execution timeout override per profile in seconds.",
    )
    parser.add_argument(
        "--worktree",
        action="store_true",
        help="Execute agents in isolated git worktrees.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned co-review dispatch plan and exit without executing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output consensus report as JSON to stdout.",
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        help="Automatically apply and verify patch if consensus is APPROVE and --patch-file is provided (Level-3 / ADR-0065).",
    )
    parser.add_argument(
        "--patch-file",
        type=str,
        default=None,
        help="Explicit path to patch file containing AnchorPatchPayload (COND-LEVEL3-TRUST).",
    )
    parser.add_argument(
        "--verify-preset",
        type=str,
        choices=["code", "doc", "skill", "adr", "telemetry", "ci", "eval"],
        default="ci",
        help="Verification preset to run upon auto-apply (default: ci).",
    )
    parser.add_argument(
        "--keep-backups",
        action="store_true",
        help="Preserve transaction backup directories under .md/backups/anchor-txn/.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root directory for workspace (default: git rev-parse --show-toplevel).",
    )

    args = parser.parse_args(args_list)
    prompt_path = Path(args.prompt_file).resolve()
    if not prompt_path.exists():
        print(f"[FAIL] Prompt file not found: {prompt_path}", file=sys.stderr)
        return 1

    from ccba_harness.peer import (
        PROFILE_SPECS,
        orchestrate_peer_co_review,
        parse_envelope_from_md,
        safe_read_and_hash,
    )

    if args.auto_apply:
        if not args.patch_file:
            print(
                "[FAIL] --auto-apply on co-review requires an explicit --patch-file (COND-LEVEL3-TRUST).",
                file=sys.stderr,
            )
            return 1
        patch_path = Path(args.patch_file).resolve()
        if not patch_path.exists():
            print(f"[FAIL] Specified patch file not found: {patch_path}", file=sys.stderr)
            return 1

    if args.dry_run:
        content, _ = safe_read_and_hash(prompt_path)
        envelope = parse_envelope_from_md(content or "")
        req_id = envelope.request_id if envelope else "unknown"
        print(f"[DRY-RUN] Request ID: {req_id}")
        print(f"[DRY-RUN] Profiles: {', '.join(args.profiles)}")
        for p in args.profiles:
            spec = PROFILE_SPECS.get(p, {})
            model = spec.get("model", "unknown")
            timeout = args.timeout if args.timeout is not None else spec.get("timeout", 180.0)
            print(f"  - Profile: {p:12s} | Model: {model:20s} | Timeout: {timeout}s")
        out_target = (
            Path(args.output_file)
            if args.output_file
            else prompt_path.parent / f"grok_consensus_{prompt_path.stem.replace('prompt_', '')}.md"
        )
        print(f"[DRY-RUN] Consensus Output: {out_target}")
        return 0

    output_path = Path(args.output_file).resolve() if args.output_file else None
    report = orchestrate_peer_co_review(
        prompt_path=prompt_path,
        profiles=args.profiles,
        output_file=output_path,
        max_workers=args.max_workers,
        timeout=args.timeout,
        worktree=args.worktree,
    )

    if report is None:
        print(
            "[FAIL] Failed to orchestrate peer co-review: prompt is unreadable.",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(f"[OK] Consensus Verdict: {report.verdict} (Risk: {report.risk_score}/5)")
        print(
            f"Quorum: {len(report.completed_profiles)}/{len(report.expected_profiles)} completed."
        )
        if report.conditions:
            print(f"Conditions ({len(report.conditions)}):")
            for c in report.conditions:
                tag = "[BLOCKING]" if c.blocking else "[ADVISORY]"
                print(f"  - {c.id} {tag}: {c.description}")

    if args.auto_apply:
        return _handle_peer_co_review_auto_apply(
            prompt_path=prompt_path,
            output_path=output_path,
            report=report,
            patch_file=args.patch_file,
            root=args.root,
            verify_preset=args.verify_preset,
            keep_backups=args.keep_backups,
        )

    if report.verdict in ("APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS"):
        return 0
    if report.verdict in ("APPROVE_WITH_CONDITIONS", "APPROVE_WITH_RESERVATIONS"):
        return 2
    if report.verdict == "REVISE_PLAN":
        return 3
    if report.verdict in ("REJECT", "REJECT_PLAN", "GATE_FAIL"):
        return 4
    if report.verdict == "HANDOFF":
        return 5
    return 1


def _handle_peer_co_review_auto_apply(
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
        atomic_write_text,
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
    gate_file = gate_target.with_suffix(".gate.md")
    gate_body = (
        f"---\n"
        f"gate_verdict: {auto_res.gate_verdict}\n"
        f"success: {str(auto_res.success).lower()}\n"
        f"rollback_proven: {str(auto_res.rollback_proven).lower()}\n"
        f"preset: {verify_preset or 'ci'}\n"
        f"transaction_id: {auto_res.transaction_id}\n"
        f"---\n\n"
        f"# 🛡️ Level-3 Consensus Orchestrator Gate Result\n\n"
        f"- **Verdict:** `{auto_res.gate_verdict}`\n"
        f"- **Success:** `{auto_res.success}`\n"
        f"- **Rollback Proven:** `{auto_res.rollback_proven}`\n"
        f"- **Summary:** {auto_res.summary}\n"
    )
    atomic_write_text(gate_file, gate_body)

    if auto_res.success:
        print(f"[OK] Level-3 Co-Review Auto-Apply passed: {auto_res.summary}")
        return 0
    if auto_res.rollback_proven:
        print(
            f"[GATE_FAIL] Level-3 Co-Review Auto-Apply verification failed and workspace rolled back cleanly: {auto_res.summary}",
            file=sys.stderr,
        )
        return 4
    print(
        f"[ERROR] Level-3 Co-Review Auto-Apply rollback verification mismatch or failure: {auto_res.summary}",
        file=sys.stderr,
    )
    return 1


def run_apply_anchor_patch_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for applying anchor patches (`ccba-harness apply-anchor-patch` - ADR-0063)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness apply-anchor-patch",
        description="Apply Level-2 anchor patches with two-phase commit and transactional rollback (ADR-0063).",
    )
    parser.add_argument(
        "--patch-file",
        "-f",
        type=str,
        required=True,
        help="Path to patch markdown/JSON file, or '-' to read from standard input.",
    )
    parser.add_argument(
        "--root",
        "-r",
        type=str,
        default=None,
        help="Project workspace root directory (default: current working directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate patch integrity and check target anchors without writing changes to disk.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create .bak backups before overwriting target files.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress informational stdout output (only errors will be emitted).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON results instead of human-readable text.",
    )

    args = parser.parse_args(args_list)

    if args.patch_file == "-":
        raw_content = sys.stdin.read()
    else:
        patch_path = Path(args.patch_file).resolve()
        if not patch_path.exists():
            err_msg = f"Patch file not found: {patch_path}"
            if args.json:
                print(json.dumps({"status": "ERROR", "error": err_msg}))
            else:
                print(f"[FAIL] {err_msg}", file=sys.stderr)
            return 1
        raw_content = patch_path.read_text(encoding="utf-8")

    from ccba_harness.peer import apply_anchor_patch, extract_anchor_payload

    payload = extract_anchor_payload(raw_content)
    if payload is None:
        err_msg = "No valid AnchorPatchPayload found in input"
        if args.json:
            print(json.dumps({"status": "ERROR", "error": err_msg}))
        else:
            print(f"[FAIL] {err_msg}", file=sys.stderr)
        return 1

    root_path = Path(args.root).resolve() if args.root else Path.cwd()
    try:
        modified_paths = apply_anchor_patch(
            root=root_path,
            payload=payload,
            dry_run=args.dry_run,
            backup=args.backup,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "ERROR", "error": str(exc)}))
        else:
            print(f"[FAIL] Failed to apply anchor patch: {exc}", file=sys.stderr)
        return 1

    rel_paths = [
        str(p.relative_to(root_path)) if p.is_relative_to(root_path) else str(p)
        for p in modified_paths
    ]
    status_label = "DRY_RUN_OK" if args.dry_run else "APPLIED"

    if args.json:
        print(
            json.dumps(
                {
                    "status": status_label,
                    "count": len(rel_paths),
                    "files": rel_paths,
                    "dry_run": args.dry_run,
                }
            )
        )
    elif not args.quiet:
        action_verb = "Validated" if args.dry_run else "Successfully applied"
        print(f"[OK] {action_verb} {len(rel_paths)} file(s):")
        for f in rel_paths:
            print(f"  - {f}")

    return 0
