#!/usr/bin/env python3
"""
Deep Module for Spoke Synchronization Engine.
Handles smart Hub discovery, atomic catalog merging, selective skill/workflow copying,
test guardrail distribution, and encrypted Spoke registration.
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


class HubDiscoverer:
    """Smart Discovery Engine to locate the CCBA Hub directory."""

    def __init__(self, spoke_root: Path, context: dict, context_file: Path = None):
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

    def register(self, spoke_root: Path, hub_root: Path, project_name: str, project_type: str):
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

    def copy_if_needed(self):
        """Copy conftest.py and safe_pytest.py if Spoke is a software project."""
        if (self.spoke_root / "pyproject.toml").exists() or self.project_type == "Phần mềm":
            hub_conftest = self.hub_root / "conftest.py"
            hub_safe_pytest = self.hub_root / "scripts" / "safe_pytest.py"

            if (
                hub_conftest.exists()
                and hub_conftest.resolve() != (self.spoke_root / "conftest.py").resolve()
            ):
                shutil.copy2(hub_conftest, self.spoke_root / "conftest.py")
                print("  - Copied test guardrail: conftest.py")

            if hub_safe_pytest.exists():
                spoke_scripts_dir = self.spoke_root / "scripts"
                spoke_scripts_dir.mkdir(parents=True, exist_ok=True)
                dest_safe_pytest = spoke_scripts_dir / "safe_pytest.py"
                if hub_safe_pytest.resolve() != dest_safe_pytest.resolve():
                    shutil.copy2(hub_safe_pytest, dest_safe_pytest)
                    print("  - Copied test wrapper CLI: scripts/safe_pytest.py")


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
    """Deep Engine managing Spoke workspace synchronization."""

    def __init__(self, spoke_path: str):
        self.spoke_root = Path(spoke_path).resolve()

    def _sync_single_item(
        self, spoke_root: Path, hub_root: Path, catalog: dict, sync_item: str
    ) -> int:
        """On-Demand synchronization for a single skill or workflow."""
        print(f"Mode: On-Demand Synchronization for '{sync_item}'")
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
                    print(f"[Sync] Copying skill [{sync_item}] -> {dest.relative_to(spoke_root)}")
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
            shutil.copy2(hub_agents_md, spoke_agents_md)

        print("\n=== Sync Completed Successfully ===")
        return 0

    def _sync_full_bundle(
        self,
        spoke_root: Path,
        hub_root: Path,
        catalog: dict,
        project_type: str,
        project_name: str,
    ) -> int:
        """Full synchronization according to Spoke project_type."""
        if not project_type:
            print(
                "[Sync] Error: 'project_type' is not defined in workspace_context.yaml.",
                file=sys.stderr,
            )
            return 1

        print(f"Project Type: {project_type}")

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

        is_same_root = spoke_root.resolve() == hub_root.resolve()

        if not is_same_root:
            safe_remove(spoke_workflows_dir)
        spoke_workflows_dir.mkdir(parents=True, exist_ok=True)
        spoke_skills_dir.mkdir(parents=True, exist_ok=True)

        print("\n[Sync] Copying skills...")
        copied_skills_count = 0
        for sk in skills_to_sync:
            src = sk["src_dir"]
            dest = spoke_skills_dir / sk["dest_name"]
            if src.exists():
                if src.resolve() == dest.resolve():
                    copied_skills_count += 1
                    continue
                print(f"  - [{sk['name']}] -> {dest.relative_to(spoke_root)}")
                try:
                    safe_remove(dest)
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                    copied_skills_count += 1
                except Exception as e:
                    print(f"  - [Cảnh báo] Lỗi ghi đè skill {sk['name']}: {e}", file=sys.stderr)
            else:
                print(f"  - [Warning] Skill source path not found: {src}", file=sys.stderr)

        print("\n[Sync] Copying workflows...")
        copied_wfs_count = 0
        for wf in wfs_to_sync:
            src = wf["src_file"]
            dest = spoke_workflows_dir / wf["filename"]
            if src.exists():
                if src.resolve() == dest.resolve():
                    copied_wfs_count += 1
                    continue
                print(f"  - [{wf['name']}] -> {dest.relative_to(spoke_root)}")
                shutil.copy2(src, dest)
                copied_wfs_count += 1
            else:
                print(f"  - [Warning] Workflow source file not found: {src}", file=sys.stderr)

        # Copy AGENTS.md
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists() and hub_agents_md.resolve() != spoke_agents_md.resolve():
            print(
                f"\n[Sync] Copying constitutional rules (AGENTS.md) -> {spoke_agents_md.relative_to(spoke_root)}"
            )
            shutil.copy2(hub_agents_md, spoke_agents_md)

        # Copy test guardrails
        TestGuardrailCopier(spoke_root, hub_root, project_type).copy_if_needed()

        # Register Spoke to Hub
        SpokeRegistrar().register(spoke_root, hub_root, project_name, project_type)

        print("\n=== Sync Completed Successfully ===")
        print(f"Synced {copied_skills_count} skills and {copied_wfs_count} workflows.")
        print("Project now structured native for Google Antigravity Auto-Discovery.")
        return 0

    def sync_spoke_bundle(self, sync_item: str = None) -> int:
        """Main entrypoint for Spoke synchronization."""
        print("\n=== CCBA Spoke Synchronization ===")
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

        # Auto git pull Hub if git repo
        if (hub_root / ".git").exists():
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
            return self._sync_single_item(self.spoke_root, hub_root, catalog, sync_item)
        else:
            return self._sync_full_bundle(
                self.spoke_root, hub_root, catalog, project_type, project_name
            )

    def sync(self, sync_item: str | None = None) -> int:
        """Deep Seam entry point for syncing spoke bundle."""
        return self.sync_spoke_bundle(sync_item=sync_item)


# Deep Seam Alias
SpokeSyncEngine = SpokeSynchronizer


def sync_project(spoke_path: str | Path = ".", sync_item: str | None = None) -> int:
    """Helper procedural delegate for spoke synchronization."""
    engine = SpokeSyncEngine(spoke_path)
    return engine.sync(sync_item=sync_item)


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
    args = parser.parse_args()
    sys.exit(sync_project(args.spoke, args.sync_item))


if __name__ == "__main__":
    main()
