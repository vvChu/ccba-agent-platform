"""ccba_harness.evals.simulators - Modular Domain Simulators Package (ADR-0023, ADR-0057, ADR-0058).

Provides decoupled, domain-specific mock agent simulators across all 17 CCBA Domain Archetypes
coordinated by a 4-tier Dual-Dispatch engine.
"""

from __future__ import annotations

from .base import BaseDomainSimulator, SimulationContext
from .dispatcher import (
    SimulatorDispatcher,
    build_mock_agent_task,
    create_domain_mock_agent_task,
)

__all__ = [
    "BaseDomainSimulator",
    "SimulationContext",
    "SimulatorDispatcher",
    "build_mock_agent_task",
    "create_domain_mock_agent_task",
]
