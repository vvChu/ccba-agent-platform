"""ccba_qc_core - Core Deep Seams for CCBA AI Quality Control."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ccba_ai import AuditReportSummary
    from ccba_qc_core.discovery import (
        DiscoveryEngine,
        ProjectBackbone,
        SheetEntry,
    )
    from ccba_qc_core.jurisdiction import (
        PcccJurisdictionResult,
        PcccJurisdictionRouter,
        PcccProjectSpec,
        PcccProjectType,
    )
    from ccba_qc_core.pccc import PcccMapReduceEngine
    from ccba_qc_core.pipeline import QCAuditPipeline, QCBatchOrchestrator
    from ccba_qc_core.quadview import QuadViewAuditEngine
    from ccba_qc_core.reporter import ReporterEngine
    from ccba_qc_core.semantic import SemanticAuditEngine

__all__ = [
    "QCAuditPipeline",
    "AuditReportSummary",
    "DiscoveryEngine",
    "ProjectBackbone",
    "SheetEntry",
    "QuadViewAuditEngine",
    "SemanticAuditEngine",
    "ReporterEngine",
    "PcccMapReduceEngine",
    "QCBatchOrchestrator",
    "PcccJurisdictionRouter",
    "PcccProjectSpec",
    "PcccProjectType",
    "PcccJurisdictionResult",
]

# Unannotated ast.Assign so check_init_lazy_exports_parity inspects all keys.
_LAZY_EXPORTS = {
    "QCAuditPipeline": "ccba_qc_core.pipeline",
    "AuditReportSummary": "ccba_ai.pipeline",
    "DiscoveryEngine": "ccba_qc_core.discovery",
    "ProjectBackbone": "ccba_qc_core.discovery",
    "SheetEntry": "ccba_qc_core.discovery",
    "QuadViewAuditEngine": "ccba_qc_core.quadview",
    "SemanticAuditEngine": "ccba_qc_core.semantic",
    "ReporterEngine": "ccba_qc_core.reporter",
    "PcccMapReduceEngine": "ccba_qc_core.pccc",
    "QCBatchOrchestrator": "ccba_qc_core.pipeline",
    "PcccJurisdictionRouter": "ccba_qc_core.jurisdiction",
    "PcccProjectSpec": "ccba_qc_core.jurisdiction",
    "PcccJurisdictionResult": "ccba_qc_core.jurisdiction",
    "PcccProjectType": "ccba_qc_core.jurisdiction",
}


def __getattr__(name: str) -> Any:
    """Lazy import module-level attributes per PEP 562."""
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        mod = importlib.import_module(module_name)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose dynamic attributes to introspection and language servers per PEP 562."""
    return sorted(set(globals().keys()) | set(__all__))
