#!/usr/bin/env python3
"""
Deep Module for Spoke Synchronization Engine.
Handles smart Hub discovery, atomic catalog merging, selective skill/workflow copying,
test guardrail distribution, encrypted Spoke registration, and non-destructive dry-run preview.
"""

import base64
import hashlib
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Attempt importing cryptography for RSA Spoke registration
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

PLATFORM_ROOT = Path(__file__).resolve().parents[2]


class HubNotFoundError(Exception):
    """Raised when the CCBA Hub directory cannot be located."""

    pass


def load_yaml(file_path: Path) -> dict:
    """Safely load a YAML file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[Sync] Error reading {file_path.name}: {e}", file=sys.stderr)
        return {}


def are_files_identical(file1: Path, file2: Path) -> bool:
    """Compare two files by byte content."""
    if not file1.exists() or not file2.exists():
        return False
    try:
        return file1.read_bytes() == file2.read_bytes()
    except Exception:
        return False


def are_dirs_identical(dir1: Path, dir2: Path) -> bool:
    """Recursively compare two directories by file contents."""
    if not dir1.exists() or not dir2.exists():
        return False

    files1 = {p.relative_to(dir1): p for p in dir1.rglob("*") if p.is_file()}
    files2 = {p.relative_to(dir2): p for p in dir2.rglob("*") if p.is_file()}

    if set(files1.keys()) != set(files2.keys()):
        return False

    for rel_path, f1 in files1.items():
        f2 = files2[rel_path]
        try:
            if f1.read_bytes() != f2.read_bytes():
                return False
        except Exception:
            return False

    return True


class HubDiscoverer:
    """Smart Discovery Engine to locate the CCBA Hub directory."""

    def __init__(self, spoke_root: Path, context: dict, context_file: Path | None = None):
        self.spoke_root = spoke_root
        self.context = context
        self.context_file = context_file

    def _is_valid_hub(self, candidate: Path) -> bool:
        catalog = candidate / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        return catalog.exists()

    def discover(self) -> Path:
        """Locate Hub using 4-step smart discovery and auto-save if path changed."""
        hub_path_str = self.context.get("hub_path")
        if not hub_path_str and isinstance(self.context.get("project"), dict):
            hub_path_str = self.context.get("project").get("hub_path")
        hub_path_str = str(hub_path_str or "").strip()

        hub_root = None

        # Step 1: Check workspace_context.yaml
        if hub_path_str:
            candidate = Path(hub_path_str)
            if not candidate.is_absolute():
                candidate = (self.spoke_root / candidate).resolve()
            if self._is_valid_hub(candidate):
                hub_root = candidate

        # Step 2: Check Sibling directory (ccba-agent-platform)
        if not hub_root:
            sibling_hub = (self.spoke_root.parent / "ccba-agent-platform").resolve()
            if self._is_valid_hub(sibling_hub):
                hub_root = sibling_hub

        # Step 3: Check CCBA_HUB_PATH environment variable
        if not hub_root and "CCBA_HUB_PATH" in os.environ:
            env_hub = Path(os.environ["CCBA_HUB_PATH"]).resolve()
            if self._is_valid_hub(env_hub):
                hub_root = env_hub

        # Step 4: Fallback to CWD if running inside Hub
        if not hub_root:
            cwd_hub = Path.cwd().resolve()
            if self._is_valid_hub(cwd_hub):
                hub_root = cwd_hub

        if not hub_root:
            raise HubNotFoundError(
                f"[Sync] Error: Could not locate Hub directory from {self.spoke_root}.\n"
                "Please set CCBA_HUB_PATH environment variable or specify hub_path in workspace_context.yaml."
            )

        # Auto-save discovered Hub path if changed
        if hub_path_str != str(hub_root) and self.context_file and self.context_file.exists():
            self.context["hub_path"] = str(hub_root)
            try:
                with open(self.context_file, "w", encoding="utf-8") as f:
                    yaml.dump(self.context, f, allow_unicode=True)
                print(f"[Sync] Auto-saved discovered Hub path: {hub_root}")
            except Exception as e:
                print(f"[Sync] Warning: Could not save Hub path to context: {e}", file=sys.stderr)

        return hub_root


class CatalogMerger:
    """Atomic Merge & Validation Engine for catalog.yaml."""

    def __init__(self, target_path: Path):
        self.target_path = target_path

    def atomic_write(self, data: dict) -> bool:
        """Write YAML data atomically via temp file replace after safe validation."""
        temp_file = self.target_path.parent / f".{self.target_path.name}.tmp"
        try:
            self.target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True)

            # Validate generated YAML
            with open(temp_file, encoding="utf-8") as f:
                validated = yaml.safe_load(f)
                if validated is None and data != {}:
                    raise ValueError("Validation produced empty structure for non-empty data")

            # Atomic Replace
            os.replace(temp_file, self.target_path)
            return True
        except Exception as e:
            print(f"[CatalogMerger] Error during atomic write: {e}", file=sys.stderr)
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False


class SpokeRegistrar:
    """Encrypted Registration Engine for registering Spokes to Hub."""

    def register(
        self,
        spoke_root: Path,
        hub_root: Path,
        project_name: str,
        project_type: str,
        dry_run: bool = False,
    ):
        if not HAS_CRYPTOGRAPHY:
            print(
                "[Registry] Warning: cryptography package not installed. Skipping Spoke registration.",
                file=sys.stderr,
            )
            return

        public_key_path = (
            hub_root / ".agents" / "workflows" / "resources" / "registry_public_key.pem"
        )
        if not public_key_path.exists():
            return

        if dry_run:
            print(
                f"[Registry] [DRY-RUN] Would register Spoke '{project_name}' to Hub Spoke Registry (Encrypted)."
            )
            return

        try:
            with open(public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())

            spoke_info = {
                "name": project_name,
                "path": str(spoke_root.resolve()),
                "project_type": project_type,
                "last_sync": datetime.now().isoformat(),
            }
            spoke_yaml = yaml.dump(spoke_info, allow_unicode=True)

            encrypted_bytes = public_key.encrypt(
                spoke_yaml.encode("utf-8"),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")

            registry_file = hub_root / ".md" / "data" / "spoke_registry.yaml"
            registry_file.parent.mkdir(parents=True, exist_ok=True)

            registry_data = {"spokes": []}
            if registry_file.exists():
                try:
                    with open(registry_file, encoding="utf-8") as f:
                        registry_data = yaml.safe_load(f) or {"spokes": []}
                except Exception:
                    pass

            spoke_id = hashlib.sha256(str(spoke_root.resolve()).encode("utf-8")).hexdigest()

            spokes = registry_data.get("spokes", [])
            updated = False
            for s in spokes:
                if s.get("spoke_id") == spoke_id:
                    s["encrypted_data"] = encrypted_b64
                    updated = True
                    break
            if not updated:
                spokes.append({"spoke_id": spoke_id, "encrypted_data": encrypted_b64})
            registry_data["spokes"] = spokes

            CatalogMerger(registry_file).atomic_write(registry_data)
            print(
                f"[Registry] Successfully registered Spoke '{project_name}' to Hub Spoke Registry (Encrypted)."
            )
        except Exception as e:
            print(f"[Registry] Warning: Failed to register Spoke to Hub: {e}", file=sys.stderr)


class TestGuardrailCopier:
    """Distributor of test guardrails (conftest.py, safe_pytest.py) for software Spokes."""

    __test__ = False

    def __init__(self, spoke_root: Path, hub_root: Path, project_type: str):
        self.spoke_root = spoke_root
        self.hub_root = hub_root
        self.project_type = project_type

    def copy_if_needed(self, dry_run: bool = False):
        """Copy conftest.py and safe_pytest.py if Spoke is a software project."""
        if (self.spoke_root / "pyproject.toml").exists() or self.project_type == "Phần mềm":
            hub_conftest = self.hub_root / "conftest.py"
            hub_safe_pytest = self.hub_root / "scripts" / "safe_pytest.py"

            dest_conftest = self.spoke_root / "conftest.py"
            if hub_conftest.exists() and hub_conftest.resolve() != dest_conftest.resolve():
                if dry_run:
                    print("  - [DRY-RUN] Would copy test guardrail: conftest.py")
                else:
                    shutil.copy2(hub_conftest, dest_conftest)
                    print("  - Copied test guardrail: conftest.py")

            if hub_safe_pytest.exists():
                spoke_scripts_dir = self.spoke_root / "scripts"
                dest_safe_pytest = spoke_scripts_dir / "safe_pytest.py"
                if hub_safe_pytest.resolve() != dest_safe_pytest.resolve():
                    if dry_run:
                        print("  - [DRY-RUN] Would copy test wrapper CLI: scripts/safe_pytest.py")
                    else:
                        spoke_scripts_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(hub_safe_pytest, dest_safe_pytest)
                        print("  - Copied test wrapper CLI: scripts/safe_pytest.py")


class SharedSdkInspector:
    """Zero-latency static file inspector for Hub shared packages in Spoke virtual environments (ADR 0044)."""

    def __init__(self, spoke_root: Path, hub_root: Path, project_type: str):
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
        packages = ["ccba-ai", "ccba-ooxml"]

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


def safe_remove(path: Path):
    """Safely remove a directory or file without crashing on permission errors."""
    if not path.exists():
        return
    try:
        shutil.rmtree(path)
    except PermissionError:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except PermissionError:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except PermissionError:
                    pass


class SpokeSynchronizer:
    """Deep Engine managing Spoke workspace synchronization with non-destructive selective merge."""

    def __init__(self, spoke_path: str):
        self.spoke_root = Path(spoke_path).resolve()

    def _sync_single_item(
        self,
        spoke_root: Path,
        hub_root: Path,
        catalog: dict,
        sync_item: str,
        dry_run: bool = False,
    ) -> int:
        """On-Demand synchronization for a single skill or workflow."""
        mode_str = " [DRY-RUN]" if dry_run else ""
        print(f"Mode: On-Demand Synchronization for '{sync_item}'{mode_str}")
        spoke_agents_dir = spoke_root / ".agents"
        spoke_skills_dir = spoke_agents_dir / "skills"
        spoke_workflows_dir = spoke_agents_dir / "workflows"

        found = False

        # Search Skills
        for skill_entry in catalog.get("skills", []):
            if skill_entry.get("name") == sync_item:
                skill_path_rel = skill_entry.get("skill_path")
                src = hub_root / Path(skill_path_rel).parent
                dest_name = Path(skill_path_rel).parent.name
                dest = spoke_skills_dir / dest_name

                if src.exists():
                    if src.resolve() == dest.resolve():
                        found = True
                        break
                    if dry_run:
                        print(
                            f"[Sync] [DRY-RUN] Would copy skill [{sync_item}] -> {dest.relative_to(spoke_root)}"
                        )
                    else:
                        print(
                            f"[Sync] Copying skill [{sync_item}] -> {dest.relative_to(spoke_root)}"
                        )
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        safe_remove(dest)
                        shutil.copytree(src, dest)
                    found = True
                    break
                else:
                    print(f"[Sync] Error: Skill source path not found at {src}", file=sys.stderr)
                    return 1

        # Search Workflows
        if not found:
            for wf_entry in catalog.get("workflows", []):
                if wf_entry.get("name") == sync_item:
                    wf_path_rel = wf_entry.get("workflow_path")
                    src = hub_root / wf_path_rel
                    filename = Path(wf_path_rel).name
                    dest = spoke_workflows_dir / filename

                    if src.exists():
                        if src.resolve() == dest.resolve():
                            found = True
                            break
                        if dry_run:
                            print(
                                f"[Sync] [DRY-RUN] Would copy workflow [{sync_item}] -> {dest.relative_to(spoke_root)}"
                            )
                        else:
                            print(
                                f"[Sync] Copying workflow [{sync_item}] -> {dest.relative_to(spoke_root)}"
                            )
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if dest.exists():
                                dest.unlink()
                            shutil.copy2(src, dest)
                        found = True
                        break
                    else:
                        print(
                            f"[Sync] Error: Workflow source file not found at {src}",
                            file=sys.stderr,
                        )
                        return 1

        if not found:
            print(
                f"[Sync] Error: Item '{sync_item}' not found in Hub catalog.yaml.", file=sys.stderr
            )
            return 1

        # Copy constitution AGENTS.md
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists():
            if dry_run:
                print(
                    f"[Sync] [DRY-RUN] Would copy constitutional rules -> {spoke_agents_md.relative_to(spoke_root)}"
                )
            else:
                spoke_agents_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(hub_agents_md, spoke_agents_md)

        if dry_run:
            print("\n=== [DRY-RUN] On-Demand Sync Simulation Completed ===")
        else:
            print("\n=== Sync Completed Successfully ===")
        return 0

    def _sync_full_bundle(
        self,
        spoke_root: Path,
        hub_root: Path,
        catalog: dict,
        project_type: str,
        project_name: str,
        dry_run: bool = False,
    ) -> int:
        """Full synchronization with Non-Destructive Selective Merge."""
        if not project_type:
            print(
                "[Sync] Error: 'project_type' is not defined in workspace_context.yaml.",
                file=sys.stderr,
            )
            return 1

        mode_banner = " [DRY-RUN MODE]" if dry_run else ""
        print(f"Project Type: {project_type}{mode_banner}")

        bundle_defs = catalog.get("bundles", {})
        if project_type not in bundle_defs:
            available_types = ", ".join(bundle_defs.keys())
            print(
                f"[Sync] Error: Project type '{project_type}' is not registered in catalog.yaml.",
                file=sys.stderr,
            )
            print(f"[Sync] Registered types: {available_types}", file=sys.stderr)
            return 1

        required_bundles = bundle_defs[project_type]
        print(f"Required Bundles: {required_bundles}")

        spoke_agents_dir = spoke_root / ".agents"
        spoke_skills_dir = spoke_agents_dir / "skills"
        spoke_workflows_dir = spoke_agents_dir / "workflows"

        skills_to_sync = []
        wfs_to_sync = []

        # Filter Skills
        for skill_entry in catalog.get("skills", []):
            skill_name = skill_entry.get("name")
            skill_bundle = skill_entry.get("bundle")
            skill_path_rel = skill_entry.get("skill_path")

            if skill_bundle in required_bundles or skill_bundle == "_core":
                skills_to_sync.append(
                    {
                        "name": skill_name,
                        "src_dir": hub_root / Path(skill_path_rel).parent,
                        "dest_name": Path(skill_path_rel).parent.name,
                    }
                )

        # Filter Workflows
        for wf_entry in catalog.get("workflows", []):
            wf_name = wf_entry.get("name")
            wf_bundle = wf_entry.get("bundle")
            wf_path_rel = wf_entry.get("workflow_path")

            if wf_bundle in required_bundles or wf_bundle == "_core":
                wfs_to_sync.append(
                    {
                        "name": wf_name,
                        "src_file": hub_root / wf_path_rel,
                        "filename": Path(wf_path_rel).name,
                    }
                )

        # Status tracking
        actions: list[dict] = []

        # 1. Process Skills (Selective Merge)
        if not dry_run:
            spoke_skills_dir.mkdir(parents=True, exist_ok=True)

        synced_skill_folders = {sk["dest_name"] for sk in skills_to_sync}
        if spoke_skills_dir.exists():
            for existing_skill in spoke_skills_dir.iterdir():
                if existing_skill.is_dir() and existing_skill.name not in synced_skill_folders:
                    actions.append(
                        {
                            "type": "Skill",
                            "name": existing_skill.name,
                            "status": "PRESERVED",
                            "path": str(existing_skill.relative_to(spoke_root)),
                        }
                    )

        for sk in skills_to_sync:
            src = sk["src_dir"]
            dest = spoke_skills_dir / sk["dest_name"]
            if not src.exists():
                print(f"  - [Warning] Skill source path not found: {src}", file=sys.stderr)
                continue

            if src.resolve() == dest.resolve():
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                continue

            if not dest.exists():
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "NEW",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dest, dirs_exist_ok=True)
            elif are_dirs_identical(src, dest):
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
            else:
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UPDATED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    safe_remove(dest)
                    shutil.copytree(src, dest, dirs_exist_ok=True)

        # 2. Process Workflows (Non-Destructive Selective Merge)
        if not dry_run:
            spoke_workflows_dir.mkdir(parents=True, exist_ok=True)

        synced_wf_filenames = {wf["filename"] for wf in wfs_to_sync}
        if spoke_workflows_dir.exists():
            for existing_wf in spoke_workflows_dir.iterdir():
                if existing_wf.is_file() and existing_wf.name not in synced_wf_filenames:
                    actions.append(
                        {
                            "type": "Workflow",
                            "name": existing_wf.stem,
                            "status": "PRESERVED",
                            "path": str(existing_wf.relative_to(spoke_root)),
                        }
                    )

        for wf in wfs_to_sync:
            src = wf["src_file"]
            dest = spoke_workflows_dir / wf["filename"]
            if not src.exists():
                print(f"  - [Warning] Workflow source file not found: {src}", file=sys.stderr)
                continue

            if src.resolve() == dest.resolve():
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                continue

            if not dest.exists():
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "NEW",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
            elif are_files_identical(src, dest):
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
            else:
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UPDATED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)

        # 3. Copy AGENTS.md
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists() and hub_agents_md.resolve() != spoke_agents_md.resolve():
            if not spoke_agents_md.exists():
                rule_status = "NEW"
            elif are_files_identical(hub_agents_md, spoke_agents_md):
                rule_status = "UNCHANGED"
            else:
                rule_status = "UPDATED"

            actions.append(
                {
                    "type": "Rule",
                    "name": "AGENTS.md",
                    "status": rule_status,
                    "path": str(spoke_agents_md.relative_to(spoke_root)),
                }
            )
            if not dry_run and rule_status in ("NEW", "UPDATED"):
                spoke_agents_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(hub_agents_md, spoke_agents_md)

        # 4. Test guardrails
        TestGuardrailCopier(spoke_root, hub_root, project_type).copy_if_needed(dry_run=dry_run)

        # 5. Spoke registration
        SpokeRegistrar().register(spoke_root, hub_root, project_name, project_type, dry_run=dry_run)

        # 6. Print Structured Output & Summary Table
        new_count = sum(1 for a in actions if a["status"] == "NEW")
        updated_count = sum(1 for a in actions if a["status"] == "UPDATED")
        unchanged_count = sum(1 for a in actions if a["status"] == "UNCHANGED")
        preserved_count = sum(1 for a in actions if a["status"] == "PRESERVED")

        print("\n" + "=" * 90)
        print(f" CCBA SPOKE SYNC REPORT — {'[DRY-RUN SIMULATION]' if dry_run else '[EXECUTION]'}")
        print("=" * 90)
        print(f"{'Loại':<10} | {'Tên Kỹ Năng / Quy Trình':<30} | {'Trạng Thái':<12} | {'Đích Đến'}")
        print("-" * 90)
        for act in actions:
            status_symbol = {
                "NEW": "🟢 NEW",
                "UPDATED": "🔄 UPDATED",
                "UNCHANGED": "⚪ UNCHANGED",
                "PRESERVED": "🛡️ PRESERVED",
            }.get(act["status"], act["status"])
            print(f"{act['type']:<10} | {act['name']:<30} | {status_symbol:<12} | {act['path']}")
        print("-" * 90)
        print(
            f"Tổng kết: {new_count} mới, {updated_count} cập nhật, {unchanged_count} không đổi, {preserved_count} giữ nguyên nội bộ."
        )

        # 7. Zero-Latency Shared Python SDKs Inspection
        sdk_inspector = SharedSdkInspector(spoke_root, hub_root, project_type)
        sdk_recs = sdk_inspector.get_recommendations()
        if sdk_recs:
            print("\n💡 Gợi ý Shared SDKs cho Spoke Python:")
            print("   Để sử dụng AI Gateway hoặc Office Processing dùng chung từ Hub:")
            for cmd in sdk_recs:
                print(f"   -> {cmd}")

        if dry_run:
            print("\n[DRY-RUN] Quá trình mô phỏng hoàn tất. 0 tệp tin nào bị sửa đổi trên đĩa.")
        else:
            print("\n=== Sync Completed Successfully ===")
        return 0

    def sync_spoke_bundle(self, sync_item: str | None = None, dry_run: bool = False) -> int:
        """Main entrypoint for Spoke synchronization."""
        mode_str = " [DRY-RUN]" if dry_run else ""
        print(f"\n=== CCBA Spoke Synchronization{mode_str} ===")
        print(f"Target Spoke: {self.spoke_root}")

        context_file = self.spoke_root / ".agents" / "workspace_context.yaml"
        if not context_file.exists():
            context_file = self.spoke_root / ".md" / "workspace_context.yaml"

        if not context_file.exists():
            print(
                f"[Sync] Error: Could not find workspace_context.yaml in {self.spoke_root}/.agents/ or {self.spoke_root}/.md/",
                file=sys.stderr,
            )
            print(
                "[Sync] Please run 'init spoke' first in the target project folder.",
                file=sys.stderr,
            )
            return 1

        context = load_yaml(context_file)

        project_name = context.get("project_name")
        if not project_name and isinstance(context.get("project"), dict):
            project_name = context.get("project").get("name")
        if not project_name:
            project_name = self.spoke_root.name
        project_name = str(project_name).strip()

        project_type = context.get("project_type")
        if not project_type and isinstance(context.get("project"), dict):
            project_type = context.get("project").get("type")
        if not project_type:
            project_type = ""
        project_type = str(project_type).strip()

        try:
            discoverer = HubDiscoverer(self.spoke_root, context, context_file)
            hub_root = discoverer.discover()
        except HubNotFoundError as e:
            print(str(e), file=sys.stderr)
            return 1

        print(f"Hub Location: {hub_root}")

        # Auto git pull Hub if git repo (only when not dry_run)
        if (hub_root / ".git").exists() and not dry_run:
            print(
                "[Sync] Hub is a Git repository. Attempting to pull latest changes from GitHub..."
            )
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "pull"], cwd=str(hub_root), capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    print("[Sync] Git pull completed successfully.")
                    if result.stdout.strip():
                        print(f"  {result.stdout.strip()}")
                else:
                    print(
                        f"[Sync] Warning: Git pull failed with code {result.returncode}.",
                        file=sys.stderr,
                    )
                    if result.stderr.strip():
                        print(f"  {result.stderr.strip()}", file=sys.stderr)
                    print("[Sync] Continuing with local offline cache...", file=sys.stderr)
            except Exception as e:
                print(f"[Sync] Warning: Could not execute git pull: {e}", file=sys.stderr)
                print("[Sync] Continuing with local offline cache...", file=sys.stderr)

        catalog_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        if not catalog_file.exists():
            print(f"[Sync] Error: Could not find catalog.yaml at {catalog_file}", file=sys.stderr)
            return 1

        catalog = load_yaml(catalog_file)

        if sync_item:
            return self._sync_single_item(
                self.spoke_root, hub_root, catalog, sync_item, dry_run=dry_run
            )
        else:
            return self._sync_full_bundle(
                self.spoke_root,
                hub_root,
                catalog,
                project_type,
                project_name,
                dry_run=dry_run,
            )

    def sync(self, sync_item: str | None = None, dry_run: bool = False) -> int:
        """Deep Seam entry point for syncing spoke bundle."""
        return self.sync_spoke_bundle(sync_item=sync_item, dry_run=dry_run)


# Deep Seam Alias
SpokeSyncEngine = SpokeSynchronizer


def sync_project(
    spoke_path: str | Path = ".",
    sync_item: str | None = None,
    dry_run: bool = False,
) -> int:
    """Helper procedural delegate for spoke synchronization."""
    engine = SpokeSyncEngine(str(spoke_path))
    return engine.sync(sync_item=sync_item, dry_run=dry_run)


def sync_all_spokes(
    hub_root: Path | None = None,
    sync_item: str | None = None,
    dry_run: bool = False,
) -> int:
    """Batch synchronize all registered active Spokes found in Hub Registry."""
    root = hub_root or Path(__file__).resolve().parents[2]
    from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

    spokes = get_registered_spokes(hub_root=root)
    if not spokes:
        print("[BatchSync] Warning: No registered Spokes found in Hub Registry.", file=sys.stderr)
        return 1

    mode_str = " [DRY-RUN SIMULATION]" if dry_run else ""
    print("\n" + "=" * 90)
    print(f" CCBA MULTI-SPOKE BATCH SYNCHRONIZATION{mode_str}")
    print(f" Tìm thấy {len(spokes)} Spoke(s) trong Hub Registry.")
    print("=" * 90)

    results: list[dict] = []
    total_exit_code = 0

    for idx, sp in enumerate(spokes, 1):
        sp_name = sp.get("name", "Unknown")
        sp_path = sp.get("path", "")
        sp_type = sp.get("project_type", "Unknown")

        print(f"\n[{idx}/{len(spokes)}] 🔄 Đang xử lý Spoke: '{sp_name}' ({sp_type})")
        print(f"  Đường dẫn: {sp_path}")

        if not os.path.exists(sp_path):
            print("  ⚠️ Cảnh báo: Spoke không tồn tại vật lý trên ổ đĩa. Bỏ qua.")
            results.append({"name": sp_name, "path": sp_path, "status": "MISSING", "code": 1})
            continue

        try:
            engine = SpokeSynchronizer(sp_path)
            res = engine.sync(sync_item=sync_item, dry_run=dry_run)
            status = "SUCCESS" if res == 0 else "FAILED"
            results.append({"name": sp_name, "path": sp_path, "status": status, "code": res})
            if res != 0:
                total_exit_code = 1
        except Exception as e:
            print(f"  ❌ Lỗi khi đồng bộ Spoke '{sp_name}': {e}", file=sys.stderr)
            results.append({"name": sp_name, "path": sp_path, "status": f"ERROR: {e}", "code": 1})
            total_exit_code = 1

    print("\n" + "=" * 90)
    print(f" BÁO CÁO TỔNG KẾT BATCH SYNC{mode_str}")
    print("=" * 90)
    print(f"{'Tên Spoke':<25} | {'Trạng Thái':<14} | {'Đường Dẫn Vật Lý'}")
    print("-" * 90)
    for r in results:
        status_icon = (
            "✅ SUCCESS"
            if r["status"] == "SUCCESS"
            else ("⚠️ MISSING" if r["status"] == "MISSING" else f"❌ {r['status']}")
        )
        print(f"{r['name']:<25} | {status_icon:<14} | {r['path']}")
    print("=" * 90)

    return total_exit_code


def main() -> None:
    """CLI entrypoint with safe stream reconfigure."""
    import argparse

    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CCBA Spoke Synchronizer")
    parser.add_argument("--spoke", default=".", help="Path to spoke project")
    parser.add_argument("--sync-item", default=None, help="Specific skill/workflow name")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Batch synchronize all registered Spokes from Hub Registry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files on disk.",
    )
    args = parser.parse_args()

    if args.all:
        sys.exit(sync_all_spokes(sync_item=args.sync_item, dry_run=args.dry_run))
    else:
        sys.exit(sync_project(args.spoke, args.sync_item, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
