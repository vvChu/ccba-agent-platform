"""dispatcher.py - Multi-Tier Modular Dispatcher for Domain Simulation.

Coordinates domain-specific mock agent simulators using a 4-tier fallback cascade:
1. Tier 1: Primary SSOT resolution via resolve_domain_archetype(skill_name) -> Zero Prompt Hijacking.
2. Tier 2: Item metadata target routing (target_archetype / target_skill).
3. Tier 3: Content / Prompt domain anchor matching (for legacy tests with empty skill_name).
4. Tier 4: Fallback generic response (item golden_answer or lean structural scaffolding).
"""

from __future__ import annotations

from collections.abc import Callable

from ..archetypes import resolve_domain_archetype
from ..models import EvalItem
from .academic import AcademicDomainSimulator
from .adr import AdrLifecycleDomainSimulator
from .base import BaseDomainSimulator, SimulationContext
from .bim_classification import BimClassificationDomainSimulator
from .bim_governance import BimGovernanceDomainSimulator
from .bim_rase import BimRaseDomainSimulator
from .bim_risk import BimRiskDomainSimulator
from .coding import CodingDomainSimulator
from .fallback import FallbackDomainSimulator
from .grilling import GrillingDomainSimulator
from .legal import LegalDomainSimulator
from .legal_tooling import LegalToolingDomainSimulator
from .office import OfficeDomainSimulator
from .orchestration import OrchestrationDomainSimulator
from .platform_tooling import PlatformToolingDomainSimulator
from .skill_repair import SkillRepairDomainSimulator
from .tech_qc import TechQCDomainSimulator
from .visual_design import VisualDesignDomainSimulator
from .visual_diagram import VisualDiagramDomainSimulator


class SimulatorDispatcher:
    """Manages simulator registration and execution via multi-tier fallback cascade."""

    def __init__(self) -> None:
        # Registry mapping archetype name -> simulator instance
        self.simulators: dict[str, BaseDomainSimulator] = {
            "grilling": GrillingDomainSimulator(),
            "adr": AdrLifecycleDomainSimulator(),
            "risk": BimRiskDomainSimulator(),
            "skill_repair": SkillRepairDomainSimulator(),
            "legal_tooling": LegalToolingDomainSimulator(),
            "legal": LegalDomainSimulator(),
            "tech_qc": TechQCDomainSimulator(),
            "academic": AcademicDomainSimulator(),
            "office": OfficeDomainSimulator(),
            "visual_design": VisualDesignDomainSimulator(),
            "visual": VisualDiagramDomainSimulator(),
            "bim_governance": BimGovernanceDomainSimulator(),
            "bim_rase": BimRaseDomainSimulator(),
            "bim": BimClassificationDomainSimulator(),
            "coding": CodingDomainSimulator(),
            "platform_tooling": PlatformToolingDomainSimulator(),
            "orchestration": OrchestrationDomainSimulator(),
        }
        self.fallback = FallbackDomainSimulator()

        # Deterministic anchor evaluation order for Tier 3 (matching simulation.py legacy ladder)
        self.anchor_order: list[BaseDomainSimulator] = [
            self.simulators["legal"],
            self.simulators["tech_qc"],
            self.simulators["academic"],
            self.simulators["risk"],
            self.simulators["bim_governance"],
            self.simulators["bim_rase"],
            self.simulators["visual_design"],
            self.simulators["legal_tooling"],
            self.simulators["platform_tooling"],
            self.simulators["office"],
            self.simulators["bim"],
            self.simulators["visual"],
            self.simulators["orchestration"],
            self.simulators["grilling"],
            self.simulators["coding"],
            self.simulators["skill_repair"],
            self.simulators["adr"],
        ]

    def dispatch(self, item: EvalItem, ctx: SimulationContext) -> str:
        """Executes simulation via 4-tier cascade."""

        # Tier 1: Primary SSOT resolution when skill_name is provided
        if ctx.skill_name:
            arch = resolve_domain_archetype(ctx.skill_name)
            if arch and arch.name in self.simulators:
                res = self.simulators[arch.name].simulate(item, ctx)
                if res is not None:
                    return res

        # Tier 2: Check item metadata (if item carries explicit target_archetype or target_skill)
        if hasattr(item, "metadata") and isinstance(item.metadata, dict):
            target = item.metadata.get("target_archetype") or item.metadata.get("target_skill")
            if target:
                arch = resolve_domain_archetype(str(target))
                arch_key = arch.name if arch else str(target)
                if arch_key in self.simulators:
                    res = self.simulators[arch_key].simulate(item, ctx)
                    if res is not None:
                        return res

        # Tier 3: Content / Prompt domain anchor cascade (for legacy callers without skill_name)
        for sim in self.anchor_order:
            if sim.can_handle(item, ctx):
                res = sim.simulate(item, ctx)
                if res is not None:
                    return res

        # Tier 4: Fallback generic response (golden answer or lean structural response)
        fallback_res = self.fallback.simulate(item, ctx)
        return fallback_res or ""


# Global singleton dispatcher instance
_GLOBAL_DISPATCHER = SimulatorDispatcher()


def build_mock_agent_task(content: str, skill_name: str = "") -> Callable[[EvalItem], str]:
    """Constructs a deterministic mock agent task simulator for offline eval testing.

    Args:
        content: The current prompt or SKILL.md body under evaluation.
        skill_name: Optional skill identifier for routing archetype simulations.

    Returns:
        Callable taking an EvalItem and returning a simulated grounded response.
    """
    ctx = SimulationContext.from_content_and_skill(content=content, skill_name=skill_name)

    def mock_agent_task(item: EvalItem) -> str:
        return _GLOBAL_DISPATCHER.dispatch(item, ctx)

    return mock_agent_task


create_domain_mock_agent_task = build_mock_agent_task

__all__ = [
    "SimulatorDispatcher",
    "build_mock_agent_task",
    "create_domain_mock_agent_task",
]
