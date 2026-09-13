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
PRIVATE_KEY_DIR = os.path.expanduser(r"~\.gemini\antigravity\keys")
PRIVATE_KEY_PATH = os.path.join(PRIVATE_KEY_DIR, "registry_private_key.pem")


def load_spoke_heartbeats(hub_root: Path | None = None) -> dict[str, Any]:
    """Loads dynamic last_sync heartbeats from .md/telemetry/spoke_heartbeats.yaml."""
    root = hub_root or Path(__file__).resolve().parents[2]
    hb_file = root / HEARTBEATS_REL_PATH
    if not hb_file.exists():
        return {}
    try:
        with open(hb_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            heartbeats = data.get("heartbeats", {})
            return heartbeats if isinstance(heartbeats, dict) else {}
    except Exception:
        return {}


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

    # Attach dynamic heartbeats and ensure archetype exists
    for sp in decrypted_spokes:
        s_id = sp.get("spoke_id")
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
