"""cli/_envelope.py - Additive Flat JSON envelope and semantic exit-code helpers."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ccba_harness.healing import SelfHealingEngine
from ccba_harness.verifier import CommandResult, PatchVerificationReport

_SEM_EXIT: dict[str, int] = {"COMMAND_TIMEOUT": 124, "INVALID_INPUT": 2}
_CARD_CMD = "ccba-harness door-triage --enforce-tradeoff-card --pr-body-file <pr.md>"
_APPROVAL_CMD = "Request Taste-Holder approval per ADR-0067"


def _attach(
    base: dict[str, Any],
    status: str,
    error: tuple[str, str, bool] | None = None,
    actions: Sequence[tuple[str, str]] = (),
) -> dict[str, Any]:
    """Attach standard 4-key Additive Flat JSON envelope fields to a base dict."""
    err = {"code": error[0], "message": error[1], "retryable": error[2]} if error else None
    acts = [{"command": c, "description": d} for c, d in actions]
    return {**base, "schema_version": "1", "status": status, "error": err, "next_actions": acts}


def build_invalid_input_envelope(msg: str, hint_cmd: str, hint_desc: str) -> dict[str, Any]:
    """Build an INVALID_INPUT JSON envelope."""
    return _attach({}, "error", ("INVALID_INPUT", msg, False), [(hint_cmd, hint_desc)])


def parse_with_json_envelope(
    parser: argparse.ArgumentParser, args_list: Sequence[str] | None
) -> tuple[argparse.Namespace | None, int | None]:
    """Parse CLI args and emit JSON INVALID_INPUT on parse error when --json is set."""
    argv = list(sys.argv[1:] if args_list is None else args_list)
    head = argv[: argv.index("--")] if "--" in argv else argv
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--json", action="store_true")
    pre_ns, _ = pre.parse_known_args(head)
    err_buf = io.StringIO()
    try:
        with contextlib.redirect_stderr(err_buf):
            return parser.parse_args(argv), None
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        err_msg = err_buf.getvalue().strip()
        if not pre_ns.json:
            if err_msg:
                print(err_msg, file=sys.stderr)
            raise
        last = err_msg.splitlines()[-1] if err_msg else "Invalid CLI arguments"
        env = build_invalid_input_envelope(last, f"{parser.prog} --help", "Show valid options")
        print(json.dumps(env, indent=2))
        return None, 2


def resolve_exit_code(*, passed: bool, semantic: bool, error_code: str | None) -> int:
    """Resolve default (0/1) or semantic (0|1|2|4|124) CLI exit code."""
    if error_code == "HUMAN_APPROVAL_REQUIRED":
        return 4 if semantic else 0
    return 0 if passed else (_SEM_EXIT.get(error_code or "", 1) if semantic else 1)


def enrich_patch_report_dict(
    active: dict[str, Any], report: PatchVerificationReport, base_dir: Path | None = None
) -> tuple[dict[str, Any], str | None]:
    """Attach Additive Flat envelope to verify-patch report using post-heal report state."""
    if report.all_passed:
        return _attach(active, "ok"), None
    eng = SelfHealingEngine(base_dir=base_dir)
    rem = eng.generate_remediation_actions(eng.diagnose_failures(report))
    acts = [(a.command, a.description) for a in rem if a.command]
    timed_out = [r for r in report.results if r.timed_out]
    if timed_out:
        cmd, c = timed_out[0].command, "COMMAND_TIMEOUT"
        to_cmd = f"ccba-harness verify-patch --timeout 300 --cmd {json.dumps(cmd)}"
        msg = timed_out[0].error_message or f"Command timed out: {cmd}"
        return _attach(active, "error", (c, msg, True), [(to_cmd, "Higher --timeout"), *acts]), c
    failed = next((r for r in report.results if not r.passed), None)
    if not acts and failed is not None:
        acts = [(failed.command, f"Re-run failing check (exit {failed.exit_code})")]
    msg = f"{report.failed_count}/{report.total_commands} verification command(s) failed"
    return _attach(active, "error", ("CHECKS_FAILED", msg, False), acts), "CHECKS_FAILED"


def enrich_doc_result_dict(
    res: CommandResult, target: str, min_bytes: int, headings: Sequence[str] | None
) -> dict[str, Any]:
    """Attach Additive Flat envelope to verify-doc CommandResult dict."""
    base = res.to_dict()
    if res.passed:
        return _attach(base, "ok")
    hdr = f" --required-headings {','.join(headings)}" if headings else ""
    cmd = f"ccba-harness verify-doc --target {target} --min-bytes {min_bytes}{hdr}"
    msg = res.error_message or "Document verification failed"
    return _attach(base, "error", ("CHECKS_FAILED", msg, False), [(cmd, "Fix and re-run")])


def enrich_door_triage_dict(
    payload: dict[str, Any], door: str, enforce: bool
) -> tuple[dict[str, Any], str | None]:
    """Attach Additive Flat envelope to door-triage payload dict."""
    if door != "ONE_WAY_DOOR":
        return _attach(payload, "ok"), None
    if enforce and not payload.get("tradeoff_card_valid", True):
        msg = "; ".join(payload.get("tradeoff_card_errors") or []) or "Missing Tradeoff Card"
        c = "TRADEOFF_CARD_INVALID"
        return _attach(payload, "error", (c, msg, False), [(_CARD_CMD, "Add valid card")]), c
    st, c = "approval_required", "HUMAN_APPROVAL_REQUIRED"
    msg = "ONE_WAY_DOOR PR requires human Taste-Holder approval (ADR-0067)"
    return _attach(payload, st, (c, msg, False), [(_APPROVAL_CMD, "Sign-off PR")]), c
