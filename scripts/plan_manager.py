#!/usr/bin/env python3
"""
Plan Manager CLI for ccba-agent-platform.
CLI wrapper delegating core logic to ccba_ai.services.plan.
"""

import argparse
import sys
from pathlib import Path

from ccba_ai.services import plan

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="CCBA Plan Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create subcommand
    create_parser = subparsers.add_parser("create", help="Create a new plan")
    create_parser.add_argument("--title", required=True, help="Title of the plan")
    create_parser.add_argument("--phases", required=True, help="Comma-separated list of phase names")

    # check subcommand
    check_parser = subparsers.add_parser("check", help="Update a phase status")
    check_parser.add_argument("--plan", required=True, help="Path to plan.md")
    check_parser.add_argument("--phase", required=True, help="Phase ID (e.g. 01)")
    check_parser.add_argument("--status", default="completed", choices=["pending", "in-progress", "completed"], help="Status target")

    # status subcommand
    status_parser = subparsers.add_parser("status", help="Show current plan status")
    status_parser.add_argument("--plan", required=True, help="Path to plan.md")

    args = parser.parse_args()

    try:
        if args.command == "create":
            phases = [p.strip() for p in args.phases.split(",") if p.strip()]
            res = plan.create_plan(args.title, phases)
            print(f"[Plan Manager] Created plan folder: {res['plan_folder']}")
            for file in res["created_files"]:
                if "phase-" in file:
                    print(f"  - Created phase file: {file}")
            print(f"Created main plan file: {res['plan_file']}")
            sys.exit(0)

        elif args.command == "check":
            res = plan.update_phase_status(args.plan, args.phase, args.status)
            print(f"[Plan Manager] Updated plan.md: Phase {res['phase_id']} -> {res['new_status']}")
            if res["phase_file_updated"]:
                print(f"[Plan Manager] Updated phase file: {res['phase_file']} -> {res['new_status']}")
            sys.exit(0)

        elif args.command == "status":
            res = plan.get_plan_status(args.plan)
            print(f"\n[Plan Manager] Plan Status for: {Path(res['plan_file']).parent.name}\n")
            print("| Phase | Name | Status | File |")
            print("|-------|------|--------|------|")
            for p in res["phases"]:
                print(f"| {p['id']} | {p['name']} | {p['status']} | {p['file']} |")
            print()
            sys.exit(0)

    except Exception as e:
        print(f"[Plan Manager] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
