"""CCBA Scaffolding Package.

Autonomous code, skill, and workflow scaffolding utilities.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from .skill_generator import (
    create_skill_from_script,
    inspect_via_dynamic_import,
    inspect_via_static_ast,
    sync_all_skills,
)

__all__ = [
    "create_skill_from_script",
    "sync_all_skills",
    "inspect_via_dynamic_import",
    "inspect_via_static_ast",
]
