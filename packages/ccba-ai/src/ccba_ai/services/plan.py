"""
Service module for managing file-based plans and phase status synchronization.
Provides clean, structured API for both CLI wrapper and MCP server.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from ccba_ai.models import (
    PhaseUpdateResult,
    PlanCreationResult,
    PlanPhaseData,
    PlanStatusResult,
)

try:
    from ccba_harness import FileMutexLock
except ImportError:
    from ccba_ai.services._lock_fallback import SimpleFileLock as FileMutexLock

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


class Phase:
    """Domain model representing a single phase in the plan."""

    def __init__(
        self,
        num: str,
        name: str,
        status: str,
        filename: str,
        content: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.num = num
        self.name = name
        self.status = status
        self.filename = filename
        self.content = content or ""
        self.metadata = metadata or {}

    @classmethod
    def from_file(cls, path: Path, num: str, name: str, status: str, filename: str) -> "Phase":
        """Loads a Phase from its Markdown file if it exists, otherwise returns a default Phase stub."""
        if not path.exists():
            return cls(num, name, status, filename)

        full_content = path.read_text(encoding="utf-8")

        meta = {}
        body = full_content
        if full_content.startswith("---"):
            fm_match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", full_content, re.DOTALL)
            if fm_match:
                yaml_block = fm_match.group(1)
                try:
                    meta = yaml.safe_load(yaml_block) or {}
                except Exception:
                    pass
                body = full_content[fm_match.end() :]

        # Use status from frontmatter as source of truth if available
        file_status = meta.get("status", status)
        return cls(num, name, file_status, filename, body, meta)

    def update_status(self, status: str) -> None:
        """Updates the status of this phase."""
        self.status = status
        self.metadata["status"] = status

    def save(self, dir_path: Path) -> None:
        """Saves the Phase back to disk. Preserves file formatting if file already exists."""
        file_path = dir_path / self.filename

        if file_path.exists():
            # Target Line Override: only update the status line in frontmatter
            content = file_path.read_text(encoding="utf-8")
            # Pattern to match: status: <word> inside the frontmatter
            fm_match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", content, re.DOTALL)
            if fm_match:
                frontmatter = fm_match.group(1)
                # Replace only status line
                new_fm = re.sub(
                    r"^status:\s*\w+", f"status: {self.status}", frontmatter, flags=re.MULTILINE
                )
                updated_content = content[: fm_match.start(1)] + new_fm + content[fm_match.end(1) :]
                file_path.write_text(updated_content, encoding="utf-8")
                return

        # Otherwise, full write
        # Generate clean metadata
        meta = {
            "phase": int(self.num),
            "title": self.name,
            "status": self.status,
            "priority": self.metadata.get("priority", "P2"),
            "dependencies": self.metadata.get(
                "dependencies", "[]" if int(self.num) == 1 else f"[phase-{(int(self.num) - 1):02d}]"
            ),
        }

        # Build frontmatter string cleanly
        fm_lines = ["---"]
        for k, v in meta.items():
            if k == "title":
                fm_lines.append(f'{k}: "{v}"')
            else:
                fm_lines.append(f"{k}: {v}")
        fm_lines.append("---")
        frontmatter = "\n".join(fm_lines)

        body = self.content
        if not body.strip():
            body = f"\n# Phase {int(self.num)}: {self.name}\n\n## Overview\nBrief objective of this phase.\n\n## Tasks\n- [ ] Task 1\n- [ ] Task 2\n\n## Success Criteria\n- [ ] Criteria 1\n"

        file_path.write_text(f"{frontmatter}\n{body}", encoding="utf-8")


class Plan:
    """Domain model representing a multi-phase implementation plan."""

    def __init__(
        self, title: str, branch: str, date: str, status: str, phases: list[Phase], file_path: Path
    ) -> None:
        self.title = title
        self.branch = branch
        self.date = date
        self.status = status
        self.phases = phases
        self.file_path = file_path

    @classmethod
    def from_file(cls, file_path: Path) -> "Plan":
        """Loads a Plan and all its phases from files."""
        if not file_path.exists():
            raise FileNotFoundError(f"Plan file {file_path} not found.")

        content = file_path.read_text(encoding="utf-8")

        # Parse title
        title_match = re.search(r"^#\s+Plan:\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else file_path.parent.name

        # Parse metadata
        branch_match = re.search(r"^>\s*Branch:\s*(.+)$", content, re.MULTILINE)
        date_match = re.search(r"^>\s*Date:\s*(.+)$", content, re.MULTILINE)
        status_match = re.search(r"^>\s*Status:\s*(.+)$", content, re.MULTILINE)

        branch = branch_match.group(1).strip() if branch_match else "unknown"
        date = date_match.group(1).strip() if date_match else "unknown"
        status = status_match.group(1).strip() if status_match else "unknown"

        # Parse phases from the Markdown table
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
                    p_id = parts[0]
                    p_name = parts[1]
                    p_status = parts[2]
                    p_file = parts[3]

                    # Load Phase object
                    phase_path = file_path.parent / p_file
                    phase_obj = Phase.from_file(phase_path, p_id, p_name, p_status, p_file)
                    phases.append(phase_obj)

        return cls(title, branch, date, status, phases, file_path)

    def get_phase(self, phase_id: str) -> Phase | None:
        """Finds a phase by its ID/number (e.g. '01')."""
        for p in self.phases:
            if p.num == phase_id:
                return p
        return None

    def to_markdown(self) -> str:
        """Renders the Plan model back to plan.md content."""
        phase_rows = []
        for p in self.phases:
            phase_rows.append(f"| {p.num} | {p.name} | {p.status} | {p.filename} |")

        return PLAN_TEMPLATE.format(
            title=self.title, branch=self.branch, date=self.date, phases_rows="\n".join(phase_rows)
        )

    def save(self) -> None:
        """Saves the Plan file to disk using FileMutexLock protection."""
        lock_file = self.file_path.with_name(".plan.lock")
        with FileMutexLock(lock_file):
            self.file_path.write_text(self.to_markdown(), encoding="utf-8")


def slugify(text: str) -> str:
    """Convert text to lower-case kebab-case slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def create_plan(
    title: str, phases_list: list[str], workspace_root: Path | None = None
) -> PlanCreationResult:
    """Create a new plan directory with plan.md and phase markdown stubs."""
    root = workspace_root or Path.cwd()
    plans_dir = root / "plans"
    plans_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%y%m%d")
    slug = slugify(title)
    plan_folder = plans_dir / f"{date_str}-{slug}"

    if plan_folder.exists():
        raise FileExistsError(f"Plan folder {plan_folder.relative_to(root)} already exists.")

    plan_folder.mkdir(parents=True, exist_ok=True)

    branch = "main"
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        branch = res.stdout.strip()
    except Exception:
        pass

    phases = []
    created_files = []

    for idx, phase_name in enumerate(phases_list, 1):
        phase_num = f"{idx:02d}"
        phase_slug = slugify(phase_name)
        phase_filename = f"phase-{phase_num}-{phase_slug}.md"

        phase_obj = Phase(num=phase_num, name=phase_name, status="pending", filename=phase_filename)
        phase_obj.save(plan_folder)
        phases.append(phase_obj)
        created_files.append(str((plan_folder / phase_filename).relative_to(root)))

    plan_filepath = plan_folder / "plan.md"
    plan_obj = Plan(
        title=title,
        branch=branch,
        date=datetime.now().strftime("%Y-%m-%d"),
        status="in-progress",
        phases=phases,
        file_path=plan_filepath,
    )
    plan_obj.save()
    created_files.append(str(plan_filepath.relative_to(root)))

    return PlanCreationResult(
        status="success",
        plan_title=title,
        plan_folder=str(plan_folder.relative_to(root)),
        plan_file=str(plan_filepath.relative_to(root)),
        created_files=created_files,
    )


def update_phase_status(
    plan_file: str | Path, phase_id: str, status: str, workspace_root: Path | None = None
) -> PhaseUpdateResult:
    """Update a phase status in both plan.md and the corresponding phase file."""
    root = workspace_root or Path.cwd()
    plan_path = Path(plan_file)
    if not plan_path.is_absolute():
        plan_path = root / plan_path

    # Load using Plan OOP
    plan_obj = Plan.from_file(plan_path)

    phase_obj = plan_obj.get_phase(phase_id)
    if not phase_obj:
        raise ValueError(f"Phase ID {phase_id} not found in plan table of {plan_path.name}.")

    old_status = phase_obj.status
    phase_obj.update_status(status)

    # Save both
    plan_obj.save()

    phase_file_path = plan_path.parent / phase_obj.filename
    phase_file_updated = False
    if phase_file_path.exists():
        phase_obj.save(plan_path.parent)
        phase_file_updated = True

    return PhaseUpdateResult(
        status="success",
        phase_id=phase_id,
        phase_name=phase_obj.name,
        old_status=old_status,
        new_status=status,
        plan_file=str(plan_path.relative_to(root) if plan_path.is_relative_to(root) else plan_path),
        phase_file=phase_obj.filename,
        phase_file_updated=phase_file_updated,
    )


def get_plan_status(plan_file: str | Path, workspace_root: Path | None = None) -> PlanStatusResult:
    """Parse and return the plan status."""
    root = workspace_root or Path.cwd()
    plan_path = Path(plan_file)
    if not plan_path.is_absolute():
        plan_path = root / plan_path

    # Load using Plan OOP
    plan_obj = Plan.from_file(plan_path)

    metadata = {
        "branch": plan_obj.branch,
        "date": plan_obj.date,
        "status": plan_obj.status,
    }

    phases_data = []
    for p in plan_obj.phases:
        phases_data.append(PlanPhaseData(id=p.num, name=p.name, status=p.status, file=p.filename))

    return PlanStatusResult(
        title=plan_obj.title,
        metadata=metadata,
        phases=phases_data,
        plan_file=str(plan_path.relative_to(root) if plan_path.is_relative_to(root) else plan_path),
    )
