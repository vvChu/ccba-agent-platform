#!/usr/bin/env python3
"""token_economy.py - Dedicated Platform CLI for Prompt Density & Token Economy Optimization.

Usage:
  python scripts/governance/token_economy.py scan [--json]
  python scripts/governance/token_economy.py report [--out .md/reports/prompt_economy_report.md]
  python scripts/governance/token_economy.py roi <conversation_id_or_log> [--role coder]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure monorepo package is resolvable
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CCBA_HARNESS = _REPO_ROOT / "packages" / "ccba-harness" / "src"
if str(_CCBA_HARNESS) not in sys.path:
    sys.path.insert(0, str(_CCBA_HARNESS))

from ccba_harness.economy import (
    DEFAULT_DMI_TOKEN_CEILING,
    DEFAULT_MI_TOKEN_CEILING,
    audit_token_economy,
    calculate_role_aware_roi,
    check_skill_token_budget,
    generate_prompt_pruning_report,
)
from ccba_harness.telemetry import analyze_subagent_transcript


def _configure_stdio_utf8() -> None:
    """Reconfigure Windows console streams to UTF-8 safely."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for token_economy subcommands."""
    parser = argparse.ArgumentParser(
        prog="token_economy.py",
        description="CCBA Prompt Density & Token Economy Optimization Engine.",
    )
    sub = parser.add_subparsers(dest="action", help="Action to perform")

    p_scan = sub.add_parser("scan", help="Scan and audit prompt density for all skills")
    p_scan.add_argument("--json", action="store_true", help="Output raw JSON format")
    p_scan.add_argument("--root", type=str, default=None, help="Root directory for skills")

    p_rep = sub.add_parser("report", help="Generate actionable prompt pruning markdown report")
    p_rep.add_argument(
        "--out",
        type=str,
        default=".md/reports/prompt_economy_report.md",
        help="Path to save report (default: .md/reports/prompt_economy_report.md)",
    )

    p_roi = sub.add_parser("roi", help="Calculate Token ROI for an agent execution session")
    p_roi.add_argument("target", help="Conversation ID, transcript file, or directory")
    p_roi.add_argument(
        "--role", type=str, default=None, help="Override role (coder, investigator, reviewer)"
    )
    p_roi.add_argument("--json", action="store_true", help="Output raw JSON format")

    p_rat = sub.add_parser("check-ratchet", help="Verify one-way LF skill token budget ratchet")
    p_rat.add_argument("--root", type=str, default=None, help="Skills root directory")
    p_rat.add_argument(
        "--baseline",
        type=str,
        default="scripts/skill_token_budget_baseline.json",
        help="Path to skill_token_budget_baseline.json",
    )
    p_rat.add_argument(
        "--ratchet-update", action="store_true", help="Lower baseline strictly downward"
    )
    p_rat.add_argument("--json", action="store_true", help="Output raw JSON format")
    return parser


def _handle_ratchet(args: argparse.Namespace) -> int:
    """Execute check-ratchet action and print result."""
    skills_root = Path(args.root) if args.root else _REPO_ROOT / ".agents" / "skills"
    if not skills_root.is_absolute():
        skills_root = _REPO_ROOT / skills_root
    base_p = Path(args.baseline)
    if not base_p.is_absolute():
        base_p = _REPO_ROOT / base_p
    res = check_skill_token_budget(
        skills_root,
        base_p,
        mi_ceiling=DEFAULT_MI_TOKEN_CEILING,
        dmi_ceiling=DEFAULT_DMI_TOKEN_CEILING,
        update_baseline=bool(args.ratchet_update),
    )
    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    elif res.passed:
        print(f"[OK] Skill token ratchet passed ({res.checked_count} skills checked).")
        if res.updated_baseline is not None:
            print(f"  Updated baseline entries (> ceiling): {len(res.updated_baseline)}")
    else:
        print(
            f"[FAIL] Skill token ratchet failed ({len(res.violations)} violation(s)):",
            file=sys.stderr,
        )
        for v in res.violations:
            print(f"  - {v}", file=sys.stderr)
    return 0 if res.passed else 1


def _handle_roi(args: argparse.Namespace) -> int:
    """Execute ROI reporting action."""
    try:
        metrics = analyze_subagent_transcript(args.target)
        roi = calculate_role_aware_roi(metrics, role_override=args.role)
        if args.json:
            print(json.dumps(roi.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(f"# 📊 Token ROI Analysis: `{roi.conversation_id}`")
            print(f"- **Assigned Role:** {roi.role} | **Efficiency:** {roi.efficiency_tier}")
            print(
                f"- **Tokens:** {roi.prompt_tokens:,} in / {roi.completion_tokens:,} out | **ROI:** {roi.token_roi:.2f}"
            )
            print(f"- **Notes:** {roi.summary_notes}")
        return 0
    except Exception as err:
        print(f"[Error] Failed to calculate ROI for '{args.target}': {err}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point for token economy governance."""
    _configure_stdio_utf8()
    args = _build_parser().parse_args(argv)
    if not args.action or args.action == "scan":
        root = Path(args.root) if getattr(args, "root", None) else _REPO_ROOT / ".agents" / "skills"
        report = audit_token_economy(skills_dir=root)
        print(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
            if getattr(args, "json", False)
            else report.to_markdown()
        )
        return 0
    if args.action == "report":
        out_p = Path(args.out) if Path(args.out).is_absolute() else _REPO_ROOT / args.out
        report = audit_token_economy(skills_dir=_REPO_ROOT / ".agents" / "skills")
        generate_prompt_pruning_report(report, output_path=out_p)
        print(
            f"[Success] Generated Prompt Pruning Report at: {out_p} ({report.total_skills} skills, {report.bloated_skills_count} bloated)"
        )
        return 0
    if args.action == "roi":
        return _handle_roi(args)
    if args.action == "check-ratchet":
        return _handle_ratchet(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
