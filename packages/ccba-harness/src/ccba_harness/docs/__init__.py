"""CCBA Documentation Evolution & Grounding Framework (ADR-0035, ADR-0057).

Exposes AST Code-Grounding, Pillar Balance, and DocAutoEvolutionEngine as a Deep Seam.
"""

from __future__ import annotations

from .daemon import (
    CodeGroundingEngine,
    DocAutoEvolutionEngine,
    DocEvolutionReport,
    DocHealthReport,
    GroundingCheckResult,
    PillarBalanceAuditor,
    PillarBloatInfo,
    ZeroDeletionGuard,
)

__all__ = [
    "GroundingCheckResult",
    "PillarBloatInfo",
    "DocHealthReport",
    "DocEvolutionReport",
    "CodeGroundingEngine",
    "ZeroDeletionGuard",
    "PillarBalanceAuditor",
    "DocAutoEvolutionEngine",
]
