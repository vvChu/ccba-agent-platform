#!/usr/bin/env python3
"""
Team Task Coordinator CLI for ccba-agent-platform.
Manages a shared, file-based JSON task database for multi-agent coordination.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_FILE = Path(".md/team_tasks.json")


def load_tasks() -> list:
    """Load tasks from the shared JSON database."""
    if not DB_FILE.exists():
        # Create empty db
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_tasks([])
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Coordinator] Warning: Could not parse {DB_FILE}: {e}")
        return []


def save_tasks(tasks: list):
    """Save tasks to the shared JSON database."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Coordinator] Error saving tasks: {e}")


def list_tasks():
    """List all tasks in a formatted table."""
    tasks = load_tasks()
    if not tasks:
        print("[Coordinator] No tasks found in the database.")
        return
        
    print(f"\n[Coordinator] Shared Tasks from {DB_FILE}:\n")
    print(f"{'Name':<35} | {'Owner':<15} | {'Status':<12}")
    print("-" * 70)
    for t in tasks:
        print(f"{t['name']:<35} | {t.get('owner', 'None'):<15} | {t['status']:<12}")
    print()


def add_task(name: str, owner: str = None) -> int:
    """Add a new task to the database."""
    tasks = load_tasks()
    # Check duplicate
    if any(t["name"] == name for t in tasks):
        print(f"[Coordinator] Error: Task '{name}' already exists.")
        return 1
        
    tasks.append({
        "name": name,
        "owner": owner or "None",
        "status": "pending" if not owner else "in-progress"
    })
    save_tasks(tasks)
    print(f"[Coordinator] Added task '{name}' (Owner: {owner or 'None'}).")
    return 0


def claim_task(name: str, owner: str) -> int:
    """Claim a task for execution."""
    tasks = load_tasks()
    for t in tasks:
        if t["name"] == name:
            if t["status"] == "completed":
                print(f"[Coordinator] Warning: Task '{name}' is already completed.")
                return 1
            t["owner"] = owner
            t["status"] = "in-progress"
            save_tasks(tasks)
            print(f"[Coordinator] Owner '{owner}' claimed task '{name}'.")
            return 0
            
    print(f"[Coordinator] Error: Task '{name}' not found.")
    return 1


def complete_task(name: str) -> int:
    """Mark a task as completed."""
    tasks = load_tasks()
    for t in tasks:
        if t["name"] == name:
            t["status"] = "completed"
            save_tasks(tasks)
            print(f"[Coordinator] Task '{name}' completed successfully.")
            return 0
            
    print(f"[Coordinator] Error: Task '{name}' not found.")
    return 1


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
    
    if args.command == "list":
        list_tasks()
    elif args.command == "add":
        sys.exit(add_task(args.name, args.owner))
    elif args.command == "claim":
        sys.exit(claim_task(args.name, args.owner))
    elif args.command == "complete":
        sys.exit(complete_task(args.name))


if __name__ == "__main__":
    main()
