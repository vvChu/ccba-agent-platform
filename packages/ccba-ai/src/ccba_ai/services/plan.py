"""
Service module for managing file-based plans and phase status synchronization.
Provides clean, structured API for both CLI wrapper and MCP server.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path

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


def create_plan(title: str, phases_list: list[str], workspace_root: Path | None = None) -> dict:
    """Create a new plan directory with plan.md and phase markdown stubs.

    Args:
        title: Title of the plan.
        phases_list: List of phase names.
        workspace_root: Optional custom workspace root path (default: current working directory).

    Returns:
        A dictionary containing the status and created plan folder details.
        
    Raises:
        FileExistsError: If the plan folder already exists.
    """
    root = workspace_root or Path.cwd()
    plans_dir = root / "plans"
    plans_dir.mkdir(exist_ok=True)

    # Get current date in YYMMDD format
    date_str = datetime.now().strftime("%y%m%d")
    slug = slugify(title)
    plan_folder = plans_dir / f"{date_str}-{slug}"

    if plan_folder.exists():
        raise FileExistsError(f"Plan folder {plan_folder.relative_to(root)} already exists.")

    plan_folder.mkdir(parents=True, exist_ok=True)

    # Get active git branch
    branch = "main"
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True
        )
        branch = res.stdout.strip()
    except Exception:
        pass

    # Generate phase rows and create phase files
    phases_rows = []
    created_files = []
    
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
        created_files.append(str(phase_filepath.relative_to(root)))

        # Append to table row
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
    created_files.append(str(plan_filepath.relative_to(root)))

    return {
        "status": "success",
        "plan_title": title,
        "plan_folder": str(plan_folder.relative_to(root)),
        "plan_file": str(plan_filepath.relative_to(root)),
        "created_files": created_files
    }


def update_phase_status(plan_file: str | Path, phase_id: str, status: str, workspace_root: Path | None = None) -> dict:
    """Update a phase status in both plan.md and the corresponding phase file.

    Args:
        plan_file: Path to plan.md file.
        phase_id: Phase ID (e.g. '01', '02').
        status: New status target ('pending', 'in-progress', 'completed').
        workspace_root: Optional custom workspace root path.

    Returns:
        A dictionary describing the updated status.

    Raises:
        FileNotFoundError: If the plan file or phase file is not found.
        ValueError: If phase ID is not found in the plan table.
    """
    root = workspace_root or Path.cwd()
    plan_path = Path(plan_file)
    if not plan_path.is_absolute():
        plan_path = root / plan_path

    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file {plan_file} not found.")

    content = plan_path.read_text(encoding="utf-8")

    # Find phase in the Markdown table
    pattern = r"\|\s*" + phase_id + r"\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
    match = re.search(pattern, content)
    if not match:
        raise ValueError(f"Phase ID {phase_id} not found in plan table of {plan_path.name}.")

    phase_name = match.group(1).strip()
    old_status = match.group(2).strip()
    phase_filename = match.group(3).strip()

    # 1. Update status in plan.md table
    updated_row = f"| {phase_id} | {phase_name} | {status} | {phase_filename} |"
    new_content = re.sub(pattern, updated_row, content)
    plan_path.write_text(new_content, encoding="utf-8")

    # 2. Update status in phase-XX-*.md file
    phase_file_path = plan_path.parent / phase_filename
    phase_file_updated = False
    
    if phase_file_path.exists():
        p_content = phase_file_path.read_text(encoding="utf-8")
        p_updated = re.sub(r"status:\s*\w+", f"status: {status}", p_content)
        phase_file_path.write_text(p_updated, encoding="utf-8")
        phase_file_updated = True
    else:
        # Warning but not hard failure
        pass

    return {
        "status": "success",
        "phase_id": phase_id,
        "phase_name": phase_name,
        "old_status": old_status,
        "new_status": status,
        "plan_file": str(plan_path.relative_to(root) if plan_path.is_relative_to(root) else plan_path),
        "phase_file": phase_filename,
        "phase_file_updated": phase_file_updated
    }


def get_plan_status(plan_file: str | Path, workspace_root: Path | None = None) -> dict:
    """Parse and return the plan status.

    Args:
        plan_file: Path to plan.md file.
        workspace_root: Optional custom workspace root path.

    Returns:
        A dictionary containing parsed plan title, metadata and list of phases.

    Raises:
        FileNotFoundError: If the plan file is not found.
    """
    root = workspace_root or Path.cwd()
    plan_path = Path(plan_file)
    if not plan_path.is_absolute():
        plan_path = root / plan_path

    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file {plan_file} not found.")

    content = plan_path.read_text(encoding="utf-8")
    
    # Parse title
    title_match = re.search(r"^#\s+Plan:\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else plan_path.parent.name
    
    # Parse metadata
    branch_match = re.search(r"^>\s*Branch:\s*(.+)$", content, re.MULTILINE)
    date_match = re.search(r"^>\s*Date:\s*(.+)$", content, re.MULTILINE)
    status_match = re.search(r"^>\s*Status:\s*(.+)$", content, re.MULTILINE)
    
    metadata = {
        "branch": branch_match.group(1).strip() if branch_match else "unknown",
        "date": date_match.group(1).strip() if date_match else "unknown",
        "status": status_match.group(1).strip() if status_match else "unknown",
    }
    
    # Parse table rows for phases
    phases = []
    lines = content.splitlines()
    in_table = False
    
    for line in lines:
        if "| Phase |" in line:
            in_table = True
            continue
        if in_table and line.startswith("|-"):
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                phases.append({
                    "id": parts[0],
                    "name": parts[1],
                    "status": parts[2],
                    "file": parts[3]
                })

    return {
        "title": title,
        "metadata": metadata,
        "phases": phases,
        "plan_file": str(plan_path.relative_to(root) if plan_path.is_relative_to(root) else plan_path)
    }
