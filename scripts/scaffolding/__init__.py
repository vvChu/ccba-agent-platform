"""CCBA Scaffolding Package.

Autonomous code, skill, workflow scaffolding, architecture metrics, and repomix packaging utilities.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from .arch_stats import ArchStatsUpdater, update_arch_metrics
from .repomix import RepomixPackager, run_repomix_pack
from .skill_generator import (
    create_skill_from_script,
    inspect_via_dynamic_import,
    inspect_via_static_ast,
    sync_all_skills,
)

__all__ = [
    "ArchStatsUpdater",
    "update_arch_metrics",
    "RepomixPackager",
    "run_repomix_pack",
    "create_skill_from_script",
    "sync_all_skills",
    "inspect_via_dynamic_import",
    "inspect_via_static_ast",
]
