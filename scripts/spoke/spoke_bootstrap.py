"""CCBA Spoke Bootstrap Engine — Automated Hub Packages Editable Link & Venv Setup.

This module automates the connection between Spoke Python workspaces and Hub packages
via standard editable installs (`pip install -e`), completely replacing brittle `sys.path.insert` hacks.
Complies with ADR 0044.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


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


# Dependency topology order: harness must be first, then ai, then domain packages
PACKAGE_TOPOLOGY_ORDER = [
    "ccba-harness",
    "ccba-ai",
    "ccba-legal-intel",
    "ccba-ooxml",
    "ccba-pdf-prep",
    "mdconverter",
    "ccba-notebooklm",
    "ccba-maskara",
]

ARCHETYPE_TIER1_DEFAULTS = {
    "knowledge_corpus": ["ccba-legal-intel"],
    "project_delivery": ["ccba-ooxml", "ccba-pdf-prep"],
    "enterprise_governance": ["ccba-ooxml"],
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
        """Dynamically resolves the Hub root repository path."""
        # 1. Environment variable
        env_hub = os.environ.get("CCBA_HUB_PATH")
        if env_hub and Path(env_hub).exists():
            return Path(env_hub).resolve()

        # 2. Workspace context (lazy yaml — graceful fallback)
        for ctx_dir in [self.spoke_root / ".agents", self.spoke_root / ".md"]:
            ctx_file = ctx_dir / "workspace_context.yaml"
            if ctx_file.exists():
                data = _safe_load_yaml(ctx_file)
                hub_config = data.get("hub", {}).get("path") or data.get("hub_path")
                if hub_config and Path(hub_config).exists():
                    return Path(hub_config).resolve()

        # 3. Known relative / standard locations (no hardcoded paths — ADR 0044)
        candidates = [
            Path(__file__).resolve().parent.parent.parent,  # scripts/spoke/ -> hub root
            self.spoke_root.parent / "ccba-agent-platform",
        ]
        for cand in candidates:
            if cand.exists() and (cand / "packages" / "ccba-harness").exists():
                return cand.resolve()

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

        if proj_type == "Phần mềm" or proj_mode == "software":
            return True

        if (self.spoke_root / "pyproject.toml").exists():
            return True
        if (self.spoke_root / "requirements.txt").exists():
            return True
        if (self.spoke_root / ".venv").exists() or (self.spoke_root / "venv").exists():
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
        for venv_name in [".venv", "venv", "env"]:
            v_dir = self.spoke_root / venv_name
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

    def resolve_target_packages(self) -> list[str]:
        """Resolves target packages according to Tier 0 + Tier 1 + Tier 2 rules.

        Returns ordered list matching topological dependency order.
        """
        target_set: set[str] = set()

        # Tier 0: Core platform packages (always required for Python projects)
        target_set.add("ccba-harness")
        target_set.add("ccba-ai")

        context = self.read_workspace_context()
        proj = context.get("project", {})
        archetype = proj.get("archetype", "")

        # Declared packages in workspace_context.yaml
        declared = context.get("hub_packages", [])
        if isinstance(declared, list):
            for pkg in declared:
                if isinstance(pkg, str) and pkg.strip():
                    target_set.add(pkg.strip())
        elif isinstance(declared, str) and declared.strip():
            target_set.add(declared.strip())

        # Archetype Tier 1 defaults if not explicitly disabled
        if not declared and archetype in ARCHETYPE_TIER1_DEFAULTS:
            for default_pkg in ARCHETYPE_TIER1_DEFAULTS[archetype]:
                target_set.add(default_pkg)

        # Sort according to topology order
        ordered: list[str] = []
        for pkg in PACKAGE_TOPOLOGY_ORDER:
            if pkg in target_set:
                ordered.append(pkg)
                target_set.remove(pkg)

        # Any extra packages not in predefined list
        ordered.extend(sorted(target_set))
        return ordered

    def ensure_gitignore_rule(self, dry_run: bool = False) -> bool:
        """Ensures requirements-hub.txt and Spoke Leakage Guard rules are included in .gitignore."""
        gitignore_path = self.spoke_root / ".gitignore"
        rules = [
            "requirements-hub.txt",
            ".md/teach/",
            ".md/scratch/",
            ".tmp/",
            ".out-of-scope/",
        ]

        if not gitignore_path.exists():
            if not dry_run:
                header = "# Hub auto-generated editable links & Spoke Leakage Guard (ADR 0045)\n"
                gitignore_path.write_text(header + "\n".join(rules) + "\n", encoding="utf-8")
            return True

        content = gitignore_path.read_text(encoding="utf-8")
        missing_rules = [r for r in rules if r not in content]
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

    def get_hub_commit_hash(self) -> str:
        """Returns the current HEAD commit hash of the Hub repository."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.hub_root),
                capture_output=True,
                text=True,
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
                res = subprocess.run(cmd, capture_output=True, text=True)
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
