"""CCBA Harness package — public re-export surface.

This file is intentionally a thin wrapper. All implementation lives in
the private sub-modules:

  _engine.py          — shared mutable state, monitors & hook engines
  _guard.py           — HarnessGuard class public interface

Only public symbols are re-exported here. Internal symbols (_prefixed)
remain private to the package. Tests that need internal access should
import directly from the sub-module (e.g. from ccba_harness._engine import _local).
"""

# ruff: noqa: F401
from __future__ import annotations

import subprocess  # needed as patch target for tests

# Public API re-exports
from ._engine import HarnessEngine
from ._guard import HarnessGuard
from ._mutex import FileMutexLock
from ._state import HarnessLocal, HarnessState
from .evals import (
    BaseScorer,
    EvalItem,
    EvalItemResult,
    EvalReport,
    EvalRunner,
    ExactMatchScorer,
    JsonSchemaScorer,
    LengthBoundsScorer,
    LLMRubricScorer,
    RegexScorer,
    ScoreResult,
)
from .gpi import (
    GPI_STANDALONE_THRESHOLD,
    MAX_METRIC_SCORE,
    MIN_METRIC_SCORE,
    WEIGHT_AUTONOMOUS_INVOCATION_A,
    WEIGHT_INTERFACE_COMPLEXITY_K,
    WEIGHT_PARENT_COUPLING_P,
    WEIGHT_REASONING_STEPS_S,
    ArchitectureTier,
    DecisionRequest,
    DecisionResult,
    GPIMetrics,
    calculate_gpi,
    evaluate_two_stage_decision,
)
from .orchestrator import EvalOrchestrator
from .skill_validator import SkillAuditIssue, SkillValidator

__all__ = [
    "HarnessEngine",
    "HarnessGuard",
    "HarnessLocal",
    "HarnessState",
    "FileMutexLock",
    "EvalOrchestrator",
    "SkillValidator",
    "SkillAuditIssue",
    "ArchitectureTier",
    "GPIMetrics",
    "DecisionRequest",
    "DecisionResult",
    "calculate_gpi",
    "evaluate_two_stage_decision",
    "GPI_STANDALONE_THRESHOLD",
    "WEIGHT_REASONING_STEPS_S",
    "WEIGHT_INTERFACE_COMPLEXITY_K",
    "WEIGHT_AUTONOMOUS_INVOCATION_A",
    "WEIGHT_PARENT_COUPLING_P",
    "MIN_METRIC_SCORE",
    "MAX_METRIC_SCORE",
    "EvalItem",
    "ScoreResult",
    "EvalItemResult",
    "EvalReport",
    "BaseScorer",
    "ExactMatchScorer",
    "RegexScorer",
    "LengthBoundsScorer",
    "JsonSchemaScorer",
    "LLMRubricScorer",
    "EvalRunner",
]
