"""sdk_inspector.py - Shared SDK Inspector & Test Guardrail Copier.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from .base import are_files_identical


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

    def __init__(self, spoke_root: Path, hub_root: Path, project_type: str) -> None:
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type

    def copy_if_needed(self, dry_run: bool = False) -> list[dict[str, Any]]:
        """Copy conftest.py, safe_pytest.py, and pre-commit guardrails if Spoke is a Python project.

        Returns:
            List of action records with format:
            {"type": "Guardrail", "name": str, "status": "NEW" | "UPDATED" | "UNCHANGED", "path": str}
        """
        actions: list[dict[str, Any]] = []
        is_python = is_python_spoke(self.spoke_root, self.project_type)

        if not is_python:
            return actions

        spoke_scripts_dir = self.spoke_root / "scripts"

        items_to_copy = [
            (
                self.hub_root / "conftest.py",
                self.spoke_root / "conftest.py",
                "conftest.py",
                "conftest.py",
            ),
            (
                self.hub_root / "scripts" / "safe_pytest.py",
                spoke_scripts_dir / "safe_pytest.py",
                "safe_pytest.py",
                "scripts/safe_pytest.py",
            ),
            (
                self.hub_root / "scripts" / "spoke" / "check_hub_import_depth.py",
                spoke_scripts_dir / "check_hub_import_depth.py",
                "check_hub_import_depth.py",
                "scripts/check_hub_import_depth.py",
            ),
            (
                self.hub_root / "scripts" / "spoke" / "check_spoke_cleanliness.py",
                spoke_scripts_dir / "check_spoke_cleanliness.py",
                "check_spoke_cleanliness.py",
                "scripts/check_spoke_cleanliness.py",
            ),
        ]

        for src, dest, name, rel_path in items_to_copy:
            if not src.exists() or src.resolve() == dest.resolve():
                continue

            if not dest.exists():
                status = "NEW"
            elif are_files_identical(src, dest):
                status = "UNCHANGED"
            else:
                status = "UPDATED"

            actions.append(
                {
                    "type": "Guardrail",
                    "name": name,
                    "status": status,
                    "path": rel_path,
                }
            )

            if not dry_run and status in ("NEW", "UPDATED"):
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                action_text = "Copied" if status == "NEW" else "Updated"
                print(f"  - {action_text} guardrail: {rel_path}")
            elif dry_run and status in ("NEW", "UPDATED"):
                action_text = "Would copy" if status == "NEW" else "Would update"
                print(f"  - [DRY-RUN] {action_text} guardrail: {rel_path}")

        return actions


LEGAL_PROJECT_TYPES = {
    "Pháp điển",
    "Thẩm tra thiết kế",
    "Kiểm định",
    "Tư vấn pháp lý",
    "PCCC",
    "Tra cứu",
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
        # Tier 0: Core mandatory packages
        packages = ["ccba-harness", "ccba-ai"]

        arch = self.archetype
        declared: list[str] = []

        # Read workspace_context.yaml if available
        for ctx_dir in [self.spoke_root / ".agents", self.spoke_root / ".md"]:
            ctx_file = ctx_dir / "workspace_context.yaml"
            if ctx_file.exists():
                try:
                    data = yaml.safe_load(ctx_file.read_text(encoding="utf-8")) or {}
                    raw_declared = data.get("hub_packages", [])
                    if isinstance(raw_declared, list):
                        declared.extend([p for p in raw_declared if isinstance(p, str) and p])
                    elif isinstance(raw_declared, str) and raw_declared:
                        declared.append(raw_declared)
                    if not arch:
                        arch = data.get("project", {}).get("archetype") or data.get("archetype")
                except Exception:
                    pass

        # Fallback to infer archetype from project_type if still empty
        if not arch and self.project_type:
            from scripts.spoke.spoke_bootstrap import PROJECT_TYPE_TO_ARCHETYPE

            raw_type = str(self.project_type).strip().lower()
            arch = PROJECT_TYPE_TO_ARCHETYPE.get(raw_type)

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

        categories: dict[str, list[str]] = {
            "AI Gateway SDKs": ["ccba-harness", "ccba-ai"],
            "Engineering QC SDKs": ["ccba-qc-core"],
            "Office & Document Processing SDKs": ["ccba-ooxml", "ccba-pdf-prep", "mdconverter"],
            "Legal Intelligence SDKs": ["ccba-legal-intel"],
            "Extension SDKs": ["ccba-notebooklm", "ccba-maskara"],
        }

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

    def sync_or_advise(self, dry_run: bool = False) -> dict[str, Any]:
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
                print(
                    "   - [DRY-RUN] Sẽ kiểm tra và kéo gói OKF v2.4 chuẩn cùng sáp nhập legal_registry.yaml"
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
                )
                if res.get("status") == "success":
                    copied = res.get("copied_docs", 0)
                    msg = res.get("message", "Đồng bộ thành công")
                    print(f"   ✅ {msg} ({copied} gói văn bản đã đồng bộ).")
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
