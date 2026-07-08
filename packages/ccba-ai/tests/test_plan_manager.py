import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from ccba_harness import FileMutexLock
from ccba_ai.services.plan import (
    Phase,
    create_plan,
    get_plan_status,
    update_phase_status,
)


def test_file_lock_basic():
    with TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / ".test.lock"

        # Lock acquisition
        with FileMutexLock(lock_file) as lock1:
            assert lock1.is_locked
            assert lock_file.exists()

            # Second acquisition should fail / timeout
            with pytest.raises(TimeoutError):
                with FileMutexLock(lock_file, timeout=0.2, retry_interval=0.05):
                    pass

        # Lock file should be cleaned up
        assert not lock_file.exists()


def test_file_lock_concurrent():
    with TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / ".test.lock"
        shared_resource = []
        errors = []

        def worker(worker_id):
            try:
                with FileMutexLock(lock_file, timeout=2.0):
                    # Simulate critical section
                    shared_resource.append(worker_id)
                    time.sleep(0.1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(shared_resource) == 3


def test_phase_parsing_and_saving():
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        phase_file = tmp_path / "phase-01-test.md"

        # 1. Stub creation
        phase = Phase(num="01", name="Init Project", status="pending", filename="phase-01-test.md")
        phase.save(tmp_path)
        assert phase_file.exists()

        # 2. Reload and verify yaml frontmatter
        reloaded = Phase.from_file(phase_file, "01", "Init Project", "pending", "phase-01-test.md")
        assert reloaded.status == "pending"
        assert reloaded.metadata["priority"] == "P2"

        # 3. Add custom comments to the frontmatter manually to test formatting preservation
        content = phase_file.read_text(encoding="utf-8")
        custom_content = content.replace(
            "priority: P2", "priority: P2\n# User custom comment here\ncustom_field: value"
        )
        phase_file.write_text(custom_content, encoding="utf-8")

        # Reload, update status and save
        phase_to_update = Phase.from_file(
            phase_file, "01", "Init Project", "pending", "phase-01-test.md"
        )
        phase_to_update.update_status("in-progress")
        phase_to_update.save(tmp_path)

        # Verify the target line was overwritten, but comments and custom_field remain intact
        updated_content = phase_file.read_text(encoding="utf-8")
        assert "status: in-progress" in updated_content
        assert "# User custom comment here" in updated_content
        assert "custom_field: value" in updated_content
        assert "priority: P2" in updated_content


def test_plan_lifecycle_and_compatibility():
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Create plan
        res = create_plan(
            title="Refactor Platform", phases_list=["Phase A", "Phase B"], workspace_root=tmp_path
        )
        assert res["status"] == "success"
        plan_file = tmp_path / res["plan_file"]
        assert plan_file.exists()

        # 2. Read plan status
        status = get_plan_status(plan_file, workspace_root=tmp_path)
        assert status["title"] == "Refactor Platform"
        assert len(status["phases"]) == 2
        assert status["phases"][0]["status"] == "pending"
        assert status["phases"][0]["name"] == "Phase A"

        # 3. Update phase status
        update_res = update_phase_status(
            plan_file=plan_file, phase_id="01", status="completed", workspace_root=tmp_path
        )
        assert update_res["status"] == "success"
        assert update_res["old_status"] == "pending"
        assert update_res["new_status"] == "completed"

        # Verify both files are updated
        new_status = get_plan_status(plan_file, workspace_root=tmp_path)
        assert new_status["phases"][0]["status"] == "completed"

        phase_file = plan_file.parent / new_status["phases"][0]["file"]
        assert phase_file.exists()
        assert "status: completed" in phase_file.read_text(encoding="utf-8")
