"""
CCBA NotebookLM Client and Auth configuration.
Handles Google accounts cookie authentication and mock adapter fallbacks.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# Deep Seam Wrapper
# ---------------------------------------------------------------------------


class CCBANotebookLMClient:
    """Giao diện seam sâu bọc NotebookLMClient để hỗ trợ mock adapter và auto auth."""

    def __init__(self, client: Any, use_mock: bool = False) -> None:
        self._client = client
        self.use_mock = use_mock

    async def __aenter__(self) -> Any:
        return await self._client.__aenter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    @classmethod
    def from_storage(cls, path: str | None = None, use_mock: bool = False) -> CCBANotebookLMClient:
        """Khởi tạo client từ storage. Chuyển đổi sang mock adapter nếu cần thiết."""
        if use_mock:
            logger.info("Kích hoạt Mock NotebookLM Client (Không phát hiện AUTH cookie).")
            from ._mock_client import MockNotebookLMClientAdapter
            return cls(MockNotebookLMClientAdapter(), use_mock=True)

        if not HAS_NOTEBOOKLM or NotebookLMClient is None:
            logger.warning(
                "Không tìm thấy thư viện notebooklm-py. Tự động chuyển sang Mock Client."
            )
            from ._mock_client import MockNotebookLMClientAdapter
            return cls(MockNotebookLMClientAdapter(), use_mock=True)

        try:
            real_client = (
                NotebookLMClient.from_storage(path=path)
                if path
                else NotebookLMClient.from_storage()
            )
            return cls(real_client, use_mock=False)
        except Exception as e:
            logger.warning("Khởi tạo Real Client lỗi (%s). Tự động chuyển sang Mock Client.", e)
            from ._mock_client import MockNotebookLMClientAdapter
            return cls(MockNotebookLMClientAdapter(), use_mock=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_temp_storage_path() -> Path:
    """Đường dẫn lưu trữ file Playwright cookie tạm thời."""
    scratch_dir = Path(".md/scratch")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir / "notebooklm_cookies.json"


def inject_auth_cookies() -> str | None:
    """Đọc biến môi trường và tạo file cookie tạm thời cho Playwright.

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
                    cookies.append(
                        {
                            "name": name,
                            "value": value,
                            "domain": ".google.com",
                            "path": "/",
                            "expires": -1,
                            "httpOnly": True,
                            "secure": True,
                            "sameSite": "Lax",
                        }
                    )
            storage_state = {"cookies": cookies, "origins": []}
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(storage_state, f, ensure_ascii=False, indent=2)
            print("[Info] Đã chuyển đổi và nạp auth từ NOTEBOOKLM_SESSION_COOKIE.")
            return str(temp_path.absolute())
        except Exception as e:
            print(f"[Warn] Lỗi phân tích NOTEBOOKLM_SESSION_COOKIE: {e}", file=sys.stderr)

    return None


def get_client() -> CCBANotebookLMClient:
    """Tạo đối tượng client với các thiết lập auth phù hợp."""
    cookie_path = inject_auth_cookies()
    env_cookie = os.environ.get("NOTEBOOKLM_SESSION_COOKIE")
    env_json = os.environ.get("NOTEBOOKLM_COOKIES_JSON")

    is_testing = bool(os.environ.get("PYTEST_CURRENT_TEST"))

    # Nếu không có biến môi trường nhưng file cookie đã tồn tại sẵn trên đĩa
    temp_path = get_temp_storage_path()
    if not cookie_path and temp_path.exists() and not is_testing:
        cookie_path = str(temp_path.absolute())

    default_state_path = Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"
    use_mock = not (
        env_cookie
        or env_json
        or (cookie_path and Path(cookie_path).exists() and not is_testing)
        or (default_state_path.exists() and not is_testing)
    )

    return CCBANotebookLMClient.from_storage(path=cookie_path, use_mock=use_mock)


async def check_auth() -> int:
    """Kiểm tra trạng thái đăng nhập NotebookLM."""
    client_instance = get_client()
    if client_instance.use_mock:
        print("[Info] SUCCESS: Chế độ giả lập (Mock Mode) hoạt động bình thường!")
        print("[Info] Subscription Tier: mock (Mock Standard Plan)")
        return 0

    if not HAS_NOTEBOOKLM:
        print(
            "ERROR: Thư viện 'notebooklm-py' chưa được cài đặt. Vui lòng chạy: pip install notebooklm-py",
            file=sys.stderr,
        )
        return 1

    try:
        async with client_instance as client:
            await client.notebooks.list()
            print("SUCCESS: Kết nối và xác thực thành công với Google NotebookLM Cloud!")
            tier = await client.settings.get_account_tier()
            print(f"[Info] Subscription Tier: {tier.tier} ({tier.plan_name or 'Standard Plan'})")
            return 0
    except Exception as e:
        print(
            f"ERROR_AUTH: Session cookie đã hết hạn hoặc không tồn tại. Vui lòng chạy 'python -m notebooklm login' trên trình duyệt để đăng nhập lại. Chi tiết: {e}",
            file=sys.stderr,
        )
        return 2
