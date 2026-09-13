"""CCBA Hub Import Depth Checker — Pre-commit hook for Spoke repositories.

Enforces ADR 0044 rule: Spoke code must only import from top-level Hub packages
(depth ≤ 2). Deep imports (depth ≥ 3) bypass the __all__ API contract and are
forbidden.

Examples:
    ✅ from ccba_legal import ChromeCDP
    ✅ from ccba_ai import ai
    ❌ from ccba_legal.crawler.chrome_cdp import _internal_helper
    ❌ from ccba_harness.core.locks import ProcessLock

Usage:
    python check_hub_import_depth.py [--path <spoke_root>]
    # Or as pre-commit hook in .pre-commit-config.yaml
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path

# Canonical fallback Hub package import prefixes for Spoke environments where packages/ is absent
FALLBACK_HUB_PACKAGES: tuple[str, ...] = (
    "ccba_ai",
    "ccba_core",
    "ccba_harness",
    "ccba_legal",
    "ccba_maskara",
    "ccba_notebooklm",
    "ccba_ooxml",
    "ccba_pdf_prep",
    "ccba_qc_core",
    "mdconverter",
)


def _read_hub_path_from_dir(directory: Path) -> Path | None:
    """Extract Hub packages directory from workspace_context.yaml in directory."""
    for rel in [
        directory / ".agents" / "workspace_context.yaml",
        directory / ".md" / "workspace_context.yaml",
        directory / "workspace_context.yaml",
    ]:
        if rel.is_file():
            try:
                for line in rel.read_text(encoding="utf-8").splitlines():
                    line_s = line.strip()
                    if line_s.startswith("hub_path:"):
                        raw = line_s.split(":", 1)[1].split("#")[0].strip().strip("'\"")
                        if raw:
                            raw_p = Path(raw)
                            spoke_dir = (
                                rel.parent.parent
                                if rel.parent.name in (".agents", ".md")
                                else rel.parent
                            )
                            hp = raw_p if raw_p.is_absolute() else (spoke_dir / raw_p).resolve()
                            pkg_dir = hp if hp.name == "packages" else hp / "packages"
                            if pkg_dir.is_dir():
                                return pkg_dir
            except OSError:
                pass
    return None


def find_hub_packages_dir(start_path: Path | None = None) -> Path | None:
    """Locate the Hub packages/ directory dynamically.

    Searches:
    1. start_path and its parents for packages/ or workspace_context.yaml hub_path
    2. Relative to this file's location (Hub or Spoke repo)
    3. Current working directory and its parents
    4. Environment variables (CCBA_HUB_PATH, HUB_PATH)
    """
    if start_path is not None:
        resolved = start_path.resolve()
        for cand in [resolved, *resolved.parents]:
            if cand.name == "packages" and cand.is_dir():
                return cand
            pkg_cand = cand / "packages"
            if pkg_cand.is_dir() and any(pkg_cand.iterdir()):
                return pkg_cand
            spoke_hub = _read_hub_path_from_dir(cand)
            if spoke_hub:
                return spoke_hub
        return None

    # When start_path is None, use discovery heuristics
    this_file = Path(__file__).resolve()
    for parent in this_file.parents:
        pkg_cand = parent / "packages"
        if pkg_cand.is_dir() and any(pkg_cand.glob("ccba-*")):
            return pkg_cand
        spoke_hub = _read_hub_path_from_dir(parent)
        if spoke_hub:
            return spoke_hub

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        pkg_cand = candidate / "packages"
        if pkg_cand.is_dir() and any(pkg_cand.glob("ccba-*")):
            return pkg_cand
        spoke_hub = _read_hub_path_from_dir(candidate)
        if spoke_hub:
            return spoke_hub

    for env_key in ("CCBA_HUB_PATH", "HUB_PATH"):
        env_val = os.environ.get(env_key)
        if env_val:
            hp = Path(env_val).resolve()
            pkg_dir = hp if hp.name == "packages" else hp / "packages"
            if pkg_dir.is_dir():
                return pkg_dir

    return None


def discover_hub_packages(
    hub_root: Path | None = None,
    fallback: tuple[str, ...] = FALLBACK_HUB_PACKAGES,
) -> tuple[str, ...]:
    """Dynamically discover official Hub package import names.

    Inspects `packages/*/src/*`, flat package layouts, and package `pyproject.toml`
    files to find canonical import package names (e.g. `ccba_legal` from `ccba-legal-intel`).
    Falls back to `fallback` if `packages/` is not accessible (e.g. in Spoke).
    """
    packages_dir = find_hub_packages_dir(hub_root)
    if not packages_dir or not packages_dir.is_dir():
        return fallback

    discovered: set[str] = set()
    for pkg_dir in packages_dir.iterdir():
        if not pkg_dir.is_dir() or pkg_dir.name.startswith((".", "_")):
            continue

        # 1. Inspect packages/*/src/* for top-level package modules
        src_dir = pkg_dir / "src"
        if src_dir.is_dir():
            for child in src_dir.iterdir():
                if (
                    child.is_dir()
                    and not child.name.startswith((".", "_"))
                    and not child.name.endswith(".egg-info")
                ):
                    discovered.add(child.name)
                elif (
                    child.is_file()
                    and child.suffix == ".py"
                    and not child.name.startswith((".", "_"))
                ):
                    discovered.add(child.stem)

        # 2. Inspect flat package layout (packages/*/<pkg_name>/__init__.py without src/)
        else:
            for child in pkg_dir.iterdir():
                if (
                    child.is_dir()
                    and not child.name.startswith((".", "_"))
                    and (child / "__init__.py").is_file()
                ):
                    discovered.add(child.name)

        # 3. Inspect pyproject.toml as complement
        pyproject = pkg_dir / "pyproject.toml"
        if pyproject.is_file():
            try:
                import tomllib

                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                wheel_pkgs = (
                    data.get("tool", {})
                    .get("hatch", {})
                    .get("build", {})
                    .get("targets", {})
                    .get("wheel", {})
                    .get("packages", [])
                )
                for wp in wheel_pkgs:
                    p_name = Path(wp).name
                    if p_name and not p_name.startswith((".", "_")):
                        discovered.add(p_name)

                st_includes = (
                    data.get("tool", {})
                    .get("setuptools", {})
                    .get("packages", {})
                    .get("find", {})
                    .get("include", [])
                )
                for inc in st_includes:
                    clean_inc = inc.rstrip("*").rstrip(".")
                    if clean_inc and not clean_inc.startswith((".", "_")):
                        discovered.add(clean_inc)

                flit_mod = data.get("tool", {}).get("flit", {}).get("module", {}).get("name")
                if flit_mod and not flit_mod.startswith((".", "_")):
                    discovered.add(flit_mod)

                scripts = data.get("project", {}).get("scripts", {})
                for entry in scripts.values():
                    if ":" in entry:
                        mod = entry.split(":")[0].split(".")[0]
                        if mod and not mod.startswith((".", "_")):
                            discovered.add(mod)
            except Exception:
                pass

    if not discovered:
        return fallback

    return tuple(sorted(discovered))


# Exported constants for compatibility with static imports & tests
HUB_PACKAGES: tuple[str, ...] = discover_hub_packages()
HUB_PACKAGE_PREFIXES: tuple[str, ...] = HUB_PACKAGES


def scan_file(
    filepath: Path,
    hub_packages: tuple[str, ...] | None = None,
) -> list[tuple[int, str]]:
    """Scans a Python file for deep Hub package imports using AST parsing.

    Returns list of (line_number, line_content) violations.
    """
    if hub_packages is None:
        hub_packages = HUB_PACKAGES

    violations: list[tuple[int, str]] = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
    except (UnicodeDecodeError, OSError, SyntaxError):
        return violations

    lines = content.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if not node.module or node.level > 0:
                continue
            parts = node.module.split(".")
            pkg = parts[0]
            if pkg in hub_packages:
                is_violation = (
                    len(parts) >= 3
                    or (len(parts) >= 2 and any(p.startswith("_") for p in parts[1:]))
                    or any(
                        alias.name.startswith("_")
                        and not (alias.name.startswith("__") and alias.name.endswith("__"))
                        for alias in node.names
                    )
                )
                if is_violation:
                    line_num = node.lineno
                    line_content = (
                        lines[line_num - 1].strip()
                        if 0 < line_num <= len(lines)
                        else f"from {node.module} import ..."
                    )
                    violations.append((line_num, line_content))

        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                pkg = parts[0]
                if pkg in hub_packages:
                    is_violation = (
                        len(parts) >= 3
                        or (len(parts) >= 2 and any(p.startswith("_") for p in parts[1:]))
                    )
                    if is_violation:
                        line_num = node.lineno
                        line_content = (
                            lines[line_num - 1].strip()
                            if 0 < line_num <= len(lines)
                            else f"import {alias.name}"
                        )
                        violations.append((line_num, line_content))

    # Deduplicate by line number and sort
    return sorted(set(violations), key=lambda x: x[0])


def main() -> int:
    """Scans Spoke Python files for deep Hub package imports."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CCBA Hub Import Depth Checker (ADR 0044)")
    parser.add_argument(
        "--path",
        "-p",
        default=".",
        help="Root directory to scan (default: current dir)",
    )
    parser.add_argument(
        "--hub-path",
        default=None,
        help="Path to Hub root directory (optional, discovered automatically if omitted)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific files to check (for pre-commit integration)",
    )
    args = parser.parse_args()

    hub_root = Path(args.hub_path).resolve() if args.hub_path else None
    if hub_root:
        active_packages = discover_hub_packages(hub_root=hub_root)
    else:
        active_packages = discover_hub_packages(hub_root=Path(args.path).resolve())
        if active_packages == FALLBACK_HUB_PACKAGES:
            active_packages = discover_hub_packages(hub_root=None)

    # Collect files to scan
    target_files: list[Path] = []
    if args.files:
        target_files = [Path(f) for f in args.files if f.endswith(".py")]
    else:
        root = Path(args.path).resolve()
        # Scan root .py files + scripts/, src/, tests/
        target_files.extend(root.glob("*.py"))
        for scan_dir in [root / "scripts", root / "src", root / "tests"]:
            if scan_dir.exists():
                target_files.extend(scan_dir.rglob("*.py"))

    # Exclude .venv, __pycache__, .git, .agents, .md
    target_files = [
        f
        for f in target_files
        if not any(
            part in (".venv", "venv", "__pycache__", ".git", "node_modules", ".agents", ".md")
            for part in f.parts
        )
    ]

    total_violations = 0
    for filepath in sorted(set(target_files)):
        violations = scan_file(filepath, hub_packages=active_packages)
        if violations:
            total_violations += len(violations)
            for line_num, line_content in violations:
                print(f"{filepath}:{line_num}: {line_content}")

    if total_violations > 0:
        print(
            f"\n❌ Phát hiện {total_violations} vi phạm Import Depth (ADR 0044).\n"
            "   Quy tắc: Chỉ import từ top-level Hub package.\n"
            "   ✅ Đúng:  from ccba_legal import ChromeCDP\n"
            "   ❌ Sai:   from ccba_legal.crawler.chrome_cdp import ChromeCDP\n"
            "   Nếu cần symbol chưa có trong top-level, tạo issue đề xuất bổ sung __all__.",
        )
        return 1

    if target_files:
        print(f"✅ Đã quét {len(target_files)} file(s), không có vi phạm Import Depth.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
