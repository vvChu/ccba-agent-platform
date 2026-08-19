"""CCBA Legislative Consolidator Package — Deterministic Legal Document Patching & VBHN Generation."""

from .patch_manifest_schema import (
    DocMode,
    PatchAction,
    PatchItem,
    PatchManifest,
    load_manifest,
)
from .dual_mode_parser import (
    ASTNode,
    DualModeASTParser,
)
from .patcher import (
    ConsolidationResult,
    LegislativeConsolidator,
)
from .manifest_generator import (
    ManifestGenerator,
)

__all__ = [
    "DocMode",
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
