"""Workspace dependency graph, PEP 503/508 normalization, and topological sorting for Spoke bootstrap."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PACKAGE_TOPOLOGY_ORDER: list[str] = [
    "ccba-harness",
    "ccba-ai",
    "ccba-legal-intel",
    "ccba-qc-core",
    "ccba-ooxml",
    "ccba-pdf-prep",
    "ccba-maskara",
    "mdconverter",
    "ccba-notebooklm",
]

_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


@dataclass(frozen=True)
class WorkspaceDepGraph:
    """Internal Hub package dependency graph and bidirectional alias table."""

    deps: dict[str, set[str]]
    alias_to_folder: dict[str, str]


def normalize_pkg_name(name: str) -> str:
    """Normalize a Python package name per PEP 503."""
    return re.sub(r"[-_.]+", "-", name.strip()).lower()


def extract_req_name(req: str) -> str:
    """Extract and PEP 503-normalize the distribution name from a PEP 508 requirement string."""
    match = _REQ_NAME_RE.match(req)
    return normalize_pkg_name(match.group(1)) if match else ""


def _load_tomllib() -> Any | None:
    """Load stdlib tomllib or fallback tomli; return None if neither is available."""
    try:
        import tomllib

        return tomllib
    except ImportError:
        try:
            import tomli  # type: ignore[import-not-found]

            return tomli
        except ImportError:
            return None


def _parse_single_pyproject(
    toml_path: Path, folder_name: str, toml_mod: Any
) -> tuple[str, list[str]]:
    """Read project.name and string entries from project.dependencies fail-softly."""
    try:
        data = toml_mod.loads(toml_path.read_text(encoding="utf-8"))
    except Exception:
        return folder_name, []
    proj = data.get("project") if isinstance(data, dict) else None
    if not isinstance(proj, dict):
        return folder_name, []
    raw_name = proj.get("name")
    proj_name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else folder_name
    raw_deps = proj.get("dependencies")
    deps = (
        [item for item in raw_deps if isinstance(item, str)] if isinstance(raw_deps, list) else []
    )
    return proj_name, deps


def read_workspace_dep_graph(hub_root: Path | None = None) -> WorkspaceDepGraph:
    """Build internal Hub dependency graph from packages/*/pyproject.toml fail-softly."""
    root = hub_root if hub_root is not None else Path(__file__).resolve().parents[2]
    pkg_dir = root / "packages"
    toml_mod = _load_tomllib()
    if not pkg_dir.is_dir() or toml_mod is None:
        return WorkspaceDepGraph(deps={}, alias_to_folder={})
    try:
        entries = sorted(pkg_dir.iterdir(), key=lambda x: x.name)
    except OSError:
        return WorkspaceDepGraph(deps={}, alias_to_folder={})

    parsed: list[tuple[str, str, list[str]]] = []
    for entry in entries:
        toml_path = entry / "pyproject.toml"
        if entry.is_dir() and toml_path.is_file():
            proj_name, raw_deps = _parse_single_pyproject(toml_path, entry.name, toml_mod)
            parsed.append((entry.name, proj_name, raw_deps))

    alias_to_folder = {normalize_pkg_name(pn): fn for fn, pn, _ in parsed}
    alias_to_folder.update({normalize_pkg_name(fn): fn for fn, _, _ in parsed})
    deps: dict[str, set[str]] = {}
    for folder, _, raw_deps in parsed:
        internal: set[str] = set()
        for req in raw_deps:
            dep_folder = alias_to_folder.get(extract_req_name(req))
            if dep_folder and dep_folder != folder:
                internal.add(dep_folder)
        deps[folder] = internal
    return WorkspaceDepGraph(deps=deps, alias_to_folder=alias_to_folder)


def expand_internal_hub_deps(selected: set[str], graph: WorkspaceDepGraph) -> set[str]:
    """Compute monotonic, cycle-safe transitive closure of internal Hub package dependencies."""
    initial = [graph.alias_to_folder.get(normalize_pkg_name(pkg), pkg) for pkg in sorted(selected)]
    expanded: set[str] = set(initial)
    queue = list(dict.fromkeys(initial))
    while queue:
        curr = queue.pop(0)
        for dep in sorted(graph.deps.get(curr, ())):
            if dep not in expanded:
                expanded.add(dep)
                queue.append(dep)
    return expanded


def topo_sort_dep_graph(dep_graph: dict[str, set[str]]) -> list[str]:
    """Order workspace packages via Kahn's topological sort with fail-closed fallback."""
    if not dep_graph:
        return list(DEFAULT_PACKAGE_TOPOLOGY_ORDER)
    in_degree: dict[str, int] = dict.fromkeys(dep_graph, 0)
    adj: dict[str, list[str]] = {pkg: [] for pkg in dep_graph}
    for folder, deps in dep_graph.items():
        for dep in deps:
            if dep != folder and dep in dep_graph:
                adj[dep].append(folder)
                in_degree[folder] += 1

    ordered: list[str] = []
    for anchor in ("ccba-harness", "ccba-ai"):
        if anchor in in_degree and anchor not in ordered:
            ordered.append(anchor)
            for neighbor in adj[anchor]:
                in_degree[neighbor] -= 1

    zero_in = sorted(pkg for pkg in in_degree if in_degree[pkg] <= 0 and pkg not in ordered)
    while zero_in:
        curr = zero_in.pop(0)
        ordered.append(curr)
        for neighbor in sorted(adj[curr]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0 and neighbor not in ordered and neighbor not in zero_in:
                zero_in.append(neighbor)
    return ordered if len(ordered) == len(dep_graph) else list(DEFAULT_PACKAGE_TOPOLOGY_ORDER)


def discover_package_topology(hub_root: Path | None = None) -> list[str]:
    """Discover all Hub packages and resolve their topological dependency order (ADR-0062)."""
    return topo_sort_dep_graph(read_workspace_dep_graph(hub_root).deps)
