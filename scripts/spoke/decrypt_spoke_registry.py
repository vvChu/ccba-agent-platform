import base64
import os
import sys
from pathlib import Path

import yaml

# Attempt importing cryptography
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Cấu hình đường dẫn mặc định
REGISTRY_REL_PATH = ".md/data/spoke_registry.yaml"
DECRYPTED_REL_PATH = ".md/data/spoke_registry_decrypted.yaml"
PRIVATE_KEY_DIR = os.path.expanduser(r"~\.gemini\antigravity\keys")
PRIVATE_KEY_PATH = os.path.join(PRIVATE_KEY_DIR, "registry_private_key.pem")


def get_registered_spokes(hub_root: Path | None = None) -> list[dict]:
    """Retrieve all decrypted active registered spokes from registry or local cache.

    Returns:
        list[dict]: List of spoke dicts with 'name', 'path', 'project_type', 'last_sync', 'spoke_id', 'exists'.
    """
    root = hub_root or Path(__file__).resolve().parents[2]
    registry_file = root / REGISTRY_REL_PATH
    decrypted_file = root / DECRYPTED_REL_PATH

    decrypted_spokes: list[dict] = []

    # Case 1: Try decrypting with RSA Private Key if available
    if HAS_CRYPTOGRAPHY and os.path.exists(PRIVATE_KEY_PATH) and registry_file.exists():
        try:
            with open(PRIVATE_KEY_PATH, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

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

    return decrypted_spokes


def decrypt_registry():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("🔓 Bắt đầu tiến trình giải mã Spoke Registry trung tâm...")

    if not os.path.exists(PRIVATE_KEY_PATH):
        print(f"❌ Lỗi: Không tìm thấy Khóa bí mật tại {PRIVATE_KEY_PATH}")
        print(" -> Vui lòng đảm bảo bạn đang chạy script này với quyền Admin giữ khóa.")
        return

    if not os.path.exists(REGISTRY_REL_PATH):
        print(
            f"⚠️ Cảnh báo: Tệp registry {REGISTRY_REL_PATH} chưa được tạo hoặc chưa có Spoke nào đăng ký."
        )
        return

    with open(REGISTRY_REL_PATH, encoding="utf-8") as f:
        registry_data = yaml.safe_load(f) or {"spokes": []}

    spokes = registry_data.get("spokes", [])
    if not spokes:
        print("Chưa có Spoke nào được ghi nhận trong registry.")
        return

    with open(PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

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

            print(
                f"{spoke_info['name']:<20} | {spoke_info['project_type']:<15} | {spoke_info['last_sync']:<20} | {spoke_info['path']:<35}"
            )

            decrypted_spokes.append({"spoke_id": spoke_id, **spoke_info})
        except Exception as e:
            print(f"❌ Lỗi giải mã Spoke ID {spoke_id[:8]}: {str(e)}")

    # Auto-Prune các Spoke không còn tồn tại vật lý
    pruned_spoke_ids = []
    active_spokes_yaml = []

    for s_info in decrypted_spokes:
        spoke_path = s_info.get("path")
        s_id = s_info.get("spoke_id")
        if not os.path.exists(spoke_path):
            print(f"⚠️ Phát hiện Spoke '{s_info['name']}' không tồn tại vật lý tại: {spoke_path}")
            print(f" -> Tiến hành gỡ bỏ Spoke ID {s_id[:8]} khỏi Registry...")
            pruned_spoke_ids.append(s_id)
        else:
            active_spokes_yaml.append(s_info)

    if pruned_spoke_ids:
        original_spokes = registry_data.get("spokes", [])
        updated_spokes = [s for s in original_spokes if s.get("spoke_id") not in pruned_spoke_ids]
        registry_data["spokes"] = updated_spokes

        with open(REGISTRY_REL_PATH, "w", encoding="utf-8") as f:
            yaml.dump(registry_data, f, allow_unicode=True)
        print(f" -> Đã cập nhật và dọn dẹp tệp registry mã hóa {REGISTRY_REL_PATH}.")

    if active_spokes_yaml:
        os.makedirs(os.path.dirname(DECRYPTED_REL_PATH), exist_ok=True)
        with open(DECRYPTED_REL_PATH, "w", encoding="utf-8") as f:
            yaml.dump({"spokes": active_spokes_yaml}, f, allow_unicode=True)
        print(
            f"\n✅ Đã lưu kết quả giải mã các Spoke hoạt động tại: {DECRYPTED_REL_PATH} (Được bỏ qua bởi Git)"
        )


if __name__ == "__main__":
    decrypt_registry()
