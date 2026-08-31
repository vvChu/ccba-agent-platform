"""CCBA Spoke Synchronization Engine Sub-Package.

Public Deep Seams:
    SpokeSynchronizer / SpokeSyncEngine — Hub discovery, catalog merge, guardrails copy, RSA registration.
    sync_project — Procedure delegate for single spoke synchronization.
    sync_all_spokes — Batch synchronize all registered active Spokes.
    rollback_project — Snapshot restoration for Spoke .agents workspace.
    list_project_backups — Discover snapshot backups.

Sub-Engines:
    HubDiscoverer, CatalogMerger, TestGuardrailCopier, SharedSdkInspector,
    GitWorkingTreeGuard, SpokeBackupManager, SpokeRegistrar, HubNotFoundError
"""

from __future__ import annotations

from .backup import GitWorkingTreeGuard, SpokeBackupManager
from .base import (
    HAS_CRYPTOGRAPHY,
    PLATFORM_ROOT,
    HubNotFoundError,
    are_dirs_identical,
    are_files_identical,
    load_yaml,
    safe_remove,
)
from .catalog import CatalogMerger
from .cli import run_spoke_sync_cli
from .coordinator import (
    PROJECT_TYPE_ALIASES,
    SpokeSyncEngine,
    SpokeSynchronizer,
    list_project_backups,
    merge_agents_constitution,
    resolve_canonical_project_type,
    rollback_project,
    sync_all_spokes,
    sync_project,
)
from .discovery import HubDiscoverer
from .registry import SpokeRegistrar
from .sdk_inspector import (
    LegalKnowledgeSyncOrchestrator,
    SharedSdkInspector,
    TestGuardrailCopier,
)

__all__ = [
    "SpokeSynchronizer",
    "SpokeSyncEngine",
    "HubDiscoverer",
    "CatalogMerger",
    "SpokeRegistrar",
    "TestGuardrailCopier",
    "SharedSdkInspector",
    "LegalKnowledgeSyncOrchestrator",
    "GitWorkingTreeGuard",
    "SpokeBackupManager",
    "HubNotFoundError",
    "PROJECT_TYPE_ALIASES",
    "resolve_canonical_project_type",
    "merge_agents_constitution",
    "sync_project",
    "sync_all_spokes",
    "rollback_project",
    "list_project_backups",
    "run_spoke_sync_cli",
    "load_yaml",
    "are_files_identical",
    "are_dirs_identical",
    "safe_remove",
    "HAS_CRYPTOGRAPHY",
    "PLATFORM_ROOT",
]
