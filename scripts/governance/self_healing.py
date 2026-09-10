#!/usr/bin/env python3
"""self_healing.py - Autonomous Self-Healing & Closed-Loop CI Patch Engine CLI.

Diagnoses verification failures (ruff check/format, catalog drift, ADR matrix drift, pytest),
synthesizes targeted remediation actions, and iterates in a closed loop (up to 2 iterations)
with atomic snapshot rollback to guarantee deterministic zero-drift recovery.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS_SRC = REPO_ROOT / "packages" / "ccba-harness" / "src"
if str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))

from ccba_harness.healing import SelfHealingEngine
from ccba_harness.verifier import resolve_preset_commands, verify_patch_execution


def run_self_healing_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entrypoint for standalone autonomous self-healing."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="python scripts/governance/self_healing.py",
        description="Autonomous Self-Healing & Closed-Loop CI Patch Engine.",
    )
    parser.add_argument(
        "pos_commands",
        nargs="*",
        default=[],
        help="Command strings to verify and heal sequentially",
    )
    parser.add_argument(
        "-c",
        "--cmd",
        "--commands",
        dest="commands",
        nargs="+",
        default=[],
        help="Command string(s) to verify and heal",
    )
    parser.add_argument(
        "--preset",
        choices=["code", "doc", "skill", "adr", "ci"],
        default=None,
        help="Verification preset to automatically generate standard commands",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target file or directory path for preset",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=REPO_ROOT,
        help="Workspace base directory (default: repo root)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum self-healing loop iterations (default: 2)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-command execution timeout in seconds (default: 60.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Diagnose failures and propose remediation actions without executing mutations",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output healing report as JSON to stdout",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=None,
        help="Write markdown or JSON report to specified file path",
    )

    args = parser.parse_args(args_list)

    commands_to_run: list[str] = []
    if args.commands:
        commands_to_run.extend(args.commands)
    if args.pos_commands:
        commands_to_run.extend(args.pos_commands)

    if args.preset:
        preset_cmds = resolve_preset_commands(preset=args.preset, target=args.target)
        commands_to_run.extend(preset_cmds)

    if not commands_to_run:
        print("ERROR: No verification commands or preset provided to heal.", file=sys.stderr)
        return 1

    engine = SelfHealingEngine(base_dir=args.base_dir, max_iterations=args.max_iterations)

    if args.dry_run:
        # Dry-run: run verification once, diagnose, generate actions, do NOT execute
        report = verify_patch_execution(
            commands=commands_to_run, cwd=args.base_dir, timeout=args.timeout
        )
        issues = engine.diagnose_failures(report)
        actions = engine.generate_remediation_actions(issues)
        result_dict = {
            "dry_run": True,
            "verification_passed": report.all_passed,
            "diagnosed_issues": [i.to_dict() for i in issues],
            "proposed_actions": [a.to_dict() for a in actions],
        }
        if args.json:
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
        else:
            print("# 🩺 Self-Healing Dry-Run Diagnostics")
            print(f"- **Initial Verification:** {'PASS' if report.all_passed else 'FAIL'}")
            print(f"- **Issues Diagnosed:** {len(issues)}")
            print(f"- **Proposed Actions:** {len(actions)}")
            for idx, act in enumerate(actions, 1):
                print(f"  {idx}. [{act.action_type}] {act.description}")
                if act.command:
                    print(f"     `{act.command}`")
        return 0 if report.all_passed else 1

    healing_report = engine.attempt_closed_loop_healing(
        verify_commands=commands_to_run,
        timeout=args.timeout,
    )

    if args.report_file:
        rf_path = Path(args.report_file)
        rf_path.parent.mkdir(parents=True, exist_ok=True)
        if rf_path.suffix.lower() == ".json":
            rf_path.write_text(
                json.dumps(healing_report.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            rf_path.write_text(healing_report.to_markdown(), encoding="utf-8")

    if args.json:
        print(json.dumps(healing_report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(healing_report.to_markdown())

    return 0 if healing_report.success else 1


if __name__ == "__main__":
    sys.exit(run_self_healing_cli())
