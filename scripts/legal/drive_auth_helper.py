"""Helper script hỗ trợ xác thực Google Drive cá nhân (OAuth 2.0 Desktop Application).

Giải quyết triệt để lỗi Google chặn truy cập (App Blocked) khi dùng gcloud default credentials.
Tạo bởi CCBA.
"""

import os
import sys
from pathlib import Path


# Thêm path để import các thư viện

try:
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False


SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_credentials_dir() -> Path:
    """Read credentials directory from environment variable or user home."""
    env_dir = os.environ.get("CCBA_CREDENTIALS_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".ccba" / "credentials"


def migrate_old_credentials() -> None:
    """Migrate client_secrets.json and drive_token.json from old .md/scratch/ paths to home folder."""
    old_secrets = Path(".md/scratch/client_secrets.json")
    old_token = Path(".md/scratch/drive_token.json")

    target_dir = get_credentials_dir()

    if old_secrets.exists() or old_token.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        print("🔄 Phát hiện credentials cũ ở .md/scratch/. Đang tự động di trú...")

        if old_secrets.exists():
            target_secrets = target_dir / "client_secrets.json"
            if not target_secrets.exists():
                try:
                    import shutil

                    shutil.move(str(old_secrets), str(target_secrets))
                    print(f" -> Đã di chuyển client_secrets.json sang: {target_secrets}")
                except Exception as e:
                    print(f" -> Lỗi di chuyển client_secrets.json: {e}")
            else:
                try:
                    old_secrets.unlink()
                except Exception:
                    pass

        if old_token.exists():
            target_token = target_dir / "drive_token.json"
            if not target_token.exists():
                try:
                    import shutil

                    shutil.move(str(old_token), str(target_token))
                    print(f" -> Đã di chuyển drive_token.json sang: {target_token}")
                except Exception as e:
                    print(f" -> Lỗi di chuyển drive_token.json: {e}")
            else:
                try:
                    old_token.unlink()
                except Exception:
                    pass


CLIENT_SECRETS_PATH = get_credentials_dir() / "client_secrets.json"
TOKEN_PATH = get_credentials_dir() / "drive_token.json"


def print_setup_guide() -> None:
    """In ra hướng dẫn chi tiết cách tạo OAuth Client ID cá nhân trên Google Cloud."""
    print("=" * 80)
    print(" HƯỚNG DẪN THIẾT LẬP OAUTH CLIENT ID CÁ NHÂN (GOOGLE DRIVE)")
    print("=" * 80)
    print("Do chính sách bảo mật mới của Google, gcloud Client ID mặc định đã bị chặn.")
    print(
        "Để xác thực an toàn bằng tài khoản cá nhân, anh vui lòng làm theo 4 bước sau (chỉ mất 2 phút):"
    )
    print("\nBước 1: Tạo dự án & Bật Drive API")
    print("  1. Truy cập: https://console.cloud.google.com/")
    print("  2. Tạo một Dự án mới (Project) bất kỳ (ví dụ: 'CCBA-BIM-Drive').")
    print("  3. Tìm kiếm và click vào 'Google Drive API', sau đó chọn 'Enable' (Bật).")
    print("\nBước 2: Cấu hình Màn hình đồng ý OAuth (OAuth consent screen)")
    print("  1. Tìm mục 'OAuth consent screen' ở thanh menu trái.")
    print("  2. Chọn User Type là 'External' -> Nhấn 'Create'.")
    print("  3. Điền thông tin bắt buộc (Tên ứng dụng: 'CCBA Link', Email liên hệ...).")
    print(
        "  4. Click tiếp tục đến phần 'Test users' -> Nhấn 'ADD USERS' -> Nhập email của anh (macvnboy@gmail.com)."
    )
    print(
        "     (* BẮT BUỘC: Google chỉ cho phép Test Users đăng nhập khi App ở trạng thái Testing để tránh bị chặn)."
    )
    print("  5. Lưu lại.")
    print("\nBước 3: Tạo thông tin xác thực (Credentials)")
    print("  1. Tìm mục 'Credentials' ở thanh menu trái.")
    print("  2. Nhấn '+ CREATE CREDENTIALS' -> Chọn 'OAuth client ID'.")
    print("  3. Chọn Application type là 'Desktop app' -> Nhập tên tùy ý -> Nhấn 'Create'.")
    print("  4. Một hộp thoại hiện ra, nhấn 'DOWNLOAD JSON' để tải tệp tin Credentials về.")
    print("\nBước 4: Lưu tệp tin vào platform")
    print("  1. Đổi tên tệp tin vừa tải về thành: client_secrets.json")
    print("  2. Sao chép/Lưu tệp tin đó vào đúng thư mục:")
    print(f"     {CLIENT_SECRETS_PATH.resolve()}")
    print(
        "\nSau khi đã lưu file 'client_secrets.json', hãy chạy lại lệnh này để hoàn tất đăng nhập!"
    )
    print("=" * 80)


def login_drive() -> None:
    """Thực hiện luồng xác thực OAuth2 cục bộ."""
    if not LIBS_AVAILABLE:
        print("[Error] Thiếu các thư viện google-auth-oauthlib. Vui lòng chạy:")
        print("  pip install google-auth-oauthlib google-auth-httplib2")
        return

    # Tự động di trú credentials cũ nếu có
    migrate_old_credentials()

    # Kiểm tra xem file client_secrets.json có tồn tại không
    if not CLIENT_SECRETS_PATH.exists():
        print_setup_guide()
        return

    print("Phát hiện file client_secrets.json. Đang khởi động luồng xác thực OAuth2...")
    try:
        # Khởi tạo thư mục scratch nếu chưa có
        CLIENT_SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)

        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_PATH), SCOPES)
        # Khởi chạy local server trên port tự do để nhận callback token
        creds = flow.run_local_server(port=0)

        # Lưu token lại vào file drive_token.json
        with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

        print("\n" + "=" * 50)
        print(" ĐĂNG NHẬP GOOGLE DRIVE THÀNH CÔNG!")
        print("=" * 50)
        print("Token xác thực đã được lưu trữ an toàn tại:")
        print(f"  {TOKEN_PATH.resolve()}")
        print("Bây giờ anh đã có thể chạy đồng bộ qua Google Drive bằng flag: --use-drive")
        print("=" * 50)

    except Exception as e:
        print(f"\n[Error] Đăng nhập thất bại: {e}")
        print(
            "Hãy chắc chắn rằng anh đã thêm đúng email macvnboy@gmail.com vào danh sách 'Test users' của app."
        )


def main() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    login_drive()



if __name__ == "__main__":
    main()
