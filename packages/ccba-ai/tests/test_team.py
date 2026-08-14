"""
Unit tests for team task coordination service in ccba_ai.services.team.
"""

from pathlib import Path

import pytest

from ccba_ai.models import TeamTask
from ccba_ai.services.team import add_task, claim_task, complete_task, load_tasks, save_tasks


def test_team_task_lifecycle(tmp_path: Path):
    # 1. Add Task
    t1 = add_task("Audit Phase 1", owner=None, workspace_root=tmp_path)
    assert isinstance(t1, TeamTask)
    assert t1.name == "Audit Phase 1"
    assert t1.owner == "None"
    assert t1.status == "pending"

    # 2. Duplicate error
    with pytest.raises(ValueError, match="already exists"):
        add_task("Audit Phase 1", workspace_root=tmp_path)

    # 3. Load tasks
    tasks = load_tasks(tmp_path)
    assert len(tasks) == 1
    assert isinstance(tasks[0], TeamTask)
    assert tasks[0].name == "Audit Phase 1"

    # 4. Claim Task
    t_claimed = claim_task("Audit Phase 1", owner="Alice", workspace_root=tmp_path)
    assert isinstance(t_claimed, TeamTask)
    assert t_claimed.owner == "Alice"
    assert t_claimed.status == "in-progress"

    # 5. Complete Task
    t_done = complete_task("Audit Phase 1", workspace_root=tmp_path)
    assert isinstance(t_done, TeamTask)
    assert t_done.status == "completed"

    # 6. Re-claim completed task raises error
    with pytest.raises(ValueError, match="already completed"):
        claim_task("Audit Phase 1", owner="Bob", workspace_root=tmp_path)


def test_save_tasks_mixed_types(tmp_path: Path):
    mixed = [
        TeamTask(name="Task A", owner="Alice", status="completed"),
        {"name": "Task B", "owner": "Bob", "status": "pending"},
    ]
    save_tasks(mixed, workspace_root=tmp_path)

    loaded = load_tasks(tmp_path)
    assert len(loaded) == 2
    assert all(isinstance(t, TeamTask) for t in loaded)
    assert loaded[0].name == "Task A"
    assert loaded[1].name == "Task B"
