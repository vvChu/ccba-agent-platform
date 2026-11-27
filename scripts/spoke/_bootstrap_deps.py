"""Workspace dependency graph, PEP 503/508 normalization, and topological sorting for Spoke bootstrap."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence
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


_HUB_COMMIT_RE = re.compile(r"^#\s*hub_commit:\s*([0-9a-fA-F]{7,40})\b")
_EDITABLE_RE = re.compile(r"^(?:-e\s+|--editable(?:=|\s+))(.+)$")


def parse_requirements_hub_lockfile(req_file: Path) -> tuple[str | None, list[str]]:
    """Parse hub_commit and editable package names from requirements-hub.txt."""
    if not req_file.is_file():
        return None, []
    try:
        lines = req_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, []
    hub_commit: str | None = None
    packages: list[str] = []
    seen: set[str] = set()
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if hub_commit is None and (m := _HUB_COMMIT_RE.match(stripped)):
            hub_commit = m.group(1)
            continue
        if stripped.startswith("#") or not (em := _EDITABLE_RE.match(stripped)):
            continue
        cleaned = em.group(1).strip().strip('"').strip("'").replace("\\", "/").rstrip("/")
        pkg_name = cleaned.rsplit("/", 1)[-1].split("[", 1)[0].strip()
        if pkg_name and pkg_name not in seen:
            seen.add(pkg_name)
            packages.append(pkg_name)
    return hub_commit, packages


def _run_hub_git(hub_root: Path, args: list[str]) -> tuple[int, str, str | None]:
    """Execute a bounded read-only git command inside hub_root."""
    try:
        res = subprocess.run(
            ["git", *args],
            cwd=str(hub_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        return res.returncode, res.stdout.strip(), None
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, "", str(exc)


def inspect_hub_git_pyproject_drift(
    hub_root: Path,
    locked_commit: str,
    target_packages: Sequence[str],
) -> tuple[list[str], str | None]:
    """Check Hub git diff for packages/*/pyproject.toml changes since locked_commit."""
    if not (hub_root / ".git").exists():
        return [], f"Hub không có metadata .git để đối chiếu hub_commit '{locked_commit}'."
    rc, head_sha, err = _run_hub_git(hub_root, ["rev-parse", "HEAD"])
    if rc != 0 or not head_sha:
        suffix = f": {err}" if err else ""
        return [], f"Không thể xác định Hub HEAD để đối chiếu hub_commit '{locked_commit}'{suffix}."
    if head_sha.lower().startswith(locked_commit.lower()):
        return [], None
    diff_args = ["diff", "--name-only", f"{locked_commit}..HEAD", "--", "packages/*/pyproject.toml"]
    rc, diff_out, err = _run_hub_git(hub_root, diff_args)
    if rc != 0:
        reason = err or "shallow clone hoặc commit không còn trong lịch sử"
        return [], (
            f"Không thể đối chiếu git diff từ hub_commit '{locked_commit}' "
            f"tới Hub HEAD '{head_sha[:12]}' ({reason})."
        )
    target_set = set(target_packages)
    changed = {
        parts[1]
        for line in diff_out.splitlines()
        if len(parts := line.strip().replace("\\", "/").split("/")) == 3
        and parts[0] == "packages"
        and parts[2] == "pyproject.toml"
        and (not target_set or parts[1] in target_set)
    }
    return sorted(changed), None
