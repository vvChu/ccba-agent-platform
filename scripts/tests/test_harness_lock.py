"""Unit tests for safe single-instance process lock in run_harness_evals.py."""

import os

from scripts.eval.process_safety import ensure_single_instance


def test_ensure_single_instance_safe_execution():
    """Verify ensure_single_instance runs without throwing exceptions and preserves self/parent process."""
    current_pid = os.getpid()
    parent_pid = getattr(os, "getppid", lambda: None)()

    # Execute lock check
    ensure_single_instance("test_keyword")

    # Verify self and parent process remain intact
    assert os.getpid() == current_pid
    if parent_pid:
        assert getattr(os, "getppid", lambda: None)() == parent_pid
