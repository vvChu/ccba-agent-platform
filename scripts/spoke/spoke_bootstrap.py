"""CCBA Spoke Bootstrap Engine — Automated Hub Packages Editable Link & Venv Setup.

This module automates the connection between Spoke Python workspaces and Hub packages
via standard editable installs (`pip install -e`), completely replacing brittle `sys.path.insert` hacks.
Complies with ADR 0044.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from scripts.spoke._bootstrap_deps import (  # noqa: E402
    DEFAULT_PACKAGE_TOPOLOGY_ORDER,
    discover_package_topology,
    expand_internal_hub_deps,
    inspect_hub_git_pyproject_drift,
    parse_requirements_hub_lockfile,
    read_workspace_dep_graph,
    topo_sort_dep_graph,
)


def _load_workspace_roots_seam() -> Any:
    """Load the pure-stdlib _workspace_roots seam via package, Tier-0 sibling, or Hub."""
    try:
        from ccba_harness import resolve_workspace_and_hub_roots as _seam_fn

        _ = _seam_fn
        return sys.modules["ccba_harness._workspace_roots"]
    except ImportError:
        pass
    here = Path(__file__).resolve().parent
    hub_fallback = here.parents[1] / "packages/ccba-harness/src/ccba_harness/_workspace_roots.py"
    for candidate in (
        here / "_workspace_roots.py",
        here / "_guardrails" / "_workspace_roots.py",
        hub_fallback,
    ):
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location("_ccba_workspace_roots", candidate)
            if spec is not None and spec.loader is not None:
                mod = sys.modules.get(spec.name)
                if mod is None:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = mod
                    spec.loader.exec_module(mod)
                return mod
    raise ImportError("Unable to locate stdlib _workspace_roots seam.")


def _safe_load_yaml(filepath: Path) -> dict[str, Any]:
    """Loads a YAML file with graceful fallback when PyYAML is unavailable."""
    try:
        import yaml
    except ImportError:
        print(
            f"⚠️ PyYAML chưa cài đặt. Bỏ qua {filepath.name}, dùng Tier 0 mặc định.",
            file=sys.stderr,
        )
        return {}
    try:
        return yaml.safe_load(filepath.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


SPOKE_HYGIENE_GITIGNORE_RULES: tuple[str, ...] = (
    "requirements-hub.txt",
    ".md/teach/",
    ".md/scratch/",
    ".md/backups/",
    ".md/peer_exchange/.bridge_cache.json",
    ".md/peer_exchange/*.lock",
    ".md/peer_exchange/status.json",
    ".md/peer_exchange/*.md",
    "!.md/peer_exchange/PEER_HANDSHAKE.md",
    "!.md/peer_exchange/README.md",
    "!.md/peer_exchange/.gitkeep",
    ".md/data/telemetry_summary.json",
    ".md/data/*.json",
    ".tmp/",
    ".out-of-scope/",
    ".skill_versions/",
    "**/.skill_versions/",
)


def get_package_topology_order(hub_root: Path | None = None) -> list[str]:
    """Returns the dynamically discovered topological package order (ADR-0062 / ADR-0065)."""
    return discover_package_topology(hub_root)


PACKAGE_TOPOLOGY_ORDER: list[str] = DEFAULT_PACKAGE_TOPOLOGY_ORDER


ARCHETYPE_TIER1_DEFAULTS = {
    "knowledge_corpus": ["ccba-legal-intel"],
    "project_delivery": ["ccba-qc-core", "ccba-ooxml", "ccba-pdf-prep", "mdconverter"],
    "enterprise_governance": ["ccba-ooxml", "ccba-pdf-prep", "mdconverter"],
}


def _binding_names(raw: Any) -> list[str]:
    """Read package names from a tier or bundle list. Mappings use the ``name`` field."""
    if isinstance(raw, str):
        text = raw.strip()
        return [text] if text else []
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    return names


def _names_passing_when(raw: Any, *, legal_related: bool) -> list[str]:
    """Keep archetype packages whose ``when`` clause matches the spoke."""
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
            continue
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        when = item.get("when") or "always"
        if not isinstance(when, str) or not when.strip():
            when = "always"
        when = when.strip()
        if when == "legal_related" and not legal_related:
            continue
        if when not in {"always", "legal_related"}:
            continue
        names.append(name.strip())
    return names


def _resolved_bundle_names(
    catalog: dict[str, Any],
    project_type: str,
    additional_bundles: Sequence[str],
) -> list[str]:
    """Bundle ids for a project type, plus caller extras. Values are bundle ids, not packages."""
    names: list[str] = []
    bundles = catalog.get("bundles")
    raw = bundles.get(project_type) if isinstance(bundles, dict) else None
    if isinstance(raw, str):
        raw = [raw]
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
    for extra in additional_bundles:
        if isinstance(extra, str) and extra.strip():
            text = extra.strip()
            if text not in names:
                names.append(text)
    return names


def _order_by_topology(selected: set[str], topo_order: Sequence[str]) -> list[str]:
    """Sort a chosen install set. Topology decides order; it does not choose members."""
    ordered: list[str] = []
    remaining = set(selected)
    for pkg in topo_order:
        if pkg in remaining:
            ordered.append(pkg)
            remaining.remove(pkg)
    ordered.extend(sorted(remaining))
    return ordered


def _coerce_name_sequence(raw: Any) -> tuple[str, ...]:
    """Normalize a string or list of strings into a tuple of stripped names."""
    if isinstance(raw, str):
        text = raw.strip()
        return (text,) if text else ()
    if isinstance(raw, (list, tuple)):
        return tuple(item.strip() for item in raw if isinstance(item, str) and item.strip())
    return ()


def _context_additional_bundles(context: dict[str, Any], proj: dict[str, Any]) -> tuple[str, ...]:
    """Read additional bundle ids from workspace context."""
    raw = context.get("additional_bundles")
    if not raw:
        raw = proj.get("additional_bundles")
    return _coerce_name_sequence(raw)


def resolve_install_set(
    hub_root: Path,
    *,
    archetype: str,
    project_type: str,
    additional_bundles: Sequence[str] = (),
    declared_packages: Sequence[str] = (),
    legal_related: bool = False,
) -> list[str] | None:
    """Resolve the Spoke install set from catalog package_bindings (ADR-0062).

    Returns None when catalog.yaml has no package_bindings mapping, so callers
    keep their legacy hardcoded defaults. Declared hub_packages replace archetype
    and bundle defaults. Tier 0 stays. Order follows discover_package_topology.
    """
    catalog_path = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if not catalog_path.is_file():
        return None
    data = _safe_load_yaml(catalog_path)
    bindings = data.get("package_bindings")
    if not isinstance(bindings, dict):
        return None

    selected: set[str] = set(_binding_names(bindings.get("tier0")))
    declared = [pkg.strip() for pkg in declared_packages if isinstance(pkg, str) and pkg.strip()]
    if declared:
        selected.update(declared)
    else:
        arch_map = bindings.get("archetypes") or {}
        if isinstance(arch_map, dict):
            selected.update(
                _names_passing_when(arch_map.get(archetype), legal_related=legal_related)
            )
        bundle_map = bindings.get("bundles") or {}
        if isinstance(bundle_map, dict):
            for bundle_name in _resolved_bundle_names(data, project_type, additional_bundles):
                selected.update(_binding_names(bundle_map.get(bundle_name)))

    graph = read_workspace_dep_graph(hub_root)
    expanded = expand_internal_hub_deps(selected, graph)
    return _order_by_topology(expanded, topo_sort_dep_graph(graph.deps))


PROJECT_TYPE_TO_ARCHETYPE: dict[str, str] = {
    "pháp điển": "knowledge_corpus",
    "phap dien": "knowledge_corpus",
    "tra cứu": "knowledge_corpus",
    "tra cuu": "knowledge_corpus",
    "lookup": "knowledge_corpus",
    "legal knowledge": "knowledge_corpus",
    "thẩm tra thiết kế": "project_delivery",
    "tham tra thiet ke": "project_delivery",
    "thẩm tra": "project_delivery",
    "tham tra": "project_delivery",
    "thiết kế": "project_delivery",
    "thiet ke": "project_delivery",
    "kiểm định": "project_delivery",
    "kiem dinh": "project_delivery",
    "tác vụ admin": "enterprise_governance",
    "tac vu admin": "enterprise_governance",
    "hành chính": "enterprise_governance",
    "admin": "enterprise_governance",
}


class SpokeBootstrapper:
    """Orchestrates virtual environment detection, editable Hub package installs,

    and git isolation for CCBA Spoke repositories.
    """

    def __init__(self, spoke_path: Path | str, hub_path: Path | str | None = None):
        self.spoke_root = Path(spoke_path).resolve()
        if hub_path:
            self.hub_root = Path(hub_path).resolve()
        else:
            self.hub_root = self._resolve_hub_root()

    def _resolve_hub_root(self) -> Path:
        """Dynamically resolves the Hub root repository path via _workspace_roots seam."""
        seam = _load_workspace_roots_seam()
        ctx = seam.resolve_workspace_and_hub_roots(self.spoke_root, require_hub_packages=True)
        if ctx.hub_root is not None:
            return ctx.hub_root
        return Path(__file__).resolve().parent.parent.parent

    def read_workspace_context(self) -> dict[str, Any]:
        """Reads workspace_context.yaml from .agents/ or .md/ (lazy yaml import)."""
        for ctx_dir in [self.spoke_root / ".agents", self.spoke_root / ".md"]:
            ctx_file = ctx_dir / "workspace_context.yaml"
            if ctx_file.exists():
                return _safe_load_yaml(ctx_file)
        return {}

    def is_python_project(self) -> bool:
        """Determines if the Spoke contains Python codebase or requirements."""
        context = self.read_workspace_context()
        proj = context.get("project", {})
        proj_type = proj.get("type", "")
        proj_mode = proj.get("mode", "")
        archetype = proj.get("archetype", "")
        norm_type = str(proj_type).strip().lower()
        if (
            proj_type in ("Phần mềm", "Pháp điển", "Tra cứu")
            or proj_mode in ("software", "knowledge")
            or archetype in ("knowledge_corpus", "project_delivery", "enterprise_governance")
            or norm_type in PROJECT_TYPE_TO_ARCHETYPE
        ):
            return True

        if (self.spoke_root / "pyproject.toml").exists():
            return True
        if (self.spoke_root / "requirements.txt").exists():
            return True
        if (
            (self.spoke_root / ".venv").exists()
            or (self.spoke_root / "venv").exists()
            or (self.spoke_root / "scripts" / ".venv").exists()
            or (self.spoke_root / "scripts" / "venv").exists()
        ):
            return True

        # Scan for .py files in root, scripts, src, tests
        for search_dir in [
            self.spoke_root,
            self.spoke_root / "scripts",
            self.spoke_root / "src",
            self.spoke_root / "tests",
        ]:
            if search_dir.exists():
                if any(search_dir.glob("*.py")):
                    return True

        return False

    def find_venv(self) -> Path | None:
        """Locates the existing virtual environment directory in Spoke."""
        candidate_dirs = [
            self.spoke_root / ".venv",
            self.spoke_root / "venv",
            self.spoke_root / "env",
            self.spoke_root / "scripts" / ".venv",
            self.spoke_root / "scripts" / "venv",
        ]
        for v_dir in candidate_dirs:
            if v_dir.exists():
                # Check for python executable inside
                win_py = v_dir / "Scripts" / "python.exe"
                posix_py = v_dir / "bin" / "python"
                if win_py.exists() or posix_py.exists():
                    return v_dir
        return None

    def get_python_exec(self, venv_dir: Path) -> Path:
        """Returns the Python executable path inside the virtual environment."""
        win_py = venv_dir / "Scripts" / "python.exe"
        if win_py.exists():
            return win_py
        posix_py = venv_dir / "bin" / "python"
        if posix_py.exists():
            return posix_py
        return win_py  # default fallback

    def get_pip_exec(self, venv_dir: Path) -> Path:
        """Returns the Pip executable path inside the virtual environment."""
        win_pip = venv_dir / "Scripts" / "pip.exe"
        if win_pip.exists():
            return win_pip
        posix_pip = venv_dir / "bin" / "pip"
        if posix_pip.exists():
            return posix_pip
        return win_pip

    def _resolve_legacy_target_packages(
        self,
        archetype: str,
        declared: Sequence[str],
        legal_related: bool,
    ) -> list[str]:
        """Resolve Tier 0/1/declared packages when catalog package_bindings are absent."""
        target_set: set[str] = {"ccba-harness", "ccba-ai"}
        if declared:
            target_set.update(declared)
        elif archetype in ARCHETYPE_TIER1_DEFAULTS:
            for default_pkg in ARCHETYPE_TIER1_DEFAULTS[archetype]:
                if default_pkg == "ccba-legal-intel" and not legal_related:
                    continue
                target_set.add(default_pkg)
        graph = read_workspace_dep_graph(self.hub_root)
        expanded = expand_internal_hub_deps(target_set, graph)
        return _order_by_topology(expanded, topo_sort_dep_graph(graph.deps))

    def resolve_target_packages(self) -> list[str]:
        """Resolves target packages according to Tier 0 + Tier 1 + Tier 2 rules.

        Returns ordered list matching topological dependency order.
        """
        context = self.read_workspace_context()
        proj = context.get("project", {})
        if not isinstance(proj, dict):
            proj = {}
        archetype = str(proj.get("archetype", "") or "")
        if not archetype:
            raw_type = str(proj.get("type", "")).strip().lower()
            archetype = PROJECT_TYPE_TO_ARCHETYPE.get(raw_type, "")

        declared_list = list(_coerce_name_sequence(context.get("hub_packages", [])))
        raw_proj_type = str(proj.get("type", "") or context.get("project_type", "")).strip()
        from scripts.spoke.sync.sdk_inspector import is_legal_related_spoke

        legal_related = is_legal_related_spoke(self.spoke_root, raw_proj_type)
        bound = resolve_install_set(
            self.hub_root,
            archetype=archetype,
            project_type=raw_proj_type,
            additional_bundles=_context_additional_bundles(context, proj),
            declared_packages=tuple(declared_list),
            legal_related=legal_related,
        )
        if bound is not None:
            return bound
        return self._resolve_legacy_target_packages(archetype, declared_list, legal_related)

    def ensure_gitignore_rule(self, dry_run: bool = False) -> bool:
        """Ensures requirements-hub.txt and Spoke Leakage Guard rules are included in .gitignore."""
        gitignore_path = self.spoke_root / ".gitignore"
        rules = list(SPOKE_HYGIENE_GITIGNORE_RULES)

        if not gitignore_path.exists():
            if not dry_run:
                header = "# Hub auto-generated editable links & Spoke Leakage Guard (ADR 0045)\n"
                gitignore_path.write_text(header + "\n".join(rules) + "\n", encoding="utf-8")
            return True

        content = gitignore_path.read_text(encoding="utf-8")
        existing_lines = {line.strip() for line in content.splitlines()}
        missing_rules = [
            r for r in rules if r not in existing_lines and r.rstrip("/") not in existing_lines
        ]
        if not missing_rules:
            return False

        if not dry_run:
            new_content = (
                content.rstrip()
                + "\n\n# Hub auto-generated editable links & Spoke Leakage Guard (ADR 0045)\n"
                + "\n".join(missing_rules)
                + "\n"
            )
            gitignore_path.write_text(new_content, encoding="utf-8")
        return True

    def ensure_githooks_configured(self, dry_run: bool = False) -> bool:
        """Configures core.hooksPath to .githooks if .githooks directory exists."""
        githooks_dir = self.spoke_root / ".githooks"
        git_dir = self.spoke_root / ".git"
        if not (githooks_dir.exists() and git_dir.exists()):
            return False

        if dry_run:
            print("[Bootstrap] [DRY-RUN] Would configure git core.hooksPath -> .githooks")
            return True

        try:
            res = subprocess.run(
                ["git", "config", "core.hooksPath", ".githooks"],
                cwd=str(self.spoke_root),
                capture_output=True,
                text=True,
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_hub_commit_hash(self) -> str:
        """Returns the current HEAD commit hash of the Hub repository."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.hub_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if res.returncode == 0:
                return res.stdout.strip()[:12]
        except Exception:
            pass
        return "unknown"

    def check_hub_branch(self) -> str | None:
        """Checks if Hub is on the main branch. Returns branch name or None on error."""
        try:
            res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.hub_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def generate_requirements_hub_file(self, packages: list[str], dry_run: bool = False) -> Path:
        """Generates requirements-hub.txt with editable links and commit hash snapshot."""
        req_file = self.spoke_root / "requirements-hub.txt"
        commit_hash = self.get_hub_commit_hash()
        lines = [
            "# =============================================================================",
            "# AUTO-GENERATED BY ccba-platform spoke-bootstrap (ADR 0044)",
            "# DO NOT COMMIT: Contains local machine absolute paths",
            f"# hub_commit: {commit_hash}",
            "# =============================================================================",
            "",
        ]
        for pkg in packages:
            pkg_path = self.hub_root / "packages" / pkg
            lines.append(f"-e {pkg_path}")

        lines.append("")
        if not dry_run:
            req_file.write_text("\n".join(lines), encoding="utf-8")
        return req_file

    def bootstrap(
        self,
        auto_create_venv: bool = False,
        dry_run: bool = False,
        check_only: bool = False,
        force: bool = False,
    ) -> int:
        """Executes the full Spoke Hub package bootstrap process."""
        print("\n=== CCBA Spoke Bootstrap (ADR 0044) ===")
        print(f"Spoke Root : {self.spoke_root}")
        print(f"Hub Root   : {self.hub_root}")

        # Branch Guard (Q2-A): Warn if Hub is not on main/master
        hub_branch = self.check_hub_branch()
        if hub_branch and hub_branch not in ("main", "master"):
            print(
                f"\n⚠️ CẢNH BÁO: Hub đang ở branch '{hub_branch}', không phải 'main'.\n"
                "   Editable links có thể trỏ vào code chưa ổn định.\n"
                "   Dùng --force để bỏ qua cảnh báo này.",
                file=sys.stderr,
            )
            if not force:
                print(
                    "   → Hủy bootstrap. Checkout Hub về main hoặc chạy lại với --force.",
                    file=sys.stderr,
                )
                return 1

        # Update .gitignore first to ensure Spoke Leakage Guard & hygiene apply to all spokes
        self.ensure_gitignore_rule(dry_run=dry_run)

        # Configure version-controlled .githooks if present (all spokes including pure-docs/BIM)
        self.ensure_githooks_configured(dry_run=dry_run)

        if not self.is_python_project():
            print(
                "\n[Bootstrap] Spoke là dự án phi-Python (Pure Data/Document). Bỏ qua thiết lập Python SDK an toàn."
            )
            return 0

        packages = self.resolve_target_packages()
        print(f"Target Hub Packages ({len(packages)}): {', '.join(packages)}")

        venv_dir = self.find_venv()
        if not venv_dir:
            if auto_create_venv:
                venv_dir = self.spoke_root / ".venv"
                print(f"\n[Bootstrap] Đang tạo môi trường ảo Python mới tại: {venv_dir}...")
                if not dry_run:
                    subprocess.run(
                        [sys.executable, "-m", "venv", str(venv_dir)],
                        check=True,
                    )
            else:
                print(
                    "\n⚠️ CẢNH BÁO: Chưa tìm thấy môi trường ảo (.venv/ hoặc venv/) tại Spoke!\n"
                    "   Khuyến nghị: Chạy lệnh với cờ `--create-venv` để tự động khởi tạo .venv.",
                    file=sys.stderr,
                )
                if check_only:
                    return 1

        # Check existing editable installs
        for pkg in packages:
            pkg_path = self.hub_root / "packages" / pkg
            if not pkg_path.exists():
                print(f"❌ Error: Hub package không tồn tại trên đĩa: {pkg_path}", file=sys.stderr)
                return 1

        # Update .gitignore and generate requirements-hub.txt (with commit hash snapshot)
        self.ensure_gitignore_rule(dry_run=dry_run)
        req_path = self.generate_requirements_hub_file(packages, dry_run=dry_run)
        commit_hash = self.get_hub_commit_hash()
        print(
            f"Generated lockfile: {req_path.name} (hub_commit: {commit_hash}, đã cách ly trong .gitignore)"
        )

        if check_only:
            print("\n[Bootstrap] Check completed.")
            return 0

        if not venv_dir:
            print(
                "\nKhông thể tiếp tục cài đặt vì thiếu virtual environment. Vui lòng tạo .venv và thử lại.",
                file=sys.stderr,
            )
            return 1

        python_bin = self.get_python_exec(venv_dir)
        pip_bin = self.get_pip_exec(venv_dir)

        # Install loop: continue-on-error + summary (Q5)
        print(f"\nĐang cài đặt các packages vào {venv_dir.name}...")
        install_results: dict[str, str] = {}
        for pkg in packages:
            pkg_path = self.hub_root / "packages" / pkg
            cmd = [str(pip_bin), "install", "-e", str(pkg_path)]
            print(f"  -> pip install -e {pkg_path.name}")
            if not dry_run:
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if res.returncode == 0:
                    install_results[pkg] = "✅ Installed"
                else:
                    install_results[pkg] = f"❌ Failed: {res.stderr.strip()[:100]}"
            else:
                install_results[pkg] = "🔵 Dry-run"

        # Verification step
        print("\nKiểm tra nạp module (Verification)...")
        test_imports = {
            "ccba-harness": "import ccba_harness",
            "ccba-ai": "import ccba_ai; from ccba_ai import ai",
            "ccba-legal-intel": "import ccba_legal; from ccba_legal import LegalIntelPipeline",
            "ccba-qc-core": "import ccba_qc_core",
            "ccba-ooxml": "import ccba_ooxml",
            "ccba-pdf-prep": "import ccba_pdf_prep",
            "mdconverter": "import mdconverter",
            "ccba-notebooklm": "import ccba_notebooklm",
            "ccba-maskara": "import ccba_maskara",
        }

        verify_results: dict[str, str] = {}
        for pkg in packages:
            if install_results.get(pkg, "").startswith("❌"):
                verify_results[pkg] = "⏭️ Skipped (install failed)"
                continue
            code = test_imports.get(pkg, f"import {pkg.replace('-', '_')}")
            if not dry_run:
                v_res = subprocess.run(
                    [str(python_bin), "-c", code],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if v_res.returncode == 0:
                    verify_results[pkg] = "✅ Import OK"
                else:
                    verify_results[pkg] = f"❌ Import failed: {v_res.stderr.strip()[:80]}"
            else:
                verify_results[pkg] = "🔵 Dry-run"

        # Summary report (Q5)
        print("\n--- Bootstrap Summary ---")
        print(f"Hub commit: {commit_hash} | Branch: {hub_branch or 'unknown'}")
        has_failures = False
        for pkg in packages:
            install_s = install_results.get(pkg, "?")
            verify_s = verify_results.get(pkg, "?")
            print(f"  {pkg}: {install_s} | {verify_s}")
            if "❌" in install_s or "❌" in verify_s:
                has_failures = True

        if not has_failures:
            print(
                "\n🎉 Bootstrap hoàn tất thành công! Spoke đã được kết nối chuẩn với Hub Packages."
            )
            return 0
        else:
            print(
                "\n⚠️ Một số package gặp lỗi. Xem chi tiết bên trên và chạy lại bootstrap sau khi sửa.",
                file=sys.stderr,
            )
            return 1


def check_bootstrap_lockfile_drift(
    spoke_root: Path,
    hub_root: Path,
    *,
    bootstrapper: SpokeBootstrapper | None = None,
) -> str | None:
    """Return a warn-only diagnostic when Spoke requirements-hub.txt drifted from Hub."""
    try:
        if spoke_root.resolve() == hub_root.resolve():
            return None
    except OSError:
        pass

    req_file = spoke_root / "requirements-hub.txt"
    if not req_file.is_file():
        return None

    bs = bootstrapper or SpokeBootstrapper(spoke_root, hub_root)
    locked_commit, locked_packages = parse_requirements_hub_lockfile(req_file)
    target_packages = bs.resolve_target_packages()
    locked_set = set(locked_packages)
    new_packages = [pkg for pkg in target_packages if pkg not in locked_set]
    changed_pyprojects, unverifiable = (
        inspect_hub_git_pyproject_drift(hub_root, locked_commit, target_packages)
        if locked_commit
        else ([], None)
    )
    if not new_packages and not changed_pyprojects and not unverifiable:
        return None

    details: list[str] = []
    if new_packages:
        details.append(f"   - Target package mới chưa có trong lockfile: {', '.join(new_packages)}")
    if changed_pyprojects:
        details.append(
            f"   - Thay đổi packages/*/pyproject.toml từ {locked_commit}: {', '.join(changed_pyprojects)}"
        )
    if unverifiable:
        details.append(f"   - {unverifiable}")
    details.append(
        "   👉 Chạy lại lệnh với cờ '--bootstrap' (-b) để đồng bộ dependencies và cập nhật requirements-hub.txt."
    )
    return (
        "⚠️ [Bootstrap Drift] requirements-hub.txt tại Spoke có thể đã lệch so với Hub:\n"
        + "\n".join(details)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="CCBA Spoke Hub Package Bootstrapper")
    parser.add_argument(
        "--spoke", "-s", default=".", help="Path to Spoke repository (default: current dir)"
    )
    parser.add_argument(
        "--hub", "-H", default=None, help="Path to Platform Hub (default: auto-discover)"
    )
    parser.add_argument(
        "--create-venv", action="store_true", help="Automatically create .venv if missing"
    )
    parser.add_argument("--check-only", action="store_true", help="Check status without installing")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without modifying filesystem"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force bootstrap even if Hub is on non-main branch"
    )

    args = parser.parse_args()
    bootstrapper = SpokeBootstrapper(spoke_path=args.spoke, hub_path=args.hub)
    return bootstrapper.bootstrap(
        auto_create_venv=args.create_venv,
        dry_run=args.dry_run,
        check_only=args.check_only,
        force=args.force,
    )


if __name__ == "__main__":
    sys.exit(main())
