import base64
import os
import sys
from pathlib import Path
from typing import Any

import yaml

# Attempt importing cryptography
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Cấu hình đường dẫn mặc định
REGISTRY_REL_PATH = ".md/data/spoke_registry.yaml"
DECRYPTED_REL_PATH = ".md/data/spoke_registry_decrypted.yaml"
HEARTBEATS_REL_PATH = ".md/telemetry/spoke_heartbeats.yaml"
PRIVATE_KEY_DIR = str(Path.home() / ".gemini" / "antigravity" / "keys")
PRIVATE_KEY_PATH = os.path.join(PRIVATE_KEY_DIR, "registry_private_key.pem")


def _is_pytest_ephemeral_path(path_str: str) -> bool:
    """Return True if path_str points to an ephemeral pytest temporary directory."""
    norm = path_str.replace("\\", "/")
    return "/pytest-of-" in norm or "/pytest-" in norm or "MOCK-TEST-SPOKE" in path_str


def load_spoke_heartbeats(hub_root: Path | None = None) -> dict[str, Any]:
    """Loads dynamic last_sync heartbeats from .md/telemetry/spoke_heartbeats.yaml."""
    default_root = Path(__file__).resolve().parents[2]
    root = hub_root or default_root
    hb_file = root / HEARTBEATS_REL_PATH
    if not hb_file.exists():
        return {}
    try:
        with open(hb_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            heartbeats = data.get("heartbeats", {})
            if not isinstance(heartbeats, dict):
                return {}
            if root.resolve() == default_root.resolve():
                return {
                    k: v
                    for k, v in heartbeats.items()
                    if isinstance(v, dict) and not _is_pytest_ephemeral_path(str(v.get("path", "")))
                }
            return heartbeats
    except Exception:
        return {}


def _build_spoke_from_heartbeat(s_id: str, hb: dict[str, Any], root: Path) -> dict[str, Any] | None:
    """Construct spoke metadata entry from active local heartbeat and workspace_context.yaml."""
    sp_path_str = str(hb.get("path", "")).strip()
    if not sp_path_str or not os.path.exists(sp_path_str):
        return None
    sp_path = Path(sp_path_str)
    if sp_path.resolve() == root.resolve() or sp_path.name.startswith("ccba-agent-platform"):
        return None
    ctx_file = sp_path / ".md" / "workspace_context.yaml"
    if not ctx_file.exists():
        ctx_file = sp_path / ".agents" / "workspace_context.yaml"
    if not ctx_file.exists():
        return None
    proj_type = ""
    archetype = ""
    is_sandbox = False
    sp_name = str(hb.get("name") or sp_path.name)
    try:
        ctx = yaml.safe_load(ctx_file.read_text(encoding="utf-8")) or {}
        proj = ctx.get("project", {}) if isinstance(ctx.get("project"), dict) else {}
        sp_name = str(proj.get("name") or ctx.get("project_name") or sp_name)
        proj_type = str(
            proj.get("type") or proj.get("project_type") or ctx.get("project_type") or ""
        )
        archetype = str(proj.get("archetype") or ctx.get("archetype") or "")
        guardrails = ctx.get("guardrails", {}) if isinstance(ctx.get("guardrails"), dict) else {}
        is_sandbox = (
            proj.get("sub_type") == "personal_sandbox" or guardrails.get("sandbox_mode") is True
        )
    except Exception:
        pass
    return {
        "spoke_id": s_id,
        "name": sp_name,
        "path": sp_path_str,
        "project_type": proj_type,
        "archetype": archetype,
        "is_sandbox": is_sandbox,
        "last_sync": str(hb.get("last_sync", "")),
        "exists": True,
    }


def get_registered_spokes(hub_root: Path | None = None) -> list[dict[str, Any]]:
    """Retrieve all decrypted active registered spokes from registry or local cache.

    Returns:
        list[dict]: List of spoke dicts with 'name', 'path', 'project_type', 'archetype', 'last_sync', 'spoke_id', 'exists'.
    """
    root = hub_root or Path(__file__).resolve().parents[2]
    registry_file = root / REGISTRY_REL_PATH
    decrypted_file = root / DECRYPTED_REL_PATH
    heartbeats = load_spoke_heartbeats(root)

    decrypted_spokes: list[dict[str, Any]] = []

    # Case 1: Try decrypting with RSA Private Key if available
    if HAS_CRYPTOGRAPHY and os.path.exists(PRIVATE_KEY_PATH) and registry_file.exists():
        try:
            with open(PRIVATE_KEY_PATH, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            if isinstance(private_key, rsa.RSAPrivateKey):
                with open(registry_file, encoding="utf-8") as f:
                    registry_data = yaml.safe_load(f) or {"spokes": []}

                for spoke in registry_data.get("spokes", []):
                    spoke_id = spoke.get("spoke_id")
                    encrypted_b64 = spoke.get("encrypted_data")
                    try:
                        encrypted_bytes = base64.b64decode(encrypted_b64)
                        decrypted_bytes = private_key.decrypt(
                            encrypted_bytes,
                            padding.OAEP(
                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(),
                                label=None,
                            ),
                        )
                        spoke_info = yaml.safe_load(decrypted_bytes.decode("utf-8"))
                        spoke_info["spoke_id"] = spoke_id
                        spoke_info["exists"] = os.path.exists(spoke_info.get("path", ""))
                        decrypted_spokes.append(spoke_info)
                    except Exception:
                        pass
        except Exception:
            pass

    # Case 2: Fallback to decrypted cache file if RSA decrypt returned nothing
    if not decrypted_spokes and decrypted_file.exists():
        try:
            with open(decrypted_file, encoding="utf-8") as f:
                cache_data = yaml.safe_load(f) or {"spokes": []}
                for s in cache_data.get("spokes", []):
                    s["exists"] = os.path.exists(s.get("path", ""))
                    decrypted_spokes.append(s)
        except Exception:
            pass

    # Case 3: Fallback to active local heartbeats when RSA key and decrypted cache are unavailable
    if not decrypted_spokes and heartbeats:
        for s_id, hb in sorted(heartbeats.items()):
            if not isinstance(hb, dict):
                continue
            sp_entry = _build_spoke_from_heartbeat(s_id, hb, root)
            if sp_entry is not None:
                decrypted_spokes.append(sp_entry)

    # Attach dynamic heartbeats and ensure archetype exists
    for sp in decrypted_spokes:
        s_id = sp.get("spoke_id")
        if not s_id and sp.get("path"):
            import hashlib

            s_id = hashlib.sha256(str(Path(sp["path"]).resolve()).encode("utf-8")).hexdigest()
            sp["spoke_id"] = s_id
        hb = heartbeats.get(s_id, {})
        if isinstance(hb, dict) and hb.get("last_sync"):
            sp["last_sync"] = hb["last_sync"]
        elif "last_sync" not in sp:
            sp["last_sync"] = ""
        if "archetype" not in sp:
            sp["archetype"] = ""

    return decrypted_spokes


def decrypt_registry(hub_root: Path | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("🔓 Bắt đầu tiến trình giải mã Spoke Registry trung tâm...")

    root = hub_root or Path(__file__).resolve().parents[2]
    registry_file = root / REGISTRY_REL_PATH
    decrypted_file = root / DECRYPTED_REL_PATH
    heartbeats = load_spoke_heartbeats(root)

    if not os.path.exists(PRIVATE_KEY_PATH):
        print(f"❌ Lỗi: Không tìm thấy Khóa bí mật tại {PRIVATE_KEY_PATH}")
        print(" -> Vui lòng đảm bảo bạn đang chạy script này với quyền Admin giữ khóa.")
        return

    if not registry_file.exists():
        print(
            f"⚠️ Cảnh báo: Tệp registry {registry_file} chưa được tạo hoặc chưa có Spoke nào đăng ký."
        )
        return

    with open(registry_file, encoding="utf-8") as f:
        registry_data = yaml.safe_load(f) or {"spokes": []}

    spokes = registry_data.get("spokes", [])
    if not spokes:
        print("Chưa có Spoke nào được ghi nhận trong registry.")
        return

    with open(PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    if not isinstance(private_key, rsa.RSAPrivateKey):
        print("❌ Khóa riêng tư không hợp lệ hoặc không phải RSA.")
        return

    decrypted_spokes = []
    print(
        f"\n{'Tên Spoke':<20} | {'Loại Nghiệp vụ':<15} | {'Đồng bộ lúc':<20} | {'Đường dẫn Vật lý':<35}"
    )
    print("-" * 100)

    for spoke in spokes:
        spoke_id = spoke.get("spoke_id")
        encrypted_b64 = spoke.get("encrypted_data")

        try:
            encrypted_bytes = base64.b64decode(encrypted_b64)
            decrypted_bytes = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            spoke_info = yaml.safe_load(decrypted_bytes.decode("utf-8"))
            hb = heartbeats.get(spoke_id, {})
            last_sync_val = (
                hb.get("last_sync")
                if isinstance(hb, dict) and hb.get("last_sync")
                else spoke_info.get("last_sync", "Chưa rõ")
            )
            spoke_info["last_sync"] = last_sync_val
            if "archetype" not in spoke_info:
                spoke_info["archetype"] = ""

            display_type = spoke_info.get("archetype") or spoke_info.get("project_type", "")
            print(
                f"{spoke_info.get('name', 'Unknown'):<20} | {display_type:<15} | {last_sync_val:<20} | {spoke_info.get('path', ''):<35}"
            )

            decrypted_spokes.append({"spoke_id": spoke_id, **spoke_info})
        except Exception as e:
            print(f"❌ Lỗi giải mã Spoke ID {spoke_id[:8] if spoke_id else 'unknown'}: {str(e)}")

    # Auto-Prune các Spoke không còn tồn tại vật lý
    pruned_spoke_ids = []
    active_spokes_yaml = []

    for s_info in decrypted_spokes:
        spoke_path = s_info.get("path")
        s_id = s_info.get("spoke_id")
        if not spoke_path or not os.path.exists(str(spoke_path)):
            print(
                f"⚠️ Phát hiện Spoke '{s_info.get('name')}' không tồn tại vật lý tại: {spoke_path}"
            )
            print(f" -> Tiến hành gỡ bỏ Spoke ID {str(s_id)[:8]} khỏi Registry...")
            pruned_spoke_ids.append(s_id)
        else:
            active_spokes_yaml.append(s_info)

    if pruned_spoke_ids:
        original_spokes = registry_data.get("spokes", [])
        updated_spokes = [s for s in original_spokes if s.get("spoke_id") not in pruned_spoke_ids]
        registry_data["spokes"] = updated_spokes

        with open(registry_file, "w", encoding="utf-8") as f:
            yaml.dump(registry_data, f, allow_unicode=True)
        print(f" -> Đã cập nhật và dọn dẹp tệp registry mã hóa {registry_file}.")

    if active_spokes_yaml:
        decrypted_file.parent.mkdir(parents=True, exist_ok=True)
        with open(decrypted_file, "w", encoding="utf-8") as f:
            yaml.dump({"spokes": active_spokes_yaml}, f, allow_unicode=True)
        print(
            f"\n✅ Đã lưu kết quả giải mã các Spoke hoạt động tại: {decrypted_file} (Được bỏ qua bởi Git)"
        )


if __name__ == "__main__":
    decrypt_registry()
