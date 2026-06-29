import os
import sys
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Đảm bảo in ký tự tiếng Việt an toàn trên console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình đường dẫn
PUBLIC_KEY_PATH = ".agents/workflows/resources/registry_public_key.pem"
# Lưu khóa bí mật ngoài codebase
PRIVATE_KEY_DIR = os.path.expanduser(r"~\.gemini\antigravity\keys")
PRIVATE_KEY_PATH = os.path.join(PRIVATE_KEY_DIR, "registry_private_key.pem")

def generate_keys():
    print("🔑 Bắt đầu khởi tạo cặp khóa mật mã RSA 2048-bit...")
    
    # 1. Sinh khóa bí mật
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # 2. Serialize Khóa bí mật sang định dạng PEM
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # 3. Serialize Khóa công khai sang định dạng PEM
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # 4. Ghi khóa bí mật ra ngoài dự án
    os.makedirs(PRIVATE_KEY_DIR, exist_ok=True)
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(pem_private)
    print(f" -> Đã lưu Khóa bí mật an toàn tại: {PRIVATE_KEY_PATH}")
    
    # 5. Ghi khóa công khai vào tài nguyên workflow của Hub
    public_dir = os.path.dirname(PUBLIC_KEY_PATH)
    os.makedirs(public_dir, exist_ok=True)
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(pem_public)
    print(f" -> Đã lưu Khóa công khai (Public Key) tại: {PUBLIC_KEY_PATH}")
    
    print("\n✅ Khởi tạo cặp khóa thành công! Hệ thống Spoke Registry đã sẵn sàng bảo mật.")

if __name__ == "__main__":
    generate_keys()
