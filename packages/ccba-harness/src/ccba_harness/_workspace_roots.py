"""Pure-stdlib workspace and Hub root discovery seam (ADR-0044 / ADR-0061).

Zero intra-package or mandatory third-party imports so this module can also run
as a standalone Tier-0 guardrail synced into Spoke ``scripts/_guardrails/``.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_WIN_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_CONTEXT_REL_PATHS: tuple[tuple[str, ...], ...] = (
    (".md", "workspace_context.yaml"),
    (".agents", "workspace_context.yaml"),
    ("workspace_context.yaml",),
)
_SCRIPT_LIKE_SUFFIXES: frozenset[str] = frozenset({".py", ".yaml", ".yml", ".json", ".md"})


@dataclass(frozen=True)
class WorkspaceHubContext:
    """Resolved workspace and Hub repository root metadata."""

    workspace_root: Path
    hub_root: Path | None
    context_file: Path | None
    context_data: dict[str, Any]
    is_hub_workspace: bool


def _translate_windows_path_wsl(raw: str) -> Path | None:
    """Translate a Windows drive path to POSIX using wslpath when available."""
    if not shutil.which("wslpath"):
        return None
    try:
        res = subprocess.run(
            ["wslpath", "-u", raw],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=2,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            cand = Path(res.stdout.strip())
            if cand.exists():
                return cand.resolve()
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def resolve_cross_platform_hub_path(
    raw: str,
    base_dir: Path,
    *,
    require_exists: bool = True,
) -> Path | None:
    """Safely resolve a candidate Hub path string across Windows and POSIX hosts."""
    cleaned = raw.strip().strip("'\"")
    if not cleaned:
        return None
    if os.name != "nt" and _WIN_DRIVE_PATTERN.match(cleaned):
        return _translate_windows_path_wsl(cleaned)
    candidate = Path(cleaned)
    resolved = candidate.resolve() if candidate.is_absolute() else (base_dir / candidate).resolve()
    return None if (require_exists and not resolved.exists()) else resolved


def _parse_yaml_fallback(content: str) -> dict[str, Any]:
    """Extract top-level and 1-level nested YAML scalars without PyYAML."""
    data: dict[str, Any] = {}
    section = ""
    sub_section = ""
    for raw_line in content.splitlines():
        stripped = raw_line.split("#", 1)[0].rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("-") or ":" not in stripped:
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        key, val = (part.strip() for part in stripped.strip().split(":", 1))
        val = val.strip("'\"")
        if indent == 0:
            section, sub_section = key, ""
            data[key] = val if val else data.get(key, {})
        elif indent == 2 and section and isinstance(data.get(section), dict):
            sub_section = key
            data[section][key] = val if val else data[section].get(key, {})
        elif indent >= 4 and section and sub_section and isinstance(data.get(section), dict):
            nested = data[section].setdefault(sub_section, {})
            if isinstance(nested, dict) and val:
                nested[key] = val
    return data


def load_workspace_context_dict(ctx_file: Path) -> dict[str, Any]:
    """Read workspace_context.yaml using PyYAML when available, else stdlib fallback."""
    try:
        content = ctx_file.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            loaded = yaml.safe_load(content)
            return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}
    return _parse_yaml_fallback(content)


def _find_workspace_context(root: Path) -> Path | None:
    """Return the first existing workspace_context.yaml file under root."""
    for parts in _CONTEXT_REL_PATHS:
        cand = root.joinpath(*parts)
        if cand.is_file():
            return cand
    return None


def _extract_raw_hub_path(context_data: dict[str, Any]) -> str:
    """Extract hub_path string or OS-specific mapping entry from context data."""
    hub_section = context_data.get("hub")
    proj_section = context_data.get("project")
    hub_val = (
        (hub_section.get("path") if isinstance(hub_section, dict) else None)
        or context_data.get("hub_path")
        or (proj_section.get("hub_path") if isinstance(proj_section, dict) else None)
    )
    if isinstance(hub_val, dict):
        os_key = "windows" if os.name == "nt" else "linux"
        return str(hub_val.get(os_key) or hub_val.get("posix") or "")
    return str(hub_val) if isinstance(hub_val, str) else ""


def _discover_workspace_root(
    start_dir: Path | None,
    *,
    include_pyproject: bool,
    include_agents_dir: bool,
) -> Path:
    """Walk upwards without stopping on AGENTS.md or internal monorepo pyproject.toml."""
    raw = (start_dir or Path.cwd()).resolve()
    current = (
        raw.parent
        if not raw.is_dir()
        and (raw.is_file() or (not raw.exists() and raw.suffix.lower() in _SCRIPT_LIKE_SUFFIXES))
        else raw
    )
    for parent in [current, *current.parents]:
        if _find_workspace_context(parent) is not None or (parent / ".git").exists():
            return parent
        if include_agents_dir and (parent / ".agents").exists():
            return parent
        if (
            include_pyproject
            and (parent / "pyproject.toml").exists()
            and not any((anc / "seam-contracts.yaml").is_file() for anc in parent.parents)
        ):
            return parent
    return current


def _matches_hub_layout(candidate: Path | None, require_hub_packages: bool) -> bool:
    """Return True if candidate is an existing Hub directory meeting layout constraints."""
    if candidate is None or not candidate.exists():
        return False
    if require_hub_packages:
        return (candidate / "packages" / "ccba-harness").is_dir()
    return (candidate / "seam-contracts.yaml").is_file() or (
        candidate / "packages" / "ccba-harness"
    ).is_dir()


def _discover_hub_root(
    workspace_root: Path,
    context_data: dict[str, Any],
    *,
    require_hub_packages: bool,
) -> Path | None:
    """Resolve Hub root dynamically via env vars, workspace_context, ancestors, or sibling."""
    for env_key in ("CCBA_HUB_PATH", "HUB_PATH"):
        raw_env = os.environ.get(env_key, "")
        if raw_env:
            cand = resolve_cross_platform_hub_path(raw_env, workspace_root)
            if cand is not None and cand.exists():
                return cand
    raw_ctx = _extract_raw_hub_path(context_data)
    if raw_ctx:
        cand = resolve_cross_platform_hub_path(raw_ctx, workspace_root)
        if cand is not None and (not require_hub_packages or _matches_hub_layout(cand, True)):
            return cand
    ancestors = [
        workspace_root,
        *workspace_root.parents,
        *Path(__file__).resolve().parents[:6],
        workspace_root.parent / "ccba-agent-platform",
    ]
    for anc in ancestors:
        if _matches_hub_layout(anc, require_hub_packages):
            return anc.resolve()
    return None


def resolve_workspace_and_hub_roots(
    start_dir: Path | None = None,
    *,
    include_pyproject: bool = True,
    include_agents_dir: bool = True,
    require_hub_packages: bool = False,
) -> WorkspaceHubContext:
    """Resolve workspace root and Hub monorepo root dynamically without import caching."""
    workspace_root = _discover_workspace_root(
        start_dir, include_pyproject=include_pyproject, include_agents_dir=include_agents_dir
    )
    context_file = _find_workspace_context(workspace_root)
    context_data = load_workspace_context_dict(context_file) if context_file else {}
    hub_root = _discover_hub_root(
        workspace_root, context_data, require_hub_packages=require_hub_packages
    )
    return WorkspaceHubContext(
        workspace_root=workspace_root,
        hub_root=hub_root,
        context_file=context_file,
        context_data=context_data,
        is_hub_workspace=(workspace_root / "seam-contracts.yaml").is_file(),
    )


__all__ = [
    "WorkspaceHubContext",
    "load_workspace_context_dict",
    "resolve_cross_platform_hub_path",
    "resolve_workspace_and_hub_roots",
]
