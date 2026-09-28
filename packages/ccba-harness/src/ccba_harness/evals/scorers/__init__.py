"""scorers/__init__.py - Public surface of the scorers package.

Re-exports 100% of the original scorers.py public API for Zero-Breaking Change compatibility.
All imports of the form `from ccba_harness.evals.scorers import ...` continue to work unchanged.
"""

from __future__ import annotations

from .base import (
    DEFAULT_SCORERS_CONFIG_PATH,
    BaseScorer,
    ScorerConfig,
    get_scorer_params,
    load_scorers_config,
    reload_scorers_config,
)
from .domain import (
    AntiDebrisScorer,
    BimClassificationScorer,
    DiagramSyntaxScorer,
    EngineeringDisciplineScorer,
    ExecutionGuardrailScorer,
    HandoffProtocolScorer,
    HardCompletionLockScorer,
    LeanStructuralScorer,
    LegalToolingIntegrityScorer,
    LegalVerbatimProvenanceScorer,
    OfficeStandardScorer,
    PcccParametricScorer,
    PlatformToolingIntegrityScorer,
    ProgressiveDisclosureScorer,
    Sha256ProvenanceScorer,
    SingleWriterInvariantScorer,
    get_academic_scorers,
    get_adr_lifecycle_scorers,
    get_bigbim_governance_scorers,
    get_bigbim_rase_scorers,
    get_bigbim_risk_scorers,
    get_bim_classification_scorers,
    get_coding_scorers,
    get_grilling_scorers,
    get_lean_structural_scorers,
    get_legal_scorers,
    get_legal_tooling_scorers,
    get_office_scorers,
    get_orchestration_scorers,
    get_pccc_scorers,
    get_platform_tooling_scorers,
    get_skill_repair_scorers,
    get_visual_design_scorers,
    get_visual_diagram_scorers,
)
from .rule_based import (
    ExactMatchScorer,
    JsonSchemaScorer,
    LengthBoundsScorer,
    RegexScorer,
)
from .semantic import LLMRubricScorer

__all__ = [
    # base
    "DEFAULT_SCORERS_CONFIG_PATH",
    "ScorerConfig",
    "BaseScorer",
    "load_scorers_config",
    "reload_scorers_config",
    "get_scorer_params",
    # rule_based
    "ExactMatchScorer",
    "RegexScorer",
    "LengthBoundsScorer",
    "JsonSchemaScorer",
    # semantic
    "LLMRubricScorer",
    # domain - scorers
    "SingleWriterInvariantScorer",
    "ProgressiveDisclosureScorer",
    "HandoffProtocolScorer",
    "HardCompletionLockScorer",
    "EngineeringDisciplineScorer",
    "AntiDebrisScorer",
    "LeanStructuralScorer",
    "LegalVerbatimProvenanceScorer",
    "LegalToolingIntegrityScorer",
    "Sha256ProvenanceScorer",
    "PlatformToolingIntegrityScorer",
    "ExecutionGuardrailScorer",
    "OfficeStandardScorer",
    "DiagramSyntaxScorer",
    "PcccParametricScorer",
    "BimClassificationScorer",
    # domain - factory functions
    "get_orchestration_scorers",
    "get_coding_scorers",
    "get_lean_structural_scorers",
    "get_legal_scorers",
    "get_legal_tooling_scorers",
    "get_platform_tooling_scorers",
    "get_office_scorers",
    "get_visual_diagram_scorers",
    "get_pccc_scorers",
    "get_bim_classification_scorers",
    "get_academic_scorers",
    "get_bigbim_risk_scorers",
    "get_bigbim_governance_scorers",
    "get_bigbim_rase_scorers",
    "get_grilling_scorers",
    "get_adr_lifecycle_scorers",
    "get_skill_repair_scorers",
    "get_visual_design_scorers",
]
