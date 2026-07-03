#!/usr/bin/env python3
"""
Sync Spoke Script for ccba-agent-platform.
Synchronizes skills and workflows from the Hub to a Spoke project directory
based on the Spoke's business project type specified in workspace_context.yaml.
"""

import argparse
import os
import shutil
import sys
import yaml
import base64
import hashlib
from datetime import datetime
from pathlib import Path

try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def load_yaml(file_path: Path) -> dict:
    """Safely load a YAML file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[Sync] Error reading {file_path.name}: {e}", file=sys.stderr)
        return {}


def register_spoke_to_hub(spoke_root: Path, hub_root: Path, project_name: str, project_type: str) -> None:
    """Register Spoke metadata to Hub using RSA public key encryption."""
    if not HAS_CRYPTOGRAPHY:
        print("[Registry] Warning: cryptography package not installed. Skipping Spoke registration.", file=sys.stderr)
        return

    public_key_path = hub_root / ".agents" / "workflows" / "resources" / "registry_public_key.pem"
    if not public_key_path.exists():
        # Admin chưa cấu hình keys (bỏ qua register)
        return

    try:
        # 1. Đọc Khóa công khai
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        # 2. Chuẩn bị payload thông tin Spoke
        spoke_info = {
            "name": project_name,
            "path": str(spoke_root.resolve()),
            "project_type": project_type,
            "last_sync": datetime.now().isoformat()
        }
        spoke_yaml = yaml.dump(spoke_info, allow_unicode=True)

        # 3. Mã hóa RSA và chuyển sang Base64
        encrypted_bytes = public_key.encrypt(
            spoke_yaml.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')

        # 4. Ghi nhận vào registry trên Hub
        registry_file = hub_root / ".md" / "data" / "spoke_registry.yaml"
        registry_file.parent.mkdir(parents=True, exist_ok=True)

        registry_data = {"spokes": []}
        if registry_file.exists():
            try:
                with open(registry_file, "r", encoding="utf-8") as f:
                    registry_data = yaml.safe_load(f) or {"spokes": []}
            except Exception:
                pass

        # Tạo Spoke ID duy nhất băm từ đường dẫn vật lý để tránh trùng lặp
        spoke_id = hashlib.sha256(str(spoke_root.resolve()).encode('utf-8')).hexdigest()

        # Cập nhật hoặc thêm mới bản ghi
        spokes = registry_data.get("spokes", [])
        updated = False
        for s in spokes:
            if s.get("spoke_id") == spoke_id:
                s["encrypted_data"] = encrypted_b64
                updated = True
                break
        if not updated:
            spokes.append({
                "spoke_id": spoke_id,
                "encrypted_data": encrypted_b64
            })
        registry_data["spokes"] = spokes

        with open(registry_file, "w", encoding="utf-8") as f:
            yaml.dump(registry_data, f, allow_unicode=True)
            
        print(f"[Registry] Successfully registered Spoke '{project_name}' to Hub Spoke Registry (Encrypted).")
    except Exception as e:
        print(f"[Registry] Warning: Failed to register Spoke to Hub: {e}", file=sys.stderr)


def sync_project(spoke_path: str, sync_item: str = None) -> int:
    """Perform selective synchronization of skills/workflows from Hub to Spoke.

    Args:
        spoke_path: Path to the target Spoke directory.
        sync_item: Optional name of a specific skill or workflow to sync.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    spoke_root = Path(spoke_path).resolve()
    print(f"\n=== CCBA Spoke Synchronization ===")
    print(f"Target Spoke: {spoke_root}")

    # 1. Locate workspace_context.yaml
    # Check both .agents/ and .md/ (for backward compatibility)
    context_file = spoke_root / ".agents" / "workspace_context.yaml"
    if not context_file.exists():
        context_file = spoke_root / ".md" / "workspace_context.yaml"

    if not context_file.exists():
        print(
            f"[Sync] Error: Could not find workspace_context.yaml in {spoke_root}/.agents/ or {spoke_root}/.md/",
            file=sys.stderr
        )
        print("[Sync] Please run 'init spoke' first in the target project folder.", file=sys.stderr)
        return 1

    # Load spoke context
    context = load_yaml(context_file)
    
    # Support both flat and nested structure
    project_name = context.get("project_name")
    if not project_name and isinstance(context.get("project"), dict):
        project_name = context.get("project").get("name")
    if not project_name:
        project_name = spoke_root.name
    project_name = str(project_name).strip()
    
    project_type = context.get("project_type")
    if not project_type and isinstance(context.get("project"), dict):
        project_type = context.get("project").get("type")
    if not project_type:
        project_type = ""
    project_type = str(project_type).strip()
    
    hub_path_str = context.get("hub_path")
    if not hub_path_str and isinstance(context.get("project"), dict):
        hub_path_str = context.get("project").get("hub_path")
    if not hub_path_str:
        hub_path_str = ""
    hub_path_str = str(hub_path_str).strip()

    # 2. Locate Hub (Smart Discovery)
    hub_root = None
    
    # Thử 1: Dùng đường dẫn trong context file
    if hub_path_str:
        candidate = Path(hub_path_str)
        if not candidate.is_absolute():
            candidate = (spoke_root / candidate).resolve()
        if (candidate / ".agents" / "skills" / "platform-loader" / "catalog.yaml").exists():
            hub_root = candidate

    # Thử 2: Quét thư mục cùng cấp (Sibling discovery)
    if not hub_root:
        sibling_hub = (spoke_root.parent / "ccba-agent-platform").resolve()
        if (sibling_hub / ".agents" / "skills" / "platform-loader" / "catalog.yaml").exists():
            hub_root = sibling_hub

    # Thử 3: Đọc biến môi trường
    if not hub_root and "CCBA_HUB_PATH" in os.environ:
        env_hub = Path(os.environ["CCBA_HUB_PATH"]).resolve()
        if (env_hub / ".agents" / "skills" / "platform-loader" / "catalog.yaml").exists():
            hub_root = env_hub

    # Thử 4: Fallback về thư mục hiện tại nếu đang chạy tại Hub
    if not hub_root:
        cwd_hub = Path.cwd().resolve()
        if (cwd_hub / ".agents" / "skills" / "platform-loader" / "catalog.yaml").exists():
            hub_root = cwd_hub

    if not hub_root:
        print("[Sync] Error: Could not locate Hub directory. Please set CCBA_HUB_PATH environment variable or specify hub_path in workspace_context.yaml.", file=sys.stderr)
        return 1

    # Lưu lại cấu hình định vị thông minh vào context nếu có thay đổi
    if hub_path_str != str(hub_root):
        context["hub_path"] = str(hub_root)
        try:
            with open(context_file, "w", encoding="utf-8") as f:
                yaml.dump(context, f, allow_unicode=True)
            print(f"[Sync] Auto-saved discovered Hub path: {hub_root}")
        except Exception as e:
            print(f"[Sync] Warning: Could not save Hub path to context: {e}", file=sys.stderr)

    print(f"Hub Location: {hub_root}")

    # 2.5 Auto git pull Hub if it is a git repo
    if (hub_root / ".git").exists():
        print("[Sync] Hub is a Git repository. Attempting to pull latest changes from GitHub...")
        try:
            import subprocess
            result = subprocess.run(
                ["git", "pull"],
                cwd=str(hub_root),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("[Sync] Git pull completed successfully.")
                if result.stdout.strip():
                    print(f"  {result.stdout.strip()}")
            else:
                print(f"[Sync] Warning: Git pull failed with code {result.returncode}.", file=sys.stderr)
                if result.stderr.strip():
                    print(f"  {result.stderr.strip()}", file=sys.stderr)
                print("[Sync] Continuing with local offline cache...", file=sys.stderr)
        except Exception as e:
            print(f"[Sync] Warning: Could not execute git pull: {e}", file=sys.stderr)
            print("[Sync] Continuing with local offline cache...", file=sys.stderr)

    # Locate Hub catalog.yaml
    catalog_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if not catalog_file.exists():
        print(f"[Sync] Error: Could not find catalog.yaml at {catalog_file}", file=sys.stderr)
        return 1

    catalog = load_yaml(catalog_file)
    
    spoke_agents_dir = spoke_root / ".agents"
    spoke_skills_dir = spoke_agents_dir / "skills"
    spoke_workflows_dir = spoke_agents_dir / "workflows"

    # CHẾ ĐỘ 1: Đồng bộ bổ sung một Item cụ thể (On-Demand / Lazy Loading)
    if sync_item:
        print(f"Mode: On-Demand Synchronization for '{sync_item}'")
        found = False
        
        # Thử tìm trong danh sách Skills
        for skill_entry in catalog.get("skills", []):
            if skill_entry.get("name") == sync_item:
                skill_path_rel = skill_entry.get("skill_path")
                src = hub_root / Path(skill_path_rel).parent
                dest_name = Path(skill_path_rel).parent.name
                dest = spoke_skills_dir / dest_name
                
                if src.exists():
                    print(f"[Sync] Copying skill [{sync_item}] -> {dest.relative_to(spoke_root)}")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                    found = True
                    break
                else:
                    print(f"[Sync] Error: Skill source path not found at {src}", file=sys.stderr)
                    return 1
                    
        # Thử tìm trong danh sách Workflows nếu chưa tìm thấy trong Skills
        if not found:
            for wf_entry in catalog.get("workflows", []):
                if wf_entry.get("name") == sync_item:
                    wf_path_rel = wf_entry.get("workflow_path")
                    src = hub_root / wf_path_rel
                    filename = Path(wf_path_rel).name
                    dest = spoke_workflows_dir / filename
                    
                    if src.exists():
                        print(f"[Sync] Copying workflow [{sync_item}] -> {dest.relative_to(spoke_root)}")
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        if dest.exists():
                            dest.unlink()
                        shutil.copy2(src, dest)
                        found = True
                        break
                    else:
                        print(f"[Sync] Error: Workflow source file not found at {src}", file=sys.stderr)
                        return 1
                        
        if not found:
            print(f"[Sync] Error: Item '{sync_item}' not found in Hub catalog.yaml.", file=sys.stderr)
            return 1
            
        # Copy hiến pháp
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists():
            shutil.copy2(hub_agents_md, spoke_agents_md)
            
        print("\n=== Sync Completed Successfully ===")
        return 0

    # CHẾ ĐỘ 2: Đồng bộ toàn bộ theo Project Type (mặc định)
    if not project_type:
        print("[Sync] Error: 'project_type' is not defined in workspace_context.yaml.", file=sys.stderr)
        return 1

    print(f"Project Type: {project_type}")

    # Resolve bundles and requirements
    bundle_defs = catalog.get("bundles", {})
    if project_type not in bundle_defs:
        available_types = ", ".join(bundle_defs.keys())
        print(
            f"[Sync] Error: Project type '{project_type}' is not registered in catalog.yaml.",
            file=sys.stderr
        )
        print(f"[Sync] Registered types: {available_types}", file=sys.stderr)
        return 1

    required_bundles = bundle_defs[project_type]
    print(f"Required Bundles: {required_bundles}")

    skills_to_sync = []
    wfs_to_sync = []

    # Filter Skills
    for skill_entry in catalog.get("skills", []):
        skill_name = skill_entry.get("name")
        skill_bundle = skill_entry.get("bundle")
        skill_path_rel = skill_entry.get("skill_path")
        
        if skill_bundle in required_bundles or skill_bundle == "_core":
            skills_to_sync.append({
                "name": skill_name,
                "src_dir": hub_root / Path(skill_path_rel).parent,
                "dest_name": Path(skill_path_rel).parent.name
            })

    # Filter Workflows
    for wf_entry in catalog.get("workflows", []):
        wf_name = wf_entry.get("name")
        wf_bundle = wf_entry.get("bundle")
        wf_path_rel = wf_entry.get("workflow_path")
        
        if wf_bundle in required_bundles or wf_bundle == "_core":
            wfs_to_sync.append({
                "name": wf_name,
                "src_file": hub_root / wf_path_rel,
                "filename": Path(wf_path_rel).name
            })

    # Clean existing
    def safe_remove(path: Path):
        if not path.exists():
            return
        try:
            shutil.rmtree(path)
        except PermissionError:
            # Fallback: Xóa tối đa các file không bị lock thay vì crash
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

    # Dọn dẹp workflows cũ (thường là tệp đơn lẻ, ít bị lock hơn folder)
    safe_remove(spoke_workflows_dir)
    spoke_workflows_dir.mkdir(parents=True, exist_ok=True)

    # Đảm bảo thư mục skills đích tồn tại
    spoke_skills_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Sync] Copying skills...")
    copied_skills_count = 0
    for sk in skills_to_sync:
        src = sk["src_dir"]
        dest = spoke_skills_dir / sk["dest_name"]
        if src.exists():
            print(f"  - [{sk['name']}] -> {dest.relative_to(spoke_root)}")
            try:
                # Xóa sạch dest cũ của skill cụ thể trước nếu được
                safe_remove(dest)
                # Copy đè, dirs_exist_ok=True giúp ghi đè an toàn kể cả khi folder bị lock
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
            print(f"  - [{wf['name']}] -> {dest.relative_to(spoke_root)}")
            shutil.copy2(src, dest)
            copied_wfs_count += 1
        else:
            print(f"  - [Warning] Workflow source file not found: {src}", file=sys.stderr)

    # Copy AGENTS.md
    hub_agents_md = hub_root / ".agents" / "AGENTS.md"
    spoke_agents_md = spoke_agents_dir / "AGENTS.md"
    if hub_agents_md.exists():
        print(f"\n[Sync] Copying constitutional rules (AGENTS.md) -> {spoke_agents_md.relative_to(spoke_root)}")
        shutil.copy2(hub_agents_md, spoke_agents_md)

    # Đăng ký Spoke vào Hub Registry (Mã hóa RSA)
    register_spoke_to_hub(spoke_root, hub_root, project_name, project_type)

    print("\n=== Sync Completed Successfully ===")
    print(f"Synced {copied_skills_count} skills and {copied_wfs_count} workflows.")
    print("Project now structured native for Google Antigravity Auto-Discovery.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="CCBA Spoke Selective Skills Synchronizer")
    parser.add_argument(
        "--spoke",
        default=".",
        help="Path to the target spoke project folder (defaults to current directory)."
    )
    parser.add_argument(
        "--sync-item",
        default=None,
        help="Name of a specific skill or workflow to synchronize on-demand."
    )
    args = parser.parse_args()
    sys.exit(sync_project(args.spoke, args.sync_item))


if __name__ == "__main__":
    main()
