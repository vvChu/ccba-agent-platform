"""sdk_inspector.py - Shared SDK Inspector & Test Guardrail Copier.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

from .base import are_text_files_identical


def is_python_spoke(spoke_root: Path, project_type: str = "") -> bool:
    """Check if Spoke is a Python project by configuration, file presence, or scripts."""
    if (
        project_type in ("Phần mềm", "Pháp điển")
        or (spoke_root / "pyproject.toml").exists()
        or (spoke_root / "requirements.txt").exists()
        or (spoke_root / ".venv").exists()
        or (spoke_root / "venv").exists()
    ):
        return True

    # Check for any .py file in spoke root, scripts, or src
    for d in [spoke_root, spoke_root / "scripts", spoke_root / "src"]:
        if d.exists() and any(d.glob("*.py")):
            return True

    return False


class TestGuardrailCopier:
    """Distributor of test guardrails (conftest.py, safe_pytest.py) for software Spokes."""

    __test__ = False

    # Used only when the catalog has no guardrails key (ADR-0062).
    # An explicit empty list must not fall back to this constant.
    TIER0_GUARDRAIL_FALLBACK: list[dict[str, Any]] = [
        {
            "name": "conftest.py",
            "src": "conftest.py",
            "dest": "conftest.py",
            "applies_to": ["python"],
        },
        {
            "name": "safe_pytest.py",
            "src": "scripts/safe_pytest.py",
            "dest": "scripts/_guardrails/safe_pytest.py",
            "applies_to": ["python"],
        },
        {
            "name": "safe_runner.py",
            "src": "scripts/safe_runner.py",
            "dest": "scripts/_guardrails/safe_runner.py",
            "applies_to": ["python"],
        },
        {
            "name": "check_hub_import_depth.py",
            "src": "scripts/spoke/check_hub_import_depth.py",
            "dest": "scripts/_guardrails/check_hub_import_depth.py",
            "applies_to": ["python"],
        },
        {
            "name": "check_spoke_cleanliness.py",
            "src": "scripts/spoke/check_spoke_cleanliness.py",
            "dest": "scripts/_guardrails/check_spoke_cleanliness.py",
            "applies_to": ["python"],
        },
        {
            "name": "pre-commit",
            "src": ".githooks/pre-commit",
            "dest": ".githooks/pre-commit",
            "chmod": "0o755",
            "git_index": True,
            "applies_to": ["all"],
        },
        {
            "name": "pre-push",
            "src": ".githooks/pre-push",
            "dest": ".githooks/pre-push",
            "chmod": "0o755",
            "git_index": True,
            "applies_to": ["all"],
        },
    ]

    def __init__(self, spoke_root: Path, hub_root: Path, project_type: str) -> None:
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type

    def copy_if_needed(
        self,
        dry_run: bool = False,
        force: bool = False,
        catalog: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Copy declared guardrails when the Spoke is a Python project.

        ``catalog=None`` reads Hub ``catalog.yaml``. A missing ``guardrails`` key
        uses ``TIER0_GUARDRAIL_FALLBACK``. An explicit empty list copies nothing.

        Returns:
            Action records:
            {"type": "Guardrail", "name": str,
             "status": "NEW" | "UPDATED" | "UNCHANGED" | "MISSING_SRC", "path": str}
        """
        actions: list[dict[str, Any]] = []
        if not is_python_spoke(self.spoke_root, self.project_type):
            return actions

        guardrails_cfg = self._resolve_guardrails_config(catalog)
        using_fallback = guardrails_cfg is None
        if using_fallback:
            guardrails_cfg = self.TIER0_GUARDRAIL_FALLBACK
        elif guardrails_cfg == []:
            return []

        has_githooks = False
        for g in guardrails_cfg:
            if not isinstance(g, dict):
                continue
            applies = g.get("applies_to", ["python"])
            if not isinstance(applies, list):
                applies = ["python"]
            if "python" not in applies and "all" not in applies:
                continue
            src_rel = g.get("src")
            dest_rel = g.get("dest")
            name = g.get("name")
            if not isinstance(src_rel, str) or not isinstance(dest_rel, str) or not name:
                continue
            src_path = self.hub_root / src_rel
            dest_path = self.spoke_root / dest_rel

            if not src_path.is_file():
                # Fallback keeps the historical "copy what exists" behavior so
                # Spokes without a guardrails key do not gain MISSING_SRC noise.
                if not using_fallback:
                    actions.append(
                        {
                            "type": "Guardrail",
                            "name": name,
                            "status": "MISSING_SRC",
                            "path": dest_rel,
                        }
                    )
                continue

            try:
                same_path = src_path.resolve() == dest_path.resolve()
            except OSError:
                same_path = False
            if same_path:
                continue

            if not dest_path.exists():
                status = "NEW"
            elif are_text_files_identical(src_path, dest_path):
                status = "UNCHANGED"
            else:
                status = "UPDATED"

            actions.append(
                {
                    "type": "Guardrail",
                    "name": name,
                    "status": status,
                    "path": dest_rel,
                }
            )

            chmod_str = g.get("chmod")
            if not dry_run and status in ("NEW", "UPDATED"):
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                if isinstance(chmod_str, str) and chmod_str:
                    try:
                        mode = int(chmod_str, 8) if chmod_str.startswith("0o") else int(chmod_str)
                        dest_path.chmod(mode)
                    except (OSError, ValueError):
                        pass
                action_text = "Copied" if status == "NEW" else "Updated"
                print(f"  - {action_text} guardrail: {dest_rel}")
            elif dry_run and status in ("NEW", "UPDATED"):
                action_text = "Would copy" if status == "NEW" else "Would update"
                print(f"  - [DRY-RUN] {action_text} guardrail: {dest_rel}")

            # Automatic migration: if a guardrail moved to scripts/_guardrails/,
            # clean up obsolete top-level scripts/<name> in the Spoke (Issue #502).
            dest_parts = Path(dest_rel).parts
            if len(dest_parts) == 3 and dest_parts[0] == "scripts" and dest_parts[1] == "_guardrails":
                legacy_file = self.spoke_root / "scripts" / dest_parts[2]
                if legacy_file.is_file():
                    if dry_run:
                        print(f"  - [DRY-RUN] Would remove legacy guardrail: scripts/{dest_parts[2]}")
                    else:
                        try:
                            legacy_file.unlink()
                            print(f"  - Removed legacy guardrail: scripts/{dest_parts[2]}")
                        except OSError as e:
                            print(f"  - Warning: could not remove legacy guardrail scripts/{dest_parts[2]}: {e}")

            if dest_rel.startswith(".githooks/"):
                has_githooks = True

            if g.get("git_index") is True and not dry_run:
                import subprocess

                try:
                    subprocess.run(
                        [
                            "git",
                            "-C",
                            str(self.spoke_root),
                            "update-index",
                            "--add",
                            "--chmod=+x",
                            dest_rel,
                        ],
                        capture_output=True,
                        timeout=5,
                    )
                except (OSError, subprocess.SubprocessError):
                    pass

        githooks_present = (self.spoke_root / ".githooks" / "pre-commit").exists() or (
            self.spoke_root / ".githooks" / "pre-push"
        ).exists()
        if has_githooks or githooks_present:
            self._ensure_git_hook_activated(dry_run=dry_run, force=force)

        return actions

    def _resolve_guardrails_config(self, catalog: dict[str, Any] | None) -> list[Any] | None:
        """Return guardrail entries.

        None means the key is absent, the file is missing, or YAML is unreadable
        (caller uses Tier-0 fallback). A list, including ``[]``, is explicit.
        """
        loaded: dict[str, Any] | None = catalog
        if loaded is None:
            catalog_path = self.hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
            if not catalog_path.is_file():
                return None
            try:
                parsed = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
            except Exception:
                return None
            if not isinstance(parsed, dict):
                return None
            loaded = parsed
        if "guardrails" not in loaded:
            return None
        raw = loaded.get("guardrails")
        if raw is None:
            return None
        if isinstance(raw, list):
            return raw
        return []

    def _ensure_git_hook_activated(self, dry_run: bool = False, force: bool = False) -> None:
        """Configures core.hooksPath and .gitattributes for Spoke if inside a git repository."""
        import subprocess

        # Check if Spoke is a git repository
        git_dir = self.spoke_root / ".git"
        if not git_dir.exists():
            return

        # 1. Ensure .gitattributes has .githooks/* text eol=lf (idempotent, cross-platform)
        gitattributes_path = self.spoke_root / ".gitattributes"
        attr_line = ".githooks/* text eol=lf\n"
        if not dry_run:
            existing_attrs = ""
            if gitattributes_path.is_file():
                try:
                    existing_attrs = gitattributes_path.read_text(encoding="utf-8")
                except Exception:
                    existing_attrs = ""
            if ".githooks/* text eol=lf" not in existing_attrs:
                try:
                    with gitattributes_path.open("a", encoding="utf-8") as attr_file:
                        if existing_attrs and not existing_attrs.endswith("\n"):
                            attr_file.write("\n")
                        attr_file.write(attr_line)
                except Exception:
                    pass

        # 2. Check existing core.hooksPath
        existing_hookspath = ""
        try:
            cfg_check = subprocess.run(
                ["git", "-C", str(self.spoke_root), "config", "core.hooksPath"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            if cfg_check.returncode == 0:
                existing_hookspath = cfg_check.stdout.strip()
        except Exception:
            existing_hookspath = ""

        if existing_hookspath and existing_hookspath != ".githooks" and not force:
            print(
                f"  - ⚠️ [Warning] Existing git core.hooksPath detected: '{existing_hookspath}'. "
                "Skipped overwriting (use --force to override).",
                file=sys.stderr,
            )
            return

        if existing_hookspath != ".githooks":
            if dry_run:
                print("  - [DRY-RUN] Would configure git core.hooksPath=.githooks")
            else:
                try:
                    subprocess.run(
                        [
                            "git",
                            "-C",
                            str(self.spoke_root),
                            "config",
                            "core.hooksPath",
                            ".githooks",
                        ],
                        check=True,
                        capture_output=True,
                        timeout=5,
                    )
                    print("  - Configured git core.hooksPath=.githooks")
                except Exception as e:
                    print(f"  - ⚠️ Could not set git core.hooksPath: {e}", file=sys.stderr)

        # 3. Add to git index with executable bit if not dry_run (Grok Condition 3)
        if not dry_run:
            githooks_dir = self.spoke_root / ".githooks"
            if githooks_dir.is_dir():
                for hook_file in sorted(githooks_dir.iterdir()):
                    if hook_file.is_file() and not hook_file.name.endswith(
                        (".sample", ".bak", ".tmp")
                    ):
                        try:
                            subprocess.run(
                                [
                                    "git",
                                    "-C",
                                    str(self.spoke_root),
                                    "update-index",
                                    "--add",
                                    "--chmod=+x",
                                    f".githooks/{hook_file.name}",
                                ],
                                capture_output=True,
                                timeout=5,
                            )
                        except Exception:
                            pass


LEGAL_PROJECT_TYPES = {
    "Pháp điển",
    "Thẩm tra thiết kế",
    "Kiểm định",
    "Tư vấn pháp lý",
    "PCCC",
    "Tra cứu",
}


def _coerce_str_list(raw: Any) -> list[str]:
    """Normalize a workspace string or list into stripped names."""
    if isinstance(raw, str):
        text = raw.strip()
        return [text] if text else []
    if isinstance(raw, list):
        return [item.strip() for item in raw if isinstance(item, str) and item.strip()]
    return []


def _categories_from_catalog(hub_root: Path) -> dict[str, list[str]] | None:
    """Read package_bindings.categories. None means the caller keeps the legacy map."""
    catalog_path = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if not catalog_path.is_file():
        return None
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    bindings = data.get("package_bindings")
    if not isinstance(bindings, dict):
        return None
    raw_categories = bindings.get("categories")
    if not isinstance(raw_categories, list) or not raw_categories:
        return None
    categories: dict[str, list[str]] = {}
    for entry in raw_categories:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        packages = entry.get("packages")
        if not isinstance(name, str) or not name.strip() or not isinstance(packages, list):
            continue
        names = [pkg.strip() for pkg in packages if isinstance(pkg, str) and pkg.strip()]
        if names:
            categories[name.strip()] = names
    return categories or None


_LEGACY_SDK_CATEGORIES: dict[str, list[str]] = {
    "AI Gateway SDKs": ["ccba-harness", "ccba-ai"],
    "Engineering QC SDKs": ["ccba-qc-core"],
    "Office & Document Processing SDKs": ["ccba-ooxml", "ccba-pdf-prep", "mdconverter"],
    "Legal Intelligence SDKs": ["ccba-legal-intel"],
    "Extension SDKs": ["ccba-notebooklm", "ccba-maskara"],
}


def is_legal_related_spoke(spoke_root: Path, project_type: str = "") -> bool:
    """Determines if the target Spoke requires legal knowledge bundle synchronization."""
    if project_type in LEGAL_PROJECT_TYPES:
        return True
    if (spoke_root / "legal_registry.yaml").exists():
        return True
    if (spoke_root / ".md" / "data" / "legal_registry.yaml").exists():
        return True
    if (spoke_root / "legal_docs").exists():
        return True
    return False


class SharedSdkInspector:
    """Zero-latency static file inspector for Hub shared packages in Spoke virtual environments (ADR 0044)."""

    def __init__(
        self,
        spoke_root: Path,
        hub_root: Path,
        project_type: str = "",
        archetype: str = "",
    ) -> None:
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type
        self.archetype = archetype

    def is_python_project(self) -> bool:
        """Check if Spoke is a Python project by configuration, file presence, or scripts."""
        return is_python_spoke(self.spoke_root, self.project_type)

    def find_site_packages(self) -> list[Path]:
        """Locate site-packages directories across standard virtual environment folders."""
        site_packages_dirs: list[Path] = []
        candidate_venvs = [
            self.spoke_root / ".venv",
            self.spoke_root / "venv",
            self.spoke_root / "env",
            self.spoke_root / ".env",
            self.spoke_root / "scripts" / ".venv",
            self.spoke_root / "scripts" / "venv",
        ]
        for venv_path in candidate_venvs:
            if not venv_path.exists():
                continue
            # Windows: .venv/Lib/site-packages
            win_sp = venv_path / "Lib" / "site-packages"
            if win_sp.exists():
                site_packages_dirs.append(win_sp)
            # POSIX: .venv/lib/pythonX.Y/site-packages
            posix_lib = venv_path / "lib"
            if posix_lib.exists():
                for py_dir in posix_lib.glob("python*"):
                    sp = py_dir / "site-packages"
                    if sp.exists():
                        site_packages_dirs.append(sp)
        return site_packages_dirs

    def resolve_packages_to_check(self) -> list[str]:
        """Resolves the list of Hub packages to inspect for the Spoke according to ADR-0044 tiers."""
        arch = self.archetype
        declared: list[str] = []
        additional_bundles: list[str] = []

        # Read workspace_context.yaml if available
        for ctx_dir in [self.spoke_root / ".agents", self.spoke_root / ".md"]:
            ctx_file = ctx_dir / "workspace_context.yaml"
            if ctx_file.exists():
                try:
                    data = yaml.safe_load(ctx_file.read_text(encoding="utf-8")) or {}
                    raw_declared = data.get("hub_packages", [])
                    if isinstance(raw_declared, list):
                        declared.extend(
                            [p.strip() for p in raw_declared if isinstance(p, str) and p.strip()]
                        )
                    elif isinstance(raw_declared, str) and raw_declared.strip():
                        declared.append(raw_declared.strip())
                    if not arch:
                        raw_arch = (
                            data.get("project", {}).get("archetype")
                            if isinstance(data.get("project"), dict)
                            else None
                        ) or data.get("archetype")
                        if isinstance(raw_arch, str):
                            arch = raw_arch
                    project = data.get("project")
                    raw_add = data.get("additional_bundles")
                    if not raw_add and isinstance(project, dict):
                        raw_add = project.get("additional_bundles")
                    additional_bundles.extend(_coerce_str_list(raw_add))
                except Exception:
                    pass

        # Fallback to infer archetype from project_type if still empty
        if not arch and self.project_type:
            from scripts.spoke.spoke_bootstrap import PROJECT_TYPE_TO_ARCHETYPE

            raw_type = str(self.project_type).strip().lower()
            arch = PROJECT_TYPE_TO_ARCHETYPE.get(raw_type) or ""

        from scripts.spoke.spoke_bootstrap import resolve_install_set

        bound = resolve_install_set(
            self.hub_root,
            archetype=arch or "",
            project_type=self.project_type or "",
            additional_bundles=tuple(additional_bundles),
            declared_packages=tuple(declared),
            legal_related=(
                is_legal_related_spoke(self.spoke_root, self.project_type)
                or self.spoke_root.name.lower() == "ccba-legal-knowledge"
            ),
        )
        if bound is not None:
            return bound

        # Tier 0: Core mandatory packages
        packages = ["ccba-harness", "ccba-ai"]

        # Tier 1: Archetype Defaults
        if arch == "knowledge_corpus":
            if (
                is_legal_related_spoke(self.spoke_root, self.project_type)
                or self.spoke_root.name.lower() == "ccba-legal-knowledge"
            ):
                if "ccba-legal-intel" not in packages:
                    packages.append("ccba-legal-intel")
        elif arch in ("project_delivery", "enterprise_governance"):
            for p in ["ccba-ooxml", "ccba-pdf-prep", "mdconverter"]:
                if p not in packages:
                    packages.append(p)
            if arch == "project_delivery" and "ccba-qc-core" not in packages:
                packages.append("ccba-qc-core")
        else:
            # Fallback for unspecified archetypes (e.g. standalone python apps)
            if self.project_type in ("Phần mềm", "Thiết kế", "Thẩm tra thiết kế", "Kiểm định"):
                for p in ["ccba-ooxml", "ccba-pdf-prep", "mdconverter"]:
                    if p not in packages:
                        packages.append(p)
                if self.project_type != "Phần mềm" and "ccba-qc-core" not in packages:
                    packages.append("ccba-qc-core")
            elif self.project_type in ("Tác vụ Admin", "Hành chính"):
                for p in ["ccba-ooxml", "ccba-pdf-prep", "mdconverter"]:
                    if p not in packages:
                        packages.append(p)

        # Tier 2: Declared packages in workspace_context.yaml
        for p in declared:
            if p and p not in packages:
                packages.append(p)

        return packages

    def inspect(self) -> dict[str, bool]:
        """Returns {package_name: is_installed} for key Hub shared packages."""
        if not self.is_python_project():
            return {}

        packages_to_check = self.resolve_packages_to_check()
        installed_status = dict.fromkeys(packages_to_check, False)
        site_packages_dirs = self.find_site_packages()

        if not site_packages_dirs:
            return installed_status

        for sp_dir in site_packages_dirs:
            try:
                for item in sp_dir.iterdir():
                    item_name_lower = item.name.lower().replace("-", "_")
                    for pkg in packages_to_check:
                        pkg_norm = pkg.replace("-", "_")
                        if pkg_norm in item_name_lower:
                            installed_status[pkg] = True
                    # Check inside .pth files (e.g. easy-install.pth or custom .pth)
                    if item.suffix == ".pth" and item.is_file():
                        try:
                            content = item.read_text(encoding="utf-8", errors="ignore").lower()
                            for pkg in packages_to_check:
                                pkg_norm = pkg.replace("-", "_")
                                if pkg_norm in content:
                                    installed_status[pkg] = True
                        except Exception:
                            pass
            except Exception:
                pass

        return installed_status

    def get_categorized_recommendations(self) -> dict[str, list[str]]:
        """Returns actionable pip install commands categorized by SDK domain."""
        status = self.inspect()
        if not status:
            return {}
        missing = [pkg for pkg, installed in status.items() if not installed]
        if not missing:
            return {}

        categories = _categories_from_catalog(self.hub_root)
        if categories is None:
            categories = dict(_LEGACY_SDK_CATEGORIES)

        categorized_recs: dict[str, list[str]] = {}
        for cat_name, cat_pkgs in categories.items():
            cat_cmds: list[str] = []
            for pkg in cat_pkgs:
                if pkg in missing:
                    pkg_path = self.hub_root / "packages" / pkg
                    if pkg_path.exists():
                        cat_cmds.append(f'pip install -e "{pkg_path}"')
            if cat_cmds:
                categorized_recs[cat_name] = cat_cmds

        # Any extra packages not in predefined categories
        known_pkgs = {p for pkgs in categories.values() for p in pkgs}
        extra_cmds = []
        for pkg in missing:
            if pkg not in known_pkgs:
                pkg_path = self.hub_root / "packages" / pkg
                if pkg_path.exists():
                    extra_cmds.append(f'pip install -e "{pkg_path}"')
        if extra_cmds:
            categorized_recs["Other Shared SDKs"] = extra_cmds

        return categorized_recs

    def get_recommendations(self) -> list[str]:
        """Returns actionable pip install commands for unlinked shared packages."""
        cat_recs = self.get_categorized_recommendations()
        flat: list[str] = []
        for cmds in cat_recs.values():
            flat.extend(cmds)
        return flat


class LegalKnowledgeSyncOrchestrator:
    """Orchestrates automatic legal data synchronization for legal-related Spokes (ADR 0050)."""

    LEGAL_PROJECT_TYPES = LEGAL_PROJECT_TYPES

    def __init__(
        self,
        spoke_root: Path,
        hub_root: Path,
        project_type: str = "",
        archetype: str = "",
    ) -> None:
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type
        self.archetype = archetype

    def is_master_legal_corpus(self) -> bool:
        """Determines if the target Spoke is the Master Legal Corpus itself (ADR 0036/0050)."""
        if self.spoke_root.name.lower() == "ccba-legal-knowledge":
            return True

        # Check workspace_context.yaml for archetype == 'knowledge_corpus' or mode == 'knowledge'
        for ctx_dir in [self.spoke_root / ".agents", self.spoke_root / ".md"]:
            ctx_file = ctx_dir / "workspace_context.yaml"
            if ctx_file.exists():
                try:
                    data = yaml.safe_load(ctx_file.read_text(encoding="utf-8")) or {}
                    proj = data.get("project", {})
                    if isinstance(proj, dict):
                        if (
                            str(proj.get("name", "")).lower() == "ccba-legal-knowledge"
                            or proj.get("is_master") is True
                        ):
                            return True
                except Exception:
                    pass

        # Check if legal_docs exists in spoke root AND legal_registry exists at root
        if (self.spoke_root / "legal_docs").exists() and (
            (self.spoke_root / "legal_registry.yaml").exists()
            or (self.spoke_root / ".md" / "data" / "legal_registry.yaml").exists()
        ):
            pyproject = self.spoke_root / "pyproject.toml"
            if pyproject.exists():
                try:
                    if "ccba-legal-knowledge" in pyproject.read_text(encoding="utf-8"):
                        return True
                except Exception:
                    pass
            if (
                self.project_type == "Pháp điển"
                and not (self.spoke_root / ".md" / "legal_docs").exists()
            ):
                return True

        return False

    def is_legal_related_spoke(self) -> bool:
        """Determines if the target Spoke requires legal knowledge bundle synchronization."""
        if self.project_type in self.LEGAL_PROJECT_TYPES:
            return True
        if (self.spoke_root / "legal_registry.yaml").exists():
            return True
        if (self.spoke_root / ".md" / "data" / "legal_registry.yaml").exists():
            return True
        if (self.spoke_root / "legal_docs").exists():
            return True
        return False

    def sync_or_advise(self, dry_run: bool = False, pull_assets: bool = False) -> dict[str, Any]:
        """Executes automatic Two-Tier Legal Sync for legal Spokes or emits zero-bloat advisory.

        Returns:
            Dict containing action taken and status report.
        """
        if self.is_master_legal_corpus():
            print(
                "\n📚 [Legal Sync] Spoke hiện tại là Master Legal Corpus ('ccba-legal-knowledge')."
            )
            print(
                "   🛡️ Bảo tồn cấu trúc dữ liệu nguyên bản, bỏ qua sao chép nội bộ (ADR 0036 & ADR 0050)."
            )
            return {
                "is_legal": True,
                "is_master": True,
                "dry_run": dry_run,
                "status": "master_corpus_preserved",
            }

        if self.is_legal_related_spoke():
            print("\n📚 [Legal Sync] Tự động đồng bộ Tri thức Pháp lý (ADR 0050):")
            if dry_run:
                if pull_assets:
                    print(
                        "   - [DRY-RUN] [Full Assets] Sẽ kiểm tra và kéo gói OKF v2.4 chuẩn cùng sáp nhập legal_registry.yaml"
                    )
                else:
                    print(
                        "   - [DRY-RUN] [Zero-Bloat Reference] Sẽ sáp nhập legal_registry.yaml (Reference-Only, không sao chép legal_docs/)"
                    )
                return {"is_legal": True, "dry_run": True, "status": "simulated"}

            try:
                # Add packages/ccba-legal-intel/src to sys.path if not present
                import sys

                legal_pkg_path = self.hub_root / "packages" / "ccba-legal-intel" / "src"
                if legal_pkg_path.exists() and str(legal_pkg_path) not in sys.path:
                    sys.path.insert(0, str(legal_pkg_path))

                from ccba_legal.sync import sync_legal_assets

                res = sync_legal_assets(
                    target_dir=self.spoke_root / ".md" / "legal_docs",
                    project_root=self.spoke_root,
                    pull_assets=pull_assets,
                )
                if res.get("status") == "success":
                    copied = len(res.get("bundles_synced", []))
                    if pull_assets:
                        msg = res.get("message", "Đồng bộ thành công")
                        print(f"   ✅ {msg} ({copied} gói văn bản đã đồng bộ).")
                    else:
                        reg_summary = res.get("registry_merge", {})
                        reg_info = f"updated={reg_summary.get('updated', 0)}, added={reg_summary.get('added', 0)}"
                        print(
                            f"   ✅ [Zero-Bloat Reference] Sáp nhập legal_registry.yaml thành công ({reg_info})."
                        )
                        print(
                            "      💡 Bật cờ '--pull-assets' nếu Spoke thực sự cần sao chép vật lý legal_docs/."
                        )
                else:
                    print(f"   ℹ️ {res.get('message', 'Không có dữ liệu mới.')}")
                return {"is_legal": True, "dry_run": False, "result": res}
            except Exception as e:
                print(f"   ⚠️ Không thể nạp trực tiếp module sync: {e}")
                print("   Khuyến nghị chạy: python -m ccba_legal sync --pull-latest")
                return {"is_legal": True, "dry_run": False, "error": str(e)}
        else:
            display_type = self.archetype or self.project_type or "Chung"
            print("\n💡 [Khuyến nghị Tri thức Pháp lý (Zero-Bloat)]:")
            print(
                f"   Spoke hiện tại thuộc phân hệ '{display_type}', không bắt buộc tải trước toàn bộ kho văn bản OKF v2.4 (tiết kiệm dung lượng đĩa)."
            )
            print(
                "   Khi cần tra cứu văn bản cụ thể, hãy dùng lệnh On-Demand: 'python -m ccba_legal sync --doc <doc_id>' hoặc tra cứu RAG qua AI Gateway."
            )
            return {"is_legal": False, "dry_run": dry_run, "status": "advised_zero_bloat"}
