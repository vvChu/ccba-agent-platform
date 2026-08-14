"""Thin Backward-Compatible Facade for Architecture Stats Updater.

Delegates execution to the deep ``ArchStatsUpdater`` class in ``scripts.scaffolding.arch_stats``.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from scripts.scaffolding.arch_stats import ArchStatsUpdater, main, update_arch_metrics
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.scaffolding.arch_stats import ArchStatsUpdater, main, update_arch_metrics

_updater = ArchStatsUpdater()
get_counts = _updater.get_counts
update_file = _updater.update_file
SKILLS_DIR = _updater.skills_dir
WORKFLOWS_DIR = _updater.workflows_dir
PACKAGES_DIR = _updater.packages_dir
DOCS_TO_UPDATE = _updater.DEFAULT_DOCS

__all__ = [
    "ArchStatsUpdater",
    "update_arch_metrics",
    "get_counts",
    "update_file",
    "main",
    "SKILLS_DIR",
    "WORKFLOWS_DIR",
    "PACKAGES_DIR",
    "DOCS_TO_UPDATE",
]

if __name__ == "__main__":
    main()
