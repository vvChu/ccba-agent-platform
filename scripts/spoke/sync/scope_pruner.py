"""scope_pruner.py - Hub-scoped skill filtering, --prune-unscoped, and manifest helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from .base import safe_remove


def should_sync_skill_to_spoke(skill_entry: dict[str, Any]) -> bool:
    """Return False only when catalog explicitly marks a skill as scope == 'hub'."""
    scope = str(skill_entry.get("scope") or "").strip().lower()
    return scope != "hub"


def extract_hub_scoped_skill_folders(catalog: dict[str, Any] | None) -> set[str]:
    """Return folder names and declared skill names tagged scope == 'hub' in catalog."""
    hub_only: set[str] = set()
    if not isinstance(catalog, dict):
        return hub_only
    for entry in catalog.get("skills", []):
        if not isinstance(entry, dict) or should_sync_skill_to_spoke(entry):
            continue
        skill_path = entry.get("skill_path")
        if isinstance(skill_path, str) and skill_path.strip():
            hub_only.add(Path(skill_path).parent.name)
        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            hub_only.add(name.strip())
    return hub_only


def reconcile_existing_skills(
    spoke_root: Path,
    spoke_skills_dir: Path,
    synced_skill_folders: set[str],
    deprecation_aliases: dict[str, str],
    catalog: dict[str, Any] | None = None,
    prune_unscoped: bool = False,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Preserve custom/other-bundle skills, clean aliases, and prune hub-scoped skills if enabled."""
    actions: list[dict[str, Any]] = []
    if not spoke_skills_dir.exists():
        return actions
    hub_scoped = extract_hub_scoped_skill_folders(catalog) if prune_unscoped else set()
    for existing in sorted(spoke_skills_dir.iterdir(), key=lambda p: p.name):
        if not existing.is_dir() or existing.name in synced_skill_folders:
            continue
        replacement = deprecation_aliases.get(existing.name)
        rel_path = str(existing.relative_to(spoke_root))
        if replacement and replacement in synced_skill_folders:
            status, should_rm = "DEPRECATED_REPLACED", True
        elif prune_unscoped and existing.name in hub_scoped:
            status, should_rm = "REMOVED", True
        else:
            status, should_rm = "PRESERVED", False
        actions.append({"type": "Skill", "name": existing.name, "status": status, "path": rel_path})
        if should_rm and not dry_run:
            safe_remove(existing)
    return actions


def _load_guardrail_manifest_seam(hub_root: Path, spoke_root: Path) -> Any:
    """Dynamically load pure-stdlib _guardrail_manifest.py via importlib without static import."""
    rel = Path("packages/ccba-harness/src/ccba_harness/_guardrail_manifest.py")
    candidates = (
        hub_root / rel,
        Path(__file__).resolve().parents[3] / rel,
        spoke_root / "scripts" / "_guardrails" / "_guardrail_manifest.py",
    )
    for cand in candidates:
        if cand.is_file():
            spec = importlib.util.spec_from_file_location("_ccba_guardrail_manifest_sync", cand)
            if spec is not None and spec.loader is not None:
                mod = sys.modules.get(spec.name)
                if mod is None:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = mod
                    spec.loader.exec_module(mod)
                return mod
    raise ImportError("Unable to locate _guardrail_manifest.py Tier-0 seam.")


def sync_guardrail_manifest(
    spoke_root: Path,
    hub_root: Path,
    actions: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    """Write deterministic scripts/_guardrails/guardrails_manifest.json after real Spoke sync."""
    if dry_run or not actions:
        return
    try:
        if spoke_root.resolve() == hub_root.resolve():
            return
    except OSError:
        return
    applied = [a for a in actions if a.get("status") in ("NEW", "UPDATED", "UNCHANGED")]
    if not applied:
        return
    stamped_rels = [
        str(a["path"]).replace("\\", "/")
        for a in applied
        if str(a.get("path", "")).replace("\\", "/").startswith("scripts/_guardrails/")
        and (spoke_root / str(a["path"])).is_file()
    ]
    seam = _load_guardrail_manifest_seam(hub_root, spoke_root)
    seam.write_guardrail_manifest(spoke_root, stamped_rels)
