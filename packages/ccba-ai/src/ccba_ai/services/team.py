"""
Service module for managing a shared, file-based JSON task database for multi-agent coordination.
Provides structured API for both CLI wrapper and MCP server.
"""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ccba_ai.models import TeamTask

try:
    from ccba_harness import FileMutexLock
except ImportError:
    from ccba_ai.services._lock_fallback import SimpleFileLock

    FileMutexLock = SimpleFileLock  # type: ignore[misc,assignment]


def _get_db_file(workspace_root: Path | None = None) -> Path:
    """Get path to the team_tasks.json file."""
    root = workspace_root or Path.cwd()
    return root / ".md" / "data" / "team_tasks.json"


def load_tasks(workspace_root: Path | None = None) -> list[TeamTask]:
    """Load tasks from the shared JSON database.

    Args:
        workspace_root: Optional custom workspace root path.

    Returns:
        List of TeamTask models.
    """
    db_file = _get_db_file(workspace_root)
    if not db_file.exists():
        db_file.parent.mkdir(parents=True, exist_ok=True)
        save_tasks([], workspace_root)
        return []
    try:
        with open(db_file, encoding="utf-8") as f:
            raw_data = json.load(f)
            return [TeamTask(**item) if isinstance(item, dict) else item for item in raw_data]
    except Exception:
        return []


def save_tasks(
    tasks: Sequence[TeamTask | dict[str, Any]], workspace_root: Path | None = None
) -> None:
    """Save tasks to the shared JSON database.

    Args:
        tasks: List of TeamTask objects or dicts to save.
        workspace_root: Optional custom workspace root path.
    """
    db_file = _get_db_file(workspace_root)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    serialized = [t.model_dump() if isinstance(t, TeamTask) else t for t in tasks]
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2, ensure_ascii=False)


def add_task(name: str, owner: str | None = None, workspace_root: Path | None = None) -> TeamTask:
    """Add a new task to the database.

    Args:
        name: Name of the task.
        owner: Optional owner name.
        workspace_root: Optional custom workspace root path.

    Returns:
        The newly added TeamTask.

    Raises:
        ValueError: If a task with the same name already exists.
    """
    db_file = _get_db_file(workspace_root)
    lock_file = db_file.with_suffix(".lock")
    with FileMutexLock(lock_file):
        tasks = load_tasks(workspace_root)
        # Check duplicate
        if any(t.name == name for t in tasks):
            raise ValueError(f"Task '{name}' already exists.")

        new_task = TeamTask(
            name=name,
            owner=owner or "None",
            status="pending" if not owner else "in-progress",
        )
        tasks.append(new_task)
        save_tasks(tasks, workspace_root)
        return new_task


def claim_task(name: str, owner: str, workspace_root: Path | None = None) -> TeamTask:
    """Claim a task for execution.

    Args:
        name: Name of the task.
        owner: Owner claiming the task.
        workspace_root: Optional custom workspace root path.

    Returns:
        The updated TeamTask details.

    Raises:
        FileNotFoundError: If the task is not found.
        ValueError: If the task is already completed.
    """
    db_file = _get_db_file(workspace_root)
    lock_file = db_file.with_suffix(".lock")
    with FileMutexLock(lock_file):
        tasks = load_tasks(workspace_root)
        for t in tasks:
            if t.name == name:
                if t.status == "completed":
                    raise ValueError(f"Task '{name}' is already completed.")
                t.owner = owner
                t.status = "in-progress"
                save_tasks(tasks, workspace_root)
                return t

        raise FileNotFoundError(f"Task '{name}' not found.")


def complete_task(name: str, workspace_root: Path | None = None) -> TeamTask:
    """Mark a task as completed.

    Args:
        name: Name of the task.
        workspace_root: Optional custom workspace root path.

    Returns:
        The updated TeamTask details.

    Raises:
        FileNotFoundError: If the task is not found.
    """
    db_file = _get_db_file(workspace_root)
    lock_file = db_file.with_suffix(".lock")
    with FileMutexLock(lock_file):
        tasks = load_tasks(workspace_root)
        for t in tasks:
            if t.name == name:
                t.status = "completed"
                save_tasks(tasks, workspace_root)
                return t

        raise FileNotFoundError(f"Task '{name}' not found.")
