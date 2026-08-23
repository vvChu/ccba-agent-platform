"""CCBA Legislative Consolidator Package — Deterministic Legal Document Patching & VBHN Generation."""

from .dual_mode_parser import (
    ASTNode,
    DualModeASTParser,
)
from .manifest_generator import (
    ManifestGenerator,
)
from .patch_manifest_schema import (
    DefectSeverity,
    DocMode,
    PatchAction,
    PatchItem,
    PatchManifest,
    load_manifest,
)
from .patcher import (
    ConsolidationResult,
    LegislativeConsolidator,
)

__all__ = [
    "DocMode",
    "DefectSeverity",
    "PatchAction",
    "PatchItem",
    "PatchManifest",
    "load_manifest",
    "ASTNode",
    "DualModeASTParser",
    "ConsolidationResult",
    "LegislativeConsolidator",
    "ManifestGenerator",
]
