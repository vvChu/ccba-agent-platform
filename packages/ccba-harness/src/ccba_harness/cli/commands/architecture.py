"""commands/architecture.py - CLI handlers for blast-radius and why commands (ADR-0009)."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path


def run_blast_radius_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for cross-boundary blast radius scanner (`ccba-harness blast-radius`)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness blast-radius",
        description="Analyze cross-boundary blast radius and impacted test suites (ADR-0009).",
    )
    parser.add_argument("targets", nargs="+", help="Module, skill, or symbol names changed")
    parser.add_argument("--root", type=str, default=None, help="Workspace root directory to scan")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")

    args = parser.parse_args(args_list)
    root_p = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    from ccba_harness.blast_radius import analyze_blast_radius

    report = analyze_blast_radius(set(args.targets), root_p)

    if args.json:
        print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 65)
        print(f"💥 BLAST RADIUS REPORT — Risk Level: [{report.risk_level}]")
        print("=" * 65)
        print(f"Targets Analyzed : {', '.join(report.targets)}")
        print(f"Affected Files   : {report.affected_file_count}")
        for f in report.affected_files[:10]:
            print(f"  - {f}")
        if len(report.affected_files) > 10:
            print(f"  ... and {len(report.affected_files) - 10} more files.")
        print(f"Recommended Tests: {len(report.recommended_tests)}")
        for t in report.recommended_tests:
            print(f"  - pytest {t}")
        print("=" * 65 + "\n")

    return 0 if report.risk_level != "CRITICAL" else 1


def run_explain_why_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for architecture why explainer (`ccba-harness why`)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness why",
        description="Query architectural rationale from ADRs, git logs & peer exchanges (ADR-0009).",
    )
    parser.add_argument("query", type=str, help="Architectural question or topic keyword")
    parser.add_argument("--root", type=str, default=None, help="Workspace root directory")
    parser.add_argument("--json", action="store_true", help="Output result in JSON format")

    args = parser.parse_args(args_list)
    root_p = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    from ccba_harness.architecture import explain_architecture_why

    explanation = explain_architecture_why(args.query, root_dir=root_p)

    if args.json:
        print(json.dumps(explanation.model_dump(), indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 65)
        print(f"🏛️ ARCHITECTURE WHY: '{explanation.query}'")
        print("=" * 65)
        print(f"Synthesis:\n{explanation.synthesis}\n")
        if explanation.adr_matches:
            print("Matched ADRs:")
            for m in explanation.adr_matches:
                print(f"  - ADR-{m.adr_id} ({m.title}) [{m.status}]: {m.decision_summary}")
        if explanation.git_commits:
            print("\nRelated Git Commits:")
            for c in explanation.git_commits:
                print(f"  - {c.get('hash')}: {c.get('message')}")
        print("=" * 65 + "\n")

    return 0


def _execute_door_triage(args: argparse.Namespace) -> int:
    """Executes door policy classification and optional Tradeoff Card validation."""
    from ccba_harness.backpressure import validate_tradeoff_card
    from ccba_harness.door_policy import classify_pr_door, load_recent_merges_from_git

    root_p = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    merges = load_recent_merges_from_git(root_p)
    res = classify_pr_door(
        changed_files=args.files or [],
        logic_loc=args.logic_loc,
        recent_merges=merges,
        repo=args.repo,
        pr_number=args.pr_number,
    )
    card_errors: list[str] = []
    if args.pr_body_file and Path(args.pr_body_file).exists():
        body_text = Path(args.pr_body_file).read_text(encoding="utf-8")
        if res.door_type == "ONE_WAY_DOOR":
            card_errors = validate_tradeoff_card(body_text)

    payload = {
        **res.model_dump(mode="json"),
        "tradeoff_card_errors": card_errors,
        "tradeoff_card_valid": len(card_errors) == 0,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        cats = ", ".join(c.value for c in res.matched_categories) or "NONE"
        print(
            f"Door: {res.door_type} | Categories: {cats} | Streak: {res.cumulative_streak} | Sampled: {res.sampled_for_audit}"
        )
    if args.enforce_tradeoff_card and res.door_type == "ONE_WAY_DOOR" and card_errors:
        return 1
    return 0


def run_door_triage_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for 3-tier PR door classification (`ccba-harness door-triage`)."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness door-triage",
        description="Classify PR into TWO_WAY_DOOR, PAVED_ROAD, or ONE_WAY_DOOR (Issue #519).",
    )
    parser.add_argument("files", nargs="*", help="Modified repository-relative file paths")
    parser.add_argument("--logic-loc", type=int, default=0, help="Total logic LOC diff")
    parser.add_argument("--pr-number", type=int, default=0, help="Pull request number")
    parser.add_argument("--repo", type=str, default="vvChu/ccba-agent-platform", help="Repo slug")
    parser.add_argument(
        "--pr-body-file", type=str, default=None, help="Path to PR body markdown file"
    )
    parser.add_argument(
        "--enforce-tradeoff-card",
        action="store_true",
        help="Exit 1 if ONE_WAY_DOOR PR lacks a valid Tradeoff Card",
    )
    parser.add_argument("--root", type=str, default=None, help="Workspace root directory")
    parser.add_argument("--json", action="store_true", help="Output result in JSON format")

    args = parser.parse_args(args_list)
    return _execute_door_triage(args)
