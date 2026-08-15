"""CCBA Spoke Management & Governance Seams.

Deep Seams:
    SpokeSyncEngine / SpokeSynchronizer — Hub discovery, catalog merge, guardrails copy, RSA registration.
    sync_project — Quick procedural delegate for spoke synchronization.
    sync_all_spokes — Batch synchronize all registered active Spokes.

Sub-Engines:
    HubDiscoverer, CatalogMerger, TestGuardrailCopier, HubNotFoundError, get_registered_spokes
"""

from .decrypt_spoke_registry import get_registered_spokes
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
    SharedSdkInspector,
    SpokeSyncEngine,
    SpokeSynchronizer,
    TestGuardrailCopier,
    sync_all_spokes,
    sync_project,
)

__all__ = [
    "SpokeSyncEngine",
    "SpokeSynchronizer",
    "SharedSdkInspector",
    "sync_project",
    "sync_all_spokes",
    "get_registered_spokes",
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
