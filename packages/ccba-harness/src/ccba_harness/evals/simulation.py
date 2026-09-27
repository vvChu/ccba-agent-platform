"""ccba_harness.evals.simulation - Grounded Domain Simulation Facade (ADR-0023, ADR-0057, ADR-0058).

This module is a backwards-compatible facade delegating to the modular simulators package:
`ccba_harness.evals.simulators`.

All domain-specific simulation logic has been decomposed into decoupled domain simulators
across all 17 CCBA Domain Archetypes coordinated via a 4-tier Dual-Dispatch engine.
"""

from __future__ import annotations

from .simulators import (
    build_mock_agent_task,
    create_domain_mock_agent_task,
)

__all__ = [
    "build_mock_agent_task",
    "create_domain_mock_agent_task",
]
