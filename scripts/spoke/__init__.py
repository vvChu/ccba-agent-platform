"""CCBA Spoke Management & Governance Seams.

Deep Seams:
    SpokeSyncEngine / SpokeSynchronizer — Hub discovery, catalog merge, guardrails copy, RSA registration.
    sync_project — Quick procedural delegate for spoke synchronization.

Sub-Engines:
    HubDiscoverer, CatalogMerger, TestGuardrailCopier, HubNotFoundError
"""

from .spoke_adopter import (
    SpokeAdopter,
    SpokeDiscoveryReport,
    adopt_project,
    detect_spoke_stack,
    merge_workspace_context,
)
from .spoke_synchronizer import (
    CatalogMerger,
    HubDiscoverer,
    HubNotFoundError,
    SpokeSyncEngine,
    SpokeSynchronizer,
    TestGuardrailCopier,
    sync_project,
)

__all__ = [
    "SpokeSyncEngine",
    "SpokeSynchronizer",
    "sync_project",
    "SpokeAdopter",
    "SpokeDiscoveryReport",
    "adopt_project",
    "detect_spoke_stack",
    "merge_workspace_context",
    "HubDiscoverer",
    "CatalogMerger",
    "TestGuardrailCopier",
    "HubNotFoundError",
]
