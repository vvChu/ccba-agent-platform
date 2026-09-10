"""ccba_qc_core - Core Deep Seams for CCBA AI Quality Control."""

from __future__ import annotations

from ccba_pdf_prep import PDFAnalyzer, TitleBlockDetector
from ccba_qc_core.discovery import (
    DiscoveryEngine,
    ProjectBackbone,
    SheetEntry,
)
from ccba_qc_core.pccc import PcccMapReduceEngine
from ccba_qc_core.pipeline import QCBatchOrchestrator
from ccba_qc_core.quadview import QuadViewAuditEngine
from ccba_qc_core.reporter import ReporterEngine
from ccba_qc_core.semantic import SemanticAuditEngine

__all__ = [
    "DiscoveryEngine",
    "PDFAnalyzer",
    "TitleBlockDetector",
    "ProjectBackbone",
    "SheetEntry",
    "QuadViewAuditEngine",
    "SemanticAuditEngine",
    "ReporterEngine",
    "PcccMapReduceEngine",
    "QCBatchOrchestrator",
]
