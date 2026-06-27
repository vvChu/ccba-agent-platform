#!/usr/bin/env python3
"""
Plan Manager CLI for ccba-agent-platform.
Manages file-based plans and phase status synchronization.
"""

import sys
import os
import re
import argparse
from datetime import datetime
from pathlib import Path

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

PLAN_TEMPLATE = """# Plan: {title}

> Branch: {branch}
> Date: {date}
> Status: in-progress

## Phases

| Phase | Name | Status | File |
|-------|------|--------|------|
{phases_rows}
"""

PHASE_TEMPLATE = """---
phase: {phase_num}
title: "{phase_name}"
status: {status}
priority: P2
dependencies: {dependencies}
---

# Phase {phase_num}: {phase_name}

## Overview
Brief objective of this phase.

## Tasks
- [ ] Task 1
- [ ] Task 2

## Success Criteria
- [ ] Criteria 1
"""


def slugify(text: str) -> str:
    """Convert text to lower-case kebab-case slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def create_plan(title: str, phases_list: list) -> int:
    """Create a new plan directory with plan.md and phase markdown stubs."""
    plans_dir = Path("plans")
    plans_dir.mkdir(exist_ok=True)
    
    # Get current date in YYMMDD format
    date_str = datetime.now().strftime("%y%m%d")
    slug = slugify(title)
    plan_folder = plans_dir / f"{date_str}-{slug}"
    
    if plan_folder.exists():
        print(f"[Plan Manager] Error: Plan folder {plan_folder} already exists.")
        return 1
        
    plan_folder.mkdir(parents=True, exist_ok=True)
    print(f"[Plan Manager] Created plan folder: {plan_folder}")
    
    # Get active git branch
    import subprocess
    branch = "main"
    try:
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
        branch = res.stdout.strip()
    except subprocess.SubprocessError:
        pass
        
    # Generate phase rows and create phase files
    phases_rows = []
    for idx, phase_name in enumerate(phases_list, 1):
        phase_num = f"{idx:02d}"
        phase_slug = slugify(phase_name)
        phase_filename = f"phase-{phase_num}-{phase_slug}.md"
        phase_filepath = plan_folder / phase_filename
        
        # Write phase file
        phase_content = PHASE_TEMPLATE.format(
            phase_num=idx,
            phase_name=phase_name,
            status="pending",
            dependencies="[]" if idx == 1 else f"[phase-{(idx-1):02d}]"
        )
        phase_filepath.write_text(phase_content, encoding="utf-8")
        print(f"  - Created phase file: {phase_filepath}")
        
        # Append to table
        phases_rows.append(f"| {phase_num} | {phase_name} | pending | {phase_filename} |")
        
    # Write plan file
    plan_content = PLAN_TEMPLATE.format(
        title=title,
        branch=branch,
        date=datetime.now().strftime("%Y-%m-%d"),
        phases_rows="\n".join(phases_rows)
    )
    plan_filepath = plan_folder / "plan.md"
    plan_filepath.write_text(plan_content, encoding="utf-8")
    print(f"Created main plan file: {plan_filepath}")
    return 0


def update_phase_status(plan_file: str, phase_id: str, status: str) -> int:
    """Update a phase status in both plan.md and the corresponding phase file."""
    plan_path = Path(plan_file)
    if not plan_path.exists():
        print(f"[Plan Manager] Error: Plan file {plan_file} not found.")
        return 1
        
    content = plan_path.read_text(encoding="utf-8")
    
    # Find phase in the Markdown table
    pattern = r"\|\s*" + phase_id + r"\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
    match = re.search(pattern, content)
    if not match:
        print(f"[Plan Manager] Error: Phase ID {phase_id} not found in plan table.")
        return 1
        
    phase_name = match.group(1).strip()
    old_status = match.group(2).strip()
    phase_filename = match.group(3).strip()
    
    # 1. Update status in plan.md table
    updated_row = f"| {phase_id} | {phase_name} | {status} | {phase_filename} |"
    new_content = re.sub(pattern, updated_row, content)
    plan_path.write_text(new_content, encoding="utf-8")
    print(f"[Plan Manager] Updated plan.md: Phase {phase_id} -> {status}")
    
    # 2. Update status in phase-XX-*.md file
    phase_file_path = plan_path.parent / phase_filename
    if phase_file_path.exists():
        p_content = phase_file_path.read_text(encoding="utf-8")
        p_updated = re.sub(r"status:\s*\w+", f"status: {status}", p_content)
        phase_file_path.write_text(p_updated, encoding="utf-8")
        print(f"[Plan Manager] Updated phase file: {phase_filename} -> {status}")
        
    return 0


def display_status(plan_file: str) -> int:
    """Parse and print the plan status."""
    plan_path = Path(plan_file)
    if not plan_path.exists():
        print(f"[Plan Manager] Error: Plan file {plan_file} not found.")
        return 1
        
    print(f"\n[Plan Manager] Plan Status for: {plan_path.parent.name}\n")
    content = plan_path.read_text(encoding="utf-8")
    
    # Print the table lines
    lines = content.splitlines()
    in_table = False
    for line in lines:
        if "| Phase |" in line:
            in_table = True
        if in_table:
            print(line)
            if line.strip() == "" or not line.startswith("|"):
                in_table = False
    print()
    return 0


def main():
    parser = argparse.ArgumentParser(description="CCBA Plan Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # create subcommand
    create_parser = subparsers.add_parser("create", help="Create a new plan")
    create_parser.add_argument("--title", required=True, help="Title of the plan")
    create_parser.add_argument("--phases", required=True, help="Comma-separated list of phase names")
    
    # check subcommand
    check_parser = subparsers.add_parser("check", help="Update a phase status to completed")
    check_parser.add_argument("--plan", required=True, help="Path to plan.md")
    check_parser.add_argument("--phase", required=True, help="Phase ID (e.g. 01)")
    check_parser.add_argument("--status", default="completed", choices=["pending", "in-progress", "completed"], help="Status target")
    
    # status subcommand
    status_parser = subparsers.add_parser("status", help="Show current plan status")
    status_parser.add_argument("--plan", required=True, help="Path to plan.md")
    
    args = parser.parse_args()
    
    if args.command == "create":
        phases = [p.strip() for p in args.phases.split(",") if p.strip()]
        sys.exit(create_plan(args.title, phases))
    elif args.command == "check":
        sys.exit(update_phase_status(args.plan, args.phase, args.status))
    elif args.command == "status":
        sys.exit(display_status(args.plan))


if __name__ == "__main__":
    main()
