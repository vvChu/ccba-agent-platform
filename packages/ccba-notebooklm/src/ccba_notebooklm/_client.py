import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from notebooklm import NotebookLMClient
    from notebooklm.exceptions import NetworkError
    from notebooklm.rpc.types import (
        InfographicDetail,
        InfographicOrientation,
        InfographicStyle,
        QuizDifficulty,
        QuizQuantity,
        ReportFormat,
        SlideDeckFormat,
        SlideDeckLength,
        VideoFormat,
        VideoStyle,
    )
    HAS_NOTEBOOKLM = True
except ImportError:
    NotebookLMClient = None
    HAS_NOTEBOOKLM = False
    QuizQuantity = QuizDifficulty = SlideDeckFormat = SlideDeckLength = None
    ReportFormat = InfographicOrientation = InfographicDetail = InfographicStyle = None
    VideoFormat = VideoStyle = None
    NetworkError = Exception


def get_temp_storage_path() -> Path:
    """Đường dẫn lưu trữ file Playwright cookie tạm thời."""
    scratch_dir = Path(".md/scratch")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir / "notebooklm_cookies.json"


def inject_auth_cookies() -> str | None:
    """
    Đọc biến môi trường và tạo file cookie tạm thời cho Playwright.
    Trả về đường dẫn file cookies JSON nếu thành công, None nếu dùng mặc định.
    """
    env_cookie = os.environ.get("NOTEBOOKLM_SESSION_COOKIE")
    env_json = os.environ.get("NOTEBOOKLM_COOKIES_JSON")
    temp_path = get_temp_storage_path()

    if env_json:
        try:
            data = json.loads(env_json)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("[Info] Đã nạp cấu hình auth từ NOTEBOOKLM_COOKIES_JSON.")
            return str(temp_path.absolute())
        except Exception as e:
            print(f"[Warn] Lỗi phân tích NOTEBOOKLM_COOKIES_JSON: {e}", file=sys.stderr)

    if env_cookie:
        try:
            cookies = []
            for part in env_cookie.split(";"):
                if "=" in part:
                    name, value = part.strip().split("=", 1)
                    cookies.append({
                        "name": name,
                        "value": value,
                        "domain": ".google.com",
                        "path": "/",
                        "expires": -1,
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax"
                    })
            storage_state = {
                "cookies": cookies,
                "origins": []
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(storage_state, f, ensure_ascii=False, indent=2)
            print("[Info] Đã chuyển đổi và nạp auth từ NOTEBOOKLM_SESSION_COOKIE.")
            return str(temp_path.absolute())
        except Exception as e:
            print(f"[Warn] Lỗi phân tích NOTEBOOKLM_SESSION_COOKIE: {e}", file=sys.stderr)

    return None


def get_client() -> Any:
    """Tạo đối tượng client với các thiết lập auth phù hợp."""
    cookie_path = inject_auth_cookies()
    if cookie_path:
        return NotebookLMClient.from_storage(path=cookie_path)
    return NotebookLMClient.from_storage()


async def check_auth() -> int:
    """Kiểm tra trạng thái đăng nhập NotebookLM."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt. Vui lòng chạy: pip install notebooklm-py", file=sys.stderr)
        return 1

    try:
        async with get_client() as client:
            await client.notebooks.list()
            print("SUCCESS: Kết nối và xác thực thành công với Google NotebookLM Cloud!")
            tier = await client.settings.get_account_tier()
            print(f"[Info] Subscription Tier: {tier.tier} ({tier.plan_name or 'Standard Plan'})")
            return 0
    except Exception as e:
        print(f"ERROR_AUTH: Session cookie đã hết hạn hoặc không tồn tại. Vui lòng chạy 'python -m notebooklm login' trên trình duyệt để đăng nhập lại. Chi tiết: {e}", file=sys.stderr)
        return 2
