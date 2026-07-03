import base64
import os
import sys

import yaml
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Đảm bảo in ký tự tiếng Việt an toàn trên console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình đường dẫn
REGISTRY_PATH = ".md/data/spoke_registry.yaml"
DECRYPTED_PATH = ".md/data/spoke_registry_decrypted.yaml"
PRIVATE_KEY_DIR = os.path.expanduser(r"~\.gemini\antigravity\keys")
PRIVATE_KEY_PATH = os.path.join(PRIVATE_KEY_DIR, "registry_private_key.pem")

def decrypt_registry():
    print("🔓 Bắt đầu tiến trình giải mã Spoke Registry trung tâm...")

    # 1. Kiểm tra khóa bí mật
    if not os.path.exists(PRIVATE_KEY_PATH):
        print(f"❌ Lỗi: Không tìm thấy Khóa bí mật tại {PRIVATE_KEY_PATH}")
        print(" -> Vui lòng đảm bảo bạn đang chạy script này với quyền Admin giữ khóa.")
        return

    # 2. Đọc khóa bí mật
    with open(PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    # 3. Kiểm tra tệp registry mã hóa
    if not os.path.exists(REGISTRY_PATH):
        print(f"⚠️ Cảnh báo: Tệp registry {REGISTRY_PATH} chưa được tạo hoặc chưa có Spoke nào đăng ký.")
        return

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry_data = yaml.safe_load(f) or {"spokes": []}

    spokes = registry_data.get("spokes", [])
    if not spokes:
        print("Chưa có Spoke nào được ghi nhận trong registry.")
        return

    decrypted_spokes = []
    print(f"\n{'Tên Spoke':<20} | {'Loại Nghiệp vụ':<15} | {'Đồng bộ lúc':<20} | {'Đường dẫn Vật lý':<35}")
    print("-" * 100)

    for spoke in spokes:
        spoke_id = spoke.get("spoke_id")
        encrypted_b64 = spoke.get("encrypted_data")

        try:
            # Giải mã dữ liệu
            encrypted_bytes = base64.b64decode(encrypted_b64)
            decrypted_bytes = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            # Parse YAML dữ liệu gốc của Spoke
            spoke_info = yaml.safe_load(decrypted_bytes.decode('utf-8'))

            print(f"{spoke_info['name']:<20} | {spoke_info['project_type']:<15} | {spoke_info['last_sync']:<20} | {spoke_info['path']:<35}")

            decrypted_spokes.append({
                "spoke_id": spoke_id,
                **spoke_info
            })
        except Exception as e:
            print(f"❌ Lỗi giải mã Spoke ID {spoke_id[:8]}: {str(e)}")

    # 4. Tự động dọn dẹp (Auto-Prune) các Spoke không còn tồn tại vật lý
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
        # Cập nhật lại file registry mã hóa gốc
        original_spokes = registry_data.get("spokes", [])
        updated_spokes = [s for s in original_spokes if s.get("spoke_id") not in pruned_spoke_ids]
        registry_data["spokes"] = updated_spokes

        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            yaml.dump(registry_data, f, allow_unicode=True)
        print(f" -> Đã cập nhật và dọn dẹp tệp registry mã hóa {REGISTRY_PATH}.")

    # 5. Ghi file giải mã nháp cục bộ
    if active_spokes_yaml:
        os.makedirs(os.path.dirname(DECRYPTED_PATH), exist_ok=True)
        with open(DECRYPTED_PATH, "w", encoding="utf-8") as f:
            yaml.dump({"spokes": active_spokes_yaml}, f, allow_unicode=True)
        print(f"\n✅ Đã lưu kết quả giải mã các Spoke hoạt động tại: {DECRYPTED_PATH} (Được bỏ qua bởi Git)")

if __name__ == "__main__":
    decrypt_registry()
