#!/usr/bin/env python3
"""
Team Task Coordinator CLI for ccba-agent-platform.
CLI wrapper delegating core logic to ccba_ai.services.team.
"""

import argparse
import sys
from pathlib import Path

from ccba_ai.services import team

# Enforce UTF-8 output
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def list_tasks():
    """List all tasks in a formatted table."""
    tasks = team.load_tasks()
    if not tasks:
        print("[Coordinator] No tasks found in the database.")
        return

    db_file = Path(".md/data/team_tasks.json")
    print(f"\n[Coordinator] Shared Tasks from {db_file}:\n")
    print(f"{'Name':<35} | {'Owner':<15} | {'Status':<12}")
    print("-" * 70)
    for t in tasks:
        print(f"{t['name']:<35} | {t.get('owner', 'None'):<15} | {t['status']:<12}")
    print()


def main():
    parser = argparse.ArgumentParser(description="CCBA Team Task Coordinator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    subparsers.add_parser("list", help="List all coordinator tasks")

    # add command
    add_parser = subparsers.add_parser("add", help="Add a task")
    add_parser.add_argument("--name", required=True, help="Name of the task")
    add_parser.add_argument("--owner", help="Owner of the task")

    # claim command
    claim_parser = subparsers.add_parser("claim", help="Claim a task")
    claim_parser.add_argument("--name", required=True, help="Name of the task")
    claim_parser.add_argument("--owner", required=True, help="Owner name claiming the task")

    # complete command
    complete_parser = subparsers.add_parser("complete", help="Complete a task")
    complete_parser.add_argument("--name", required=True, help="Name of the task")

    args = parser.parse_args()

    try:
        if args.command == "list":
            list_tasks()
            sys.exit(0)
        elif args.command == "add":
            res = team.add_task(args.name, args.owner)
            print(f"[Coordinator] Added task '{res['name']}' (Owner: {res['owner']}).")
            sys.exit(0)
        elif args.command == "claim":
            res = team.claim_task(args.name, args.owner)
            print(f"[Coordinator] Owner '{res['owner']}' claimed task '{res['name']}'.")
            sys.exit(0)
        elif args.command == "complete":
            res = team.complete_task(args.name)
            print(f"[Coordinator] Task '{res['name']}' completed successfully.")
            sys.exit(0)

    except Exception as e:
        print(f"[Coordinator] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
