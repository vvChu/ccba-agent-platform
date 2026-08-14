"""CCBA Process Safety & Evaluation Infrastructure Package.

Provides core primitives for safe detached execution, singleton locking,
process tree termination, and automated evaluation gates.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from .process_safety import (
    DetachedExecutionEngine,
    ensure_single_instance,
    get_venv_python,
    kill_process_tree,
)
from .run_harness_evals import (
    check_pre_eval_health,
    get_git_modified_files,
)
from .run_safe_eval_wrapper import (
    extract_culprit_file,
    extract_failed_gate,
    extract_summary_traceback,
)

__all__ = [
    "DetachedExecutionEngine",
    "ensure_single_instance",
    "kill_process_tree",
    "get_venv_python",
    "check_pre_eval_health",
    "get_git_modified_files",
    "extract_summary_traceback",
    "extract_failed_gate",
    "extract_culprit_file",
]
