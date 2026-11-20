"""Multi-tier Master Legal Registry discovery helpers (ADR 0050)."""

from __future__ import annotations

import os
from pathlib import Path

import yaml


def _find_registry_under(base_dir: Path) -> Path | None:
    """Return legal_registry.yaml under base_dir or its .md/data directory if present."""
    for name in ("legal_registry.yaml", ".md/data/legal_registry.yaml"):
        cand = base_dir / name
        if cand.is_file():
            return cand.resolve()
    return None


def _resolve_registry_tier12(custom_path: Path | str | None) -> Path | None:
    """Resolve Tier 1 explicit custom_path and Tier 2 environment variables."""
    if custom_path:
        p = Path(custom_path)
        if p.is_file():
            return p.resolve()
        if p.is_dir():
            if found := _find_registry_under(p):
                return found
    for env_key in ("CCBA_LEGAL_REGISTRY_PATH", "CCBA_LEGAL_KNOWLEDGE_PATH"):
        env_val = os.environ.get(env_key)
        if not env_val:
            continue
        p = Path(env_val)
        if env_key == "CCBA_LEGAL_REGISTRY_PATH" and p.is_file():
            return p.resolve()
        if found := _find_registry_under(p):
            return found
    return None


def _resolve_registry_in_context(root_dir: Path) -> Path | None:
    """Resolve Tier 3 master registry path declared in local .md/workspace_context.yaml."""
    local_ctx_path = root_dir / ".md" / "workspace_context.yaml"
    if not local_ctx_path.is_file():
        return None
    try:
        ctx = yaml.safe_load(local_ctx_path.read_text(encoding="utf-8")) or {}
        if not isinstance(ctx, dict):
            return None
        if ctx.get("master_registry_path"):
            cand = Path(ctx["master_registry_path"])
            if not cand.is_absolute():
                cand = root_dir / cand
            if cand.is_file():
                return cand.resolve()
        proj = ctx.get("project", {})
        if isinstance(proj, dict) and (
            proj.get("name") == "ccba-legal-knowledge"
            or proj.get("archetype") == "knowledge_corpus"
        ):
            return _find_registry_under(root_dir)
    except Exception:
        pass
    return None


def _collect_hub_candidates(project_root: Path, cwd_hub: Path | None) -> list[Path]:
    """Collect ordered Hub candidates across env vars, workspace_roots seam, and defaults."""
    hub_candidates: list[Path] = []
    for env_hub_key in ("CCBA_HUB_PATH", "HUB_PATH"):
        if env_hub := os.environ.get(env_hub_key):
            p_hub = Path(env_hub).resolve()
            if p_hub.exists():
                hub_candidates.append(p_hub)
    if cwd_hub is not None and cwd_hub.exists():
        hub_candidates.append(cwd_hub)
    hub_candidates.extend([project_root, project_root.parent / "ccba-agent-platform"])
    if os.name == "nt":
        hub_candidates.extend(
            [
                Path("D:/GitHubProjects/ccba-agent-platform"),  # ccba:allow-machine-path
                Path("C:/GitHubProjects/ccba-agent-platform"),  # ccba:allow-machine-path
            ]
        )
    else:
        hub_candidates.extend(
            [
                Path.home() / "ccba" / "ccba-agent-platform",
                Path.home() / "GitHubProjects" / "ccba-agent-platform",
            ]
        )
    return hub_candidates


def _resolve_registry_from_hub(hub_candidates: list[Path]) -> Path | None:
    """Resolve Tier 4 master registry via Hub spoke_registry YAML files."""
    for h_path in hub_candidates:
        if not h_path.exists():
            continue
        for reg_name in ("spoke_registry_decrypted.yaml", "spoke_registry.yaml"):
            spoke_reg_file = h_path / ".md" / "data" / reg_name
            if not spoke_reg_file.is_file():
                continue
            try:
                spoke_data = yaml.safe_load(spoke_reg_file.read_text(encoding="utf-8")) or {}
                for sp in spoke_data.get("spokes", []) if isinstance(spoke_data, dict) else []:
                    if not isinstance(sp, dict):
                        continue
                    is_corpus = (
                        sp.get("name") == "ccba-legal-knowledge"
                        or "legal-knowledge" in str(sp.get("name", "")).lower()
                        or sp.get("archetype") == "knowledge_corpus"
                    )
                    if is_corpus and sp.get("path"):
                        if found := _find_registry_under(Path(sp["path"])):
                            return found
            except Exception:
                pass
    return None


def _resolve_registry_from_local_candidates(project_root: Path) -> Path | None:
    """Resolve Tier 5 known sibling and machine-local knowledge corpus directories."""
    candidates = [
        project_root.parent / "ccba-legal-knowledge",
        project_root / ".." / "ccba-legal-knowledge",
    ]
    if os.name == "nt":
        candidates.extend(
            [
                Path("D:/GitHubProjects/ccba-legal-knowledge"),  # ccba:allow-machine-path
                Path("C:/GitHubProjects/ccba-legal-knowledge"),  # ccba:allow-machine-path
            ]
        )
    else:
        candidates.extend(
            [
                Path.home() / "ccba" / "ccba-legal-knowledge",
                Path.home() / "GitHubProjects" / "ccba-legal-knowledge",
            ]
        )
    try:
        candidates.extend(
            [
                Path.home() / "GitHubProjects" / "ccba-legal-knowledge",
                Path.home() / "ccba-legal-knowledge",
            ]
        )
    except Exception:
        pass
    for cand in candidates:
        try:
            resolved = cand.resolve()
            if resolved.exists():
                if found := _find_registry_under(resolved):
                    return found
        except Exception:
            continue
    return None


def _discover_tier3_to_6_for_root(project_root: Path) -> Path:
    """Resolve Tier 3 through Tier 6 master registry paths given an already-resolved project_root."""
    from ccba_harness import resolve_workspace_and_hub_roots

    if tier3 := _resolve_registry_in_context(project_root):
        return tier3

    cwd_ctx = resolve_workspace_and_hub_roots(Path.cwd())
    if cwd_ctx.workspace_root != project_root and cwd_ctx.context_file is not None:
        if cwd_tier3 := _resolve_registry_in_context(cwd_ctx.workspace_root):
            return cwd_tier3

    proj_hub = resolve_workspace_and_hub_roots(project_root).hub_root
    cwd_hub = cwd_ctx.hub_root if cwd_ctx.context_file is not None else proj_hub
    hub_candidates = _collect_hub_candidates(project_root, cwd_hub or proj_hub)
    if tier4 := _resolve_registry_from_hub(hub_candidates):
        return tier4
    if tier5 := _resolve_registry_from_local_candidates(project_root):
        return tier5
    return project_root / ".md" / "data" / "legal_registry.yaml"
