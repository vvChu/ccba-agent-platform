"""CCBA Evals Framework — Public Interface for Evaluation Benchmarks & Scorers.

Provides local-first evaluation runners, code-based scorers, and model-based rubric judges.
"""

from __future__ import annotations

from .daemon import (
    NightlyDaemonReport,
    NightlyTunerDaemon,
    SkillEvolutionSummary,
    WeightedPriorityQueue,
    send_telegram_alert,
)
from .legal_index import (
    DEFAULT_FLAT_INDEX_PATH,
    LegalFlatIndex,
    StatutoryDocument,
    load_legal_flat_index,
)
from .miner import (
    classify_target_skill,
    generate_eval_spec_item,
    identify_failures,
    mine_logs_and_export,
    parse_transcript_logs,
    redact_sensitive_info,
)
from .models import EvalItem, EvalItemResult, EvalReport, ScoreResult
from .runner import AutoItemScorer, EvalRunner, load_eval_dataset, run_eval_pipeline
from .scorers import (
    AntiDebrisScorer,
    BaseScorer,
    EngineeringDisciplineScorer,
    ExactMatchScorer,
    HardCompletionLockScorer,
    JsonSchemaScorer,
    LeanStructuralScorer,
    LegalVerbatimProvenanceScorer,
    LengthBoundsScorer,
    LLMRubricScorer,
    RegexScorer,
    get_coding_scorers,
    get_lean_structural_scorers,
    get_legal_scorers,
)
from .tuner import (
    CODING_ARCHETYPE_KEYWORDS,
    AdaptiveRateLimiter,
    GitRatchetOptimizer,
    GitRatchetTuner,
    RatchetConfig,
    RatchetReport,
    RatchetTrialResult,
    RateLimiter,
    get_default_domain_scorers,
    mutate_skill,
    preserve_yaml_frontmatter,
)

__all__ = [
    "CODING_ARCHETYPE_KEYWORDS",
    "mutate_skill",
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
    "HardCompletionLockScorer",
    "EngineeringDisciplineScorer",
    "AntiDebrisScorer",
    "LeanStructuralScorer",
    "LegalVerbatimProvenanceScorer",
    "get_coding_scorers",
    "get_lean_structural_scorers",
    "get_legal_scorers",
    "EvalRunner",
    "AutoItemScorer",
    "load_eval_dataset",
    "run_eval_pipeline",
    "RatchetConfig",
    "RatchetTrialResult",
    "RatchetReport",
    "preserve_yaml_frontmatter",
    "get_default_domain_scorers",
    "GitRatchetOptimizer",
    "GitRatchetTuner",
    "RateLimiter",
    "AdaptiveRateLimiter",
    "NightlyDaemonReport",
    "NightlyTunerDaemon",
    "SkillEvolutionSummary",
    "WeightedPriorityQueue",
    "send_telegram_alert",
    "classify_target_skill",
    "generate_eval_spec_item",
    "identify_failures",
    "mine_logs_and_export",
    "parse_transcript_logs",
    "redact_sensitive_info",
    "DEFAULT_FLAT_INDEX_PATH",
    "StatutoryDocument",
    "LegalFlatIndex",
    "load_legal_flat_index",
]
