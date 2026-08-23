#!/usr/bin/env python3
"""spoke_synchronizer.py - Thin Forwarding Facade for Spoke Synchronization Engine.

Delegates 100% of domain logic to `scripts.spoke.sync` sub-package.
Sub-modules live in `scripts/spoke/sync/`:
- `discovery.py`      — Smart Hub discovery & auto-save
- `catalog.py`        — Atomic YAML catalog merge
- `registry.py`       — Encrypted Spoke registration & TTL
- `sdk_inspector.py`  — Zero-latency shared SDK & guardrails inspector
- `backup.py`         — Git tree safety guard & snapshot backup/rollback
- `coordinator.py`    — Multi-phase synchronization coordinator
- `cli.py`            — 2-Phase Safe-by-Default CLI runner

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure root directory is in sys.path
_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from scripts.spoke.sync import (
    HAS_CRYPTOGRAPHY,
    PLATFORM_ROOT,
    CatalogMerger,
    GitWorkingTreeGuard,
    HubDiscoverer,
    HubNotFoundError,
    SharedSdkInspector,
    SpokeBackupManager,
    SpokeRegistrar,
    SpokeSyncEngine,
    SpokeSynchronizer,
    TestGuardrailCopier,
    are_dirs_identical,
    are_files_identical,
    list_project_backups,
    load_yaml,
    rollback_project,
    run_spoke_sync_cli,
    safe_remove,
    sync_all_spokes,
    sync_project,
)


def main() -> None:
    """CLI entrypoint forwarding to sync.cli."""
    sys.exit(run_spoke_sync_cli())


if __name__ == "__main__":
    main()


__all__ = [
    "SpokeSynchronizer",
    "SpokeSyncEngine",
    "HubDiscoverer",
    "CatalogMerger",
    "SpokeRegistrar",
    "TestGuardrailCopier",
    "SharedSdkInspector",
    "GitWorkingTreeGuard",
    "SpokeBackupManager",
    "HubNotFoundError",
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
