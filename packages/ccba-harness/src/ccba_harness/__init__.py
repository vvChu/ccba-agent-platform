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
from .dashboard import (
    generate_swarm_dashboard_html,
    render_swarm_dashboard,
)
from .economy import (
    EconomyAuditReport,
    SkillPromptMetrics,
    TokenROIMetrics,
    analyze_skill_prompt_density,
    audit_token_economy,
    calculate_role_aware_roi,
    detect_sentence_duplicates,
    generate_prompt_pruning_report,
    scan_all_skills_economy,
)
from .evals import (
    AutoItemScorer,
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
    load_eval_dataset,
    run_eval_pipeline,
)
from .execution import DetachedExecutionEngine
from .fleet import (
    FleetTelemetryReport,
    SpokeTelemetrySummary,
    aggregate_fleet_telemetry,
    generate_fleet_dashboard_html,
    render_fleet_dashboard,
    scan_spoke_telemetry,
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
from .healing import (
    DiagnosticIssue,
    ErrorCategory,
    HealingAction,
    HealingReport,
    SelfHealingEngine,
)
from .orchestrator import EvalOrchestrator
from .skill_validator import SkillAuditIssue, SkillValidator
from .streamer import (
    AsyncTranscriptFollower,
    OfflineBufferManager,
    StreamingConfig,
    StreamingReport,
    StreamingStatus,
    TelemetryEvent,
    TelemetryEventType,
    TelemetryStreamingBridge,
)
from .telemetry import (
    OtelSpanExporter,
    SubagentSessionMetrics,
    SwarmSessionTelemetryReport,
    TokenEstimator,
    ToolCallRecord,
    TranscriptStep,
    TurnRecord,
    analyze_subagent_transcript,
    audit_swarm_session,
    check_subagent_budget,
    find_spawned_subagent_ids,
    resolve_transcript_path,
    stream_transcript_steps,
)
from .verifier import (
    CommandResult,
    PatchVerificationReport,
    resolve_preset_commands,
    verify_document_artifact,
    verify_patch_execution,
)

__all__ = [
    "verify_document_artifact",
    "resolve_preset_commands",
    "HarnessEngine",
    "HarnessGuard",
    "HarnessLocal",
    "HarnessState",
    "FileMutexLock",
    "EvalOrchestrator",
    "SkillValidator",
    "SkillAuditIssue",
    "CommandResult",
    "PatchVerificationReport",
    "verify_patch_execution",
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
    "AutoItemScorer",
    "load_eval_dataset",
    "run_eval_pipeline",
    "TokenEstimator",
    "TranscriptStep",
    "ToolCallRecord",
    "TurnRecord",
    "SubagentSessionMetrics",
    "SwarmSessionTelemetryReport",
    "OtelSpanExporter",
    "stream_transcript_steps",
    "resolve_transcript_path",
    "find_spawned_subagent_ids",
    "analyze_subagent_transcript",
    "check_subagent_budget",
    "audit_swarm_session",
    "generate_swarm_dashboard_html",
    "render_swarm_dashboard",
    "SpokeTelemetrySummary",
    "FleetTelemetryReport",
    "scan_spoke_telemetry",
    "aggregate_fleet_telemetry",
    "generate_fleet_dashboard_html",
    "render_fleet_dashboard",
    "SkillPromptMetrics",
    "TokenROIMetrics",
    "EconomyAuditReport",
    "analyze_skill_prompt_density",
    "detect_sentence_duplicates",
    "scan_all_skills_economy",
    "calculate_role_aware_roi",
    "audit_token_economy",
    "generate_prompt_pruning_report",
    # Real-Time Telemetry Streaming Bridge (Spark :8090)
    "StreamingStatus",
    "TelemetryEventType",
    "TelemetryEvent",
    "StreamingConfig",
    "StreamingReport",
    "OfflineBufferManager",
    "AsyncTranscriptFollower",
    "TelemetryStreamingBridge",
    # Autonomous Self-Healing & Closed-Loop CI Patch Engine (P4.4)
    "ErrorCategory",
    "DiagnosticIssue",
    "HealingAction",
    "HealingReport",
    "SelfHealingEngine",
    # Detached Process Execution Engine (ADR 0028 & Issue #255)
    "DetachedExecutionEngine",
]
