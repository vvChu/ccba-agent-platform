"""sdk_inspector.py - Shared SDK Inspector & Test Guardrail Copier.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml


class TestGuardrailCopier:
    """Distributor of test guardrails (conftest.py, safe_pytest.py) for software Spokes."""

    __test__ = False

    def __init__(self, spoke_root: Path, hub_root: Path, project_type: str) -> None:
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type

    def copy_if_needed(self, dry_run: bool = False) -> None:
        """Copy conftest.py, safe_pytest.py, and pre-commit guardrails if Spoke is a Python project."""
        is_python = (
            self.project_type in ("Phần mềm", "Pháp điển")
            or (self.spoke_root / "pyproject.toml").exists()
            or (self.spoke_root / "requirements.txt").exists()
            or (self.spoke_root / ".venv").exists()
        )

        if is_python:
            spoke_scripts_dir = self.spoke_root / "scripts"

            # 1. conftest.py
            hub_conftest = self.hub_root / "conftest.py"
            dest_conftest = self.spoke_root / "conftest.py"
            if hub_conftest.exists() and hub_conftest.resolve() != dest_conftest.resolve():
                if dry_run:
                    print("  - [DRY-RUN] Would copy test guardrail: conftest.py")
                else:
                    shutil.copy2(hub_conftest, dest_conftest)
                    print("  - Copied test guardrail: conftest.py")

            # 2. safe_pytest.py
            hub_safe_pytest = self.hub_root / "scripts" / "safe_pytest.py"
            if hub_safe_pytest.exists():
                dest_safe_pytest = spoke_scripts_dir / "safe_pytest.py"
                if hub_safe_pytest.resolve() != dest_safe_pytest.resolve():
                    if dry_run:
                        print("  - [DRY-RUN] Would copy test wrapper CLI: scripts/safe_pytest.py")
                    else:
                        spoke_scripts_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(hub_safe_pytest, dest_safe_pytest)
                        print("  - Copied test wrapper CLI: scripts/safe_pytest.py")

            # 3. check_hub_import_depth.py (ADR 0044 §7)
            hub_import_depth = self.hub_root / "scripts" / "spoke" / "check_hub_import_depth.py"
            if hub_import_depth.exists():
                dest_import_depth = spoke_scripts_dir / "check_hub_import_depth.py"
                if hub_import_depth.resolve() != dest_import_depth.resolve():
                    if dry_run:
                        print(
                            "  - [DRY-RUN] Would copy guardrail: scripts/check_hub_import_depth.py"
                        )
                    else:
                        spoke_scripts_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(hub_import_depth, dest_import_depth)
                        print("  - Copied guardrail: scripts/check_hub_import_depth.py")

            # 4. check_spoke_cleanliness.py (ADR 0044 / Issue #215)
            hub_cleanliness = self.hub_root / "scripts" / "spoke" / "check_spoke_cleanliness.py"
            if hub_cleanliness.exists():
                dest_cleanliness = spoke_scripts_dir / "check_spoke_cleanliness.py"
                if hub_cleanliness.resolve() != dest_cleanliness.resolve():
                    if dry_run:
                        print(
                            "  - [DRY-RUN] Would copy guardrail: scripts/check_spoke_cleanliness.py"
                        )
                    else:
                        spoke_scripts_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(hub_cleanliness, dest_cleanliness)
                        print("  - Copied guardrail: scripts/check_spoke_cleanliness.py")


class SharedSdkInspector:
    """Zero-latency static file inspector for Hub shared packages in Spoke virtual environments (ADR 0044)."""

    def __init__(self, spoke_root: Path, hub_root: Path, project_type: str) -> None:
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type

    def is_python_project(self) -> bool:
        """Check if Spoke is a Python project by configuration, file presence, or scripts."""
        if (
            self.project_type == "Phần mềm"
            or (self.spoke_root / "pyproject.toml").exists()
            or (self.spoke_root / "requirements.txt").exists()
            or (self.spoke_root / ".venv").exists()
            or (self.spoke_root / "venv").exists()
        ):
            return True

        # Check for any .py file in spoke
        for d in [self.spoke_root, self.spoke_root / "scripts", self.spoke_root / "src"]:
            if d.exists() and any(d.glob("*.py")):
                return True

        return False

    def find_site_packages(self) -> list[Path]:
        """Locate site-packages directories across standard virtual environment folders."""
        site_packages_dirs: list[Path] = []
        for venv_name in [".venv", "venv", "env", ".env"]:
            venv_path = self.spoke_root / venv_name
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
        """Resolves the list of Hub packages to inspect for the Spoke."""
        packages = ["ccba-harness", "ccba-ai", "ccba-ooxml"]

        # Read workspace_context.yaml if available
        for ctx_dir in [self.spoke_root / ".agents", self.spoke_root / ".md"]:
            ctx_file = ctx_dir / "workspace_context.yaml"
            if ctx_file.exists():
                try:
                    data = yaml.safe_load(ctx_file.read_text(encoding="utf-8")) or {}
                    declared = data.get("hub_packages", [])
                    if isinstance(declared, list):
                        for p in declared:
                            if p and p not in packages:
                                packages.append(p)
                    # If knowledge_corpus archetype, check ccba-legal-intel
                    if data.get("project", {}).get("archetype") == "knowledge_corpus":
                        if "ccba-legal-intel" not in packages:
                            packages.append("ccba-legal-intel")
                except Exception:
                    pass

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

    def get_recommendations(self) -> list[str]:
        """Returns actionable pip install commands for unlinked shared packages."""
        status = self.inspect()
        if not status:
            return []
        missing = [pkg for pkg, installed in status.items() if not installed]
        if not missing:
            return []
        commands: list[str] = []
        for pkg in missing:
            pkg_path = self.hub_root / "packages" / pkg
            if pkg_path.exists():
                commands.append(f'pip install -e "{pkg_path}"')
        return commands


class LegalKnowledgeSyncOrchestrator:
    """Orchestrates automatic legal data synchronization for legal-related Spokes (ADR 0050)."""

    LEGAL_PROJECT_TYPES = {
        "Pháp điển",
        "Thẩm tra thiết kế",
        "Kiểm định",
        "Tư vấn pháp lý",
        "PCCC",
    }

    def __init__(self, spoke_root: Path, hub_root: Path, project_type: str) -> None:
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type

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
                            proj.get("archetype") == "knowledge_corpus"
                            or proj.get("mode") == "knowledge"
                            or proj.get("name") == "ccba-legal-knowledge"
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
            print("\n💡 [Khuyến nghị Tri thức Pháp lý (Zero-Bloat)]:")
            print(
                f"   Spoke hiện tại thuộc phân hệ '{self.project_type or 'Chung'}', không bắt buộc tải trước toàn bộ kho văn bản OKF v2.4 (tiết kiệm dung lượng đĩa)."
            )
            print(
                "   Khi cần tra cứu văn bản cụ thể, hãy dùng lệnh On-Demand: 'python -m ccba_legal sync --doc <doc_id>' hoặc tra cứu RAG qua AI Gateway."
            )
            return {"is_legal": False, "dry_run": dry_run, "status": "advised_zero_bloat"}
